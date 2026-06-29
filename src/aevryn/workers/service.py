"""Background job submission and worker execution services."""

from __future__ import annotations

import json
import logging
import tempfile
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Protocol

from aevryn.extraction import SceneExtractor
from aevryn.import_storage import ImportContentStore
from aevryn.persistence import EngineRunRecord, ProjectRepository, SnapshotRecord
from aevryn.presentation import PresentationEngine, PresentationSection
from aevryn.presentation.models import (
    CharacterProfileView,
    ProductionPackView,
    SceneSheetView,
    WorldSheetView,
)
from aevryn.projects import (
    AevrynProjectRunner,
    ContinuityRecord,
    ContinuityReport,
    ContinuitySceneReport,
    ProjectRunResult,
)
from aevryn.prompts import CanonPromptBuilder
from aevryn.workers.models import BackgroundJob, BackgroundWorkerRunSummary
from aevryn.workers.queue import BackgroundJobQueue, DuplicateJobError

_TIMELINE_OMITTED_ATTRIBUTES = frozenset(
    {"display_name", "race", "species", "gender", "sex"}
)
_SOURCE_BACKED_PLACEHOLDER = "Source-backed detail available through evidence controls."
_MAX_TIMELINE_CHANGES_PER_SCENE = 8
_MAX_PROJECT_SCENE_SHEETS = 12
_MAX_PROJECT_PROMPT_PACKS = 6

logger = logging.getLogger(__name__)


class BackgroundJobHandler(Protocol):
    """Handler that performs a claimed background job."""

    def process(self, job: BackgroundJob) -> tuple[SnapshotRecord, ...] | None:
        """Execute a claimed job or raise a clear exception."""


class ProjectImportSnapshotHandler:
    """Run imported source content and return durable snapshot records."""

    def __init__(
        self,
        repository: ProjectRepository,
        import_content_store: ImportContentStore,
        extractor: SceneExtractor | None = None,
    ) -> None:
        """Create a project import snapshot handler."""
        self._repository = repository
        self._import_content_store = import_content_store
        self._extractor = extractor

    def process(self, job: BackgroundJob) -> tuple[SnapshotRecord, ...]:
        """Process one import job into deterministic engine output snapshots."""
        if job.kind != "process_import":
            raise ValueError(f"Unsupported background job kind: {job.kind}")
        import_record = self._repository.get_import_for_worker(job.import_id)
        if import_record.story_id != job.story_id:
            raise ValueError("Background job import does not match story scope.")
        content = self._import_content_store.read_import_content(import_record.storage_ref)
        with tempfile.TemporaryDirectory(prefix="AEVRYN_worker_import_") as directory:
            source_path = Path(directory) / import_record.filename
            source_path.write_bytes(content)
            runner = AevrynProjectRunner()
            imported_source = runner.import_text_file(
                path=source_path,
                source_id=import_record.source_id,
                title=source_path.stem,
            )
            if self._extractor is None:
                result = runner.run_demo_imported_source(imported_source)
            else:
                result = runner.run_imported_source(
                    imported_source=imported_source,
                    extractor=self._extractor,
                    reject_unknown_anchor_candidates=True,
                )
        return (
            SnapshotRecord(
                snapshot_id=f"snapshot_{job.run_id}_canon",
                project_id=job.project_id,
                story_id=job.story_id,
                run_id=job.run_id,
                snapshot_kind="canon",
                content_type="application/json",
                serialized_output=_canon_snapshot_payload(result),
                created_at=job.status_updated_at,
            ),
        )


class BackgroundJobService:
    """Submit background jobs without executing engine logic inline."""

    def __init__(
        self,
        repository: ProjectRepository,
        queue: BackgroundJobQueue,
        engine_version: str,
    ) -> None:
        """Create a background job submission service."""
        if not engine_version.strip():
            raise ValueError("Engine version cannot be blank.")
        self._repository = repository
        self._queue = queue
        self._engine_version = engine_version

    def submit_import_processing_job(
        self,
        *,
        job_id: str,
        run_id: str,
        project_id: str,
        story_id: str,
        import_id: str,
        queued_at: str,
    ) -> BackgroundJob:
        """Record a pending engine run and enqueue import processing.

        The service owns job submission only. The worker owns execution, and the
        engine remains the only owner of continuity behavior.
        """
        job = BackgroundJob(
            job_id=job_id,
            kind="process_import",
            run_id=run_id,
            project_id=project_id,
            story_id=story_id,
            import_id=import_id,
            status="queued",
            queued_at=queued_at,
            status_updated_at=queued_at,
        )
        if self._queue.has_job(job_id):
            raise DuplicateJobError(f"Duplicate background job: {job_id}")
        run = EngineRunRecord(
            run_id=run_id,
            project_id=project_id,
            story_id=story_id,
            import_id=import_id,
            status="pending",
            engine_version=self._engine_version,
            started_at=queued_at,
            status_updated_at=queued_at,
            job_ref=f"queue://{job_id}",
        )
        self._repository.record_engine_run(run)
        try:
            self._queue.enqueue(job)
        except Exception as error:
            self._repository.update_engine_run(
                replace(
                    run,
                    status="failed",
                    status_updated_at=queued_at,
                    finished_at=queued_at,
                    error_summary=_error_summary(error),
                )
            )
            raise
        logger.debug(
            "background_job_submitted",
            extra={"job_id": job_id, "run_id": run_id},
        )
        return job


class BackgroundWorker:
    """Claim queued jobs and synchronize engine run lifecycle records."""

    def __init__(
        self,
        repository: ProjectRepository,
        queue: BackgroundJobQueue,
        handler: BackgroundJobHandler,
    ) -> None:
        """Create a background worker."""
        self._repository = repository
        self._queue = queue
        self._handler = handler

    def process_next(self, *, started_at: str, finished_at: str) -> BackgroundJob | None:
        """Process one queued job and return its final queue record.

        Returns:
            The succeeded or failed job, or ``None`` when the queue is empty.
        """
        _require_worker_timestamp_order(started_at=started_at, finished_at=finished_at)
        job = self._queue.claim_next(claimed_at=started_at)
        if job is None:
            logger.debug("background_worker_idle")
            return None

        perf_started_at = time.perf_counter()
        run = self._repository.get_engine_run_for_worker(job.run_id)
        if run.status in {"succeeded", "failed"}:
            summary = "Background job was ignored because its run is already terminal."
            failed_job = self._queue.fail(
                job_id=job.job_id,
                failed_at=finished_at,
                error_summary=summary,
            )
            _log_worker_job_event(
                job=failed_job,
                status="failed",
                duration_ms=_elapsed_ms(perf_started_at),
                error_summary=summary,
                snapshot_count=0,
            )
            return failed_job
        scope_error = _job_scope_error(job=job, run=run)
        if scope_error:
            self._repository.update_engine_run(
                replace(
                    run,
                    status="failed",
                    status_updated_at=finished_at,
                    finished_at=finished_at,
                    error_summary=scope_error,
                )
            )
            failed_job = self._queue.fail(
                job_id=job.job_id,
                failed_at=finished_at,
                error_summary=scope_error,
            )
            _log_worker_job_event(
                job=failed_job,
                status="failed",
                duration_ms=_elapsed_ms(perf_started_at),
                error_summary=scope_error,
                snapshot_count=0,
            )
            return failed_job
        self._repository.update_engine_run(
            replace(run, status="running", status_updated_at=started_at)
        )
        try:
            snapshots = self._handler.process(job) or ()
        except Exception as error:
            summary = _error_summary(error)
            latest_run = self._repository.get_engine_run_for_worker(job.run_id)
            self._repository.update_engine_run(
                replace(
                    latest_run,
                    status="failed",
                    status_updated_at=finished_at,
                    finished_at=finished_at,
                    error_summary=summary,
                )
            )
            failed_job = self._queue.fail(
                job_id=job.job_id,
                failed_at=finished_at,
                error_summary=summary,
            )
            _log_worker_job_event(
                job=failed_job,
                status="failed",
                duration_ms=_elapsed_ms(perf_started_at),
                error_summary=summary,
                snapshot_count=0,
            )
            return failed_job

        latest_run = self._repository.get_engine_run_for_worker(job.run_id)
        self._repository.update_engine_run(
            replace(
                latest_run,
                status="succeeded",
                status_updated_at=finished_at,
                finished_at=finished_at,
            )
        )
        for snapshot in snapshots:
            snapshot_started_at = time.perf_counter()
            self._repository.store_snapshot(snapshot)
            _log_snapshot_event(
                snapshot=snapshot,
                duration_ms=_elapsed_ms(snapshot_started_at),
            )
        completed_job = self._queue.complete(job_id=job.job_id, completed_at=finished_at)
        _log_worker_job_event(
            job=completed_job,
            status="succeeded",
            duration_ms=_elapsed_ms(perf_started_at),
            error_summary="",
            snapshot_count=len(snapshots),
        )
        return completed_job

    def process_available(
        self,
        *,
        started_at: str,
        finished_at: str,
        max_jobs: int,
    ) -> BackgroundWorkerRunSummary:
        """Process queued jobs until idle or the job limit is reached.

        Parameters:
            started_at: UTC timestamp applied to each claimed job.
            finished_at: UTC timestamp applied to each completed job.
            max_jobs: Maximum number of jobs to process in this drain loop.

        Returns:
            Summary of claimed, succeeded, and failed jobs.
        """
        if isinstance(max_jobs, bool) or max_jobs < 1:
            raise ValueError("max_jobs must be a positive integer.")
        succeeded_jobs = 0
        failed_jobs = 0
        for _ in range(max_jobs):
            job = self.process_next(started_at=started_at, finished_at=finished_at)
            if job is None:
                break
            if job.status == "succeeded":
                succeeded_jobs += 1
            elif job.status == "failed":
                failed_jobs += 1

        return BackgroundWorkerRunSummary(
            claimed_jobs=succeeded_jobs + failed_jobs,
            succeeded_jobs=succeeded_jobs,
            failed_jobs=failed_jobs,
        )


def _require_worker_timestamp_order(started_at: str, finished_at: str) -> None:
    """Require worker finish timestamps to be at or after start timestamps."""
    started = _parse_utc_timestamp(started_at, "Worker started_at")
    finished = _parse_utc_timestamp(finished_at, "Worker finished_at")
    if finished < started:
        raise ValueError("Worker finished_at cannot be before started_at.")


def _parse_utc_timestamp(value: str, label: str) -> datetime:
    """Parse a UTC timestamp ending in Z."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} cannot be blank.")
    if "T" not in value or not value.endswith("Z"):
        raise ValueError(f"{label} must be an ISO UTC timestamp ending in Z.")
    try:
        return datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO UTC timestamp ending in Z.") from error


def _job_scope_error(job: BackgroundJob, run: EngineRunRecord) -> str:
    """Return a scope error when a job does not match its engine run."""
    if (
        job.project_id != run.project_id
        or job.story_id != run.story_id
        or job.import_id != run.import_id
    ):
        return "Background job scope does not match engine run scope."
    expected_job_ref = f"queue://{job.job_id}"
    if run.job_ref != expected_job_ref:
        return "Background job reference does not match engine run job_ref."
    return ""


def _canon_snapshot_payload(result: ProjectRunResult) -> str:
    """Return a deterministic JSON snapshot for a completed canon run."""
    scene_ids = tuple(
        scene.scene_id
        for chapter in result.imported_source.story.chapters
        for scene in chapter.scenes
    )
    payload = {
        "source_id": result.imported_source.source_id,
        "title": result.imported_source.story.title,
        "chapters": len(result.imported_source.story.chapters),
        "scenes": len(scene_ids),
        "scene_ids": scene_ids,
        "evidence_anchor_count": len(result.imported_source.anchors),
        "extraction_result_count": len(result.extraction_results),
        "accepted_entity_count": sum(
            len(summary.accepted_entities) for summary in result.update_summaries
        ),
        "accepted_fact_count": sum(
            len(summary.accepted_facts) for summary in result.update_summaries
        ),
        "accepted_relationship_count": sum(
            len(summary.accepted_relationships) for summary in result.update_summaries
        ),
        "accepted_state_change_count": sum(
            len(summary.accepted_state_changes) for summary in result.update_summaries
        ),
        "rejected_candidate_count": sum(
            len(summary.rejected_candidates) for summary in result.update_summaries
        ),
        "timeline_changes": _timeline_changes_payload(result, source_quotes=_source_quotes(result)),
        "presentation": _presentation_snapshot_payload(result),
        "update_summaries": tuple(
            {
                "scene_id": extraction_result.scene_id,
                "accepted_entities": summary.accepted_entities,
                "accepted_facts": summary.accepted_facts,
                "accepted_relationships": summary.accepted_relationships,
                "accepted_state_changes": summary.accepted_state_changes,
                "rejected_candidates": summary.rejected_candidates,
            }
            for extraction_result, summary in zip(
                result.extraction_results,
                result.update_summaries,
                strict=True,
            )
        ),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _timeline_changes_payload(
    result: ProjectRunResult,
    *,
    source_quotes: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    """Return safe, creator-readable timeline state changes in story order."""
    chapters_by_id = {
        chapter.chapter_id: chapter for chapter in result.imported_source.story.chapters
    }
    scenes_by_id = {
        scene.scene_id: scene
        for chapter in result.imported_source.story.chapters
        for scene in chapter.scenes
    }
    changes: list[dict[str, object]] = []
    scene_change_counts: dict[str, int] = {}
    for summary in result.update_summaries:
        for state_change_id in summary.accepted_state_changes:
            state_change = result.database.retrieve_state_change(state_change_id)
            if state_change is None:
                continue
            fact = result.database.retrieve_fact(state_change.fact_id)
            if fact is None:
                continue
            evidence = result.database.retrieve_evidence(fact.evidence_id)
            if evidence is None:
                continue
            chapter = chapters_by_id.get(evidence.chapter_id)
            if chapter is None:
                continue
            scene = scenes_by_id.get(evidence.scene_id)
            if scene is None:
                continue
            entity = result.database.retrieve_entity(fact.entity_id)
            entity_name = entity.display_name if entity is not None else fact.entity_id
            if _timeline_change_should_be_hidden(
                attribute=fact.attribute,
                entity_name=entity_name,
                value=fact.value,
                source_quotes=source_quotes,
            ):
                continue
            scene_count = scene_change_counts.get(scene.scene_id, 0)
            if scene_count >= _MAX_TIMELINE_CHANGES_PER_SCENE:
                continue
            scene_change_counts[scene.scene_id] = scene_count + 1
            changes.append(
                {
                    "change_id": state_change.state_change_id,
                    "chapter_index": chapter.chapter_index,
                    "scene_index": scene.scene_index,
                    "chapter_title": _safe_display_text(chapter.title, source_quotes),
                    "scene_title": _safe_display_text(scene.title, source_quotes),
                    "entity_id": fact.entity_id,
                    "entity_name": _safe_display_text(
                        entity_name, source_quotes
                    ),
                    "attribute": _safe_display_text(fact.attribute, source_quotes),
                    "value": _safe_display_text(fact.value, source_quotes),
                }
            )

    return tuple(changes)


def _timeline_change_should_be_hidden(
    *,
    attribute: str,
    entity_name: str,
    value: str,
    source_quotes: tuple[str, ...],
) -> bool:
    """Return whether a state change is UI noise for the alpha Timeline."""
    if attribute.lower() in _TIMELINE_OMITTED_ATTRIBUTES:
        return True
    return (
        _safe_display_text(entity_name, source_quotes) == _SOURCE_BACKED_PLACEHOLDER
        or _safe_display_text(value, source_quotes) == _SOURCE_BACKED_PLACEHOLDER
    )


def _presentation_snapshot_payload(result: ProjectRunResult) -> dict[str, object]:
    """Return compact human-readable output panels for a completed run."""
    runner = AevrynProjectRunner()
    presenter = PresentationEngine()
    scene_id = runner.latest_scene_id(result)
    source_quotes = _source_quotes(result)
    return {
        "scenes": _scene_sheets_payload(
            result=result,
            runner=runner,
            presenter=presenter,
            source_quotes=source_quotes,
        ),
        "prompt_packs": _production_packs_payload(
            result=result,
            runner=runner,
            presenter=presenter,
            source_quotes=source_quotes,
        ),
        "continuity_report": _continuity_report_payload(
            runner.build_continuity_report(result)
        ),
        "export_options": _export_options_payload(),
        "characters": tuple(
            _character_profile_payload(
                presenter.character_profile(
                    runner.build_character_card_at_scene(
                        result=result,
                        character_id=character_id,
                        scene_id=scene_id,
                    )
                ),
                source_quotes=source_quotes,
            )
            for character_id in _accepted_character_ids(result)
        ),
        "world": _world_sheet_payload(
            presenter.world_sheet(
                runner.build_world_state_at_scene(
                    result=result,
                    entity_ids=_accepted_world_entity_ids(result),
                    scene_id=scene_id,
                )
            ),
            source_quotes=source_quotes,
        ),
    }


def _scene_sheets_payload(
    *,
    result: ProjectRunResult,
    runner: AevrynProjectRunner,
    presenter: PresentationEngine,
    source_quotes: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    """Return a capped set of persisted scene sheets in story order."""
    prompt_builder = CanonPromptBuilder()
    character_ids_by_scene = _accepted_character_ids_by_scene(result)
    scene_payloads: list[dict[str, object]] = []
    for chapter in result.imported_source.story.chapters:
        for scene in chapter.scenes:
            if len(scene_payloads) >= _MAX_PROJECT_SCENE_SHEETS:
                return tuple(scene_payloads)
            character_ids = character_ids_by_scene.get(scene.scene_id, ())
            context = runner.build_scene_context(
                result=result,
                scene_id=scene.scene_id,
                character_ids=character_ids,
            )
            pack = prompt_builder.build_production_pack(context)
            scene_sheet = presenter.scene_sheet(context=context, analysis=pack.analysis)
            scene_payloads.append(
                _scene_sheet_payload(
                    scene_sheet,
                    chapter_label=f"Chapter {chapter.chapter_index}",
                    source_quotes=source_quotes,
                )
            )

    return tuple(scene_payloads)


def _production_packs_payload(
    *,
    result: ProjectRunResult,
    runner: AevrynProjectRunner,
    presenter: PresentationEngine,
    source_quotes: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    """Return a capped set of persisted prompt packs in story order."""
    prompt_builder = CanonPromptBuilder()
    character_ids_by_scene = _accepted_character_ids_by_scene(result)
    prompt_payloads: list[dict[str, object]] = []
    for chapter in result.imported_source.story.chapters:
        for scene in chapter.scenes:
            if len(prompt_payloads) >= _MAX_PROJECT_PROMPT_PACKS:
                return tuple(prompt_payloads)
            character_ids = character_ids_by_scene.get(scene.scene_id, ())
            context = runner.build_scene_context(
                result=result,
                scene_id=scene.scene_id,
                character_ids=character_ids,
            )
            pack = prompt_builder.build_production_pack(context)
            scene_sheet = presenter.scene_sheet(context=context, analysis=pack.analysis)
            prompt_payloads.append(
                _production_pack_payload(
                    presenter.production_pack(pack=pack, scene=scene_sheet),
                    chapter_label=f"Chapter {chapter.chapter_index}",
                    source_quotes=source_quotes,
                )
            )

    return tuple(prompt_payloads)


def _accepted_character_ids_by_scene(
    result: ProjectRunResult,
) -> dict[str, tuple[str, ...]]:
    """Return accepted character IDs keyed by first-seen scene."""
    characters_by_scene: dict[str, dict[str, None]] = {}
    for extraction_result, summary in zip(
        result.extraction_results,
        result.update_summaries,
        strict=True,
    ):
        for entity_id in summary.accepted_entities:
            if result.database.retrieve_character(entity_id) is not None:
                characters_by_scene.setdefault(extraction_result.scene_id, {})[entity_id] = None

    return {
        scene_id: tuple(character_ids)
        for scene_id, character_ids in characters_by_scene.items()
    }


def _accepted_character_ids(result: ProjectRunResult) -> tuple[str, ...]:
    """Return accepted character IDs in first-seen scene order."""
    character_ids: dict[str, None] = {}
    for summary in result.update_summaries:
        for entity_id in summary.accepted_entities:
            if result.database.retrieve_character(entity_id) is not None:
                character_ids.setdefault(entity_id, None)

    return tuple(character_ids)


def _accepted_world_entity_ids(result: ProjectRunResult) -> tuple[str, ...]:
    """Return accepted non-character entity IDs in first-seen scene order."""
    entity_ids: dict[str, None] = {}
    for summary in result.update_summaries:
        for entity_id in summary.accepted_entities:
            entity = result.database.retrieve_entity(entity_id)
            if entity is not None and entity.entity_type != "character":
                entity_ids.setdefault(entity_id, None)

    return tuple(entity_ids)


def _source_quotes(result: ProjectRunResult) -> tuple[str, ...]:
    """Return normalized source quotes that should not become display text."""
    return tuple(
        " ".join(anchor.quote.split())
        for anchor in result.imported_source.anchors
        if anchor.quote.strip()
    )


def _character_profile_payload(
    profile: CharacterProfileView,
    *,
    source_quotes: tuple[str, ...],
) -> dict[str, object]:
    """Return a JSON-ready character profile panel."""
    return {
        "character_id": profile.character_id,
        "display_name": _safe_display_text(profile.display_name, source_quotes),
        "subtitle": _safe_display_text(profile.subtitle, source_quotes),
        "race": _section_payload(profile.race, source_quotes=source_quotes),
        "gender": _section_payload(profile.gender, source_quotes=source_quotes),
        "status": _section_payload(profile.status, source_quotes=source_quotes),
        "current_goal": _section_payload(profile.current_goal, source_quotes=source_quotes),
        "current_equipment": _section_payload(
            profile.current_equipment,
            source_quotes=source_quotes,
        ),
        "current_abilities": _section_payload(
            profile.current_abilities,
            source_quotes=source_quotes,
        ),
        "current_assets": _section_payload(profile.current_assets, source_quotes=source_quotes),
        "territory": _section_payload(profile.territory, source_quotes=source_quotes),
        "relationships": _section_payload(profile.relationships, source_quotes=source_quotes),
        "current_limitations": _section_payload(
            profile.current_limitations,
            source_quotes=source_quotes,
        ),
        "recent_changes": _section_payload(profile.recent_changes, source_quotes=source_quotes),
        "evidence_summary": profile.evidence_summary,
    }


def _scene_sheet_payload(
    scene: SceneSheetView,
    *,
    chapter_label: str,
    source_quotes: tuple[str, ...],
) -> dict[str, object]:
    """Return a JSON-ready scene sheet panel."""
    return {
        "scene_id": scene.scene_id,
        "title": _safe_display_text(scene.title, source_quotes),
        "chapter_label": chapter_label,
        "location": _section_payload(scene.location, source_quotes=source_quotes),
        "characters_present": _section_payload(
            scene.characters_present,
            source_quotes=source_quotes,
        ),
        "mood": _section_payload(scene.mood, source_quotes=source_quotes),
        "purpose": _section_payload(scene.purpose, source_quotes=source_quotes),
        "visual_highlights": _section_payload(
            scene.visual_highlights,
            source_quotes=source_quotes,
        ),
        "continuity_changes": _section_payload(
            scene.continuity_changes,
            source_quotes=source_quotes,
        ),
        "environment": _section_payload(scene.environment, source_quotes=source_quotes),
        "evidence_summary": scene.evidence_summary,
    }


def _production_pack_payload(
    pack: ProductionPackView,
    *,
    chapter_label: str,
    source_quotes: tuple[str, ...],
) -> dict[str, object]:
    """Return a JSON-ready production pack panel."""
    return {
        "scene": _scene_sheet_payload(
            pack.scene,
            chapter_label=chapter_label,
            source_quotes=source_quotes,
        ),
        "image_prompt": _section_payload(pack.image_prompt, source_quotes=source_quotes),
        "narration_prompt": _section_payload(
            pack.narration_prompt,
            source_quotes=source_quotes,
        ),
        "camera_prompt": _section_payload(pack.camera_prompt, source_quotes=source_quotes),
        "animation_prompt": _section_payload(
            pack.animation_prompt,
            source_quotes=source_quotes,
        ),
    }


def _continuity_report_payload(report: ContinuityReport) -> dict[str, object]:
    """Return a JSON-ready continuity report without exact source prose."""
    return {
        "source_id": report.source_id,
        "scenes": tuple(
            _continuity_scene_payload(scene)
            for scene in report.scenes
        ),
    }


def _continuity_scene_payload(scene: ContinuitySceneReport) -> dict[str, object]:
    """Return one JSON-ready continuity scene."""
    return {
        "scene_id": scene.scene_id,
        "new": tuple(_continuity_record_payload(record) for record in scene.new),
        "updated": tuple(_continuity_record_payload(record) for record in scene.updated),
        "still_known": tuple(
            _continuity_record_payload(record) for record in scene.still_known[:8]
        ),
        "invalidated": tuple(
            _continuity_record_payload(record) for record in scene.invalidated
        ),
    }


def _continuity_record_payload(record: ContinuityRecord) -> dict[str, object]:
    """Return one JSON-ready continuity record without source prose."""
    return {
        "record_id": record.record_id,
        "record_type": record.record_type,
        "description": record.description,
        "evidence_id": record.evidence_id,
        "chapter_id": record.chapter_id,
        "scene_id": record.scene_id,
    }


def _export_options_payload() -> tuple[dict[str, object], ...]:
    """Return alpha-safe export availability without serialized export content."""
    return (
        {
            "export_kind": "character_profile",
            "formats": ("markdown",),
            "label": "Character Profile",
        },
        {
            "export_kind": "scene_sheet",
            "formats": ("markdown",),
            "label": "Scene Sheet",
        },
        {
            "export_kind": "production_pack",
            "formats": ("markdown",),
            "label": "Production Pack",
        },
        {
            "export_kind": "prompt_bundle",
            "formats": ("markdown", "json", "csv"),
            "label": "Prompt Bundle",
        },
        {
            "export_kind": "continuity_report",
            "formats": ("markdown", "json"),
            "label": "Continuity Report",
        },
    )


def _world_sheet_payload(
    world: WorldSheetView,
    *,
    source_quotes: tuple[str, ...],
) -> dict[str, object]:
    """Return a JSON-ready world sheet panel."""
    return {
        "chapter_label": world.chapter_label,
        "entity_sections": tuple(
            _section_payload(section, source_quotes=source_quotes)
            for section in world.entity_sections
        ),
        "evidence_summary": world.evidence_summary,
    }


def _section_payload(
    section: PresentationSection,
    *,
    source_quotes: tuple[str, ...],
) -> dict[str, object]:
    """Return a JSON-ready presentation section without exact source prose."""
    return {
        "title": section.title,
        "items": tuple(
            _safe_display_text(item, source_quotes)
            for item in section.items
        ),
    }


def _safe_display_text(value: str, source_quotes: tuple[str, ...]) -> str:
    """Return display text while suppressing exact long source-prose echoes."""
    normalized = " ".join(value.split())
    for quote in source_quotes:
        if len(quote) >= 20 and (
            quote in normalized or (len(normalized) >= 20 and normalized in quote)
        ):
            return "Source-backed detail available through evidence controls."

    return normalized


def _error_summary(error: Exception) -> str:
    """Return a short stable worker error summary."""
    message = str(error).strip()
    if message.startswith("Unknown evidence anchor:"):
        return (
            "Import evidence could not be matched during AI extraction. "
            "Review the import structure, then retry processing. If it repeats, "
            "split the import into smaller chapter batches."
        )
    if message.startswith("Conflicting fact:"):
        return (
            "AI extraction produced conflicting canon facts. Retry processing. "
            "If it repeats, review the import structure or split the import into "
            "smaller chapter batches."
        )
    if message == "World sheet section titles must be unique.":
        return (
            "World sheet output contained duplicate sections. Aevryn merged matching "
            "sections; retry processing."
        )
    if message == "OpenAI extraction request timed out.":
        return (
            "AI extraction timed out while reading the provider response. Retry with "
            "a smaller chapter batch or increase the provider timeout for large imports."
        )
    if not message:
        return error.__class__.__name__
    return message[:500]


def _elapsed_ms(started_at: float) -> float:
    """Return rounded elapsed milliseconds for metadata-only worker logs."""
    return round((time.perf_counter() - started_at) * 1000, 3)


def _log_worker_job_event(
    *,
    job: BackgroundJob,
    status: str,
    duration_ms: float,
    error_summary: str,
    snapshot_count: int,
) -> None:
    """Emit metadata-only worker job timing."""
    extra: dict[str, object] = {
        "workflow_kind": "worker_processing",
        "workflow_status": status,
        "duration_ms": duration_ms,
        "job_id": job.job_id,
        "run_id": job.run_id,
        "project_id": job.project_id,
        "story_id": job.story_id,
        "import_id": job.import_id,
        "snapshot_count": snapshot_count,
    }
    if error_summary:
        extra["error_summary"] = error_summary
    logger.info("background_worker_job_completed", extra=extra)


def _log_snapshot_event(*, snapshot: SnapshotRecord, duration_ms: float) -> None:
    """Emit metadata-only snapshot creation timing."""
    logger.info(
        "background_snapshot_stored",
        extra={
            "workflow_kind": "snapshot_creation",
            "workflow_status": "succeeded",
            "duration_ms": duration_ms,
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_kind": snapshot.snapshot_kind,
            "project_id": snapshot.project_id,
            "story_id": snapshot.story_id,
            "run_id": snapshot.run_id,
            "content_type": snapshot.content_type,
        },
    )

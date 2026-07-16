"""Background job submission and worker execution services."""

from __future__ import annotations

import json
import logging
import re
import tempfile
import time
from collections.abc import Mapping
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

        try:
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
        "ungrounded_extraction_candidate_count": sum(
            extraction_result.rejected_candidate_count
            for extraction_result in result.extraction_results
        ),
        "translation": _translation_snapshot_payload(result),
        "entity_resolution": _entity_resolution_snapshot_payload(result),
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


def _translation_snapshot_payload(result: ProjectRunResult) -> dict[str, object]:
    """Return metadata-only Translation Foundation snapshot details."""
    return {
        "unit_count": len(result.translation_units),
        "issue_count": sum(len(unit.issues) for unit in result.translation_units),
        "units": tuple(
            {
                "unit_id": unit.unit_id,
                "source_language": unit.source_language,
                "target_language": unit.target_language,
                "mode": unit.mode,
                "source_chapter_id": unit.source_chapter_id,
                "source_scene_id": unit.source_scene_id,
                "source_evidence_anchor_ids": unit.source_evidence_anchor_ids,
                "issue_count": len(unit.issues),
                "issues": tuple(
                    {
                        "issue_code": _translation_issue_code(issue.issue_code),
                        "issue_label": _translation_issue_label(
                            issue.issue_code,
                            possible_meaning_count=issue.possible_meaning_count,
                        ),
                        "term_kind": issue.term_kind,
                        "evidence_anchor_count": len(issue.evidence_anchor_ids),
                        "possible_meaning_count": issue.possible_meaning_count,
                    }
                    for issue in unit.issues
                ),
            }
            for unit in result.translation_units
        ),
    }


def _translation_issue_code(value: str) -> str:
    """Return a stable translation issue code without storing source terms."""
    if value == "translation_review_required":
        return value
    return "translation_review_required"


def _translation_issue_label(
    value: str,
    *,
    possible_meaning_count: int = 0,
) -> str:
    """Return metadata-only translation review label."""
    if (
        _translation_issue_code(value) == "translation_review_required"
        and possible_meaning_count > 1
    ):
        return "Multiple meanings need review"
    if _translation_issue_code(value) == "translation_review_required":
        return "Glossary term needs review"
    return "Translation needs review"


def _entity_resolution_snapshot_payload(result: ProjectRunResult) -> dict[str, object]:
    """Return metadata-only Entity Resolution snapshot details."""
    status_counts = {
        "resolved": 0,
        "ambiguous": 0,
        "unresolved": 0,
    }
    for decision in result.identity_resolutions:
        status_counts[decision.status] += 1
    return {
        "decision_count": len(result.identity_resolutions),
        "status_counts": status_counts,
        "decisions": tuple(
            {
                "status": decision.status,
                "entity_id": decision.entity_id,
                "confidence": decision.confidence,
                "evidence_anchor_id": decision.reference.evidence_anchor_id,
                "chapter_id": decision.reference.chapter_id,
                "scene_id": decision.reference.scene_id,
                "reference_kind": _identity_reference_kind(decision.reference.text),
                "reference_label": _identity_reference_label(decision.reference.text),
                "candidate_count": len(decision.candidates),
                "reason": _identity_snapshot_reason(decision.status),
            }
            for decision in result.identity_resolutions
        ),
    }


def _identity_reference_kind(value: str) -> str:
    """Classify an identity surface reference without storing source prose."""
    normalized = value.strip().lower()
    words = tuple(
        part
        for part in "".join(
            character.lower() if character.isalnum() else " "
            for character in normalized.replace("-", " ")
        ).split()
        if part
    )
    if words in {
        ("he",),
        ("him",),
        ("his",),
        ("she",),
        ("her",),
        ("hers",),
        ("they",),
        ("them",),
        ("their",),
        ("theirs",),
    }:
        return "pronoun"
    if not words:
        return "unknown"
    if len(words) == 1:
        return "name"
    if words[0] in {"the", "a", "an"}:
        words = words[1:]
    title_words = {
        "captain",
        "commander",
        "engineer",
        "general",
        "leader",
        "officer",
        "student",
        "teacher",
    }
    if words and (words[0] in title_words or words[-1] in title_words):
        return "title"
    return "description"


def _identity_reference_label(value: str) -> str:
    """Return creator-facing review copy for an identity surface reference."""
    kind = _identity_reference_kind(value)
    if kind == "pronoun":
        return "Pronoun reference"
    if kind == "name":
        return "Name reference"
    if kind == "title":
        return "Title reference"
    if kind == "description":
        return "Description reference"
    return "Reference needs review"


def _identity_snapshot_reason(status: str) -> str:
    """Return stable metadata-only identity review copy for persisted snapshots."""
    if status == "ambiguous":
        return "Identity has multiple possible matches and needs review."
    if status == "unresolved":
        return "Identity could not be matched with enough evidence."
    return "Identity was resolved with available evidence."


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
    display_names = _entity_display_names(result)
    return {
        "scenes": _scene_sheets_payload(
            result=result,
            runner=runner,
            presenter=presenter,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "prompt_packs": _production_packs_payload(
            result=result,
            runner=runner,
            presenter=presenter,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "continuity_report": _continuity_report_payload(
            runner.build_continuity_report(result),
            display_names=display_names,
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
                display_names=display_names,
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
            display_names=display_names,
        ),
    }


def _scene_sheets_payload(
    *,
    result: ProjectRunResult,
    runner: AevrynProjectRunner,
    presenter: PresentationEngine,
    source_quotes: tuple[str, ...],
    display_names: Mapping[str, str],
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
                    display_names=display_names,
                )
            )

    return tuple(scene_payloads)


def _production_packs_payload(
    *,
    result: ProjectRunResult,
    runner: AevrynProjectRunner,
    presenter: PresentationEngine,
    source_quotes: tuple[str, ...],
    display_names: Mapping[str, str],
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
                    display_names=display_names,
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


def _entity_display_names(result: ProjectRunResult) -> dict[str, str]:
    """Return accepted entity display names for creator-facing presentation."""
    display_names: dict[str, str] = {}
    for summary in result.update_summaries:
        for entity_id in summary.accepted_entities:
            entity = result.database.retrieve_entity(entity_id)
            if entity is None:
                continue
            display_names[entity.entity_id] = entity.display_name
            display_names[entity.entity_id.lower()] = entity.display_name
    return display_names


def _character_profile_payload(
    profile: CharacterProfileView,
    *,
    source_quotes: tuple[str, ...],
    display_names: Mapping[str, str],
) -> dict[str, object]:
    """Return a JSON-ready character profile panel."""
    return {
        "character_id": profile.character_id,
        "display_name": _safe_display_text(
            profile.display_name,
            source_quotes,
            display_names=display_names,
        ),
        "subtitle": _safe_display_text(
            profile.subtitle,
            source_quotes,
            display_names=display_names,
        ),
        "aliases": _section_payload(
            profile.aliases,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "titles": _section_payload(
            profile.titles,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "descriptions": _section_payload(
            profile.descriptions,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "race": _section_payload(
            profile.race,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "gender": _section_payload(
            profile.gender,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "status": _section_payload(
            profile.status,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "current_goal": _section_payload(
            profile.current_goal,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "current_equipment": _section_payload(
            profile.current_equipment,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "current_abilities": _section_payload(
            profile.current_abilities,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "current_assets": _section_payload(
            profile.current_assets,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "territory": _section_payload(
            profile.territory,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "relationships": _section_payload(
            profile.relationships,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "current_limitations": _section_payload(
            profile.current_limitations,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "recent_changes": _section_payload(
            profile.recent_changes,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "evidence_summary": profile.evidence_summary,
    }


def _scene_sheet_payload(
    scene: SceneSheetView,
    *,
    chapter_label: str,
    source_quotes: tuple[str, ...],
    display_names: Mapping[str, str],
) -> dict[str, object]:
    """Return a JSON-ready scene sheet panel."""
    return {
        "scene_id": scene.scene_id,
        "title": _safe_display_text(
            scene.title,
            source_quotes,
            display_names=display_names,
        ),
        "chapter_label": chapter_label,
        "location": _section_payload(
            scene.location,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "characters_present": _section_payload(
            scene.characters_present,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "mood": _section_payload(
            scene.mood,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "purpose": _section_payload(
            scene.purpose,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "visual_highlights": _section_payload(
            scene.visual_highlights,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "continuity_changes": _section_payload(
            scene.continuity_changes,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "environment": _section_payload(
            scene.environment,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "evidence_summary": scene.evidence_summary,
    }


def _production_pack_payload(
    pack: ProductionPackView,
    *,
    chapter_label: str,
    source_quotes: tuple[str, ...],
    display_names: Mapping[str, str],
) -> dict[str, object]:
    """Return a JSON-ready production pack panel."""
    return {
        "scene": _scene_sheet_payload(
            pack.scene,
            chapter_label=chapter_label,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "image_prompt": _section_payload(
            pack.image_prompt,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "narration_prompt": _section_payload(
            pack.narration_prompt,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "camera_prompt": _section_payload(
            pack.camera_prompt,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
        "animation_prompt": _section_payload(
            pack.animation_prompt,
            source_quotes=source_quotes,
            display_names=display_names,
        ),
    }


def _continuity_report_payload(
    report: ContinuityReport,
    *,
    display_names: Mapping[str, str],
) -> dict[str, object]:
    """Return a JSON-ready continuity report without exact source prose."""
    return {
        "source_id": report.source_id,
        "scenes": tuple(
            _continuity_scene_payload(scene, display_names=display_names)
            for scene in report.scenes
        ),
    }


def _continuity_scene_payload(
    scene: ContinuitySceneReport,
    *,
    display_names: Mapping[str, str],
) -> dict[str, object]:
    """Return one JSON-ready continuity scene."""
    return {
        "scene_id": scene.scene_id,
        "new": tuple(
            _continuity_record_payload(record, display_names=display_names)
            for record in scene.new
        ),
        "updated": tuple(
            _continuity_record_payload(record, display_names=display_names)
            for record in scene.updated
        ),
        "still_known": tuple(
            _continuity_record_payload(record, display_names=display_names)
            for record in scene.still_known[:8]
        ),
        "invalidated": tuple(
            _continuity_record_payload(record, display_names=display_names)
            for record in scene.invalidated
        ),
    }


def _continuity_record_payload(
    record: ContinuityRecord,
    *,
    display_names: Mapping[str, str],
) -> dict[str, object]:
    """Return one JSON-ready continuity record without source prose."""
    return {
        "record_id": record.record_id,
        "record_type": record.record_type,
        "description": _humanized_continuity_description(
            record.description,
            display_names=display_names,
        ),
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
    display_names: Mapping[str, str],
) -> dict[str, object]:
    """Return a JSON-ready world sheet panel."""
    return {
        "chapter_label": world.chapter_label,
        "entity_sections": tuple(
            _section_payload(
                section,
                source_quotes=source_quotes,
                display_names=display_names,
            )
            for section in world.entity_sections
        ),
        "evidence_summary": world.evidence_summary,
    }


def _section_payload(
    section: PresentationSection,
    *,
    source_quotes: tuple[str, ...],
    display_names: Mapping[str, str],
) -> dict[str, object]:
    """Return a JSON-ready presentation section without exact source prose."""
    return {
        "title": _humanized_display_text(section.title, display_names=display_names),
        "items": tuple(
            safe_item
            for item in section.items
            if (
                safe_item := _safe_display_text(
                    item,
                    source_quotes,
                    display_names=display_names,
                )
            ) != _SOURCE_BACKED_PLACEHOLDER
        ),
    }


def _safe_display_text(
    value: str,
    source_quotes: tuple[str, ...],
    *,
    display_names: Mapping[str, str] | None = None,
) -> str:
    """Return display text while suppressing exact long source-prose echoes."""
    normalized = " ".join(value.split())
    for quote in source_quotes:
        if len(quote) >= 20 and (
            quote in normalized or (len(normalized) >= 20 and normalized in quote)
        ):
            return _SOURCE_BACKED_PLACEHOLDER

    return _humanized_display_text(normalized, display_names=display_names)


def _humanized_continuity_description(
    description: str,
    *,
    display_names: Mapping[str, str],
) -> str:
    """Return creator-readable continuity text from engine descriptions."""
    normalized = " ".join(description.split())
    if normalized.startswith("Entity accepted: "):
        entity_id = normalized.removeprefix("Entity accepted: ")
        return f"New entity: {_humanized_entity_id(entity_id, display_names=display_names)}"
    if normalized.lower().startswith("state valid from "):
        return "State changed at this scene."
    if " = " in normalized:
        left, value = normalized.split(" = ", 1)
        parts = left.split(" ", 1)
        if len(parts) == 2:
            entity_id, attribute = parts
            return (
                f"{_humanized_entity_id(entity_id, display_names=display_names)} "
                f"{_humanized_attribute(attribute)}: "
                f"{_humanized_display_text(value, display_names=display_names)}"
            )
    relationship_parts = normalized.split(" ")
    if len(relationship_parts) == 3:
        source_id, relationship_type, target_id = relationship_parts
        return (
            f"{_humanized_entity_id(source_id, display_names=display_names)} "
            f"{_humanized_relationship(relationship_type)} "
            f"{_humanized_entity_id(target_id, display_names=display_names)}"
        )
    return _humanized_display_text(normalized, display_names=display_names)


def _humanized_display_text(
    value: str,
    *,
    display_names: Mapping[str, str] | None = None,
) -> str:
    """Return display text with common machine tokens made readable."""
    display_names = display_names or {}
    normalized = " ".join(value.split())
    if _looks_like_anchor_derived_text(normalized):
        return "State changed at this scene."
    relationship_text = _humanized_relationship_line(
        normalized,
        display_names=display_names,
    )
    if relationship_text is not None:
        return relationship_text
    normalized = _strip_internal_entity_suffixes(normalized)
    normalized = _replace_entity_tokens(normalized, display_names=display_names)
    if _looks_like_machine_id(normalized):
        return _humanized_entity_id(normalized, display_names=display_names)
    if " " not in normalized and "_" in normalized:
        return normalized.replace("_", " ")
    return normalized


def _humanized_entity_id(
    entity_id: str,
    *,
    display_names: Mapping[str, str] | None = None,
) -> str:
    """Return a readable label for common Aevryn entity IDs."""
    display_names = display_names or {}
    display_name = display_names.get(entity_id) or display_names.get(entity_id.lower())
    if display_name:
        return display_name
    if _looks_like_short_entity_id(entity_id):
        return f"Entity {entity_id[1:]}"
    prefixes = (
        "character_",
        "item_",
        "location_",
        "organization_",
        "vehicle_",
        "skill_",
        "system_",
        "fact_",
        "state_",
        "event_",
        "rel_",
    )
    text = entity_id
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text.removeprefix(prefix)
            break
    return _title_preserving_acronyms(text.replace("_", " "))


def _humanized_attribute(attribute: str) -> str:
    """Return a readable attribute label."""
    return attribute.replace("_", " ")


def _humanized_relationship(relationship_type: str) -> str:
    """Return a readable relationship phrase."""
    phrase = relationship_type.replace("_", " ")
    if phrase in {"located in", "under entity"}:
        return "is located in"
    if phrase in {"owns", "owned by"}:
        return "is connected to"
    if phrase == "member of":
        return "is a member of"
    return phrase


def _humanized_relationship_line(
    value: str,
    *,
    display_names: Mapping[str, str],
) -> str | None:
    """Return a readable relationship line when value is source-relation-target."""
    parts = value.split(" ")
    if len(parts) != 3:
        return None
    source_id, relationship_type, target_id = parts
    if not (
        _looks_like_entity_reference(source_id, display_names=display_names)
        and _looks_like_entity_reference(target_id, display_names=display_names)
    ):
        return None
    source_label = _humanized_entity_id(source_id, display_names=display_names)
    target_label = _humanized_entity_id(target_id, display_names=display_names)
    if source_label == target_label:
        return ""
    return (
        f"{source_label} "
        f"{_humanized_relationship(relationship_type)} "
        f"{target_label}"
    )


def _looks_like_machine_id(value: str) -> bool:
    """Return whether a value is likely an internal Aevryn ID."""
    return _looks_like_short_entity_id(value) or ("_" in value and any(
        value.startswith(prefix)
        for prefix in (
            "character_",
            "item_",
            "location_",
            "organization_",
            "vehicle_",
            "skill_",
            "system_",
            "fact_",
            "state_",
            "event_",
            "rel_",
        )
    ))


def _looks_like_entity_reference(
    value: str,
    *,
    display_names: Mapping[str, str],
) -> bool:
    """Return whether a token is an entity reference known to presentation."""
    return (
        value in display_names
        or value.lower() in display_names
        or _looks_like_machine_id(value)
    )


def _looks_like_short_entity_id(value: str) -> bool:
    """Return whether a value is an extraction-style entity token such as E1."""
    return re.fullmatch(r"[Ee]\d{1,4}", value.strip()) is not None


def _looks_like_anchor_derived_text(value: str) -> bool:
    """Return whether text is an anchor/event ID expanded into prose."""
    lowered = value.lower()
    return (
        lowered.startswith("state valid from event ")
        or " aevryn import bundle chapter " in lowered
        or " evidence aevryn import bundle " in lowered
    )


def _strip_internal_entity_suffixes(value: str) -> str:
    """Remove parenthesized internal entity IDs from visible prompt lines."""
    return re.sub(
        r"\s+\(([A-Za-z]\d{1,4}|(?:character|item|location|organization|vehicle|skill|system)_[A-Za-z0-9_]+)\)",
        "",
        value,
    )


def _replace_entity_tokens(
    value: str,
    *,
    display_names: Mapping[str, str],
) -> str:
    """Replace standalone internal entity IDs with accepted display names."""

    def replacement(match: re.Match[str]) -> str:
        token = match.group(0)
        return _humanized_entity_id(token, display_names=display_names)

    return re.sub(
        r"(?<![A-Za-z0-9_])(?:[Ee]\d{1,4}|(?:character|item|location|organization|vehicle|skill|system)_[A-Za-z0-9_]+)(?![A-Za-z0-9_])",
        replacement,
        value,
    )


def _title_preserving_acronyms(value: str) -> str:
    """Title-case labels while preserving short all-caps-like tokens."""
    words = []
    for word in value.split():
        if len(word) <= 3 and any(character.isdigit() for character in word):
            words.append(word.upper())
        else:
            words.append(word.capitalize())
    return " ".join(words)


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

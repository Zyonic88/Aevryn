"""Project Manager workflow runner for proof-stage SceneSmith commands."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scenesmith.canon import CanonDatabase, CanonUpdater, CanonUpdateSummary
from scenesmith.characters import CanonCharacterCard, CharacterCardBuilder
from scenesmith.extraction import (
    EntityExtractionEngine,
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractedStateChange,
    ExtractionResult,
    SceneEvidenceAnchor,
    SceneExtractionInput,
)
from scenesmith.extraction.engine import SceneExtractor
from scenesmith.importing import EvidenceAnchor, ImportedSource, StoryImporter
from scenesmith.prompts import CanonPromptBuilder, PromptBundle
from scenesmith.scenes import CanonSceneContext, SceneContextBuilder
from scenesmith.world import WorldState, WorldStateBuilder

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProjectRunResult:
    """Result of running the proof-stage project workflow.

    Attributes:
        imported_source: Story Import output for the source text.
        database: In-memory Canon Database populated by accepted candidates.
        extraction_results: Candidate extraction results in scene order.
        update_summaries: Canon update summaries in scene order.
    """

    imported_source: ImportedSource
    database: CanonDatabase
    extraction_results: tuple[ExtractionResult, ...]
    update_summaries: tuple[CanonUpdateSummary, ...]


@dataclass(frozen=True, slots=True)
class ContinuityRecord:
    """One continuity report entry derived from accepted Canon updates."""

    record_id: str
    record_type: str
    description: str
    evidence_id: str = ""
    chapter_id: str = ""
    scene_id: str = ""
    evidence_quote: str = ""


@dataclass(frozen=True, slots=True)
class ContinuitySceneReport:
    """Continuity changes for one scene in story order."""

    scene_id: str
    new: tuple[ContinuityRecord, ...] = ()
    updated: tuple[ContinuityRecord, ...] = ()
    still_known: tuple[ContinuityRecord, ...] = ()
    invalidated: tuple[ContinuityRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class ContinuityReport:
    """Project-level continuity report for a proof workflow run."""

    source_id: str
    scenes: tuple[ContinuitySceneReport, ...]


class SceneSmithProjectRunner:
    """Coordinate existing systems for local proof workflows.

    The runner does not own canon truth, extraction logic, import parsing, prompt
    generation, or export formatting. It only wires the existing systems together
    for CLI and test workflows.
    """

    def import_text_file(
        self,
        path: Path,
        source_id: str,
        title: str | None = None,
    ) -> ImportedSource:
        """Import a UTF-8 text file.

        Parameters:
            path: Source file path.
            source_id: Stable source identifier.
            title: Optional story title. Defaults to the file stem.

        Returns:
            Imported source structure with evidence anchors.

        Raises:
            OSError: If the source file cannot be read.
            ValueError: If Story Import rejects the source content.
        """
        return StoryImporter().import_text(
            source_id=source_id,
            title=title or path.stem,
            text=path.read_text(encoding="utf-8"),
        )

    def run_demo_text_file(
        self,
        path: Path,
        source_id: str,
        title: str | None = None,
    ) -> ProjectRunResult:
        """Run the deterministic proof pipeline over a text file.

        Parameters:
            path: Source file path.
            source_id: Stable source identifier.
            title: Optional story title. Defaults to the file stem.

        Returns:
            Project run result containing imported source, candidates, and Canon.
        """
        imported_source = self.import_text_file(path=path, source_id=source_id, title=title)
        return self.run_demo_imported_source(imported_source)

    def run_demo_imported_source(self, imported_source: ImportedSource) -> ProjectRunResult:
        """Run deterministic extraction and canon updating over imported source.

        Parameters:
            imported_source: Story Import output.

        Returns:
            Project run result containing imported source, candidates, and Canon.
        """
        return self.run_imported_source(
            imported_source=imported_source,
            extractor=_KeywordDemoExtractor(),
        )

    def run_imported_source(
        self,
        imported_source: ImportedSource,
        extractor: SceneExtractor,
    ) -> ProjectRunResult:
        """Run extraction and canon updating over imported source.

        Parameters:
            imported_source: Story Import output.
            extractor: Evidence-bounded extractor that proposes candidates.

        Returns:
            Project run result containing imported source, candidates, and Canon.
        """
        self._require_imported_scenes(imported_source)
        extraction_results = EntityExtractionEngine(
            extractor=extractor
        ).extract_imported_source(imported_source)
        database = CanonDatabase()
        updater = CanonUpdater(database=database)
        anchors_by_scene = _anchors_by_scene(imported_source.anchors)
        summaries = tuple(
            updater.apply_extraction_result(
                result=extraction_result,
                anchors=anchors_by_scene.get(extraction_result.scene_id, ()),
            )
            for extraction_result in extraction_results
        )
        result = ProjectRunResult(
            imported_source=imported_source,
            database=database,
            extraction_results=extraction_results,
            update_summaries=summaries,
        )
        logger.info(
            "Ran imported source workflow",
            extra={
                "source_id": imported_source.source_id,
                "scene_count": len(extraction_results),
                "accepted_entities": sum(
                    len(summary.accepted_entities) for summary in summaries
                ),
                "rejected_candidates": sum(
                    len(summary.rejected_candidates) for summary in summaries
                ),
            },
        )
        return result

    def run_imported_scene(
        self,
        imported_source: ImportedSource,
        extractor: SceneExtractor,
        scene_id: str | None = None,
    ) -> ProjectRunResult:
        """Run extraction and canon updating over one imported scene.

        Parameters:
            imported_source: Story Import output.
            extractor: Evidence-bounded extractor that proposes candidates.
            scene_id: Optional scene ID. Defaults to latest imported scene.

        Returns:
            Project run result containing one scene extraction result and Canon.

        Raises:
            ValueError: If the requested scene is unknown.
        """
        self._require_imported_scenes(imported_source)
        requested_scene_id = scene_id or self._latest_scene_id_from_source(imported_source)
        extraction_input = self.build_scene_extraction_input(
            imported_source=imported_source,
            scene_id=requested_scene_id,
        )
        anchors = self._anchors_for_scene(
            imported_source=imported_source,
            scene_id=requested_scene_id,
        )
        extraction_result = EntityExtractionEngine(extractor=extractor).extract_scene(
            scene_id=extraction_input.scene_id,
            text=extraction_input.text,
            anchors=anchors,
        )
        if extraction_result.scene_id != requested_scene_id:
            raise ValueError(
                "Extractor returned candidates for the wrong scene: "
                f"{extraction_result.scene_id}"
            )
        database = CanonDatabase()
        updater = CanonUpdater(database=database)
        summary = updater.apply_extraction_result(
            result=extraction_result,
            anchors=anchors,
        )
        result = ProjectRunResult(
            imported_source=imported_source,
            database=database,
            extraction_results=(extraction_result,),
            update_summaries=(summary,),
        )
        logger.info(
            "Ran imported scene workflow",
            extra={
                "source_id": imported_source.source_id,
                "scene_id": requested_scene_id,
                "accepted_entities": len(summary.accepted_entities),
                "rejected_candidates": len(summary.rejected_candidates),
            },
        )
        return result

    def build_scene_extraction_input(
        self,
        imported_source: ImportedSource,
        scene_id: str | None = None,
    ) -> SceneExtractionInput:
        """Build evidence-bounded extraction input for one imported scene.

        Parameters:
            imported_source: Story Import output.
            scene_id: Optional scene ID. Defaults to latest imported scene.

        Returns:
            Scene extraction input with text and evidence anchors.

        Raises:
            ValueError: If the requested scene is unknown.
        """
        requested_scene_id = scene_id or self._latest_scene_id_from_source(imported_source)
        for chapter in imported_source.story.chapters:
            for scene in chapter.scenes:
                if scene.scene_id == requested_scene_id:
                    anchors = tuple(
                        anchor
                        for anchor in imported_source.anchors
                        if anchor.scene_id == requested_scene_id
                    )
                    return SceneExtractionInput(
                        scene_id=scene.scene_id,
                        text="\n\n".join(scene.paragraphs),
                        evidence_anchor_ids=tuple(anchor.anchor_id for anchor in anchors),
                        evidence_anchors=tuple(
                            SceneEvidenceAnchor(
                                anchor_id=anchor.anchor_id,
                                quote=anchor.quote,
                            )
                            for anchor in anchors
                        ),
                    )

        raise ValueError(f"Unknown scene: {requested_scene_id}")

    def build_character_card(
        self,
        result: ProjectRunResult,
        character_id: str,
        chapter_index: int | None = None,
    ) -> CanonCharacterCard:
        """Build a character card from a project run result.

        Parameters:
            result: Completed project run result.
            character_id: Character entity ID.
            chapter_index: Optional chapter index. Defaults to latest chapter.

        Returns:
            Canon-backed character card.

        Raises:
            ValueError: If the character is unknown.
        """
        return CharacterCardBuilder(result.database).build_card(
            character_id=character_id,
            chapter_index=chapter_index or self.latest_chapter_index(result),
        )

    def build_scene_context(
        self,
        result: ProjectRunResult,
        scene_id: str | None = None,
        character_ids: Sequence[str] = ("character_mark",),
    ) -> CanonSceneContext:
        """Build scene context from a project run result.

        Parameters:
            result: Completed project run result.
            scene_id: Optional scene ID. Defaults to latest imported scene.
            character_ids: Character IDs present in the requested scene.

        Returns:
            Canon-backed scene context.

        Raises:
            ValueError: If the scene or a requested character is unknown.
        """
        return SceneContextBuilder(
            database=result.database,
            character_cards=CharacterCardBuilder(result.database),
        ).build_context(
            imported_source=result.imported_source,
            scene_id=scene_id or self.latest_scene_id(result),
            character_ids=self._dedupe_ids(character_ids),
        )

    def build_prompt_bundle(
        self,
        result: ProjectRunResult,
        scene_id: str | None = None,
        character_ids: Sequence[str] = ("character_mark",),
    ) -> PromptBundle:
        """Build a prompt bundle from project scene context.

        Parameters:
            result: Completed project run result.
            scene_id: Optional scene ID. Defaults to latest imported scene.
            character_ids: Character IDs present in the requested scene.

        Returns:
            Deterministic prompt bundle built from accepted canon.
        """
        context = self.build_scene_context(
            result=result,
            scene_id=scene_id,
            character_ids=character_ids,
        )
        return CanonPromptBuilder().build_bundle(context)

    def build_world_state(
        self,
        result: ProjectRunResult,
        entity_ids: Sequence[str],
        chapter_index: int | None = None,
    ) -> WorldState:
        """Build world state from a project run result.

        Parameters:
            result: Completed project run result.
            entity_ids: World entity IDs to reconstruct.
            chapter_index: Optional chapter index. Defaults to latest chapter.

        Returns:
            Canon-backed world state.
        """
        return WorldStateBuilder(database=result.database).build_state(
            entity_ids=self._dedupe_ids(entity_ids),
            chapter_index=chapter_index or self.latest_chapter_index(result),
        )

    def build_continuity_report(self, result: ProjectRunResult) -> ContinuityReport:
        """Build a continuity report from accepted Canon updates.

        Parameters:
            result: Completed project run result.

        Returns:
            Continuity report separating new, updated, still-known, and
            invalidated records by scene.
        """
        known_records: dict[str, ContinuityRecord] = {}
        latest_fact_by_key: dict[tuple[str, str], ContinuityRecord] = {}
        scene_reports: list[ContinuitySceneReport] = []

        for extraction_result, summary in zip(
            result.extraction_results,
            result.update_summaries,
            strict=True,
        ):
            new_records: list[ContinuityRecord] = []
            updated_records: list[ContinuityRecord] = []
            invalidated_records: list[ContinuityRecord] = []
            scene_changed_ids: set[str] = set()

            for entity_id in summary.accepted_entities:
                record = ContinuityRecord(
                    record_id=entity_id,
                    record_type="entity",
                    description=f"Entity accepted: {entity_id}",
                )
                self._classify_continuity_record(
                    record=record,
                    known_records=known_records,
                    new_records=new_records,
                    scene_changed_ids=scene_changed_ids,
                )

            for fact_id in summary.accepted_facts:
                fact = result.database.retrieve_fact(fact_id)
                if fact is None:
                    continue

                record = ContinuityRecord(
                    record_id=fact.fact_id,
                    record_type="fact",
                    description=f"{fact.entity_id} {fact.attribute} = {fact.value}",
                    evidence_id=fact.evidence_id,
                )
                record = self._with_evidence_context(result, record)
                fact_key = (fact.entity_id, fact.attribute)
                previous_fact = latest_fact_by_key.get(fact_key)
                if previous_fact is None:
                    new_records.append(record)
                elif previous_fact.record_id != record.record_id:
                    updated_records.append(record)
                    invalidated_records.append(previous_fact)
                scene_changed_ids.add(record.record_id)
                known_records[record.record_id] = record
                latest_fact_by_key[fact_key] = record

            for relationship_id in summary.accepted_relationships:
                relationship = result.database.retrieve_relationship(relationship_id)
                if relationship is None:
                    continue

                record = ContinuityRecord(
                    record_id=relationship.relationship_id,
                    record_type="relationship",
                    description=(
                        f"{relationship.source_entity_id} "
                        f"{relationship.relationship_type} "
                        f"{relationship.target_entity_id}"
                    ),
                    evidence_id=relationship.evidence_id,
                )
                record = self._with_evidence_context(result, record)
                self._classify_continuity_record(
                    record=record,
                    known_records=known_records,
                    new_records=new_records,
                    scene_changed_ids=scene_changed_ids,
                )

            for state_change_id in summary.accepted_state_changes:
                state_change = result.database.retrieve_state_change(state_change_id)
                if state_change is None:
                    continue

                fact = result.database.retrieve_fact(state_change.fact_id)
                evidence_id = fact.evidence_id if fact is not None else ""
                record = ContinuityRecord(
                    record_id=state_change.state_change_id,
                    record_type="state_change",
                    description=f"State valid from {state_change.valid_from_event_id}",
                    evidence_id=evidence_id,
                )
                record = self._with_evidence_context(result, record)
                self._classify_continuity_record(
                    record=record,
                    known_records=known_records,
                    new_records=new_records,
                    scene_changed_ids=scene_changed_ids,
                )

            still_known = tuple(
                record
                for record_id, record in sorted(known_records.items())
                if record_id not in scene_changed_ids
            )
            scene_reports.append(
                ContinuitySceneReport(
                    scene_id=extraction_result.scene_id,
                    new=tuple(new_records),
                    updated=tuple(updated_records),
                    still_known=still_known,
                    invalidated=tuple(invalidated_records),
                )
            )

        return ContinuityReport(
            source_id=result.imported_source.source_id,
            scenes=tuple(scene_reports),
        )

    def run_imported_source_with_scene_payloads(
        self,
        imported_source: ImportedSource,
        payloads_by_scene_id: dict[str, dict[str, Any]],
    ) -> ProjectRunResult:
        """Run imported source using precomputed scene extraction payloads.

        Parameters:
            imported_source: Story Import output.
            payloads_by_scene_id: JSON-like extraction payloads keyed by scene ID.

        Returns:
            Project run result containing accepted Canon from all provided scene
            payloads.

        Raises:
            ValueError: If a payload references a scene not in the imported source
                or a scene has no payload.
        """
        imported_scene_ids = {
            scene.scene_id
            for chapter in imported_source.story.chapters
            for scene in chapter.scenes
        }
        unknown_scene_ids = set(payloads_by_scene_id) - imported_scene_ids
        if unknown_scene_ids:
            unknown = ", ".join(sorted(unknown_scene_ids))
            raise ValueError(f"AI response includes unknown scenes: {unknown}")

        missing_scene_ids = imported_scene_ids - set(payloads_by_scene_id)
        if missing_scene_ids:
            missing = ", ".join(sorted(missing_scene_ids))
            raise ValueError(f"AI response is missing scenes: {missing}")

        return self.run_imported_source(
            imported_source=imported_source,
            extractor=_StaticScenePayloadExtractor(payloads_by_scene_id),
        )

    @staticmethod
    def latest_chapter_index(result: ProjectRunResult) -> int:
        """Return the latest imported chapter index."""
        if not result.imported_source.story.chapters:
            raise ValueError("Project result contains no imported chapters.")

        return result.imported_source.story.chapters[-1].chapter_index

    @staticmethod
    def latest_scene_id(result: ProjectRunResult) -> str:
        """Return the latest imported scene ID."""
        return SceneSmithProjectRunner._latest_scene_id_from_source(result.imported_source)

    @staticmethod
    def _latest_scene_id_from_source(imported_source: ImportedSource) -> str:
        """Return the latest scene ID from an imported source."""
        SceneSmithProjectRunner._require_imported_scenes(imported_source)
        return imported_source.story.chapters[-1].scenes[-1].scene_id

    @staticmethod
    def _anchors_for_scene(
        imported_source: ImportedSource,
        scene_id: str,
    ) -> tuple[EvidenceAnchor, ...]:
        """Return evidence anchors for a scene."""
        return tuple(
            anchor
            for anchor in imported_source.anchors
            if anchor.scene_id == scene_id
        )

    @staticmethod
    def _require_imported_scenes(imported_source: ImportedSource) -> None:
        """Ensure an imported source contains at least one scene."""
        if not imported_source.story.chapters:
            raise ValueError("Imported source contains no chapters.")
        if not imported_source.story.chapters[-1].scenes:
            raise ValueError("Imported source contains no scenes.")

    @staticmethod
    def _dedupe_ids(entity_ids: Sequence[str]) -> tuple[str, ...]:
        """Return IDs in first-seen order without duplicates."""
        deduped: dict[str, None] = {}
        for entity_id in entity_ids:
            deduped.setdefault(entity_id, None)

        return tuple(deduped)

    @staticmethod
    def _classify_continuity_record(
        record: ContinuityRecord,
        known_records: dict[str, ContinuityRecord],
        new_records: list[ContinuityRecord],
        scene_changed_ids: set[str],
    ) -> None:
        """Track a continuity record as new or already known."""
        if record.record_id not in known_records:
            new_records.append(record)

        known_records[record.record_id] = record
        scene_changed_ids.add(record.record_id)

    @staticmethod
    def _with_evidence_context(
        result: ProjectRunResult,
        record: ContinuityRecord,
    ) -> ContinuityRecord:
        """Attach chapter, scene, and quote context to a continuity record."""
        if not record.evidence_id:
            return record

        evidence = result.database.retrieve_evidence(record.evidence_id)
        if evidence is None:
            return record

        return ContinuityRecord(
            record_id=record.record_id,
            record_type=record.record_type,
            description=record.description,
            evidence_id=record.evidence_id,
            chapter_id=evidence.chapter_id,
            scene_id=evidence.scene_id,
            evidence_quote=evidence.quote,
        )


class _KeywordDemoExtractor:
    """Deterministic extractor used only to prove the local pipeline."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Extract a tiny set of known demo candidates from scene text."""
        if not scene.evidence_anchor_ids:
            return ExtractionResult(scene_id=scene.scene_id)

        anchor_id = scene.evidence_anchor_ids[0]
        lowered_text = scene.text.lower()
        entities: list[ExtractedEntity] = []
        relationships: list[ExtractedRelationship] = []

        mark_is_present = "mark" in lowered_text
        if mark_is_present:
            entities.append(
                ExtractedEntity(
                    entity_id="character_mark",
                    entity_type="character",
                    display_name="Mark",
                    evidence_anchor_id=anchor_id,
                    confidence=0.95,
                )
            )

        item_id = self._item_id_from_text(lowered_text)
        if item_id is not None:
            item_name = self._display_name(item_id)
            entities.append(
                ExtractedEntity(
                    entity_id=item_id,
                    entity_type="item",
                    display_name=item_name,
                    evidence_anchor_id=anchor_id,
                    confidence=0.9,
                )
            )
            if mark_is_present:
                relationships.append(
                    ExtractedRelationship(
                        source_entity_id="character_mark",
                        relationship_type=self._item_relationship(lowered_text),
                        target_entity_id=item_id,
                        evidence_anchor_id=anchor_id,
                        confidence=0.88,
                    )
                )

        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=tuple(entities),
            relationships=tuple(relationships),
        )

    @staticmethod
    def _item_id_from_text(text: str) -> str | None:
        """Return a known demo item ID mentioned by the text."""
        if "iron sword" in text:
            return "item_iron_sword"
        if "rusty dagger" in text:
            return "item_rusty_dagger"
        return None

    @staticmethod
    def _display_name(entity_id: str) -> str:
        """Convert a demo entity ID to display text."""
        return entity_id.removeprefix("item_").replace("_", " ").title()

    @staticmethod
    def _item_relationship(text: str) -> str:
        """Return the relationship label for a known demo item mention."""
        if "lost" in text or "loses" in text:
            return "lost"
        return "owns"


class _StaticScenePayloadExtractor:
    """Extractor backed by precomputed JSON-like payloads keyed by scene ID."""

    def __init__(self, payloads_by_scene_id: dict[str, dict[str, Any]]) -> None:
        """Create a static scene payload extractor."""
        self._payloads_by_scene_id = payloads_by_scene_id

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return extraction candidates for the requested scene."""
        payload = self._payloads_by_scene_id.get(scene.scene_id)
        if payload is None:
            raise ValueError(f"AI response is missing scene: {scene.scene_id}")

        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=tuple(self._entities(payload)),
            facts=tuple(self._facts(payload)),
            relationships=tuple(self._relationships(payload)),
            state_changes=tuple(self._state_changes(payload)),
        )

    @staticmethod
    def _entities(payload: dict[str, Any]) -> tuple[ExtractedEntity, ...]:
        """Parse static entity payloads."""
        return tuple(
            ExtractedEntity(
                entity_id=str(item["entity_id"]),
                entity_type=str(item["entity_type"]),
                display_name=str(item["display_name"]),
                evidence_anchor_id=str(item["evidence_anchor_id"]),
                confidence=float(item["confidence"]),
            )
            for item in payload.get("entities", [])
        )

    @staticmethod
    def _facts(payload: dict[str, Any]) -> tuple[ExtractedFact, ...]:
        """Parse static fact payloads."""
        return tuple(
            ExtractedFact(
                fact_id=str(item["fact_id"]),
                entity_id=str(item["entity_id"]),
                attribute=str(item["attribute"]),
                value=str(item["value"]),
                evidence_anchor_id=str(item["evidence_anchor_id"]),
                confidence=float(item["confidence"]),
            )
            for item in payload.get("facts", [])
        )

    @staticmethod
    def _relationships(payload: dict[str, Any]) -> tuple[ExtractedRelationship, ...]:
        """Parse static relationship payloads."""
        return tuple(
            ExtractedRelationship(
                source_entity_id=str(item["source_entity_id"]),
                relationship_type=str(item["relationship_type"]),
                target_entity_id=str(item["target_entity_id"]),
                evidence_anchor_id=str(item["evidence_anchor_id"]),
                confidence=float(item["confidence"]),
            )
            for item in payload.get("relationships", [])
        )

    @staticmethod
    def _state_changes(payload: dict[str, Any]) -> tuple[ExtractedStateChange, ...]:
        """Parse static state-change payloads."""
        return tuple(
            ExtractedStateChange(
                entity_id=str(item["entity_id"]),
                attribute=str(item["attribute"]),
                value=str(item["value"]),
                valid_from_anchor_id=str(item["valid_from_anchor_id"]),
                valid_until_anchor_id=item.get("valid_until_anchor_id"),
                confidence=float(item["confidence"]),
            )
            for item in payload.get("state_changes", [])
        )


def _anchors_by_scene(
    anchors: tuple[EvidenceAnchor, ...],
) -> dict[str, tuple[EvidenceAnchor, ...]]:
    """Group evidence anchors by scene ID."""
    grouped: dict[str, list[EvidenceAnchor]] = {}
    for anchor in anchors:
        grouped.setdefault(anchor.scene_id, []).append(anchor)

    return {
        scene_id: tuple(scene_anchors)
        for scene_id, scene_anchors in grouped.items()
    }

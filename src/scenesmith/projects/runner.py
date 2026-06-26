"""Project Manager workflow runner for proof-stage SceneSmith commands."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scenesmith.canon import CanonDatabase, CanonUpdater, CanonUpdateSummary
from scenesmith.canon.policies import is_additive_fact_attribute
from scenesmith.characters import CanonCharacterCard, CharacterCardBuilder
from scenesmith.core import Fact
from scenesmith.extraction import (
    EntityExtractionEngine,
    EvidenceBoundedAIExtractor,
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractionResult,
    SceneEvidenceAnchor,
    SceneExtractionInput,
    StaticAIExtractionClient,
)
from scenesmith.extraction.engine import SceneExtractor
from scenesmith.importing import (
    EpubTextExtractor,
    EvidenceAnchor,
    ImportedSource,
    StoryImporter,
)
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

    def __post_init__(self) -> None:
        """Validate project workflow result alignment."""
        if len(self.extraction_results) != len(self.update_summaries):
            raise ValueError(
                "Project run extraction results and update summaries must align."
            )


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

    def __post_init__(self) -> None:
        """Validate continuity record identity and evidence references."""
        _require_machine_token(self.record_id, "Continuity record ID")
        _require_machine_token(self.record_type, "Continuity record type")
        _require_text(self.description, "Continuity record description")
        if self.evidence_id:
            _require_machine_token(self.evidence_id, "Continuity evidence ID")
        if self.chapter_id:
            _require_machine_token(self.chapter_id, "Continuity chapter ID")
        if self.scene_id:
            _require_machine_token(self.scene_id, "Continuity scene ID")
        if not isinstance(self.evidence_quote, str) or (
            self.evidence_quote and not self.evidence_quote.strip()
        ):
            raise ValueError("Continuity evidence quote cannot be blank.")


@dataclass(frozen=True, slots=True)
class ContinuitySceneReport:
    """Continuity changes for one scene in story order."""

    scene_id: str
    new: tuple[ContinuityRecord, ...] = ()
    updated: tuple[ContinuityRecord, ...] = ()
    still_known: tuple[ContinuityRecord, ...] = ()
    invalidated: tuple[ContinuityRecord, ...] = ()

    def __post_init__(self) -> None:
        """Validate scene report identity and bucket uniqueness."""
        _require_machine_token(self.scene_id, "Continuity scene report ID")
        for bucket_name, records in (
            ("new", self.new),
            ("updated", self.updated),
            ("still-known", self.still_known),
            ("invalidated", self.invalidated),
        ):
            _require_unique_record_ids(records, bucket_name)


@dataclass(frozen=True, slots=True)
class ContinuityReport:
    """Project-level continuity report for a proof workflow run."""

    source_id: str
    scenes: tuple[ContinuitySceneReport, ...]

    def __post_init__(self) -> None:
        """Validate continuity report source identity and scene uniqueness."""
        _require_machine_token(self.source_id, "Continuity report source ID")
        scene_ids = [scene.scene_id for scene in self.scenes]
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("Continuity report cannot contain duplicate scenes.")


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
        """Import a UTF-8 text file or EPUB file.

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
        if path.suffix.casefold() == ".epub":
            extracted = EpubTextExtractor().extract_path(path)
            return StoryImporter().import_text(
                source_id=source_id,
                title=title or path.stem,
                text=extracted.text,
            )

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

    def build_character_card_at_scene(
        self,
        result: ProjectRunResult,
        character_id: str,
        scene_id: str | None = None,
    ) -> CanonCharacterCard:
        """Build a character card at an exact imported scene position.

        Parameters:
            result: Completed project run result.
            character_id: Character entity ID.
            scene_id: Optional scene ID. Defaults to latest imported scene.

        Returns:
            Canon-backed character card reconstructed for the requested scene.

        Raises:
            ValueError: If the scene or character is unknown.
        """
        chapter_index, scene_index = self._scene_position(
            result=result,
            scene_id=scene_id or self.latest_scene_id(result),
        )
        return CharacterCardBuilder(result.database).build_card_at_scene(
            character_id=character_id,
            chapter_index=chapter_index,
            scene_index=scene_index,
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

    def build_world_state_at_scene(
        self,
        result: ProjectRunResult,
        entity_ids: Sequence[str],
        scene_id: str | None = None,
    ) -> WorldState:
        """Build world state at an exact imported scene position.

        Parameters:
            result: Completed project run result.
            entity_ids: World entity IDs to reconstruct.
            scene_id: Optional scene ID. Defaults to latest imported scene.

        Returns:
            Canon-backed world state reconstructed for the requested scene.

        Raises:
            ValueError: If the scene or a requested world entity is unknown.
        """
        chapter_index, scene_index = self._scene_position(
            result=result,
            scene_id=scene_id or self.latest_scene_id(result),
        )
        return WorldStateBuilder(database=result.database).build_state_at_scene(
            entity_ids=self._dedupe_ids(entity_ids),
            chapter_index=chapter_index,
            scene_index=scene_index,
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
        latest_fact_by_key: dict[tuple[str, ...], ContinuityRecord] = {}
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
                fact_key = self._continuity_fact_key(fact)
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
        for scene_id in payloads_by_scene_id:
            if not isinstance(scene_id, str):
                raise ValueError("AI multi-scene response scene IDs must be strings.")
            _require_machine_token(scene_id, "AI multi-scene response scene ID")

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
    def _scene_position(
        result: ProjectRunResult,
        scene_id: str,
    ) -> tuple[int, int]:
        """Return chapter and scene indexes for an imported scene ID."""
        for chapter in result.imported_source.story.chapters:
            for scene in chapter.scenes:
                if scene.scene_id == scene_id:
                    return chapter.chapter_index, scene.scene_index

        raise ValueError(f"Unknown scene: {scene_id}")

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

    @staticmethod
    def _continuity_fact_key(fact: Fact) -> tuple[str, str] | tuple[str, str, str]:
        """Return replacement key for continuity fact classification."""
        if is_additive_fact_attribute(fact.attribute):
            return (fact.entity_id, fact.attribute, fact.value)

        return (fact.entity_id, fact.attribute)


class _KeywordDemoExtractor:
    """Deterministic extractor used only to prove the local pipeline."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Extract a tiny set of known demo candidates from scene text."""
        if not scene.evidence_anchor_ids:
            return ExtractionResult(scene_id=scene.scene_id)

        anchor_id = scene.evidence_anchor_ids[0]
        lowered_text = scene.text.lower()
        entities: list[ExtractedEntity] = []
        facts: list[ExtractedFact] = []
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
                facts.append(
                    ExtractedFact(
                        fact_id=(
                            f"fact_character_mark_current_weapon_"
                            f"{item_id.removeprefix('item_')}_{scene.scene_id}"
                        ),
                        entity_id="character_mark",
                        attribute="current_weapon",
                        value=(
                            "None"
                            if self._item_relationship(lowered_text) == "lost"
                            else item_name
                        ),
                        evidence_anchor_id=anchor_id,
                        confidence=0.9,
                    )
                )
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
            facts=tuple(facts),
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

        return EvidenceBoundedAIExtractor(
            StaticAIExtractionClient(json.dumps(payload))
        ).extract_scene(
            scene
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


def _require_text(value: str, field_name: str) -> None:
    """Validate a required human-readable text field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a required whitespace-free machine token."""
    _require_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _require_unique_record_ids(
    records: tuple[ContinuityRecord, ...],
    bucket_name: str,
) -> None:
    """Validate that one continuity bucket has no duplicate records."""
    record_ids = [record.record_id for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError(
            f"Continuity {bucket_name} records cannot contain duplicate IDs."
        )

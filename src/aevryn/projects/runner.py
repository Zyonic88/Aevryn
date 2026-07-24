"""Project Manager workflow runner for proof-stage Aevryn commands."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aevryn.canon import CanonDatabase, CanonUpdater, CanonUpdateSummary
from aevryn.canon.policies import is_additive_fact_attribute
from aevryn.characters import CanonCharacterCard, CharacterCardBuilder
from aevryn.core import Fact
from aevryn.entity_resolution import (
    EntityIdentityProfile,
    EntityResolutionEngine,
    ResolvedReference,
    SurfaceReference,
)
from aevryn.extraction import (
    EntityExtractionEngine,
    EvidenceBoundedAIExtractor,
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractedStateChange,
    ExtractionResult,
    SceneEvidenceAnchor,
    SceneExtractionInput,
    SceneSentenceUnderstanding,
    StaticAIExtractionClient,
)
from aevryn.extraction.engine import SceneExtractor
from aevryn.importing import (
    EvidenceAnchor,
    ImportedSource,
    SourceFileTextExtractor,
    StoryImporter,
)
from aevryn.prompts import CanonPromptBuilder, PromptBundle
from aevryn.scenes import CanonSceneContext, SceneContextBuilder
from aevryn.sentences import SentenceUnderstanding, SentenceUnderstandingEngine
from aevryn.translation import (
    GlossaryTerm,
    TranslatedUnit,
    TranslationEngine,
    TranslationSentenceUnderstanding,
    TranslationUnit,
)
from aevryn.world import WorldState, WorldStateBuilder

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProjectRunResult:
    """Result of running the proof-stage project workflow.

    Attributes:
        imported_source: Story Import output for the source text.
        database: In-memory Canon Database populated by accepted candidates.
        extraction_results: Candidate extraction results in scene order.
        update_summaries: Canon update summaries in scene order.
        translation_units: Translation Foundation metadata in scene order.
        identity_resolutions: Entity Resolution metadata for extracted entities.
    """

    imported_source: ImportedSource
    database: CanonDatabase
    extraction_results: tuple[ExtractionResult, ...]
    update_summaries: tuple[CanonUpdateSummary, ...]
    translation_units: tuple[TranslatedUnit, ...] = ()
    identity_resolutions: tuple[ResolvedReference, ...] = ()

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


class AevrynProjectRunner:
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
        """Import a supported source file.

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
        extracted = SourceFileTextExtractor().extract_path(path)
        return StoryImporter().import_text(
            source_id=source_id,
            title=title or path.stem,
            text=extracted.text,
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
        reject_unknown_anchor_candidates: bool = False,
        translation_glossary: tuple[GlossaryTerm, ...] = (),
    ) -> ProjectRunResult:
        """Run extraction and canon updating over imported source.

        Parameters:
            imported_source: Story Import output.
            extractor: Evidence-bounded extractor that proposes candidates.
            reject_unknown_anchor_candidates: When true, candidates that cite
                anchors outside their scene are discarded instead of failing the
                whole run.

        Returns:
            Project run result containing imported source, candidates, and Canon.
        """
        self._require_imported_scenes(imported_source)
        translation_units = self.build_translation_units(
            imported_source,
            glossary=translation_glossary,
        )
        raw_extraction_results = EntityExtractionEngine(
            extractor=extractor,
            unknown_anchor_policy=(
                "reject_candidate" if reject_unknown_anchor_candidates else "raise"
            ),
        ).extract_imported_source(
            imported_source,
            normalized_scene_text_by_id=_translated_scene_text_by_id(translation_units),
        )
        database = CanonDatabase()
        updater = CanonUpdater(database=database)
        anchors_by_scene = _anchors_by_scene(imported_source.anchors)
        extraction_results: list[ExtractionResult] = []
        summaries: list[CanonUpdateSummary] = []
        identity_resolutions: list[ResolvedReference] = []
        identity_profiles: tuple[EntityIdentityProfile, ...] = ()
        for raw_extraction_result in raw_extraction_results:
            extraction_result, decisions = self.resolve_extraction_result_identities(
                raw_extraction_result,
                identity_profiles=identity_profiles,
            )
            summary = updater.apply_extraction_result(
                result=extraction_result,
                anchors=anchors_by_scene.get(extraction_result.scene_id, ()),
            )
            extraction_results.append(extraction_result)
            summaries.append(summary)
            identity_resolutions.extend(decisions)
            identity_profiles = _merged_identity_profiles(
                identity_profiles,
                _identity_profiles_from_accepted_extraction_result(
                    result=extraction_result,
                    summary=summary,
                ),
            )
        result = ProjectRunResult(
            imported_source=imported_source,
            database=database,
            extraction_results=tuple(extraction_results),
            update_summaries=tuple(summaries),
            translation_units=translation_units,
            identity_resolutions=tuple(identity_resolutions),
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
        extraction_result, identity_resolutions = self.resolve_extraction_result_identities(
            extraction_result,
            identity_profiles=(),
        )
        summary = updater.apply_extraction_result(
            result=extraction_result,
            anchors=anchors,
        )
        result = ProjectRunResult(
            imported_source=imported_source,
            database=database,
            extraction_results=(extraction_result,),
            update_summaries=(summary,),
            translation_units=self.build_translation_units(
                imported_source,
                scene_id=requested_scene_id,
            ),
            identity_resolutions=identity_resolutions,
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
                    sentence_understanding = _sentence_understanding_for_scene(
                        imported_source=imported_source,
                        scene_id=requested_scene_id,
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
                        sentence_understanding=sentence_understanding,
                    )

        raise ValueError(f"Unknown scene: {requested_scene_id}")

    def build_translation_units(
        self,
        imported_source: ImportedSource,
        scene_id: str | None = None,
        glossary: tuple[GlossaryTerm, ...] = (),
    ) -> tuple[TranslatedUnit, ...]:
        """Build Translation Foundation units without changing source structure."""
        requested_scene_ids = {scene_id} if scene_id is not None else None
        units: list[TranslationUnit] = []
        sentence_understanding_by_scene = _translation_sentence_understanding_by_scene(
            imported_source
        )
        for chapter in imported_source.story.chapters:
            for scene in chapter.scenes:
                if requested_scene_ids is not None and scene.scene_id not in requested_scene_ids:
                    continue
                anchors = tuple(
                    anchor
                    for anchor in imported_source.anchors
                    if anchor.scene_id == scene.scene_id
                )
                units.append(
                    TranslationUnit(
                        unit_id=f"translation_{scene.scene_id}",
                        source_text="\n\n".join(scene.paragraphs),
                        evidence_anchor_ids=tuple(anchor.anchor_id for anchor in anchors),
                        sentence_understanding=sentence_understanding_by_scene.get(
                            scene.scene_id,
                            (),
                        ),
                        source_chapter_id=chapter.chapter_id,
                        source_scene_id=scene.scene_id,
                    )
                )
        if requested_scene_ids is not None and not units:
            raise ValueError(f"Unknown scene: {scene_id}")
        return TranslationEngine().normalize_units(tuple(units), glossary=glossary)

    def resolve_extracted_identities(
        self,
        extraction_results: tuple[ExtractionResult, ...],
    ) -> tuple[ResolvedReference, ...]:
        """Build Entity Resolution decisions from extracted entity candidates."""
        profiles = _identity_profiles_from_extraction_results(extraction_results)
        references = tuple(
            SurfaceReference(
                text=entity.display_name,
                evidence_anchor_id=entity.evidence_anchor_id,
                scene_id=result.scene_id,
                chapter_id=_chapter_id_from_scene_id(result.scene_id),
            )
            for result in extraction_results
            for entity in result.entities
        )
        return EntityResolutionEngine().resolve_references(references, profiles)

    def resolve_extraction_result_identities(
        self,
        extraction_result: ExtractionResult,
        *,
        identity_profiles: tuple[EntityIdentityProfile, ...],
    ) -> tuple[ExtractionResult, tuple[ResolvedReference, ...]]:
        """Rewrite high-confidence identity references to prior accepted entities."""
        local_identity_profiles = _identity_profiles_from_extraction_results(
            (extraction_result,)
        )
        resolution_profiles = _merged_identity_profiles(
            identity_profiles,
            local_identity_profiles,
        )
        context_entity_ids = _resolution_context_entity_ids(
            extraction_result=extraction_result,
            existing_profiles=identity_profiles,
        )
        resolver = EntityResolutionEngine()
        decisions = tuple(
            resolver.resolve_reference(
                SurfaceReference(
                    text=entity.display_name,
                    evidence_anchor_id=entity.evidence_anchor_id,
                    scene_id=extraction_result.scene_id,
                    chapter_id=_chapter_id_from_scene_id(extraction_result.scene_id),
                ),
                _resolution_profiles_for_entity(
                    entity=entity,
                    identity_profiles=resolution_profiles,
                ),
                context_entity_ids=context_entity_ids,
            )
            for entity in extraction_result.entities
        )
        entity_id_map = {
            entity.entity_id: decision.entity_id
            for entity, decision in zip(
                extraction_result.entities,
                decisions,
                strict=True,
            )
            if decision.status == "resolved"
            and decision.entity_id is not None
            and decision.entity_id != entity.entity_id
        }
        if not entity_id_map:
            return extraction_result, decisions

        rewritten_entities = tuple(
            entity
            for entity in extraction_result.entities
            if entity.entity_id not in entity_id_map
        )
        rewritten_facts = tuple(
            _rewritten_fact_for_resolved_identity(fact, entity_id_map[fact.entity_id])
            if fact.entity_id in entity_id_map
            else fact
            for fact in extraction_result.facts
        )
        rewritten_relationships = tuple(
            ExtractedRelationship(
                source_entity_id=entity_id_map.get(
                    relationship.source_entity_id,
                    relationship.source_entity_id,
                ),
                relationship_type=relationship.relationship_type,
                target_entity_id=entity_id_map.get(
                    relationship.target_entity_id,
                    relationship.target_entity_id,
                ),
                evidence_anchor_id=relationship.evidence_anchor_id,
                confidence=relationship.confidence,
            )
            for relationship in extraction_result.relationships
        )
        rewritten_state_changes = tuple(
            ExtractedStateChange(
                entity_id=entity_id_map.get(state_change.entity_id, state_change.entity_id),
                attribute=state_change.attribute,
                value=state_change.value,
                valid_from_anchor_id=state_change.valid_from_anchor_id,
                confidence=state_change.confidence,
                valid_until_anchor_id=state_change.valid_until_anchor_id,
            )
            for state_change in extraction_result.state_changes
        )
        return (
            ExtractionResult(
                scene_id=extraction_result.scene_id,
                entities=rewritten_entities,
                facts=rewritten_facts,
                relationships=rewritten_relationships,
                state_changes=rewritten_state_changes,
                rejected_candidate_count=extraction_result.rejected_candidate_count,
            ),
            decisions,
        )

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
        return AevrynProjectRunner._latest_scene_id_from_source(result.imported_source)

    @staticmethod
    def _latest_scene_id_from_source(imported_source: ImportedSource) -> str:
        """Return the latest scene ID from an imported source."""
        AevrynProjectRunner._require_imported_scenes(imported_source)
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


def _identity_profiles_from_extraction_results(
    extraction_results: tuple[ExtractionResult, ...],
) -> tuple[EntityIdentityProfile, ...]:
    """Return deterministic identity profiles from extracted entity candidates."""
    entities_by_id: dict[str, ExtractedEntity] = {}
    aliases_by_id: dict[str, set[str]] = {}
    titles_by_id: dict[str, set[str]] = {}
    descriptions_by_id: dict[str, set[str]] = {}
    relationship_labels_by_id: dict[str, set[str]] = {}
    pronouns_by_id: dict[str, set[str]] = {}
    evidence_by_id: dict[str, set[str]] = {}

    for result in extraction_results:
        for entity in result.entities:
            entities_by_id.setdefault(entity.entity_id, entity)
            evidence_by_id.setdefault(entity.entity_id, set()).add(entity.evidence_anchor_id)
        for fact in result.facts:
            if fact.entity_id not in entities_by_id:
                continue
            evidence_by_id.setdefault(fact.entity_id, set()).add(fact.evidence_anchor_id)
            _add_identity_profile_fact(
                fact=fact,
                aliases_by_id=aliases_by_id,
                titles_by_id=titles_by_id,
                descriptions_by_id=descriptions_by_id,
                relationship_labels_by_id=relationship_labels_by_id,
                pronouns_by_id=pronouns_by_id,
            )

    return tuple(
        _identity_profile_from_parts(
            entity=entity,
            aliases=aliases_by_id.get(entity.entity_id, set()),
            titles=titles_by_id.get(entity.entity_id, set()),
            descriptions=descriptions_by_id.get(entity.entity_id, set()),
            relationship_labels=relationship_labels_by_id.get(entity.entity_id, set()),
            pronouns=pronouns_by_id.get(entity.entity_id, set()),
            evidence_anchor_ids=evidence_by_id.get(entity.entity_id, set()),
        )
        for entity in sorted(entities_by_id.values(), key=lambda item: item.entity_id)
    )


def _translated_scene_text_by_id(
    translation_units: tuple[TranslatedUnit, ...],
) -> dict[str, str]:
    """Return normalized scene text keyed by source scene ID."""
    return {
        unit.source_scene_id: unit.normalized_text
        for unit in translation_units
        if unit.source_scene_id
    }


def _sentence_understanding_for_scene(
    *,
    imported_source: ImportedSource,
    scene_id: str,
) -> tuple[SceneSentenceUnderstanding, ...]:
    """Return extraction-safe sentence-understanding metadata for a scene."""
    return tuple(
        _scene_sentence_understanding(understanding)
        for understanding in SentenceUnderstandingEngine().analyze_imported_source(
            imported_source
        )
        if understanding.source_scene_id == scene_id
    )


def _translation_sentence_understanding_by_scene(
    imported_source: ImportedSource,
) -> dict[str, tuple[TranslationSentenceUnderstanding, ...]]:
    """Return translation-safe sentence-understanding metadata by scene."""
    grouped: dict[str, list[TranslationSentenceUnderstanding]] = {}
    for understanding in SentenceUnderstandingEngine().analyze_imported_source(
        imported_source
    ):
        grouped.setdefault(understanding.source_scene_id, []).append(
            _translation_sentence_understanding(understanding)
        )
    return {
        scene_id: tuple(scene_understanding)
        for scene_id, scene_understanding in grouped.items()
    }


def _translation_sentence_understanding(
    understanding: SentenceUnderstanding,
) -> TranslationSentenceUnderstanding:
    """Convert sentence understanding to translation-facing metadata."""
    return TranslationSentenceUnderstanding(
        evidence_anchor_id=understanding.evidence_anchor_id,
        signals=understanding.signals,
        ambiguity_terms=understanding.ambiguity_terms,
        review_required=understanding.review_required,
    )


def _scene_sentence_understanding(
    understanding: SentenceUnderstanding,
) -> SceneSentenceUnderstanding:
    """Convert sentence understanding to extraction-facing metadata."""
    return SceneSentenceUnderstanding(
        evidence_anchor_id=understanding.evidence_anchor_id,
        signals=understanding.signals,
        cue_terms=understanding.cue_terms,
        ambiguity_terms=understanding.ambiguity_terms,
        review_required=understanding.review_required,
    )


def _chapter_id_from_scene_id(scene_id: str) -> str:
    """Return the imported chapter ID prefix for a stable scene ID."""
    marker = "_scene_"
    if marker not in scene_id:
        return ""
    return scene_id.split(marker, maxsplit=1)[0]


def _resolution_profiles_for_entity(
    *,
    entity: ExtractedEntity,
    identity_profiles: tuple[EntityIdentityProfile, ...],
) -> tuple[EntityIdentityProfile, ...]:
    """Return compatible profiles for resolving one extracted entity."""
    return tuple(
        profile
        for profile in identity_profiles
        if profile.entity_id != entity.entity_id
        and profile.entity_type == entity.entity_type
        and profile.entity_type == "character"
    )


def _resolution_context_entity_ids(
    *,
    extraction_result: ExtractionResult,
    existing_profiles: tuple[EntityIdentityProfile, ...],
) -> tuple[str, ...]:
    """Return context IDs that may support conservative pronoun resolution."""
    context_ids = {profile.entity_id for profile in existing_profiles}
    context_ids.update(
        entity.entity_id
        for entity in extraction_result.entities
        if entity.entity_type == "character"
        and not _is_pronoun_reference(entity.display_name)
    )
    return tuple(sorted(context_ids))


def _is_pronoun_reference(value: str) -> bool:
    """Return whether a display value is only a pronoun surface reference."""
    return value.strip().lower() in {
        "he",
        "him",
        "his",
        "she",
        "her",
        "hers",
        "they",
        "them",
        "their",
        "theirs",
    }


def _identity_profiles_from_accepted_extraction_result(
    *,
    result: ExtractionResult,
    summary: CanonUpdateSummary,
) -> tuple[EntityIdentityProfile, ...]:
    """Return identity profiles from candidates accepted into Canon."""
    accepted_entity_ids = set(summary.accepted_entities)
    if not accepted_entity_ids:
        return ()

    entities_by_id = {
        entity.entity_id: entity
        for entity in result.entities
        if entity.entity_id in accepted_entity_ids
    }
    aliases_by_id: dict[str, set[str]] = {}
    titles_by_id: dict[str, set[str]] = {}
    descriptions_by_id: dict[str, set[str]] = {}
    relationship_labels_by_id: dict[str, set[str]] = {}
    pronouns_by_id: dict[str, set[str]] = {}
    evidence_by_id: dict[str, set[str]] = {
        entity_id: {entity.evidence_anchor_id}
        for entity_id, entity in entities_by_id.items()
    }

    for fact in result.facts:
        if fact.entity_id not in accepted_entity_ids:
            continue
        evidence_by_id.setdefault(fact.entity_id, set()).add(fact.evidence_anchor_id)
        _add_identity_profile_fact(
            fact=fact,
            aliases_by_id=aliases_by_id,
            titles_by_id=titles_by_id,
            descriptions_by_id=descriptions_by_id,
            relationship_labels_by_id=relationship_labels_by_id,
            pronouns_by_id=pronouns_by_id,
        )

    return tuple(
        _identity_profile_from_parts(
            entity=entity,
            aliases=aliases_by_id.get(entity.entity_id, set()),
            titles=titles_by_id.get(entity.entity_id, set()),
            descriptions=descriptions_by_id.get(entity.entity_id, set()),
            relationship_labels=relationship_labels_by_id.get(entity.entity_id, set()),
            pronouns=pronouns_by_id.get(entity.entity_id, set()),
            evidence_anchor_ids=evidence_by_id.get(entity.entity_id, set()),
        )
        for entity in sorted(entities_by_id.values(), key=lambda item: item.entity_id)
    )


def _merged_identity_profiles(
    existing: tuple[EntityIdentityProfile, ...],
    additions: tuple[EntityIdentityProfile, ...],
) -> tuple[EntityIdentityProfile, ...]:
    """Merge identity profiles by entity ID without losing surface references."""
    profiles_by_id = {profile.entity_id: profile for profile in existing}
    for addition in additions:
        current = profiles_by_id.get(addition.entity_id)
        if current is None:
            profiles_by_id[addition.entity_id] = addition
            continue
        profiles_by_id[addition.entity_id] = EntityIdentityProfile(
            entity_id=current.entity_id,
            canonical_name=current.canonical_name,
            entity_type=current.entity_type,
            aliases=_unique_identity_surfaces((*current.aliases, *addition.aliases)),
            titles=_unique_identity_surfaces((*current.titles, *addition.titles)),
            descriptions=_unique_identity_surfaces(
                (*current.descriptions, *addition.descriptions)
            ),
            relationship_labels=_unique_identity_surfaces(
                (*current.relationship_labels, *addition.relationship_labels)
            ),
            pronouns=_unique_identity_surfaces((*current.pronouns, *addition.pronouns)),
            evidence_anchor_ids=tuple(
                sorted(
                    set(current.evidence_anchor_ids).union(
                        addition.evidence_anchor_ids
                    )
                )
            ),
        )
    return tuple(profiles_by_id[entity_id] for entity_id in sorted(profiles_by_id))


def _identity_profile_from_parts(
    *,
    entity: ExtractedEntity,
    aliases: set[str],
    titles: set[str],
    descriptions: set[str],
    relationship_labels: set[str],
    pronouns: set[str],
    evidence_anchor_ids: set[str],
) -> EntityIdentityProfile:
    """Create one identity profile with useful composite descriptions."""
    composite_aliases = set(aliases)
    composite_descriptions = set(descriptions)
    name_surfaces = {entity.display_name, *aliases}
    genders = _explicit_gender_terms_for_identity_surfaces(
        (entity.display_name, *aliases, *titles, *descriptions)
    )
    composite_descriptions.update(genders)
    for title in titles:
        for name in name_surfaces:
            composite_aliases.add(f"{title} {name}")
            composite_aliases.add(f"{name} {title}")
    for gender in genders:
        for title in titles:
            composite_descriptions.add(f"{gender} {title}")

    return EntityIdentityProfile(
        entity_id=entity.entity_id,
        canonical_name=entity.display_name,
        entity_type=entity.entity_type,
        aliases=_unique_identity_surfaces(tuple(composite_aliases)),
        titles=_unique_identity_surfaces(tuple(titles)),
        descriptions=_unique_identity_surfaces(tuple(composite_descriptions)),
        relationship_labels=_unique_identity_surfaces(tuple(relationship_labels)),
        pronouns=_unique_identity_surfaces(tuple(pronouns)),
        evidence_anchor_ids=tuple(sorted(evidence_anchor_ids)),
    )


def _unique_identity_surfaces(values: tuple[str, ...]) -> tuple[str, ...]:
    """Return deterministic identity surfaces unique by comparison tokens."""
    surfaces_by_key: dict[str, str] = {}
    for value in sorted(values):
        key = " ".join(_identity_surface_tokens(value))
        if not key:
            continue
        surfaces_by_key.setdefault(key, value)
    return tuple(surfaces_by_key[key] for key in sorted(surfaces_by_key))


def _add_identity_profile_fact(
    *,
    fact: ExtractedFact,
    aliases_by_id: dict[str, set[str]],
    titles_by_id: dict[str, set[str]],
    descriptions_by_id: dict[str, set[str]],
    relationship_labels_by_id: dict[str, set[str]],
    pronouns_by_id: dict[str, set[str]],
) -> None:
    """Route an accepted fact into identity-profile fields."""
    attribute = fact.attribute.lower()
    if attribute in {"display_name", "name", "alias"}:
        aliases_by_id.setdefault(fact.entity_id, set()).add(fact.value)
    elif attribute in {"title", "role", "profession"} or (
        attribute == "status" and _status_value_is_title_like(fact.value)
    ):
        titles_by_id.setdefault(fact.entity_id, set()).add(fact.value)
    elif attribute in {"description", "appearance", "race", "species", "gender", "sex"}:
        descriptions_by_id.setdefault(fact.entity_id, set()).add(fact.value)
    elif attribute in {
        "family_role",
        "relationship_role",
        "relationship_context",
        "kinship",
    }:
        descriptions_by_id.setdefault(fact.entity_id, set()).add(fact.value)
        relationship_labels_by_id.setdefault(fact.entity_id, set()).add(fact.value)
    pronouns = _pronouns_for_identity_fact_value(fact.value)
    if pronouns:
        pronouns_by_id.setdefault(fact.entity_id, set()).update(pronouns)


def _pronouns_for_identity_fact_value(value: str) -> tuple[str, ...]:
    """Return conservative pronoun hints from explicit gendered terms."""
    gender_terms = _explicit_gender_terms_for_identity_surfaces((value,))
    if gender_terms == {"female"}:
        return ("she", "her", "hers")
    if gender_terms == {"male"}:
        return ("he", "him", "his")
    return ()


def _status_value_is_title_like(value: str) -> bool:
    """Return whether a status value is safe to reuse as an identity title."""
    tokens = _identity_surface_tokens(value)
    if not 1 <= len(tokens) <= 4:
        return False
    normalized = " ".join(tokens)
    return normalized in _TITLE_LIKE_STATUS_VALUES


def _explicit_gender_terms_for_identity_surfaces(values: tuple[str, ...]) -> set[str]:
    """Return explicit gender terms present in identity surfaces without guessing."""
    gender_terms: set[str] = set()
    for value in values:
        tokens = _identity_surface_tokens(value)
        for index, token in enumerate(tokens):
            if _gender_token_is_negated(tokens, index):
                continue
            if token in _FEMALE_IDENTITY_TERMS:
                gender_terms.add("female")
            elif token in _MALE_IDENTITY_TERMS:
                gender_terms.add("male")
    return gender_terms


_FEMALE_IDENTITY_TERMS = {
    "female",
    "woman",
    "women",
    "girl",
    "girls",
    "sister",
    "sisters",
    "mother",
    "mothers",
    "daughter",
    "daughters",
    "wife",
    "wives",
    "fiancee",
    "fiancees",
    "fianc\u00e9e",
    "fianc\u00e9es",
    "queen",
    "queens",
    "princess",
    "princesses",
}
_MALE_IDENTITY_TERMS = {
    "male",
    "man",
    "men",
    "boy",
    "boys",
    "brother",
    "brothers",
    "father",
    "fathers",
    "son",
    "sons",
    "husband",
    "husbands",
    "fiance",
    "fiances",
    "fianc\u00e9",
    "fianc\u00e9s",
    "king",
    "kings",
    "prince",
    "princes",
}
_GENDER_NEGATION_TERMS = {"not", "no", "non", "without"}
_TITLE_LIKE_STATUS_VALUES = {
    "admiral",
    "baron",
    "baroness",
    "captain",
    "chief",
    "chief engineer",
    "commander",
    "doctor",
    "director",
    "elder",
    "emperor",
    "empress",
    "general",
    "king",
    "lady",
    "lord",
    "master",
    "officer",
    "prince",
    "princess",
    "professor",
    "queen",
    "teacher",
    "vice captain",
}


def _identity_surface_tokens(value: str) -> tuple[str, ...]:
    """Return lowercase alphanumeric tokens from a human identity surface."""
    normalized = "".join(
        character.lower() if character.isalnum() else " "
        for character in value
    )
    return tuple(part for part in normalized.split() if part)


def _gender_token_is_negated(tokens: tuple[str, ...], index: int) -> bool:
    """Return whether a gendered token has a nearby explicit negation."""
    start = max(0, index - 2)
    return any(token in _GENDER_NEGATION_TERMS for token in tokens[start:index])


def _rewritten_fact_for_resolved_identity(
    fact: ExtractedFact,
    resolved_entity_id: str,
) -> ExtractedFact:
    """Return a fact rewritten to a resolved entity ID."""
    return ExtractedFact(
        fact_id=(
            "fact_"
            f"{resolved_entity_id}_"
            f"{fact.attribute}_"
            f"{_machine_suffix(fact.value)}_"
            f"{fact.evidence_anchor_id}"
        ),
        entity_id=resolved_entity_id,
        attribute=fact.attribute,
        value=fact.value,
        evidence_anchor_id=fact.evidence_anchor_id,
        confidence=fact.confidence,
    )


def _machine_suffix(value: str) -> str:
    """Return a stable machine-token suffix from human text."""
    normalized = "".join(
        character.lower() if character.isalnum() else "_"
        for character in value
    )
    collapsed = "_".join(part for part in normalized.split("_") if part)
    return collapsed[:80] or "value"


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

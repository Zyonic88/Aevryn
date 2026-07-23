"""Entity Extraction boundary implementation."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Literal, Protocol

from aevryn.extraction.models import (
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractedStateChange,
    ExtractionResult,
    SceneEvidenceAnchor,
    SceneExtractionInput,
    SceneSentenceUnderstanding,
)
from aevryn.importing import EvidenceAnchor, ImportedSource
from aevryn.sentences import SentenceUnderstanding, SentenceUnderstandingEngine

logger = logging.getLogger(__name__)

UnknownAnchorPolicy = Literal["raise", "reject_candidate"]

PHYSICAL_ENTITY_TERMS = frozenset(
    {
        "armor",
        "artifact",
        "battlecruiser",
        "blade",
        "blueprint",
        "book",
        "car",
        "coin",
        "credits",
        "cruiser",
        "dagger",
        "equipment",
        "facility",
        "gun",
        "hangar",
        "jacket",
        "manual",
        "potion",
        "rifle",
        "room",
        "ship",
        "shuttle",
        "spaceship",
        "spear",
        "starship",
        "sword",
        "token",
        "uniform",
        "vehicle",
        "vessel",
        "weapon",
    }
)
SKILL_ENTITY_TERMS = frozenset(
    {
        "ability",
        "art",
        "cast",
        "spell",
        "skill",
        "technique",
    }
)
SYSTEM_ENTITY_TERMS = frozenset(
    {
        "interface",
        "panel",
        "system",
    }
)
ROLE_OR_TITLE_ENTITY_TERMS = frozenset(
    {
        "admiral",
        "baron",
        "baroness",
        "captain",
        "commander",
        "department",
        "doctor",
        "engineer",
        "general",
        "officer",
        "professor",
        "recruit",
        "soldier",
        "student",
        "teacher",
    }
)
ENTITY_ID_TYPE_PREFIXES = {
    "armor": "armor",
    "building": "building",
    "character": "character",
    "creature": "creature",
    "item": "item",
    "location": "location",
    "organization": "organization",
    "skill": "skill",
    "system": "system",
    "vehicle": "vehicle",
    "weapon": "weapon",
}


class SceneExtractor(Protocol):
    """Protocol for AI or test extractors."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Extract candidate entities and relationships from a scene."""


class EntityExtractionEngine:
    """Coordinate entity extraction without updating Canon."""

    def __init__(
        self,
        extractor: SceneExtractor,
        unknown_anchor_policy: UnknownAnchorPolicy = "raise",
    ) -> None:
        """Create an Entity Extraction Engine.

        Parameters:
            extractor: AI-backed or test extractor that proposes candidates.
            unknown_anchor_policy: How to handle candidates referencing anchors
                outside the scene evidence set.
        """
        if unknown_anchor_policy not in {"raise", "reject_candidate"}:
            raise ValueError("Unknown anchor policy is invalid.")
        self._extractor = extractor
        self._unknown_anchor_policy = unknown_anchor_policy

    def extract_imported_source(
        self,
        imported_source: ImportedSource,
        normalized_scene_text_by_id: Mapping[str, str] | None = None,
    ) -> tuple[ExtractionResult, ...]:
        """Extract candidates from every imported scene.

        Parameters:
            imported_source: Source structure produced by Story Import.
            normalized_scene_text_by_id: Optional translated or normalized scene
                text keyed by imported scene ID. Evidence anchors still come from
                the original import.

        Returns:
            Extraction results in scene order.
        """
        anchors_by_scene = self._anchors_by_scene(imported_source.anchors)
        understanding_by_scene = self._sentence_understanding_by_scene(imported_source)
        results = tuple(
            self.extract_scene(
                scene_id=scene.scene_id,
                text=(
                    normalized_scene_text_by_id.get(scene.scene_id)
                    if normalized_scene_text_by_id is not None
                    else None
                )
                or "\n\n".join(scene.paragraphs),
                anchors=anchors_by_scene.get(scene.scene_id, ()),
                sentence_understanding=understanding_by_scene.get(scene.scene_id, ()),
            )
            for chapter in imported_source.story.chapters
            for scene in chapter.scenes
        )
        results = self._without_cross_scene_fact_id_collisions(results)
        logger.info(
            "entity_extraction_completed",
            extra={
                "source_id": imported_source.source_id,
                "scene_count": len(results),
            },
        )
        return results

    @staticmethod
    def _without_cross_scene_fact_id_collisions(
        results: tuple[ExtractionResult, ...],
    ) -> tuple[ExtractionResult, ...]:
        """Return results with conflicting cross-scene fact IDs rewritten."""
        fact_signatures_by_id: dict[str, set[tuple[str, str, str, str]]] = {}
        for result in results:
            for fact in result.facts:
                fact_signatures_by_id.setdefault(fact.fact_id, set()).add(
                    EntityExtractionEngine._fact_signature(fact)
                )

        colliding_fact_ids = {
            fact_id
            for fact_id, signatures in fact_signatures_by_id.items()
            if len(signatures) > 1
        }
        if not colliding_fact_ids:
            return results

        rewritten_results = tuple(
            ExtractionResult(
                scene_id=result.scene_id,
                entities=result.entities,
                facts=tuple(
                    EntityExtractionEngine._fact_with_collision_safe_id(fact)
                    if fact.fact_id in colliding_fact_ids
                    else fact
                    for fact in result.facts
                ),
                relationships=result.relationships,
                state_changes=result.state_changes,
                rejected_candidate_count=result.rejected_candidate_count,
            )
            for result in results
        )
        logger.warning(
            "extraction_fact_ids_rewritten_for_cross_scene_collisions",
            extra={"rewritten_fact_ids": len(colliding_fact_ids)},
        )
        return rewritten_results

    @staticmethod
    def _fact_signature(fact: ExtractedFact) -> tuple[str, str, str, str]:
        """Return the semantic identity of an extracted fact candidate."""
        return (
            fact.entity_id,
            fact.attribute,
            fact.value,
            fact.evidence_anchor_id,
        )

    @staticmethod
    def _fact_with_collision_safe_id(fact: ExtractedFact) -> ExtractedFact:
        """Return a fact with a deterministic source-grounded ID."""
        return ExtractedFact(
            fact_id=(
                "fact_"
                f"{fact.entity_id}_"
                f"{fact.attribute}_"
                f"{EntityExtractionEngine._machine_suffix(fact.value)}_"
                f"{fact.evidence_anchor_id}"
            ),
            entity_id=fact.entity_id,
            attribute=fact.attribute,
            value=fact.value,
            evidence_anchor_id=fact.evidence_anchor_id,
            confidence=fact.confidence,
        )

    @staticmethod
    def _machine_suffix(value: str) -> str:
        """Return a stable machine-token suffix from human text."""
        normalized = "".join(
            character.lower() if character.isalnum() else "_"
            for character in value
        )
        collapsed = "_".join(part for part in normalized.split("_") if part)
        return collapsed[:80] or "value"

    def extract_scene(
        self,
        scene_id: str,
        text: str,
        anchors: tuple[EvidenceAnchor, ...],
        sentence_understanding: tuple[SceneSentenceUnderstanding, ...] = (),
    ) -> ExtractionResult:
        """Extract candidates from one scene without changing Canon.

        Parameters:
            scene_id: Imported scene identifier.
            text: Scene source text.
            anchors: Evidence anchors belonging to the scene.
            sentence_understanding: Optional sentence-level meaning metadata for
                the scene's evidence anchors.

        Returns:
            Validated extraction result.

        Raises:
            ValueError: If extractor output lacks required evidence anchors or confidence.
        """
        anchor_ids = tuple(anchor.anchor_id for anchor in anchors)
        result = self._extractor.extract_scene(
            SceneExtractionInput(
                scene_id=scene_id,
                text=text,
                evidence_anchor_ids=anchor_ids,
                evidence_anchors=tuple(
                    SceneEvidenceAnchor(
                        anchor_id=anchor.anchor_id,
                        quote=anchor.quote,
                    )
                    for anchor in anchors
                ),
                sentence_understanding=sentence_understanding,
            )
        )
        result = self._validate_result(result=result, allowed_anchor_ids=anchor_ids)
        if result.scene_id != scene_id:
            raise ValueError(
                "Extraction result has wrong scene_id for requested scene: "
                f"{result.scene_id}"
            )
        logger.debug(
            "scene_extraction_validated",
            extra={
                "scene_id": scene_id,
                "entity_count": len(result.entities),
                "fact_count": len(result.facts),
                "relationship_count": len(result.relationships),
                "state_change_count": len(result.state_changes),
            },
        )
        return result

    @staticmethod
    def _sentence_understanding_by_scene(
        imported_source: ImportedSource,
    ) -> dict[str, tuple[SceneSentenceUnderstanding, ...]]:
        """Return extraction-safe sentence-understanding metadata by scene."""
        understandings = SentenceUnderstandingEngine().analyze_imported_source(
            imported_source
        )
        grouped: dict[str, list[SceneSentenceUnderstanding]] = {}
        for understanding in understandings:
            grouped.setdefault(understanding.source_scene_id, []).append(
                EntityExtractionEngine._scene_sentence_understanding(understanding)
            )
        return {
            scene_id: tuple(scene_understandings)
            for scene_id, scene_understandings in grouped.items()
        }

    @staticmethod
    def _scene_sentence_understanding(
        understanding: SentenceUnderstanding,
    ) -> SceneSentenceUnderstanding:
        """Convert full sentence understanding to extraction-facing metadata."""
        return SceneSentenceUnderstanding(
            evidence_anchor_id=understanding.evidence_anchor_id,
            signals=understanding.signals,
            cue_terms=understanding.cue_terms,
            ambiguity_terms=understanding.ambiguity_terms,
            review_required=understanding.review_required,
        )

    def _validate_result(
        self,
        result: ExtractionResult,
        allowed_anchor_ids: tuple[str, ...],
    ) -> ExtractionResult:
        """Validate extractor candidates against Story Import anchors."""
        allowed = set(allowed_anchor_ids)
        self._validate_unique_result_candidates(result)
        if self._unknown_anchor_policy == "reject_candidate":
            result = self._without_unknown_anchor_candidates(
                result=result,
                allowed_anchor_ids=allowed,
            )
        for entity in result.entities:
            self._validate_entity(entity=entity, allowed_anchor_ids=allowed)
        for fact in result.facts:
            self._validate_fact(fact=fact, allowed_anchor_ids=allowed)
        for relationship in result.relationships:
            self._validate_relationship(
                relationship=relationship,
                allowed_anchor_ids=allowed,
            )
        for state_change in result.state_changes:
            self._validate_state_change(
                state_change=state_change,
                allowed_anchor_ids=allowed,
            )
        return result

    @staticmethod
    def _without_unknown_anchor_candidates(
        result: ExtractionResult,
        allowed_anchor_ids: set[str],
    ) -> ExtractionResult:
        """Return a copy with ungrounded candidates removed."""
        filtered = ExtractionResult(
            scene_id=result.scene_id,
            entities=tuple(
                entity
                for entity in result.entities
                if entity.evidence_anchor_id in allowed_anchor_ids
            ),
            facts=tuple(
                fact
                for fact in result.facts
                if fact.evidence_anchor_id in allowed_anchor_ids
            ),
            relationships=tuple(
                relationship
                for relationship in result.relationships
                if relationship.evidence_anchor_id in allowed_anchor_ids
            ),
            state_changes=tuple(
                state_change
                for state_change in result.state_changes
                if state_change.valid_from_anchor_id in allowed_anchor_ids
                and (
                    state_change.valid_until_anchor_id is None
                    or state_change.valid_until_anchor_id in allowed_anchor_ids
                )
            ),
            rejected_candidate_count=result.rejected_candidate_count,
        )
        rejected_count = (
            len(result.entities)
            + len(result.facts)
            + len(result.relationships)
            + len(result.state_changes)
            - len(filtered.entities)
            - len(filtered.facts)
            - len(filtered.relationships)
            - len(filtered.state_changes)
        )
        if rejected_count:
            logger.warning(
                "extraction_candidates_rejected_unknown_anchors",
                extra={
                    "scene_id": result.scene_id,
                    "rejected_candidates": rejected_count,
                },
            )
        return ExtractionResult(
            scene_id=filtered.scene_id,
            entities=filtered.entities,
            facts=filtered.facts,
            relationships=filtered.relationships,
            state_changes=filtered.state_changes,
            rejected_candidate_count=result.rejected_candidate_count + rejected_count,
        )

    @staticmethod
    def _validate_entity(
        entity: ExtractedEntity,
        allowed_anchor_ids: set[str],
    ) -> None:
        """Validate an extracted entity candidate."""
        if entity.evidence_anchor_id not in allowed_anchor_ids:
            raise ValueError(f"Unknown evidence anchor: {entity.evidence_anchor_id}")
        EntityExtractionEngine._validate_confidence(entity.confidence)
        classification_error = EntityExtractionEngine._entity_classification_error(entity)
        if classification_error is not None:
            raise ValueError(classification_error)

    @staticmethod
    def _entity_classification_error(entity: ExtractedEntity) -> str | None:
        """Return a deterministic error for obvious entity classification conflicts."""
        expected_type = EntityExtractionEngine._expected_type_from_entity_id(entity.entity_id)
        if expected_type is not None and expected_type != entity.entity_type:
            return (
                "Entity classification conflicts with entity ID prefix: "
                f"{entity.entity_id} is {entity.entity_type}, expected {expected_type}."
            )

        classification_terms = EntityExtractionEngine._classification_terms(entity)
        physical_terms = classification_terms & PHYSICAL_ENTITY_TERMS
        skill_terms = classification_terms & SKILL_ENTITY_TERMS
        system_terms = classification_terms & SYSTEM_ENTITY_TERMS
        role_or_title_terms = classification_terms & ROLE_OR_TITLE_ENTITY_TERMS
        if entity.entity_type == "skill" and physical_terms and not skill_terms:
            return (
                "Entity classification conflict: physical object cannot be skill: "
                f"{entity.display_name}."
            )
        if entity.entity_type == "skill" and role_or_title_terms and not skill_terms:
            return (
                "Entity classification conflict: rank or profession cannot be skill: "
                f"{entity.display_name}."
            )
        if entity.entity_type == "system" and physical_terms and not system_terms:
            return (
                "Entity classification conflict: physical object cannot be system: "
                f"{entity.display_name}."
            )
        if (
            entity.entity_type in {"item", "weapon", "armor", "vehicle"}
            and system_terms
            and not physical_terms
        ):
            return (
                "Entity classification conflict: governing system cannot be physical item: "
                f"{entity.display_name}."
            )
        if (
            entity.entity_type in {"item", "weapon", "armor", "vehicle"}
            and skill_terms
            and not physical_terms
        ):
            return (
                "Entity classification conflict: usable ability cannot be physical item: "
                f"{entity.display_name}."
            )
        return None

    @staticmethod
    def _expected_type_from_entity_id(entity_id: str) -> str | None:
        """Return expected entity type from a conventional entity ID prefix."""
        prefix = entity_id.split("_", maxsplit=1)[0]
        return ENTITY_ID_TYPE_PREFIXES.get(prefix)

    @staticmethod
    def _classification_terms(entity: ExtractedEntity) -> set[str]:
        """Return lowercase tokens used for deterministic classification checks."""
        raw_text = entity.display_name
        tokens = {
            token
            for token in "".join(
                character.lower() if character.isalnum() else " "
                for character in raw_text
            ).split()
            if token
        }
        if "battle" in tokens and "cruiser" in tokens:
            tokens.add("battlecruiser")
        if "star" in tokens and "ship" in tokens:
            tokens.add("starship")
        return tokens

    @staticmethod
    def _validate_relationship(
        relationship: ExtractedRelationship,
        allowed_anchor_ids: set[str],
    ) -> None:
        """Validate an extracted relationship candidate."""
        if relationship.evidence_anchor_id not in allowed_anchor_ids:
            raise ValueError(f"Unknown evidence anchor: {relationship.evidence_anchor_id}")
        EntityExtractionEngine._validate_confidence(relationship.confidence)

    @staticmethod
    def _validate_fact(
        fact: ExtractedFact,
        allowed_anchor_ids: set[str],
    ) -> None:
        """Validate an extracted fact candidate."""
        if fact.evidence_anchor_id not in allowed_anchor_ids:
            raise ValueError(f"Unknown evidence anchor: {fact.evidence_anchor_id}")
        EntityExtractionEngine._validate_confidence(fact.confidence)

    @staticmethod
    def _validate_state_change(
        state_change: ExtractedStateChange,
        allowed_anchor_ids: set[str],
    ) -> None:
        """Validate an extracted state-change candidate."""
        if state_change.valid_from_anchor_id not in allowed_anchor_ids:
            raise ValueError(f"Unknown evidence anchor: {state_change.valid_from_anchor_id}")
        if (
            state_change.valid_until_anchor_id is not None
            and state_change.valid_until_anchor_id not in allowed_anchor_ids
        ):
            raise ValueError(f"Unknown evidence anchor: {state_change.valid_until_anchor_id}")
        EntityExtractionEngine._validate_confidence(state_change.confidence)

    @staticmethod
    def _validate_unique_result_candidates(result: ExtractionResult) -> None:
        """Validate that one scene result does not repeat candidate identities."""
        entity_ids = tuple(entity.entity_id for entity in result.entities)
        EntityExtractionEngine._require_unique_values(entity_ids, "entity IDs")

        fact_ids = tuple(fact.fact_id for fact in result.facts)
        EntityExtractionEngine._require_unique_values(fact_ids, "fact IDs")

        state_change_keys = tuple(
            (
                state_change.entity_id,
                state_change.attribute,
                state_change.value,
                state_change.valid_from_anchor_id,
                state_change.valid_until_anchor_id,
            )
            for state_change in result.state_changes
        )
        EntityExtractionEngine._require_unique_values(
            state_change_keys,
            "state-change candidates",
        )

    @staticmethod
    def _require_unique_values(values: tuple[object, ...], field_name: str) -> None:
        """Validate unique candidate identities."""
        if len(values) != len(set(values)):
            raise ValueError(f"Extraction result contains duplicate {field_name}.")

    @staticmethod
    def _validate_confidence(confidence: float) -> None:
        """Validate extraction confidence score."""
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, int | float)
            or not 0.0 <= confidence <= 1.0
        ):
            raise ValueError("Extraction confidence must be between 0.0 and 1.0.")

    @staticmethod
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

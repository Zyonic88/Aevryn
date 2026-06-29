"""Entity Extraction boundary implementation."""

from __future__ import annotations

import logging
from typing import Literal, Protocol

from aevryn.extraction.models import (
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractedStateChange,
    ExtractionResult,
    SceneEvidenceAnchor,
    SceneExtractionInput,
)
from aevryn.importing import EvidenceAnchor, ImportedSource

logger = logging.getLogger(__name__)

UnknownAnchorPolicy = Literal["raise", "reject_candidate"]


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
    ) -> tuple[ExtractionResult, ...]:
        """Extract candidates from every imported scene.

        Parameters:
            imported_source: Source structure produced by Story Import.

        Returns:
            Extraction results in scene order.
        """
        anchors_by_scene = self._anchors_by_scene(imported_source.anchors)
        results = tuple(
            self.extract_scene(
                scene_id=scene.scene_id,
                text="\n\n".join(scene.paragraphs),
                anchors=anchors_by_scene.get(scene.scene_id, ()),
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
    ) -> ExtractionResult:
        """Extract candidates from one scene without changing Canon.

        Parameters:
            scene_id: Imported scene identifier.
            text: Scene source text.
            anchors: Evidence anchors belonging to the scene.

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
        return filtered

    @staticmethod
    def _validate_entity(
        entity: ExtractedEntity,
        allowed_anchor_ids: set[str],
    ) -> None:
        """Validate an extracted entity candidate."""
        if entity.evidence_anchor_id not in allowed_anchor_ids:
            raise ValueError(f"Unknown evidence anchor: {entity.evidence_anchor_id}")
        EntityExtractionEngine._validate_confidence(entity.confidence)

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

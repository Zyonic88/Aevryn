"""Entity Extraction boundary implementation."""

from __future__ import annotations

import logging
from typing import Protocol

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


class SceneExtractor(Protocol):
    """Protocol for AI or test extractors."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Extract candidate entities and relationships from a scene."""


class EntityExtractionEngine:
    """Coordinate entity extraction without updating Canon."""

    def __init__(self, extractor: SceneExtractor) -> None:
        """Create an Entity Extraction Engine.

        Parameters:
            extractor: AI-backed or test extractor that proposes candidates.
        """
        self._extractor = extractor

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
        logger.info(
            "entity_extraction_completed",
            extra={
                "source_id": imported_source.source_id,
                "scene_count": len(results),
            },
        )
        return results

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
        self._validate_result(result=result, allowed_anchor_ids=anchor_ids)
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
    ) -> None:
        """Validate extractor candidates against Story Import anchors."""
        allowed = set(allowed_anchor_ids)
        self._validate_unique_result_candidates(result)
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

        relationship_keys = tuple(
            (
                relationship.source_entity_id,
                relationship.relationship_type,
                relationship.target_entity_id,
            )
            for relationship in result.relationships
        )
        EntityExtractionEngine._require_unique_values(
            relationship_keys,
            "relationship candidates",
        )

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

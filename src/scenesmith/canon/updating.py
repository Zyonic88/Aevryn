"""Canon Updating implementation."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from scenesmith.canon import CanonDatabase
from scenesmith.canon.policies import is_additive_fact_attribute
from scenesmith.core import (
    Chapter,
    Character,
    Entity,
    Evidence,
    Fact,
    Relationship,
    StateChange,
    TimelineEvent,
)
from scenesmith.extraction import (
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractionResult,
)
from scenesmith.importing import EvidenceAnchor

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CanonUpdateSummary:
    """Summary of accepted and rejected canon update candidates."""

    accepted_entities: tuple[str, ...] = ()
    accepted_facts: tuple[str, ...] = ()
    accepted_relationships: tuple[str, ...] = ()
    accepted_state_changes: tuple[str, ...] = ()
    rejected_candidates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate accepted and rejected candidate summary IDs."""
        accepted_candidate_ids: list[str] = []
        for bucket_name, candidate_ids in (
            ("accepted entity", self.accepted_entities),
            ("accepted fact", self.accepted_facts),
            ("accepted relationship", self.accepted_relationships),
            ("accepted state change", self.accepted_state_changes),
            ("rejected candidate", self.rejected_candidates),
        ):
            _require_unique_machine_tokens(candidate_ids, bucket_name)
            if bucket_name != "rejected candidate":
                accepted_candidate_ids.extend(candidate_ids)
        rejected_accepted_overlap = set(accepted_candidate_ids).intersection(
            self.rejected_candidates
        )
        if rejected_accepted_overlap:
            overlap = ", ".join(sorted(rejected_accepted_overlap))
            raise ValueError(
                "Canon summary IDs cannot be both accepted and rejected: "
                f"{overlap}"
            )


class CanonUpdater:
    """Validate extraction candidates before changing Canon."""

    def __init__(self, database: CanonDatabase, minimum_confidence: float = 0.75) -> None:
        """Create a Canon Updater.

        Parameters:
            database: Canon Database where accepted truth is stored.
            minimum_confidence: Minimum confidence required for acceptance.

        Raises:
            ValueError: If minimum_confidence is outside 0.0 to 1.0.
        """
        if (
            isinstance(minimum_confidence, bool)
            or not isinstance(minimum_confidence, int | float)
            or not 0.0 <= minimum_confidence <= 1.0
        ):
            raise ValueError("Minimum confidence must be between 0.0 and 1.0.")

        self._database = database
        self._minimum_confidence = minimum_confidence

    def apply_extraction_result(
        self,
        result: ExtractionResult,
        anchors: tuple[EvidenceAnchor, ...],
    ) -> CanonUpdateSummary:
        """Apply accepted extraction candidates to Canon.

        Parameters:
            result: Extraction candidates for one scene.
            anchors: Story Import evidence anchors for the scene.

        Returns:
            Summary of accepted and rejected candidates.

        Raises:
            ValueError: If the extraction result scene does not match the
                supplied evidence anchors.
        """
        self._validate_result_scene(result=result, anchors=anchors)
        anchor_by_id = {anchor.anchor_id: anchor for anchor in anchors}
        accepted_entities: list[str] = []
        accepted_facts: list[str] = []
        accepted_relationships: list[str] = []
        accepted_state_changes: list[str] = []
        rejected_candidates: list[str] = []

        for candidate in result.entities:
            if not self._candidate_is_acceptable(candidate, anchor_by_id):
                rejected_candidates.append(candidate.entity_id)
                continue

            anchor = anchor_by_id[candidate.evidence_anchor_id]
            evidence = self._store_evidence(anchor=anchor, confidence=candidate.confidence)
            self._store_entity(candidate)
            fact = self._store_entity_name_fact(candidate=candidate, evidence=evidence)
            if fact is None:
                accepted_entities.append(candidate.entity_id)
                continue

            event = self._store_event(
                candidate_id=candidate.entity_id,
                anchor=anchor,
                evidence=evidence,
            )
            stored_state_change = self._store_state_change(fact=fact, event=event)
            if stored_state_change is not None:
                accepted_state_changes.append(stored_state_change.state_change_id)
            accepted_entities.append(candidate.entity_id)
            accepted_facts.append(fact.fact_id)

        known_entity_ids = set(accepted_entities)
        for fact_candidate in result.facts:
            if not self._fact_is_acceptable(
                fact=fact_candidate,
                anchor_by_id=anchor_by_id,
                known_entity_ids=known_entity_ids,
            ):
                rejected_candidates.append(fact_candidate.fact_id)
                continue

            anchor = anchor_by_id[fact_candidate.evidence_anchor_id]
            evidence = self._store_evidence(
                anchor=anchor,
                confidence=fact_candidate.confidence,
            )
            fact = self._store_extracted_fact(
                candidate=fact_candidate,
                evidence=evidence,
            )
            if fact is None:
                continue

            event = self._store_event(
                candidate_id=fact_candidate.fact_id,
                anchor=anchor,
                evidence=evidence,
            )
            stored_state_change = self._store_state_change(fact=fact, event=event)
            if stored_state_change is not None:
                accepted_state_changes.append(stored_state_change.state_change_id)
            accepted_facts.append(fact.fact_id)

        for relationship in result.relationships:
            if not self._relationship_is_acceptable(
                relationship=relationship,
                anchor_by_id=anchor_by_id,
                known_entity_ids=known_entity_ids,
            ):
                rejected_candidates.append(
                    self._relationship_id(relationship)
                )
                continue

            anchor = anchor_by_id[relationship.evidence_anchor_id]
            evidence = self._store_evidence(
                anchor=anchor,
                confidence=relationship.confidence,
            )
            stored_relationship = self._store_relationship(
                relationship=relationship,
                evidence=evidence,
            )
            if stored_relationship is not None:
                accepted_relationships.append(stored_relationship.relationship_id)

        for state_change in result.state_changes:
            state_change_id = self._state_change_candidate_id(
                entity_id=state_change.entity_id,
                attribute=state_change.attribute,
                value=state_change.value,
            )
            if not self._state_change_is_acceptable(
                entity_id=state_change.entity_id,
                attribute=state_change.attribute,
                value=state_change.value,
                confidence=state_change.confidence,
                anchor_id=state_change.valid_from_anchor_id,
                anchor_by_id=anchor_by_id,
                known_entity_ids=known_entity_ids,
            ):
                rejected_candidates.append(state_change_id)
                continue

        summary = CanonUpdateSummary(
            accepted_entities=tuple(accepted_entities),
            accepted_facts=tuple(accepted_facts),
            accepted_relationships=tuple(accepted_relationships),
            accepted_state_changes=tuple(accepted_state_changes),
            rejected_candidates=tuple(rejected_candidates),
        )
        logger.info(
            "Applied extraction result to Canon",
            extra={
                "scene_id": result.scene_id,
                "accepted_entities": len(summary.accepted_entities),
                "accepted_facts": len(summary.accepted_facts),
                "accepted_relationships": len(summary.accepted_relationships),
                "accepted_state_changes": len(summary.accepted_state_changes),
                "rejected_candidates": len(summary.rejected_candidates),
            },
        )
        if summary.rejected_candidates:
            logger.warning(
                "Rejected canon candidates",
                extra={
                    "scene_id": result.scene_id,
                    "rejected_candidates": summary.rejected_candidates,
                },
            )

        return summary

    @staticmethod
    def _validate_result_scene(
        result: ExtractionResult,
        anchors: tuple[EvidenceAnchor, ...],
    ) -> None:
        """Ensure extraction results are applied with same-scene evidence anchors."""
        anchor_ids = tuple(anchor.anchor_id for anchor in anchors)
        if len(anchor_ids) != len(set(anchor_ids)):
            raise ValueError("Canon update evidence anchors cannot contain duplicates.")
        mismatched_scene_ids = sorted(
            {anchor.scene_id for anchor in anchors if anchor.scene_id != result.scene_id}
        )
        if mismatched_scene_ids:
            mismatched = ", ".join(mismatched_scene_ids)
            raise ValueError(
                "Extraction result scene_id does not match evidence anchor scenes: "
                f"{mismatched}"
            )

    def _candidate_is_acceptable(
        self,
        candidate: ExtractedEntity,
        anchor_by_id: dict[str, EvidenceAnchor],
    ) -> bool:
        """Return whether an extracted entity can be accepted."""
        anchor = anchor_by_id.get(candidate.evidence_anchor_id)
        return (
            candidate.confidence >= self._minimum_confidence
            and anchor is not None
            and self._display_name_position_is_acceptable(
                candidate=candidate,
                anchor=anchor,
            )
        )

    def _display_name_position_is_acceptable(
        self,
        candidate: ExtractedEntity,
        anchor: EvidenceAnchor,
    ) -> bool:
        """Return whether a display-name update has an unambiguous source order."""
        current_fact = self._database.retrieve_current_fact(
            entity_id=candidate.entity_id,
            attribute="display_name",
        )
        if current_fact is None or current_fact.value == candidate.display_name:
            return True

        current_evidence = self._database.retrieve_evidence(current_fact.evidence_id)
        if current_evidence is None:
            return True

        return self._anchor_position_key(anchor) > self._evidence_position_key(
            current_evidence
        )

    def _relationship_is_acceptable(
        self,
        relationship: ExtractedRelationship,
        anchor_by_id: dict[str, EvidenceAnchor],
        known_entity_ids: set[str],
    ) -> bool:
        """Return whether an extracted relationship can be accepted."""
        return (
            relationship.confidence >= self._minimum_confidence
            and relationship.evidence_anchor_id in anchor_by_id
            and self._entity_is_known(relationship.source_entity_id, known_entity_ids)
            and self._entity_is_known(relationship.target_entity_id, known_entity_ids)
        )

    def _fact_is_acceptable(
        self,
        fact: ExtractedFact,
        anchor_by_id: dict[str, EvidenceAnchor],
        known_entity_ids: set[str],
    ) -> bool:
        """Return whether an extracted fact can be accepted."""
        anchor = anchor_by_id.get(fact.evidence_anchor_id)
        return (
            fact.confidence >= self._minimum_confidence
            and anchor is not None
            and self._entity_is_known(fact.entity_id, known_entity_ids)
            and self._replacement_fact_position_is_acceptable(fact=fact, anchor=anchor)
        )

    def _replacement_fact_position_is_acceptable(
        self,
        fact: ExtractedFact,
        anchor: EvidenceAnchor,
    ) -> bool:
        """Return whether a replacement fact has an unambiguous source order."""
        if is_additive_fact_attribute(fact.attribute):
            return True

        current_fact = self._database.retrieve_current_fact(
            entity_id=fact.entity_id,
            attribute=fact.attribute,
        )
        if current_fact is None or current_fact.value == fact.value:
            return True

        current_evidence = self._database.retrieve_evidence(current_fact.evidence_id)
        if current_evidence is None:
            return True

        return self._anchor_position_key(anchor) > self._evidence_position_key(
            current_evidence
        )

    def _entity_is_known(self, entity_id: str, known_entity_ids: set[str]) -> bool:
        """Return whether an entity is accepted in this result or already known."""
        return (
            entity_id in known_entity_ids
            or self._database.retrieve_entity(entity_id) is not None
        )

    def _state_change_is_acceptable(
        self,
        entity_id: str,
        attribute: str,
        value: str,
        confidence: float,
        anchor_id: str,
        anchor_by_id: dict[str, EvidenceAnchor],
        known_entity_ids: set[str],
    ) -> bool:
        """Return whether an extracted state-change candidate matches Canon."""
        current_fact = self._database.retrieve_current_fact(
            entity_id=entity_id,
            attribute=attribute,
        )
        value_is_current = (
            self._additive_fact_value_is_active(
                entity_id=entity_id,
                attribute=attribute,
                value=value,
            )
            if is_additive_fact_attribute(attribute)
            else current_fact is not None and current_fact.value == value
        )
        return (
            confidence >= self._minimum_confidence
            and anchor_id in anchor_by_id
            and self._entity_is_known(entity_id, known_entity_ids)
            and value_is_current
        )

    def _additive_fact_value_is_active(
        self,
        entity_id: str,
        attribute: str,
        value: str,
    ) -> bool:
        """Return whether an additive fact value is currently active."""
        history = self._database.retrieve_fact_history(
            entity_id=entity_id,
            attribute=attribute,
        )
        if not history:
            return False

        chapter_indexes = tuple(
            self._chapter_index_from_id(evidence.chapter_id)
            for fact in history
            if (evidence := self._database.retrieve_evidence(fact.evidence_id))
            is not None
        )
        if not chapter_indexes:
            return False

        chapter_index = max(chapter_indexes)
        return any(
            fact.value == value
            for fact in self._database.retrieve_state_at_chapter(
                entity_id=entity_id,
                chapter_index=chapter_index,
            )
            if fact.attribute == attribute
        )

    def _store_evidence(self, anchor: EvidenceAnchor, confidence: float) -> Evidence:
        """Store evidence converted from an evidence anchor."""
        evidence_id = self._evidence_id(anchor.anchor_id)
        existing_evidence = self._database.retrieve_evidence(evidence_id)
        if existing_evidence is not None:
            return existing_evidence

        if self._database.retrieve_chapter(anchor.chapter_id) is None:
            self._database.store_chapter(chapter=self._chapter_from_anchor(anchor))

        evidence = Evidence(
            evidence_id=evidence_id,
            source_id=anchor.source_id,
            chapter_id=anchor.chapter_id,
            scene_id=anchor.scene_id,
            paragraph_index=anchor.paragraph_index,
            sentence_index=anchor.sentence_index,
            quote=anchor.quote,
            confidence=confidence,
        )
        self._database.store_evidence(evidence)
        return evidence

    def _store_entity(self, candidate: ExtractedEntity) -> None:
        """Store or update a core entity wrapper based on candidate type."""
        entity = Entity(
            entity_id=candidate.entity_id,
            entity_type=candidate.entity_type,
            display_name=candidate.display_name,
        )
        self._store_generic_entity(entity)
        if candidate.entity_type == "character":
            self._store_character(Character(entity=entity))

    def _store_generic_entity(self, entity: Entity) -> None:
        """Store or version a generic entity."""
        if self._database.retrieve_entity(entity.entity_id) is None:
            self._database.store_entity(entity)
            return

        self._database.update_entity(entity)

    def _store_character(self, character: Character) -> None:
        """Store or version a character."""
        if self._database.retrieve_character(character.entity.entity_id) is None:
            self._database.store_character(character)
            return

        self._database.update_character(character)

    def _store_entity_name_fact(
        self,
        candidate: ExtractedEntity,
        evidence: Evidence,
    ) -> Fact | None:
        """Store a display-name fact for an accepted entity."""
        current_fact = self._database.retrieve_current_fact(
            entity_id=candidate.entity_id,
            attribute="display_name",
        )
        if current_fact is not None and current_fact.value == candidate.display_name:
            return None

        fact = Fact(
            fact_id=self._fact_id(
                candidate.entity_id,
                "display_name",
                candidate.display_name,
                evidence.evidence_id,
            ),
            entity_id=candidate.entity_id,
            attribute="display_name",
            value=candidate.display_name,
            evidence_id=evidence.evidence_id,
        )
        self._database.store_fact(fact)
        return fact

    def _store_extracted_fact(
        self,
        candidate: ExtractedFact,
        evidence: Evidence,
    ) -> Fact | None:
        """Store an extracted fact candidate."""
        current_fact = self._database.retrieve_current_fact(
            entity_id=candidate.entity_id,
            attribute=candidate.attribute,
        )
        if (
            current_fact is not None
            and current_fact.value == candidate.value
            and not is_additive_fact_attribute(candidate.attribute)
        ):
            return None

        fact = Fact(
            fact_id=candidate.fact_id,
            entity_id=candidate.entity_id,
            attribute=candidate.attribute,
            value=candidate.value,
            evidence_id=evidence.evidence_id,
        )
        self._database.store_fact(fact)
        return fact

    def _store_event(
        self,
        candidate_id: str,
        anchor: EvidenceAnchor,
        evidence: Evidence,
    ) -> TimelineEvent:
        """Store a timeline event for an accepted candidate."""
        event = TimelineEvent(
            event_id=self._event_id(candidate_id, evidence.evidence_id),
            chapter_id=anchor.chapter_id,
            scene_id=anchor.scene_id,
            description=f"Accepted canon candidate {candidate_id}",
            evidence_id=evidence.evidence_id,
        )
        self._database.store_timeline_event(event)
        return event

    def _store_state_change(
        self,
        fact: Fact,
        event: TimelineEvent,
    ) -> StateChange | None:
        """Store a state change for an accepted fact."""
        state_change_id = self._state_change_id(fact.fact_id)
        if self._database.retrieve_state_change(state_change_id) is not None:
            return None

        self._database.close_open_state_changes(
            entity_id=fact.entity_id,
            attribute=fact.attribute,
            valid_until_event_id=event.event_id,
        )
        state_change = StateChange(
            state_change_id=state_change_id,
            fact_id=fact.fact_id,
            valid_from_event_id=event.event_id,
        )
        self._database.store_state_change(state_change)
        return state_change

    def _store_relationship(
        self,
        relationship: ExtractedRelationship,
        evidence: Evidence,
    ) -> Relationship | None:
        """Store an accepted relationship if it is not already known."""
        stored_relationship = Relationship(
            relationship_id=self._relationship_id(relationship),
            source_entity_id=relationship.source_entity_id,
            relationship_type=relationship.relationship_type,
            target_entity_id=relationship.target_entity_id,
            evidence_id=evidence.evidence_id,
        )
        if self._relationship_already_exists(stored_relationship):
            return None

        self._database.store_relationship(stored_relationship)
        return stored_relationship

    def _relationship_already_exists(self, relationship: Relationship) -> bool:
        """Return whether Canon already has the same semantic relationship."""
        return any(
            existing.source_entity_id == relationship.source_entity_id
            and existing.relationship_type == relationship.relationship_type
            and existing.target_entity_id == relationship.target_entity_id
            for existing in self._database.list_relationships_for_entity(
                relationship.source_entity_id
            )
        )

    @staticmethod
    def _chapter_from_anchor(anchor: EvidenceAnchor) -> Chapter:
        """Build minimal chapter data from an evidence anchor."""
        return Chapter(
            chapter_id=anchor.chapter_id,
            story_id=anchor.source_id,
            chapter_index=CanonUpdater._chapter_index_from_id(anchor.chapter_id),
            title=anchor.chapter_id,
        )

    @staticmethod
    def _chapter_index_from_id(chapter_id: str) -> int:
        """Extract a chapter index from a generated chapter ID."""
        return int(chapter_id.rsplit("_", maxsplit=1)[-1])

    @classmethod
    def _anchor_position_key(cls, anchor: EvidenceAnchor) -> tuple[int, int, int, int]:
        """Return a story-order source key for an evidence anchor."""
        return (
            cls._chapter_index_from_id(anchor.chapter_id),
            cls._scene_index_from_id(anchor.scene_id),
            anchor.paragraph_index,
            anchor.sentence_index,
        )

    @classmethod
    def _evidence_position_key(cls, evidence: Evidence) -> tuple[int, int, int, int]:
        """Return a story-order source key for stored evidence."""
        return (
            cls._chapter_index_from_id(evidence.chapter_id),
            cls._scene_index_from_id(evidence.scene_id),
            evidence.paragraph_index,
            evidence.sentence_index,
        )

    @staticmethod
    def _scene_index_from_id(scene_id: str) -> int:
        """Extract a scene index from a generated scene ID."""
        return int(scene_id.rsplit("_", maxsplit=1)[-1])

    @staticmethod
    def _evidence_id(anchor_id: str) -> str:
        """Build evidence ID from an anchor ID."""
        return f"evidence_{anchor_id}"

    @staticmethod
    def _fact_id(entity_id: str, attribute: str, value: str, evidence_id: str) -> str:
        """Build fact ID."""
        normalized_value = value.lower().replace(" ", "_")
        return f"fact_{entity_id}_{attribute}_{normalized_value}_{evidence_id}"

    @staticmethod
    def _event_id(candidate_id: str, evidence_id: str) -> str:
        """Build timeline event ID."""
        return f"event_{candidate_id}_{evidence_id}"

    @staticmethod
    def _state_change_id(fact_id: str) -> str:
        """Build state change ID."""
        return f"state_{fact_id}"

    @staticmethod
    def _state_change_candidate_id(entity_id: str, attribute: str, value: str) -> str:
        """Build state-change candidate ID."""
        normalized_value = value.lower().replace(" ", "_")
        return f"state_candidate_{entity_id}_{attribute}_{normalized_value}"

    @staticmethod
    def _relationship_id(relationship: ExtractedRelationship) -> str:
        """Build relationship ID."""
        return (
            f"relationship_{relationship.source_entity_id}_"
            f"{relationship.relationship_type}_{relationship.target_entity_id}"
        )


def _require_unique_machine_tokens(values: tuple[str, ...], field_name: str) -> None:
    """Validate summary IDs in one bucket."""
    if len(values) != len(set(values)):
        raise ValueError(f"Canon summary {field_name} IDs cannot contain duplicates.")
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Canon summary {field_name} ID is required.")
        if any(character.isspace() for character in value):
            raise ValueError(
                f"Canon summary {field_name} ID cannot contain whitespace."
            )

"""In-memory Canon Engine implementation."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import replace

from scenesmith.canon.exceptions import (
    DuplicateEntityError,
    MissingEvidenceError,
    UnknownEntityError,
)
from scenesmith.canon.models import (
    CanonConflict,
    CanonEntity,
    CanonFactVersion,
    CanonRelationship,
    CanonSnapshot,
    EntityType,
    Evidence,
    StoryPosition,
)

logger = logging.getLogger(__name__)


class CanonEngine:
    """Maintain evidence-backed canon state and version history.

    The engine stores permanent entities, versioned facts, and relationships in
    memory. It does not parse stories, extract facts, generate prompts, or write
    to a database.
    """

    def __init__(self) -> None:
        """Create an empty Canon Engine."""
        self._entities: dict[str, CanonEntity] = {}
        self._fact_history: dict[tuple[str, str], list[CanonFactVersion]] = defaultdict(list)
        self._relationships: list[CanonRelationship] = []
        self._conflicts: list[CanonConflict] = []

    def register_entity(self, entity: CanonEntity) -> None:
        """Register a permanent canon entity.

        Parameters:
            entity: Entity to register.

        Raises:
            DuplicateEntityError: If the entity ID is already registered.
        """
        if entity.entity_id in self._entities:
            raise DuplicateEntityError(f"Entity already exists: {entity.entity_id}")

        self._entities[entity.entity_id] = entity

    def rename_entity(
        self,
        entity_id: str,
        display_name: str,
        evidence: Evidence,
    ) -> CanonFactVersion:
        """Rename an entity while preserving its permanent ID.

        Parameters:
            entity_id: Permanent entity ID to rename.
            display_name: New human-readable display name.
            evidence: Evidence proving the name change.

        Returns:
            Fact version recording the display name change.

        Raises:
            MissingEvidenceError: If evidence is missing.
            UnknownEntityError: If the entity has not been registered.
            ValueError: If the display name is empty.
        """
        self._require_registered_entity(entity_id)
        self._require_evidence(evidence)
        if not display_name.strip():
            raise ValueError("Entity display name is required.")

        self._entities[entity_id] = replace(
            self._entities[entity_id],
            display_name=display_name,
        )
        return self.record_fact(
            entity_id=entity_id,
            attribute="display_name",
            value=display_name,
            evidence=evidence,
        )

    def get_entity(self, entity_id: str) -> CanonEntity | None:
        """Return an entity by ID.

        Parameters:
            entity_id: Permanent entity ID to retrieve.

        Returns:
            The matching entity, or None when it has not been registered.
        """
        return self._entities.get(entity_id)

    def list_entities(self, entity_type: EntityType | None = None) -> Sequence[CanonEntity]:
        """Return registered entities in insertion order.

        Parameters:
            entity_type: Optional entity type value used to filter entities.

        Returns:
            Immutable sequence view of registered canon entities.
        """
        if entity_type is not None:
            return tuple(
                entity
                for entity in self._entities.values()
                if entity.entity_type == entity_type
            )

        return tuple(self._entities.values())

    def record_fact(
        self,
        entity_id: str,
        attribute: str,
        value: str,
        evidence: Evidence,
    ) -> CanonFactVersion:
        """Record a new evidence-backed version of a canon fact.

        Parameters:
            entity_id: Entity that owns the fact.
            attribute: Fact name, such as current_weapon.
            value: Fact value to record.
            evidence: Evidence proving the value.

        Returns:
            The newly recorded fact version.

        Raises:
            MissingEvidenceError: If evidence is missing.
            UnknownEntityError: If the entity has not been registered.
            ValueError: If entity, attribute, or value are empty.
        """
        self._require_registered_entity(entity_id)
        self._require_evidence(evidence)

        history_key = self._fact_history_key(entity_id, attribute)
        history = self._fact_history[history_key]
        if history and history[-1].value == value and history[-1].evidence == evidence:
            logger.debug(
                "canon_engine_duplicate_fact_ignored",
                extra={"entity_id": entity_id, "attribute": attribute},
            )
            return history[-1]

        previous_value = history[-1].value if history else None
        version = CanonFactVersion(
            entity_id=entity_id,
            attribute=attribute,
            value=value,
            evidence=evidence,
            previous_value=previous_value,
        )

        self._record_conflict_if_needed(history, version)
        history.append(version)
        return version

    def get_current_fact(self, entity_id: str, attribute: str) -> CanonFactVersion | None:
        """Return the current version of a canon fact.

        Parameters:
            entity_id: Entity that owns the fact.
            attribute: Fact name to retrieve.

        Returns:
            Latest fact version, or None if the fact is unknown.

        Raises:
            UnknownEntityError: If the entity has not been registered.
        """
        self._require_registered_entity(entity_id)
        history = self.get_fact_history(entity_id, attribute)
        if not history:
            return None

        return history[-1]

    def get_fact_at(
        self,
        entity_id: str,
        attribute: str,
        position: StoryPosition,
    ) -> CanonFactVersion | None:
        """Return the canon fact version active at a story position.

        Parameters:
            entity_id: Entity that owns the fact.
            attribute: Fact name to retrieve.
            position: Story position to inspect.

        Returns:
            Latest fact version at or before the requested position, or None
            when the fact was still unknown.

        Raises:
            UnknownEntityError: If the entity has not been registered.
        """
        self._require_registered_entity(entity_id)
        matching_versions = tuple(
            version
            for version in self.get_fact_history(entity_id, attribute)
            if version.evidence.position is not None and version.evidence.position <= position
        )
        if not matching_versions:
            return None

        return max(
            matching_versions,
            key=lambda version: version.evidence.position or StoryPosition(1, 1),
        )

    def get_fact_history(self, entity_id: str, attribute: str) -> Sequence[CanonFactVersion]:
        """Return all versions for a canon fact.

        Parameters:
            entity_id: Entity that owns the fact.
            attribute: Fact name to retrieve.

        Returns:
            Immutable sequence of fact versions from oldest to newest.

        Raises:
            UnknownEntityError: If the entity has not been registered.
        """
        self._require_registered_entity(entity_id)
        history_key = self._fact_history_key(entity_id, attribute)
        return tuple(self._fact_history.get(history_key, ()))

    def list_current_facts(self, entity_id: str) -> dict[str, CanonFactVersion]:
        """Return the current fact map for an entity.

        Parameters:
            entity_id: Entity whose current facts should be returned.

        Returns:
            Dictionary keyed by fact attribute.

        Raises:
            UnknownEntityError: If the entity has not been registered.
        """
        self._require_registered_entity(entity_id)
        return {
            attribute: history[-1]
            for (history_entity_id, attribute), history in self._fact_history.items()
            if history_entity_id == entity_id and history
        }

    def snapshot_entity(
        self,
        entity_id: str,
        position: StoryPosition | None = None,
    ) -> CanonSnapshot:
        """Return a canon snapshot for an entity.

        Parameters:
            entity_id: Entity to snapshot.
            position: Optional story position. If omitted, the current state is
                returned.

        Returns:
            Snapshot containing facts and relationships for the requested point.

        Raises:
            UnknownEntityError: If the entity has not been registered.
        """
        self._require_registered_entity(entity_id)
        facts = self._facts_at_position(entity_id, position)
        relationships = self._relationships_at_position(entity_id, position)
        return CanonSnapshot(
            entity_id=entity_id,
            facts=facts,
            relationships=relationships,
        )

    def snapshot_all(self, position: StoryPosition | None = None) -> Sequence[CanonSnapshot]:
        """Return canon snapshots for every registered entity.

        Parameters:
            position: Optional story position. If omitted, current state is
                returned.

        Returns:
            Immutable sequence of entity snapshots.
        """
        return tuple(
            self.snapshot_entity(
                entity_id=entity.entity_id,
                position=position,
            )
            for entity in self._entities.values()
        )

    def record_relationship(
        self,
        source_entity_id: str,
        relationship_type: str,
        target_entity_id: str,
        evidence: Evidence,
    ) -> CanonRelationship:
        """Record an evidence-backed relationship between two entities.

        Parameters:
            source_entity_id: Entity where the relationship starts.
            relationship_type: Relationship label, such as owns.
            target_entity_id: Entity where the relationship ends.
            evidence: Evidence proving the relationship.

        Returns:
            The newly recorded relationship.

        Raises:
            MissingEvidenceError: If evidence is missing.
            UnknownEntityError: If either entity has not been registered.
        """
        self._require_registered_entity(source_entity_id)
        self._require_registered_entity(target_entity_id)
        self._require_evidence(evidence)

        relationship = CanonRelationship(
            source_entity_id=source_entity_id,
            relationship_type=relationship_type,
            target_entity_id=target_entity_id,
            evidence=evidence,
        )
        existing_relationship = self._find_relationship_by_semantic_key(relationship)
        if existing_relationship is not None:
            logger.debug(
                "canon_engine_duplicate_relationship_ignored",
                extra={
                    "source_entity_id": source_entity_id,
                    "relationship_type": relationship_type,
                    "target_entity_id": target_entity_id,
                },
            )
            return existing_relationship

        self._relationships.append(relationship)
        return relationship

    def list_relationships(
        self,
        entity_id: str | None = None,
        position: StoryPosition | None = None,
    ) -> Sequence[CanonRelationship]:
        """Return recorded relationships.

        Parameters:
            entity_id: Optional entity ID used to filter relationships where the
                entity is either the source or target.
            position: Optional story position used to return relationships
                recorded at or before that point.

        Returns:
            Immutable sequence of matching relationships.
        """
        relationships = self._relationships
        if position is not None:
            relationships = [
                relationship
                for relationship in relationships
                if relationship.evidence.position is not None
                and relationship.evidence.position <= position
            ]

        if entity_id is None:
            return tuple(relationships)

        self._require_registered_entity(entity_id)
        return tuple(
            relationship
            for relationship in relationships
            if self._relationship_contains_entity(relationship, entity_id)
        )

    def list_conflicts(self) -> Sequence[CanonConflict]:
        """Return preserved canon conflicts.

        Returns:
            Immutable sequence of detected conflicting fact versions.
        """
        return tuple(self._conflicts)

    @staticmethod
    def _fact_history_key(entity_id: str, attribute: str) -> tuple[str, str]:
        """Build the internal key for a versioned fact history."""
        return (entity_id, attribute)

    @staticmethod
    def _require_evidence(evidence: Evidence | None) -> None:
        """Ensure a canon operation includes evidence."""
        if evidence is None:
            raise MissingEvidenceError("Canon updates require evidence.")

    def _require_registered_entity(self, entity_id: str) -> None:
        """Ensure an operation references a known entity."""
        if entity_id not in self._entities:
            raise UnknownEntityError(f"Unknown entity: {entity_id}")

    @staticmethod
    def _relationship_contains_entity(
        relationship: CanonRelationship,
        entity_id: str,
    ) -> bool:
        """Return whether a relationship references an entity."""
        return (
            relationship.source_entity_id == entity_id
            or relationship.target_entity_id == entity_id
        )

    def _record_conflict_if_needed(
        self,
        history: Sequence[CanonFactVersion],
        new_version: CanonFactVersion,
    ) -> None:
        """Preserve same-position contradictions without blocking updates."""
        for existing_version in history:
            if (
                existing_version.evidence.position == new_version.evidence.position
                and existing_version.value != new_version.value
            ):
                self._conflicts.append(
                    CanonConflict(
                        entity_id=new_version.entity_id,
                        attribute=new_version.attribute,
                        existing_version=existing_version,
                        conflicting_version=new_version,
                    )
                )

    def _find_relationship_by_semantic_key(
        self,
        relationship: CanonRelationship,
    ) -> CanonRelationship | None:
        """Return an existing relationship with the same semantic connection."""
        for existing_relationship in self._relationships:
            if (
                existing_relationship.source_entity_id == relationship.source_entity_id
                and existing_relationship.relationship_type == relationship.relationship_type
                and existing_relationship.target_entity_id == relationship.target_entity_id
            ):
                return existing_relationship

        return None

    def _facts_at_position(
        self,
        entity_id: str,
        position: StoryPosition | None,
    ) -> dict[str, CanonFactVersion]:
        """Return fact versions active at a position."""
        if position is None:
            return self.list_current_facts(entity_id)

        facts: dict[str, CanonFactVersion] = {}
        attributes = {
            attribute
            for history_entity_id, attribute in self._fact_history
            if history_entity_id == entity_id
        }
        for attribute in attributes:
            fact = self.get_fact_at(entity_id, attribute, position)
            if fact is not None:
                facts[attribute] = fact

        return facts

    def _relationships_at_position(
        self,
        entity_id: str,
        position: StoryPosition | None,
    ) -> tuple[CanonRelationship, ...]:
        """Return relationships active at a position."""
        return tuple(self.list_relationships(entity_id=entity_id, position=position))

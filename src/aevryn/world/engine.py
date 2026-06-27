"""World Engine implementation."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from aevryn.canon import CanonDatabase
from aevryn.core import Entity, Fact, Relationship
from aevryn.world.models import WorldEntityFact, WorldEntityState, WorldState

logger = logging.getLogger(__name__)


class WorldStateBuilder:
    """Build world state views from accepted Canon truth.

    The World Engine owns world-state presentation for locations, buildings,
    organizations, items, vehicles, creatures, and environmental entities. It
    does not parse stories, extract candidates, generate prompts, or mutate
    Canon.
    """

    def __init__(self, database: CanonDatabase) -> None:
        """Create a World State Builder.

        Parameters:
            database: Canon Database used as the source of truth.
        """
        self._database = database

    def build_state(
        self,
        entity_ids: tuple[str, ...],
        chapter_index: int,
    ) -> WorldState:
        """Build world state for selected entities at a chapter.

        Parameters:
            entity_ids: World entity IDs to reconstruct.
            chapter_index: One-based chapter index.

        Returns:
            World state containing requested entity states.

        Raises:
            ValueError: If a requested entity is unknown.
        """
        self._validate_chapter_index(chapter_index)
        for entity_id in entity_ids:
            self._validate_entity_id(entity_id)
        return WorldState(
            chapter_index=chapter_index,
            entities=tuple(
                self.build_entity_state(
                    entity_id=entity_id,
                    chapter_index=chapter_index,
                )
                for entity_id in entity_ids
            ),
        )

    def build_state_at_scene(
        self,
        entity_ids: tuple[str, ...],
        chapter_index: int,
        scene_index: int,
    ) -> WorldState:
        """Build world state for selected entities at a scene position.

        Parameters:
            entity_ids: World entity IDs to reconstruct.
            chapter_index: One-based chapter index.
            scene_index: One-based scene index.

        Returns:
            World state containing requested entity states.

        Raises:
            ValueError: If a requested entity is unknown or the position is invalid.
        """
        self._validate_chapter_index(chapter_index)
        self._validate_scene_index(scene_index)
        for entity_id in entity_ids:
            self._validate_entity_id(entity_id)
        return WorldState(
            chapter_index=chapter_index,
            entities=tuple(
                self.build_entity_state_at_scene(
                    entity_id=entity_id,
                    chapter_index=chapter_index,
                    scene_index=scene_index,
                )
                for entity_id in entity_ids
            ),
        )

    def build_entity_state(
        self,
        entity_id: str,
        chapter_index: int,
    ) -> WorldEntityState:
        """Build world state for one entity at a chapter.

        Parameters:
            entity_id: World entity ID to reconstruct.
            chapter_index: One-based chapter index.

        Returns:
            World entity state.

        Raises:
            ValueError: If the entity is unknown or fact evidence is missing.
        """
        self._validate_chapter_index(chapter_index)
        self._validate_entity_id(entity_id)
        entity = self._database.retrieve_entity(entity_id)
        if entity is None:
            raise ValueError(f"Unknown world entity: {entity_id}")
        if entity.entity_type == "character":
            raise ValueError(f"Entity is not a world entity: {entity_id}")

        active_facts = self._database.retrieve_state_at_chapter(
            entity_id=entity_id,
            chapter_index=chapter_index,
        )
        relationships = self._relationships_for_entity_at_chapter(
            entity_id=entity_id,
            chapter_index=chapter_index,
        )
        return self._build_entity_state_from_active_records(
            entity=entity,
            chapter_index=chapter_index,
            active_facts=active_facts,
            relationships=relationships,
        )

    def build_entity_state_at_scene(
        self,
        entity_id: str,
        chapter_index: int,
        scene_index: int,
    ) -> WorldEntityState:
        """Build world state for one entity at a scene position.

        Parameters:
            entity_id: World entity ID to reconstruct.
            chapter_index: One-based chapter index.
            scene_index: One-based scene index.

        Returns:
            World entity state.

        Raises:
            ValueError: If the entity is unknown or the position is invalid.
        """
        self._validate_chapter_index(chapter_index)
        self._validate_scene_index(scene_index)
        self._validate_entity_id(entity_id)
        entity = self._database.retrieve_entity(entity_id)
        if entity is None:
            raise ValueError(f"Unknown world entity: {entity_id}")
        if entity.entity_type == "character":
            raise ValueError(f"Entity is not a world entity: {entity_id}")

        active_facts = self._database.retrieve_state_at_scene(
            entity_id=entity_id,
            chapter_index=chapter_index,
            scene_index=scene_index,
        )
        relationships = self._relationships_for_entity_at_scene(
            entity_id=entity_id,
            chapter_index=chapter_index,
            scene_index=scene_index,
        )
        return self._build_entity_state_from_active_records(
            entity=entity,
            chapter_index=chapter_index,
            active_facts=active_facts,
            relationships=relationships,
        )

    def _build_entity_state_from_active_records(
        self,
        entity: Entity,
        chapter_index: int,
        active_facts: Sequence[Fact],
        relationships: tuple[Relationship, ...],
    ) -> WorldEntityState:
        """Build a world entity state from selected active Canon records."""
        world_facts = tuple(self._build_fact(fact) for fact in active_facts)
        display_name = self._display_name_from_facts(
            fallback=entity.display_name,
            facts=world_facts,
        )
        logger.debug(
            "world_entity_state_built",
            extra={
                "entity_id": entity.entity_id,
                "chapter_index": chapter_index,
                "fact_count": len(world_facts),
                "relationship_count": len(relationships),
            },
        )
        return WorldEntityState(
            entity_id=entity.entity_id,
            entity_type=entity.entity_type,
            display_name=display_name,
            chapter_index=chapter_index,
            facts=world_facts,
            relationships=relationships,
        )

    def _build_fact(self, fact: Fact) -> WorldEntityFact:
        """Build a world fact with evidence details."""
        evidence = self._database.retrieve_evidence(fact.evidence_id)
        if evidence is None:
            raise ValueError(f"Missing evidence for fact: {fact.fact_id}")

        return WorldEntityFact(
            attribute=fact.attribute,
            value=fact.value,
            evidence=evidence,
            valid_from_chapter_id=evidence.chapter_id,
            valid_from_scene_id=evidence.scene_id,
        )

    def _relationships_for_entity_at_chapter(
        self,
        entity_id: str,
        chapter_index: int,
    ) -> tuple[Relationship, ...]:
        """Return validated relationships connected at a chapter."""
        relationships = tuple(
            sorted(
                self._database.list_relationships_for_entity_at_chapter(
                    entity_id=entity_id,
                    chapter_index=chapter_index,
                ),
                key=lambda relationship: relationship.relationship_id,
            )
        )
        self._validate_relationship_endpoints(
            entity_id=entity_id,
            relationships=relationships,
        )
        return relationships

    def _relationships_for_entity_at_scene(
        self,
        entity_id: str,
        chapter_index: int,
        scene_index: int,
    ) -> tuple[Relationship, ...]:
        """Return validated relationships connected at a scene."""
        relationships = tuple(
            sorted(
                self._database.list_relationships_for_entity_at_scene(
                    entity_id=entity_id,
                    chapter_index=chapter_index,
                    scene_index=scene_index,
                ),
                key=lambda relationship: relationship.relationship_id,
            )
        )
        self._validate_relationship_endpoints(
            entity_id=entity_id,
            relationships=relationships,
        )
        return relationships

    def _validate_relationship_endpoints(
        self,
        entity_id: str,
        relationships: tuple[Relationship, ...],
    ) -> None:
        """Validate relationship endpoints connected to a world entity."""
        for relationship in relationships:
            connected_entity_id = self._connected_entity_id(relationship, entity_id)
            if self._database.retrieve_entity(connected_entity_id) is None:
                raise ValueError(f"Unknown related world entity: {connected_entity_id}")

    @staticmethod
    def _connected_entity_id(relationship: Relationship, entity_id: str) -> str:
        """Return the entity ID on the other side of a relationship."""
        if relationship.source_entity_id == entity_id:
            return relationship.target_entity_id

        return relationship.source_entity_id

    @staticmethod
    def _display_name_from_facts(
        fallback: str,
        facts: tuple[WorldEntityFact, ...],
    ) -> str:
        """Return the active display name fact when one exists."""
        for fact in facts:
            if fact.attribute == "display_name":
                return fact.value

        return fallback

    @staticmethod
    def _validate_chapter_index(chapter_index: int) -> None:
        """Validate one-based chapter lookup positions."""
        if (
            isinstance(chapter_index, bool)
            or not isinstance(chapter_index, int)
            or chapter_index < 1
        ):
            raise ValueError("Chapter index must be at least 1.")

    @staticmethod
    def _validate_scene_index(scene_index: int) -> None:
        """Validate one-based scene lookup positions."""
        if (
            isinstance(scene_index, bool)
            or not isinstance(scene_index, int)
            or scene_index < 1
        ):
            raise ValueError("Scene index must be at least 1.")

    @staticmethod
    def _validate_entity_id(entity_id: str) -> None:
        """Validate a selected world entity ID."""
        if not isinstance(entity_id, str) or not entity_id.strip():
            raise ValueError("World entity ID is required.")
        if any(character.isspace() for character in entity_id):
            raise ValueError("World entity ID cannot contain whitespace.")

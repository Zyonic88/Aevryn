"""World Engine implementation."""

from __future__ import annotations

import logging

from scenesmith.canon import CanonDatabase
from scenesmith.core import Fact, Relationship
from scenesmith.world.models import WorldEntityFact, WorldEntityState, WorldState

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
        entity = self._database.retrieve_entity(entity_id)
        if entity is None:
            raise ValueError(f"Unknown world entity: {entity_id}")
        if entity.entity_type == "character":
            raise ValueError(f"Entity is not a world entity: {entity_id}")

        active_facts = self._database.retrieve_state_at_chapter(
            entity_id=entity_id,
            chapter_index=chapter_index,
        )
        world_facts = tuple(self._build_fact(fact) for fact in active_facts)
        relationships = self._relationships_for_entity(entity_id)
        display_name = self._display_name_from_facts(
            fallback=entity.display_name,
            facts=world_facts,
        )
        logger.debug(
            "world_entity_state_built",
            extra={
                "entity_id": entity_id,
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

    def _relationships_for_entity(self, entity_id: str) -> tuple[Relationship, ...]:
        """Return validated relationships connected to a world entity."""
        relationships = tuple(
            sorted(
                self._database.list_relationships_for_entity(entity_id),
                key=lambda relationship: relationship.relationship_id,
            )
        )
        for relationship in relationships:
            connected_entity_id = self._connected_entity_id(relationship, entity_id)
            if self._database.retrieve_entity(connected_entity_id) is None:
                raise ValueError(f"Unknown related world entity: {connected_entity_id}")

        return relationships

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

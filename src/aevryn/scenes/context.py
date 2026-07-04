"""Phase 7 scene context builder over Canon Database."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from aevryn.canon import CanonDatabase
from aevryn.canon.policies import (
    is_current_state_relationship_type,
    is_scene_context_fact_attribute,
)
from aevryn.characters import CanonCharacterCard, CharacterCardBuilder
from aevryn.core import Fact, Relationship, Scene, SceneSnapshot
from aevryn.importing import ImportedSource

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CanonSceneContext:
    """Scene context reconstructed from accepted Canon state."""

    snapshot: SceneSnapshot
    scene: Scene
    character_cards: tuple[CanonCharacterCard, ...]
    active_facts: tuple[Fact, ...]
    relationships: tuple[Relationship, ...]

    def __post_init__(self) -> None:
        """Validate scene context snapshot consistency."""
        if self.snapshot.scene_id != self.scene.scene_id:
            raise ValueError("Scene context snapshot must reference the scene.")
        snapshot_character_ids = set(self.snapshot.character_ids)
        card_character_ids = {card.character_id for card in self.character_cards}
        if snapshot_character_ids != card_character_ids:
            raise ValueError("Scene context snapshot character IDs must match cards.")
        if set(self.snapshot.fact_ids) != {fact.fact_id for fact in self.active_facts}:
            raise ValueError("Scene context snapshot fact IDs must match active facts.")
        if set(self.snapshot.relationship_ids) != {
            relationship.relationship_id for relationship in self.relationships
        }:
            raise ValueError(
                "Scene context snapshot relationship IDs must match relationships."
            )


class SceneContextBuilder:
    """Build scene context from imported structure and accepted Canon."""

    def __init__(self, database: CanonDatabase, character_cards: CharacterCardBuilder) -> None:
        """Create a Scene Context Builder.

        Parameters:
            database: Canon Database used as source of accepted truth.
            character_cards: Character Card Builder used for character state.
        """
        self._database = database
        self._character_cards = character_cards

    def build_context(
        self,
        imported_source: ImportedSource,
        scene_id: str,
        character_ids: tuple[str, ...],
    ) -> CanonSceneContext:
        """Build scene context for an imported scene.

        Parameters:
            imported_source: Source structure produced by Story Import.
            scene_id: Scene to reconstruct.
            character_ids: Characters known to be present in the scene.

        Returns:
            Scene context for the requested scene.

        Raises:
            ValueError: If the scene ID is not found.
        """
        chapter_index, scene = self._find_scene(imported_source, scene_id)
        unique_character_ids = self._dedupe_ids(character_ids)
        cards = tuple(
            self._character_cards.build_card_at_scene(
                character_id=character_id,
                chapter_index=chapter_index,
                scene_index=scene.scene_index,
            )
            for character_id in unique_character_ids
        )
        character_facts = tuple(
            fact
            for character_id in unique_character_ids
            for fact in self._database.retrieve_state_at_scene(
                entity_id=character_id,
                chapter_index=chapter_index,
                scene_index=scene.scene_index,
            )
            if self._fact_is_scene_relevant(
                fact=fact,
                chapter_index=chapter_index,
            )
        )
        relationships = self._dedupe_relationships(
            relationship
            for character_id in unique_character_ids
            for relationship in self._database.list_relationships_for_entity_at_scene(
                entity_id=character_id,
                chapter_index=chapter_index,
                scene_index=scene.scene_index,
            )
            if self._relationship_is_scene_relevant(
                relationship=relationship,
                chapter_index=chapter_index,
                character_ids=unique_character_ids,
            )
        )
        context_entity_ids = self._context_entity_ids(
            character_ids=unique_character_ids,
            relationships=relationships,
        )
        world_facts = tuple(
            fact
            for entity_id in context_entity_ids
            for fact in self._database.retrieve_state_at_scene(
                entity_id=entity_id,
                chapter_index=chapter_index,
                scene_index=scene.scene_index,
            )
            if self._fact_is_scene_relevant(
                fact=fact,
                chapter_index=chapter_index,
            )
        )
        active_facts = self._dedupe_facts((*character_facts, *world_facts))
        location_ids = self._location_ids_from_relationships(relationships)
        snapshot = SceneSnapshot(
            snapshot_id=f"snapshot_{scene.scene_id}",
            scene_id=scene.scene_id,
            character_ids=unique_character_ids,
            location_ids=location_ids,
            fact_ids=tuple(fact.fact_id for fact in active_facts),
            relationship_ids=tuple(
                relationship.relationship_id for relationship in relationships
            ),
        )
        logger.debug(
            "canon_scene_context_built",
            extra={
                "scene_id": scene.scene_id,
                "character_count": len(unique_character_ids),
                "fact_count": len(active_facts),
                "relationship_count": len(relationships),
                "location_count": len(location_ids),
            },
        )

        return CanonSceneContext(
            snapshot=snapshot,
            scene=scene,
            character_cards=cards,
            active_facts=active_facts,
            relationships=relationships,
        )

    @staticmethod
    def _find_scene(imported_source: ImportedSource, scene_id: str) -> tuple[int, Scene]:
        """Find a scene and its chapter index."""
        for chapter in imported_source.story.chapters:
            for scene in chapter.scenes:
                if scene.scene_id == scene_id:
                    return chapter.chapter_index, scene

        raise ValueError(f"Unknown scene: {scene_id}")

    @staticmethod
    def _dedupe_relationships(
        relationships: Iterable[Relationship],
    ) -> tuple[Relationship, ...]:
        """Return relationships without duplicate IDs."""
        deduped: dict[str, Relationship] = {}
        for relationship in relationships:
            deduped.setdefault(relationship.relationship_id, relationship)

        return tuple(
            deduped[relationship_id]
            for relationship_id in sorted(deduped)
        )

    @staticmethod
    def _dedupe_ids(entity_ids: Iterable[str]) -> tuple[str, ...]:
        """Return entity IDs in first-seen order without duplicates."""
        deduped: dict[str, None] = {}
        for entity_id in entity_ids:
            deduped.setdefault(entity_id, None)

        return tuple(deduped)

    def _context_entity_ids(
        self,
        *,
        character_ids: tuple[str, ...],
        relationships: tuple[Relationship, ...],
    ) -> tuple[str, ...]:
        """Return non-character entities connected to the scene context."""
        character_id_set = set(character_ids)
        entity_ids: dict[str, None] = {}
        for relationship in relationships:
            for entity_id in (
                relationship.source_entity_id,
                relationship.target_entity_id,
            ):
                if entity_id in character_id_set:
                    continue
                entity = self._database.retrieve_entity(entity_id)
                if entity is not None:
                    entity_ids.setdefault(entity_id, None)

        return tuple(entity_ids)

    @staticmethod
    def _dedupe_facts(facts: Iterable[Fact]) -> tuple[Fact, ...]:
        """Return active facts without duplicate fact IDs."""
        deduped: dict[str, Fact] = {}
        for fact in facts:
            deduped.setdefault(fact.fact_id, fact)

        return tuple(deduped.values())

    def _location_ids_from_relationships(
        self,
        relationships: tuple[Relationship, ...],
    ) -> tuple[str, ...]:
        """Return connected location IDs discovered from scene relationships."""
        location_ids: dict[str, None] = {}
        for relationship in relationships:
            for entity_id in (
                relationship.source_entity_id,
                relationship.target_entity_id,
            ):
                entity = self._database.retrieve_entity(entity_id)
                if entity is not None and entity.entity_type == "location":
                    location_ids.setdefault(entity_id, None)

        return tuple(location_ids)

    def _relationship_is_scene_relevant(
        self,
        relationship: Relationship,
        chapter_index: int,
        character_ids: tuple[str, ...],
    ) -> bool:
        """Return whether a relationship belongs in a scene context view."""
        evidence_chapter_index = self._database.relationship_evidence_chapter_index(
            relationship
        )
        if evidence_chapter_index == chapter_index:
            return True

        if is_current_state_relationship_type(relationship.relationship_type):
            return True

        return (
            relationship.source_entity_id in character_ids
            and relationship.target_entity_id in character_ids
        )

    def _fact_is_scene_relevant(self, fact: Fact, chapter_index: int) -> bool:
        """Return whether a fact belongs in a scene context view."""
        if self._database.fact_evidence_chapter_index(fact) == chapter_index:
            return True

        return is_scene_context_fact_attribute(fact.attribute)

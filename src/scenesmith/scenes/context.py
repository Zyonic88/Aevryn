"""Phase 7 scene context builder over Canon Database."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from scenesmith.canon import CanonDatabase
from scenesmith.characters import CanonCharacterCard, CharacterCardBuilder
from scenesmith.core import Fact, Relationship, Scene, SceneSnapshot
from scenesmith.importing import ImportedSource

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CanonSceneContext:
    """Scene context reconstructed from accepted Canon state."""

    snapshot: SceneSnapshot
    scene: Scene
    character_cards: tuple[CanonCharacterCard, ...]
    active_facts: tuple[Fact, ...]
    relationships: tuple[Relationship, ...]


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
            self._character_cards.build_card(
                character_id=character_id,
                chapter_index=chapter_index,
            )
            for character_id in unique_character_ids
        )
        active_facts = tuple(
            fact
            for character_id in unique_character_ids
            for fact in self._database.retrieve_state_at_chapter(
                entity_id=character_id,
                chapter_index=chapter_index,
            )
        )
        relationships = self._dedupe_relationships(
            relationship
            for character_id in unique_character_ids
            for relationship in self._database.list_relationships_for_entity(character_id)
        )
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

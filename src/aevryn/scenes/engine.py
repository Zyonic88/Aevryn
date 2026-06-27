"""Scene Engine implementation."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from aevryn.canon import CanonEngine, StoryPosition
from aevryn.characters import CharacterEngine
from aevryn.scenes.models import SceneContext, SceneEnvironmentSnapshot
from aevryn.timeline import TimelineEngine

logger = logging.getLogger(__name__)


class SceneEngine:
    """Assemble scene context from Canon, Timeline, and Character state."""

    def __init__(
        self,
        canon_engine: CanonEngine,
        timeline_engine: TimelineEngine,
        character_engine: CharacterEngine,
    ) -> None:
        """Create a Scene Engine.

        Parameters:
            canon_engine: Canon Engine used for environment snapshots.
            timeline_engine: Timeline Engine used for scene data.
            character_engine: Character Engine used for character cards.
        """
        self._canon_engine = canon_engine
        self._timeline_engine = timeline_engine
        self._character_engine = character_engine

    def build_context(
        self,
        position: StoryPosition,
        character_ids: Sequence[str] = (),
        environment_entity_ids: Sequence[str] = (),
    ) -> SceneContext:
        """Build scene context for a story position.

        Parameters:
            position: Registered story position to inspect.
            character_ids: Character IDs known to be present in the scene.
            environment_entity_ids: Environment or world entity IDs relevant to
                the scene.

        Returns:
            Scene context assembled from existing engine state.

        Raises:
            InvalidTimelinePositionError: If the scene position is unknown.
            UnknownEntityError: If any entity ID is unknown to Canon.
            NotACharacterError: If a character ID points to a non-character.
        """
        scene = self._timeline_engine.get_scene(position)
        unique_character_ids = self._dedupe_ids(character_ids)
        unique_environment_entity_ids = self._dedupe_ids(environment_entity_ids)
        characters = tuple(
            self._character_engine.build_card(
                character_id=character_id,
                position=position,
            )
            for character_id in unique_character_ids
        )
        environment = tuple(
            self._build_environment_snapshot(
                entity_id=entity_id,
                position=position,
            )
            for entity_id in unique_environment_entity_ids
        )
        events = tuple(self._timeline_engine.list_events(position=position))
        active_state_changes = tuple(
            self._timeline_engine.get_active_state_changes(position=position)
        )
        logger.debug(
            "scene_context_built",
            extra={
                "chapter_index": position.chapter_index,
                "scene_index": position.scene_index,
                "character_count": len(characters),
                "environment_count": len(environment),
                "event_count": len(events),
                "state_change_count": len(active_state_changes),
            },
        )

        return SceneContext(
            position=position,
            scene=scene,
            characters=characters,
            environment=environment,
            events=events,
            active_state_changes=active_state_changes,
        )

    def _build_environment_snapshot(
        self,
        entity_id: str,
        position: StoryPosition,
    ) -> SceneEnvironmentSnapshot:
        """Build a canon snapshot for an environment entity."""
        snapshot = self._canon_engine.snapshot_entity(
            entity_id=entity_id,
            position=position,
        )
        return SceneEnvironmentSnapshot(
            entity_id=entity_id,
            facts=snapshot.facts,
        )

    @staticmethod
    def _dedupe_ids(entity_ids: Sequence[str]) -> tuple[str, ...]:
        """Return entity IDs in first-seen order without duplicates."""
        deduped: dict[str, None] = {}
        for entity_id in entity_ids:
            deduped.setdefault(entity_id, None)

        return tuple(deduped)

"""Character Engine implementation."""

from __future__ import annotations

import logging

from aevryn.canon import (
    CanonEngine,
    CanonFactVersion,
    EntityType,
    StoryPosition,
    UnknownEntityError,
)
from aevryn.characters.exceptions import NotACharacterError
from aevryn.characters.models import CharacterCard, CharacterFact
from aevryn.timeline import TimelineEngine

logger = logging.getLogger(__name__)


class CharacterEngine:
    """Build living character cards from Canon and Timeline.

    The Character Engine reads from Canon and Timeline. It does not mutate canon,
    manage timeline windows, extract facts, or generate prompts.
    """

    def __init__(self, canon_engine: CanonEngine, timeline_engine: TimelineEngine) -> None:
        """Create a Character Engine.

        Parameters:
            canon_engine: Canon Engine used as the source of truth.
            timeline_engine: Timeline Engine used for current story position.
        """
        self._canon_engine = canon_engine
        self._timeline_engine = timeline_engine

    def build_card(
        self,
        character_id: str,
        position: StoryPosition | None = None,
    ) -> CharacterCard:
        """Build a living character card.

        Parameters:
            character_id: Permanent canon ID of the character.
            position: Optional story position. If omitted, the Timeline Engine's
                current position is used. If no current position is set, current
                canon state is used.

        Returns:
            Character card for the requested position.

        Raises:
            UnknownEntityError: If the entity does not exist in canon.
            NotACharacterError: If the entity is not a character.
            InvalidTimelinePositionError: If an explicit position is not a
                registered timeline scene.
        """
        character = self._canon_engine.get_entity(character_id)
        if character is None:
            raise UnknownEntityError(f"Unknown entity: {character_id}")
        if character.entity_type is not EntityType.CHARACTER:
            raise NotACharacterError(f"Entity is not a character: {character_id}")

        card_position = self._resolve_position(position)
        snapshot = self._canon_engine.snapshot_entity(
            entity_id=character_id,
            position=card_position,
        )
        facts = {
            attribute: self._build_character_fact(version)
            for attribute, version in snapshot.facts.items()
        }

        card = CharacterCard(
            character_id=character.entity_id,
            display_name=character.display_name,
            position=card_position,
            facts=facts,
            relationships=snapshot.relationships,
        )
        logger.debug(
            "character_engine_card_built",
            extra={
                "character_id": character_id,
                "fact_count": len(facts),
                "relationship_count": len(snapshot.relationships),
            },
        )
        return card

    def _resolve_position(self, position: StoryPosition | None) -> StoryPosition | None:
        """Resolve explicit position or Timeline Engine current position."""
        if position is not None:
            self._timeline_engine.get_scene(position)
            return position

        return self._timeline_engine.get_current_position()

    @staticmethod
    def _build_character_fact(version: CanonFactVersion) -> CharacterFact:
        """Convert a canon fact version into a character-card fact."""
        if version.evidence.position is None:
            msg = "Canon fact evidence must include a story position."
            raise ValueError(msg)

        return CharacterFact(
            attribute=version.attribute,
            value=version.value,
            previous_value=version.previous_value,
            evidence=version.evidence,
            valid_from=version.evidence.position,
        )

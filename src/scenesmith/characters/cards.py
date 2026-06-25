"""Phase 6 character card builder over Canon Database."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from scenesmith.canon import CanonDatabase
from scenesmith.core import Evidence, Fact

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CanonCharacterFact:
    """Character fact displayed on a Phase 6 character card."""

    attribute: str
    value: str
    previous_value: str | None
    evidence: Evidence
    valid_from_chapter_id: str
    valid_from_scene_id: str


@dataclass(frozen=True, slots=True)
class CanonCharacterCard:
    """Character card assembled from accepted Canon Database truth."""

    character_id: str
    display_name: str
    chapter_index: int
    facts: tuple[CanonCharacterFact, ...]


class CharacterCardBuilder:
    """Build character cards from Canon Database state."""

    def __init__(self, database: CanonDatabase) -> None:
        """Create a Character Card Builder.

        Parameters:
            database: Canon Database used as the source of truth.
        """
        self._database = database

    def build_card(self, character_id: str, chapter_index: int) -> CanonCharacterCard:
        """Build a character card for a chapter.

        Parameters:
            character_id: Character entity ID.
            chapter_index: Chapter index used for state lookup.

        Returns:
            Character card for the requested chapter.

        Raises:
            ValueError: If the character is unknown or fact evidence is missing.
        """
        character = self._database.retrieve_character(character_id)
        if character is None:
            raise ValueError(f"Unknown character: {character_id}")

        active_facts = self._database.retrieve_state_at_chapter(
            entity_id=character_id,
            chapter_index=chapter_index,
        )
        card_facts = tuple(self._build_fact(fact) for fact in active_facts)
        display_name = self._display_name_from_facts(
            fallback=character.entity.display_name,
            facts=card_facts,
        )
        logger.debug(
            "character_card_built",
            extra={
                "character_id": character_id,
                "chapter_index": chapter_index,
                "fact_count": len(card_facts),
            },
        )

        return CanonCharacterCard(
            character_id=character_id,
            display_name=display_name,
            chapter_index=chapter_index,
            facts=card_facts,
        )

    def _build_fact(self, fact: Fact) -> CanonCharacterFact:
        """Build a display fact from a canon fact."""
        evidence = self._database.retrieve_evidence(fact.evidence_id)
        if evidence is None:
            raise ValueError(f"Missing evidence for fact: {fact.fact_id}")

        previous_value = self._previous_value(fact)
        return CanonCharacterFact(
            attribute=fact.attribute,
            value=fact.value,
            previous_value=previous_value,
            evidence=evidence,
            valid_from_chapter_id=evidence.chapter_id,
            valid_from_scene_id=evidence.scene_id,
        )

    def _previous_value(self, fact: Fact) -> str | None:
        """Return the previous value for a fact attribute."""
        history = self._database.retrieve_fact_history(
            entity_id=fact.entity_id,
            attribute=fact.attribute,
        )
        for index, historical_fact in enumerate(history):
            if historical_fact.fact_id == fact.fact_id:
                if index == 0:
                    return None

                return history[index - 1].value

        return None

    @staticmethod
    def _display_name_from_facts(
        fallback: str,
        facts: tuple[CanonCharacterFact, ...],
    ) -> str:
        """Return the active display name fact when one exists."""
        for fact in facts:
            if fact.attribute == "display_name":
                return fact.value

        return fallback

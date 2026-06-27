"""Phase 6 character card builder over Canon Database."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from aevryn.canon import CanonDatabase
from aevryn.canon.policies import is_additive_fact_attribute
from aevryn.core import Evidence, Fact

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

    def __post_init__(self) -> None:
        """Validate character fact display fields."""
        _require_machine_token(self.attribute, "Character fact attribute")
        object.__setattr__(
            self,
            "value",
            _normalized_text(self.value, "Character fact value"),
        )
        if self.previous_value is not None:
            object.__setattr__(
                self,
                "previous_value",
                _normalized_text(
                    self.previous_value,
                    "Character fact previous value",
                ),
            )
        _require_machine_token(
            self.valid_from_chapter_id,
            "Character fact valid-from chapter ID",
        )
        _require_machine_token(
            self.valid_from_scene_id,
            "Character fact valid-from scene ID",
        )


@dataclass(frozen=True, slots=True)
class CanonCharacterCard:
    """Character card assembled from accepted Canon Database truth."""

    character_id: str
    display_name: str
    chapter_index: int
    facts: tuple[CanonCharacterFact, ...]

    def __post_init__(self) -> None:
        """Validate character card identity and story position."""
        _require_machine_token(self.character_id, "Character card character ID")
        object.__setattr__(
            self,
            "display_name",
            _normalized_text(self.display_name, "Character card display name"),
        )
        if (
            isinstance(self.chapter_index, bool)
            or not isinstance(self.chapter_index, int)
            or self.chapter_index < 1
        ):
            raise ValueError("Character card chapter index must be at least 1.")


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
        if (
            isinstance(chapter_index, bool)
            or not isinstance(chapter_index, int)
            or chapter_index < 1
        ):
            raise ValueError("Chapter index must be at least 1.")

        character = self._database.retrieve_character(character_id)
        if character is None:
            raise ValueError(f"Unknown character: {character_id}")

        active_facts = self._database.retrieve_state_at_chapter(
            entity_id=character_id,
            chapter_index=chapter_index,
        )
        return self._build_card_from_facts(
            character_id=character_id,
            fallback_display_name=character.entity.display_name,
            chapter_index=chapter_index,
            active_facts=active_facts,
        )

    def build_card_at_scene(
        self,
        character_id: str,
        chapter_index: int,
        scene_index: int,
    ) -> CanonCharacterCard:
        """Build a character card for a scene position.

        Parameters:
            character_id: Character entity ID.
            chapter_index: Chapter index used for state lookup.
            scene_index: Scene index used for state lookup.

        Returns:
            Character card for the requested scene.

        Raises:
            ValueError: If the character is unknown or the position is invalid.
        """
        if (
            isinstance(chapter_index, bool)
            or not isinstance(chapter_index, int)
            or chapter_index < 1
        ):
            raise ValueError("Chapter index must be at least 1.")
        if (
            isinstance(scene_index, bool)
            or not isinstance(scene_index, int)
            or scene_index < 1
        ):
            raise ValueError("Scene index must be at least 1.")

        character = self._database.retrieve_character(character_id)
        if character is None:
            raise ValueError(f"Unknown character: {character_id}")

        active_facts = self._database.retrieve_state_at_scene(
            entity_id=character_id,
            chapter_index=chapter_index,
            scene_index=scene_index,
        )
        return self._build_card_from_facts(
            character_id=character_id,
            fallback_display_name=character.entity.display_name,
            chapter_index=chapter_index,
            active_facts=active_facts,
        )

    def _build_card_from_facts(
        self,
        character_id: str,
        fallback_display_name: str,
        chapter_index: int,
        active_facts: Sequence[Fact],
    ) -> CanonCharacterCard:
        """Build a character card from already-selected active facts."""
        card_facts = tuple(self._build_fact(fact) for fact in active_facts)
        display_name = self._display_name_from_facts(
            fallback=fallback_display_name,
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
        if is_additive_fact_attribute(fact.attribute):
            return None

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


def _require_text(value: str, field_name: str) -> None:
    """Validate a required human-readable text field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


def _normalized_text(value: str, field_name: str) -> str:
    """Return normalized human-readable text or raise if it is blank."""
    _require_text(value, field_name)
    return " ".join(value.split())


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a required whitespace-free machine token."""
    _require_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")

"""Core data models for the Character Engine."""

from __future__ import annotations

from dataclasses import dataclass

from aevryn.canon import CanonRelationship, Evidence, StoryPosition


@dataclass(frozen=True, slots=True)
class CharacterFact:
    """A character-focused fact for a card.

    Parameters:
        attribute: Character attribute name.
        value: Current or historical value.
        previous_value: Previous value, if canon has one.
        evidence: Evidence proving the value.
        valid_from: Story position where the value becomes active.
        valid_until: Story position where the value stops being active.
    """

    attribute: str
    value: str
    previous_value: str | None
    evidence: Evidence
    valid_from: StoryPosition
    valid_until: StoryPosition | None = None

    def __post_init__(self) -> None:
        """Validate character fact view-model fields."""
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


@dataclass(frozen=True, slots=True)
class CharacterCard:
    """Living character card assembled from Canon and Timeline.

    Parameters:
        character_id: Permanent canon ID of the character.
        display_name: Current canon display name.
        position: Story position represented by the card.
        facts: Character facts keyed by attribute.
        relationships: Canon relationships connected to the character.
    """

    character_id: str
    display_name: str
    position: StoryPosition | None
    facts: dict[str, CharacterFact]
    relationships: tuple[CanonRelationship, ...]

    def __post_init__(self) -> None:
        """Validate character card view-model identity and fact mapping."""
        _require_machine_token(self.character_id, "Character card character ID")
        object.__setattr__(
            self,
            "display_name",
            _normalized_text(self.display_name, "Character card display name"),
        )
        for attribute, fact in self.facts.items():
            _require_machine_token(attribute, "Character card fact key")
            if attribute != fact.attribute:
                raise ValueError("Character card fact keys must match fact attributes.")


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

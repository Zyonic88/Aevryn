"""Core data models for the Character Engine."""

from __future__ import annotations

from dataclasses import dataclass

from scenesmith.canon import CanonRelationship, Evidence, StoryPosition


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

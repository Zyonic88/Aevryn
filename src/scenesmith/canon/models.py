"""Core data models for the Canon Engine."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class EntityType(StrEnum):
    """Entity categories owned by the Canon Engine."""

    ARMOR = "armor"
    BUILDING = "building"
    CHARACTER = "character"
    CREATURE = "creature"
    ITEM = "item"
    LOCATION = "location"
    ORGANIZATION = "organization"
    SKILL = "skill"
    TIMELINE_EVENT = "timeline_event"
    VEHICLE = "vehicle"
    WEAPON = "weapon"


@dataclass(frozen=True, order=True, slots=True)
class StoryPosition:
    """Sortable chapter and scene position for canon evidence.

    Parameters:
        chapter_index: Numeric chapter position in story order.
        scene_index: Numeric scene position in chapter order.

    Raises:
        ValueError: If either index is lower than 1.
    """

    chapter_index: int
    scene_index: int

    def __post_init__(self) -> None:
        """Validate that story positions are one-based."""
        if (
            isinstance(self.chapter_index, bool)
            or not isinstance(self.chapter_index, int)
            or self.chapter_index < 1
        ):
            raise ValueError("Chapter index must be at least 1.")
        if (
            isinstance(self.scene_index, bool)
            or not isinstance(self.scene_index, int)
            or self.scene_index < 1
        ):
            raise ValueError("Scene index must be at least 1.")


@dataclass(frozen=True, slots=True)
class Evidence:
    """Evidence supporting a canon fact.

    Parameters:
        chapter: Chapter identifier or number where the evidence appears.
        scene: Scene identifier or number where the evidence appears.
        quote: Source text or concise citation proving the fact.
        confidence: Confidence score from 0.0 to 1.0.

    Raises:
        ValueError: If evidence fields are empty or confidence is out of range.
    """

    chapter: str
    scene: str
    quote: str
    confidence: float
    position: StoryPosition | None = None

    def __post_init__(self) -> None:
        """Validate evidence completeness and confidence range."""
        _require_text(self.chapter, "Evidence chapter")
        _require_text(self.scene, "Evidence scene")
        _require_text(self.quote, "Evidence quote")
        if (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, int | float)
            or not 0.0 <= self.confidence <= 1.0
        ):
            raise ValueError("Evidence confidence must be between 0.0 and 1.0.")
        if self.position is None:
            object.__setattr__(self, "position", self._infer_position())

    def _infer_position(self) -> StoryPosition:
        """Infer a sortable story position from chapter and scene labels."""
        return StoryPosition(
            chapter_index=self._first_number(self.chapter, "chapter"),
            scene_index=self._first_number(self.scene, "scene"),
        )

    @staticmethod
    def _first_number(value: str, field_name: str) -> int:
        """Return the first integer in a label."""
        match = re.search(r"\d+", value)
        if match is None:
            raise ValueError(f"Evidence {field_name} must contain a number.")

        return int(match.group())


@dataclass(frozen=True, slots=True)
class CanonEntity:
    """Permanent canon entity.

    Parameters:
        entity_id: Stable identifier that never changes after creation.
        entity_type: Canon-owned entity category.
        display_name: Human-readable name, which may change over time.

    Raises:
        ValueError: If the entity ID or display name is empty.
    """

    entity_id: str
    entity_type: EntityType
    display_name: str

    def __post_init__(self) -> None:
        """Validate required entity identity fields."""
        _require_machine_token(self.entity_id, "Entity ID")
        _require_text(self.display_name, "Entity display name")


@dataclass(frozen=True, slots=True)
class CanonFactVersion:
    """A single evidence-backed version of a canon fact.

    Parameters:
        entity_id: Entity that owns this fact.
        attribute: Fact name, such as current_weapon or status.
        value: Fact value recorded at this version.
        evidence: Evidence proving the fact.
        previous_value: Prior value, if one existed.
    """

    entity_id: str
    attribute: str
    value: str
    evidence: Evidence
    previous_value: str | None = None

    def __post_init__(self) -> None:
        """Validate required fact fields."""
        _require_machine_token(self.entity_id, "Fact entity ID")
        _require_machine_token(self.attribute, "Fact attribute")
        _require_text(self.value, "Fact value")
        if self.previous_value is not None:
            _require_text(self.previous_value, "Fact previous value")


@dataclass(frozen=True, slots=True)
class CanonRelationship:
    """Evidence-backed relationship between two canon entities.

    Parameters:
        source_entity_id: Entity where the relationship starts.
        relationship_type: Relationship label, such as owns or located_at.
        target_entity_id: Entity where the relationship ends.
        evidence: Evidence proving the relationship.
    """

    source_entity_id: str
    relationship_type: str
    target_entity_id: str
    evidence: Evidence

    def __post_init__(self) -> None:
        """Validate required relationship fields."""
        _require_machine_token(self.source_entity_id, "Relationship source entity ID")
        _require_machine_token(self.relationship_type, "Relationship type")
        _require_machine_token(self.target_entity_id, "Relationship target entity ID")


@dataclass(frozen=True, slots=True)
class CanonConflict:
    """A preserved contradiction between two fact versions.

    Parameters:
        entity_id: Entity that owns the conflicting fact.
        attribute: Fact name with contradictory values.
        existing_version: Earlier version at the same story position.
        conflicting_version: Later version at the same story position.
    """

    entity_id: str
    attribute: str
    existing_version: CanonFactVersion
    conflicting_version: CanonFactVersion

    def __post_init__(self) -> None:
        """Validate that a conflict describes one fact attribute."""
        _require_machine_token(self.entity_id, "Conflict entity ID")
        _require_machine_token(self.attribute, "Conflict attribute")
        if self.existing_version.entity_id != self.entity_id:
            raise ValueError("Existing conflict version must match conflict entity ID.")
        if self.conflicting_version.entity_id != self.entity_id:
            raise ValueError("Conflicting version must match conflict entity ID.")
        if self.existing_version.attribute != self.attribute:
            raise ValueError("Existing conflict version must match conflict attribute.")
        if self.conflicting_version.attribute != self.attribute:
            raise ValueError("Conflicting version must match conflict attribute.")
        if self.existing_version.value == self.conflicting_version.value:
            raise ValueError("Canon conflict versions must have different values.")


@dataclass(frozen=True, slots=True)
class CanonSnapshot:
    """Read-only canon state for one point in the story.

    Parameters:
        entity_id: Entity represented by the snapshot.
        facts: Current fact versions for the requested point.
        relationships: Relationships active by the requested point.
    """

    entity_id: str
    facts: dict[str, CanonFactVersion]
    relationships: tuple[CanonRelationship, ...]

    def __post_init__(self) -> None:
        """Validate snapshot identity, fact mapping, and relationships."""
        _require_machine_token(self.entity_id, "Canon snapshot entity ID")
        for attribute, fact in self.facts.items():
            _require_machine_token(attribute, "Canon snapshot fact key")
            if attribute != fact.attribute:
                raise ValueError("Canon snapshot fact keys must match fact attributes.")
            if fact.entity_id != self.entity_id:
                raise ValueError("Canon snapshot facts must match snapshot entity ID.")
        for relationship in self.relationships:
            if self.entity_id not in (
                relationship.source_entity_id,
                relationship.target_entity_id,
            ):
                raise ValueError(
                    "Canon snapshot relationships must connect to snapshot entity ID."
                )


def _require_text(value: str, field_name: str) -> None:
    """Validate a required human-readable text field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a required whitespace-free machine token."""
    _require_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")

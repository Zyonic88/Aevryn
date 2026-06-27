"""World Engine view models."""

from __future__ import annotations

from dataclasses import dataclass

from aevryn.core import Evidence, Relationship


@dataclass(frozen=True, slots=True)
class WorldEntityFact:
    """Evidence-backed fact for a world entity.

    Attributes:
        attribute: Canon attribute name.
        value: Current Canon value.
        evidence: Evidence supporting the value.
        valid_from_chapter_id: Chapter where the value became valid.
        valid_from_scene_id: Scene where the value became valid.
    """

    attribute: str
    value: str
    evidence: Evidence
    valid_from_chapter_id: str
    valid_from_scene_id: str

    def __post_init__(self) -> None:
        """Validate world fact view-model fields."""
        _require_machine_token(self.attribute, "World fact attribute")
        object.__setattr__(
            self,
            "value",
            _normalized_text(self.value, "World fact value"),
        )
        _require_machine_token(
            self.valid_from_chapter_id,
            "World fact valid-from chapter ID",
        )
        _require_machine_token(
            self.valid_from_scene_id,
            "World fact valid-from scene ID",
        )


@dataclass(frozen=True, slots=True)
class WorldEntityState:
    """Current state of a world entity at a story position.

    Attributes:
        entity_id: Permanent Canon entity ID.
        entity_type: Entity category, such as location, building, or organization.
        display_name: Human-readable entity name.
        chapter_index: Chapter index used for reconstruction.
        facts: Facts active for the entity at the requested chapter.
        relationships: Relationships connected to the entity.
    """

    entity_id: str
    entity_type: str
    display_name: str
    chapter_index: int
    facts: tuple[WorldEntityFact, ...] = ()
    relationships: tuple[Relationship, ...] = ()

    def __post_init__(self) -> None:
        """Validate world entity state identity and position."""
        _require_machine_token(self.entity_id, "World entity ID")
        _require_machine_token(self.entity_type, "World entity type")
        object.__setattr__(
            self,
            "display_name",
            _normalized_text(self.display_name, "World entity display name"),
        )
        _require_positive_index(self.chapter_index, "World entity chapter index")


@dataclass(frozen=True, slots=True)
class WorldState:
    """World state reconstructed from accepted Canon.

    Attributes:
        chapter_index: Chapter index used for reconstruction.
        entities: World entity states included in the view.
    """

    chapter_index: int
    entities: tuple[WorldEntityState, ...] = ()

    def __post_init__(self) -> None:
        """Validate world state position and entity uniqueness."""
        _require_positive_index(self.chapter_index, "World state chapter index")
        entity_ids = [entity.entity_id for entity in self.entities]
        if len(entity_ids) != len(set(entity_ids)):
            raise ValueError("World state cannot contain duplicate entities.")


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


def _require_positive_index(value: int, field_name: str) -> None:
    """Validate a one-based story index."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be at least 1.")

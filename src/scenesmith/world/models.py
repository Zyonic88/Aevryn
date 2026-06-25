"""World Engine view models."""

from __future__ import annotations

from dataclasses import dataclass

from scenesmith.core import Evidence, Relationship


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


@dataclass(frozen=True, slots=True)
class WorldState:
    """World state reconstructed from accepted Canon.

    Attributes:
        chapter_index: Chapter index used for reconstruction.
        entities: World entity states included in the view.
    """

    chapter_index: int
    entities: tuple[WorldEntityState, ...] = ()

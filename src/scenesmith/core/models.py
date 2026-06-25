"""Data-only core models for SceneSmith Phase 1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Story:
    """Top-level imported story.

    Attributes:
        story_id: Permanent story identifier.
        title: Human-readable story title.
        chapters: Ordered chapters in the story.
    """

    story_id: str
    title: str
    chapters: tuple[Chapter, ...] = ()


@dataclass(frozen=True, slots=True)
class Chapter:
    """Ordered section of a story.

    Attributes:
        chapter_id: Permanent chapter identifier.
        story_id: Parent story identifier.
        chapter_index: One-based chapter order.
        title: Human-readable chapter title.
        scenes: Ordered scenes in the chapter.
    """

    chapter_id: str
    story_id: str
    chapter_index: int
    title: str
    scenes: tuple[Scene, ...] = ()


@dataclass(frozen=True, slots=True)
class Scene:
    """Ordered unit inside a chapter.

    Attributes:
        scene_id: Permanent scene identifier.
        chapter_id: Parent chapter identifier.
        scene_index: One-based scene order within the chapter.
        title: Human-readable scene title.
        paragraphs: Source paragraphs in scene order.
    """

    scene_id: str
    chapter_id: str
    scene_index: int
    title: str
    paragraphs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Entity:
    """Permanent thing in the story.

    Attributes:
        entity_id: Permanent entity identifier.
        entity_type: Entity category, such as character, location, or item.
        display_name: Human-readable entity name.
    """

    entity_id: str
    entity_type: str
    display_name: str


@dataclass(frozen=True, slots=True)
class Character:
    """Character entity in the story.

    Attributes:
        entity: Permanent entity record for the character.
    """

    entity: Entity


@dataclass(frozen=True, slots=True)
class Location:
    """Location entity in the story.

    Attributes:
        entity: Permanent entity record for the location.
    """

    entity: Entity


@dataclass(frozen=True, slots=True)
class Item:
    """Item entity in the story.

    Attributes:
        entity: Permanent entity record for the item.
    """

    entity: Entity


@dataclass(frozen=True, slots=True)
class Evidence:
    """Source proof supporting a fact or relationship.

    Attributes:
        evidence_id: Permanent evidence identifier.
        source_id: Imported source identifier.
        chapter_id: Chapter identifier containing the evidence.
        scene_id: Scene identifier containing the evidence.
        paragraph_index: One-based paragraph index.
        sentence_index: One-based sentence index.
        quote: Source text excerpt.
        confidence: Confidence score from 0.0 to 1.0.
    """

    evidence_id: str
    source_id: str
    chapter_id: str
    scene_id: str
    paragraph_index: int
    sentence_index: int
    quote: str
    confidence: float


@dataclass(frozen=True, slots=True)
class Fact:
    """Evidence-backed claim about an entity.

    Attributes:
        fact_id: Permanent fact identifier.
        entity_id: Entity the fact describes.
        attribute: Fact attribute name.
        value: Fact value.
        evidence_id: Evidence proving the fact.
    """

    fact_id: str
    entity_id: str
    attribute: str
    value: str
    evidence_id: str


@dataclass(frozen=True, slots=True)
class Relationship:
    """Evidence-backed connection between two entities.

    Attributes:
        relationship_id: Permanent relationship identifier.
        source_entity_id: Entity where the relationship starts.
        relationship_type: Relationship label.
        target_entity_id: Entity where the relationship ends.
        evidence_id: Evidence proving the relationship.
    """

    relationship_id: str
    source_entity_id: str
    relationship_type: str
    target_entity_id: str
    evidence_id: str


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """Event that happens at a story position.

    Attributes:
        event_id: Permanent event identifier.
        chapter_id: Chapter where the event happens.
        scene_id: Scene where the event happens.
        description: Human-readable event description.
        evidence_id: Evidence proving the event.
    """

    event_id: str
    chapter_id: str
    scene_id: str
    description: str
    evidence_id: str


@dataclass(frozen=True, slots=True)
class StateChange:
    """Validity window for a fact value.

    Attributes:
        state_change_id: Permanent state-change identifier.
        fact_id: Fact whose validity is described.
        valid_from_event_id: Event where the fact becomes valid.
        valid_until_event_id: Event where the fact stops being valid.
    """

    state_change_id: str
    fact_id: str
    valid_from_event_id: str
    valid_until_event_id: str | None = None


@dataclass(frozen=True, slots=True)
class SceneSnapshot:
    """Reconstructed scene state.

    Attributes:
        snapshot_id: Permanent snapshot identifier.
        scene_id: Scene represented by the snapshot.
        character_ids: Characters present in the scene.
        location_ids: Locations relevant to the scene.
        fact_ids: Facts active in the scene.
        relationship_ids: Relationships active in the scene.
        event_ids: Timeline events active in the scene.
    """

    snapshot_id: str
    scene_id: str
    character_ids: tuple[str, ...] = ()
    location_ids: tuple[str, ...] = ()
    fact_ids: tuple[str, ...] = ()
    relationship_ids: tuple[str, ...] = ()
    event_ids: tuple[str, ...] = ()

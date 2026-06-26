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

    def __post_init__(self) -> None:
        """Validate required story identity."""
        _require_machine_token(self.story_id, "Story ID")
        _require_text(self.title, "Story title")
        chapter_ids: list[str] = []
        chapter_indexes: list[int] = []
        for chapter in self.chapters:
            if chapter.story_id != self.story_id:
                raise ValueError("Story chapters must reference the story ID.")
            chapter_ids.append(chapter.chapter_id)
            chapter_indexes.append(chapter.chapter_index)
        if len(chapter_ids) != len(set(chapter_ids)):
            raise ValueError("Story cannot contain duplicate chapters.")
        if len(chapter_indexes) != len(set(chapter_indexes)):
            raise ValueError("Story cannot contain duplicate chapter indexes.")
        if chapter_indexes != sorted(chapter_indexes):
            raise ValueError("Story chapters must appear in increasing order.")


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

    def __post_init__(self) -> None:
        """Validate required chapter identity and ordering."""
        _require_machine_token(self.chapter_id, "Chapter ID")
        _require_machine_token(self.story_id, "Chapter story ID")
        _require_positive_index(self.chapter_index, "Chapter index")
        _require_text(self.title, "Chapter title")
        scene_ids: list[str] = []
        scene_indexes: list[int] = []
        for scene in self.scenes:
            if scene.chapter_id != self.chapter_id:
                raise ValueError("Chapter scenes must reference the chapter ID.")
            scene_ids.append(scene.scene_id)
            scene_indexes.append(scene.scene_index)
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("Chapter cannot contain duplicate scenes.")
        if len(scene_indexes) != len(set(scene_indexes)):
            raise ValueError("Chapter cannot contain duplicate scene indexes.")
        if scene_indexes != sorted(scene_indexes):
            raise ValueError("Chapter scenes must appear in increasing order.")


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

    def __post_init__(self) -> None:
        """Validate required scene identity and ordering."""
        _require_machine_token(self.scene_id, "Scene ID")
        _require_machine_token(self.chapter_id, "Scene chapter ID")
        _require_positive_index(self.scene_index, "Scene index")
        _require_text(self.title, "Scene title")
        for paragraph in self.paragraphs:
            _require_text(paragraph, "Scene paragraph")


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

    def __post_init__(self) -> None:
        """Validate required entity identity."""
        _require_machine_token(self.entity_id, "Entity ID")
        _require_machine_token(self.entity_type, "Entity type")
        _require_text(self.display_name, "Entity display name")


@dataclass(frozen=True, slots=True)
class Character:
    """Character entity in the story.

    Attributes:
        entity: Permanent entity record for the character.
    """

    entity: Entity

    def __post_init__(self) -> None:
        """Validate that the wrapped entity is a character."""
        if self.entity.entity_type != "character":
            raise ValueError("Character models must wrap character entities.")


@dataclass(frozen=True, slots=True)
class Location:
    """Location entity in the story.

    Attributes:
        entity: Permanent entity record for the location.
    """

    entity: Entity

    def __post_init__(self) -> None:
        """Validate that the wrapped entity is a location."""
        if self.entity.entity_type != "location":
            raise ValueError("Location models must wrap location entities.")


@dataclass(frozen=True, slots=True)
class Item:
    """Item entity in the story.

    Attributes:
        entity: Permanent entity record for the item.
    """

    entity: Entity

    def __post_init__(self) -> None:
        """Validate that the wrapped entity is an item-like entity."""
        if self.entity.entity_type not in {"armor", "item", "weapon"}:
            raise ValueError("Item models must wrap item, weapon, or armor entities.")


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

    def __post_init__(self) -> None:
        """Validate required source evidence fields."""
        _require_machine_token(self.evidence_id, "Evidence ID")
        _require_machine_token(self.source_id, "Evidence source ID")
        _require_machine_token(self.chapter_id, "Evidence chapter ID")
        _require_machine_token(self.scene_id, "Evidence scene ID")
        _require_positive_index(self.paragraph_index, "Evidence paragraph index")
        _require_positive_index(self.sentence_index, "Evidence sentence index")
        _require_text(self.quote, "Evidence quote")
        if (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, int | float)
            or not 0.0 <= self.confidence <= 1.0
        ):
            raise ValueError("Evidence confidence must be between 0.0 and 1.0.")


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

    def __post_init__(self) -> None:
        """Validate required fact identity and evidence reference."""
        _require_machine_token(self.fact_id, "Fact ID")
        _require_machine_token(self.entity_id, "Fact entity ID")
        _require_machine_token(self.attribute, "Fact attribute")
        _require_text(self.value, "Fact value")
        _require_machine_token(self.evidence_id, "Fact evidence ID")


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

    def __post_init__(self) -> None:
        """Validate required relationship identity and evidence reference."""
        _require_machine_token(self.relationship_id, "Relationship ID")
        _require_machine_token(self.source_entity_id, "Relationship source entity ID")
        _require_machine_token(self.relationship_type, "Relationship type")
        _require_machine_token(self.target_entity_id, "Relationship target entity ID")
        _require_machine_token(self.evidence_id, "Relationship evidence ID")


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

    def __post_init__(self) -> None:
        """Validate required event identity and evidence reference."""
        _require_machine_token(self.event_id, "Timeline event ID")
        _require_machine_token(self.chapter_id, "Timeline event chapter ID")
        _require_machine_token(self.scene_id, "Timeline event scene ID")
        _require_text(self.description, "Timeline event description")
        _require_machine_token(self.evidence_id, "Timeline event evidence ID")


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

    def __post_init__(self) -> None:
        """Validate required state-change identity and event references."""
        _require_machine_token(self.state_change_id, "State change ID")
        _require_machine_token(self.fact_id, "State change fact ID")
        _require_machine_token(self.valid_from_event_id, "State change start event ID")
        if self.valid_until_event_id is not None:
            _require_machine_token(
                self.valid_until_event_id,
                "State change end event ID",
            )


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

    def __post_init__(self) -> None:
        """Validate required scene snapshot identity."""
        _require_machine_token(self.snapshot_id, "Scene snapshot ID")
        _require_machine_token(self.scene_id, "Scene snapshot scene ID")
        for character_id in self.character_ids:
            _require_machine_token(character_id, "Scene snapshot character ID")
        _require_unique_values(self.character_ids, "Scene snapshot character IDs")
        for location_id in self.location_ids:
            _require_machine_token(location_id, "Scene snapshot location ID")
        _require_unique_values(self.location_ids, "Scene snapshot location IDs")
        for fact_id in self.fact_ids:
            _require_machine_token(fact_id, "Scene snapshot fact ID")
        _require_unique_values(self.fact_ids, "Scene snapshot fact IDs")
        for relationship_id in self.relationship_ids:
            _require_machine_token(relationship_id, "Scene snapshot relationship ID")
        _require_unique_values(
            self.relationship_ids,
            "Scene snapshot relationship IDs",
        )
        for event_id in self.event_ids:
            _require_machine_token(event_id, "Scene snapshot event ID")
        _require_unique_values(self.event_ids, "Scene snapshot event IDs")


def _require_text(value: str, field_name: str) -> None:
    """Validate a required human-readable text field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a required whitespace-free machine token."""
    _require_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _require_positive_index(value: int, field_name: str) -> None:
    """Validate a one-based source index."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be at least 1.")


def _require_unique_values(values: tuple[str, ...], field_name: str) -> None:
    """Validate that snapshot reference IDs are not duplicated."""
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique.")

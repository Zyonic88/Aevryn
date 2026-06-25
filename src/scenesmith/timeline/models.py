"""Core data models for the Timeline Engine."""

from __future__ import annotations

from dataclasses import dataclass

from scenesmith.canon import StoryPosition


@dataclass(frozen=True, slots=True)
class TimelineChapter:
    """A chapter in story order.

    Parameters:
        chapter_index: One-based chapter order.
        title: Human-readable chapter title.

    Raises:
        ValueError: If chapter_index is lower than 1 or title is empty.
    """

    chapter_index: int
    title: str

    def __post_init__(self) -> None:
        """Validate chapter fields."""
        if self.chapter_index < 1:
            raise ValueError("Chapter index must be at least 1.")
        if not self.title.strip():
            raise ValueError("Chapter title is required.")


@dataclass(frozen=True, slots=True)
class TimelineScene:
    """A scene attached to a chapter.

    Parameters:
        position: Chapter and scene position.
        title: Human-readable scene title.

    Raises:
        ValueError: If title is empty.
    """

    position: StoryPosition
    title: str

    def __post_init__(self) -> None:
        """Validate scene fields."""
        if not self.title.strip():
            raise ValueError("Scene title is required.")


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """A timeline event at a specific story position.

    Parameters:
        event_id: Permanent event identifier.
        position: Story position where the event happens.
        description: Human-readable event description.

    Raises:
        ValueError: If event_id or description is empty.
    """

    event_id: str
    position: StoryPosition
    description: str

    def __post_init__(self) -> None:
        """Validate event fields."""
        if not self.event_id.strip():
            raise ValueError("Event ID is required.")
        if not self.description.strip():
            raise ValueError("Event description is required.")


@dataclass(frozen=True, slots=True)
class TimelineStateChange:
    """Validity window for a state change.

    Parameters:
        change_id: Permanent state-change identifier.
        subject_id: Canon entity or relationship affected by the change.
        attribute: State attribute affected by the change.
        value: Value that becomes valid.
        valid_from: Position where the value becomes valid.
        valid_until: Optional position where the value stops being valid.
        event_id: Optional timeline event that caused the change.

    Raises:
        ValueError: If required fields are empty or valid_until precedes valid_from.
    """

    change_id: str
    subject_id: str
    attribute: str
    value: str
    valid_from: StoryPosition
    valid_until: StoryPosition | None = None
    event_id: str | None = None

    def __post_init__(self) -> None:
        """Validate state-change fields and validity window."""
        if not self.change_id.strip():
            raise ValueError("State change ID is required.")
        if not self.subject_id.strip():
            raise ValueError("State change subject ID is required.")
        if not self.attribute.strip():
            raise ValueError("State change attribute is required.")
        if not self.value.strip():
            raise ValueError("State change value is required.")
        if self.valid_until is not None and self.valid_until < self.valid_from:
            raise ValueError("valid_until cannot be earlier than valid_from.")

"""In-memory Timeline Engine implementation."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from scenesmith.canon import StoryPosition
from scenesmith.timeline.exceptions import (
    DuplicateChapterError,
    DuplicateEventError,
    DuplicateSceneError,
    DuplicateStateChangeError,
    InvalidTimelinePositionError,
    OverlappingStateChangeError,
)
from scenesmith.timeline.models import (
    TimelineChapter,
    TimelineEvent,
    TimelineScene,
    TimelineStateChange,
)

logger = logging.getLogger(__name__)


class TimelineEngine:
    """Manage story positions, events, state changes, and current position."""

    def __init__(self) -> None:
        """Create an empty Timeline Engine."""
        self._chapters: dict[int, TimelineChapter] = {}
        self._scenes: dict[StoryPosition, TimelineScene] = {}
        self._events: dict[str, TimelineEvent] = {}
        self._state_changes: dict[str, TimelineStateChange] = {}
        self._current_position: StoryPosition | None = None

    def register_chapter(self, chapter: TimelineChapter) -> None:
        """Register a chapter in story order.

        Parameters:
            chapter: Chapter to register.

        Raises:
            DuplicateChapterError: If chapter_index is already registered.
        """
        if chapter.chapter_index in self._chapters:
            raise DuplicateChapterError(
                f"Chapter already exists: {chapter.chapter_index}"
            )

        self._chapters[chapter.chapter_index] = chapter

    def register_scene(self, scene: TimelineScene) -> None:
        """Register a scene under an existing chapter.

        Parameters:
            scene: Scene to register.

        Raises:
            DuplicateSceneError: If the scene position is already registered.
            InvalidTimelinePositionError: If the chapter is unknown.
        """
        if scene.position.chapter_index not in self._chapters:
            raise InvalidTimelinePositionError(
                f"Unknown chapter: {scene.position.chapter_index}"
            )
        if scene.position in self._scenes:
            raise DuplicateSceneError(f"Scene already exists: {scene.position}")

        self._scenes[scene.position] = scene

    def record_event(self, event: TimelineEvent) -> None:
        """Record an event at a known story position.

        Parameters:
            event: Event to record.

        Raises:
            DuplicateEventError: If event_id is already registered.
            InvalidTimelinePositionError: If the event position is unknown.
        """
        self._require_registered_scene(event.position)
        if event.event_id in self._events:
            raise DuplicateEventError(f"Event already exists: {event.event_id}")

        self._events[event.event_id] = event

    def record_state_change(self, state_change: TimelineStateChange) -> None:
        """Record a validity window for a state change.

        Parameters:
            state_change: State change to record.

        Raises:
            DuplicateStateChangeError: If change_id is already registered with
                different data.
            InvalidTimelinePositionError: If valid_from, valid_until, or event_id
                references unknown timeline data.
            OverlappingStateChangeError: If the new change overlaps an existing
                validity window for the same subject attribute.
        """
        existing_change = self._state_changes.get(state_change.change_id)
        if existing_change is not None:
            if existing_change != state_change:
                logger.warning(
                    "timeline_duplicate_state_change_id",
                    extra={"change_id": state_change.change_id},
                )
                raise DuplicateStateChangeError(
                    f"State change already exists: {state_change.change_id}"
                )
            return

        self._require_registered_scene(state_change.valid_from)
        if state_change.valid_until is not None:
            self._require_registered_scene(state_change.valid_until)
        if state_change.event_id is not None and state_change.event_id not in self._events:
            raise InvalidTimelinePositionError(
                f"Unknown event: {state_change.event_id}"
            )
        self._require_non_overlapping_state_change(state_change)

        self._state_changes[state_change.change_id] = state_change

    def set_current_position(self, position: StoryPosition) -> None:
        """Set the current story position.

        Parameters:
            position: Registered scene position that is currently active.

        Raises:
            InvalidTimelinePositionError: If the position is unknown.
        """
        self._require_registered_scene(position)
        self._current_position = position

    def get_current_position(self) -> StoryPosition | None:
        """Return the current story position.

        Returns:
            Current story position, or None if one has not been set.
        """
        return self._current_position

    def list_chapters(self) -> Sequence[TimelineChapter]:
        """Return chapters in story order."""
        return tuple(
            self._chapters[index]
            for index in sorted(self._chapters)
        )

    def list_scenes(self, chapter_index: int | None = None) -> Sequence[TimelineScene]:
        """Return scenes in story order.

        Parameters:
            chapter_index: Optional chapter filter.

        Returns:
            Immutable sequence of scenes.
        """
        scenes = sorted(self._scenes.values(), key=lambda scene: scene.position)
        if chapter_index is None:
            return tuple(scenes)

        return tuple(
            scene
            for scene in scenes
            if scene.position.chapter_index == chapter_index
        )

    def get_scene(self, position: StoryPosition) -> TimelineScene:
        """Return a registered scene by story position.

        Parameters:
            position: Scene position to retrieve.

        Returns:
            Registered timeline scene.

        Raises:
            InvalidTimelinePositionError: If the position is unknown.
        """
        self._require_registered_scene(position)
        return self._scenes[position]

    def list_events(self, position: StoryPosition | None = None) -> Sequence[TimelineEvent]:
        """Return events in story order.

        Parameters:
            position: Optional exact story position filter.

        Returns:
            Immutable sequence of events.
        """
        events = sorted(
            self._events.values(),
            key=lambda event: (event.position, event.event_id),
        )
        if position is None:
            return tuple(events)

        return tuple(event for event in events if event.position == position)

    def list_state_changes(
        self,
        subject_id: str | None = None,
    ) -> Sequence[TimelineStateChange]:
        """Return state changes in story order.

        Parameters:
            subject_id: Optional subject filter.

        Returns:
            Immutable sequence of state changes.
        """
        state_changes = sorted(
            self._state_changes.values(),
            key=self._state_change_sort_key,
        )
        if subject_id is None:
            return tuple(state_changes)

        return tuple(
            state_change
            for state_change in state_changes
            if state_change.subject_id == subject_id
        )

    def get_state_history(
        self,
        subject_id: str,
        attribute: str,
    ) -> Sequence[TimelineStateChange]:
        """Return validity history for one subject attribute.

        Parameters:
            subject_id: Canon subject whose history should be returned.
            attribute: Attribute whose state history should be returned.

        Returns:
            Immutable sequence of matching state changes in story order.
        """
        return tuple(
            state_change
            for state_change in self.list_state_changes(subject_id=subject_id)
            if state_change.attribute == attribute
        )

    def get_active_state_changes(
        self,
        position: StoryPosition,
        subject_id: str | None = None,
    ) -> Sequence[TimelineStateChange]:
        """Return state changes active at a story position.

        Parameters:
            position: Story position to inspect.
            subject_id: Optional subject filter.

        Returns:
            Immutable sequence of active state changes.

        Raises:
            InvalidTimelinePositionError: If the position is unknown.
        """
        self._require_registered_scene(position)
        active_changes = tuple(
            state_change
            for state_change in self.list_state_changes()
            if self._state_change_is_active(state_change, position)
        )
        if subject_id is None:
            return active_changes

        return tuple(
            state_change
            for state_change in active_changes
            if state_change.subject_id == subject_id
        )

    def _require_registered_scene(self, position: StoryPosition) -> None:
        """Ensure a story position maps to a registered scene."""
        if position not in self._scenes:
            raise InvalidTimelinePositionError(f"Unknown scene: {position}")

    def _require_non_overlapping_state_change(
        self,
        state_change: TimelineStateChange,
    ) -> None:
        """Ensure one subject attribute has one active value per position."""
        for existing_change in self.get_state_history(
            subject_id=state_change.subject_id,
            attribute=state_change.attribute,
        ):
            if self._state_changes_overlap(existing_change, state_change):
                logger.warning(
                    "timeline_overlapping_state_change",
                    extra={
                        "change_id": state_change.change_id,
                        "existing_change_id": existing_change.change_id,
                    },
                )
                raise OverlappingStateChangeError(
                    "State change overlaps existing validity window: "
                    f"{state_change.change_id}"
                )

    @staticmethod
    def _state_change_is_active(
        state_change: TimelineStateChange,
        position: StoryPosition,
    ) -> bool:
        """Return whether a state change is active at a position."""
        if position < state_change.valid_from:
            return False
        if state_change.valid_until is None:
            return True

        return position < state_change.valid_until

    @staticmethod
    def _state_changes_overlap(
        first: TimelineStateChange,
        second: TimelineStateChange,
    ) -> bool:
        """Return whether two state-change validity windows overlap."""
        return (
            TimelineEngine._starts_before_end(first.valid_from, second.valid_until)
            and TimelineEngine._starts_before_end(second.valid_from, first.valid_until)
        )

    @staticmethod
    def _starts_before_end(
        start: StoryPosition,
        end: StoryPosition | None,
    ) -> bool:
        """Return whether a start position is before an optional end position."""
        return end is None or start < end

    @staticmethod
    def _state_change_sort_key(
        state_change: TimelineStateChange,
    ) -> tuple[StoryPosition, str, str, str]:
        """Return a deterministic story-order key for state changes."""
        return (
            state_change.valid_from,
            state_change.subject_id,
            state_change.attribute,
            state_change.change_id,
        )

"""Tests for the Aevryn Timeline Engine."""

from typing import Any, cast

import pytest

from aevryn import StoryPosition
from aevryn.timeline import (
    DuplicateChapterError,
    DuplicateEventError,
    DuplicateSceneError,
    DuplicateStateChangeError,
    InvalidTimelinePositionError,
    OverlappingStateChangeError,
    TimelineChapter,
    TimelineEngine,
    TimelineEvent,
    TimelineScene,
    TimelineStateChange,
)


def position(chapter_index: int, scene_index: int) -> StoryPosition:
    """Create a story position for tests."""
    return StoryPosition(chapter_index=chapter_index, scene_index=scene_index)


def register_basic_timeline(engine: TimelineEngine) -> None:
    """Register a small timeline used by tests."""
    engine.register_chapter(TimelineChapter(chapter_index=1, title="Opening"))
    engine.register_chapter(TimelineChapter(chapter_index=8, title="Market"))
    engine.register_chapter(TimelineChapter(chapter_index=14, title="Crossing"))
    engine.register_chapter(TimelineChapter(chapter_index=20, title="Defeat"))
    engine.register_scene(TimelineScene(position=position(1, 1), title="Road"))
    engine.register_scene(TimelineScene(position=position(8, 2), title="Blacksmith"))
    engine.register_scene(TimelineScene(position=position(14, 1), title="Bridge"))
    engine.register_scene(TimelineScene(position=position(20, 3), title="Ambush"))


def test_register_chapters_in_story_order() -> None:
    """Chapters are listed by chapter index, not registration order."""
    engine = TimelineEngine()
    engine.register_chapter(TimelineChapter(chapter_index=8, title="Market"))
    engine.register_chapter(TimelineChapter(chapter_index=1, title="Opening"))

    assert engine.list_chapters() == (
        TimelineChapter(chapter_index=1, title="Opening"),
        TimelineChapter(chapter_index=8, title="Market"),
    )


def test_register_chapter_rejects_duplicate_index() -> None:
    """A chapter index can only be registered once."""
    engine = TimelineEngine()
    chapter = TimelineChapter(chapter_index=1, title="Opening")
    engine.register_chapter(chapter)

    with pytest.raises(DuplicateChapterError):
        engine.register_chapter(chapter)


def test_register_scene_requires_known_chapter() -> None:
    """Scenes cannot be attached to unknown chapters."""
    engine = TimelineEngine()

    with pytest.raises(InvalidTimelinePositionError):
        engine.register_scene(TimelineScene(position=position(1, 1), title="Road"))


def test_register_scene_rejects_duplicate_position() -> None:
    """A scene position can only be registered once."""
    engine = TimelineEngine()
    engine.register_chapter(TimelineChapter(chapter_index=1, title="Opening"))
    scene = TimelineScene(position=position(1, 1), title="Road")
    engine.register_scene(scene)

    with pytest.raises(DuplicateSceneError):
        engine.register_scene(scene)


def test_list_scenes_can_filter_by_chapter() -> None:
    """Scenes can be listed globally or by chapter."""
    engine = TimelineEngine()
    engine.register_chapter(TimelineChapter(chapter_index=1, title="Opening"))
    first_scene = TimelineScene(position=position(1, 1), title="Road")
    second_scene = TimelineScene(position=position(1, 2), title="Gate")
    engine.register_scene(second_scene)
    engine.register_scene(first_scene)

    assert engine.list_scenes() == (first_scene, second_scene)
    assert engine.list_scenes(chapter_index=1) == (first_scene, second_scene)


def test_list_scenes_rejects_invalid_chapter_filter() -> None:
    """Timeline scene filters use one-based chapter indexes."""
    engine = TimelineEngine()

    with pytest.raises(InvalidTimelinePositionError, match="Chapter index"):
        engine.list_scenes(chapter_index=0)

    with pytest.raises(InvalidTimelinePositionError, match="Chapter index"):
        engine.list_scenes(chapter_index=True)

    with pytest.raises(InvalidTimelinePositionError, match="Chapter index"):
        engine.list_scenes(chapter_index=cast(Any, "1"))


def test_timeline_chapter_rejects_boolean_index() -> None:
    """Timeline chapter indexes must be real one-based integers."""
    with pytest.raises(ValueError, match="Chapter index"):
        TimelineChapter(chapter_index=True, title="Opening")

    with pytest.raises(ValueError, match="Chapter index"):
        TimelineChapter(chapter_index=cast(Any, "1"), title="Opening")


def test_record_event_requires_registered_scene() -> None:
    """Events must happen at registered story positions."""
    engine = TimelineEngine()

    with pytest.raises(InvalidTimelinePositionError):
        engine.record_event(
            TimelineEvent(
                event_id="event_mark_finds_dagger",
                position=position(1, 1),
                description="Mark finds a rusty dagger.",
            )
        )


def test_record_event_rejects_duplicate_id() -> None:
    """Event IDs are permanent and unique."""
    engine = TimelineEngine()
    engine.register_chapter(TimelineChapter(chapter_index=1, title="Opening"))
    engine.register_scene(TimelineScene(position=position(1, 1), title="Road"))
    event = TimelineEvent(
        event_id="event_mark_finds_dagger",
        position=position(1, 1),
        description="Mark finds a rusty dagger.",
    )
    engine.record_event(event)

    with pytest.raises(DuplicateEventError):
        engine.record_event(event)


def test_list_events_returns_story_order_and_position_filter() -> None:
    """Events are returned in story order and can be filtered by position."""
    engine = TimelineEngine()
    register_basic_timeline(engine)
    first_event = TimelineEvent(
        event_id="event_mark_finds_dagger",
        position=position(1, 1),
        description="Mark finds a rusty dagger.",
    )
    second_event = TimelineEvent(
        event_id="event_mark_buys_sword",
        position=position(8, 2),
        description="Mark buys an iron sword.",
    )
    engine.record_event(second_event)
    engine.record_event(first_event)

    assert engine.list_events() == (first_event, second_event)
    assert engine.list_events(position=position(8, 2)) == (second_event,)


def test_list_events_rejects_unknown_position_filter() -> None:
    """Event position filters must point to registered scenes."""
    engine = TimelineEngine()
    register_basic_timeline(engine)

    with pytest.raises(InvalidTimelinePositionError, match="Unknown scene"):
        engine.list_events(position=position(99, 1))


def test_list_events_uses_event_id_for_same_position_order() -> None:
    """Events at the same position have deterministic event-ID ordering."""
    engine = TimelineEngine()
    register_basic_timeline(engine)
    second_event = TimelineEvent(
        event_id="event_002",
        position=position(8, 2),
        description="Second event.",
    )
    first_event = TimelineEvent(
        event_id="event_001",
        position=position(8, 2),
        description="First event.",
    )
    engine.record_event(second_event)
    engine.record_event(first_event)

    assert engine.list_events(position=position(8, 2)) == (first_event, second_event)


def test_record_state_change_requires_registered_positions() -> None:
    """State changes require known validity positions."""
    engine = TimelineEngine()

    with pytest.raises(InvalidTimelinePositionError):
        engine.record_state_change(
            TimelineStateChange(
                change_id="change_mark_weapon_dagger",
                subject_id="character_mark",
                attribute="current_weapon",
                value="Rusty Dagger",
                valid_from=position(1, 1),
            )
        )


def test_record_state_change_event_must_match_valid_from_position() -> None:
    """A state change event must occur where the state becomes valid."""
    engine = TimelineEngine()
    register_basic_timeline(engine)
    engine.record_event(
        TimelineEvent(
            event_id="event_mark_finds_dagger",
            position=position(1, 1),
            description="Mark finds a rusty dagger.",
        )
    )

    with pytest.raises(InvalidTimelinePositionError, match="valid_from position"):
        engine.record_state_change(
            TimelineStateChange(
                change_id="change_mark_weapon_dagger",
                subject_id="character_mark",
                attribute="current_weapon",
                value="Rusty Dagger",
                valid_from=position(8, 2),
                event_id="event_mark_finds_dagger",
            )
        )


def test_state_change_rejects_invalid_validity_window() -> None:
    """valid_until cannot come before valid_from."""
    with pytest.raises(ValueError):
        TimelineStateChange(
            change_id="change_mark_weapon_invalid",
            subject_id="character_mark",
            attribute="current_weapon",
            value="Iron Sword",
            valid_from=position(8, 2),
            valid_until=position(1, 1),
        )


def test_timeline_models_reject_machine_token_whitespace() -> None:
    """Timeline IDs and state attributes are whitespace-free tokens."""
    with pytest.raises(ValueError, match="Event ID cannot contain whitespace"):
        TimelineEvent(
            event_id="event mark finds dagger",
            position=position(1, 1),
            description="Mark finds a rusty dagger.",
        )

    with pytest.raises(ValueError, match="State change attribute"):
        TimelineStateChange(
            change_id="change_mark_weapon",
            subject_id="character_mark",
            attribute="current weapon",
            value="Rusty Dagger",
            valid_from=position(1, 1),
        )


def test_active_state_changes_respect_valid_from_and_valid_until() -> None:
    """Timeline can answer which state changes are valid at a story position."""
    engine = TimelineEngine()
    register_basic_timeline(engine)
    dagger = TimelineStateChange(
        change_id="change_mark_weapon_dagger",
        subject_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        valid_from=position(1, 1),
        valid_until=position(8, 2),
    )
    sword = TimelineStateChange(
        change_id="change_mark_weapon_sword",
        subject_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        valid_from=position(8, 2),
        valid_until=position(20, 3),
    )
    engine.record_state_change(dagger)
    engine.record_state_change(sword)

    assert engine.get_active_state_changes(position(1, 1)) == (dagger,)
    assert engine.get_active_state_changes(position(14, 1)) == (sword,)
    assert engine.get_active_state_changes(position(20, 3)) == ()


def test_record_state_change_is_idempotent_for_identical_data() -> None:
    """Repeating the same state change does not duplicate timeline history."""
    engine = TimelineEngine()
    register_basic_timeline(engine)
    state_change = TimelineStateChange(
        change_id="change_mark_weapon_sword",
        subject_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        valid_from=position(8, 2),
    )

    engine.record_state_change(state_change)
    engine.record_state_change(state_change)

    assert engine.list_state_changes() == (state_change,)


def test_record_state_change_rejects_conflicting_duplicate_id() -> None:
    """State-change IDs cannot be silently reused for different data."""
    engine = TimelineEngine()
    register_basic_timeline(engine)
    engine.record_state_change(
        TimelineStateChange(
            change_id="change_mark_weapon",
            subject_id="character_mark",
            attribute="current_weapon",
            value="Rusty Dagger",
            valid_from=position(1, 1),
            valid_until=position(8, 2),
        )
    )

    with pytest.raises(DuplicateStateChangeError):
        engine.record_state_change(
            TimelineStateChange(
                change_id="change_mark_weapon",
                subject_id="character_mark",
                attribute="current_weapon",
                value="Iron Sword",
                valid_from=position(8, 2),
            )
        )


def test_record_state_change_rejects_overlapping_subject_attribute() -> None:
    """One subject attribute cannot have overlapping validity windows."""
    engine = TimelineEngine()
    register_basic_timeline(engine)
    engine.record_state_change(
        TimelineStateChange(
            change_id="change_mark_weapon_dagger",
            subject_id="character_mark",
            attribute="current_weapon",
            value="Rusty Dagger",
            valid_from=position(1, 1),
            valid_until=position(14, 1),
        )
    )

    with pytest.raises(OverlappingStateChangeError):
        engine.record_state_change(
            TimelineStateChange(
                change_id="change_mark_weapon_sword",
                subject_id="character_mark",
                attribute="current_weapon",
                value="Iron Sword",
                valid_from=position(8, 2),
            )
        )


def test_adjacent_state_change_windows_are_allowed() -> None:
    """A new state can begin exactly when the previous state ends."""
    engine = TimelineEngine()
    register_basic_timeline(engine)
    dagger = TimelineStateChange(
        change_id="change_mark_weapon_dagger",
        subject_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        valid_from=position(1, 1),
        valid_until=position(8, 2),
    )
    sword = TimelineStateChange(
        change_id="change_mark_weapon_sword",
        subject_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        valid_from=position(8, 2),
    )

    engine.record_state_change(sword)
    engine.record_state_change(dagger)

    assert engine.get_state_history("character_mark", "current_weapon") == (
        dagger,
        sword,
    )


def test_active_state_changes_can_filter_by_subject() -> None:
    """Active state changes can be filtered by affected subject."""
    engine = TimelineEngine()
    register_basic_timeline(engine)
    mark_change = TimelineStateChange(
        change_id="change_mark_weapon_sword",
        subject_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        valid_from=position(8, 2),
    )
    luna_change = TimelineStateChange(
        change_id="change_luna_location_forest",
        subject_id="character_luna",
        attribute="current_location",
        value="Northern Forest",
        valid_from=position(8, 2),
    )
    engine.record_state_change(mark_change)
    engine.record_state_change(luna_change)

    assert engine.get_active_state_changes(
        position=position(14, 1),
        subject_id="character_mark",
    ) == (mark_change,)


def test_state_change_filters_reject_invalid_machine_tokens() -> None:
    """Timeline state lookup filters use machine-safe IDs and attributes."""
    engine = TimelineEngine()
    register_basic_timeline(engine)

    with pytest.raises(InvalidTimelinePositionError, match="cannot contain whitespace"):
        engine.list_state_changes(subject_id="character mark")

    with pytest.raises(InvalidTimelinePositionError, match="attribute"):
        engine.get_state_history("character_mark", "current weapon")


def test_set_current_position_requires_registered_scene() -> None:
    """Current story position must point to a registered scene."""
    engine = TimelineEngine()

    with pytest.raises(InvalidTimelinePositionError):
        engine.set_current_position(position(14, 1))


def test_set_and_get_current_position() -> None:
    """Timeline Engine owns current story position."""
    engine = TimelineEngine()
    register_basic_timeline(engine)

    engine.set_current_position(position(14, 1))

    assert engine.get_current_position() == position(14, 1)

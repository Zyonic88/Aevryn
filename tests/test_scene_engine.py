"""Tests for the Aevryn Scene Engine."""

import pytest

from aevryn import (
    CanonEngine,
    CanonEntity,
    CanonFactVersion,
    CharacterCard,
    CharacterEngine,
    CharacterFact,
    EntityType,
    Evidence,
    InvalidTimelinePositionError,
    SceneContext,
    SceneEngine,
    SceneEnvironmentSnapshot,
    StoryPosition,
    TimelineChapter,
    TimelineEngine,
    TimelineEvent,
    TimelineScene,
    TimelineStateChange,
    UnknownEntityError,
)


def position(chapter_index: int, scene_index: int) -> StoryPosition:
    """Create a story position for tests."""
    return StoryPosition(chapter_index=chapter_index, scene_index=scene_index)


def evidence(
    *,
    chapter: str = "Chapter 14",
    scene: str = "Scene 1",
    quote: str = "The bridge was slick with rain.",
) -> Evidence:
    """Create evidence for scene tests."""
    return Evidence(
        chapter=chapter,
        scene=scene,
        quote=quote,
        confidence=1.0,
    )


def fact_version(
    *,
    entity_id: str = "location_rain_bridge",
    attribute: str = "weather",
    value: str = "Rain",
) -> CanonFactVersion:
    """Create a canon fact version for scene model tests."""
    return CanonFactVersion(
        entity_id=entity_id,
        attribute=attribute,
        value=value,
        evidence=evidence(),
    )


def build_engines() -> tuple[CanonEngine, TimelineEngine, CharacterEngine, SceneEngine]:
    """Create connected engines with a small story state."""
    canon_engine = CanonEngine()
    timeline_engine = TimelineEngine()
    character_engine = CharacterEngine(canon_engine, timeline_engine)
    scene_engine = SceneEngine(
        canon_engine=canon_engine,
        timeline_engine=timeline_engine,
        character_engine=character_engine,
    )
    return canon_engine, timeline_engine, character_engine, scene_engine


def register_scene_state(canon_engine: CanonEngine, timeline_engine: TimelineEngine) -> None:
    """Register canon and timeline state used by scene tests."""
    timeline_engine.register_chapter(TimelineChapter(chapter_index=8, title="Market"))
    timeline_engine.register_chapter(TimelineChapter(chapter_index=14, title="Bridge"))
    timeline_engine.register_scene(
        TimelineScene(position=position(8, 2), title="Blacksmith")
    )
    timeline_engine.register_scene(
        TimelineScene(position=position(14, 1), title="Rain Bridge")
    )
    timeline_engine.record_event(
        TimelineEvent(
            event_id="event_bridge_crossing",
            position=position(14, 1),
            description="Mark crosses the rain bridge.",
        )
    )
    timeline_engine.record_state_change(
        TimelineStateChange(
            change_id="change_mark_weapon_sword",
            subject_id="character_mark",
            attribute="current_weapon",
            value="Iron Sword",
            valid_from=position(8, 2),
        )
    )
    canon_engine.register_entity(
        CanonEntity(
            entity_id="character_mark",
            entity_type=EntityType.CHARACTER,
            display_name="Mark",
        )
    )
    canon_engine.register_entity(
        CanonEntity(
            entity_id="location_rain_bridge",
            entity_type=EntityType.LOCATION,
            display_name="Rain Bridge",
        )
    )
    canon_engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence=evidence(
            chapter="Chapter 8",
            scene="Scene 2",
            quote="Mark bought an iron sword.",
        ),
    )
    canon_engine.record_fact(
        entity_id="location_rain_bridge",
        attribute="weather",
        value="Rain",
        evidence=evidence(),
    )


def test_build_context_assembles_scene_data() -> None:
    """Scene context contains scene, events, characters, environment, and changes."""
    canon_engine, timeline_engine, _character_engine, scene_engine = build_engines()
    register_scene_state(canon_engine, timeline_engine)

    context = scene_engine.build_context(
        position=position(14, 1),
        character_ids=("character_mark",),
        environment_entity_ids=("location_rain_bridge",),
    )

    assert context.position == position(14, 1)
    assert context.scene.title == "Rain Bridge"
    assert context.events[0].event_id == "event_bridge_crossing"
    assert context.characters[0].facts["current_weapon"].value == "Iron Sword"
    assert context.environment[0].facts["weather"].value == "Rain"
    assert context.active_state_changes[0].change_id == "change_mark_weapon_sword"


def test_build_context_dedupes_selected_entities() -> None:
    """Scene Engine does not duplicate repeated character or environment IDs."""
    canon_engine, timeline_engine, _character_engine, scene_engine = build_engines()
    register_scene_state(canon_engine, timeline_engine)

    context = scene_engine.build_context(
        position=position(14, 1),
        character_ids=("character_mark", "character_mark"),
        environment_entity_ids=("location_rain_bridge", "location_rain_bridge"),
    )

    assert len(context.characters) == 1
    assert len(context.environment) == 1


def test_build_context_rejects_unknown_scene_position() -> None:
    """Scene context cannot be built for unregistered scene positions."""
    _canon_engine, _timeline_engine, _character_engine, scene_engine = build_engines()

    with pytest.raises(InvalidTimelinePositionError):
        scene_engine.build_context(position(99, 1))


def test_build_context_rejects_unknown_character() -> None:
    """Scene context preserves Character Engine unknown-entity failures."""
    canon_engine, timeline_engine, _character_engine, scene_engine = build_engines()
    register_scene_state(canon_engine, timeline_engine)

    with pytest.raises(UnknownEntityError):
        scene_engine.build_context(
            position=position(14, 1),
            character_ids=("character_luna",),
        )


def test_build_context_rejects_unknown_environment_entity() -> None:
    """Scene context preserves Canon unknown-entity failures for environment."""
    canon_engine, timeline_engine, _character_engine, scene_engine = build_engines()
    register_scene_state(canon_engine, timeline_engine)

    with pytest.raises(UnknownEntityError):
        scene_engine.build_context(
            position=position(14, 1),
            environment_entity_ids=("location_unknown",),
        )


def test_scene_environment_snapshot_rejects_mismatched_fact_keys() -> None:
    """Environment snapshot fact keys must match fact attributes."""
    with pytest.raises(ValueError, match="fact keys must match"):
        SceneEnvironmentSnapshot(
            entity_id="location_rain_bridge",
            facts={"climate": fact_version(attribute="weather")},
        )


def test_scene_context_rejects_mismatched_scene_position() -> None:
    """Scene context position must match Timeline scene metadata."""
    with pytest.raises(ValueError, match="position must match"):
        SceneContext(
            position=position(14, 1),
            scene=TimelineScene(position=position(8, 2), title="Blacksmith"),
            characters=(),
            environment=(),
            events=(),
            active_state_changes=(),
        )


def test_scene_context_rejects_duplicate_characters() -> None:
    """Scene context cannot contain duplicate character cards."""
    character_fact = CharacterFact(
        attribute="current_weapon",
        value="Iron Sword",
        previous_value=None,
        evidence=evidence(chapter="Chapter 8", scene="Scene 2"),
        valid_from=position(8, 2),
    )
    character = CharacterCard(
        character_id="character_mark",
        display_name="Mark",
        position=position(14, 1),
        facts={"current_weapon": character_fact},
        relationships=(),
    )

    with pytest.raises(ValueError, match="duplicate characters"):
        SceneContext(
            position=position(14, 1),
            scene=TimelineScene(position=position(14, 1), title="Rain Bridge"),
            characters=(character, character),
            environment=(),
            events=(),
            active_state_changes=(),
        )


def test_scene_context_rejects_future_active_state_changes() -> None:
    """Active state changes cannot begin after the scene position."""
    with pytest.raises(ValueError, match="future"):
        SceneContext(
            position=position(14, 1),
            scene=TimelineScene(position=position(14, 1), title="Rain Bridge"),
            characters=(),
            environment=(),
            events=(),
            active_state_changes=(
                TimelineStateChange(
                    change_id="change_future_weapon",
                    subject_id="character_mark",
                    attribute="current_weapon",
                    value="Steel Sword",
                    valid_from=position(20, 1),
                ),
            ),
        )

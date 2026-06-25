"""Tests for the SceneSmith Prompt Engine."""

from scenesmith import (
    CanonEngine,
    CanonEntity,
    CharacterEngine,
    EntityType,
    Evidence,
    PromptEngine,
    SceneContext,
    SceneEngine,
    StoryPosition,
    TimelineChapter,
    TimelineEngine,
    TimelineEvent,
    TimelineScene,
    TimelineStateChange,
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
    """Create evidence for prompt tests."""
    return Evidence(
        chapter=chapter,
        scene=scene,
        quote=quote,
        confidence=1.0,
    )


def build_scene_context() -> SceneContext:
    """Build a scene context for prompt tests."""
    canon_engine = CanonEngine()
    timeline_engine = TimelineEngine()
    character_engine = CharacterEngine(canon_engine, timeline_engine)
    scene_engine = SceneEngine(canon_engine, timeline_engine, character_engine)
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
        evidence=evidence(chapter="Chapter 8", scene="Scene 2"),
    )
    canon_engine.record_fact(
        entity_id="location_rain_bridge",
        attribute="weather",
        value="Rain",
        evidence=evidence(),
    )
    return scene_engine.build_context(
        position=position(14, 1),
        character_ids=("character_mark",),
        environment_entity_ids=("location_rain_bridge",),
    )


def test_build_image_prompt_uses_scene_context() -> None:
    """Image prompt includes known scene, character, environment, and event state."""
    context = build_scene_context()
    prompt_engine = PromptEngine()

    prompt = prompt_engine.build_image_prompt(context)

    assert "Scene: Rain Bridge (Chapter 14, Scene 1)" in prompt
    assert "Character: Mark" in prompt
    assert "- current_weapon: Iron Sword" in prompt
    assert "Environment: location_rain_bridge" in prompt
    assert "- weather: Rain" in prompt
    assert "Event: Mark crosses the rain bridge." in prompt
    assert "Active State: character_mark current_weapon = Iron Sword" in prompt


def test_build_narration_prompt_uses_known_details_only() -> None:
    """Narration prompt tells consumers to use known canon details."""
    context = build_scene_context()
    prompt_engine = PromptEngine()

    prompt = prompt_engine.build_narration_prompt(context)

    assert "Narrate the scene using only the known canon details below." in prompt
    assert "Character: Mark" in prompt
    assert "Event: Mark crosses the rain bridge." in prompt


def test_build_camera_prompt_includes_camera_instruction() -> None:
    """Camera prompt adds framing guidance without inventing story details."""
    context = build_scene_context()
    prompt_engine = PromptEngine()

    prompt = prompt_engine.build_camera_prompt(context)

    assert "Describe camera framing and movement" in prompt
    assert "Environment: location_rain_bridge" in prompt


def test_build_animation_prompt_includes_motion_instruction() -> None:
    """Animation prompt uses events and active state."""
    context = build_scene_context()
    prompt_engine = PromptEngine()

    prompt = prompt_engine.build_animation_prompt(context)

    assert "Describe motion using only known scene events and active state." in prompt
    assert "Event: Mark crosses the rain bridge." in prompt
    assert "Active State: character_mark current_weapon = Iron Sword" in prompt


def test_build_bundle_returns_all_prompt_types() -> None:
    """Prompt bundle contains all V1 prompt types."""
    context = build_scene_context()
    prompt_engine = PromptEngine()

    bundle = prompt_engine.build_bundle(context)

    assert bundle.image_prompt
    assert bundle.narration_prompt
    assert bundle.camera_prompt
    assert bundle.animation_prompt

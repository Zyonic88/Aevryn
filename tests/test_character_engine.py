"""Tests for the SceneSmith Character Engine."""

import pytest

from scenesmith import (
    CanonEngine,
    CanonEntity,
    CharacterEngine,
    EntityType,
    Evidence,
    InvalidTimelinePositionError,
    NotACharacterError,
    StoryPosition,
    TimelineChapter,
    TimelineEngine,
    TimelineScene,
    UnknownEntityError,
)


def position(chapter_index: int, scene_index: int) -> StoryPosition:
    """Create a story position for tests."""
    return StoryPosition(chapter_index=chapter_index, scene_index=scene_index)


def evidence(
    *,
    chapter: str = "Chapter 1",
    scene: str = "Scene 1",
    quote: str = "Mark carried a rusty dagger.",
) -> Evidence:
    """Create evidence for tests."""
    return Evidence(
        chapter=chapter,
        scene=scene,
        quote=quote,
        confidence=1.0,
    )


def register_timeline(timeline_engine: TimelineEngine) -> None:
    """Register timeline positions used by character tests."""
    timeline_engine.register_chapter(TimelineChapter(chapter_index=1, title="Opening"))
    timeline_engine.register_chapter(TimelineChapter(chapter_index=8, title="Market"))
    timeline_engine.register_chapter(TimelineChapter(chapter_index=14, title="Bridge"))
    timeline_engine.register_scene(TimelineScene(position=position(1, 1), title="Road"))
    timeline_engine.register_scene(TimelineScene(position=position(8, 2), title="Blacksmith"))
    timeline_engine.register_scene(TimelineScene(position=position(14, 1), title="Bridge"))


def register_character(canon_engine: CanonEngine) -> None:
    """Register Mark as a character."""
    canon_engine.register_entity(
        CanonEntity(
            entity_id="character_mark",
            entity_type=EntityType.CHARACTER,
            display_name="Mark",
        )
    )


def register_weapon(canon_engine: CanonEngine) -> None:
    """Register the rusty dagger as a weapon."""
    canon_engine.register_entity(
        CanonEntity(
            entity_id="weapon_rusty_dagger",
            entity_type=EntityType.WEAPON,
            display_name="Rusty Dagger",
        )
    )


def test_build_card_uses_timeline_current_position() -> None:
    """Character cards use the Timeline Engine current position by default."""
    canon_engine = CanonEngine()
    timeline_engine = TimelineEngine()
    register_timeline(timeline_engine)
    register_character(canon_engine)
    canon_engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence=evidence(chapter="Chapter 1", scene="Scene 1"),
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
    timeline_engine.set_current_position(position(14, 1))
    character_engine = CharacterEngine(canon_engine, timeline_engine)

    card = character_engine.build_card("character_mark")

    assert card.character_id == "character_mark"
    assert card.display_name == "Mark"
    assert card.position == position(14, 1)
    assert card.facts["current_weapon"].value == "Iron Sword"
    assert card.facts["current_weapon"].previous_value == "Rusty Dagger"
    assert card.facts["current_weapon"].valid_from == position(8, 2)


def test_build_card_can_use_explicit_historical_position() -> None:
    """Character cards can represent an earlier story position."""
    canon_engine = CanonEngine()
    timeline_engine = TimelineEngine()
    register_timeline(timeline_engine)
    register_character(canon_engine)
    canon_engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence=evidence(chapter="Chapter 1", scene="Scene 1"),
    )
    canon_engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence=evidence(chapter="Chapter 8", scene="Scene 2"),
    )
    character_engine = CharacterEngine(canon_engine, timeline_engine)

    card = character_engine.build_card(
        character_id="character_mark",
        position=position(1, 1),
    )

    assert card.facts["current_weapon"].value == "Rusty Dagger"


def test_build_card_rejects_unregistered_explicit_position() -> None:
    """Explicit character card positions must exist in Timeline."""
    canon_engine = CanonEngine()
    timeline_engine = TimelineEngine()
    register_timeline(timeline_engine)
    register_character(canon_engine)
    character_engine = CharacterEngine(canon_engine, timeline_engine)

    with pytest.raises(InvalidTimelinePositionError):
        character_engine.build_card(
            character_id="character_mark",
            position=position(99, 1),
        )


def test_build_card_preserves_unknown_information() -> None:
    """Missing character facts remain unknown by absence."""
    canon_engine = CanonEngine()
    timeline_engine = TimelineEngine()
    register_timeline(timeline_engine)
    register_character(canon_engine)
    character_engine = CharacterEngine(canon_engine, timeline_engine)

    card = character_engine.build_card("character_mark")

    assert "hair_color" not in card.facts


def test_build_card_includes_character_relationships() -> None:
    """Character cards include canon relationships connected to the character."""
    canon_engine = CanonEngine()
    timeline_engine = TimelineEngine()
    register_timeline(timeline_engine)
    register_character(canon_engine)
    register_weapon(canon_engine)
    relationship = canon_engine.record_relationship(
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="weapon_rusty_dagger",
        evidence=evidence(quote="Mark owned the rusty dagger."),
    )
    character_engine = CharacterEngine(canon_engine, timeline_engine)

    card = character_engine.build_card("character_mark")

    assert card.relationships == (relationship,)


def test_build_card_rejects_unknown_entity() -> None:
    """Character cards cannot be built for unknown entities."""
    canon_engine = CanonEngine()
    timeline_engine = TimelineEngine()
    character_engine = CharacterEngine(canon_engine, timeline_engine)

    with pytest.raises(UnknownEntityError):
        character_engine.build_card("character_mark")


def test_build_card_rejects_non_character_entity() -> None:
    """Character Engine only builds cards for character entities."""
    canon_engine = CanonEngine()
    timeline_engine = TimelineEngine()
    register_weapon(canon_engine)
    character_engine = CharacterEngine(canon_engine, timeline_engine)

    with pytest.raises(NotACharacterError):
        character_engine.build_card("weapon_rusty_dagger")

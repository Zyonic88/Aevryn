"""Tests for Phase 6 Character Cards."""

from typing import Any, cast

import pytest

from aevryn import CanonCharacterCard, CanonCharacterFact, CanonDatabase, CharacterCardBuilder
from aevryn.core import Chapter, Character, Entity, Evidence, Fact, StateChange, TimelineEvent


def chapter(chapter_id: str, chapter_index: int) -> Chapter:
    """Create a chapter."""
    return Chapter(
        chapter_id=chapter_id,
        story_id="story_demo",
        chapter_index=chapter_index,
        title=f"Chapter {chapter_index}",
    )


def evidence(evidence_id: str, chapter_id: str, scene_id: str, quote: str) -> Evidence:
    """Create evidence."""
    return Evidence(
        evidence_id=evidence_id,
        source_id="source_demo",
        chapter_id=chapter_id,
        scene_id=scene_id,
        paragraph_index=1,
        sentence_index=1,
        quote=quote,
        confidence=1.0,
    )


def scene_event(
    event_id: str,
    chapter_id: str,
    scene_id: str,
    evidence_id: str,
) -> TimelineEvent:
    """Create an event at a specific scene."""
    return TimelineEvent(
        event_id=event_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        description=event_id,
        evidence_id=evidence_id,
    )


def build_database() -> CanonDatabase:
    """Build Canon Database with character weapon history."""
    database = CanonDatabase()
    database.store_character(
        Character(
            entity=Entity(
                entity_id="character_mark",
                entity_type="character",
                display_name="Mark",
            )
        )
    )
    database.store_chapter(chapter("chapter_001", 1))
    database.store_chapter(chapter("chapter_008", 8))
    database.store_chapter(chapter("chapter_020", 20))
    database.store_evidence(
        evidence(
            evidence_id="evidence_001",
            chapter_id="chapter_001",
            scene_id="scene_001_001",
            quote="Mark carried a rusty dagger.",
        )
    )
    database.store_evidence(
        evidence(
            evidence_id="evidence_008",
            chapter_id="chapter_008",
            scene_id="scene_008_002",
            quote="Mark bought an iron sword.",
        )
    )
    dagger_fact = Fact(
        fact_id="fact_001_mark_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence_id="evidence_001",
    )
    sword_fact = Fact(
        fact_id="fact_008_mark_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence_id="evidence_008",
    )
    database.store_fact(dagger_fact)
    database.store_fact(sword_fact)
    database.store_timeline_event(
        scene_event("event_001_weapon", "chapter_001", "scene_001_001", "evidence_001")
    )
    database.store_timeline_event(
        scene_event("event_008_weapon", "chapter_008", "scene_008_002", "evidence_008")
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_001_weapon",
            fact_id="fact_001_mark_weapon",
            valid_from_event_id="event_001_weapon",
            valid_until_event_id="event_008_weapon",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_008_weapon",
            fact_id="fact_008_mark_weapon",
            valid_from_event_id="event_008_weapon",
        )
    )
    return database


def test_character_card_builder_returns_current_state_for_chapter() -> None:
    """Character cards show accepted canon state for the requested chapter."""
    builder = CharacterCardBuilder(database=build_database())

    card = builder.build_card(character_id="character_mark", chapter_index=8)

    assert card.character_id == "character_mark"
    assert card.display_name == "Mark"
    assert card.chapter_index == 8
    assert card.facts[0].attribute == "current_weapon"
    assert card.facts[0].value == "Iron Sword"


def test_character_card_builder_includes_previous_state() -> None:
    """Character cards include previous value when canon history exists."""
    builder = CharacterCardBuilder(database=build_database())

    card = builder.build_card(character_id="character_mark", chapter_index=8)

    assert card.facts[0].previous_value == "Rusty Dagger"


def test_character_card_builder_includes_valid_from_evidence() -> None:
    """Character cards include evidence and valid-from source references."""
    builder = CharacterCardBuilder(database=build_database())

    card = builder.build_card(character_id="character_mark", chapter_index=8)

    assert card.facts[0].evidence.quote == "Mark bought an iron sword."
    assert card.facts[0].valid_from_chapter_id == "chapter_008"
    assert card.facts[0].valid_from_scene_id == "scene_008_002"


def test_character_card_builder_returns_historical_state() -> None:
    """Character cards can show earlier canon state."""
    builder = CharacterCardBuilder(database=build_database())

    card = builder.build_card(character_id="character_mark", chapter_index=1)

    assert card.facts[0].value == "Rusty Dagger"
    assert card.facts[0].previous_value is None


def test_character_card_builder_returns_scene_specific_state() -> None:
    """Scene-position cards do not leak later facts in the same chapter."""
    database = CanonDatabase()
    database.store_character(
        Character(
            entity=Entity(
                entity_id="character_mark",
                entity_type="character",
                display_name="Mark",
            )
        )
    )
    database.store_chapter(chapter("chapter_001", 1))
    database.store_evidence(
        evidence("evidence_scene_001", "chapter_001", "scene_001", "Mark was calm.")
    )
    database.store_evidence(
        evidence("evidence_scene_002", "chapter_001", "scene_002", "Mark became alarmed.")
    )
    calm_fact = Fact(
        fact_id="fact_mark_mood_calm",
        entity_id="character_mark",
        attribute="current_mood",
        value="Calm",
        evidence_id="evidence_scene_001",
    )
    alarmed_fact = Fact(
        fact_id="fact_mark_mood_alarmed",
        entity_id="character_mark",
        attribute="current_mood",
        value="Alarmed",
        evidence_id="evidence_scene_002",
    )
    database.store_fact(calm_fact)
    database.store_fact(alarmed_fact)
    database.store_timeline_event(
        scene_event("event_calm", "chapter_001", "scene_001", "evidence_scene_001")
    )
    database.store_timeline_event(
        scene_event("event_alarmed", "chapter_001", "scene_002", "evidence_scene_002")
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_calm",
            fact_id="fact_mark_mood_calm",
            valid_from_event_id="event_calm",
            valid_until_event_id="event_alarmed",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_alarmed",
            fact_id="fact_mark_mood_alarmed",
            valid_from_event_id="event_alarmed",
        )
    )
    builder = CharacterCardBuilder(database=database)

    first_scene_card = builder.build_card_at_scene(
        character_id="character_mark",
        chapter_index=1,
        scene_index=1,
    )
    second_scene_card = builder.build_card_at_scene(
        character_id="character_mark",
        chapter_index=1,
        scene_index=2,
    )

    assert tuple(fact.value for fact in first_scene_card.facts) == ("Calm",)
    assert tuple(fact.value for fact in second_scene_card.facts) == ("Alarmed",)


def test_character_card_builder_previous_value_uses_timeline_history() -> None:
    """Previous values follow timeline history instead of fact ID order."""
    database = CanonDatabase()
    database.store_character(
        Character(
            entity=Entity(
                entity_id="character_mark",
                entity_type="character",
                display_name="Mark",
            )
        )
    )
    database.store_chapter(chapter("chapter_001", 1))
    database.store_chapter(chapter("chapter_008", 8))
    database.store_evidence(
        evidence("evidence_001", "chapter_001", "scene_001", "Mark held a dagger.")
    )
    database.store_evidence(
        evidence("evidence_008", "chapter_008", "scene_008", "Mark bought a sword.")
    )
    dagger_fact = Fact(
        fact_id="fact_010_mark_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence_id="evidence_001",
    )
    sword_fact = Fact(
        fact_id="fact_002_mark_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence_id="evidence_008",
    )
    database.store_fact(dagger_fact)
    database.store_fact(sword_fact)
    database.store_timeline_event(
        scene_event("event_001_weapon", "chapter_001", "scene_001", "evidence_001")
    )
    database.store_timeline_event(
        scene_event("event_008_weapon", "chapter_008", "scene_008", "evidence_008")
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_010_weapon",
            fact_id="fact_010_mark_weapon",
            valid_from_event_id="event_001_weapon",
            valid_until_event_id="event_008_weapon",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_002_weapon",
            fact_id="fact_002_mark_weapon",
            valid_from_event_id="event_008_weapon",
        )
    )
    builder = CharacterCardBuilder(database=database)

    card = builder.build_card("character_mark", chapter_index=8)

    assert card.facts[0].value == "Iron Sword"
    assert card.facts[0].previous_value == "Rusty Dagger"


def test_character_card_builder_displays_additive_abilities() -> None:
    """Character cards keep multiple active ability facts."""
    database = build_database()
    database.store_evidence(
        evidence("evidence_ability_1", "chapter_001", "scene_001", "Mark gained luck.")
    )
    database.store_evidence(
        evidence("evidence_ability_2", "chapter_008", "scene_008", "Mark gained insight.")
    )
    fleet_luck = Fact(
        fact_id="fact_mark_ability_fleet_luck",
        entity_id="character_mark",
        attribute="ability",
        value="Fleet Luck Bonus",
        evidence_id="evidence_ability_1",
    )
    eye_of_insight = Fact(
        fact_id="fact_mark_ability_eye",
        entity_id="character_mark",
        attribute="ability",
        value="Eye of Insight",
        evidence_id="evidence_ability_2",
    )
    database.store_fact(fleet_luck)
    database.store_fact(eye_of_insight)
    database.store_timeline_event(
        scene_event("event_ability_1", "chapter_001", "scene_001", "evidence_ability_1")
    )
    database.store_timeline_event(
        scene_event("event_ability_2", "chapter_008", "scene_008", "evidence_ability_2")
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_ability_1",
            fact_id="fact_mark_ability_fleet_luck",
            valid_from_event_id="event_ability_1",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_ability_2",
            fact_id="fact_mark_ability_eye",
            valid_from_event_id="event_ability_2",
        )
    )
    builder = CharacterCardBuilder(database=database)

    card = builder.build_card("character_mark", chapter_index=8)
    ability_facts = tuple(fact for fact in card.facts if fact.attribute == "ability")

    assert tuple(fact.value for fact in ability_facts) == (
        "Fleet Luck Bonus",
        "Eye of Insight",
    )
    assert all(fact.previous_value is None for fact in ability_facts)


def test_character_card_builder_uses_active_display_name_fact() -> None:
    """Historical character cards display the active canon name."""
    database = build_database()
    database.store_evidence(
        evidence("evidence_name", "chapter_001", "scene_001", "Mark introduced himself.")
    )
    name_fact = Fact(
        fact_id="fact_001_display_name",
        entity_id="character_mark",
        attribute="display_name",
        value="Mark",
        evidence_id="evidence_name",
    )
    database.store_fact(name_fact)
    database.store_timeline_event(
        scene_event("event_001_name", "chapter_001", "scene_001", "evidence_name")
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_001_display_name",
            fact_id="fact_001_display_name",
            valid_from_event_id="event_001_name",
        )
    )
    database.update_character(
        Character(
            entity=Entity(
                entity_id="character_mark",
                entity_type="character",
                display_name="Sir Mark",
            )
        )
    )
    builder = CharacterCardBuilder(database=database)

    card = builder.build_card("character_mark", chapter_index=1)

    assert card.display_name == "Mark"


def test_character_card_builder_rejects_unknown_character() -> None:
    """Unknown characters cannot get character cards."""
    builder = CharacterCardBuilder(database=CanonDatabase())

    with pytest.raises(ValueError, match="Unknown character"):
        builder.build_card(character_id="character_mark", chapter_index=1)


def test_character_card_builder_rejects_invalid_chapter_index() -> None:
    """Character card lookups use one-based story positions."""
    builder = CharacterCardBuilder(database=build_database())

    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        builder.build_card(character_id="character_mark", chapter_index=0)

    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        builder.build_card(character_id="character_mark", chapter_index=True)

    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        builder.build_card(
            character_id="character_mark",
            chapter_index=cast(Any, "1"),
        )


def test_character_card_builder_rejects_invalid_scene_index() -> None:
    """Scene-position character card lookups use one-based positions."""
    builder = CharacterCardBuilder(database=build_database())

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        builder.build_card_at_scene(
            character_id="character_mark",
            chapter_index=1,
            scene_index=0,
        )

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        builder.build_card_at_scene(
            character_id="character_mark",
            chapter_index=1,
            scene_index=True,
        )

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        builder.build_card_at_scene(
            character_id="character_mark",
            chapter_index=1,
            scene_index=cast(Any, "1"),
        )


def test_canon_character_fact_rejects_invalid_display_fields() -> None:
    """Character card facts reject malformed display data."""
    with pytest.raises(ValueError, match="attribute cannot contain whitespace"):
        CanonCharacterFact(
            attribute="current weapon",
            value="Rusty Dagger",
            previous_value=None,
            evidence=evidence("evidence_001", "chapter_001", "scene_001", "Quote."),
            valid_from_chapter_id="chapter_001",
            valid_from_scene_id="scene_001",
        )

    with pytest.raises(ValueError, match="valid-from scene ID cannot contain whitespace"):
        CanonCharacterFact(
            attribute="current_weapon",
            value="Rusty Dagger",
            previous_value=None,
            evidence=evidence("evidence_001", "chapter_001", "scene_001", "Quote."),
            valid_from_chapter_id="chapter_001",
            valid_from_scene_id="scene 001",
        )


def test_canon_character_fact_normalizes_display_values() -> None:
    """Canon-backed character card facts normalize visible values."""
    fact = CanonCharacterFact(
        attribute="current_weapon",
        value=" Rusty   Dagger ",
        previous_value=" Old   Knife ",
        evidence=evidence("evidence_001", "chapter_001", "scene_001", "Quote."),
        valid_from_chapter_id="chapter_001",
        valid_from_scene_id="scene_001",
    )

    assert fact.value == "Rusty Dagger"
    assert fact.previous_value == "Old Knife"


def test_canon_character_card_rejects_invalid_identity() -> None:
    """Character cards reject malformed identity and chapter values."""
    with pytest.raises(ValueError, match="character ID cannot contain whitespace"):
        CanonCharacterCard(
            character_id="character mark",
            display_name="Mark",
            chapter_index=1,
            facts=(),
        )


def test_canon_character_card_normalizes_display_name() -> None:
    """Canon-backed character cards normalize visible display names."""
    card = CanonCharacterCard(
        character_id="character_mark",
        display_name=" Mark   Stone ",
        chapter_index=1,
        facts=(),
    )

    assert card.display_name == "Mark Stone"

    with pytest.raises(ValueError, match="chapter index must be at least 1"):
        CanonCharacterCard(
            character_id="character_mark",
            display_name="Mark",
            chapter_index=0,
            facts=(),
        )

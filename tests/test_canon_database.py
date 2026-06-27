"""Tests for Phase 2 Canon Database storage."""

from typing import Any, cast

import pytest

from aevryn import CanonDatabase
from aevryn.core import (
    Chapter,
    Character,
    Entity,
    Evidence,
    Fact,
    Relationship,
    Scene,
    StateChange,
    TimelineEvent,
)


def character(name: str) -> Character:
    """Create a character core model."""
    return Character(
        entity=Entity(
            entity_id="character_mark",
            entity_type="character",
            display_name=name,
        )
    )


def generic_entity(entity_id: str, entity_type: str = "item") -> Entity:
    """Create a generic canon entity for database tests."""
    return Entity(
        entity_id=entity_id,
        entity_type=entity_type,
        display_name=entity_id.replace("_", " ").title(),
    )


def chapter(chapter_id: str, chapter_index: int) -> Chapter:
    """Create a chapter core model."""
    return Chapter(
        chapter_id=chapter_id,
        story_id="story_demo",
        chapter_index=chapter_index,
        title=f"Chapter {chapter_index}",
    )


def evidence(
    evidence_id: str,
    chapter_id: str,
    scene_id: str,
    paragraph_index: int = 1,
    sentence_index: int = 1,
) -> Evidence:
    """Create an evidence core model."""
    return Evidence(
        evidence_id=evidence_id,
        source_id="source_demo",
        chapter_id=chapter_id,
        scene_id=scene_id,
        paragraph_index=paragraph_index,
        sentence_index=sentence_index,
        quote="Evidence quote.",
        confidence=1.0,
    )


def event(event_id: str, chapter_id: str, evidence_id: str) -> TimelineEvent:
    """Create a timeline event core model."""
    evidence_scene_id = f"scene_{evidence_id.removeprefix('evidence_')}"
    return TimelineEvent(
        event_id=event_id,
        chapter_id=chapter_id,
        scene_id=evidence_scene_id,
        description=f"Event {event_id}",
        evidence_id=evidence_id,
    )


def scene_event(
    event_id: str,
    chapter_id: str,
    scene_id: str,
    evidence_id: str,
) -> TimelineEvent:
    """Create a timeline event at an explicit scene position."""
    return TimelineEvent(
        event_id=event_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        description=f"Event {event_id}",
        evidence_id=evidence_id,
    )


def test_store_and_retrieve_character() -> None:
    """Canon Database stores and retrieves the latest character version."""
    database = CanonDatabase()
    mark = character("Mark")

    database.store_character(mark)

    assert database.retrieve_character("character_mark") == mark


def test_store_character_rejects_duplicate_initial_version() -> None:
    """A character must be updated through versioning after initial storage."""
    database = CanonDatabase()
    mark = character("Mark")
    database.store_character(mark)

    with pytest.raises(ValueError, match="Character already exists"):
        database.store_character(mark)


def test_update_character_appends_new_version() -> None:
    """Updating a character preserves previous versions."""
    database = CanonDatabase()
    original = character("Mark")
    renamed = character("Sir Mark")
    database.store_character(original)

    database.update_character(renamed)

    assert database.retrieve_character("character_mark") == renamed
    assert database.version_character("character_mark") == (original, renamed)


def test_update_character_ignores_identical_version() -> None:
    """Updating a character with identical data is idempotent."""
    database = CanonDatabase()
    mark = character("Mark")
    database.store_character(mark)

    database.update_character(mark)

    assert database.version_character("character_mark") == (mark,)


def test_update_character_rejects_unknown_character() -> None:
    """Unknown characters cannot be updated."""
    database = CanonDatabase()

    with pytest.raises(ValueError, match="Unknown character"):
        database.update_character(character("Mark"))


def test_store_and_retrieve_generic_entity() -> None:
    """Canon Database stores and retrieves non-character entities."""
    database = CanonDatabase()
    location = Entity(
        entity_id="location_northern_forest",
        entity_type="location",
        display_name="Northern Forest",
    )

    database.store_entity(location)

    assert database.retrieve_entity("location_northern_forest") == location


def test_update_generic_entity_versions_history() -> None:
    """Generic entity updates preserve previous versions."""
    database = CanonDatabase()
    original = Entity(
        entity_id="location_northern_forest",
        entity_type="location",
        display_name="Northern Forest",
    )
    renamed = Entity(
        entity_id="location_northern_forest",
        entity_type="location",
        display_name="Northern Wilds",
    )
    database.store_entity(original)

    database.update_entity(renamed)

    assert database.retrieve_entity("location_northern_forest") == renamed
    assert database.version_entity("location_northern_forest") == (original, renamed)


def test_update_generic_entity_ignores_identical_version() -> None:
    """Updating a generic entity with identical data is idempotent."""
    database = CanonDatabase()
    location = Entity(
        entity_id="location_northern_forest",
        entity_type="location",
        display_name="Northern Forest",
    )
    database.store_entity(location)

    database.update_entity(location)

    assert database.version_entity("location_northern_forest") == (location,)


def test_store_chapter_is_idempotent_for_identical_data() -> None:
    """Storing the same chapter twice does not create a conflict."""
    database = CanonDatabase()
    first_chapter = chapter("chapter_001", 1)

    database.store_chapter(first_chapter)
    database.store_chapter(first_chapter)

    assert database.retrieve_state_at_chapter("character_mark", 1) == ()


def test_store_chapter_rejects_conflicting_id() -> None:
    """Chapter IDs cannot be silently reused for different data."""
    database = CanonDatabase()
    database.store_chapter(chapter("chapter_001", 1))

    with pytest.raises(ValueError, match="Conflicting chapter"):
        database.store_chapter(
            Chapter(
                chapter_id="chapter_001",
                story_id="story_demo",
                chapter_index=2,
                title="Wrong Chapter",
            )
        )


def test_store_evidence_rejects_conflicting_id() -> None:
    """Evidence IDs cannot be silently reused for different anchors."""
    database = CanonDatabase()
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))

    with pytest.raises(ValueError, match="Conflicting evidence"):
        database.store_evidence(evidence("evidence_001", "chapter_001", "scene_002"))


def test_store_evidence_rejects_unknown_registered_chapter() -> None:
    """Evidence must point to known chapters once chapter structure is registered."""
    database = CanonDatabase()
    database.store_chapter(chapter("chapter_001", 1))

    with pytest.raises(ValueError, match="Unknown chapter"):
        database.store_evidence(evidence("evidence_999", "chapter_999", "scene_001"))


def test_store_evidence_rejects_unknown_registered_scene() -> None:
    """Evidence must point to known scenes when a chapter has scene structure."""
    database = CanonDatabase()
    database.store_chapter(
        Chapter(
            chapter_id="chapter_001",
            story_id="story_demo",
            chapter_index=1,
            title="Chapter 1",
            scenes=(
                Scene(
                    scene_id="scene_001",
                    chapter_id="chapter_001",
                    scene_index=1,
                    title="Scene 1",
                ),
            ),
        )
    )

    with pytest.raises(ValueError, match="Unknown scene"):
        database.store_evidence(evidence("evidence_002", "chapter_001", "scene_002"))


def test_store_fact_requires_stored_evidence() -> None:
    """Facts cannot be stored without evidence already in Canon Database."""
    database = CanonDatabase()

    with pytest.raises(ValueError, match="Unknown evidence"):
        database.store_fact(
            Fact(
                fact_id="fact_mark_weapon_dagger",
                entity_id="character_mark",
                attribute="current_weapon",
                value="Rusty Dagger",
                evidence_id="evidence_missing",
            )
        )


def test_store_fact_is_idempotent_for_identical_data() -> None:
    """Storing the same fact twice is a no-op."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))
    fact = Fact(
        fact_id="fact_mark_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence_id="evidence_001",
    )

    database.store_fact(fact)
    database.store_fact(fact)

    assert database.retrieve_fact("fact_mark_weapon") == fact


def test_store_fact_rejects_conflicting_id() -> None:
    """Fact IDs cannot be silently reused for different canon values."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))
    database.store_fact(
        Fact(
            fact_id="fact_mark_weapon",
            entity_id="character_mark",
            attribute="current_weapon",
            value="Rusty Dagger",
            evidence_id="evidence_001",
        )
    )

    with pytest.raises(ValueError, match="Conflicting fact"):
        database.store_fact(
            Fact(
                fact_id="fact_mark_weapon",
                entity_id="character_mark",
                attribute="current_weapon",
                value="Iron Sword",
                evidence_id="evidence_001",
            )
        )


def test_store_fact_requires_known_entity() -> None:
    """Facts cannot be stored for unknown entities."""
    database = CanonDatabase()
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))

    with pytest.raises(ValueError, match="Unknown entity"):
        database.store_fact(
            Fact(
                fact_id="fact_mark_weapon",
                entity_id="character_mark",
                attribute="current_weapon",
                value="Rusty Dagger",
                evidence_id="evidence_001",
            )
        )


def test_store_relationship_dedupes_identical_semantic_relationships() -> None:
    """Canon Database keeps one semantic relationship connection."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_entity(generic_entity("item_iron_sword"))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))
    database.store_evidence(evidence("evidence_002", "chapter_001", "scene_001"))
    first = Relationship(
        relationship_id="relationship_001",
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="item_iron_sword",
        evidence_id="evidence_001",
    )
    duplicate = Relationship(
        relationship_id="relationship_002",
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="item_iron_sword",
        evidence_id="evidence_002",
    )

    database.store_relationship(first)
    database.store_relationship(duplicate)

    assert database.list_relationships_for_entity("character_mark") == (first,)


def test_store_relationship_rejects_conflicting_id() -> None:
    """Relationship IDs cannot be silently reused for different connections."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_entity(generic_entity("item_iron_sword"))
    database.store_entity(generic_entity("location_academy", "location"))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))
    database.store_evidence(evidence("evidence_002", "chapter_001", "scene_001"))
    database.store_relationship(
        Relationship(
            relationship_id="relationship_001",
            source_entity_id="character_mark",
            relationship_type="owns",
            target_entity_id="item_iron_sword",
            evidence_id="evidence_001",
        )
    )

    with pytest.raises(ValueError, match="Conflicting relationship"):
        database.store_relationship(
            Relationship(
                relationship_id="relationship_001",
                source_entity_id="character_mark",
                relationship_type="located_at",
                target_entity_id="location_academy",
                evidence_id="evidence_002",
            )
        )


def test_store_relationship_requires_known_source_and_target() -> None:
    """Relationships cannot connect unknown entities."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))

    with pytest.raises(ValueError, match="Unknown entity: item_iron_sword"):
        database.store_relationship(
            Relationship(
                relationship_id="relationship_001",
                source_entity_id="character_mark",
                relationship_type="owns",
                target_entity_id="item_iron_sword",
                evidence_id="evidence_001",
            )
        )


def test_list_relationships_at_chapter_keeps_latest_exclusive_relationship() -> None:
    """Timeline-aware relationship lookup drops stale exclusive relationships."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_entity(generic_entity("location_classroom", "location"))
    database.store_entity(generic_entity("location_cafeteria", "location"))
    database.store_chapter(chapter("chapter_001", 1))
    database.store_chapter(chapter("chapter_002", 2))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))
    database.store_evidence(evidence("evidence_002", "chapter_002", "scene_002"))
    classroom = Relationship(
        relationship_id="relationship_mark_classroom",
        source_entity_id="character_mark",
        relationship_type="located_at",
        target_entity_id="location_classroom",
        evidence_id="evidence_001",
    )
    cafeteria = Relationship(
        relationship_id="relationship_mark_cafeteria",
        source_entity_id="character_mark",
        relationship_type="located_at",
        target_entity_id="location_cafeteria",
        evidence_id="evidence_002",
    )
    database.store_relationship(classroom)
    database.store_relationship(cafeteria)

    assert database.list_relationships_for_entity_at_chapter("character_mark", 1) == (
        classroom,
    )
    assert database.list_relationships_for_entity_at_chapter("character_mark", 2) == (
        cafeteria,
    )
    assert database.list_relationships_for_entity_at_chapter("location_classroom", 2) == ()


def test_list_relationships_at_chapter_keeps_nonexclusive_history() -> None:
    """Nonexclusive relationship types remain visible once known."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_entity(generic_entity("item_dagger"))
    database.store_entity(generic_entity("item_blueprint"))
    database.store_chapter(chapter("chapter_001", 1))
    database.store_chapter(chapter("chapter_002", 2))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))
    database.store_evidence(evidence("evidence_002", "chapter_002", "scene_002"))
    dagger = Relationship(
        relationship_id="relationship_mark_dagger",
        source_entity_id="character_mark",
        relationship_type="has_item",
        target_entity_id="item_dagger",
        evidence_id="evidence_001",
    )
    blueprint = Relationship(
        relationship_id="relationship_mark_blueprint",
        source_entity_id="character_mark",
        relationship_type="has_item",
        target_entity_id="item_blueprint",
        evidence_id="evidence_002",
    )
    database.store_relationship(dagger)
    database.store_relationship(blueprint)

    assert database.list_relationships_for_entity_at_chapter("character_mark", 2) == (
        dagger,
        blueprint,
    )


def test_scene_position_relationship_lookup_blocks_later_same_chapter_state() -> None:
    """Scene-aware relationship lookup does not leak later scenes."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_entity(generic_entity("location_classroom", "location"))
    database.store_entity(generic_entity("location_hangar", "location"))
    database.store_chapter(chapter("chapter_001", 1))
    database.store_evidence(evidence("evidence_scene_001", "chapter_001", "scene_001"))
    database.store_evidence(evidence("evidence_scene_002", "chapter_001", "scene_002"))
    classroom = Relationship(
        relationship_id="relationship_mark_classroom",
        source_entity_id="character_mark",
        relationship_type="located_at",
        target_entity_id="location_classroom",
        evidence_id="evidence_scene_001",
    )
    hangar = Relationship(
        relationship_id="relationship_mark_hangar",
        source_entity_id="character_mark",
        relationship_type="located_at",
        target_entity_id="location_hangar",
        evidence_id="evidence_scene_002",
    )
    database.store_relationship(classroom)
    database.store_relationship(hangar)

    assert database.list_relationships_for_entity_at_scene(
        entity_id="character_mark",
        chapter_index=1,
        scene_index=1,
    ) == (classroom,)
    assert database.list_relationships_for_entity_at_scene(
        entity_id="character_mark",
        chapter_index=1,
        scene_index=2,
    ) == (hangar,)


def test_retrieve_state_at_chapter_uses_validity_windows() -> None:
    """Canon Database retrieves entity state valid at a chapter."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_chapter(chapter("chapter_001", 1))
    database.store_chapter(chapter("chapter_008", 8))
    database.store_chapter(chapter("chapter_020", 20))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001_001"))
    database.store_evidence(evidence("evidence_008", "chapter_008", "scene_008_002"))
    database.store_evidence(evidence("evidence_020", "chapter_020", "scene_020_003"))
    dagger_fact = Fact(
        fact_id="fact_mark_weapon_dagger",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence_id="evidence_001",
    )
    sword_fact = Fact(
        fact_id="fact_mark_weapon_sword",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence_id="evidence_008",
    )
    database.store_fact(dagger_fact)
    database.store_fact(sword_fact)
    database.store_timeline_event(
        scene_event("event_dagger", "chapter_001", "scene_001_001", "evidence_001")
    )
    database.store_timeline_event(
        scene_event("event_sword", "chapter_008", "scene_008_002", "evidence_008")
    )
    database.store_timeline_event(
        scene_event("event_lost_sword", "chapter_020", "scene_020_003", "evidence_020")
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_mark_weapon_dagger",
            fact_id="fact_mark_weapon_dagger",
            valid_from_event_id="event_dagger",
            valid_until_event_id="event_sword",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_mark_weapon_sword",
            fact_id="fact_mark_weapon_sword",
            valid_from_event_id="event_sword",
            valid_until_event_id="event_lost_sword",
        )
    )

    stored_state_change = database.retrieve_state_change("state_mark_weapon_sword")

    assert stored_state_change is not None
    assert stored_state_change.fact_id == "fact_mark_weapon_sword"
    assert database.retrieve_state_at_chapter("character_mark", 1) == (dagger_fact,)
    assert database.retrieve_state_at_chapter("character_mark", 14) == (sword_fact,)
    assert database.retrieve_state_at_chapter("character_mark", 20) == ()


def test_retrieve_state_at_scene_blocks_later_same_chapter_facts() -> None:
    """Scene-aware state lookup only sees facts valid by that scene."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_chapter(chapter("chapter_001", 1))
    database.store_evidence(evidence("evidence_scene_001", "chapter_001", "scene_001"))
    database.store_evidence(evidence("evidence_scene_002", "chapter_001", "scene_002"))
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

    assert database.retrieve_state_at_scene(
        entity_id="character_mark",
        chapter_index=1,
        scene_index=1,
    ) == (calm_fact,)
    assert database.retrieve_state_at_scene(
        entity_id="character_mark",
        chapter_index=1,
        scene_index=2,
    ) == (alarmed_fact,)


def test_chapter_lookups_reject_invalid_chapter_index() -> None:
    """Canon Database chapter lookups use one-based story positions."""
    database = CanonDatabase()

    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        database.retrieve_state_at_chapter(
            entity_id="character_mark",
            chapter_index=0,
        )

    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        database.list_relationships_for_entity_at_chapter(
            entity_id="character_mark",
            chapter_index=0,
        )

    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        database.retrieve_state_at_chapter(
            entity_id="character_mark",
            chapter_index=True,
        )

    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        database.retrieve_state_at_chapter(
            entity_id="character_mark",
            chapter_index=cast(Any, "1"),
        )


def test_scene_lookups_reject_invalid_scene_index() -> None:
    """Canon Database scene lookups use one-based story positions."""
    database = CanonDatabase()

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        database.retrieve_state_at_scene(
            entity_id="character_mark",
            chapter_index=1,
            scene_index=0,
        )

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        database.list_relationships_for_entity_at_scene(
            entity_id="character_mark",
            chapter_index=1,
            scene_index=0,
        )

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        database.retrieve_state_at_scene(
            entity_id="character_mark",
            chapter_index=1,
            scene_index=True,
        )

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        database.retrieve_state_at_scene(
            entity_id="character_mark",
            chapter_index=1,
            scene_index=cast(Any, "1"),
        )


def test_retrieve_state_at_chapter_keeps_additive_attributes_active() -> None:
    """Additive attributes accumulate instead of replacing prior values."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_chapter(chapter("chapter_001", 1))
    database.store_chapter(chapter("chapter_002", 2))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))
    database.store_evidence(evidence("evidence_002", "chapter_002", "scene_002"))
    fleet_luck = Fact(
        fact_id="fact_mark_ability_fleet_luck",
        entity_id="character_mark",
        attribute="ability",
        value="Fleet Luck Bonus",
        evidence_id="evidence_001",
    )
    eye_of_insight = Fact(
        fact_id="fact_mark_ability_eye",
        entity_id="character_mark",
        attribute="ability",
        value="Eye of Insight",
        evidence_id="evidence_002",
    )
    database.store_fact(fleet_luck)
    database.store_fact(eye_of_insight)
    database.store_timeline_event(event("event_fleet_luck", "chapter_001", "evidence_001"))
    database.store_timeline_event(event("event_eye", "chapter_002", "evidence_002"))
    database.store_state_change(
        StateChange(
            state_change_id="state_fleet_luck",
            fact_id="fact_mark_ability_fleet_luck",
            valid_from_event_id="event_fleet_luck",
        )
    )
    database.close_open_state_changes(
        entity_id="character_mark",
        attribute="ability",
        valid_until_event_id="event_eye",
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_eye",
            fact_id="fact_mark_ability_eye",
            valid_from_event_id="event_eye",
        )
    )

    active_values = tuple(
        fact.value
        for fact in database.retrieve_state_at_chapter("character_mark", 2)
        if fact.attribute == "ability"
    )

    assert active_values == ("Fleet Luck Bonus", "Eye of Insight")


def test_fact_history_uses_timeline_order_before_fact_id_order() -> None:
    """Fact history follows story chronology rather than lexicographic IDs."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_chapter(chapter("chapter_001", 1))
    database.store_chapter(chapter("chapter_008", 8))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))
    database.store_evidence(evidence("evidence_008", "chapter_008", "scene_008"))
    early_fact = Fact(
        fact_id="fact_010_mark_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence_id="evidence_001",
    )
    later_fact = Fact(
        fact_id="fact_002_mark_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence_id="evidence_008",
    )
    database.store_fact(early_fact)
    database.store_fact(later_fact)
    database.store_timeline_event(event("event_001", "chapter_001", "evidence_001"))
    database.store_timeline_event(event("event_008", "chapter_008", "evidence_008"))
    database.store_state_change(
        StateChange(
            state_change_id="state_010_mark_weapon",
            fact_id="fact_010_mark_weapon",
            valid_from_event_id="event_001",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_002_mark_weapon",
            fact_id="fact_002_mark_weapon",
            valid_from_event_id="event_008",
        )
    )

    assert database.retrieve_fact_history("character_mark", "current_weapon") == (
        early_fact,
        later_fact,
    )
    assert database.retrieve_current_fact("character_mark", "current_weapon") == later_fact


def test_store_state_change_rejects_unknown_fact() -> None:
    """State changes cannot reference missing facts."""
    database = CanonDatabase()

    with pytest.raises(ValueError, match="Unknown fact"):
        database.store_state_change(
            StateChange(
                state_change_id="state_missing",
                fact_id="fact_missing",
                valid_from_event_id="event_missing",
            )
        )


def test_store_timeline_event_rejects_evidence_chapter_mismatch() -> None:
    """Timeline events must cite evidence from the same chapter."""
    database = CanonDatabase()
    database.store_chapter(chapter("chapter_001", 1))
    database.store_chapter(chapter("chapter_002", 2))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))

    with pytest.raises(ValueError, match="must match evidence chapter"):
        database.store_timeline_event(
            TimelineEvent(
                event_id="event_wrong_chapter",
                chapter_id="chapter_002",
                scene_id="scene_002",
                description="Wrong chapter event.",
                evidence_id="evidence_001",
            )
        )


def test_store_timeline_event_rejects_evidence_scene_mismatch() -> None:
    """Timeline events must cite evidence from the same scene."""
    database = CanonDatabase()
    database.store_chapter(chapter("chapter_001", 1))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))

    with pytest.raises(ValueError, match="must match evidence scene"):
        database.store_timeline_event(
            TimelineEvent(
                event_id="event_wrong_scene",
                chapter_id="chapter_001",
                scene_id="scene_002",
                description="Wrong scene event.",
                evidence_id="evidence_001",
            )
        )


def test_store_state_change_rejects_backward_validity_window() -> None:
    """State changes cannot end before they begin."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_chapter(chapter("chapter_001", 1))
    database.store_chapter(chapter("chapter_002", 2))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))
    database.store_evidence(evidence("evidence_002", "chapter_002", "scene_002"))
    fact = Fact(
        fact_id="fact_mark_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence_id="evidence_001",
    )
    database.store_fact(fact)
    database.store_timeline_event(event("event_start", "chapter_002", "evidence_002"))
    database.store_timeline_event(event("event_end", "chapter_001", "evidence_001"))

    with pytest.raises(ValueError, match="cannot be earlier"):
        database.store_state_change(
            StateChange(
                state_change_id="state_backward",
                fact_id="fact_mark_weapon",
                valid_from_event_id="event_start",
                valid_until_event_id="event_end",
            )
        )


def test_close_open_state_changes_rejects_backward_validity_window() -> None:
    """Closing an open state cannot create a backward validity window."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_chapter(chapter("chapter_001", 1))
    database.store_chapter(chapter("chapter_002", 2))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))
    database.store_evidence(evidence("evidence_002", "chapter_002", "scene_002"))
    fact = Fact(
        fact_id="fact_mark_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence_id="evidence_002",
    )
    database.store_fact(fact)
    database.store_timeline_event(event("event_start", "chapter_002", "evidence_002"))
    database.store_timeline_event(event("event_end", "chapter_001", "evidence_001"))
    database.store_state_change(
        StateChange(
            state_change_id="state_weapon",
            fact_id="fact_mark_weapon",
            valid_from_event_id="event_start",
        )
    )

    with pytest.raises(ValueError, match="cannot be earlier"):
        database.close_open_state_changes(
            entity_id="character_mark",
            attribute="current_weapon",
            valid_until_event_id="event_end",
        )


def test_close_open_state_changes_allows_later_sentence_in_same_scene() -> None:
    """Same-scene replacements are ordered by evidence sentence position."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_chapter(
        Chapter(
            chapter_id="chapter_001",
            story_id="story_demo",
            chapter_index=1,
            title="Chapter 1",
                scenes=(Scene("scene_001", "chapter_001", 1, "Scene 1"),),
        )
    )
    database.store_evidence(
        evidence("evidence_001", "chapter_001", "scene_001", sentence_index=1)
    )
    database.store_evidence(
        evidence("evidence_002", "chapter_001", "scene_001", sentence_index=2)
    )
    first_fact = Fact(
        fact_id="fact_mark_mood_calm",
        entity_id="character_mark",
        attribute="current_mood",
        value="Calm",
        evidence_id="evidence_001",
    )
    second_fact = Fact(
        fact_id="fact_mark_mood_alarmed",
        entity_id="character_mark",
        attribute="current_mood",
        value="Alarmed",
        evidence_id="evidence_002",
    )
    database.store_fact(first_fact)
    database.store_fact(second_fact)
    database.store_timeline_event(
        scene_event("event_calm", "chapter_001", "scene_001", "evidence_001")
    )
    database.store_timeline_event(
        scene_event("event_alarmed", "chapter_001", "scene_001", "evidence_002")
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_calm",
            fact_id="fact_mark_mood_calm",
            valid_from_event_id="event_calm",
        )
    )

    database.close_open_state_changes(
        entity_id="character_mark",
        attribute="current_mood",
        valid_until_event_id="event_alarmed",
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_alarmed",
            fact_id="fact_mark_mood_alarmed",
            valid_from_event_id="event_alarmed",
        )
    )

    state = database.retrieve_state_at_scene("character_mark", 1, 1)

    assert tuple(fact.value for fact in state if fact.attribute == "current_mood") == (
        "Alarmed",
    )


def test_close_open_state_changes_rejects_same_source_position_replacement() -> None:
    """Same-position replacements are ambiguous and cannot close prior state."""
    database = CanonDatabase()
    database.store_character(character("Mark"))
    database.store_chapter(chapter("chapter_001", 1))
    database.store_evidence(evidence("evidence_001", "chapter_001", "scene_001"))
    database.store_evidence(evidence("evidence_002", "chapter_001", "scene_001"))
    first_fact = Fact(
        fact_id="fact_mark_mood_calm",
        entity_id="character_mark",
        attribute="current_mood",
        value="Calm",
        evidence_id="evidence_001",
    )
    second_fact = Fact(
        fact_id="fact_mark_mood_alarmed",
        entity_id="character_mark",
        attribute="current_mood",
        value="Alarmed",
        evidence_id="evidence_002",
    )
    database.store_fact(first_fact)
    database.store_fact(second_fact)
    database.store_timeline_event(
        scene_event("event_calm", "chapter_001", "scene_001", "evidence_001")
    )
    database.store_timeline_event(
        scene_event("event_alarmed", "chapter_001", "scene_001", "evidence_002")
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_calm",
            fact_id="fact_mark_mood_calm",
            valid_from_event_id="event_calm",
        )
    )

    with pytest.raises(ValueError, match="cannot be earlier"):
        database.close_open_state_changes(
            entity_id="character_mark",
            attribute="current_mood",
            valid_until_event_id="event_alarmed",
        )

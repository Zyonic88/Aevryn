"""Tests for World Engine."""

from typing import Any, cast

import pytest

from scenesmith import (
    CanonDatabase,
    WorldEntityFact,
    WorldEntityState,
    WorldState,
    WorldStateBuilder,
)
from scenesmith.core import (
    Chapter,
    Character,
    Entity,
    Evidence,
    Fact,
    Relationship,
    StateChange,
    TimelineEvent,
)


def evidence(evidence_id: str, chapter_id: str, scene_id: str, quote: str) -> Evidence:
    """Create evidence for world state tests."""
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


def event(event_id: str, chapter_id: str, scene_id: str, evidence_id: str) -> TimelineEvent:
    """Create a timeline event for world state tests."""
    return TimelineEvent(
        event_id=event_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        description=event_id,
        evidence_id=evidence_id,
    )


def build_database() -> CanonDatabase:
    """Build Canon Database with world-state history."""
    database = CanonDatabase()
    database.store_entity(
        Entity(
            entity_id="location_northern_fortress",
            entity_type="location",
            display_name="Northern Fortress",
        )
    )
    database.store_entity(
        Entity(
            entity_id="organization_iron_guard",
            entity_type="organization",
            display_name="Iron Guard",
        )
    )
    database.store_chapter(
        Chapter(
            chapter_id="chapter_001",
            story_id="story_demo",
            chapter_index=1,
            title="Chapter 1",
        )
    )
    database.store_chapter(
        Chapter(
            chapter_id="chapter_006",
            story_id="story_demo",
            chapter_index=6,
            title="Chapter 6",
        )
    )
    database.store_evidence(
        evidence(
            evidence_id="evidence_owner",
            chapter_id="chapter_001",
            scene_id="chapter_001_scene_001",
            quote="The Iron Guard held the Northern Fortress.",
        )
    )
    database.store_evidence(
        evidence(
            evidence_id="evidence_damage",
            chapter_id="chapter_006",
            scene_id="chapter_006_scene_001",
            quote="The Northern Fortress walls were damaged in the siege.",
        )
    )
    owner_fact = Fact(
        fact_id="fact_fortress_owner",
        entity_id="location_northern_fortress",
        attribute="ownership",
        value="Iron Guard",
        evidence_id="evidence_owner",
    )
    damage_fact = Fact(
        fact_id="fact_fortress_damage",
        entity_id="location_northern_fortress",
        attribute="damage",
        value="Walls damaged",
        evidence_id="evidence_damage",
    )
    database.store_fact(owner_fact)
    database.store_fact(damage_fact)
    database.store_relationship(
        Relationship(
            relationship_id="relationship_iron_guard_controls_fortress",
            source_entity_id="organization_iron_guard",
            relationship_type="controls",
            target_entity_id="location_northern_fortress",
            evidence_id="evidence_owner",
        )
    )
    database.store_timeline_event(
        event(
            event_id="event_owner",
            chapter_id="chapter_001",
            scene_id="chapter_001_scene_001",
            evidence_id="evidence_owner",
        )
    )
    database.store_timeline_event(
        event(
            event_id="event_damage",
            chapter_id="chapter_006",
            scene_id="chapter_006_scene_001",
            evidence_id="evidence_damage",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_owner",
            fact_id="fact_fortress_owner",
            valid_from_event_id="event_owner",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_damage",
            fact_id="fact_fortress_damage",
            valid_from_event_id="event_damage",
        )
    )
    return database


def test_world_state_builder_reconstructs_world_entity_state() -> None:
    """World Engine returns accepted world state for a chapter."""
    builder = WorldStateBuilder(database=build_database())

    state = builder.build_entity_state(
        entity_id="location_northern_fortress",
        chapter_index=6,
    )

    assert state.display_name == "Northern Fortress"
    assert state.entity_type == "location"
    assert tuple(fact.attribute for fact in state.facts) == ("damage", "ownership")
    assert state.relationships[0].relationship_type == "controls"


def test_world_state_builder_includes_evidence_references() -> None:
    """World facts carry source evidence."""
    builder = WorldStateBuilder(database=build_database())

    state = builder.build_entity_state(
        entity_id="location_northern_fortress",
        chapter_index=6,
    )

    damage = next(fact for fact in state.facts if fact.attribute == "damage")

    assert damage.evidence.quote == "The Northern Fortress walls were damaged in the siege."
    assert damage.valid_from_chapter_id == "chapter_006"
    assert damage.valid_from_scene_id == "chapter_006_scene_001"


def test_world_state_builder_returns_selected_entities() -> None:
    """World Engine can build a multi-entity world state view."""
    builder = WorldStateBuilder(database=build_database())

    state = builder.build_state(
        entity_ids=("location_northern_fortress", "organization_iron_guard"),
        chapter_index=6,
    )

    assert state.chapter_index == 6
    assert tuple(entity.entity_id for entity in state.entities) == (
        "location_northern_fortress",
        "organization_iron_guard",
    )


def test_world_state_builder_returns_scene_specific_world_state() -> None:
    """Scene-position world state does not leak later same-chapter facts."""
    database = CanonDatabase()
    database.store_entity(
        Entity(
            entity_id="location_hangar",
            entity_type="location",
            display_name="Hangar",
        )
    )
    database.store_chapter(
        Chapter(
            chapter_id="chapter_001",
            story_id="story_demo",
            chapter_index=1,
            title="Chapter 1",
        )
    )
    database.store_evidence(
        evidence(
            evidence_id="evidence_quiet",
            chapter_id="chapter_001",
            scene_id="chapter_001_scene_001",
            quote="The hangar was quiet.",
        )
    )
    database.store_evidence(
        evidence(
            evidence_id="evidence_alarm",
            chapter_id="chapter_001",
            scene_id="chapter_001_scene_002",
            quote="The hangar alarm started.",
        )
    )
    quiet_fact = Fact(
        fact_id="fact_hangar_condition_quiet",
        entity_id="location_hangar",
        attribute="condition",
        value="Quiet",
        evidence_id="evidence_quiet",
    )
    alarm_fact = Fact(
        fact_id="fact_hangar_condition_alarm",
        entity_id="location_hangar",
        attribute="condition",
        value="Alarm active",
        evidence_id="evidence_alarm",
    )
    database.store_fact(quiet_fact)
    database.store_fact(alarm_fact)
    database.store_timeline_event(
        event(
            event_id="event_quiet",
            chapter_id="chapter_001",
            scene_id="chapter_001_scene_001",
            evidence_id="evidence_quiet",
        )
    )
    database.store_timeline_event(
        event(
            event_id="event_alarm",
            chapter_id="chapter_001",
            scene_id="chapter_001_scene_002",
            evidence_id="evidence_alarm",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_quiet",
            fact_id="fact_hangar_condition_quiet",
            valid_from_event_id="event_quiet",
            valid_until_event_id="event_alarm",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_alarm",
            fact_id="fact_hangar_condition_alarm",
            valid_from_event_id="event_alarm",
        )
    )
    builder = WorldStateBuilder(database=database)

    first_scene = builder.build_entity_state_at_scene(
        entity_id="location_hangar",
        chapter_index=1,
        scene_index=1,
    )
    second_scene = builder.build_entity_state_at_scene(
        entity_id="location_hangar",
        chapter_index=1,
        scene_index=2,
    )

    assert tuple(fact.value for fact in first_scene.facts) == ("Quiet",)
    assert tuple(fact.value for fact in second_scene.facts) == ("Alarm active",)


def test_world_state_builder_filters_later_same_chapter_relationships() -> None:
    """Scene-position world state only includes relationships known by the scene."""
    database = build_database()
    database.store_chapter(
        Chapter(
            chapter_id="chapter_007",
            story_id="story_demo",
            chapter_index=7,
            title="Chapter 7",
        )
    )
    database.store_entity(
        Entity(
            entity_id="organization_silver_guard",
            entity_type="organization",
            display_name="Silver Guard",
        )
    )
    database.store_evidence(
        evidence(
            evidence_id="evidence_silver_guard",
            chapter_id="chapter_006",
            scene_id="chapter_006_scene_002",
            quote="The Silver Guard entered the fortress.",
        )
    )
    database.store_relationship(
        Relationship(
            relationship_id="relationship_silver_guard_enters_fortress",
            source_entity_id="organization_silver_guard",
            relationship_type="enters",
            target_entity_id="location_northern_fortress",
            evidence_id="evidence_silver_guard",
        )
    )
    builder = WorldStateBuilder(database=database)

    first_scene = builder.build_entity_state_at_scene(
        entity_id="location_northern_fortress",
        chapter_index=6,
        scene_index=1,
    )
    second_scene = builder.build_entity_state_at_scene(
        entity_id="location_northern_fortress",
        chapter_index=6,
        scene_index=2,
    )

    assert tuple(relationship.relationship_id for relationship in first_scene.relationships) == (
        "relationship_iron_guard_controls_fortress",
    )
    assert tuple(relationship.relationship_id for relationship in second_scene.relationships) == (
        "relationship_iron_guard_controls_fortress",
        "relationship_silver_guard_enters_fortress",
    )


def test_world_state_builder_rejects_unknown_entity() -> None:
    """Unknown world entities cannot get world state views."""
    builder = WorldStateBuilder(database=CanonDatabase())

    with pytest.raises(ValueError, match="Unknown world entity"):
        builder.build_entity_state(entity_id="location_missing", chapter_index=1)


def test_world_state_builder_rejects_invalid_entity_ids() -> None:
    """World state builders reject malformed selected entity IDs before lookup."""
    builder = WorldStateBuilder(database=build_database())

    with pytest.raises(ValueError, match="World entity ID is required"):
        builder.build_entity_state(entity_id=" ", chapter_index=1)

    with pytest.raises(ValueError, match="World entity ID is required"):
        builder.build_entity_state(entity_id=cast(Any, 42), chapter_index=1)

    with pytest.raises(ValueError, match="World entity ID cannot contain whitespace"):
        builder.build_state(
            entity_ids=("location northern fortress",),
            chapter_index=1,
        )


def test_world_state_builder_rejects_invalid_chapter_index() -> None:
    """World state lookups use one-based story positions."""
    builder = WorldStateBuilder(database=build_database())

    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        builder.build_entity_state(
            entity_id="location_northern_fortress",
            chapter_index=0,
        )

    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        builder.build_state(
            entity_ids=("location_northern_fortress",),
            chapter_index=0,
        )

    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        builder.build_entity_state(
            entity_id="location_northern_fortress",
            chapter_index=True,
        )

    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        builder.build_entity_state(
            entity_id="location_northern_fortress",
            chapter_index=cast(Any, "1"),
        )


def test_world_state_builder_rejects_invalid_scene_index() -> None:
    """Scene-position world state lookups use one-based scene positions."""
    builder = WorldStateBuilder(database=build_database())

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        builder.build_entity_state_at_scene(
            entity_id="location_northern_fortress",
            chapter_index=1,
            scene_index=0,
        )

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        builder.build_state_at_scene(
            entity_ids=("location_northern_fortress",),
            chapter_index=1,
            scene_index=0,
        )

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        builder.build_entity_state_at_scene(
            entity_id="location_northern_fortress",
            chapter_index=1,
            scene_index=True,
        )

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        builder.build_entity_state_at_scene(
            entity_id="location_northern_fortress",
            chapter_index=1,
            scene_index=cast(Any, "1"),
        )


def test_world_state_builder_rejects_character_entity() -> None:
    """World Engine does not build character-owned views."""
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
    builder = WorldStateBuilder(database=database)

    with pytest.raises(ValueError, match="not a world entity"):
        builder.build_entity_state(entity_id="character_mark", chapter_index=1)


def test_world_state_builder_sorts_relationships_by_id() -> None:
    """World relationships are returned deterministically."""
    database = build_database()
    database.store_entity(
        Entity(
            entity_id="organization_silver_guard",
            entity_type="organization",
            display_name="Silver Guard",
        )
    )
    database.store_relationship(
        Relationship(
            relationship_id="relationship_silver_guard_watches_fortress",
            source_entity_id="organization_silver_guard",
            relationship_type="watches",
            target_entity_id="location_northern_fortress",
            evidence_id="evidence_owner",
        )
    )
    builder = WorldStateBuilder(database=database)

    state = builder.build_entity_state(
        entity_id="location_northern_fortress",
        chapter_index=6,
    )

    assert tuple(relationship.relationship_id for relationship in state.relationships) == (
        "relationship_iron_guard_controls_fortress",
        "relationship_silver_guard_watches_fortress",
    )


def test_world_state_builder_rejects_relationship_with_unknown_endpoint() -> None:
    """Canon rejects world relationships with unknown endpoints before read layers."""
    database = build_database()

    with pytest.raises(ValueError, match="Unknown entity: organization_missing"):
        database.store_relationship(
            Relationship(
                relationship_id="relationship_missing_group_claims_fortress",
                source_entity_id="organization_missing",
                relationship_type="claims",
                target_entity_id="location_northern_fortress",
                evidence_id="evidence_owner",
            )
        )


def test_world_state_builder_uses_active_display_name_fact() -> None:
    """World state displays the active Canon name for the requested chapter."""
    database = build_database()
    database.store_evidence(
        evidence(
            evidence_id="evidence_name",
            chapter_id="chapter_001",
            scene_id="chapter_001_scene_001",
            quote="The fortress was called North Gate.",
        )
    )
    name_fact = Fact(
        fact_id="fact_fortress_name",
        entity_id="location_northern_fortress",
        attribute="display_name",
        value="North Gate",
        evidence_id="evidence_name",
    )
    database.store_fact(name_fact)
    database.store_timeline_event(
        event(
            event_id="event_name",
            chapter_id="chapter_001",
            scene_id="chapter_001_scene_001",
            evidence_id="evidence_name",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_name",
            fact_id="fact_fortress_name",
            valid_from_event_id="event_name",
        )
    )
    database.update_entity(
        Entity(
            entity_id="location_northern_fortress",
            entity_type="location",
            display_name="Northern Fortress",
        )
    )
    builder = WorldStateBuilder(database=database)

    state = builder.build_entity_state(
        entity_id="location_northern_fortress",
        chapter_index=1,
    )

    assert state.display_name == "North Gate"


def test_world_entity_fact_rejects_invalid_display_fields() -> None:
    """World facts reject malformed display values and source IDs."""
    with pytest.raises(ValueError, match="attribute cannot contain whitespace"):
        WorldEntityFact(
            attribute="damage level",
            value="Walls damaged",
            evidence=evidence("evidence_damage", "chapter_006", "scene_006", "Quote."),
            valid_from_chapter_id="chapter_006",
            valid_from_scene_id="scene_006",
        )

    with pytest.raises(ValueError, match="valid-from chapter ID cannot contain whitespace"):
        WorldEntityFact(
            attribute="damage",
            value="Walls damaged",
            evidence=evidence("evidence_damage", "chapter_006", "scene_006", "Quote."),
            valid_from_chapter_id="chapter 006",
            valid_from_scene_id="scene_006",
        )


def test_world_entity_fact_normalizes_display_values() -> None:
    """World facts normalize visible values for stable sheets."""
    fact = WorldEntityFact(
        attribute="damage",
        value=" Walls   damaged ",
        evidence=evidence("evidence_damage", "chapter_006", "scene_006", "Quote."),
        valid_from_chapter_id="chapter_006",
        valid_from_scene_id="scene_006",
    )

    assert fact.value == "Walls damaged"


def test_world_entity_state_rejects_invalid_identity() -> None:
    """World entity state requires valid identity and chapter values."""
    with pytest.raises(ValueError, match="World entity ID cannot contain whitespace"):
        WorldEntityState(
            entity_id="location fortress",
            entity_type="location",
            display_name="Northern Fortress",
            chapter_index=1,
        )

    with pytest.raises(ValueError, match="chapter index must be at least 1"):
        WorldEntityState(
            entity_id="location_northern_fortress",
            entity_type="location",
            display_name="Northern Fortress",
            chapter_index=0,
        )


def test_world_entity_state_normalizes_display_name() -> None:
    """World entity states normalize visible display names."""
    state = WorldEntityState(
        entity_id="location_northern_fortress",
        entity_type="location",
        display_name=" Northern   Fortress ",
        chapter_index=1,
    )

    assert state.display_name == "Northern Fortress"


def test_world_state_rejects_duplicate_entities() -> None:
    """World state views cannot contain duplicate entity entries."""
    entity = WorldEntityState(
        entity_id="location_northern_fortress",
        entity_type="location",
        display_name="Northern Fortress",
        chapter_index=1,
    )

    with pytest.raises(ValueError, match="duplicate entities"):
        WorldState(chapter_index=1, entities=(entity, entity))

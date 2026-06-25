"""Tests for Phase 1 core SceneSmith data models."""

from dataclasses import FrozenInstanceError

import pytest

from scenesmith.core import (
    Chapter,
    Character,
    Entity,
    Evidence,
    Fact,
    Item,
    Location,
    Relationship,
    Scene,
    SceneSnapshot,
    StateChange,
    Story,
    TimelineEvent,
)


def test_story_contains_ordered_chapters_and_scenes() -> None:
    """Story, Chapter, and Scene models preserve source structure references."""
    scene = Scene(
        scene_id="scene_001_001",
        chapter_id="chapter_001",
        scene_index=1,
        title="Opening Scene",
        paragraphs=("Paragraph one.", "Paragraph two."),
    )
    chapter = Chapter(
        chapter_id="chapter_001",
        story_id="story_demo",
        chapter_index=1,
        title="Chapter One",
        scenes=(scene,),
    )
    story = Story(
        story_id="story_demo",
        title="Demo Story",
        chapters=(chapter,),
    )

    assert story.chapters[0].scenes[0].paragraphs == (
        "Paragraph one.",
        "Paragraph two.",
    )


def test_entity_specializations_wrap_permanent_entities() -> None:
    """Character, Location, and Item models wrap permanent entity records."""
    character_entity = Entity(
        entity_id="character_mark",
        entity_type="character",
        display_name="Mark",
    )
    location_entity = Entity(
        entity_id="location_bridge",
        entity_type="location",
        display_name="Rain Bridge",
    )
    item_entity = Entity(
        entity_id="item_iron_sword",
        entity_type="item",
        display_name="Iron Sword",
    )

    assert Character(entity=character_entity).entity.entity_id == "character_mark"
    assert Location(entity=location_entity).entity.entity_id == "location_bridge"
    assert Item(entity=item_entity).entity.entity_id == "item_iron_sword"


def test_fact_and_relationship_reference_evidence() -> None:
    """Facts and relationships point back to evidence anchors."""
    evidence = Evidence(
        evidence_id="evidence_001",
        source_id="source_001",
        chapter_id="chapter_001",
        scene_id="scene_001_001",
        paragraph_index=3,
        sentence_index=2,
        quote="Mark lifted the iron sword.",
        confidence=1.0,
    )
    fact = Fact(
        fact_id="fact_mark_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence_id=evidence.evidence_id,
    )
    relationship = Relationship(
        relationship_id="relationship_mark_owns_sword",
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="item_iron_sword",
        evidence_id=evidence.evidence_id,
    )

    assert fact.evidence_id == "evidence_001"
    assert relationship.evidence_id == "evidence_001"


def test_timeline_event_and_state_change_define_validity() -> None:
    """Timeline events and state changes connect facts to validity windows."""
    event = TimelineEvent(
        event_id="event_mark_buys_sword",
        chapter_id="chapter_008",
        scene_id="scene_008_002",
        description="Mark buys the iron sword.",
        evidence_id="evidence_008_002",
    )
    state_change = StateChange(
        state_change_id="state_mark_weapon_sword",
        fact_id="fact_mark_weapon",
        valid_from_event_id=event.event_id,
        valid_until_event_id=None,
    )

    assert state_change.valid_from_event_id == "event_mark_buys_sword"
    assert state_change.valid_until_event_id is None


def test_scene_snapshot_references_reconstructed_scene_state() -> None:
    """Scene snapshots reference active scene entities, facts, relationships, and events."""
    snapshot = SceneSnapshot(
        snapshot_id="snapshot_scene_014_001",
        scene_id="scene_014_001",
        character_ids=("character_mark",),
        location_ids=("location_bridge",),
        fact_ids=("fact_mark_weapon",),
        relationship_ids=("relationship_mark_owns_sword",),
        event_ids=("event_bridge_crossing",),
    )

    assert snapshot.character_ids == ("character_mark",)
    assert snapshot.fact_ids == ("fact_mark_weapon",)


def test_core_models_are_immutable_data() -> None:
    """Core data models are frozen and do not expose mutation behavior."""
    entity = Entity(
        entity_id="character_mark",
        entity_type="character",
        display_name="Mark",
    )

    with pytest.raises(FrozenInstanceError):
        entity.display_name = "Sir Mark"  # type: ignore[misc]

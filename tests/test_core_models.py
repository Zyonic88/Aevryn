"""Tests for Phase 1 core SceneSmith data models."""

from dataclasses import FrozenInstanceError
from typing import Any, cast

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


def test_story_rejects_mismatched_child_chapter() -> None:
    """Stories only contain chapters that reference the same story ID."""
    chapter = Chapter(
        chapter_id="chapter_001",
        story_id="other_story",
        chapter_index=1,
        title="Chapter One",
    )

    with pytest.raises(ValueError, match="reference the story ID"):
        Story(
            story_id="story_demo",
            title="Demo Story",
            chapters=(chapter,),
        )


def test_story_rejects_duplicate_chapter_indexes() -> None:
    """Stories cannot contain duplicate chapter positions."""
    first = Chapter(
        chapter_id="chapter_001",
        story_id="story_demo",
        chapter_index=1,
        title="Chapter One",
    )
    second = Chapter(
        chapter_id="chapter_duplicate",
        story_id="story_demo",
        chapter_index=1,
        title="Duplicate Chapter",
    )

    with pytest.raises(ValueError, match="duplicate chapter indexes"):
        Story(
            story_id="story_demo",
            title="Demo Story",
            chapters=(first, second),
        )


def test_story_rejects_out_of_order_chapter_indexes() -> None:
    """Stories preserve imported chapter order explicitly."""
    first = Chapter(
        chapter_id="chapter_001",
        story_id="story_demo",
        chapter_index=1,
        title="Chapter One",
    )
    second = Chapter(
        chapter_id="chapter_002",
        story_id="story_demo",
        chapter_index=2,
        title="Chapter Two",
    )

    with pytest.raises(ValueError, match="increasing order"):
        Story(
            story_id="story_demo",
            title="Demo Story",
            chapters=(second, first),
        )


def test_chapter_rejects_mismatched_child_scene() -> None:
    """Chapters only contain scenes that reference the chapter ID."""
    scene = Scene(
        scene_id="scene_001_001",
        chapter_id="other_chapter",
        scene_index=1,
        title="Opening Scene",
    )

    with pytest.raises(ValueError, match="reference the chapter ID"):
        Chapter(
            chapter_id="chapter_001",
            story_id="story_demo",
            chapter_index=1,
            title="Chapter One",
            scenes=(scene,),
        )


def test_chapter_rejects_out_of_order_scene_indexes() -> None:
    """Chapters preserve imported scene order explicitly."""
    first = Scene(
        scene_id="scene_001_001",
        chapter_id="chapter_001",
        scene_index=1,
        title="Opening Scene",
    )
    second = Scene(
        scene_id="scene_001_002",
        chapter_id="chapter_001",
        scene_index=2,
        title="Second Scene",
    )

    with pytest.raises(ValueError, match="increasing order"):
        Chapter(
            chapter_id="chapter_001",
            story_id="story_demo",
            chapter_index=1,
            title="Chapter One",
            scenes=(second, first),
        )


def test_scene_rejects_blank_paragraphs() -> None:
    """Scene paragraphs are source text and cannot be blank."""
    with pytest.raises(ValueError, match="Scene paragraph is required"):
        Scene(
            scene_id="scene_001_001",
            chapter_id="chapter_001",
            scene_index=1,
            title="Opening Scene",
            paragraphs=(" ",),
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


def test_entity_specializations_reject_wrong_entity_type() -> None:
    """Specialized core wrappers enforce their entity category."""
    location_entity = Entity(
        entity_id="location_bridge",
        entity_type="location",
        display_name="Rain Bridge",
    )
    character_entity = Entity(
        entity_id="character_mark",
        entity_type="character",
        display_name="Mark",
    )

    with pytest.raises(ValueError, match="character entities"):
        Character(entity=location_entity)

    with pytest.raises(ValueError, match="location entities"):
        Location(entity=character_entity)


def test_item_specialization_accepts_item_like_entity_types() -> None:
    """Item wrappers support item, weapon, and armor entities."""
    weapon_entity = Entity(
        entity_id="weapon_iron_sword",
        entity_type="weapon",
        display_name="Iron Sword",
    )
    armor_entity = Entity(
        entity_id="armor_steel_plate",
        entity_type="armor",
        display_name="Steel Plate",
    )

    assert Item(entity=weapon_entity).entity.entity_id == "weapon_iron_sword"
    assert Item(entity=armor_entity).entity.entity_id == "armor_steel_plate"


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


@pytest.mark.parametrize(
    ("field_name", "values", "message"),
    (
        ("character_ids", ("character_mark", "character_mark"), "character IDs"),
        ("location_ids", ("location_bridge", "location_bridge"), "location IDs"),
        ("fact_ids", ("fact_mark_weapon", "fact_mark_weapon"), "fact IDs"),
        (
            "relationship_ids",
            ("relationship_mark_owns_sword", "relationship_mark_owns_sword"),
            "relationship IDs",
        ),
        ("event_ids", ("event_bridge_crossing", "event_bridge_crossing"), "event IDs"),
    ),
)
def test_scene_snapshot_rejects_duplicate_reference_ids(
    field_name: str,
    values: tuple[str, str],
    message: str,
) -> None:
    """Scene snapshots cannot contain duplicate reference IDs."""
    with pytest.raises(ValueError, match=message):
        if field_name == "character_ids":
            SceneSnapshot(
                snapshot_id="snapshot_scene_014_001",
                scene_id="scene_014_001",
                character_ids=values,
            )
        elif field_name == "location_ids":
            SceneSnapshot(
                snapshot_id="snapshot_scene_014_001",
                scene_id="scene_014_001",
                location_ids=values,
            )
        elif field_name == "fact_ids":
            SceneSnapshot(
                snapshot_id="snapshot_scene_014_001",
                scene_id="scene_014_001",
                fact_ids=values,
            )
        elif field_name == "relationship_ids":
            SceneSnapshot(
                snapshot_id="snapshot_scene_014_001",
                scene_id="scene_014_001",
                relationship_ids=values,
            )
        else:
            SceneSnapshot(
                snapshot_id="snapshot_scene_014_001",
                scene_id="scene_014_001",
                event_ids=values,
            )


def test_core_models_are_immutable_data() -> None:
    """Core data models are frozen and do not expose mutation behavior."""
    entity = Entity(
        entity_id="character_mark",
        entity_type="character",
        display_name="Mark",
    )

    with pytest.raises(FrozenInstanceError):
        entity.display_name = "Sir Mark"  # type: ignore[misc]


def test_core_models_reject_blank_required_text() -> None:
    """Core models reject missing human-readable values."""
    with pytest.raises(ValueError, match="Entity display name is required"):
        Entity(
            entity_id="character_mark",
            entity_type="character",
            display_name=" ",
        )

    with pytest.raises(ValueError, match="Entity display name is required"):
        Entity(
            entity_id="character_mark",
            entity_type="character",
            display_name=cast(Any, 42),
        )


def test_core_models_reject_machine_token_whitespace() -> None:
    """Core model IDs and machine labels are whitespace-free tokens."""
    with pytest.raises(ValueError, match="Fact attribute cannot contain whitespace"):
        Fact(
            fact_id="fact_mark_weapon",
            entity_id="character_mark",
            attribute="current weapon",
            value="Iron Sword",
            evidence_id="evidence_001",
        )


def test_core_models_reject_invalid_source_indexes_and_confidence() -> None:
    """Evidence source positions and confidence are validated at construction."""
    with pytest.raises(ValueError, match="Evidence paragraph index must be at least 1"):
        Evidence(
            evidence_id="evidence_001",
            source_id="source_001",
            chapter_id="chapter_001",
            scene_id="scene_001_001",
            paragraph_index=0,
            sentence_index=1,
            quote="Mark lifted the iron sword.",
            confidence=1.0,
        )

    with pytest.raises(ValueError, match="Evidence sentence index must be at least 1"):
        Evidence(
            evidence_id="evidence_001",
            source_id="source_001",
            chapter_id="chapter_001",
            scene_id="scene_001_001",
            paragraph_index=1,
            sentence_index=True,
            quote="Mark lifted the iron sword.",
            confidence=1.0,
        )

    with pytest.raises(ValueError, match="Evidence confidence"):
        Evidence(
            evidence_id="evidence_001",
            source_id="source_001",
            chapter_id="chapter_001",
            scene_id="scene_001_001",
            paragraph_index=1,
            sentence_index=1,
            quote="Mark lifted the iron sword.",
            confidence=1.5,
        )


def test_core_evidence_rejects_boolean_confidence() -> None:
    """Evidence confidence must be numeric and not boolean."""
    with pytest.raises(ValueError, match="Evidence confidence"):
        Evidence(
            evidence_id="evidence_001",
            source_id="source_001",
            chapter_id="chapter_001",
            scene_id="scene_001_001",
            paragraph_index=1,
            sentence_index=1,
            quote="Mark lifted the iron sword.",
            confidence=True,
        )


def test_core_evidence_rejects_non_numeric_indexes_and_confidence() -> None:
    """Evidence positions and confidence reject non-numeric runtime values."""
    with pytest.raises(ValueError, match="Evidence paragraph index"):
        Evidence(
            evidence_id="evidence_001",
            source_id="source_001",
            chapter_id="chapter_001",
            scene_id="scene_001_001",
            paragraph_index=cast(Any, "1"),
            sentence_index=1,
            quote="Mark lifted the iron sword.",
            confidence=1.0,
        )

    with pytest.raises(ValueError, match="Evidence confidence"):
        Evidence(
            evidence_id="evidence_001",
            source_id="source_001",
            chapter_id="chapter_001",
            scene_id="scene_001_001",
            paragraph_index=1,
            sentence_index=1,
            quote="Mark lifted the iron sword.",
            confidence=cast(Any, "high"),
        )

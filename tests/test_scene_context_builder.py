"""Tests for Phase 7 Scene Context."""

import pytest

from scenesmith import (
    CanonDatabase,
    CharacterCardBuilder,
    ImportedSource,
    SceneContextBuilder,
    StoryImporter,
)
from scenesmith.core import (
    Character,
    Entity,
    Evidence,
    Fact,
    Relationship,
    StateChange,
    TimelineEvent,
)


def evidence(evidence_id: str, chapter_id: str, scene_id: str, quote: str) -> Evidence:
    """Create evidence for scene context tests."""
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
    """Create an event for scene context tests."""
    return TimelineEvent(
        event_id=event_id,
        chapter_id=chapter_id,
        scene_id=scene_id,
        description=event_id,
        evidence_id=evidence_id,
    )


def build_imported_source() -> ImportedSource:
    """Build imported source for scene context tests."""
    return StoryImporter().import_text(
        source_id="source_demo",
        title="Demo Story",
        text="""Chapter 1
Mark carried a rusty dagger.

Chapter 2
Mark bought an iron sword.""",
    )


def build_database() -> CanonDatabase:
    """Build Canon Database with accepted character state."""
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
    database.store_chapter(build_imported_source().story.chapters[0])
    database.store_chapter(build_imported_source().story.chapters[1])
    database.store_evidence(
        evidence(
            evidence_id="evidence_001",
            chapter_id="source_demo_chapter_001",
            scene_id="source_demo_chapter_001_scene_001",
            quote="Mark carried a rusty dagger.",
        )
    )
    database.store_evidence(
        evidence(
            evidence_id="evidence_008",
            chapter_id="source_demo_chapter_002",
            scene_id="source_demo_chapter_002_scene_001",
            quote="Mark bought an iron sword.",
        )
    )
    database.store_evidence(
        evidence(
            evidence_id="evidence_relationship",
            chapter_id="source_demo_chapter_002",
            scene_id="source_demo_chapter_002_scene_001",
            quote="Mark bought an iron sword.",
        )
    )
    dagger = Fact(
        fact_id="fact_001_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence_id="evidence_001",
    )
    sword = Fact(
        fact_id="fact_008_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence_id="evidence_008",
    )
    database.store_fact(dagger)
    database.store_fact(sword)
    database.store_relationship(
        Relationship(
            relationship_id="relationship_mark_owns_sword",
            source_entity_id="character_mark",
            relationship_type="owns",
            target_entity_id="item_iron_sword",
            evidence_id="evidence_relationship",
        )
    )
    database.store_timeline_event(
        event(
            event_id="event_001_weapon",
            chapter_id="source_demo_chapter_001",
            scene_id="source_demo_chapter_001_scene_001",
            evidence_id="evidence_001",
        )
    )
    database.store_timeline_event(
        event(
            event_id="event_008_weapon",
            chapter_id="source_demo_chapter_002",
            scene_id="source_demo_chapter_002_scene_001",
            evidence_id="evidence_008",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_001_weapon",
            fact_id="fact_001_weapon",
            valid_from_event_id="event_001_weapon",
            valid_until_event_id="event_008_weapon",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_008_weapon",
            fact_id="fact_008_weapon",
            valid_from_event_id="event_008_weapon",
        )
    )
    return database


def test_scene_context_builder_reconstructs_scene_state() -> None:
    """Scene context includes character cards, active facts, and relationships."""
    imported_source = build_imported_source()
    database = build_database()
    builder = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    )

    context = builder.build_context(
        imported_source=imported_source,
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark",),
    )

    assert context.scene.scene_id == "source_demo_chapter_002_scene_001"
    assert context.character_cards[0].facts[0].value == "Iron Sword"
    assert context.active_facts[0].fact_id == "fact_008_weapon"
    assert context.relationships[0].relationship_id == "relationship_mark_owns_sword"
    assert context.snapshot.character_ids == ("character_mark",)
    assert context.snapshot.fact_ids == ("fact_008_weapon",)


def test_scene_context_builder_dedupes_shared_relationships() -> None:
    """Scene context does not duplicate relationships shared by selected entities."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_character(
        Character(
            entity=Entity(
                entity_id="character_luna",
                entity_type="character",
                display_name="Luna",
            )
        )
    )
    database.store_relationship(
        Relationship(
            relationship_id="relationship_mark_travels_with_luna",
            source_entity_id="character_mark",
            relationship_type="travels_with",
            target_entity_id="character_luna",
            evidence_id="evidence_relationship",
        )
    )
    builder = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    )

    context = builder.build_context(
        imported_source=imported_source,
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark", "character_luna"),
    )

    assert tuple(
        relationship.relationship_id for relationship in context.relationships
    ) == (
        "relationship_mark_owns_sword",
        "relationship_mark_travels_with_luna",
    )


def test_scene_context_builder_dedupes_duplicate_character_ids() -> None:
    """Scene context treats repeated character IDs as one scene participant."""
    imported_source = build_imported_source()
    database = build_database()
    builder = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    )

    context = builder.build_context(
        imported_source=imported_source,
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark", "character_mark"),
    )

    assert len(context.character_cards) == 1
    assert context.snapshot.character_ids == ("character_mark",)
    assert context.snapshot.fact_ids == ("fact_008_weapon",)


def test_scene_context_builder_sorts_relationships_by_id() -> None:
    """Scene relationships are returned deterministically."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_relationship(
        Relationship(
            relationship_id="relationship_aaa_mark_knows_luna",
            source_entity_id="character_mark",
            relationship_type="knows",
            target_entity_id="character_luna",
            evidence_id="evidence_relationship",
        )
    )
    builder = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    )

    context = builder.build_context(
        imported_source=imported_source,
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark",),
    )

    assert tuple(
        relationship.relationship_id for relationship in context.relationships
    ) == (
        "relationship_aaa_mark_knows_luna",
        "relationship_mark_owns_sword",
    )


def test_scene_context_builder_includes_related_location_ids() -> None:
    """Scene snapshots include location IDs discovered from relationships."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_entity(
        Entity(
            entity_id="location_academy",
            entity_type="location",
            display_name="Academy",
        )
    )
    database.store_relationship(
        Relationship(
            relationship_id="relationship_mark_located_at_academy",
            source_entity_id="character_mark",
            relationship_type="located_at",
            target_entity_id="location_academy",
            evidence_id="evidence_relationship",
        )
    )
    builder = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    )

    context = builder.build_context(
        imported_source=imported_source,
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark",),
    )

    assert context.snapshot.location_ids == ("location_academy",)


def test_scene_context_builder_rejects_unknown_scene() -> None:
    """Scene context cannot be built for scenes Story Import did not create."""
    imported_source = build_imported_source()
    database = build_database()
    builder = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    )

    with pytest.raises(ValueError, match="Unknown scene"):
        builder.build_context(
            imported_source=imported_source,
            scene_id="missing_scene",
            character_ids=("character_mark",),
        )

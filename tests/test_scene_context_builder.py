"""Tests for Phase 7 Scene Context."""

from dataclasses import replace

import pytest

from aevryn import (
    CanonDatabase,
    CanonSceneContext,
    CharacterCardBuilder,
    ImportedSource,
    SceneContextBuilder,
    StoryImporter,
)
from aevryn.core import (
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


def build_two_scene_imported_source() -> ImportedSource:
    """Build one chapter with two explicit scenes."""
    return StoryImporter().import_text(
        source_id="source_demo",
        title="Demo Story",
        text="""Chapter 1
Mark was calm.

---

Mark became alarmed in the hangar.""",
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
    database.store_entity(
        Entity(
            entity_id="location_hangar",
            entity_type="location",
            display_name="Hangar",
        )
    )
    database.store_entity(
        Entity(
            entity_id="item_iron_sword",
            entity_type="item",
            display_name="Iron Sword",
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


def test_scene_context_builder_includes_related_world_entity_facts() -> None:
    """Scene context includes accepted facts for connected world entities."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_fact(
        Fact(
            fact_id="fact_sword_visual_design",
            entity_id="item_iron_sword",
            attribute="visual_design",
            value="Chipped iron blade",
            evidence_id="evidence_relationship",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_sword_visual_design",
            fact_id="fact_sword_visual_design",
            valid_from_event_id="event_008_weapon",
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

    assert tuple(fact.fact_id for fact in context.active_facts) == (
        "fact_008_weapon",
        "fact_sword_visual_design",
    )
    assert context.snapshot.fact_ids == (
        "fact_008_weapon",
        "fact_sword_visual_design",
    )


def test_scene_context_builder_does_not_leak_future_relationships() -> None:
    """Scene context only includes relationships known by the requested chapter."""
    imported_source = build_imported_source()
    database = build_database()
    builder = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    )

    context = builder.build_context(
        imported_source=imported_source,
        scene_id="source_demo_chapter_001_scene_001",
        character_ids=("character_mark",),
    )

    assert context.relationships == ()
    assert context.snapshot.relationship_ids == ()


def test_scene_context_builder_does_not_leak_later_same_chapter_state() -> None:
    """Scene context reconstructs state at the requested scene, not whole chapter."""
    imported_source = build_two_scene_imported_source()
    first_scene = imported_source.story.chapters[0].scenes[0]
    second_scene = imported_source.story.chapters[0].scenes[1]
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
    database.store_entity(
        Entity(
            entity_id="location_hangar",
            entity_type="location",
            display_name="Hangar",
        )
    )
    database.store_chapter(imported_source.story.chapters[0])
    database.store_evidence(
        evidence(
            evidence_id="evidence_scene_001",
            chapter_id=first_scene.chapter_id,
            scene_id=first_scene.scene_id,
            quote="Mark was calm.",
        )
    )
    database.store_evidence(
        evidence(
            evidence_id="evidence_scene_002",
            chapter_id=second_scene.chapter_id,
            scene_id=second_scene.scene_id,
            quote="Mark became alarmed in the hangar.",
        )
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
    database.store_relationship(
        Relationship(
            relationship_id="relationship_mark_observes_hangar",
            source_entity_id="character_mark",
            relationship_type="observes",
            target_entity_id="location_hangar",
            evidence_id="evidence_scene_002",
        )
    )
    database.store_timeline_event(
        event(
            event_id="event_calm",
            chapter_id=first_scene.chapter_id,
            scene_id=first_scene.scene_id,
            evidence_id="evidence_scene_001",
        )
    )
    database.store_timeline_event(
        event(
            event_id="event_alarmed",
            chapter_id=second_scene.chapter_id,
            scene_id=second_scene.scene_id,
            evidence_id="evidence_scene_002",
        )
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
    builder = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    )

    first_context = builder.build_context(
        imported_source=imported_source,
        scene_id=first_scene.scene_id,
        character_ids=("character_mark",),
    )
    second_context = builder.build_context(
        imported_source=imported_source,
        scene_id=second_scene.scene_id,
        character_ids=("character_mark",),
    )

    assert tuple(fact.value for fact in first_context.active_facts) == ("Calm",)
    assert tuple(fact.value for fact in first_context.character_cards[0].facts) == (
        "Calm",
    )
    assert first_context.relationships == ()
    assert tuple(fact.value for fact in second_context.active_facts) == ("Alarmed",)
    assert tuple(fact.value for fact in second_context.character_cards[0].facts) == (
        "Alarmed",
    )
    assert tuple(
        relationship.relationship_id for relationship in second_context.relationships
    ) == ("relationship_mark_observes_hangar",)


def test_scene_context_builder_filters_stale_background_facts() -> None:
    """Scene context omits old non-scene facts from later scene views."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_fact(
        Fact(
            fact_id="fact_mark_school_year",
            entity_id="character_mark",
            attribute="school_year",
            value="Third Year",
            evidence_id="evidence_001",
        )
    )
    database.store_timeline_event(
        event(
            event_id="event_001_school_year",
            chapter_id="source_demo_chapter_001",
            scene_id="source_demo_chapter_001_scene_001",
            evidence_id="evidence_001",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_001_school_year",
            fact_id="fact_mark_school_year",
            valid_from_event_id="event_001_school_year",
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

    assert tuple(fact.fact_id for fact in context.active_facts) == ("fact_008_weapon",)


def test_scene_context_builder_keeps_persistent_scene_facts() -> None:
    """Scene context keeps old facts needed to reconstruct the character."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_fact(
        Fact(
            fact_id="fact_mark_status_injured",
            entity_id="character_mark",
            attribute="status",
            value="Injured",
            evidence_id="evidence_001",
        )
    )
    database.store_timeline_event(
        event(
            event_id="event_001_status",
            chapter_id="source_demo_chapter_001",
            scene_id="source_demo_chapter_001_scene_001",
            evidence_id="evidence_001",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_001_status",
            fact_id="fact_mark_status_injured",
            valid_from_event_id="event_001_status",
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

    assert tuple(fact.fact_id for fact in context.active_facts) == (
        "fact_008_weapon",
        "fact_mark_status_injured",
    )


def test_scene_context_builder_keeps_generic_rule_facts() -> None:
    """Scene context relevance is generic, not tied to one story domain."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_fact(
        Fact(
            fact_id="fact_mark_ritual_rule",
            entity_id="character_mark",
            attribute="ritual_rule",
            value="Must enter the kitchen before sunrise",
            evidence_id="evidence_001",
        )
    )
    database.store_timeline_event(
        event(
            event_id="event_001_ritual_rule",
            chapter_id="source_demo_chapter_001",
            scene_id="source_demo_chapter_001_scene_001",
            evidence_id="evidence_001",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_001_ritual_rule",
            fact_id="fact_mark_ritual_rule",
            valid_from_event_id="event_001_ritual_rule",
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

    assert tuple(fact.fact_id for fact in context.active_facts) == (
        "fact_008_weapon",
        "fact_mark_ritual_rule",
    )


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


def test_scene_context_rejects_snapshot_character_mismatch() -> None:
    """Scene context snapshots must agree with character cards."""
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

    with pytest.raises(ValueError, match="character IDs"):
        CanonSceneContext(
            snapshot=replace(context.snapshot, character_ids=("character_luna",)),
            scene=context.scene,
            character_cards=context.character_cards,
            active_facts=context.active_facts,
            relationships=context.relationships,
        )


def test_scene_context_rejects_snapshot_fact_mismatch() -> None:
    """Scene context snapshots must agree with active facts."""
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

    with pytest.raises(ValueError, match="fact IDs"):
        CanonSceneContext(
            snapshot=replace(context.snapshot, fact_ids=("fact_missing",)),
            scene=context.scene,
            character_cards=context.character_cards,
            active_facts=context.active_facts,
            relationships=context.relationships,
        )


def test_scene_context_builder_sorts_relationships_by_id() -> None:
    """Scene relationships are returned deterministically."""
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


def test_scene_context_builder_does_not_leak_future_location_ids() -> None:
    """Future location relationships cannot appear in earlier scene snapshots."""
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
        scene_id="source_demo_chapter_001_scene_001",
        character_ids=("character_mark",),
    )

    assert context.snapshot.location_ids == ()


def test_scene_context_builder_filters_stale_transient_relationships() -> None:
    """Scene context omits old action relationships after their chapter."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_entity(
        Entity(
            entity_id="location_market",
            entity_type="location",
            display_name="Market",
        )
    )
    database.store_evidence(
        evidence(
            evidence_id="evidence_observes",
            chapter_id="source_demo_chapter_001",
            scene_id="source_demo_chapter_001_scene_001",
            quote="Mark observed the market.",
        )
    )
    database.store_relationship(
        Relationship(
            relationship_id="relationship_mark_observes_market",
            source_entity_id="character_mark",
            relationship_type="observes",
            target_entity_id="location_market",
            evidence_id="evidence_observes",
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
    ) == ("relationship_mark_owns_sword",)


def test_scene_context_builder_filters_stale_background_relationships() -> None:
    """Old background relationships are omitted when target is absent."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_entity(
        Entity(
            entity_id="item_rusty_dagger",
            entity_type="item",
            display_name="Rusty Dagger",
        )
    )
    database.store_relationship(
        Relationship(
            relationship_id="relationship_mark_owns_dagger",
            source_entity_id="character_mark",
            relationship_type="owns",
            target_entity_id="item_rusty_dagger",
            evidence_id="evidence_001",
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
    ) == ("relationship_mark_owns_sword",)


def test_scene_context_builder_keeps_relationship_between_present_characters() -> None:
    """Background relationships between present characters remain relevant."""
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
    database.store_evidence(
        evidence(
            evidence_id="evidence_friend",
            chapter_id="source_demo_chapter_001",
            scene_id="source_demo_chapter_001_scene_001",
            quote="Luna was Mark's friend.",
        )
    )
    database.store_relationship(
        Relationship(
            relationship_id="relationship_luna_friend_of_mark",
            source_entity_id="character_luna",
            relationship_type="friend_of",
            target_entity_id="character_mark",
            evidence_id="evidence_friend",
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

    assert "relationship_luna_friend_of_mark" in tuple(
        relationship.relationship_id for relationship in context.relationships
    )


def test_scene_context_builder_keeps_current_chapter_transient_relationships() -> None:
    """Scene context includes action relationships in their evidence chapter."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_relationship(
        Relationship(
            relationship_id="relationship_mark_uses_sword",
            source_entity_id="character_mark",
            relationship_type="uses",
            target_entity_id="item_iron_sword",
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
        "relationship_mark_owns_sword",
        "relationship_mark_uses_sword",
    )


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

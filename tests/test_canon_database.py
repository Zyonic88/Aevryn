"""Tests for Phase 2 Canon Database storage."""

import pytest

from scenesmith import CanonDatabase
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


def character(name: str) -> Character:
    """Create a character core model."""
    return Character(
        entity=Entity(
            entity_id="character_mark",
            entity_type="character",
            display_name=name,
        )
    )


def chapter(chapter_id: str, chapter_index: int) -> Chapter:
    """Create a chapter core model."""
    return Chapter(
        chapter_id=chapter_id,
        story_id="story_demo",
        chapter_index=chapter_index,
        title=f"Chapter {chapter_index}",
    )


def evidence(evidence_id: str, chapter_id: str, scene_id: str) -> Evidence:
    """Create an evidence core model."""
    return Evidence(
        evidence_id=evidence_id,
        source_id="source_demo",
        chapter_id=chapter_id,
        scene_id=scene_id,
        paragraph_index=1,
        sentence_index=1,
        quote="Evidence quote.",
        confidence=1.0,
    )


def event(event_id: str, chapter_id: str, evidence_id: str) -> TimelineEvent:
    """Create a timeline event core model."""
    return TimelineEvent(
        event_id=event_id,
        chapter_id=chapter_id,
        scene_id=f"scene_{chapter_id}",
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


def test_store_relationship_dedupes_identical_semantic_relationships() -> None:
    """Canon Database keeps one semantic relationship connection."""
    database = CanonDatabase()
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


def test_retrieve_state_at_chapter_uses_validity_windows() -> None:
    """Canon Database retrieves entity state valid at a chapter."""
    database = CanonDatabase()
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
    database.store_timeline_event(event("event_dagger", "chapter_001", "evidence_001"))
    database.store_timeline_event(event("event_sword", "chapter_008", "evidence_008"))
    database.store_timeline_event(event("event_lost_sword", "chapter_020", "evidence_020"))
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


def test_fact_history_uses_timeline_order_before_fact_id_order() -> None:
    """Fact history follows story chronology rather than lexicographic IDs."""
    database = CanonDatabase()
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

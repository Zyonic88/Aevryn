"""Tests for Phase 5 Canon Updating."""

import logging

import pytest

from scenesmith import CanonDatabase, CanonUpdater
from scenesmith.extraction import (
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractedStateChange,
    ExtractionResult,
)
from scenesmith.importing import EvidenceAnchor


def anchor() -> EvidenceAnchor:
    """Create an evidence anchor for update tests."""
    return EvidenceAnchor(
        anchor_id="source_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
        source_id="source_demo",
        chapter_id="source_demo_chapter_001",
        scene_id="source_demo_chapter_001_scene_001",
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        sentence_id="source_demo_chapter_001_scene_001_paragraph_001_sentence_001",
        paragraph_index=1,
        sentence_index=1,
        quote="Mark lifted the iron sword.",
    )


def accepted_entity(name: str = "Mark") -> ExtractedEntity:
    """Create an accepted character candidate."""
    return ExtractedEntity(
        entity_id="character_mark",
        entity_type="character",
        display_name=name,
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.95,
    )


def accepted_item() -> ExtractedEntity:
    """Create an accepted item candidate."""
    return ExtractedEntity(
        entity_id="item_iron_sword",
        entity_type="item",
        display_name="Iron Sword",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.9,
    )


def extraction_result(
    *,
    entities: tuple[ExtractedEntity, ...] = (),
    facts: tuple[ExtractedFact, ...] = (),
    relationships: tuple[ExtractedRelationship, ...] = (),
    state_changes: tuple[ExtractedStateChange, ...] = (),
) -> ExtractionResult:
    """Create an extraction result for update tests."""
    return ExtractionResult(
        scene_id=anchor().scene_id,
        entities=entities,
        facts=facts,
        relationships=relationships,
        state_changes=state_changes,
    )


def test_canon_updater_accepts_entity_and_stores_character_fact() -> None:
    """Accepted extraction candidates become evidence-backed canon records."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)

    summary = updater.apply_extraction_result(
        result=extraction_result(entities=(accepted_entity(),)),
        anchors=(anchor(),),
    )

    character = database.retrieve_character("character_mark")

    assert summary.accepted_entities == ("character_mark",)
    assert character is not None
    assert character.entity.display_name == "Mark"
    assert database.retrieve_state_at_chapter("character_mark", 1)[0].value == "Mark"


def test_canon_updater_versions_existing_character() -> None:
    """Accepted updates preserve previous character versions."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    updater.apply_extraction_result(
        result=extraction_result(entities=(accepted_entity("Mark"),)),
        anchors=(anchor(),),
    )

    updater.apply_extraction_result(
        result=extraction_result(entities=(accepted_entity("Sir Mark"),)),
        anchors=(anchor(),),
    )

    versions = database.version_character("character_mark")

    assert len(versions) == 2
    assert versions[0].entity.display_name == "Mark"
    assert versions[1].entity.display_name == "Sir Mark"


def test_canon_updater_does_not_version_identical_character() -> None:
    """Repeated identical entity candidates do not create noisy versions."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    updater.apply_extraction_result(
        result=extraction_result(entities=(accepted_entity("Mark"),)),
        anchors=(anchor(),),
    )

    updater.apply_extraction_result(
        result=extraction_result(entities=(accepted_entity("Mark"),)),
        anchors=(anchor(),),
    )

    assert len(database.version_character("character_mark")) == 1


def test_canon_updater_closes_previous_state_when_fact_changes() -> None:
    """Accepted updates keep only the latest fact active after the change."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    updater.apply_extraction_result(
        result=extraction_result(entities=(accepted_entity("Mark"),)),
        anchors=(anchor(),),
    )
    later_anchor = EvidenceAnchor(
        anchor_id="source_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor",
        source_id="source_demo",
        chapter_id="source_demo_chapter_002",
        scene_id="source_demo_chapter_002_scene_001",
        paragraph_id="source_demo_chapter_002_scene_001_paragraph_001",
        sentence_id="source_demo_chapter_002_scene_001_paragraph_001_sentence_001",
        paragraph_index=1,
        sentence_index=1,
        quote="Sir Mark entered the hall.",
    )
    later_entity = ExtractedEntity(
        entity_id="character_mark",
        entity_type="character",
        display_name="Sir Mark",
        evidence_anchor_id=later_anchor.anchor_id,
        confidence=0.95,
    )

    updater.apply_extraction_result(
        result=ExtractionResult(
            scene_id=later_anchor.scene_id,
            entities=(later_entity,),
        ),
        anchors=(later_anchor,),
    )

    chapter_one_state = database.retrieve_state_at_chapter("character_mark", 1)
    chapter_two_state = database.retrieve_state_at_chapter("character_mark", 2)

    assert tuple(fact.value for fact in chapter_one_state) == ("Mark",)
    assert tuple(fact.value for fact in chapter_two_state) == ("Sir Mark",)


def test_canon_updater_rejects_low_confidence_candidate() -> None:
    """Low confidence candidates do not change Canon."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database, minimum_confidence=0.8)
    low_confidence = ExtractedEntity(
        entity_id="character_mark",
        entity_type="character",
        display_name="Mark",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.5,
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(entities=(low_confidence,)),
        anchors=(anchor(),),
    )

    assert summary.accepted_entities == ()
    assert summary.rejected_candidates == ("character_mark",)
    assert database.retrieve_character("character_mark") is None


def test_canon_updater_rejects_unknown_anchor_candidate() -> None:
    """Candidates without known evidence anchors do not change Canon."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    bad_anchor = ExtractedEntity(
        entity_id="character_mark",
        entity_type="character",
        display_name="Mark",
        evidence_anchor_id="missing_anchor",
        confidence=0.95,
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(entities=(bad_anchor,)),
        anchors=(anchor(),),
    )

    assert summary.accepted_entities == ()
    assert summary.rejected_candidates == ("character_mark",)
    assert database.retrieve_character("character_mark") is None


def test_canon_updater_logs_rejected_candidates(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Canon Updating logs rejected candidates for operational visibility."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    bad_anchor = ExtractedEntity(
        entity_id="character_mark",
        entity_type="character",
        display_name="Mark",
        evidence_anchor_id="missing_anchor",
        confidence=0.95,
    )

    with caplog.at_level(logging.WARNING, logger="scenesmith.canon.updating"):
        updater.apply_extraction_result(
            result=extraction_result(entities=(bad_anchor,)),
            anchors=(anchor(),),
        )

    assert "Rejected canon candidates" in caplog.text


def test_canon_updater_accepts_relationship_between_accepted_entities() -> None:
    """Accepted relationships are stored only after related entities are accepted."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    relationship = ExtractedRelationship(
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="item_iron_sword",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.9,
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity(), accepted_item()),
            relationships=(relationship,),
        ),
        anchors=(anchor(),),
    )

    stored_relationship = database.retrieve_relationship(
        "relationship_character_mark_owns_item_iron_sword"
    )

    assert summary.accepted_relationships == (
        "relationship_character_mark_owns_item_iron_sword",
    )
    assert stored_relationship is not None
    assert stored_relationship.relationship_type == "owns"


def test_canon_updater_does_not_report_duplicate_relationship_as_accepted() -> None:
    """Duplicate semantic relationships are idempotent in update summaries."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    relationship = ExtractedRelationship(
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="item_iron_sword",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.9,
    )
    updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity(), accepted_item()),
            relationships=(relationship,),
        ),
        anchors=(anchor(),),
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity(), accepted_item()),
            relationships=(relationship,),
        ),
        anchors=(anchor(),),
    )

    assert summary.accepted_relationships == ()
    assert len(database.list_relationships_for_entity("character_mark")) == 1


def test_canon_updater_stores_non_character_entities() -> None:
    """Accepted item and location candidates become Canon entities."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    location = ExtractedEntity(
        entity_id="location_academy_classroom",
        entity_type="location",
        display_name="Academy Classroom",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.9,
    )

    updater.apply_extraction_result(
        result=extraction_result(entities=(accepted_item(), location)),
        anchors=(anchor(),),
    )

    item_entity = database.retrieve_entity("item_iron_sword")
    location_entity = database.retrieve_entity("location_academy_classroom")

    assert item_entity is not None
    assert item_entity.display_name == "Iron Sword"
    assert location_entity is not None
    assert location_entity.display_name == "Academy Classroom"


def test_canon_updater_stores_generic_world_entities() -> None:
    """Accepted non-character V1 entity types are stored generically."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    organization = ExtractedEntity(
        entity_id="organization_starlight_empire",
        entity_type="organization",
        display_name="Starlight Empire",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.95,
    )
    ability = ExtractedEntity(
        entity_id="ability_eye_of_insight",
        entity_type="ability",
        display_name="Eye of Insight",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.95,
    )

    updater.apply_extraction_result(
        result=extraction_result(entities=(organization, ability)),
        anchors=(anchor(),),
    )

    stored_organization = database.retrieve_entity("organization_starlight_empire")
    stored_ability = database.retrieve_entity("ability_eye_of_insight")

    assert stored_organization is not None
    assert stored_organization.entity_type == "organization"
    assert stored_organization.display_name == "Starlight Empire"
    assert stored_ability is not None
    assert stored_ability.entity_type == "ability"
    assert stored_ability.display_name == "Eye of Insight"


def test_canon_updater_accepts_fact_and_state_change_candidate() -> None:
    """Accepted fact candidates update Canon state with evidence."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    fact = ExtractedFact(
        fact_id="fact_character_mark_current_weapon_iron_sword",
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.9,
    )
    state_change = ExtractedStateChange(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        valid_from_anchor_id=anchor().anchor_id,
        confidence=0.9,
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity(),),
            facts=(fact,),
            state_changes=(state_change,),
        ),
        anchors=(anchor(),),
    )

    active_state = database.retrieve_state_at_chapter("character_mark", 1)

    assert fact.fact_id in summary.accepted_facts
    assert summary.accepted_state_changes
    assert any(stored_fact.value == "Iron Sword" for stored_fact in active_state)


def test_canon_updater_rejects_relationship_with_unknown_entity() -> None:
    """Relationships cannot be accepted unless both entities are accepted."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    relationship = ExtractedRelationship(
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="item_iron_sword",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.9,
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity(),),
            relationships=(relationship,),
        ),
        anchors=(anchor(),),
    )

    assert summary.accepted_relationships == ()
    assert summary.rejected_candidates == (
        "relationship_character_mark_owns_item_iron_sword",
    )

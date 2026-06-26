"""Tests for Phase 5 Canon Updating."""

import logging
from typing import Any, cast

import pytest

from scenesmith import CanonDatabase, CanonUpdater, CanonUpdateSummary
from scenesmith.extraction import (
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractedStateChange,
    ExtractionResult,
)
from scenesmith.importing import EvidenceAnchor


def anchor(
    paragraph_index: int = 1,
    sentence_index: int = 1,
    quote: str = "Mark lifted the iron sword.",
) -> EvidenceAnchor:
    """Create an evidence anchor for update tests."""
    return EvidenceAnchor(
        anchor_id=(
            "source_demo_chapter_001_scene_001_"
            f"paragraph_{paragraph_index:03d}_sentence_{sentence_index:03d}_anchor"
        ),
        source_id="source_demo",
        chapter_id="source_demo_chapter_001",
        scene_id="source_demo_chapter_001_scene_001",
        paragraph_id=(
            "source_demo_chapter_001_scene_001_"
            f"paragraph_{paragraph_index:03d}"
        ),
        sentence_id=(
            "source_demo_chapter_001_scene_001_"
            f"paragraph_{paragraph_index:03d}_sentence_{sentence_index:03d}"
        ),
        paragraph_index=paragraph_index,
        sentence_index=sentence_index,
        quote=quote,
    )


def accepted_entity(
    name: str = "Mark",
    evidence_anchor_id: str | None = None,
) -> ExtractedEntity:
    """Create an accepted character candidate."""
    return ExtractedEntity(
        entity_id="character_mark",
        entity_type="character",
        display_name=name,
        evidence_anchor_id=evidence_anchor_id or anchor().anchor_id,
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
    scene_id: str | None = None,
) -> ExtractionResult:
    """Create an extraction result for update tests."""
    return ExtractionResult(
        scene_id=scene_id or anchor().scene_id,
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


def test_canon_updater_rejects_duplicate_evidence_anchors() -> None:
    """Canon updates must not accept ambiguous duplicate source anchors."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    source_anchor = anchor()

    with pytest.raises(ValueError, match="cannot contain duplicates"):
        updater.apply_extraction_result(
            result=extraction_result(entities=(accepted_entity(),)),
            anchors=(source_anchor, source_anchor),
        )


def test_canon_updater_versions_existing_character() -> None:
    """Accepted updates preserve previous character versions."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    first_anchor = anchor(sentence_index=1, quote="Mark arrived.")
    second_anchor = anchor(sentence_index=2, quote="Sir Mark arrived.")
    updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity("Mark", first_anchor.anchor_id),)
        ),
        anchors=(first_anchor,),
    )

    updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity("Sir Mark", second_anchor.anchor_id),)
        ),
        anchors=(second_anchor,),
    )

    versions = database.version_character("character_mark")

    assert len(versions) == 2
    assert versions[0].entity.display_name == "Mark"
    assert versions[1].entity.display_name == "Sir Mark"


def test_canon_updater_rejects_same_position_display_name_change() -> None:
    """Display-name changes need later source evidence like other replacements."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    shared_anchor = anchor(quote="Mark, also called Sir Mark, arrived.")
    updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity("Mark", shared_anchor.anchor_id),)
        ),
        anchors=(shared_anchor,),
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity("Sir Mark", shared_anchor.anchor_id),)
        ),
        anchors=(shared_anchor,),
    )

    character = database.retrieve_character("character_mark")

    assert summary.accepted_entities == ()
    assert summary.rejected_candidates == ("character_mark",)
    assert character is not None
    assert character.entity.display_name == "Mark"


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


def test_canon_updater_does_not_create_duplicate_display_name_state() -> None:
    """Repeated display-name mentions do not create noisy state changes."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    first_summary = updater.apply_extraction_result(
        result=extraction_result(entities=(accepted_entity("Mark"),)),
        anchors=(anchor(),),
    )
    second_summary = updater.apply_extraction_result(
        result=extraction_result(entities=(accepted_entity("Mark"),)),
        anchors=(anchor(),),
    )

    assert len(first_summary.accepted_state_changes) == 1
    assert second_summary.accepted_facts == ()
    assert second_summary.accepted_state_changes == ()
    assert len(database.retrieve_state_at_chapter("character_mark", 1)) == 1


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


def test_canon_updater_skips_same_value_replacement_fact() -> None:
    """Repeated replacement facts reinforce canon without versioning state."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    points = ExtractedFact(
        fact_id="fact_character_mark_system_points_100_first",
        entity_id="character_mark",
        attribute="system_points",
        value="100",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.95,
    )
    repeated_points = ExtractedFact(
        fact_id="fact_character_mark_system_points_100_second",
        entity_id="character_mark",
        attribute="system_points",
        value="100",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.95,
    )
    updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity(),),
            facts=(points,),
        ),
        anchors=(anchor(),),
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(facts=(repeated_points,)),
        anchors=(anchor(),),
    )
    active_points = tuple(
        fact
        for fact in database.retrieve_state_at_chapter("character_mark", 1)
        if fact.attribute == "system_points"
    )

    assert summary.accepted_facts == ()
    assert summary.accepted_state_changes == ()
    assert len(active_points) == 1
    assert active_points[0].fact_id == "fact_character_mark_system_points_100_first"


def test_canon_updater_accepts_same_scene_replacement_at_later_sentence() -> None:
    """Replacement facts in one scene require later evidence sentence order."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    first_anchor = anchor(sentence_index=1, quote="Mark felt calm.")
    second_anchor = anchor(sentence_index=2, quote="Mark became alarmed.")
    calm = ExtractedFact(
        fact_id="fact_character_mark_current_mood_calm",
        entity_id="character_mark",
        attribute="current_mood",
        value="Calm",
        evidence_anchor_id=first_anchor.anchor_id,
        confidence=0.95,
    )
    alarmed = ExtractedFact(
        fact_id="fact_character_mark_current_mood_alarmed",
        entity_id="character_mark",
        attribute="current_mood",
        value="Alarmed",
        evidence_anchor_id=second_anchor.anchor_id,
        confidence=0.95,
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity(),),
            facts=(calm, alarmed),
        ),
        anchors=(first_anchor, second_anchor),
    )
    active_mood = tuple(
        fact
        for fact in database.retrieve_state_at_scene("character_mark", 1, 1)
        if fact.attribute == "current_mood"
    )

    assert "fact_character_mark_current_mood_calm" in summary.accepted_facts
    assert "fact_character_mark_current_mood_alarmed" in summary.accepted_facts
    assert tuple(fact.value for fact in active_mood) == ("Alarmed",)


def test_canon_updater_rejects_same_position_replacement_fact() -> None:
    """Ambiguous same-position replacement facts are rejected cleanly."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    shared_anchor = anchor(quote="Mark seemed calm and alarmed.")
    calm = ExtractedFact(
        fact_id="fact_character_mark_current_mood_calm",
        entity_id="character_mark",
        attribute="current_mood",
        value="Calm",
        evidence_anchor_id=shared_anchor.anchor_id,
        confidence=0.95,
    )
    alarmed = ExtractedFact(
        fact_id="fact_character_mark_current_mood_alarmed",
        entity_id="character_mark",
        attribute="current_mood",
        value="Alarmed",
        evidence_anchor_id=shared_anchor.anchor_id,
        confidence=0.95,
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity(),),
            facts=(calm, alarmed),
        ),
        anchors=(shared_anchor,),
    )
    active_mood = tuple(
        fact
        for fact in database.retrieve_state_at_scene("character_mark", 1, 1)
        if fact.attribute == "current_mood"
    )

    assert "fact_character_mark_current_mood_calm" in summary.accepted_facts
    assert summary.rejected_candidates == (
        "fact_character_mark_current_mood_alarmed",
    )
    assert tuple(fact.value for fact in active_mood) == ("Calm",)
    assert database.retrieve_fact("fact_character_mark_current_mood_alarmed") is None


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


def test_canon_updater_rejects_boolean_minimum_confidence() -> None:
    """Updater confidence threshold must be numeric and not boolean."""
    with pytest.raises(ValueError, match="Minimum confidence"):
        CanonUpdater(database=CanonDatabase(), minimum_confidence=True)


def test_canon_updater_rejects_non_numeric_minimum_confidence() -> None:
    """Updater confidence threshold rejects non-numeric runtime values."""
    with pytest.raises(ValueError, match="Minimum confidence"):
        CanonUpdater(database=CanonDatabase(), minimum_confidence=cast(Any, "high"))


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


def test_canon_updater_rejects_result_scene_mismatch() -> None:
    """Canon Updating rejects extraction results applied to another scene."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)

    with pytest.raises(ValueError, match="scene_id does not match"):
        updater.apply_extraction_result(
            result=extraction_result(
                entities=(accepted_entity(),),
                scene_id="source_demo_chapter_999_scene_001",
            ),
            anchors=(anchor(),),
        )


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


def test_canon_update_summary_rejects_duplicate_ids() -> None:
    """Canon update summaries keep each accepted bucket deterministic."""
    with pytest.raises(ValueError, match="cannot contain duplicates"):
        CanonUpdateSummary(
            accepted_facts=("fact_mark_weapon", "fact_mark_weapon"),
        )


def test_canon_update_summary_rejects_accepted_rejected_overlap() -> None:
    """Canon update summaries cannot classify one ID both ways."""
    with pytest.raises(ValueError, match="both accepted and rejected"):
        CanonUpdateSummary(
            accepted_entities=("character_mark",),
            rejected_candidates=("character_mark",),
        )


def test_canon_update_summary_rejects_invalid_ids() -> None:
    """Canon update summaries require machine-safe candidate IDs."""
    with pytest.raises(ValueError, match="cannot contain whitespace"):
        CanonUpdateSummary(
            rejected_candidates=("character mark",),
        )


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


def test_canon_updater_accepts_relationship_between_existing_entities() -> None:
    """Relationships can connect entities already accepted in earlier scenes."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    updater.apply_extraction_result(
        result=extraction_result(entities=(accepted_entity(), accepted_item())),
        anchors=(anchor(),),
    )
    relationship = ExtractedRelationship(
        source_entity_id="character_mark",
        relationship_type="uses",
        target_entity_id="item_iron_sword",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.9,
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(relationships=(relationship,)),
        anchors=(anchor(),),
    )

    assert summary.accepted_relationships == (
        "relationship_character_mark_uses_item_iron_sword",
    )


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
    assert all(
        database.retrieve_state_change(state_change_id) is not None
        for state_change_id in summary.accepted_state_changes
    )


def test_canon_updater_does_not_report_unstored_state_change_candidates() -> None:
    """State-change summaries only contain IDs stored in Canon Database."""
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

    assert summary.accepted_state_changes == (
        "state_fact_character_mark_display_name_mark_"
        "evidence_source_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
        "state_fact_character_mark_current_weapon_iron_sword",
    )
    assert all(
        database.retrieve_state_change(state_change_id) is not None
        for state_change_id in summary.accepted_state_changes
    )


def test_canon_updater_keeps_multiple_abilities_active() -> None:
    """Accepted ability facts accumulate as active canon state."""
    database = CanonDatabase()
    updater = CanonUpdater(database=database)
    fleet_luck = ExtractedFact(
        fact_id="fact_character_mark_ability_fleet_luck",
        entity_id="character_mark",
        attribute="ability",
        value="Fleet Luck Bonus",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.95,
    )
    eye_of_insight = ExtractedFact(
        fact_id="fact_character_mark_ability_eye",
        entity_id="character_mark",
        attribute="ability",
        value="Eye of Insight",
        evidence_anchor_id=anchor().anchor_id,
        confidence=0.95,
    )

    summary = updater.apply_extraction_result(
        result=extraction_result(
            entities=(accepted_entity(),),
            facts=(fleet_luck, eye_of_insight),
        ),
        anchors=(anchor(),),
    )

    active_abilities = tuple(
        fact.value
        for fact in database.retrieve_state_at_chapter("character_mark", 1)
        if fact.attribute == "ability"
    )

    assert fleet_luck.fact_id in summary.accepted_facts
    assert eye_of_insight.fact_id in summary.accepted_facts
    assert set(active_abilities) == {"Fleet Luck Bonus", "Eye of Insight"}


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

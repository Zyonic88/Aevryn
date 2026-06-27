"""Tests for the Aevryn Canon Engine."""

from typing import Any, cast

import pytest

from aevryn.canon import (
    CanonConflict,
    CanonEngine,
    CanonEntity,
    CanonFactVersion,
    CanonRelationship,
    CanonSnapshot,
    DuplicateEntityError,
    EntityType,
    Evidence,
    MissingEvidenceError,
    StoryPosition,
    UnknownEntityError,
)


def make_evidence(
    *,
    chapter: str = "Chapter 1",
    scene: str = "Scene 1",
    quote: str = "Mark lifted the rusty dagger.",
    confidence: float = 1.0,
) -> Evidence:
    """Create valid test evidence."""
    return Evidence(
        chapter=chapter,
        scene=scene,
        quote=quote,
        confidence=confidence,
    )


def register_mark(engine: CanonEngine) -> CanonEntity:
    """Register Mark as a test character."""
    entity = CanonEntity(
        entity_id="character_mark",
        entity_type=EntityType.CHARACTER,
        display_name="Mark",
    )
    engine.register_entity(entity)
    return entity


def register_rusty_dagger(engine: CanonEngine) -> CanonEntity:
    """Register the rusty dagger as a test weapon."""
    entity = CanonEntity(
        entity_id="weapon_rusty_dagger",
        entity_type=EntityType.WEAPON,
        display_name="Rusty Dagger",
    )
    engine.register_entity(entity)
    return entity


def test_canon_evidence_rejects_boolean_confidence() -> None:
    """Canon evidence confidence must be numeric and not boolean."""
    with pytest.raises(ValueError, match="Evidence confidence"):
        Evidence(
            chapter="Chapter 1",
            scene="Scene 1",
            quote="Mark lifted the rusty dagger.",
            confidence=True,
        )


def test_story_position_rejects_boolean_indexes() -> None:
    """Story positions require real one-based integer indexes."""
    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        StoryPosition(chapter_index=True, scene_index=1)

    with pytest.raises(ValueError, match="Scene index must be at least 1"):
        StoryPosition(chapter_index=1, scene_index=True)


def test_story_position_and_evidence_reject_non_numeric_values() -> None:
    """Canon positions and confidence reject non-numeric runtime values."""
    with pytest.raises(ValueError, match="Chapter index must be at least 1"):
        StoryPosition(chapter_index=cast(Any, "1"), scene_index=1)

    with pytest.raises(ValueError, match="Evidence confidence"):
        Evidence(
            chapter="Chapter 1",
            scene="Scene 1",
            quote="Mark lifted the rusty dagger.",
            confidence=cast(Any, "high"),
        )


def test_register_entity_keeps_permanent_id() -> None:
    """Canon entities are registered by permanent ID."""
    engine = CanonEngine()
    entity = CanonEntity(
        entity_id="character_mark",
        entity_type=EntityType.CHARACTER,
        display_name="Mark",
    )

    engine.register_entity(entity)

    assert engine.get_entity("character_mark") == entity
    assert engine.list_entities() == (entity,)


def test_register_entity_rejects_duplicate_id() -> None:
    """The same permanent entity ID cannot be registered twice."""
    engine = CanonEngine()
    entity = CanonEntity(
        entity_id="character_mark",
        entity_type=EntityType.CHARACTER,
        display_name="Mark",
    )
    engine.register_entity(entity)

    with pytest.raises(DuplicateEntityError):
        engine.register_entity(entity)


def test_list_entities_can_filter_by_type() -> None:
    """Registered entities can be listed by canon-owned type."""
    engine = CanonEngine()
    character = register_mark(engine)
    weapon = register_rusty_dagger(engine)

    assert engine.list_entities(EntityType.CHARACTER) == (character,)
    assert engine.list_entities(EntityType.WEAPON) == (weapon,)


def test_record_fact_requires_evidence() -> None:
    """Canon updates cannot be recorded without evidence."""
    engine = CanonEngine()
    register_mark(engine)

    with pytest.raises(MissingEvidenceError):
        engine.record_fact(
            entity_id="character_mark",
            attribute="current_weapon",
            value="Rusty Dagger",
            evidence=None,  # type: ignore[arg-type]
        )


def test_record_fact_rejects_unknown_entity() -> None:
    """Canon facts cannot be attached to unregistered entities."""
    engine = CanonEngine()

    with pytest.raises(UnknownEntityError):
        engine.record_fact(
            entity_id="character_mark",
            attribute="current_weapon",
            value="Rusty Dagger",
            evidence=make_evidence(),
        )


def test_fact_queries_reject_unknown_entity() -> None:
    """Fact query methods reject IDs outside canon."""
    engine = CanonEngine()

    with pytest.raises(UnknownEntityError):
        engine.get_current_fact("character_mark", "current_weapon")

    with pytest.raises(UnknownEntityError):
        engine.get_fact_history("character_mark", "current_weapon")

    with pytest.raises(UnknownEntityError):
        engine.get_fact_at(
            entity_id="character_mark",
            attribute="current_weapon",
            position=StoryPosition(chapter_index=1, scene_index=1),
        )


def test_record_fact_versions_without_overwriting() -> None:
    """New fact values append history instead of overwriting prior canon."""
    engine = CanonEngine()
    register_mark(engine)
    first_evidence = make_evidence(
        chapter="Chapter 1",
        scene="Scene 2",
        quote="Mark carried a rusty dagger.",
    )
    second_evidence = make_evidence(
        chapter="Chapter 8",
        scene="Scene 4",
        quote="Mark replaced the dagger with an iron sword.",
    )

    first_version = engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence=first_evidence,
    )
    second_version = engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence=second_evidence,
    )

    assert first_version.previous_value is None
    assert second_version.previous_value == "Rusty Dagger"
    assert engine.get_current_fact("character_mark", "current_weapon") == second_version
    assert engine.get_fact_history("character_mark", "current_weapon") == (
        first_version,
        second_version,
    )


def test_record_fact_ignores_identical_latest_version() -> None:
    """Repeating the same fact and evidence does not duplicate history."""
    engine = CanonEngine()
    register_mark(engine)
    evidence = make_evidence(
        chapter="Chapter 1",
        scene="Scene 2",
        quote="Mark carried a rusty dagger.",
    )

    first_version = engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence=evidence,
    )
    second_version = engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence=evidence,
    )

    assert second_version == first_version
    assert engine.get_fact_history("character_mark", "current_weapon") == (
        first_version,
    )


def test_unknown_fact_returns_none() -> None:
    """Unknown canon remains unknown until evidence-backed facts exist."""
    engine = CanonEngine()
    register_mark(engine)

    assert engine.get_current_fact("character_mark", "hair_color") is None
    assert engine.get_fact_history("character_mark", "hair_color") == ()


def test_record_relationship_requires_evidence() -> None:
    """Relationships are canon facts and require evidence."""
    engine = CanonEngine()
    register_mark(engine)
    register_rusty_dagger(engine)

    with pytest.raises(MissingEvidenceError):
        engine.record_relationship(
            source_entity_id="character_mark",
            relationship_type="owns",
            target_entity_id="weapon_rusty_dagger",
            evidence=None,  # type: ignore[arg-type]
        )


def test_record_relationship_connects_entities() -> None:
    """Canon relationships connect entities with evidence."""
    engine = CanonEngine()
    register_mark(engine)
    register_rusty_dagger(engine)
    evidence = make_evidence(quote="Mark owned the rusty dagger.")

    relationship = engine.record_relationship(
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="weapon_rusty_dagger",
        evidence=evidence,
    )

    assert relationship.source_entity_id == "character_mark"
    assert relationship.relationship_type == "owns"
    assert relationship.target_entity_id == "weapon_rusty_dagger"
    assert engine.list_relationships("character_mark") == (relationship,)
    assert engine.list_relationships("weapon_rusty_dagger") == (relationship,)


def test_record_relationship_dedupes_semantic_connection() -> None:
    """Repeating a relationship connection returns the existing relationship."""
    engine = CanonEngine()
    register_mark(engine)
    register_rusty_dagger(engine)
    first_evidence = make_evidence(quote="Mark owned the rusty dagger.")
    second_evidence = make_evidence(quote="The rusty dagger belonged to Mark.")

    first_relationship = engine.record_relationship(
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="weapon_rusty_dagger",
        evidence=first_evidence,
    )
    second_relationship = engine.record_relationship(
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="weapon_rusty_dagger",
        evidence=second_evidence,
    )

    assert second_relationship == first_relationship
    assert engine.list_relationships("character_mark") == (first_relationship,)


def test_record_relationship_rejects_unknown_entities() -> None:
    """Relationships cannot reference entities outside canon."""
    engine = CanonEngine()
    register_mark(engine)

    with pytest.raises(UnknownEntityError):
        engine.record_relationship(
            source_entity_id="character_mark",
            relationship_type="owns",
            target_entity_id="weapon_rusty_dagger",
            evidence=make_evidence(),
        )


def test_get_fact_at_returns_historical_state() -> None:
    """Canon can answer what was true at a specific story position."""
    engine = CanonEngine()
    register_mark(engine)
    rusty_dagger_evidence = make_evidence(
        chapter="Chapter 2",
        scene="Scene 1",
        quote="Mark carried a rusty dagger.",
    )
    iron_sword_evidence = make_evidence(
        chapter="Chapter 8",
        scene="Scene 2",
        quote="Mark drew his iron sword.",
    )

    rusty_dagger = engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence=rusty_dagger_evidence,
    )
    iron_sword = engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence=iron_sword_evidence,
    )

    assert engine.get_fact_at(
        "character_mark",
        "current_weapon",
        StoryPosition(chapter_index=2, scene_index=5),
    ) == rusty_dagger
    assert engine.get_fact_at(
        "character_mark",
        "current_weapon",
        StoryPosition(chapter_index=8, scene_index=2),
    ) == iron_sword
    assert engine.get_fact_at(
        "character_mark",
        "current_weapon",
        StoryPosition(chapter_index=1, scene_index=1),
    ) is None


def test_record_fact_preserves_same_position_conflict() -> None:
    """Conflicting values at the same story position are preserved."""
    engine = CanonEngine()
    register_mark(engine)
    first_version = engine.record_fact(
        entity_id="character_mark",
        attribute="hair_color",
        value="Black",
        evidence=make_evidence(
            chapter="Chapter 3",
            scene="Scene 1",
            quote="Mark's black hair was soaked by rain.",
        ),
    )
    conflicting_version = engine.record_fact(
        entity_id="character_mark",
        attribute="hair_color",
        value="Brown",
        evidence=make_evidence(
            chapter="Chapter 3",
            scene="Scene 1",
            quote="Mark pushed brown hair from his eyes.",
        ),
    )

    conflict = engine.list_conflicts()[0]

    assert conflict.entity_id == "character_mark"
    assert conflict.attribute == "hair_color"
    assert conflict.existing_version == first_version
    assert conflict.conflicting_version == conflicting_version


def test_rename_entity_preserves_permanent_id_and_records_fact() -> None:
    """Entity names can change without changing permanent IDs."""
    engine = CanonEngine()
    register_mark(engine)

    name_fact = engine.rename_entity(
        entity_id="character_mark",
        display_name="Sir Mark",
        evidence=make_evidence(
            chapter="Chapter 10",
            scene="Scene 1",
            quote="The court named him Sir Mark.",
        ),
    )

    renamed_entity = engine.get_entity("character_mark")

    assert renamed_entity is not None
    assert renamed_entity.entity_id == "character_mark"
    assert renamed_entity.display_name == "Sir Mark"
    assert name_fact.attribute == "display_name"
    assert name_fact.value == "Sir Mark"


def test_canon_entity_rejects_machine_id_whitespace() -> None:
    """Canon entity IDs are permanent machine-safe IDs."""
    with pytest.raises(ValueError, match="Entity ID cannot contain whitespace"):
        CanonEntity(
            entity_id="character mark",
            entity_type=EntityType.CHARACTER,
            display_name="Mark",
        )


def test_canon_fact_version_rejects_invalid_fields() -> None:
    """Canon fact versions require machine-safe identity and visible values."""
    with pytest.raises(ValueError, match="Fact attribute cannot contain whitespace"):
        CanonFactVersion(
            entity_id="character_mark",
            attribute="current weapon",
            value="Rusty Dagger",
            evidence=make_evidence(),
        )

    with pytest.raises(ValueError, match="Fact previous value is required"):
        CanonFactVersion(
            entity_id="character_mark",
            attribute="current_weapon",
            value="Rusty Dagger",
            previous_value=" ",
            evidence=make_evidence(),
        )


def test_canon_relationship_rejects_invalid_machine_fields() -> None:
    """Canon relationships require machine-safe endpoints and type."""
    with pytest.raises(
        ValueError,
        match="Relationship type cannot contain whitespace",
    ):
        CanonRelationship(
            source_entity_id="character_mark",
            relationship_type="travels with",
            target_entity_id="character_luna",
            evidence=make_evidence(),
        )


def test_canon_conflict_rejects_mismatched_versions() -> None:
    """Canon conflicts must describe different values for one entity attribute."""
    existing = CanonFactVersion(
        entity_id="character_mark",
        attribute="hair_color",
        value="Black",
        evidence=make_evidence(),
    )
    conflicting = CanonFactVersion(
        entity_id="character_luna",
        attribute="hair_color",
        value="Brown",
        evidence=make_evidence(),
    )

    with pytest.raises(ValueError, match="must match conflict entity ID"):
        CanonConflict(
            entity_id="character_mark",
            attribute="hair_color",
            existing_version=existing,
            conflicting_version=conflicting,
        )


def test_canon_snapshot_rejects_mismatched_facts_and_relationships() -> None:
    """Canon snapshots must describe one entity's active state."""
    fact = CanonFactVersion(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence=make_evidence(),
    )

    with pytest.raises(ValueError, match="fact keys must match"):
        CanonSnapshot(
            entity_id="character_mark",
            facts={"weapon": fact},
            relationships=(),
        )

    unrelated_relationship = CanonRelationship(
        source_entity_id="character_luna",
        relationship_type="owns",
        target_entity_id="weapon_rusty_dagger",
        evidence=make_evidence(),
    )
    with pytest.raises(ValueError, match="relationships must connect"):
        CanonSnapshot(
            entity_id="character_mark",
            facts={"current_weapon": fact},
            relationships=(unrelated_relationship,),
        )


def test_snapshot_entity_returns_current_facts_and_relationships() -> None:
    """Snapshots summarize canon state for one entity."""
    engine = CanonEngine()
    register_mark(engine)
    register_rusty_dagger(engine)
    weapon_fact = engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence=make_evidence(),
    )
    relationship = engine.record_relationship(
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="weapon_rusty_dagger",
        evidence=make_evidence(quote="Mark owned the rusty dagger."),
    )

    snapshot = engine.snapshot_entity("character_mark")

    assert snapshot.entity_id == "character_mark"
    assert snapshot.facts == {"current_weapon": weapon_fact}
    assert snapshot.relationships == (relationship,)


def test_snapshot_entity_can_return_historical_state() -> None:
    """Entity snapshots can be generated for a past story position."""
    engine = CanonEngine()
    register_mark(engine)
    register_rusty_dagger(engine)
    rusty_dagger = engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Rusty Dagger",
        evidence=make_evidence(
            chapter="Chapter 2",
            scene="Scene 1",
            quote="Mark carried a rusty dagger.",
        ),
    )
    engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence=make_evidence(
            chapter="Chapter 8",
            scene="Scene 1",
            quote="Mark drew an iron sword.",
        ),
    )
    relationship = engine.record_relationship(
        source_entity_id="character_mark",
        relationship_type="owns",
        target_entity_id="weapon_rusty_dagger",
        evidence=make_evidence(
            chapter="Chapter 2",
            scene="Scene 2",
            quote="The rusty dagger belonged to Mark.",
        ),
    )

    snapshot = engine.snapshot_entity(
        entity_id="character_mark",
        position=StoryPosition(chapter_index=3, scene_index=1),
    )

    assert snapshot.facts == {"current_weapon": rusty_dagger}
    assert snapshot.relationships == (relationship,)


def test_snapshot_all_returns_every_registered_entity() -> None:
    """Whole-canon snapshots include each registered entity."""
    engine = CanonEngine()
    register_mark(engine)
    register_rusty_dagger(engine)

    snapshots = engine.snapshot_all()

    assert [snapshot.entity_id for snapshot in snapshots] == [
        "character_mark",
        "weapon_rusty_dagger",
    ]

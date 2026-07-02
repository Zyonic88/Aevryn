"""Tests for the Entity Resolution foundation."""

import pytest

from aevryn.entity_resolution import (
    EntityIdentityProfile,
    EntityResolutionEngine,
    SurfaceReference,
)


def charlotte_profile() -> EntityIdentityProfile:
    """Return a profile with aliases, titles, descriptions, and pronouns."""
    return EntityIdentityProfile(
        entity_id="character_charlotte",
        canonical_name="Charlotte",
        aliases=("General Charlotte", "Commander Charlotte"),
        titles=("General", "Commander"),
        descriptions=(
            "white-haired Half-Beastman",
            "white-haired beauty",
            "female general",
        ),
        pronouns=("she", "her"),
        evidence_anchor_ids=("anchor_001",),
    )


def test_resolves_alias_title_description_and_pronoun_to_same_identity() -> None:
    """Obvious surface references should resolve to one canonical identity."""
    engine = EntityResolutionEngine()
    profile = charlotte_profile()
    references = (
        SurfaceReference("Charlotte", "anchor_001"),
        SurfaceReference("General Charlotte", "anchor_002"),
        SurfaceReference("the General", "anchor_003"),
        SurfaceReference("the white-haired beauty", "anchor_004"),
        SurfaceReference("the female general", "anchor_005"),
        SurfaceReference("She", "anchor_006"),
    )

    decisions = engine.resolve_references(
        references,
        (profile,),
        context_entity_ids=("character_charlotte",),
    )

    assert tuple(decision.status for decision in decisions) == ("resolved",) * 6
    assert tuple(decision.entity_id for decision in decisions) == (
        "character_charlotte",
    ) * 6
    assert decisions[5].confidence == 0.87


def test_pronoun_resolution_stays_ambiguous_with_multiple_context_candidates() -> None:
    """Pronouns should not merge identities when context supports multiple candidates."""
    engine = EntityResolutionEngine()
    charlotte = charlotte_profile()
    li_na = EntityIdentityProfile(
        entity_id="character_li_na",
        canonical_name="Li Na",
        pronouns=("she", "her"),
        evidence_anchor_ids=("anchor_010",),
    )

    decision = engine.resolve_reference(
        SurfaceReference("she", "anchor_020"),
        (charlotte, li_na),
        context_entity_ids=("character_charlotte", "character_li_na"),
    )

    assert decision.status == "ambiguous"
    assert decision.entity_id is None
    assert {candidate.entity_id for candidate in decision.candidates} == {
        "character_charlotte",
        "character_li_na",
    }


def test_low_confidence_description_remains_unresolved_candidate() -> None:
    """Soft matches should remain candidates instead of silently merging entities."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("the officer", "anchor_030"),
        (
            EntityIdentityProfile(
                entity_id="character_charlotte",
                canonical_name="Charlotte",
                titles=("General",),
                descriptions=("female general officer",),
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "unresolved"
    assert decision.entity_id is None
    assert decision.candidates
    assert decision.candidates[0].confidence < 0.75


def test_surface_reference_preserves_source_anchor() -> None:
    """Resolution decisions should keep the original evidence anchor visible."""
    engine = EntityResolutionEngine()
    reference = SurfaceReference(
        text="Commander Charlotte",
        evidence_anchor_id="anchor_040",
        scene_id="scene_001",
        chapter_id="chapter_001",
    )

    decision = engine.resolve_reference(reference, (charlotte_profile(),))

    assert decision.status == "resolved"
    assert decision.reference.evidence_anchor_id == "anchor_040"
    assert decision.reference.scene_id == "scene_001"
    assert decision.reference.chapter_id == "chapter_001"


def test_identity_profiles_reject_duplicate_aliases() -> None:
    """Identity profiles should stay deterministic."""
    with pytest.raises(ValueError, match="aliases must be unique"):
        EntityIdentityProfile(
            entity_id="character_charlotte",
            canonical_name="Charlotte",
            aliases=("General Charlotte", "General Charlotte"),
        )


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


def test_pronoun_resolution_requires_contextual_identity_support() -> None:
    """Pronouns should not resolve from profile data alone."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("she", "anchor_025"),
        (charlotte_profile(),),
    )

    assert decision.status == "unresolved"
    assert decision.entity_id is None
    assert decision.confidence == 0.87
    assert decision.reason == "Pronoun reference requires contextual identity support."


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


def test_resolves_supported_description_variant_to_same_identity() -> None:
    """Description variants should resolve when multiple explicit tokens support one profile."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("the white-haired woman", "anchor_031"),
        (charlotte_profile(),),
    )

    assert decision.status == "resolved"
    assert decision.entity_id == "character_charlotte"
    assert decision.confidence == 0.82
    assert decision.candidates[0].match_kind == "description_variant"


def test_resolves_title_name_variant_without_prebuilt_alias() -> None:
    """Title plus canonical name should resolve through explicit title/name support."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("General Charlotte", "anchor_032"),
        (
            EntityIdentityProfile(
                entity_id="character_charlotte",
                canonical_name="Charlotte",
                titles=("General",),
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "resolved"
    assert decision.entity_id == "character_charlotte"
    assert decision.confidence == 0.97
    assert decision.candidates[0].match_kind == "title_name"


def test_resolves_explicit_relationship_label_variant() -> None:
    """Family-role references should resolve only when explicitly profile-backed."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("Zhao Chen's sister", "anchor_032a"),
        (
            EntityIdentityProfile(
                entity_id="character_jiang_shasha",
                canonical_name="Jiang Shasha",
                relationship_labels=("sister of Zhao Chen",),
                evidence_anchor_ids=("anchor_002",),
            ),
        ),
    )

    assert decision.status == "resolved"
    assert decision.entity_id == "character_jiang_shasha"
    assert decision.confidence == 0.91
    assert decision.candidates[0].match_kind == "relationship_label"


def test_shared_honorific_stays_ambiguous() -> None:
    """Honorifics should not merge identities when multiple profiles carry the same title."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("Senior Brother", "anchor_032c"),
        (
            EntityIdentityProfile(
                entity_id="character_li_wei",
                canonical_name="Li Wei",
                honorifics=("Senior Brother",),
                evidence_anchor_ids=("anchor_010",),
            ),
            EntityIdentityProfile(
                entity_id="character_han_feng",
                canonical_name="Han Feng",
                honorifics=("Senior Brother",),
                evidence_anchor_ids=("anchor_011",),
            ),
        ),
    )

    assert decision.status == "ambiguous"
    assert decision.entity_id is None
    assert {candidate.entity_id for candidate in decision.candidates} == {
        "character_han_feng",
        "character_li_wei",
    }


def test_title_with_different_name_does_not_resolve_from_title_alone() -> None:
    """A shared title should not merge a different named surface reference."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("General Li", "anchor_032b"),
        (
            EntityIdentityProfile(
                entity_id="character_charlotte",
                canonical_name="Charlotte",
                titles=("General",),
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "unresolved"
    assert decision.entity_id is None
    assert decision.candidates == ()


def test_description_variant_stays_ambiguous_when_multiple_profiles_fit() -> None:
    """Description variants should not merge when multiple identities fit."""
    engine = EntityResolutionEngine()
    elaine = EntityIdentityProfile(
        entity_id="character_elaine",
        canonical_name="Elaine",
        descriptions=("white-haired beauty",),
        evidence_anchor_ids=("anchor_032",),
    )

    decision = engine.resolve_reference(
        SurfaceReference("the white-haired woman", "anchor_033"),
        (charlotte_profile(), elaine),
    )

    assert decision.status == "ambiguous"
    assert decision.entity_id is None
    assert {candidate.entity_id for candidate in decision.candidates} == {
        "character_charlotte",
        "character_elaine",
    }


def test_near_tied_high_confidence_matches_remain_ambiguous() -> None:
    """Near-tied strong matches should not silently merge identities."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("Charlotte", "anchor_035"),
        (
            EntityIdentityProfile(
                entity_id="character_charlotte",
                canonical_name="Charlotte",
                evidence_anchor_ids=("anchor_001",),
            ),
            EntityIdentityProfile(
                entity_id="character_mira",
                canonical_name="Mira",
                aliases=("Charlotte",),
                evidence_anchor_ids=("anchor_002",),
            ),
        ),
    )

    assert decision.status == "ambiguous"
    assert decision.entity_id is None
    assert decision.confidence == 0.99
    assert tuple(candidate.entity_id for candidate in decision.candidates) == (
        "character_charlotte",
        "character_mira",
    )


def test_clear_high_confidence_match_can_still_resolve_over_weaker_candidate() -> None:
    """A strong match should resolve when competing candidates are not close."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("Charlotte", "anchor_036"),
        (
            EntityIdentityProfile(
                entity_id="character_charlotte",
                canonical_name="Charlotte",
                evidence_anchor_ids=("anchor_001",),
            ),
            EntityIdentityProfile(
                entity_id="character_mira",
                canonical_name="Mira",
                descriptions=("brave Charlotte ally",),
                evidence_anchor_ids=("anchor_002",),
            ),
        ),
    )

    assert decision.status == "resolved"
    assert decision.entity_id == "character_charlotte"
    assert decision.confidence == 0.99


def test_duplicate_identity_profile_ids_are_rejected() -> None:
    """Duplicate profile IDs should not create duplicate candidates for one identity."""
    engine = EntityResolutionEngine()

    with pytest.raises(ValueError, match="Entity identity profile IDs must be unique"):
        engine.resolve_reference(
            SurfaceReference("Charlotte", "anchor_037"),
            (
                charlotte_profile(),
                EntityIdentityProfile(
                    entity_id="character_charlotte",
                    canonical_name="General Charlotte",
                    aliases=("Charlotte",),
                    evidence_anchor_ids=("anchor_002",),
                ),
            ),
        )


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


def test_identity_profiles_reject_duplicate_relationship_labels() -> None:
    """Relationship labels should stay deterministic."""
    with pytest.raises(ValueError, match="relationship labels must be unique"):
        EntityIdentityProfile(
            entity_id="character_jiang_shasha",
            canonical_name="Jiang Shasha",
            relationship_labels=("sister of Zhao Chen", "sister of Zhao Chen"),
        )

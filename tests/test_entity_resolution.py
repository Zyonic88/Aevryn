"""Tests for the Entity Resolution foundation."""

import pytest

from aevryn.entity_resolution import (
    EntityIdentityProfile,
    EntityResolutionEngine,
    ResolutionCandidate,
    ResolvedReference,
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


def test_resolves_unicode_equivalent_alias_to_same_identity() -> None:
    """Equivalent Unicode forms should not fragment identity resolution."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("Cafe\u0301 Captain", "anchor_unicode_alias"),
        (
            EntityIdentityProfile(
                entity_id="character_cafe_captain",
                canonical_name="Mira",
                aliases=("Caf\u00e9 Captain",),
                evidence_anchor_ids=("anchor_unicode_alias",),
            ),
        ),
    )

    assert decision.status == "resolved"
    assert decision.entity_id == "character_cafe_captain"
    assert decision.candidates[0].match_kind == "alias"


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


def test_pronoun_surface_does_not_resolve_as_canonical_name() -> None:
    """Pronoun-looking extraction artifacts should not bypass pronoun safety rules."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("She", "anchor_026"),
        (
            EntityIdentityProfile(
                entity_id="character_she",
                canonical_name="She",
                evidence_anchor_ids=("anchor_026",),
            ),
        ),
        context_entity_ids=("character_she",),
    )

    assert decision.status == "unresolved"
    assert decision.entity_id is None
    assert decision.candidates == ()


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


def test_resolves_composite_visual_description_to_same_identity() -> None:
    """Separate visible-trait facts should support one later descriptive reference."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("the white-haired woman", "anchor_031b"),
        (
            EntityIdentityProfile(
                entity_id="character_mira",
                canonical_name="Mira",
                descriptions=("Female", "White hair"),
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "resolved"
    assert decision.entity_id == "character_mira"
    assert decision.candidates[0].match_kind == "composite_description"


def test_gender_only_description_variant_stays_unresolved() -> None:
    """Generic gender words alone are not enough to merge a surface reference."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("the woman", "anchor_031c"),
        (
            EntityIdentityProfile(
                entity_id="character_mira",
                canonical_name="Mira",
                descriptions=("Female",),
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "unresolved"
    assert decision.entity_id is None


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


def test_resolves_supported_title_prefix_with_known_name() -> None:
    """Generic rank/title prefixes should not create duplicate named identities."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("Captain Mira", "anchor_032d"),
        (
            EntityIdentityProfile(
                entity_id="character_mira",
                canonical_name="Mira",
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "resolved"
    assert decision.entity_id == "character_mira"
    assert decision.confidence == 0.93
    assert decision.candidates[0].match_kind == "title_prefix_name"


@pytest.mark.parametrize(
    "reference_text",
    (
        "Captain Mira's",
        "the Captain Mira",
        "Captain-Mira",
        "Captain Mira,",
    ),
)
def test_resolves_punctuated_title_prefix_with_known_name(
    reference_text: str,
) -> None:
    """Punctuation and possessives should not fragment title/name identities."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference(reference_text, "anchor_032f"),
        (
            EntityIdentityProfile(
                entity_id="character_mira",
                canonical_name="Mira",
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "resolved"
    assert decision.entity_id == "character_mira"
    assert decision.candidates[0].match_kind == "title_prefix_name"


def test_title_prefix_resolution_rejects_unknown_descriptors() -> None:
    """Descriptors should not be treated as identity titles."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("Wounded Mira", "anchor_032e"),
        (
            EntityIdentityProfile(
                entity_id="character_mira",
                canonical_name="Mira",
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "unresolved"
    assert decision.entity_id is None
    assert decision.candidates == ()


@pytest.mark.parametrize(
    "reference_text",
    (
        "Mira the Captain",
        "Mira, Captain",
        "Mira-Captain",
    ),
)
def test_resolves_supported_title_suffix_with_known_name(
    reference_text: str,
) -> None:
    """Known names with conservative title suffixes should not fragment identities."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference(reference_text, "anchor_032g"),
        (
            EntityIdentityProfile(
                entity_id="character_mira",
                canonical_name="Mira",
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "resolved"
    assert decision.entity_id == "character_mira"
    assert decision.confidence == 0.93
    assert decision.candidates[0].match_kind == "title_suffix_name"


def test_title_suffix_resolution_rejects_unknown_descriptors() -> None:
    """Generic suffix descriptors should not be treated as identity titles."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("Mira Present", "anchor_032h"),
        (
            EntityIdentityProfile(
                entity_id="character_mira",
                canonical_name="Mira",
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "unresolved"
    assert decision.entity_id is None
    assert decision.candidates == ()


def test_resolves_embedded_name_with_supported_identity_context() -> None:
    """Known names inside backed descriptions should not fragment identities."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("the female general Charlotte", "anchor_032i"),
        (
            EntityIdentityProfile(
                entity_id="character_charlotte",
                canonical_name="Charlotte",
                titles=("General",),
                descriptions=("Female",),
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "resolved"
    assert decision.entity_id == "character_charlotte"
    assert decision.confidence == 0.94
    assert decision.candidates[0].match_kind == "embedded_name_context"


def test_resolves_embedded_alias_with_supported_identity_context() -> None:
    """Known aliases plus supported roles should not create duplicate identities."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("Captain Mark the engineer", "anchor_032k"),
        (
            EntityIdentityProfile(
                entity_id="character_mark",
                canonical_name="Mark",
                aliases=("Captain Mark",),
                descriptions=("Engineer",),
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "resolved"
    assert decision.entity_id == "character_mark"
    assert decision.confidence == 0.94
    assert decision.candidates[0].match_kind == "embedded_name_context"


def test_embedded_name_rejects_unsupported_identity_context() -> None:
    """Unknown descriptors around a known name should not force a merge."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("the wounded Charlotte", "anchor_032j"),
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


def test_embedded_alias_rejects_unsupported_identity_context() -> None:
    """Aliases do not make unsupported descriptors safe to merge."""
    engine = EntityResolutionEngine()

    decision = engine.resolve_reference(
        SurfaceReference("Captain Mark the traitor", "anchor_032l"),
        (
            EntityIdentityProfile(
                entity_id="character_mark",
                canonical_name="Mark",
                aliases=("Captain Mark",),
                descriptions=("Engineer",),
                evidence_anchor_ids=("anchor_001",),
            ),
        ),
    )

    assert decision.status == "unresolved"
    assert decision.entity_id is None
    assert decision.candidates == ()


def test_resolves_explicit_relationship_label_variant() -> None:
    """Family-role references should resolve only when explicitly profile-backed."""
    engine = EntityResolutionEngine()

    decisions = tuple(
        engine.resolve_reference(
            SurfaceReference(reference_text, f"anchor_032a_{index}"),
            (
                EntityIdentityProfile(
                    entity_id="character_jiang_shasha",
                    canonical_name="Jiang Shasha",
                    relationship_labels=("sister of Zhao Chen",),
                    evidence_anchor_ids=("anchor_002",),
                ),
            ),
        )
        for index, reference_text in enumerate(
            (
                "Zhao Chen's sister",
                "Zhao Chen’s sister",
                "Zhao Chen’S sister",
            ),
            start=1,
        )
    )

    assert tuple(decision.status for decision in decisions) == ("resolved",) * 3
    assert tuple(decision.entity_id for decision in decisions) == (
        "character_jiang_shasha",
    ) * 3
    assert tuple(decision.confidence for decision in decisions) == (0.91,) * 3
    assert tuple(decision.candidates[0].match_kind for decision in decisions) == (
        "relationship_label",
    ) * 3


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
            aliases=("General Charlotte", " general charlotte "),
        )


def test_identity_profiles_reject_unicode_equivalent_duplicate_aliases() -> None:
    """Alias uniqueness should compare normalized Unicode, not raw code points."""
    with pytest.raises(ValueError, match="aliases must be unique"):
        EntityIdentityProfile(
            entity_id="character_cafe_captain",
            canonical_name="Mira",
            aliases=("Caf\u00e9 Captain", "Cafe\u0301 Captain"),
        )


def test_identity_profile_surface_lists_must_be_tuples() -> None:
    """Identity profile surfaces should not accept loose strings as sequences."""
    with pytest.raises(ValueError, match="aliases must be a tuple"):
        EntityIdentityProfile(
            entity_id="character_charlotte",
            canonical_name="Charlotte",
            aliases="General Charlotte",  # type: ignore[arg-type]
        )


def test_identity_profiles_reject_duplicate_relationship_labels() -> None:
    """Relationship labels should stay deterministic."""
    with pytest.raises(ValueError, match="relationship labels must be unique"):
        EntityIdentityProfile(
            entity_id="character_jiang_shasha",
            canonical_name="Jiang Shasha",
            relationship_labels=("sister of Zhao Chen", " Sister of Zhao Chen "),
        )


def test_resolved_reference_candidates_must_be_a_tuple() -> None:
    """Resolution candidate metadata should not accept mutable sequences."""
    with pytest.raises(ValueError, match="candidates must be a tuple"):
        ResolvedReference(
            reference=SurfaceReference("Charlotte", "anchor_050"),
            status="ambiguous",
            candidates=[
                ResolutionCandidate(
                    entity_id="character_charlotte",
                    confidence=0.99,
                    match_kind="canonical_name",
                    matched_text="Charlotte",
                )
            ],  # type: ignore[arg-type]
        )


def test_resolved_reference_rejects_duplicate_candidate_entity_ids() -> None:
    """One resolution decision should not carry duplicate candidates for one identity."""
    with pytest.raises(ValueError, match="candidate entity IDs must be unique"):
        ResolvedReference(
            reference=SurfaceReference("Charlotte", "anchor_051"),
            status="ambiguous",
            candidates=(
                ResolutionCandidate(
                    entity_id="character_charlotte",
                    confidence=0.99,
                    match_kind="canonical_name",
                    matched_text="Charlotte",
                ),
                ResolutionCandidate(
                    entity_id="character_charlotte",
                    confidence=0.95,
                    match_kind="alias",
                    matched_text="General Charlotte",
                ),
            ),
        )

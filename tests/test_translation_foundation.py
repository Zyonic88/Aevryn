"""Tests for the Translation Foundation boundary."""

import pytest

from aevryn.translation import (
    GlossaryTerm,
    TranslationEngine,
    TranslationIssue,
    TranslationMode,
    TranslationSentenceUnderstanding,
    TranslationUnit,
)


def test_translation_normalization_preserves_source_anchor_links() -> None:
    """Normalized text should remain tied to original evidence anchors."""
    engine = TranslationEngine()
    unit = TranslationUnit(
        unit_id="chapter_001_scene_001_unit_001",
        source_text="Zhao Chen activated the Super Starfleet System.",
        evidence_anchor_ids=("anchor_001", "anchor_002"),
        source_language="en",
        target_language="en",
        source_chapter_id="chapter_001",
        source_scene_id="scene_001",
    )

    result = engine.normalize_unit(unit)

    assert result.normalized_text == "Zhao Chen activated the Super Starfleet System."
    assert result.source_evidence_anchor_ids == ("anchor_001", "anchor_002")
    assert result.source_scene_id == "scene_001"
    assert result.issues == ()


def test_translation_modes_are_bounded_and_preserved() -> None:
    """Supported modes should stay explicit metadata instead of changing Canon truth."""
    engine = TranslationEngine()
    unit = TranslationUnit(
        unit_id="chapter_001_scene_001_unit_002",
        source_text="Charlotte raised her sword.",
        evidence_anchor_ids=("anchor_003",),
    )

    modes: tuple[TranslationMode, ...] = (
        "literal",
        "clean_english",
        "localized",
        "subtitle_narration",
    )

    assert tuple(engine.normalize_unit(unit, mode=mode).mode for mode in modes) == modes


def test_translation_rejects_unknown_mode() -> None:
    """Unsupported modes should fail closed instead of implying untested behavior."""
    engine = TranslationEngine()

    with pytest.raises(ValueError, match="Translated unit mode is invalid"):
        engine.normalize_unit(
            TranslationUnit(
                unit_id="chapter_001_scene_001_unit_003",
                source_text="Charlotte raised her sword.",
                evidence_anchor_ids=("anchor_004",),
            ),
            mode="marketing_copy",  # type: ignore[arg-type]
        )


def test_translation_glossary_preserves_preferred_story_terms() -> None:
    """Glossary terms should normalize story-specific terms consistently."""
    engine = TranslationEngine()

    result = engine.normalize_unit(
        TranslationUnit(
            unit_id="unit_001",
            source_text="The eye of insight scanned the T3 blizzard-class light cruiser.",
            evidence_anchor_ids=("anchor_010",),
        ),
        glossary=(
            GlossaryTerm(
                source_term="eye of insight",
                preferred_term="Eye of Insight",
                evidence_anchor_id="anchor_010",
            ),
            GlossaryTerm(
                source_term="T3 blizzard-class light cruiser",
                preferred_term="T3 Blizzard-class Light Interstellar Battlecruiser",
                evidence_anchor_id="anchor_010",
                entity_id="item_t3_blizzard",
            ),
        ),
    )

    assert "Eye of Insight" in result.normalized_text
    assert "T3 Blizzard-class Light Interstellar Battlecruiser" in result.normalized_text


def test_translation_normalizes_unicode_before_glossary_matching() -> None:
    """Visually identical Unicode terms should match deterministically."""
    engine = TranslationEngine()

    result = engine.normalize_unit(
        TranslationUnit(
            unit_id="unit_001_unicode_normalized",
            source_text="The Cafe\u0301 Nebula opened above the academy.",
            evidence_anchor_ids=("anchor_unicode",),
        ),
        glossary=(
            GlossaryTerm(
                source_term="Caf\u00e9 Nebula",
                preferred_term="Cafe Nebula",
                evidence_anchor_id="anchor_unicode",
                term_kind="location",
            ),
        ),
    )

    assert result.normalized_text == "The Cafe Nebula opened above the academy."


def test_glossary_source_terms_are_unicode_normalized_before_duplicate_checks() -> None:
    """Equivalent Unicode source terms should not create order-dependent glossary matches."""
    with pytest.raises(ValueError, match="Glossary source terms must be unique"):
        TranslationEngine().normalize_unit(
            TranslationUnit(
                unit_id="unit_001_unicode_duplicate",
                source_text="The Cafe\u0301 Nebula opened.",
                evidence_anchor_ids=("anchor_unicode_duplicate",),
            ),
            glossary=(
                GlossaryTerm(
                    source_term="Caf\u00e9 Nebula",
                    preferred_term="Cafe Nebula",
                    evidence_anchor_id="anchor_unicode_duplicate",
                ),
                GlossaryTerm(
                    source_term="Cafe\u0301 Nebula",
                    preferred_term="Coffee Nebula",
                    evidence_anchor_id="anchor_unicode_duplicate",
                ),
            ),
        )


def test_translation_glossary_tracks_protected_term_categories() -> None:
    """Glossary terms should classify the story term they protect without creating canon."""
    engine = TranslationEngine()
    glossary = (
        GlossaryTerm(
            source_term="Zhao Chen",
            preferred_term="Zhao Chen",
            evidence_anchor_id="anchor_name",
            entity_id="character_zhao_chen",
            term_kind="name",
        ),
        GlossaryTerm(
            source_term="North Star Academy",
            preferred_term="North Star Academy",
            evidence_anchor_id="anchor_location",
            entity_id="location_north_star_academy",
            term_kind="location",
        ),
        GlossaryTerm(
            source_term="Eye of Insight",
            preferred_term="Eye of Insight",
            evidence_anchor_id="anchor_skill",
            entity_id="skill_eye_of_insight",
            term_kind="skill",
        ),
    )

    result = engine.normalize_unit(
        TranslationUnit(
            unit_id="unit_001_term_categories",
            source_text="Zhao Chen trained at North Star Academy and used Eye of Insight.",
            evidence_anchor_ids=("anchor_name", "anchor_location", "anchor_skill"),
        ),
        glossary=glossary,
    )

    assert result.normalized_text == (
        "Zhao Chen trained at North Star Academy and used Eye of Insight."
    )
    assert tuple(term.term_kind for term in glossary) == ("name", "location", "skill")
    assert result.issues == ()


def test_translation_glossary_rejects_unknown_term_category() -> None:
    """Unsupported categories should fail closed instead of creating ambiguous metadata."""
    with pytest.raises(ValueError, match="Translation term kind is invalid"):
        GlossaryTerm(
            source_term="Zhao Chen",
            preferred_term="Zhao Chen",
            evidence_anchor_id="anchor_invalid_kind",
            term_kind="species",  # type: ignore[arg-type]
        )


def test_translation_glossary_matches_complete_terms_only() -> None:
    """Glossary handling should not mutate unrelated longer words."""
    engine = TranslationEngine()

    result = engine.normalize_unit(
        TranslationUnit(
            unit_id="unit_001_complete_terms",
            source_text="Qi steadied her breath, but the qilin statue did not move.",
            evidence_anchor_ids=("anchor_011",),
        ),
        glossary=(
            GlossaryTerm(
                source_term="qi",
                preferred_term="Qi",
                evidence_anchor_id="anchor_011",
            ),
        ),
    )

    assert result.normalized_text == (
        "Qi steadied her breath, but the qilin statue did not move."
    )


def test_translation_glossary_respects_cjk_compound_boundaries() -> None:
    """Single-character CJK terms should not mutate larger source compounds."""
    engine = TranslationEngine()

    result = engine.normalize_unit(
        TranslationUnit(
            unit_id="unit_001_cjk_boundaries",
            source_text="她参悟了天道，也提到了 道 。",
            evidence_anchor_ids=("anchor_011a",),
            source_language="zh",
            target_language="en",
        ),
        glossary=(
            GlossaryTerm(
                source_term="道",
                preferred_term="Dao",
                evidence_anchor_id="anchor_011a",
                term_kind="power_system",
            ),
        ),
    )

    assert result.normalized_text == "她参悟了天道，也提到了 Dao 。"


def test_translation_glossary_prefers_longer_overlapping_terms() -> None:
    """Specific canon terms should win over shorter overlapping glossary terms."""
    engine = TranslationEngine()

    result = engine.normalize_unit(
        TranslationUnit(
            unit_id="unit_001_overlapping_terms",
            source_text="The Super Starfleet System assigned a Starfleet reward.",
            evidence_anchor_ids=("anchor_012",),
        ),
        glossary=(
            GlossaryTerm(
                source_term="Starfleet",
                preferred_term="Starfleet",
                evidence_anchor_id="anchor_012",
            ),
            GlossaryTerm(
                source_term="Super Starfleet System",
                preferred_term="Super Starfleet System",
                evidence_anchor_id="anchor_012",
                entity_id="skill_super_starfleet_system",
            ),
        ),
    )

    assert result.normalized_text == (
        "The Super Starfleet System assigned a Starfleet reward."
    )


def test_translation_glossary_does_not_rewrite_preferred_long_term_output() -> None:
    """Shorter terms should not mutate the preferred output for a longer term."""
    engine = TranslationEngine()

    result = engine.normalize_unit(
        TranslationUnit(
            unit_id="unit_001_no_cascade",
            source_text="The t3 blizzard-class light cruiser docked beside a blizzard shrine.",
            evidence_anchor_ids=("anchor_012a",),
        ),
        glossary=(
            GlossaryTerm(
                source_term="t3 blizzard-class light cruiser",
                preferred_term="T3 Blizzard-class Light Interstellar Battlecruiser",
                evidence_anchor_id="anchor_012a",
                entity_id="item_t3_blizzard",
            ),
            GlossaryTerm(
                source_term="blizzard",
                preferred_term="storm",
                evidence_anchor_id="anchor_012a",
            ),
        ),
    )

    assert result.normalized_text == (
        "The T3 Blizzard-class Light Interstellar Battlecruiser docked beside a storm shrine."
    )


def test_uncertain_long_glossary_term_blocks_partial_replacement() -> None:
    """Uncertain phrases should be preserved whole instead of partially normalized."""
    engine = TranslationEngine()

    result = engine.normalize_unit(
        TranslationUnit(
            unit_id="unit_001_uncertain_overlap",
            source_text="Charlotte studied the qi blade before sensing qi nearby.",
            evidence_anchor_ids=("anchor_012b",),
        ),
        glossary=(
            GlossaryTerm(
                source_term="qi blade",
                preferred_term="qi blade",
                evidence_anchor_id="anchor_012b",
                review_required=True,
            ),
            GlossaryTerm(
                source_term="qi",
                preferred_term="Qi",
                evidence_anchor_id="anchor_012b",
            ),
        ),
    )

    assert result.normalized_text == "Charlotte studied the qi blade before sensing Qi nearby."
    assert len(result.issues) == 1
    assert result.issues[0].source_term == "qi blade"


def test_translation_glossary_rejects_duplicate_source_terms() -> None:
    """Duplicate glossary source terms should not make normalization order-dependent."""
    engine = TranslationEngine()

    with pytest.raises(ValueError, match="Glossary source terms must be unique"):
        engine.normalize_unit(
            TranslationUnit(
                unit_id="unit_001_duplicate_terms",
                source_text="Qi steadied her breath.",
                evidence_anchor_ids=("anchor_013",),
            ),
            glossary=(
                GlossaryTerm(
                    source_term="qi",
                    preferred_term="Qi",
                    evidence_anchor_id="anchor_013",
                ),
                GlossaryTerm(
                    source_term="QI",
                    preferred_term="Mystic Energy",
                    evidence_anchor_id="anchor_013",
                    review_required=True,
                ),
            ),
        )


def test_uncertain_glossary_term_is_preserved_for_review() -> None:
    """Uncertain terms should stay in text and become review issues."""
    engine = TranslationEngine()

    result = engine.normalize_unit(
        TranslationUnit(
            unit_id="unit_002",
            source_text="Charlotte used qi to steady the formation.",
            evidence_anchor_ids=("anchor_020",),
        ),
        glossary=(
            GlossaryTerm(
                source_term="qi",
                preferred_term="qi",
                evidence_anchor_id="anchor_020",
                review_required=True,
            ),
        ),
    )

    assert "qi" in result.normalized_text
    assert len(result.issues) == 1
    assert result.issues[0].issue_code == "translation_review_required"
    assert result.issues[0].term_kind == "term"
    assert result.issues[0].evidence_anchor_ids == ("anchor_020",)


def test_uncertain_glossary_issue_keeps_protected_term_category() -> None:
    """Review issues should carry safe term-category metadata without source prose leakage."""
    engine = TranslationEngine()

    result = engine.normalize_unit(
        TranslationUnit(
            unit_id="unit_002_power_system_review",
            source_text="The dantian pulsed with unfamiliar force.",
            evidence_anchor_ids=("anchor_021",),
        ),
        glossary=(
            GlossaryTerm(
                source_term="dantian",
                preferred_term="dantian",
                evidence_anchor_id="anchor_021",
                term_kind="power_system",
                review_required=True,
            ),
        ),
    )

    assert result.normalized_text == "The dantian pulsed with unfamiliar force."
    assert len(result.issues) == 1
    assert result.issues[0].term_kind == "power_system"
    assert result.issues[0].source_term == "dantian"


def test_ambiguous_glossary_term_preserves_source_and_records_meaning_count() -> None:
    """Terms with multiple plausible meanings should not be translated by guesswork."""
    engine = TranslationEngine()

    result = engine.normalize_unit(
        TranslationUnit(
            unit_id="unit_002_ambiguous_term",
            source_text="The dao shook as Charlotte stepped forward.",
            evidence_anchor_ids=("anchor_022",),
        ),
        glossary=(
            GlossaryTerm(
                source_term="dao",
                preferred_term="Dao",
                possible_meanings=("path or principle", "blade or saber"),
                evidence_anchor_id="anchor_022",
                term_kind="power_system",
            ),
        ),
    )

    assert result.normalized_text == "The dao shook as Charlotte stepped forward."
    assert len(result.issues) == 1
    assert result.issues[0].issue_code == "translation_review_required"
    assert result.issues[0].message == "Ambiguous glossary term preserved for review."
    assert result.issues[0].term_kind == "power_system"
    assert result.issues[0].possible_meaning_count == 2


def test_glossary_possible_meanings_are_normalized_and_unique() -> None:
    """Ambiguity choices should be deterministic before they enter translation review."""
    with pytest.raises(ValueError, match="possible meanings must be unique"):
        GlossaryTerm(
            source_term="dao",
            preferred_term="Dao",
            possible_meanings=("path or principle", " path or principle "),
            evidence_anchor_id="anchor_023",
        )


def test_glossary_possible_meanings_reject_case_only_duplicates() -> None:
    """Ambiguous meaning choices should not differ only by capitalization."""
    with pytest.raises(ValueError, match="possible meanings must be unique"):
        GlossaryTerm(
            source_term="dao",
            preferred_term="Dao",
            possible_meanings=("Dao principle", "dao principle"),
            evidence_anchor_id="anchor_023a",
        )


def test_glossary_possible_meanings_must_be_multiple_tuple_values() -> None:
    """Possible meanings should be explicit multiple choices, not loose strings."""
    with pytest.raises(ValueError, match="must be a tuple"):
        GlossaryTerm(
            source_term="dao",
            preferred_term="Dao",
            possible_meanings="path or principle",  # type: ignore[arg-type]
            evidence_anchor_id="anchor_024",
        )

    with pytest.raises(ValueError, match="at least two values"):
        GlossaryTerm(
            source_term="dao",
            preferred_term="Dao",
            possible_meanings=("path or principle",),
            evidence_anchor_id="anchor_024",
        )


def test_translation_issue_possible_meaning_count_rejects_single_choice() -> None:
    """Review metadata should not describe a single meaning as ambiguous."""
    with pytest.raises(ValueError, match="cannot be exactly one"):
        TranslationIssue(
            issue_code="translation_review_required",
            source_term="dao",
            message="Ambiguous glossary term preserved for review.",
            evidence_anchor_ids=("anchor_025",),
            possible_meaning_count=1,
        )


def test_translation_evidence_anchor_links_must_be_tuples() -> None:
    """Source links should not accept loose strings that look like sequences."""
    with pytest.raises(ValueError, match="evidence anchor IDs must be a tuple"):
        TranslationUnit(
            unit_id="unit_002_anchor_string",
            source_text="Text",
            evidence_anchor_ids="anchor_001",  # type: ignore[arg-type]
        )


def test_translation_units_reject_duplicate_anchor_links() -> None:
    """Translation source links should remain deterministic."""
    with pytest.raises(ValueError, match="must be unique"):
        TranslationUnit(
            unit_id="unit_003",
            source_text="Text",
            evidence_anchor_ids=("anchor_001", "anchor_001"),
        )


def test_translation_issue_anchor_links_must_be_tuples() -> None:
    """Review issues should keep evidence links as immutable metadata."""
    with pytest.raises(ValueError, match="evidence anchor IDs must be a tuple"):
        TranslationIssue(
            issue_code="translation_review_required",
            source_term="dao",
            message="Ambiguous glossary term preserved for review.",
            evidence_anchor_ids=["anchor_025"],  # type: ignore[arg-type]
        )


def test_translation_uses_sentence_understanding_to_flag_ambiguity() -> None:
    """Sentence ambiguity should become review metadata without changing source text."""
    result = TranslationEngine().normalize_unit(
        TranslationUnit(
            unit_id="unit_sentence_ambiguity",
            source_text="The dao core reacted.",
            evidence_anchor_ids=("anchor_sentence_ambiguity",),
            sentence_understanding=(
                TranslationSentenceUnderstanding(
                    evidence_anchor_id="anchor_sentence_ambiguity",
                    signals=("translation_ambiguity",),
                    ambiguity_terms=("dao", "core"),
                    review_required=True,
                ),
            ),
        )
    )

    assert result.normalized_text == "The dao core reacted."
    assert tuple(issue.issue_code for issue in result.issues) == (
        "translation_sentence_ambiguity",
        "translation_sentence_ambiguity",
    )
    assert tuple(issue.source_term for issue in result.issues) == ("core", "dao")
    assert all(
        issue.evidence_anchor_ids == ("anchor_sentence_ambiguity",)
        for issue in result.issues
    )
    assert all(issue.term_kind == "power_system" for issue in result.issues)
    assert "The dao core reacted." not in {
        issue.source_term for issue in result.issues
    }
    assert "The dao core reacted." not in {issue.message for issue in result.issues}


def test_translation_classifies_cultivation_body_ambiguity_as_power_system() -> None:
    """Cultivation body terms should remain reviewable power-system metadata."""
    result = TranslationEngine().normalize_unit(
        TranslationUnit(
            unit_id="unit_cultivation_body_ambiguity",
            source_text="The dantian and spiritual root reacted.",
            evidence_anchor_ids=("anchor_cultivation_body",),
            sentence_understanding=(
                TranslationSentenceUnderstanding(
                    evidence_anchor_id="anchor_cultivation_body",
                    signals=("translation_ambiguity",),
                    ambiguity_terms=("dantian", "spiritual root"),
                    review_required=True,
                ),
            ),
        )
    )

    assert result.normalized_text == "The dantian and spiritual root reacted."
    assert tuple(issue.source_term for issue in result.issues) == (
        "dantian",
        "spiritual root",
    )
    assert all(issue.term_kind == "power_system" for issue in result.issues)
    assert all(
        issue.evidence_anchor_ids == ("anchor_cultivation_body",)
        for issue in result.issues
    )
    assert all(
        "The dantian and spiritual root reacted." not in issue.message
        for issue in result.issues
    )


def test_translation_sentence_ambiguity_deduplicates_glossary_review_terms() -> None:
    """Glossary review should not be duplicated by sentence ambiguity metadata."""
    result = TranslationEngine().normalize_unit(
        TranslationUnit(
            unit_id="unit_sentence_glossary_dedup",
            source_text="The dao shook.",
            evidence_anchor_ids=("anchor_sentence_glossary",),
            sentence_understanding=(
                TranslationSentenceUnderstanding(
                    evidence_anchor_id="anchor_sentence_glossary",
                    signals=("translation_ambiguity",),
                    ambiguity_terms=("dao",),
                    review_required=True,
                ),
            ),
        ),
        glossary=(
            GlossaryTerm(
                source_term="dao",
                preferred_term="Dao",
                possible_meanings=("path or principle", "blade or saber"),
                evidence_anchor_id="anchor_sentence_glossary",
                term_kind="power_system",
            ),
        ),
    )

    assert result.normalized_text == "The dao shook."
    assert tuple(issue.issue_code for issue in result.issues) == (
        "translation_review_required",
    )


def test_translation_accepts_world_context_sentence_signals_without_review_noise() -> None:
    """World-routing signals should remain metadata unless translation is ambiguous."""
    result = TranslationEngine().normalize_unit(
        TranslationUnit(
            unit_id="unit_sentence_world_context",
            source_text="Zhao Chen entered North Star Academy.",
            evidence_anchor_ids=("anchor_sentence_world",),
            sentence_understanding=(
                TranslationSentenceUnderstanding(
                    evidence_anchor_id="anchor_sentence_world",
                    signals=("location_reference", "organization_reference"),
                    review_required=False,
                ),
            ),
        )
    )

    assert result.normalized_text == "Zhao Chen entered North Star Academy."
    assert result.issues == ()


def test_translation_unit_rejects_sentence_understanding_anchor_mismatch() -> None:
    """Sentence metadata must point to one of the unit evidence anchors."""
    with pytest.raises(ValueError, match="must match evidence anchors"):
        TranslationUnit(
            unit_id="unit_sentence_anchor_mismatch",
            source_text="The dao shook.",
            evidence_anchor_ids=("anchor_known",),
            sentence_understanding=(
                TranslationSentenceUnderstanding(
                    evidence_anchor_id="anchor_unknown",
                    signals=("translation_ambiguity",),
                    ambiguity_terms=("dao",),
                ),
            ),
        )


def test_translation_unit_rejects_duplicate_sentence_understanding_anchors() -> None:
    """Sentence metadata should remain deterministic per evidence anchor."""
    with pytest.raises(ValueError, match="anchors must be unique"):
        TranslationUnit(
            unit_id="unit_sentence_duplicate_anchor",
            source_text="The dao shook. The dao settled.",
            evidence_anchor_ids=("anchor_duplicate",),
            sentence_understanding=(
                TranslationSentenceUnderstanding(
                    evidence_anchor_id="anchor_duplicate",
                    signals=("translation_ambiguity",),
                    ambiguity_terms=("dao",),
                ),
                TranslationSentenceUnderstanding(
                    evidence_anchor_id="anchor_duplicate",
                    signals=("translation_ambiguity",),
                    ambiguity_terms=("dao",),
                ),
            ),
        )

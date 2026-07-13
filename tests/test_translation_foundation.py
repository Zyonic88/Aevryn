"""Tests for the Translation Foundation boundary."""

import pytest

from aevryn.translation import GlossaryTerm, TranslationEngine, TranslationUnit


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
    assert result.issues[0].evidence_anchor_ids == ("anchor_020",)


def test_translation_units_reject_duplicate_anchor_links() -> None:
    """Translation source links should remain deterministic."""
    with pytest.raises(ValueError, match="must be unique"):
        TranslationUnit(
            unit_id="unit_003",
            source_text="Text",
            evidence_anchor_ids=("anchor_001", "anchor_001"),
        )

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

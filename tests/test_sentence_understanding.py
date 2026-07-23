"""Tests for the Sentence Understanding boundary."""

import pytest

from aevryn import SentenceUnderstandingEngine, StoryImporter
from aevryn.importing import EvidenceAnchor, ImportedSentence


def test_sentence_understanding_analyzes_each_imported_sentence() -> None:
    """Every imported sentence should receive evidence-linked meaning metadata."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_demo",
        title="Sentence Demo",
        text=(
            "Chapter 1\n"
            "Zhao Chen activated the Super Starfleet System.\n"
            "Charlotte raised her sword and used Eye of Insight technique."
        ),
    )

    understandings = SentenceUnderstandingEngine().analyze_imported_source(imported)

    assert len(understandings) == 2
    assert tuple(item.sentence_index for item in understandings) == (1, 2)
    anchor_ids = {anchor.anchor_id for anchor in imported.anchors}
    assert all(item.evidence_anchor_id in anchor_ids for item in understandings)
    assert "system_reference" in understandings[0].signals
    assert "skill_reference" in understandings[1].signals
    assert "item_reference" in understandings[1].signals
    assert understandings[1].review_required is True


def test_sentence_understanding_keeps_full_source_text_out_of_metadata() -> None:
    """Understanding output stores signals and cue terms, not full manuscript prose."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_privacy",
        title="Sentence Privacy",
        text="Chapter 1\nCharlotte whispered, \"The seal can mean a mark or a technique.\"",
    )

    understanding = SentenceUnderstandingEngine().analyze_imported_source(imported)[0]
    serialized_values = (
        understanding.sentence_id,
        understanding.evidence_anchor_id,
        understanding.source_chapter_id,
        understanding.source_scene_id,
        *understanding.signals,
        *understanding.cue_terms,
        *understanding.ambiguity_terms,
    )

    assert "dialogue" in understanding.signals
    assert "translation_ambiguity" in understanding.signals
    assert "seal" in understanding.ambiguity_terms
    assert all(
        "The seal can mean a mark or a technique" not in value
        for value in serialized_values
    )


def test_sentence_understanding_flags_translation_ambiguous_terms() -> None:
    """Ambiguous power-system terms should be reviewable before translation chooses meaning."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_ambiguity",
        title="Sentence Ambiguity",
        text="Chapter 1\nThe dao core inside the vessel reacted to qi.",
    )

    understanding = SentenceUnderstandingEngine().analyze_imported_source(imported)[0]

    assert "translation_ambiguity" in understanding.signals
    assert understanding.ambiguity_terms == ("core", "dao", "qi", "vessel")
    assert understanding.review_required is True


def test_sentence_understanding_detects_relationship_language() -> None:
    """Family, title, and social references should be visible before extraction."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_relationships",
        title="Sentence Relationships",
        text="Chapter 1\nThe general's sister asked her master for help.",
    )

    understanding = SentenceUnderstandingEngine().analyze_imported_source(imported)[0]

    assert "dialogue" in understanding.signals
    assert "identity_reference" in understanding.signals
    assert "relationship_reference" in understanding.signals


def test_sentence_understanding_requires_matching_anchor() -> None:
    """Sentence analysis must remain tied to the exact source evidence anchor."""
    sentence = ImportedSentence(
        sentence_id="source_demo_chapter_001_scene_001_paragraph_001_sentence_001",
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        sentence_index=1,
        text="Mark lifted the sword.",
    )
    anchor = EvidenceAnchor(
        anchor_id="source_demo_chapter_001_scene_001_paragraph_001_sentence_002_anchor",
        source_id="source_demo",
        chapter_id="source_demo_chapter_001",
        scene_id="source_demo_chapter_001_scene_001",
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        sentence_id="source_demo_chapter_001_scene_001_paragraph_001_sentence_002",
        paragraph_index=1,
        sentence_index=2,
        quote="Different sentence.",
    )

    with pytest.raises(ValueError, match="anchor must match sentence ID"):
        SentenceUnderstandingEngine().analyze_sentence(sentence=sentence, anchor=anchor)

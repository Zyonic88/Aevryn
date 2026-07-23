"""Tests for the Sentence Understanding boundary."""

from dataclasses import replace

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


def test_sentence_understanding_does_not_treat_ordinary_item_use_as_skill() -> None:
    """Using an object is action plus item context, not automatically a skill."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_item_use",
        title="Sentence Item Use",
        text="Chapter 1\nCharlotte used the iron sword.",
    )

    understanding = SentenceUnderstandingEngine().analyze_imported_source(imported)[0]

    assert "action" in understanding.signals
    assert "item_reference" in understanding.signals
    assert "skill_reference" not in understanding.signals
    assert understanding.review_required is False


def test_sentence_understanding_detects_system_ui_phrases() -> None:
    """System interface phrases should be recognized as system context."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_system_phrases",
        title="Sentence System Phrases",
        text="Chapter 1\nA blue status panel opened and displayed a quest reward.",
    )

    understanding = SentenceUnderstandingEngine().analyze_imported_source(imported)[0]

    assert "system_reference" in understanding.signals
    assert "status panel" in understanding.cue_terms
    assert "quest reward" in understanding.cue_terms


def test_sentence_understanding_keeps_system_rewards_out_of_skill_context() -> None:
    """Quest, mission, points, and reward language are system context, not abilities."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_system_rewards",
        title="Sentence System Rewards",
        text="Chapter 1\nThe mission reward gave Zhao Chen 100 system points.",
    )

    understanding = SentenceUnderstandingEngine().analyze_imported_source(imported)[0]

    assert "system_reference" in understanding.signals
    assert "skill_reference" not in understanding.signals
    assert "mission reward" in understanding.cue_terms
    assert "points" in understanding.cue_terms
    assert understanding.review_required is True


def test_sentence_understanding_treats_skill_phrase_as_skill_context() -> None:
    """An item-like word inside a skill phrase should not become a separate item."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_skill_phrase",
        title="Sentence Skill Phrase",
        text="Chapter 1\nCharlotte practiced the Moon Shadow sword technique.",
    )

    understanding = SentenceUnderstandingEngine().analyze_imported_source(imported)[0]

    assert "skill_reference" in understanding.signals
    assert "sword technique" in understanding.cue_terms
    assert "item_reference" not in understanding.signals
    assert understanding.review_required is False


def test_sentence_understanding_keeps_separate_item_and_skill_reviewable() -> None:
    """Separate item and skill cues should still route to review."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_separate_item_skill",
        title="Sentence Separate Item Skill",
        text="Chapter 1\nCharlotte raised her sword and prepared a technique.",
    )

    understanding = SentenceUnderstandingEngine().analyze_imported_source(imported)[0]

    assert "item_reference" in understanding.signals
    assert "skill_reference" in understanding.signals
    assert understanding.review_required is True


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


def test_sentence_understanding_detects_location_and_organization_language() -> None:
    """World-routing cues should surface places and institutions without deciding Canon."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_world_context",
        title="Sentence World Context",
        text=(
            "Chapter 1\n"
            "Zhao Chen stood inside the North Star Academy classroom while the "
            "Starlight Empire fleet waited."
        ),
    )

    understanding = SentenceUnderstandingEngine().analyze_imported_source(imported)[0]

    assert "location_reference" in understanding.signals
    assert "organization_reference" in understanding.signals
    assert "north star academy" in understanding.cue_terms
    assert "classroom" in understanding.cue_terms
    assert "starlight empire" in understanding.cue_terms
    assert "fleet" in understanding.cue_terms


def test_sentence_understanding_keeps_location_and_organization_metadata_compact() -> None:
    """World-routing metadata should not carry full manuscript prose."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_world_privacy",
        title="Sentence World Privacy",
        text="Chapter 1\nThe captain walked through the academy hall.",
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

    assert "location_reference" in understanding.signals
    assert "organization_reference" in understanding.signals
    assert all("captain walked through" not in value for value in serialized_values)


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


def test_sentence_understanding_rejects_import_without_sentence_anchor() -> None:
    """Every analyzed sentence must have its own evidence anchor."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_missing_anchor",
        title="Sentence Missing Anchor",
        text="Chapter 1\nMark lifted the sword.",
    )
    imported_without_anchor = replace(imported, anchors=())

    with pytest.raises(ValueError, match="without evidence anchor"):
        SentenceUnderstandingEngine().analyze_imported_source(imported_without_anchor)


def test_sentence_understanding_rejects_duplicate_sentence_anchors() -> None:
    """Sentence analysis requires one stable anchor per sentence."""
    imported = StoryImporter().import_text(
        source_id="source_sentence_duplicate_anchor",
        title="Sentence Duplicate Anchor",
        text="Chapter 1\nMark lifted the sword.",
    )
    first_anchor = imported.anchors[0]
    duplicate_anchor = replace(
        first_anchor,
        anchor_id=(
            "source_sentence_duplicate_anchor_chapter_001_scene_001_"
            "paragraph_001_sentence_001_duplicate_anchor"
        ),
    )
    imported_with_duplicate_anchor = replace(
        imported,
        anchors=(first_anchor, duplicate_anchor),
    )

    with pytest.raises(ValueError, match="one anchor per sentence"):
        SentenceUnderstandingEngine().analyze_imported_source(
            imported_with_duplicate_anchor
        )

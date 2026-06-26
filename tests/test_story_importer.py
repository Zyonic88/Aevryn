"""Tests for Phase 3 Story Import."""

import logging
from typing import Any, cast

import pytest

from scenesmith import (
    EvidenceAnchor,
    ImportedSentence,
    ImportedSource,
    SourceParagraph,
    StoryImporter,
)
from scenesmith.core import Chapter, Scene, Story


def imported_source_with_anchor(anchor: EvidenceAnchor) -> ImportedSource:
    """Build a minimal imported source around one paragraph and anchor."""
    story = Story(
        story_id="source_demo",
        title="Demo",
        chapters=(
            Chapter(
                chapter_id="source_demo_chapter_001",
                story_id="source_demo",
                chapter_index=1,
                title="Chapter 1",
                scenes=(
                    Scene(
                        scene_id="source_demo_chapter_001_scene_001",
                        chapter_id="source_demo_chapter_001",
                        scene_index=1,
                        title="Scene 1",
                    ),
                ),
            ),
        ),
    )
    sentence = ImportedSentence(
        sentence_id="source_demo_chapter_001_scene_001_paragraph_001_sentence_001",
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        sentence_index=1,
        text="Mark woke up.",
    )
    paragraph = SourceParagraph(
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        scene_id="source_demo_chapter_001_scene_001",
        paragraph_index=1,
        text="Mark woke up.",
        sentences=(sentence,),
    )
    return ImportedSource(
        source_id="source_demo",
        title="Demo",
        story=story,
        paragraphs=(paragraph,),
        anchors=(anchor,),
    )


def demo_anchor(**overrides: object) -> EvidenceAnchor:
    """Build a valid demo evidence anchor with selected field overrides."""
    values = {
        "anchor_id": "source_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
        "source_id": "source_demo",
        "chapter_id": "source_demo_chapter_001",
        "scene_id": "source_demo_chapter_001_scene_001",
        "paragraph_id": "source_demo_chapter_001_scene_001_paragraph_001",
        "sentence_id": "source_demo_chapter_001_scene_001_paragraph_001_sentence_001",
        "paragraph_index": 1,
        "sentence_index": 1,
        "quote": "Mark woke up.",
    }
    values.update(overrides)
    return EvidenceAnchor(**values)  # type: ignore[arg-type]


def test_import_text_splits_chapters_scenes_paragraphs_and_sentences() -> None:
    """Story Import creates stable structure and evidence anchors."""
    importer = StoryImporter()
    text = """Chapter 1
Mark woke up. He held a rusty dagger.

The room was cold.
---
Luna entered. She smiled.

Chapter 2
Scene: Market
Mark bought an iron sword."""

    imported = importer.import_text(
        source_id="source_demo",
        title="Demo Story",
        text=text,
    )

    assert imported.story.story_id == "source_demo"
    assert len(imported.story.chapters) == 2
    assert imported.story.chapters[0].chapter_id == "source_demo_chapter_001"
    assert imported.story.chapters[0].scenes[0].scene_id == (
        "source_demo_chapter_001_scene_001"
    )
    assert imported.story.chapters[0].scenes[1].scene_index == 2
    assert imported.paragraphs[0].paragraph_id == (
        "source_demo_chapter_001_scene_001_paragraph_001"
    )
    assert imported.paragraphs[0].sentences[0].sentence_id == (
        "source_demo_chapter_001_scene_001_paragraph_001_sentence_001"
    )
    assert imported.paragraphs[0].sentences[1].text == "He held a rusty dagger."
    assert imported.anchors[1].quote == "He held a rusty dagger."
    assert imported.anchors[1].paragraph_index == 1
    assert imported.anchors[1].sentence_index == 2


def test_import_text_derives_paragraphs_from_long_unspaced_chapter() -> None:
    """Story Import creates readable paragraphs from oversized source blocks."""
    importer = StoryImporter()
    sentences = [f"Sentence {index} describes the scene." for index in range(1, 15)]

    imported = importer.import_text(
        source_id="source_unspaced",
        title="Unspaced Story",
        text="Chapter 1\n" + " ".join(sentences),
    )

    scene = imported.story.chapters[0].scenes[0]
    assert len(scene.paragraphs) > 1
    assert len(imported.anchors) == len(sentences)
    assert imported.anchors[0].quote == "Sentence 1 describes the scene."
    assert imported.anchors[-1].quote == "Sentence 14 describes the scene."


def test_import_text_derives_paragraph_break_before_interface_lines() -> None:
    """System-style interface text starts a derived paragraph."""
    importer = StoryImporter()
    text = (
        "Chapter 1\n"
        "Liu Feng sat alone. He closed his eyes. Energy gathered around him. "
        "The room became quiet. His pulse slowed. His thoughts sharpened. "
        "\u3010Trait: Amplification (White)\u3011 "
        "He stared at the text. He took a breath. He made his decision."
    )

    imported = importer.import_text(
        source_id="source_interface",
        title="Interface Story",
        text=text,
    )

    paragraphs = imported.story.chapters[0].scenes[0].paragraphs
    assert any(paragraph.startswith("\u3010Trait:") for paragraph in paragraphs)
    assert imported.anchors[6].quote == "\u3010Trait: Amplification (White)\u3011"


def test_import_text_does_not_split_sentences_on_decimals_or_titles() -> None:
    """Sentence structure keeps decimals, titles, and numbered names intact."""
    importer = StoryImporter()

    imported = importer.import_text(
        source_id="source_sentence_structure",
        title="Sentence Structure Story",
        text=(
            "Chapter 1\n"
            "City No. 1 High School opened the ceremony. "
            "Mr. Li announced a 0.5x Amplification Trait. "
            "Liu Feng listened."
        ),
    )

    assert [anchor.quote for anchor in imported.anchors] == [
        "City No. 1 High School opened the ceremony.",
        "Mr. Li announced a 0.5x Amplification Trait.",
        "Liu Feng listened.",
    ]


def test_import_text_without_markers_preserves_single_chapter_and_scene() -> None:
    """Story Import preserves ambiguous structure instead of guessing."""
    importer = StoryImporter()

    imported = importer.import_text(
        source_id="source_single",
        title="Single Scene",
        text="Mark walked alone. The forest was silent.",
    )

    assert len(imported.story.chapters) == 1
    assert len(imported.story.chapters[0].scenes) == 1
    assert imported.story.chapters[0].title == "Chapter 1"
    assert imported.story.chapters[0].scenes[0].title == "Scene 1"
    assert len(imported.anchors) == 2


def test_import_text_supports_markdown_chapter_headings() -> None:
    """Markdown-style chapter headings are accepted."""
    importer = StoryImporter()
    text = """# Chapter 1
Opening sentence.

# Chapter 2
Second chapter sentence."""

    imported = importer.import_text(
        source_id="source_markdown",
        title="Markdown Story",
        text=text,
    )

    assert len(imported.story.chapters) == 2
    assert imported.story.chapters[1].title == "Chapter 2"


def test_import_text_supports_numbered_title_chapter_headings() -> None:
    """Numbered web-novel title lines create chapter boundaries."""
    importer = StoryImporter()
    text = """#1The system is messing up
Chapter 1: The System Is Making Trouble
Zhao Chen opened his eyes.

#2A starfleet that can only recruit female soldiers?
Chapter 2: A Starfleet That Can Only Recruit Female Soldiers?
The cursor stopped on option two."""

    imported = importer.import_text(
        source_id="starfleet",
        title="Web Novel",
        text=text,
    )

    assert len(imported.story.chapters) == 2
    assert imported.story.chapters[0].chapter_id == "starfleet_chapter_001"
    assert imported.story.chapters[1].chapter_id == "starfleet_chapter_002"
    assert imported.story.chapters[0].title == "Chapter 1: The System Is Making Trouble"
    assert imported.story.chapters[1].title == (
        "Chapter 2: A Starfleet That Can Only Recruit Female Soldiers?"
    )
    assert imported.story.chapters[1].scenes[0].scene_id == (
        "starfleet_chapter_002_scene_001"
    )


def test_import_text_preface_before_first_heading_does_not_shift_chapter_index() -> None:
    """Text before the first explicit chapter heading stays in chapter one."""
    importer = StoryImporter()
    text = """Story Title

Chapter 1: The System Is Making Trouble
Zhao Chen opened his eyes."""

    imported = importer.import_text(
        source_id="source_preface",
        title="Preface Story",
        text=text,
    )

    assert len(imported.story.chapters) == 1
    assert imported.story.chapters[0].chapter_index == 1
    assert imported.story.chapters[0].chapter_id == "source_preface_chapter_001"
    assert imported.story.chapters[0].title == "Chapter 1: The System Is Making Trouble"
    assert "Story Title" in imported.story.chapters[0].scenes[0].paragraphs[0]


def test_import_text_single_explicit_chapter_preserves_heading_index() -> None:
    """A standalone Chapter 2 file keeps chapter index 2."""
    importer = StoryImporter()
    text = """Chapter 2: A Starfleet That Can Only Recruit Female Soldiers?
Zhao Chen opened the system panel."""

    imported = importer.import_text(
        source_id="source_standalone",
        title="Standalone Chapter",
        text=text,
    )

    assert len(imported.story.chapters) == 1
    assert imported.story.chapters[0].chapter_index == 2
    assert imported.story.chapters[0].chapter_id == "source_standalone_chapter_002"
    assert imported.story.chapters[0].scenes[0].scene_id == (
        "source_standalone_chapter_002_scene_001"
    )


def test_import_text_rejects_out_of_order_explicit_chapters() -> None:
    """Story Import rejects multi-chapter sources that move backward."""
    importer = StoryImporter()
    text = """Chapter 3
Third chapter text.

Chapter 1
First chapter text.

Chapter 2
Second chapter text."""

    with pytest.raises(ValueError, match="increasing order"):
        importer.import_text(
            source_id="source_out_of_order",
            title="Out of Order Story",
            text=text,
        )


def test_import_text_repairs_common_utf8_mojibake() -> None:
    """Story Import repairs common UTF-8 text decoded as Windows-1252."""
    importer = StoryImporter()

    imported = importer.import_text(
        source_id="source_encoding",
        title="Encoding Story",
        text="Chapter 1\nZhao Chen saw his fianc\u00c3\u0192\u00c2\u00a9e.",
    )

    assert imported.anchors[0].quote == "Zhao Chen saw his fiancée."


def test_import_text_repairs_single_layer_utf8_mojibake() -> None:
    """Story Import repairs single-layer UTF-8 mojibake."""
    importer = StoryImporter()

    imported = importer.import_text(
        source_id="source_single_encoding",
        title="Encoding Story",
        text="Chapter 3: The Useless Baron's Fianc\u00c3\u00a9e\nZhao Chen walked.",
    )

    assert imported.story.chapters[0].title == "Chapter 3: The Useless Baron's Fiancée"


def test_import_text_repairs_mojibake_cjk_brackets() -> None:
    """Story Import repairs common Chinese bracket mojibake."""
    importer = StoryImporter()

    imported = importer.import_text(
        source_id="source_brackets",
        title="Bracket Story",
        text=(
            "Chapter 1\n"
            "\u00e3\u20ac\u0090Random selection starting...\u00e3\u20ac\u0091"
        ),
    )

    assert imported.anchors[0].quote == "\u3010Random selection starting...\u3011"


def test_import_text_rejects_empty_input() -> None:
    """Story Import rejects empty source data."""
    importer = StoryImporter()

    with pytest.raises(ValueError, match="Source text is required"):
        importer.import_text(source_id="source_empty", title="Empty", text=" ")

    with pytest.raises(ValueError, match="Source text is required"):
        importer.import_text(
            source_id="source_empty",
            title="Empty",
            text=cast(Any, 42),
        )


def test_import_text_trims_source_id_and_title() -> None:
    """Story Import trims source metadata before building stable IDs."""
    importer = StoryImporter()

    imported = importer.import_text(
        source_id=" source_trimmed ",
        title=" Trimmed Story ",
        text="Chapter 1\nMark woke up.",
    )

    assert imported.source_id == "source_trimmed"
    assert imported.title == "Trimmed Story"
    assert imported.story.story_id == "source_trimmed"
    assert imported.anchors[0].anchor_id.startswith("source_trimmed_chapter_001")


def test_import_text_rejects_source_id_whitespace() -> None:
    """Source IDs are machine tokens because they become evidence anchor IDs."""
    importer = StoryImporter()

    with pytest.raises(ValueError, match="Source ID cannot contain whitespace"):
        importer.import_text(
            source_id="source demo",
            title="Demo",
            text="Chapter 1\nMark woke up.",
        )


def test_imported_sentence_rejects_invalid_source_indexes() -> None:
    """Imported sentence indexes are one-based source references."""
    with pytest.raises(ValueError, match="Sentence index must be at least 1"):
        ImportedSentence(
            sentence_id="source_chapter_001_scene_001_paragraph_001_sentence_000",
            paragraph_id="source_chapter_001_scene_001_paragraph_001",
            sentence_index=0,
            text="Mark woke up.",
        )

    with pytest.raises(ValueError, match="Sentence index must be at least 1"):
        ImportedSentence(
            sentence_id="source_chapter_001_scene_001_paragraph_001_sentence_001",
            paragraph_id="source_chapter_001_scene_001_paragraph_001",
            sentence_index=True,
            text="Mark woke up.",
        )

    with pytest.raises(ValueError, match="Sentence index must be at least 1"):
        ImportedSentence(
            sentence_id="source_chapter_001_scene_001_paragraph_001_sentence_001",
            paragraph_id="source_chapter_001_scene_001_paragraph_001",
            sentence_index=cast(Any, "1"),
            text="Mark woke up.",
        )


def test_source_paragraph_rejects_machine_id_whitespace() -> None:
    """Paragraph IDs cannot contain whitespace because anchors depend on them."""
    with pytest.raises(ValueError, match="Paragraph ID cannot contain whitespace"):
        SourceParagraph(
            paragraph_id="paragraph 001",
            scene_id="source_chapter_001_scene_001",
            paragraph_index=1,
            text="Mark woke up.",
            sentences=(),
        )


def test_evidence_anchor_rejects_boolean_source_index() -> None:
    """Evidence anchors require real one-based source indexes."""
    with pytest.raises(ValueError, match="Evidence paragraph index must be at least 1"):
        EvidenceAnchor(
            anchor_id="source_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
            source_id="source",
            chapter_id="source_chapter_001",
            scene_id="source_chapter_001_scene_001",
            paragraph_id="source_chapter_001_scene_001_paragraph_001",
            sentence_id="source_chapter_001_scene_001_paragraph_001_sentence_001",
            paragraph_index=True,
            sentence_index=1,
            quote="Mark woke up.",
        )


def test_source_paragraph_rejects_sentence_parent_mismatch() -> None:
    """Paragraph sentence lists must reference the owning paragraph."""
    sentence = ImportedSentence(
        sentence_id="source_chapter_001_scene_001_paragraph_002_sentence_001",
        paragraph_id="source_chapter_001_scene_001_paragraph_002",
        sentence_index=1,
        text="Mark woke up.",
    )

    with pytest.raises(ValueError, match="reference the paragraph ID"):
        SourceParagraph(
            paragraph_id="source_chapter_001_scene_001_paragraph_001",
            scene_id="source_chapter_001_scene_001",
            paragraph_index=1,
            text="Mark woke up.",
            sentences=(sentence,),
        )


def test_source_paragraph_rejects_untraceable_sentence_text() -> None:
    """Paragraph sentences must be traceable to the paragraph source text."""
    sentence = ImportedSentence(
        sentence_id="source_chapter_001_scene_001_paragraph_001_sentence_001",
        paragraph_id="source_chapter_001_scene_001_paragraph_001",
        sentence_index=1,
        text="Mark drew a sword.",
    )

    with pytest.raises(ValueError, match="traceable to paragraph text"):
        SourceParagraph(
            paragraph_id="source_chapter_001_scene_001_paragraph_001",
            scene_id="source_chapter_001_scene_001",
            paragraph_index=1,
            text="Mark woke up.",
            sentences=(sentence,),
        )


def test_evidence_anchor_rejects_empty_quote() -> None:
    """Evidence anchors must preserve source text for canon proof."""
    with pytest.raises(ValueError, match="Evidence quote is required"):
        EvidenceAnchor(
            anchor_id="source_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
            source_id="source",
            chapter_id="source_chapter_001",
            scene_id="source_chapter_001_scene_001",
            paragraph_id="source_chapter_001_scene_001_paragraph_001",
            sentence_id="source_chapter_001_scene_001_paragraph_001_sentence_001",
            paragraph_index=1,
            sentence_index=1,
            quote=" ",
        )


def test_imported_source_rejects_story_source_mismatch() -> None:
    """Imported source identity must match the imported story."""
    story = Story(story_id="story_demo", title="Demo")

    with pytest.raises(ValueError, match="must match story ID"):
        ImportedSource(
            source_id="source_demo",
            title="Demo",
            story=story,
            paragraphs=(),
            anchors=(),
        )


def test_imported_source_rejects_unknown_paragraph_anchor() -> None:
    """Evidence anchors must point to imported paragraphs and sentences."""
    story = Story(
        story_id="source_demo",
        title="Demo",
        chapters=(
            Chapter(
                chapter_id="source_demo_chapter_001",
                story_id="source_demo",
                chapter_index=1,
                title="Chapter 1",
                scenes=(
                    Scene(
                        scene_id="source_demo_chapter_001_scene_001",
                        chapter_id="source_demo_chapter_001",
                        scene_index=1,
                        title="Scene 1",
                    ),
                ),
            ),
        ),
    )
    anchor = EvidenceAnchor(
        anchor_id="source_demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor",
        source_id="source_demo",
        chapter_id="source_demo_chapter_001",
        scene_id="source_demo_chapter_001_scene_001",
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        sentence_id="source_demo_chapter_001_scene_001_paragraph_001_sentence_001",
        paragraph_index=1,
        sentence_index=1,
        quote="Mark woke up.",
    )

    with pytest.raises(ValueError, match="unknown paragraph"):
        ImportedSource(
            source_id="source_demo",
            title="Demo",
            story=story,
            paragraphs=(),
            anchors=(anchor,),
        )


def test_imported_source_rejects_unknown_chapter_anchor() -> None:
    """Evidence anchors must reference known imported chapters."""
    with pytest.raises(ValueError, match="unknown chapter"):
        imported_source_with_anchor(
            demo_anchor(chapter_id="source_demo_chapter_999"),
        )


def test_imported_source_rejects_unknown_scene_anchor() -> None:
    """Evidence anchors must reference known imported scenes."""
    with pytest.raises(ValueError, match="unknown scene"):
        imported_source_with_anchor(
            demo_anchor(scene_id="source_demo_chapter_001_scene_999"),
        )


def test_imported_source_rejects_anchor_scene_chapter_mismatch() -> None:
    """Evidence anchors must keep chapter metadata aligned with scenes."""
    story = Story(
        story_id="source_demo",
        title="Demo",
        chapters=(
            Chapter(
                chapter_id="source_demo_chapter_001",
                story_id="source_demo",
                chapter_index=1,
                title="Chapter 1",
                scenes=(
                    Scene(
                        scene_id="source_demo_chapter_001_scene_001",
                        chapter_id="source_demo_chapter_001",
                        scene_index=1,
                        title="Scene 1",
                    ),
                ),
            ),
            Chapter(
                chapter_id="source_demo_chapter_002",
                story_id="source_demo",
                chapter_index=2,
                title="Chapter 2",
                scenes=(
                    Scene(
                        scene_id="source_demo_chapter_002_scene_001",
                        chapter_id="source_demo_chapter_002",
                        scene_index=1,
                        title="Scene 1",
                    ),
                ),
            ),
        ),
    )
    sentence = ImportedSentence(
        sentence_id="source_demo_chapter_002_scene_001_paragraph_001_sentence_001",
        paragraph_id="source_demo_chapter_002_scene_001_paragraph_001",
        sentence_index=1,
        text="Mark woke up.",
    )
    paragraph = SourceParagraph(
        paragraph_id="source_demo_chapter_002_scene_001_paragraph_001",
        scene_id="source_demo_chapter_002_scene_001",
        paragraph_index=1,
        text="Mark woke up.",
        sentences=(sentence,),
    )

    with pytest.raises(ValueError, match="scene must belong"):
        ImportedSource(
            source_id="source_demo",
            title="Demo",
            story=story,
            paragraphs=(paragraph,),
            anchors=(
                EvidenceAnchor(
                    anchor_id=(
                        "source_demo_chapter_002_scene_001_paragraph_001_"
                        "sentence_001_anchor"
                    ),
                    source_id="source_demo",
                    chapter_id="source_demo_chapter_001",
                    scene_id="source_demo_chapter_002_scene_001",
                    paragraph_id="source_demo_chapter_002_scene_001_paragraph_001",
                    sentence_id=(
                        "source_demo_chapter_002_scene_001_paragraph_001_"
                        "sentence_001"
                    ),
                    paragraph_index=1,
                    sentence_index=1,
                    quote="Mark woke up.",
                ),
            ),
        )


def test_imported_source_rejects_anchor_scene_paragraph_mismatch() -> None:
    """Evidence anchors must keep scene metadata aligned with paragraphs."""
    story = Story(
        story_id="source_demo",
        title="Demo",
        chapters=(
            Chapter(
                chapter_id="source_demo_chapter_001",
                story_id="source_demo",
                chapter_index=1,
                title="Chapter 1",
                scenes=(
                    Scene(
                        scene_id="source_demo_chapter_001_scene_001",
                        chapter_id="source_demo_chapter_001",
                        scene_index=1,
                        title="Scene 1",
                    ),
                    Scene(
                        scene_id="source_demo_chapter_001_scene_002",
                        chapter_id="source_demo_chapter_001",
                        scene_index=2,
                        title="Scene 2",
                    ),
                ),
            ),
        ),
    )
    sentence = ImportedSentence(
        sentence_id="source_demo_chapter_001_scene_001_paragraph_001_sentence_001",
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        sentence_index=1,
        text="Mark woke up.",
    )
    paragraph = SourceParagraph(
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        scene_id="source_demo_chapter_001_scene_001",
        paragraph_index=1,
        text="Mark woke up.",
        sentences=(sentence,),
    )

    with pytest.raises(ValueError, match="scene must match"):
        ImportedSource(
            source_id="source_demo",
            title="Demo",
            story=story,
            paragraphs=(paragraph,),
            anchors=(
                demo_anchor(scene_id="source_demo_chapter_001_scene_002"),
            ),
        )


def test_imported_source_rejects_anchor_sentence_paragraph_mismatch() -> None:
    """Evidence anchors must keep sentence metadata aligned with paragraphs."""
    first_sentence = ImportedSentence(
        sentence_id="source_demo_chapter_001_scene_001_paragraph_001_sentence_001",
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        sentence_index=1,
        text="Mark woke up.",
    )
    first_paragraph = SourceParagraph(
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        scene_id="source_demo_chapter_001_scene_001",
        paragraph_index=1,
        text="Mark woke up.",
        sentences=(first_sentence,),
    )
    second_sentence = ImportedSentence(
        sentence_id="source_demo_chapter_001_scene_001_paragraph_002_sentence_001",
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_002",
        sentence_index=1,
        text="Mark walked.",
    )
    second_paragraph = SourceParagraph(
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_002",
        scene_id="source_demo_chapter_001_scene_001",
        paragraph_index=2,
        text="Mark walked.",
        sentences=(second_sentence,),
    )
    story = Story(
        story_id="source_demo",
        title="Demo",
        chapters=(
            Chapter(
                chapter_id="source_demo_chapter_001",
                story_id="source_demo",
                chapter_index=1,
                title="Chapter 1",
                scenes=(
                    Scene(
                        scene_id="source_demo_chapter_001_scene_001",
                        chapter_id="source_demo_chapter_001",
                        scene_index=1,
                        title="Scene 1",
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="sentence must belong"):
        ImportedSource(
            source_id="source_demo",
            title="Demo",
            story=story,
            paragraphs=(first_paragraph, second_paragraph),
            anchors=(demo_anchor(sentence_id=second_sentence.sentence_id),),
        )


def test_imported_source_rejects_duplicate_scene_paragraph_indexes() -> None:
    """Paragraph indexes must be unique inside a scene source map."""
    first_sentence = ImportedSentence(
        sentence_id="source_demo_chapter_001_scene_001_paragraph_001_sentence_001",
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        sentence_index=1,
        text="Mark woke up.",
    )
    second_sentence = ImportedSentence(
        sentence_id="source_demo_chapter_001_scene_001_paragraph_002_sentence_001",
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_002",
        sentence_index=1,
        text="Mark stood up.",
    )
    first_paragraph = SourceParagraph(
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_001",
        scene_id="source_demo_chapter_001_scene_001",
        paragraph_index=1,
        text="Mark woke up.",
        sentences=(first_sentence,),
    )
    second_paragraph = SourceParagraph(
        paragraph_id="source_demo_chapter_001_scene_001_paragraph_002",
        scene_id="source_demo_chapter_001_scene_001",
        paragraph_index=1,
        text="Mark stood up.",
        sentences=(second_sentence,),
    )
    story = Story(
        story_id="source_demo",
        title="Demo",
        chapters=(
            Chapter(
                chapter_id="source_demo_chapter_001",
                story_id="source_demo",
                chapter_index=1,
                title="Chapter 1",
                scenes=(
                    Scene(
                        scene_id="source_demo_chapter_001_scene_001",
                        chapter_id="source_demo_chapter_001",
                        scene_index=1,
                        title="Scene 1",
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="duplicate paragraph indexes"):
        ImportedSource(
            source_id="source_demo",
            title="Demo",
            story=story,
            paragraphs=(first_paragraph, second_paragraph),
            anchors=(),
        )


def test_imported_source_rejects_anchor_paragraph_index_mismatch() -> None:
    """Evidence anchors must keep paragraph indexes aligned with paragraphs."""
    with pytest.raises(ValueError, match="paragraph index must match"):
        imported_source_with_anchor(demo_anchor(paragraph_index=2))


def test_imported_source_rejects_anchor_sentence_index_mismatch() -> None:
    """Evidence anchors must keep sentence indexes aligned with sentences."""
    with pytest.raises(ValueError, match="sentence index must match"):
        imported_source_with_anchor(demo_anchor(sentence_index=2))


def test_imported_source_rejects_anchor_quote_mismatch() -> None:
    """Evidence anchor quotes must match imported sentence text exactly."""
    with pytest.raises(ValueError, match="quote must match"):
        imported_source_with_anchor(demo_anchor(quote="Mark stood up."))


def test_import_text_logs_import_summary(caplog: pytest.LogCaptureFixture) -> None:
    """Story Import logs source structure counts."""
    importer = StoryImporter()

    with caplog.at_level(logging.INFO, logger="scenesmith.importing.engine"):
        importer.import_text(
            source_id="source_logging",
            title="Logging Story",
            text="Chapter 1\nMark woke up.",
        )

    assert "Imported source" in caplog.text

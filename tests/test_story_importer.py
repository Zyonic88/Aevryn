"""Tests for Phase 3 Story Import."""

import logging

import pytest

from scenesmith import StoryImporter


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

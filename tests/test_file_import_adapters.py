"""Tests for non-EPUB source file adapters."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from aevryn.projects import AevrynProjectRunner


def test_markdown_import_preserves_headings() -> None:
    """Markdown files are treated as readable text for Story Import."""
    path = write_file(
        "chapter.md",
        "# Chapter 1\n\nIshmael wrote in **bold** markdown.",
    )

    imported = AevrynProjectRunner().import_text_file(
        path=path,
        source_id="markdown_story",
    )

    assert imported.story.chapters[0].title == "Chapter 1"
    assert imported.anchors[0].quote == "Ishmael wrote in **bold** markdown."


def test_html_import_extracts_visible_text() -> None:
    """HTML import extracts visible story text and skips nav/script/style."""
    path = write_file(
        "chapter.html",
        (
            "<html><body><nav>Skip CHAPTER 99.</nav>"
            "<h1>CHAPTER 1. Loomings.</h1>"
            "<p>Call me Ishmael.</p>"
            "<script>skip()</script></body></html>"
        ),
    )

    imported = AevrynProjectRunner().import_text_file(
        path=path,
        source_id="html_story",
    )

    assert imported.story.chapters[0].title == "CHAPTER 1. Loomings."
    assert [anchor.quote for anchor in imported.anchors] == ["Call me Ishmael."]


def test_fb2_import_extracts_paragraph_text() -> None:
    """FB2 import extracts paragraph-like XML text."""
    path = write_file(
        "chapter.fb2",
        (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">'
            "<body><section><title><p>CHAPTER 1. Loomings.</p></title>"
            "<p>Call me Ishmael.</p></section></body></FictionBook>"
        ),
    )

    imported = AevrynProjectRunner().import_text_file(
        path=path,
        source_id="fb2_story",
    )

    assert imported.story.chapters[0].title == "CHAPTER 1. Loomings."
    assert imported.anchors[0].quote == "Call me Ishmael."


def test_docx_import_extracts_paragraph_text() -> None:
    """DOCX import extracts word/document.xml paragraph text."""
    path = Path("build") / "test_file_import_adapters" / "chapter.docx"
    path.parent.mkdir(parents=True, exist_ok=True)
    document = (
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p><w:r><w:t>CHAPTER 1. Loomings.</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Call me Ishmael.</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)

    imported = AevrynProjectRunner().import_text_file(
        path=path,
        source_id="docx_story",
    )

    assert imported.story.chapters[0].title == "CHAPTER 1. Loomings."
    assert imported.anchors[0].quote == "Call me Ishmael."


def test_odt_import_extracts_paragraph_text() -> None:
    """ODT import extracts content.xml heading and paragraph text."""
    path = Path("build") / "test_file_import_adapters" / "chapter.odt"
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        '<office:document-content '
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
        "<office:body><office:text>"
        "<text:h>CHAPTER 1. Loomings.</text:h>"
        "<text:p>Call me Ishmael.</text:p>"
        "</office:text></office:body></office:document-content>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("content.xml", content)

    imported = AevrynProjectRunner().import_text_file(
        path=path,
        source_id="odt_story",
    )

    assert imported.story.chapters[0].title == "CHAPTER 1. Loomings."
    assert imported.anchors[0].quote == "Call me Ishmael."


@pytest.mark.parametrize("suffix", [".pdf", ".mobi", ".azw3"])
def test_binary_formats_fail_with_clear_dependency_message(suffix: str) -> None:
    """Binary formats that need dedicated parsers fail clearly in V1.1."""
    path = write_file(f"chapter{suffix}", "binary placeholder")

    with pytest.raises(ValueError, match="requires a dedicated parser dependency"):
        AevrynProjectRunner().import_text_file(
            path=path,
            source_id="unsupported_story",
        )


def write_file(filename: str, text: str) -> Path:
    """Write a UTF-8 test source file."""
    path = Path("build") / "test_file_import_adapters" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path

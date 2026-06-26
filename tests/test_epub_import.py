"""Tests for EPUB Story Import adapter behavior."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from scenesmith.importing import EpubTextExtractor
from scenesmith.projects import SceneSmithProjectRunner


def test_epub_extractor_uses_spine_text_and_excludes_navigation() -> None:
    """EPUB extraction prepares clean spine text for Story Import."""
    epub_path = build_epub(
        "navigation_trim.epub",
        {
            "toc.xhtml": (
                "<html><body><nav><ol>"
                "<li>CHAPTER 1. Navigation Only.</li>"
                "<li>CHAPTER 2. Navigation Only.</li>"
                "</ol></nav></body></html>"
            ),
            "chapter.xhtml": (
                "<html><body>"
                "<p>CHAPTER 1. Loomings.</p>"
                "<p>Call me Ishmael.</p>"
                "<p>The sea was blue\u2014very blue.</p>"
                "</body></html>"
            ),
        },
        spine_ids=("toc", "chapter"),
        nav_id="toc",
    )

    extracted = EpubTextExtractor().extract_path(epub_path)

    assert "Navigation Only" not in extracted.text
    assert "CHAPTER 1. Loomings." in extracted.text
    assert "blue\u2014very blue" in extracted.text
    assert extracted.spine_document_count == 1


def test_epub_extractor_trims_leading_chapter_list_reset() -> None:
    """Leading TOC-like chapter lists are removed when real chapters restart."""
    epub_path = build_epub(
        "chapter_list_reset.epub",
        {
            "chapter.xhtml": (
                "<html><body>"
                "<p>CHAPTER 1. Listed.</p>"
                "<p>CHAPTER 2. Listed.</p>"
                "<p>CHAPTER 1. Real Opening.</p>"
                "<p>Ishmael entered the inn.</p>"
                "<p>CHAPTER 2. Real Next.</p>"
                "<p>Queequeg arrived.</p>"
                "</body></html>"
            ),
        },
        spine_ids=("chapter",),
    )

    extracted = EpubTextExtractor().extract_path(epub_path)
    imported = SceneSmithProjectRunner().import_text_file(
        path=epub_path,
        source_id="moby_demo",
    )

    assert extracted.trimmed_navigation_lines > 0
    assert "CHAPTER 1. Listed." not in extracted.text
    assert imported.story.chapters[0].title == "CHAPTER 1. Real Opening."
    assert imported.story.chapters[1].title == "CHAPTER 2. Real Next."


def test_epub_import_is_deterministic() -> None:
    """The same EPUB imported twice produces the same structure and anchors."""
    epub_path = build_epub(
        "deterministic.epub",
        {
            "chapter.xhtml": (
                "<html><body>"
                "<p>CHAPTER 1. Loomings.</p>"
                "<p>Call me Ishmael. He watched the sea.</p>"
                "</body></html>"
            ),
        },
        spine_ids=("chapter",),
    )
    runner = SceneSmithProjectRunner()

    first = runner.import_text_file(path=epub_path, source_id="deterministic")
    second = runner.import_text_file(path=epub_path, source_id="deterministic")

    assert len(first.story.chapters) == len(second.story.chapters)
    assert len(first.paragraphs) == len(second.paragraphs)
    assert [anchor.anchor_id for anchor in first.anchors] == [
        anchor.anchor_id for anchor in second.anchors
    ]
    assert [anchor.quote for anchor in first.anchors] == [
        anchor.quote for anchor in second.anchors
    ]


def test_epub_import_fails_clearly_for_malformed_epub() -> None:
    """Malformed EPUB files fail with a clear adapter error."""
    path = Path("build") / "test_epub_import" / "malformed.epub"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not a zip file", encoding="utf-8")

    with pytest.raises(ValueError, match="Malformed EPUB archive"):
        EpubTextExtractor().extract_path(path)


def build_epub(
    filename: str,
    documents: dict[str, str],
    spine_ids: tuple[str, ...],
    nav_id: str | None = None,
) -> Path:
    """Build a minimal deterministic EPUB test fixture."""
    path = Path("build") / "test_epub_import" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    id_by_href = {href.removesuffix(".xhtml"): href for href in documents}
    manifest_items = []
    for item_id, href in id_by_href.items():
        properties = ' properties="nav"' if item_id == nav_id else ""
        manifest_items.append(
            f'<item id="{item_id}" href="{href}" '
            f'media-type="application/xhtml+xml"{properties}/>'
        )
    spine_items = [
        f'<itemref idref="{item_id}"/>' for item_id in spine_ids
    ]
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0">'
        f'<manifest>{"".join(manifest_items)}</manifest>'
        f'<spine>{"".join(spine_items)}</spine>'
        "</package>"
    )
    container = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" '
        'version="1.0">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles>'
        "</container>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", opf)
        for href, text in documents.items():
            archive.writestr(f"OEBPS/{href}", text)

    return path

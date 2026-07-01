"""File-format adapters for Story Import."""

from __future__ import annotations

import html
import logging
import re
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol

from defusedxml import ElementTree

from aevryn.importing.epub import EpubTextExtractor

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SourceFileText:
    """Text extracted from a source file before Story Import parses it."""

    text: str
    source_format: str

    def __post_init__(self) -> None:
        """Validate extracted source text."""
        if not self.text.strip():
            raise ValueError("Extracted source text is required.")
        if not self.source_format.strip():
            raise ValueError("Source format is required.")


class SourceFileTextExtractor:
    """Extract deterministic readable text from supported source file formats."""

    _plain_text_suffixes = frozenset({".txt", ".md", ".markdown"})
    _unsupported_binary_suffixes = frozenset({".pdf", ".mobi", ".azw3"})
    _source_format_by_suffix = {
        ".txt": "txt",
        ".md": "markdown",
        ".markdown": "markdown",
        ".html": "html",
        ".htm": "html",
        ".xhtml": "html",
        ".fb2": "fb2",
        ".docx": "docx",
        ".odt": "odt",
        ".epub": "epub",
    }

    @classmethod
    def source_format_for_path(cls, path: Path) -> str:
        """Return the normalized source format for a supported file path.

        Parameters:
            path: Source file path.

        Returns:
            Normalized source format name.

        Raises:
            ValueError: If the file suffix is unsupported.
        """
        suffix = path.suffix.casefold()
        source_format = cls._source_format_by_suffix.get(suffix)
        if source_format is not None:
            return source_format
        if suffix in cls._unsupported_binary_suffixes:
            raise ValueError(
                f"{suffix} import requires a dedicated parser dependency and is not "
                "enabled in V1.1."
            )

        raise ValueError(f"Unsupported source file format: {suffix or '<none>'}")

    def extract_path(self, path: Path) -> SourceFileText:
        """Extract readable text for Story Import.

        Parameters:
            path: Source file path.

        Returns:
            Deterministic readable text and source format metadata.

        Raises:
            OSError: If the file cannot be read.
            ValueError: If the file type is unsupported or malformed.
        """
        suffix = path.suffix.casefold()
        source_format = self.source_format_for_path(path)
        if suffix in self._plain_text_suffixes:
            # API uploads are copied to a service-owned temporary path before this read.
            return SourceFileText(
                text=path.read_text(encoding="utf-8"),
                source_format=source_format,
            )
        if suffix in {".html", ".htm", ".xhtml"}:
            return SourceFileText(
                # API uploads are copied to a service-owned temporary path before this read.
                text=_ReadableHtmlTextParser.extract(path.read_text(encoding="utf-8")),
                source_format=source_format,
            )
        if suffix == ".fb2":
            return SourceFileText(
                text=self._extract_xml_paragraph_text(
                    path=path,
                    readable_format="FB2",
                    paragraph_local_names={"p", "subtitle", "text-author"},
                ),
                source_format=source_format,
            )
        if suffix == ".docx":
            return SourceFileText(
                text=self._extract_docx_text(path),
                source_format=source_format,
            )
        if suffix == ".odt":
            return SourceFileText(
                text=self._extract_odt_text(path),
                source_format=source_format,
            )
        if suffix == ".epub":
            extracted = EpubTextExtractor().extract_path(path)
            return SourceFileText(text=extracted.text, source_format=source_format)

        raise ValueError(f"Unsupported source file format: {suffix or '<none>'}")

    def _extract_docx_text(self, path: Path) -> str:
        """Extract paragraph text from a DOCX document."""
        try:
            with zipfile.ZipFile(path) as archive:
                document = ElementTree.fromstring(archive.read("word/document.xml"))
        except zipfile.BadZipFile as error:
            raise ValueError("Malformed DOCX archive.") from error
        except KeyError as error:
            raise ValueError(f"Malformed DOCX is missing required file: {error}") from error
        except ElementTree.ParseError as error:
            raise ValueError(f"Malformed DOCX XML: {path}") from error

        paragraphs = [
            _normalize_visible_text(_iter_text(paragraph))
            for paragraph in document.iter()
            if _local_name(paragraph.tag) == "p"
        ]
        return self._require_extracted_text(paragraphs, readable_format="DOCX")

    def _extract_odt_text(self, path: Path) -> str:
        """Extract paragraph text from an ODT document."""
        try:
            with zipfile.ZipFile(path) as archive:
                document = ElementTree.fromstring(archive.read("content.xml"))
        except zipfile.BadZipFile as error:
            raise ValueError("Malformed ODT archive.") from error
        except KeyError as error:
            raise ValueError(f"Malformed ODT is missing required file: {error}") from error
        except ElementTree.ParseError as error:
            raise ValueError(f"Malformed ODT XML: {path}") from error

        paragraphs = [
            _normalize_visible_text(_iter_text(paragraph))
            for paragraph in document.iter()
            if _local_name(paragraph.tag) in {"h", "p"}
        ]
        return self._require_extracted_text(paragraphs, readable_format="ODT")

    def _extract_xml_paragraph_text(
        self,
        path: Path,
        readable_format: str,
        paragraph_local_names: set[str],
    ) -> str:
        """Extract paragraph-like XML text from a source document."""
        try:
            document = ElementTree.fromstring(path.read_text(encoding="utf-8"))
        except ElementTree.ParseError as error:
            raise ValueError(f"Malformed {readable_format} XML.") from error

        paragraphs = [
            _normalize_visible_text(_iter_text(paragraph))
            for paragraph in document.iter()
            if _local_name(paragraph.tag) in paragraph_local_names
        ]
        return self._require_extracted_text(
            paragraphs,
            readable_format=readable_format,
        )

    @staticmethod
    def _require_extracted_text(
        paragraphs: list[str],
        readable_format: str,
    ) -> str:
        """Return normalized paragraph text or fail clearly."""
        cleaned = [paragraph for paragraph in paragraphs if paragraph]
        if not cleaned:
            raise ValueError(f"{readable_format} contains no readable text.")

        return "\n\n".join(cleaned)


class _ReadableHtmlTextParser(HTMLParser):
    """Extract visible readable text from HTML-like files."""

    _block_tags = frozenset(
        {
            "article",
            "blockquote",
            "body",
            "br",
            "div",
            "footer",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "header",
            "li",
            "main",
            "p",
            "section",
        }
    )
    _skip_tags = frozenset({"script", "style", "nav"})

    def __init__(self) -> None:
        """Create a readable HTML text parser."""
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    @classmethod
    def extract(cls, source: str) -> str:
        """Extract visible readable text from HTML source."""
        parser = cls()
        parser.feed(source)
        text = parser.text()
        if not text:
            raise ValueError("HTML contains no readable text.")

        return text

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        """Handle HTML start tags."""
        del attrs
        lowered_tag = tag.casefold()
        if lowered_tag in self._skip_tags:
            self._skip_depth += 1
        if self._skip_depth == 0 and lowered_tag in self._block_tags:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        """Handle HTML end tags."""
        lowered_tag = tag.casefold()
        if lowered_tag in self._skip_tags and self._skip_depth:
            self._skip_depth -= 1
        if self._skip_depth == 0 and lowered_tag in self._block_tags:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        """Handle visible HTML text."""
        if self._skip_depth:
            return

        cleaned = re.sub(r"\s+", " ", html.unescape(data)).strip()
        if cleaned:
            self._parts.append(f"{cleaned} ")

    def text(self) -> str:
        """Return normalized visible text."""
        value = "".join(self._parts)
        value = re.sub(r"[ \t]+\n", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()


class _XmlElement(Protocol):
    tag: str

    def iter(self) -> Iterator[_XmlElement]:
        """Return this element and descendants."""

    def itertext(self) -> Iterator[str]:
        """Return text fragments below this element."""


def _iter_text(element: _XmlElement) -> list[str]:
    """Return all text fragments below an XML element."""
    return [text for text in element.itertext()]


def _local_name(tag: str) -> str:
    """Return an XML tag's local name without its namespace."""
    return tag.rsplit("}", maxsplit=1)[-1]


def _normalize_visible_text(parts: list[str]) -> str:
    """Normalize extracted visible text without changing story meaning."""
    value = "".join(parts)
    value = re.sub(r"\s+", " ", value).strip()
    return html.unescape(value)

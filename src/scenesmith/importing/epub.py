"""EPUB adapter for Story Import."""

from __future__ import annotations

import html
import logging
import re
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from scenesmith.importing.engine import StoryImporter

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EpubText:
    """Text extracted from an EPUB for Story Import.

    Attributes:
        text: Deterministic readable text from ordered spine documents.
        spine_document_count: Number of readable spine documents included.
        trimmed_navigation_lines: Number of leading navigation lines removed.
    """

    text: str
    spine_document_count: int
    trimmed_navigation_lines: int = 0

    def __post_init__(self) -> None:
        """Validate extracted EPUB text metadata."""
        if not self.text.strip():
            raise ValueError("EPUB extracted text is required.")
        for field_name, value in (
            ("spine document count", self.spine_document_count),
            ("trimmed navigation lines", self.trimmed_navigation_lines),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"EPUB {field_name} cannot be negative.")
        if self.spine_document_count < 1:
            raise ValueError("EPUB must contain at least one readable spine document.")


class EpubTextExtractor:
    """Extract deterministic readable text from EPUB spine documents."""

    _container_path = "META-INF/container.xml"
    _container_namespace = "urn:oasis:names:tc:opendocument:xmlns:container"
    _opf_namespace = "http://www.idpf.org/2007/opf"

    def extract_path(self, path: Path) -> EpubText:
        """Extract Story Import text from an EPUB file.

        Parameters:
            path: EPUB file path.

        Returns:
            Extracted EPUB text and adapter metadata.

        Raises:
            OSError: If the file cannot be read.
            ValueError: If the EPUB is malformed or has no readable text.
        """
        if path.suffix.casefold() != ".epub":
            raise ValueError(f"EPUB import requires a .epub file: {path}")

        try:
            with zipfile.ZipFile(path) as archive:
                return self._extract_archive(archive)
        except zipfile.BadZipFile as error:
            raise ValueError(f"Malformed EPUB archive: {path}") from error
        except KeyError as error:
            raise ValueError(f"Malformed EPUB is missing required file: {error}") from error
        except ElementTree.ParseError as error:
            raise ValueError(f"Malformed EPUB metadata XML: {path}") from error
        except UnicodeDecodeError as error:
            raise ValueError(f"EPUB text document is not valid UTF-8: {path}") from error

    def _extract_archive(self, archive: zipfile.ZipFile) -> EpubText:
        """Extract text from an opened EPUB archive."""
        opf_path = self._rootfile_path(archive)
        opf = ElementTree.fromstring(archive.read(opf_path.as_posix()))
        manifest = self._manifest(opf)
        text_blocks: list[str] = []
        spine_document_count = 0

        for itemref in opf.findall(f".//{self._opf('spine')}/{self._opf('itemref')}"):
            if itemref.attrib.get("linear", "yes").casefold() == "no":
                continue
            item = manifest.get(itemref.attrib.get("idref", ""))
            if item is None or self._is_navigation_item(item):
                continue
            href = item.get("href", "")
            media_type = item.get("media-type", "")
            if not self._is_html_item(href=href, media_type=media_type):
                continue

            member_path = (opf_path.parent / href).as_posix()
            parser = _ReadableHtmlTextParser()
            parser.feed(archive.read(member_path).decode("utf-8"))
            text = parser.text()
            if text:
                spine_document_count += 1
                text_blocks.append(text)

        if not text_blocks:
            raise ValueError("EPUB contains no readable spine text.")

        combined_text = "\n\n".join(text_blocks)
        trimmed_text, trimmed_lines = self._trim_leading_navigation(combined_text)
        extracted = EpubText(
            text=trimmed_text,
            spine_document_count=spine_document_count,
            trimmed_navigation_lines=trimmed_lines,
        )
        logger.info(
            "Extracted EPUB text",
            extra={
                "spine_document_count": extracted.spine_document_count,
                "trimmed_navigation_lines": extracted.trimmed_navigation_lines,
            },
        )
        return extracted

    def _rootfile_path(self, archive: zipfile.ZipFile) -> Path:
        """Return the EPUB package document path."""
        container = ElementTree.fromstring(archive.read(self._container_path))
        rootfile = container.find(f".//{self._container('rootfile')}")
        if rootfile is None:
            raise ValueError("Malformed EPUB container has no rootfile.")

        full_path = rootfile.attrib.get("full-path", "").strip()
        if not full_path:
            raise ValueError("Malformed EPUB rootfile has no full-path.")

        return Path(full_path)

    def _manifest(self, opf: ElementTree.Element) -> dict[str, dict[str, str]]:
        """Return package manifest items keyed by ID."""
        manifest: dict[str, dict[str, str]] = {}
        for item in opf.findall(f".//{self._opf('manifest')}/{self._opf('item')}"):
            item_id = item.attrib.get("id", "").strip()
            if item_id:
                manifest[item_id] = dict(item.attrib)

        return manifest

    @staticmethod
    def _is_html_item(href: str, media_type: str) -> bool:
        """Return whether a manifest item can contain readable document text."""
        lowered_href = href.casefold()
        return (
            "html" in media_type.casefold()
            or lowered_href.endswith((".html", ".xhtml", ".htm"))
        )

    @staticmethod
    def _is_navigation_item(item: dict[str, str]) -> bool:
        """Return whether a manifest item is navigation-only metadata."""
        properties = item.get("properties", "")
        media_type = item.get("media-type", "")
        href = item.get("href", "").casefold()
        return (
            "nav" in properties.split()
            or media_type == "application/x-dtbncx+xml"
            or href.endswith(".ncx")
        )

    @staticmethod
    def _trim_leading_navigation(text: str) -> tuple[str, int]:
        """Remove leading chapter-list navigation when it precedes real text."""
        lines = text.splitlines()
        headings: list[tuple[int, int]] = []
        for line_index, line in enumerate(lines):
            stripped = line.strip()
            if StoryImporter._is_chapter_heading(stripped):
                chapter_index = StoryImporter._chapter_index_from_title(stripped)
                if chapter_index is not None:
                    headings.append((line_index, chapter_index))

        previous: tuple[int, int] | None = None
        for current in headings:
            if (
                previous is not None
                and current[1] <= previous[1]
                and current[1] == 1
            ):
                return "\n".join(lines[current[0] :]).strip(), current[0]
            previous = current

        return text.strip(), 0

    @classmethod
    def _container(cls, name: str) -> str:
        """Return a namespaced EPUB container tag."""
        return f"{{{cls._container_namespace}}}{name}"

    @classmethod
    def _opf(cls, name: str) -> str:
        """Return a namespaced EPUB package tag."""
        return f"{{{cls._opf_namespace}}}{name}"


class _ReadableHtmlTextParser(HTMLParser):
    """Extract visible readable text from an EPUB HTML document."""

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
        """Create a readable text parser."""
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

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

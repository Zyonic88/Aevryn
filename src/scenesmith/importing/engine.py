"""Story Import implementation."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from scenesmith.core import Chapter, Scene, Story
from scenesmith.importing.models import (
    EvidenceAnchor,
    ImportedSentence,
    ImportedSource,
    SourceParagraph,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _ChapterBlock:
    """Internal parsed chapter block."""

    title: str
    text: str
    chapter_index: int | None = None


@dataclass(frozen=True, slots=True)
class _SceneBlock:
    """Internal parsed scene block."""

    title: str
    text: str


class StoryImporter:
    """Import source text into stable story structure."""

    _chapter_pattern = re.compile(r"^(?:#\s+)?chapter\s+(?P<index>\d+).*$", re.IGNORECASE)
    _numbered_chapter_title_pattern = re.compile(r"^#\s*(?P<index>\d+)\D.*$")
    _scene_pattern = re.compile(r"^(?:##\s+)?scene\s*:?.*$", re.IGNORECASE)
    _sentence_pattern = re.compile(r".+?(?:\.{3}|[.!?]+)(?:[\"')\]\u3011]*)|.+$")
    _sentence_abbreviations = frozenset(
        {"Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "St.", "No.", "vs.", "etc."}
    )
    _derived_paragraph_sentence_limit = 6
    _derived_paragraph_character_limit = 700
    _paragraph_derivation_sentence_threshold = 8
    _paragraph_derivation_character_threshold = 1200
    _mojibake_replacements = {
        "\u00e3\u20ac\u0090": "\u3010",
        "\u00e3\u20ac\u0091": "\u3011",
    }
    _mojibake_markers = ("\u00c3", "\u00c2", "\u00e3\u20ac")

    def import_text(
        self,
        source_id: str,
        title: str,
        text: str,
    ) -> ImportedSource:
        """Import TXT or Markdown-like text."""
        self._validate_input(source_id=source_id, title=title, text=text)
        source_id = source_id.strip()
        title = title.strip()
        text = self._normalize_text(text)

        chapter_blocks = self._split_chapters(text)
        self._validate_chapter_order(chapter_blocks)
        chapters: list[Chapter] = []
        all_paragraphs: list[SourceParagraph] = []
        all_anchors: list[EvidenceAnchor] = []

        for fallback_index, chapter_block in enumerate(chapter_blocks, start=1):
            chapter_index = chapter_block.chapter_index or fallback_index
            chapter_id = self._chapter_id(source_id, chapter_index)
            scenes, paragraphs, anchors = self._build_chapter(
                source_id=source_id,
                chapter_id=chapter_id,
                chapter_index=chapter_index,
                chapter_block=chapter_block,
            )
            chapters.append(
                Chapter(
                    chapter_id=chapter_id,
                    story_id=source_id,
                    chapter_index=chapter_index,
                    title=chapter_block.title,
                    scenes=scenes,
                )
            )
            all_paragraphs.extend(paragraphs)
            all_anchors.extend(anchors)

        imported_source = ImportedSource(
            source_id=source_id,
            title=title,
            story=Story(story_id=source_id, title=title, chapters=tuple(chapters)),
            paragraphs=tuple(all_paragraphs),
            anchors=tuple(all_anchors),
        )
        logger.info(
            "Imported source",
            extra={
                "source_id": source_id,
                "chapter_count": len(chapters),
                "paragraph_count": len(all_paragraphs),
                "evidence_anchor_count": len(all_anchors),
            },
        )
        return imported_source

    def _build_chapter(
        self,
        source_id: str,
        chapter_id: str,
        chapter_index: int,
        chapter_block: _ChapterBlock,
    ) -> tuple[tuple[Scene, ...], tuple[SourceParagraph, ...], tuple[EvidenceAnchor, ...]]:
        """Build scenes, paragraphs, and anchors for a chapter."""
        scene_blocks = self._split_scenes(chapter_block.text)
        scenes: list[Scene] = []
        paragraphs: list[SourceParagraph] = []
        anchors: list[EvidenceAnchor] = []

        for scene_index, scene_block in enumerate(scene_blocks, start=1):
            scene_id = self._scene_id(chapter_id, scene_index)
            scene_paragraphs, scene_anchors = self._build_scene_source(
                source_id=source_id,
                chapter_id=chapter_id,
                scene_id=scene_id,
                scene_text=scene_block.text,
            )
            scenes.append(
                Scene(
                    scene_id=scene_id,
                    chapter_id=chapter_id,
                    scene_index=scene_index,
                    title=scene_block.title,
                    paragraphs=tuple(paragraph.text for paragraph in scene_paragraphs),
                )
            )
            paragraphs.extend(scene_paragraphs)
            anchors.extend(scene_anchors)

        return tuple(scenes), tuple(paragraphs), tuple(anchors)

    def _build_scene_source(
        self,
        source_id: str,
        chapter_id: str,
        scene_id: str,
        scene_text: str,
    ) -> tuple[tuple[SourceParagraph, ...], tuple[EvidenceAnchor, ...]]:
        """Build paragraph and sentence anchors for a scene."""
        paragraph_texts = self._split_paragraphs(scene_text)
        paragraphs: list[SourceParagraph] = []
        anchors: list[EvidenceAnchor] = []

        for paragraph_index, paragraph_text in enumerate(paragraph_texts, start=1):
            paragraph_id = self._paragraph_id(scene_id, paragraph_index)
            sentences = self._build_sentences(paragraph_id, paragraph_text)
            paragraph = SourceParagraph(
                paragraph_id=paragraph_id,
                scene_id=scene_id,
                paragraph_index=paragraph_index,
                text=paragraph_text,
                sentences=sentences,
            )
            paragraphs.append(paragraph)
            anchors.extend(
                self._build_anchor(
                    source_id=source_id,
                    chapter_id=chapter_id,
                    scene_id=scene_id,
                    paragraph=paragraph,
                    sentence=sentence,
                )
                for sentence in sentences
            )

        return tuple(paragraphs), tuple(anchors)

    def _build_sentences(
        self,
        paragraph_id: str,
        paragraph_text: str,
    ) -> tuple[ImportedSentence, ...]:
        """Split paragraph text into indexed sentences."""
        sentences = self._split_sentences(paragraph_text)
        if not sentences:
            sentences = [paragraph_text]

        return tuple(
            ImportedSentence(
                sentence_id=self._sentence_id(paragraph_id, sentence_index),
                paragraph_id=paragraph_id,
                sentence_index=sentence_index,
                text=sentence,
            )
            for sentence_index, sentence in enumerate(sentences, start=1)
        )

    def _build_anchor(
        self,
        source_id: str,
        chapter_id: str,
        scene_id: str,
        paragraph: SourceParagraph,
        sentence: ImportedSentence,
    ) -> EvidenceAnchor:
        """Build an evidence anchor for a sentence."""
        return EvidenceAnchor(
            anchor_id=self._anchor_id(sentence.sentence_id),
            source_id=source_id,
            chapter_id=chapter_id,
            scene_id=scene_id,
            paragraph_id=paragraph.paragraph_id,
            sentence_id=sentence.sentence_id,
            paragraph_index=paragraph.paragraph_index,
            sentence_index=sentence.sentence_index,
            quote=sentence.text,
        )

    def _split_chapters(self, text: str) -> tuple[_ChapterBlock, ...]:
        """Split text into chapter blocks using explicit chapter headings."""
        lines = text.splitlines()
        blocks: list[_ChapterBlock] = []
        current_title = "Chapter 1"
        current_lines: list[str] = []
        found_heading = False
        preface_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if self._is_chapter_heading(stripped):
                found_heading = True
                if current_lines:
                    blocks.append(
                        _ChapterBlock(
                            title=current_title,
                            text="\n".join(current_lines).strip(),
                            chapter_index=self._chapter_index_from_title(current_title),
                        )
                    )
                    current_lines = []
                current_title = stripped.lstrip("#").strip()
            else:
                if found_heading:
                    current_lines.append(line)
                else:
                    preface_lines.append(line)

        if current_lines:
            if not blocks and preface_lines:
                current_lines = self._merge_preface_lines(
                    preface_lines=preface_lines,
                    chapter_lines=current_lines,
                )
            blocks.append(
                _ChapterBlock(
                    title=current_title,
                    text="\n".join(current_lines).strip(),
                    chapter_index=self._chapter_index_from_title(current_title)
                    if found_heading
                    else None,
                )
            )

        if not found_heading:
            return (_ChapterBlock(title="Chapter 1", text=text.strip(), chapter_index=1),)

        return tuple(block for block in blocks if block.text)

    @staticmethod
    def _validate_chapter_order(chapter_blocks: tuple[_ChapterBlock, ...]) -> None:
        """Reject explicit chapter headings that move backward or duplicate."""
        explicit_indices = [
            chapter_block.chapter_index
            for chapter_block in chapter_blocks
            if chapter_block.chapter_index is not None
        ]
        if len(explicit_indices) <= 1:
            return

        previous_index = explicit_indices[0]
        for chapter_index in explicit_indices[1:]:
            if chapter_index <= previous_index:
                raise ValueError(
                    "Chapter headings must appear in increasing order; "
                    f"found Chapter {chapter_index} after Chapter {previous_index}."
                )
            previous_index = chapter_index

    @staticmethod
    def _merge_preface_lines(
        preface_lines: list[str],
        chapter_lines: list[str],
    ) -> list[str]:
        """Attach pre-chapter text to the first detected chapter."""
        preface_text = "\n".join(preface_lines).strip()
        if not preface_text:
            return chapter_lines

        return [preface_text, "", *chapter_lines]

    @classmethod
    def _chapter_index_from_title(cls, title: str) -> int | None:
        """Return explicit chapter index from a chapter heading."""
        stripped = title.strip()
        match = cls._chapter_pattern.match(stripped)
        if match is not None:
            return int(match.group("index"))

        numbered_match = cls._numbered_chapter_title_pattern.match(stripped)
        if numbered_match is not None:
            return int(numbered_match.group("index"))

        return None

    @classmethod
    def _is_chapter_heading(cls, line: str) -> bool:
        """Return whether a line marks a chapter boundary."""
        return (
            cls._chapter_pattern.match(line) is not None
            or cls._numbered_chapter_title_pattern.match(line) is not None
        )

    def _split_scenes(self, text: str) -> tuple[_SceneBlock, ...]:
        """Split chapter text into scene blocks using explicit scene markers."""
        lines = text.splitlines()
        blocks: list[_SceneBlock] = []
        current_title = "Scene 1"
        current_lines: list[str] = []
        scene_index = 1
        found_marker = False

        for line in lines:
            stripped = line.strip()
            if stripped == "---" or self._scene_pattern.match(stripped):
                found_marker = True
                if current_lines:
                    blocks.append(
                        _SceneBlock(
                            title=current_title,
                            text="\n".join(current_lines).strip(),
                        )
                    )
                    current_lines = []
                    scene_index += 1
                current_title = (
                    stripped.lstrip("#").strip()
                    if stripped != "---"
                    else f"Scene {scene_index}"
                )
            else:
                current_lines.append(line)

        if current_lines:
            blocks.append(
                _SceneBlock(title=current_title, text="\n".join(current_lines).strip())
            )

        if not found_marker:
            return (_SceneBlock(title="Scene 1", text=text.strip()),)

        return tuple(block for block in blocks if block.text)

    @staticmethod
    def _split_paragraphs(text: str) -> tuple[str, ...]:
        """Split text into explicit or deterministically derived paragraphs."""
        if not isinstance(text, str):
            raise ValueError("Paragraph source text is required.")
        source_paragraphs = [
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", text)
            if paragraph.strip()
        ]
        if not source_paragraphs and text.strip():
            return (text.strip(),)

        paragraphs: list[str] = []
        for paragraph in source_paragraphs:
            paragraphs.extend(StoryImporter._derive_paragraphs(paragraph))

        return tuple(paragraphs)

    @staticmethod
    def _derive_paragraphs(paragraph: str) -> tuple[str, ...]:
        """Create readable paragraphs from an oversized unspaced source block."""
        sentences = StoryImporter._split_sentences(paragraph)
        if not sentences:
            return (paragraph,)
        if (
            len(sentences) <= StoryImporter._paragraph_derivation_sentence_threshold
            and len(paragraph) <= StoryImporter._paragraph_derivation_character_threshold
        ):
            return (paragraph,)

        derived: list[str] = []
        current: list[str] = []
        current_length = 0

        for sentence in sentences:
            starts_new_focus = StoryImporter._starts_paragraph_focus(sentence)
            if current and (
                starts_new_focus
                or len(current) >= StoryImporter._derived_paragraph_sentence_limit
                or current_length + len(sentence) > StoryImporter._derived_paragraph_character_limit
            ):
                derived.append(" ".join(current))
                current = []
                current_length = 0

            current.append(sentence)
            current_length += len(sentence) + 1

        if current:
            derived.append(" ".join(current))

        return tuple(derived)

    @staticmethod
    def _starts_paragraph_focus(sentence: str) -> bool:
        """Return whether a sentence should start a derived paragraph."""
        stripped = sentence.lstrip()
        return (
            stripped.startswith(('"', "'", "\u201c", "\u3010"))
            or stripped.startswith(("Chapter ", "Scene "))
            or stripped.endswith(":")
        )

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into complete sentences without decimal or title breaks."""
        normalized = re.sub(r"\s+", " ", text.strip())
        if not normalized:
            return []

        sentences: list[str] = []
        start = 0
        index = 0
        while index < len(normalized):
            if normalized[start] == "\u3010":
                panel_end = normalized.find("\u3011", start)
                if panel_end != -1 and StoryImporter._is_sentence_boundary(
                    normalized,
                    panel_end,
                ):
                    sentences.append(normalized[start : panel_end + 1].strip())
                    start = StoryImporter._next_sentence_start(normalized, panel_end + 1)
                    index = start
                    continue

            character = normalized[index]
            if character in ".!?" and StoryImporter._is_real_sentence_end(
                normalized,
                index,
            ):
                end = StoryImporter._sentence_end_with_closers(normalized, index)
                sentences.append(normalized[start:end].strip())
                start = StoryImporter._next_sentence_start(normalized, end)
                index = start
                continue

            index += 1

        if start < len(normalized):
            sentences.append(normalized[start:].strip())

        return [sentence for sentence in sentences if sentence]

    @staticmethod
    def _is_real_sentence_end(text: str, index: int) -> bool:
        """Return whether punctuation at an index ends a sentence."""
        character = text[index]
        if character == ".":
            previous_character = text[index - 1] if index > 0 else ""
            next_character = text[index + 1] if index + 1 < len(text) else ""
            if previous_character.isdigit() and next_character.isdigit():
                return False
            token_start = text.rfind(" ", 0, index) + 1
            token = text[token_start : index + 1]
            if token in StoryImporter._sentence_abbreviations:
                return False

        return True

    @staticmethod
    def _is_sentence_boundary(text: str, index: int) -> bool:
        """Return whether an index is followed by a sentence boundary."""
        next_index = index + 1
        return next_index >= len(text) or text[next_index].isspace()

    @staticmethod
    def _sentence_end_with_closers(text: str, index: int) -> int:
        """Return sentence end index including closing punctuation."""
        end = index + 1
        while end < len(text) and text[end] in "\"')]\u201d\u2019\u3011":
            end += 1
        return end

    @staticmethod
    def _next_sentence_start(text: str, index: int) -> int:
        """Return the next non-space sentence start index."""
        while index < len(text) and text[index].isspace():
            index += 1
        return index

    @staticmethod
    def _validate_input(source_id: str, title: str, text: str) -> None:
        """Validate import inputs."""
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("Source ID is required.")
        if any(character.isspace() for character in source_id.strip()):
            raise ValueError("Source ID cannot contain whitespace.")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Source title is required.")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Source text is required.")

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize common text encoding artifacts before import."""
        repaired = text
        for broken, replacement in StoryImporter._mojibake_replacements.items():
            repaired = repaired.replace(broken, replacement)

        for _attempt in range(3):
            if not any(marker in repaired for marker in StoryImporter._mojibake_markers):
                break

            try:
                next_repair = repaired.encode("cp1252").decode("utf-8")
            except UnicodeError:
                break

            if next_repair == repaired:
                break

            repaired = next_repair

        return repaired

    @staticmethod
    def _chapter_id(source_id: str, chapter_index: int) -> str:
        """Build a stable chapter ID."""
        return f"{source_id}_chapter_{chapter_index:03d}"

    @staticmethod
    def _scene_id(chapter_id: str, scene_index: int) -> str:
        """Build a stable scene ID."""
        return f"{chapter_id}_scene_{scene_index:03d}"

    @staticmethod
    def _paragraph_id(scene_id: str, paragraph_index: int) -> str:
        """Build a stable paragraph ID."""
        return f"{scene_id}_paragraph_{paragraph_index:03d}"

    @staticmethod
    def _sentence_id(paragraph_id: str, sentence_index: int) -> str:
        """Build a stable sentence ID."""
        return f"{paragraph_id}_sentence_{sentence_index:03d}"

    @staticmethod
    def _anchor_id(sentence_id: str) -> str:
        """Build a stable evidence anchor ID."""
        return f"{sentence_id}_anchor"

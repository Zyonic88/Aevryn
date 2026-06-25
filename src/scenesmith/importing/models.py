"""Story Import structural models."""

from __future__ import annotations

from dataclasses import dataclass

from scenesmith.core import Story


@dataclass(frozen=True, slots=True)
class ImportedSentence:
    """Sentence with a stable source position."""

    sentence_id: str
    paragraph_id: str
    sentence_index: int
    text: str


@dataclass(frozen=True, slots=True)
class SourceParagraph:
    """Paragraph with stable sentence indexing."""

    paragraph_id: str
    scene_id: str
    paragraph_index: int
    text: str
    sentences: tuple[ImportedSentence, ...]


@dataclass(frozen=True, slots=True)
class EvidenceAnchor:
    """Stable source reference for future evidence."""

    anchor_id: str
    source_id: str
    chapter_id: str
    scene_id: str
    paragraph_id: str
    sentence_id: str
    paragraph_index: int
    sentence_index: int
    quote: str


@dataclass(frozen=True, slots=True)
class ImportedSource:
    """Imported story plus source anchors."""

    source_id: str
    title: str
    story: Story
    paragraphs: tuple[SourceParagraph, ...]
    anchors: tuple[EvidenceAnchor, ...]

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

    def __post_init__(self) -> None:
        """Validate imported sentence identity and source text."""
        _require_machine_token(self.sentence_id, "Sentence ID")
        _require_machine_token(self.paragraph_id, "Sentence paragraph ID")
        _require_positive_index(self.sentence_index, "Sentence index")
        _require_text(self.text, "Sentence text")


@dataclass(frozen=True, slots=True)
class SourceParagraph:
    """Paragraph with stable sentence indexing."""

    paragraph_id: str
    scene_id: str
    paragraph_index: int
    text: str
    sentences: tuple[ImportedSentence, ...]

    def __post_init__(self) -> None:
        """Validate source paragraph identity and indexed text."""
        _require_machine_token(self.paragraph_id, "Paragraph ID")
        _require_machine_token(self.scene_id, "Paragraph scene ID")
        _require_positive_index(self.paragraph_index, "Paragraph index")
        _require_text(self.text, "Paragraph text")
        sentence_ids: list[str] = []
        sentence_indexes: list[int] = []
        for sentence in self.sentences:
            if sentence.paragraph_id != self.paragraph_id:
                raise ValueError("Paragraph sentences must reference the paragraph ID.")
            sentence_ids.append(sentence.sentence_id)
            sentence_indexes.append(sentence.sentence_index)
        if len(sentence_ids) != len(set(sentence_ids)):
            raise ValueError("Paragraph cannot contain duplicate sentences.")
        if len(sentence_indexes) != len(set(sentence_indexes)):
            raise ValueError("Paragraph cannot contain duplicate sentence indexes.")


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

    def __post_init__(self) -> None:
        """Validate evidence anchor identity, indexes, and quote text."""
        _require_machine_token(self.anchor_id, "Evidence anchor ID")
        _require_machine_token(self.source_id, "Evidence source ID")
        _require_machine_token(self.chapter_id, "Evidence chapter ID")
        _require_machine_token(self.scene_id, "Evidence scene ID")
        _require_machine_token(self.paragraph_id, "Evidence paragraph ID")
        _require_machine_token(self.sentence_id, "Evidence sentence ID")
        _require_positive_index(self.paragraph_index, "Evidence paragraph index")
        _require_positive_index(self.sentence_index, "Evidence sentence index")
        _require_text(self.quote, "Evidence quote")


@dataclass(frozen=True, slots=True)
class ImportedSource:
    """Imported story plus source anchors."""

    source_id: str
    title: str
    story: Story
    paragraphs: tuple[SourceParagraph, ...]
    anchors: tuple[EvidenceAnchor, ...]

    def __post_init__(self) -> None:
        """Validate imported source structure and evidence references."""
        _require_machine_token(self.source_id, "Imported source ID")
        _require_text(self.title, "Imported source title")
        if self.story.story_id != self.source_id:
            raise ValueError("Imported source ID must match story ID.")

        chapter_ids = {chapter.chapter_id for chapter in self.story.chapters}
        scene_ids = {
            scene.scene_id
            for chapter in self.story.chapters
            for scene in chapter.scenes
        }
        paragraphs_by_id: dict[str, SourceParagraph] = {}
        sentences_by_id: dict[str, ImportedSentence] = {}
        for paragraph in self.paragraphs:
            if paragraph.scene_id not in scene_ids:
                raise ValueError("Imported paragraph references an unknown scene.")
            if paragraph.paragraph_id in paragraphs_by_id:
                raise ValueError("Imported source cannot contain duplicate paragraphs.")
            paragraphs_by_id[paragraph.paragraph_id] = paragraph
            for sentence in paragraph.sentences:
                if sentence.sentence_id in sentences_by_id:
                    raise ValueError(
                        "Imported source cannot contain duplicate sentences."
                    )
                sentences_by_id[sentence.sentence_id] = sentence

        anchor_ids: set[str] = set()
        for anchor in self.anchors:
            if anchor.source_id != self.source_id:
                raise ValueError("Evidence anchors must match imported source ID.")
            if anchor.anchor_id in anchor_ids:
                raise ValueError("Imported source cannot contain duplicate anchors.")
            if anchor.chapter_id not in chapter_ids:
                raise ValueError("Evidence anchor references an unknown chapter.")
            if anchor.scene_id not in scene_ids:
                raise ValueError("Evidence anchor references an unknown scene.")
            anchor_paragraph = paragraphs_by_id.get(anchor.paragraph_id)
            if anchor_paragraph is None:
                raise ValueError("Evidence anchor references an unknown paragraph.")
            anchor_sentence = sentences_by_id.get(anchor.sentence_id)
            if anchor_sentence is None:
                raise ValueError("Evidence anchor references an unknown sentence.")
            if anchor_paragraph.scene_id != anchor.scene_id:
                raise ValueError("Evidence anchor scene must match its paragraph scene.")
            if anchor_sentence.paragraph_id != anchor.paragraph_id:
                raise ValueError(
                    "Evidence anchor sentence must belong to its paragraph."
                )
            if anchor.quote != anchor_sentence.text:
                raise ValueError("Evidence anchor quote must match sentence text.")
            anchor_ids.add(anchor.anchor_id)


def _require_text(value: str, field_name: str) -> None:
    """Validate a required human-readable text field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a required whitespace-free machine token."""
    _require_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _require_positive_index(value: int, field_name: str) -> None:
    """Validate a one-based source index."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be at least 1.")

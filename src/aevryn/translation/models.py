"""Translation Foundation data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TranslationMode = Literal["literal", "clean_english", "localized", "subtitle_narration"]
TranslationTermKind = Literal[
    "term",
    "name",
    "alias",
    "title",
    "honorific",
    "faction",
    "location",
    "item",
    "skill",
    "power_system",
]


@dataclass(frozen=True, slots=True)
class GlossaryTerm:
    """Preferred handling for a story-specific translation term."""

    source_term: str
    preferred_term: str
    evidence_anchor_id: str
    possible_meanings: tuple[str, ...] = ()
    entity_id: str | None = None
    term_kind: TranslationTermKind = "term"
    review_required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_term", _normalized_text(self.source_term, "Source term"))
        object.__setattr__(
            self,
            "preferred_term",
            _normalized_text(self.preferred_term, "Preferred term"),
        )
        object.__setattr__(
            self,
            "possible_meanings",
            _normalized_text_values(
                self.possible_meanings,
                "Glossary term possible meanings",
            ),
        )
        _require_machine_token(self.evidence_anchor_id, "Glossary term evidence anchor ID")
        if self.entity_id is not None:
            _require_machine_token(self.entity_id, "Glossary term entity ID")
        _require_term_kind(self.term_kind)


@dataclass(frozen=True, slots=True)
class TranslationUnit:
    """Source text unit prepared for translation or normalization."""

    unit_id: str
    source_text: str
    evidence_anchor_ids: tuple[str, ...]
    source_language: str = "auto"
    target_language: str = "en"
    source_chapter_id: str = ""
    source_scene_id: str = ""

    def __post_init__(self) -> None:
        _require_machine_token(self.unit_id, "Translation unit ID")
        object.__setattr__(
            self,
            "source_text",
            _normalized_text(self.source_text, "Translation source text"),
        )
        _require_unique_machine_tokens(
            self.evidence_anchor_ids,
            "Translation unit evidence anchor IDs",
        )
        _require_language_token(self.source_language, "Translation source language")
        _require_language_token(self.target_language, "Translation target language")
        if self.source_chapter_id:
            _require_machine_token(
                self.source_chapter_id,
                "Translation source chapter ID",
            )
        if self.source_scene_id:
            _require_machine_token(self.source_scene_id, "Translation source scene ID")


@dataclass(frozen=True, slots=True)
class TranslationIssue:
    """Review issue raised while preserving uncertain translated meaning."""

    issue_code: str
    source_term: str
    message: str
    evidence_anchor_ids: tuple[str, ...]
    term_kind: TranslationTermKind = "term"
    possible_meaning_count: int = 0

    def __post_init__(self) -> None:
        _require_machine_token(self.issue_code, "Translation issue code")
        _require_term_kind(self.term_kind)
        _require_non_negative_count(
            self.possible_meaning_count,
            "Translation issue possible meaning count",
        )
        object.__setattr__(
            self,
            "source_term",
            _normalized_text(self.source_term, "Translation issue source term"),
        )
        object.__setattr__(
            self,
            "message",
            _normalized_text(self.message, "Translation issue message"),
        )
        _require_unique_machine_tokens(
            self.evidence_anchor_ids,
            "Translation issue evidence anchor IDs",
        )


@dataclass(frozen=True, slots=True)
class TranslatedUnit:
    """Translated or normalized text with original source links."""

    unit_id: str
    source_language: str
    target_language: str
    mode: TranslationMode
    normalized_text: str
    source_evidence_anchor_ids: tuple[str, ...]
    issues: tuple[TranslationIssue, ...] = ()
    source_chapter_id: str = ""
    source_scene_id: str = ""

    def __post_init__(self) -> None:
        _require_machine_token(self.unit_id, "Translated unit ID")
        _require_language_token(self.source_language, "Translated unit source language")
        _require_language_token(self.target_language, "Translated unit target language")
        if self.mode not in {"literal", "clean_english", "localized", "subtitle_narration"}:
            raise ValueError("Translated unit mode is invalid.")
        object.__setattr__(
            self,
            "normalized_text",
            _normalized_text(self.normalized_text, "Translated normalized text"),
        )
        _require_unique_machine_tokens(
            self.source_evidence_anchor_ids,
            "Translated unit source evidence anchor IDs",
        )
        if self.source_chapter_id:
            _require_machine_token(
                self.source_chapter_id,
                "Translated unit source chapter ID",
            )
        if self.source_scene_id:
            _require_machine_token(self.source_scene_id, "Translated unit source scene ID")


def _normalized_text(value: str, field_name: str) -> str:
    """Normalize required human-readable text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    return " ".join(value.split())


def _normalized_text_values(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    """Normalize optional human-readable text choices."""
    if not isinstance(values, tuple):
        raise ValueError(f"{field_name} must be a tuple.")
    normalized_values = tuple(_normalized_text(value, field_name) for value in values)
    if len(normalized_values) == 1:
        raise ValueError(f"{field_name} must include at least two values when provided.")
    if len(normalized_values) != len(set(normalized_values)):
        raise ValueError(f"{field_name} must be unique.")
    return normalized_values


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a required whitespace-free machine token."""
    _normalized_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _require_unique_machine_tokens(values: tuple[str, ...], field_name: str) -> None:
    """Validate unique machine-token values."""
    if not values:
        raise ValueError(f"{field_name} are required.")
    for value in values:
        _require_machine_token(value, field_name)
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique.")


def _require_language_token(value: str, field_name: str) -> None:
    """Validate compact language tokens like auto, en, zh, ko, or ja."""
    _require_machine_token(value, field_name)
    if not all(character.isalnum() or character in {"-", "_"} for character in value):
        raise ValueError(f"{field_name} is invalid.")


def _require_term_kind(value: str) -> None:
    """Validate supported glossary term categories."""
    if value not in {
        "term",
        "name",
        "alias",
        "title",
        "honorific",
        "faction",
        "location",
        "item",
        "skill",
        "power_system",
    }:
        raise ValueError("Translation term kind is invalid.")


def _require_non_negative_count(value: int, field_name: str) -> None:
    """Validate safe metadata counts."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer.")
    if value == 1:
        raise ValueError(f"{field_name} cannot be exactly one.")

"""Sentence Understanding data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SentenceSignal = Literal[
    "dialogue",
    "action",
    "description",
    "identity_reference",
    "relationship_reference",
    "item_reference",
    "skill_reference",
    "system_reference",
    "translation_ambiguity",
]


@dataclass(frozen=True, slots=True)
class SentenceUnderstanding:
    """Metadata-only meaning signals for one imported sentence."""

    sentence_id: str
    evidence_anchor_id: str
    source_chapter_id: str
    source_scene_id: str
    paragraph_index: int
    sentence_index: int
    signals: tuple[SentenceSignal, ...]
    cue_terms: tuple[str, ...] = ()
    ambiguity_terms: tuple[str, ...] = ()
    review_required: bool = False

    def __post_init__(self) -> None:
        """Validate sentence understanding metadata."""
        _require_machine_token(self.sentence_id, "Sentence understanding sentence ID")
        _require_machine_token(
            self.evidence_anchor_id,
            "Sentence understanding evidence anchor ID",
        )
        _require_machine_token(
            self.source_chapter_id,
            "Sentence understanding source chapter ID",
        )
        _require_machine_token(
            self.source_scene_id,
            "Sentence understanding source scene ID",
        )
        _require_positive_index(self.paragraph_index, "Sentence understanding paragraph index")
        _require_positive_index(self.sentence_index, "Sentence understanding sentence index")
        _require_unique_signals(self.signals)
        object.__setattr__(
            self,
            "cue_terms",
            _normalized_unique_terms(self.cue_terms, "Sentence understanding cue terms"),
        )
        object.__setattr__(
            self,
            "ambiguity_terms",
            _normalized_unique_terms(
                self.ambiguity_terms,
                "Sentence understanding ambiguity terms",
            ),
        )


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a required whitespace-free machine token."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _require_positive_index(value: int, field_name: str) -> None:
    """Validate a one-based source index."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be at least 1.")


def _require_unique_signals(values: tuple[SentenceSignal, ...]) -> None:
    """Validate sentence signal collection."""
    if not isinstance(values, tuple):
        raise ValueError("Sentence understanding signals must be a tuple.")
    if not values:
        raise ValueError("Sentence understanding signals are required.")
    if len(values) != len(set(values)):
        raise ValueError("Sentence understanding signals must be unique.")


def _normalized_unique_terms(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    """Normalize compact cue terms used for review and routing."""
    if not isinstance(values, tuple):
        raise ValueError(f"{field_name} must be a tuple.")
    normalized_values = tuple(_normalized_term(value, field_name) for value in values)
    if len(normalized_values) != len({value.casefold() for value in normalized_values}):
        raise ValueError(f"{field_name} must be unique.")
    return normalized_values


def _normalized_term(value: str, field_name: str) -> str:
    """Normalize one compact cue term."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} cannot include blank values.")
    return " ".join(value.split())

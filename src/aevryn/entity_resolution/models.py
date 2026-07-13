"""Entity Resolution data models."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Literal

ResolutionStatus = Literal["resolved", "ambiguous", "unresolved"]


@dataclass(frozen=True, slots=True)
class SurfaceReference:
    """One text reference to a possible entity identity."""

    text: str
    evidence_anchor_id: str
    scene_id: str = ""
    chapter_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", _normalized_text(self.text, "Surface reference"))
        _require_machine_token(self.evidence_anchor_id, "Surface reference evidence anchor ID")
        if self.scene_id:
            _require_machine_token(self.scene_id, "Surface reference scene ID")
        if self.chapter_id:
            _require_machine_token(self.chapter_id, "Surface reference chapter ID")


@dataclass(frozen=True, slots=True)
class EntityIdentityProfile:
    """Known identity information that resolution may match against."""

    entity_id: str
    canonical_name: str
    entity_type: str = "character"
    aliases: tuple[str, ...] = ()
    titles: tuple[str, ...] = ()
    honorifics: tuple[str, ...] = ()
    descriptions: tuple[str, ...] = ()
    relationship_labels: tuple[str, ...] = ()
    pronouns: tuple[str, ...] = ()
    evidence_anchor_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_machine_token(self.entity_id, "Entity identity profile ID")
        _require_machine_token(self.entity_type, "Entity identity profile type")
        object.__setattr__(
            self,
            "canonical_name",
            _normalized_text(self.canonical_name, "Entity identity canonical name"),
        )
        object.__setattr__(
            self,
            "aliases",
            _normalized_text_values(self.aliases, "Entity identity aliases"),
        )
        object.__setattr__(
            self,
            "titles",
            _normalized_text_values(self.titles, "Entity identity titles"),
        )
        object.__setattr__(
            self,
            "honorifics",
            _normalized_text_values(self.honorifics, "Entity identity honorifics"),
        )
        object.__setattr__(
            self,
            "descriptions",
            _normalized_text_values(self.descriptions, "Entity identity descriptions"),
        )
        object.__setattr__(
            self,
            "relationship_labels",
            _normalized_text_values(
                self.relationship_labels,
                "Entity identity relationship labels",
            ),
        )
        object.__setattr__(
            self,
            "pronouns",
            _normalized_text_values(self.pronouns, "Entity identity pronouns"),
        )
        for anchor_id in self.evidence_anchor_ids:
            _require_machine_token(anchor_id, "Entity identity evidence anchor ID")


@dataclass(frozen=True, slots=True)
class ResolutionCandidate:
    """Possible entity match for a surface reference."""

    entity_id: str
    confidence: float
    match_kind: str
    matched_text: str

    def __post_init__(self) -> None:
        _require_machine_token(self.entity_id, "Resolution candidate entity ID")
        _require_confidence(self.confidence)
        _require_machine_token(self.match_kind, "Resolution candidate match kind")
        object.__setattr__(
            self,
            "matched_text",
            _normalized_text(self.matched_text, "Resolution candidate matched text"),
        )


@dataclass(frozen=True, slots=True)
class ResolvedReference:
    """Resolution decision for one surface reference."""

    reference: SurfaceReference
    status: ResolutionStatus
    entity_id: str | None = None
    confidence: float = 0.0
    candidates: tuple[ResolutionCandidate, ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        if self.status not in {"resolved", "ambiguous", "unresolved"}:
            raise ValueError("Resolved reference status is invalid.")
        if self.entity_id is not None:
            _require_machine_token(self.entity_id, "Resolved reference entity ID")
        _require_confidence(self.confidence)
        object.__setattr__(
            self,
            "reason",
            _normalized_text(self.reason or self.status, "Resolved reference reason"),
        )
        _require_candidate_values(self.candidates)
        if self.status == "resolved" and not self.entity_id:
            raise ValueError("Resolved references require an entity ID.")
        if self.status != "resolved" and self.entity_id:
            raise ValueError("Only resolved references can carry an entity ID.")


def _normalized_text_values(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    """Normalize a sequence of human-readable values."""
    if not isinstance(values, tuple):
        raise ValueError(f"{field_name} must be a tuple.")
    normalized = tuple(_normalized_text(value, field_name) for value in values)
    if len(normalized) != len({value.casefold() for value in normalized}):
        raise ValueError(f"{field_name} must be unique.")
    return normalized


def _require_candidate_values(candidates: tuple[ResolutionCandidate, ...]) -> None:
    """Validate candidate metadata for deterministic resolution decisions."""
    if not isinstance(candidates, tuple):
        raise ValueError("Resolved reference candidates must be a tuple.")
    entity_ids = tuple(candidate.entity_id for candidate in candidates)
    if len(entity_ids) != len(set(entity_ids)):
        raise ValueError("Resolved reference candidate entity IDs must be unique.")


def _normalized_text(value: str, field_name: str) -> str:
    """Normalize required human-readable text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    return unicodedata.normalize("NFC", " ".join(value.split()))


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a required whitespace-free machine token."""
    _normalized_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _require_confidence(confidence: float) -> None:
    """Validate resolution confidence."""
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, int | float)
        or not 0.0 <= confidence <= 1.0
    ):
        raise ValueError("Resolution confidence must be between 0.0 and 1.0.")

"""Entity Extraction candidate models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SceneEvidenceAnchor:
    """Evidence anchor summary sent to an extractor."""

    anchor_id: str
    quote: str


@dataclass(frozen=True, slots=True)
class SceneExtractionInput:
    """Scene text and anchors sent to an extractor."""

    scene_id: str
    text: str
    evidence_anchor_ids: tuple[str, ...]
    evidence_anchors: tuple[SceneEvidenceAnchor, ...] = ()


@dataclass(frozen=True, slots=True)
class ExtractedEntity:
    """Candidate entity proposed by extraction."""

    entity_id: str
    entity_type: str
    display_name: str
    evidence_anchor_id: str
    confidence: float


@dataclass(frozen=True, slots=True)
class ExtractedRelationship:
    """Candidate relationship proposed by extraction."""

    source_entity_id: str
    relationship_type: str
    target_entity_id: str
    evidence_anchor_id: str
    confidence: float


@dataclass(frozen=True, slots=True)
class ExtractedFact:
    """Candidate fact proposed by extraction."""

    fact_id: str
    entity_id: str
    attribute: str
    value: str
    evidence_anchor_id: str
    confidence: float


@dataclass(frozen=True, slots=True)
class ExtractedStateChange:
    """Candidate state change proposed by extraction."""

    entity_id: str
    attribute: str
    value: str
    valid_from_anchor_id: str
    confidence: float
    valid_until_anchor_id: str | None = None


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Candidate extraction result for a scene."""

    scene_id: str
    entities: tuple[ExtractedEntity, ...] = ()
    facts: tuple[ExtractedFact, ...] = ()
    relationships: tuple[ExtractedRelationship, ...] = ()
    state_changes: tuple[ExtractedStateChange, ...] = ()

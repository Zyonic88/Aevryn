"""Entity Extraction candidate models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SceneEvidenceAnchor:
    """Evidence anchor summary sent to an extractor."""

    anchor_id: str
    quote: str

    def __post_init__(self) -> None:
        """Validate scene evidence anchor fields."""
        _require_machine_token(self.anchor_id, "Scene evidence anchor ID")
        _require_text(self.quote, "Scene evidence anchor quote")


@dataclass(frozen=True, slots=True)
class SceneExtractionInput:
    """Scene text and anchors sent to an extractor."""

    scene_id: str
    text: str
    evidence_anchor_ids: tuple[str, ...]
    evidence_anchors: tuple[SceneEvidenceAnchor, ...] = ()

    def __post_init__(self) -> None:
        """Validate scene extraction input fields."""
        _require_machine_token(self.scene_id, "Scene extraction scene ID")
        _require_text(self.text, "Scene extraction text")
        for anchor_id in self.evidence_anchor_ids:
            _require_machine_token(anchor_id, "Scene extraction evidence anchor ID")
        _require_unique_values(
            self.evidence_anchor_ids,
            "Scene extraction evidence anchor IDs",
        )
        evidence_anchor_ids = tuple(anchor.anchor_id for anchor in self.evidence_anchors)
        _require_unique_values(
            evidence_anchor_ids,
            "Scene extraction evidence anchors",
        )
        if evidence_anchor_ids and set(evidence_anchor_ids) != set(self.evidence_anchor_ids):
            raise ValueError(
                "Scene extraction evidence anchors must match evidence anchor IDs."
            )


@dataclass(frozen=True, slots=True)
class ExtractedEntity:
    """Candidate entity proposed by extraction."""

    entity_id: str
    entity_type: str
    display_name: str
    evidence_anchor_id: str
    confidence: float

    def __post_init__(self) -> None:
        """Validate extracted entity candidate fields."""
        _require_machine_token(self.entity_id, "Extracted entity ID")
        _require_machine_token(self.entity_type, "Extracted entity type")
        object.__setattr__(
            self,
            "display_name",
            _normalized_text(self.display_name, "Extracted entity display name"),
        )
        _require_machine_token(self.evidence_anchor_id, "Extracted entity evidence anchor ID")
        _require_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class ExtractedRelationship:
    """Candidate relationship proposed by extraction."""

    source_entity_id: str
    relationship_type: str
    target_entity_id: str
    evidence_anchor_id: str
    confidence: float

    def __post_init__(self) -> None:
        """Validate extracted relationship candidate fields."""
        _require_machine_token(
            self.source_entity_id,
            "Extracted relationship source entity ID",
        )
        _require_machine_token(
            self.relationship_type,
            "Extracted relationship type",
        )
        _require_machine_token(
            self.target_entity_id,
            "Extracted relationship target entity ID",
        )
        _require_machine_token(
            self.evidence_anchor_id,
            "Extracted relationship evidence anchor ID",
        )
        _require_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class ExtractedFact:
    """Candidate fact proposed by extraction."""

    fact_id: str
    entity_id: str
    attribute: str
    value: str
    evidence_anchor_id: str
    confidence: float

    def __post_init__(self) -> None:
        """Validate extracted fact candidate fields."""
        _require_machine_token(self.fact_id, "Extracted fact ID")
        _require_machine_token(self.entity_id, "Extracted fact entity ID")
        _require_machine_token(self.attribute, "Extracted fact attribute")
        object.__setattr__(
            self,
            "value",
            _normalized_text(self.value, "Extracted fact value"),
        )
        _require_machine_token(self.evidence_anchor_id, "Extracted fact evidence anchor ID")
        _require_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class ExtractedStateChange:
    """Candidate state change proposed by extraction."""

    entity_id: str
    attribute: str
    value: str
    valid_from_anchor_id: str
    confidence: float
    valid_until_anchor_id: str | None = None

    def __post_init__(self) -> None:
        """Validate extracted state-change candidate fields."""
        _require_machine_token(self.entity_id, "Extracted state-change entity ID")
        _require_machine_token(self.attribute, "Extracted state-change attribute")
        object.__setattr__(
            self,
            "value",
            _normalized_text(self.value, "Extracted state-change value"),
        )
        _require_machine_token(
            self.valid_from_anchor_id,
            "Extracted state-change valid-from anchor ID",
        )
        if self.valid_until_anchor_id is not None:
            _require_machine_token(
                self.valid_until_anchor_id,
                "Extracted state-change valid-until anchor ID",
            )
        _require_confidence(self.confidence)


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Candidate extraction result for a scene."""

    scene_id: str
    entities: tuple[ExtractedEntity, ...] = ()
    facts: tuple[ExtractedFact, ...] = ()
    relationships: tuple[ExtractedRelationship, ...] = ()
    state_changes: tuple[ExtractedStateChange, ...] = ()

    def __post_init__(self) -> None:
        """Validate extraction result identity."""
        _require_machine_token(self.scene_id, "Extraction result scene ID")
        _require_unique_candidate_values(
            tuple(entity.entity_id for entity in self.entities),
            "entity IDs",
        )
        _require_unique_candidate_values(
            tuple(fact.fact_id for fact in self.facts),
            "fact IDs",
        )
        _require_unique_candidate_values(
            tuple(
                (
                    relationship.source_entity_id,
                    relationship.relationship_type,
                    relationship.target_entity_id,
                )
                for relationship in self.relationships
            ),
            "relationship candidates",
        )
        _require_unique_candidate_values(
            tuple(
                (
                    state_change.entity_id,
                    state_change.attribute,
                    state_change.value,
                    state_change.valid_from_anchor_id,
                    state_change.valid_until_anchor_id,
                )
                for state_change in self.state_changes
            ),
            "state-change candidates",
        )


def _require_text(value: str, field_name: str) -> None:
    """Validate a required human-readable text field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


def _normalized_text(value: str, field_name: str) -> str:
    """Return normalized human-readable text or raise if it is blank."""
    _require_text(value, field_name)
    return " ".join(value.split())


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a required whitespace-free machine token."""
    _require_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _require_confidence(confidence: float) -> None:
    """Validate extraction confidence."""
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, int | float)
        or not 0.0 <= confidence <= 1.0
    ):
        raise ValueError("Extraction confidence must be between 0.0 and 1.0.")


def _require_unique_values(values: tuple[object, ...], field_name: str) -> None:
    """Validate that model-level identity values are unique."""
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique.")


def _require_unique_candidate_values(
    values: tuple[object, ...],
    field_name: str,
) -> None:
    """Validate that extraction result candidate identities are unique."""
    if len(values) != len(set(values)):
        raise ValueError(f"Extraction result contains duplicate {field_name}.")

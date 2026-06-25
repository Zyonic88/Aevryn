"""Evidence-bounded AI extraction adapter."""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol

from scenesmith.extraction.models import (
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractedStateChange,
    ExtractionResult,
    SceneExtractionInput,
)

logger = logging.getLogger(__name__)


class AIExtractionClient(Protocol):
    """Protocol for AI clients used by evidence-bounded extraction."""

    def complete(self, prompt: str) -> str:
        """Return a JSON extraction response for the prompt."""


class StaticAIExtractionClient:
    """AI extraction client that returns a precomputed JSON response."""

    def __init__(self, response: str) -> None:
        """Create a static client.

        Parameters:
            response: JSON response text to return for every prompt.
        """
        self._response = response

    def complete(self, _prompt: str) -> str:
        """Return the configured JSON response."""
        return self._response


class EvidenceBoundedAIExtractor:
    """Extract candidates from one scene using an evidence-bounded AI client."""

    _required_payload_keys = frozenset(
        {"entities", "facts", "relationships", "state_changes"}
    )
    _mojibake_replacements = {
        "\u00e3\u20ac\u0090": "\u3010",
        "\u00e3\u20ac\u0091": "\u3011",
    }
    _mojibake_markers = ("\u00c3", "\u00c2", "\u00e3\u20ac")

    def __init__(self, client: AIExtractionClient) -> None:
        """Create an AI extractor.

        Parameters:
            client: AI client that returns JSON candidate data.
        """
        self._client = client

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Extract candidates from a scene without updating Canon.

        Parameters:
            scene: Scene text plus allowed evidence anchors.

        Returns:
            Extraction candidates with required evidence and confidence.

        Raises:
            ValueError: If the client returns invalid JSON or unsupported values.
        """
        payload = self._load_payload(self._client.complete(self.build_prompt(scene)))
        result = ExtractionResult(
            scene_id=scene.scene_id,
            entities=self._entities(payload),
            facts=self._facts(payload),
            relationships=self._relationships(payload),
            state_changes=self._state_changes(payload),
        )
        logger.info(
            "Extracted scene candidates",
            extra={
                "scene_id": scene.scene_id,
                "candidate_entities": len(result.entities),
                "candidate_facts": len(result.facts),
                "candidate_relationships": len(result.relationships),
                "candidate_state_changes": len(result.state_changes),
            },
        )
        return result

    def build_prompt(self, scene: SceneExtractionInput) -> str:
        """Build an evidence-bounded extraction prompt.

        Parameters:
            scene: Scene extraction input containing text and allowed anchors.

        Returns:
            Prompt text suitable for an AI extraction client.
        """
        anchors = "\n".join(
            f"- {anchor.anchor_id}: {anchor.quote}"
            for anchor in scene.evidence_anchors
        )
        return "\n".join(
            [
                "You extract candidates for SceneSmith.",
                "The AI may propose. Canon decides.",
                "Use only the provided evidence anchors.",
                "Do not infer unsupported claims.",
                "If information is not stated, omit it. Unknown stays unknown.",
                "Return JSON only with keys: entities, facts, relationships, state_changes.",
                "",
                f"Scene ID: {scene.scene_id}",
                "",
                "Evidence Anchors:",
                anchors,
                "",
                "Scene Text:",
                scene.text,
            ]
        )

    @staticmethod
    def _load_payload(raw_response: str) -> dict[str, Any]:
        """Parse an AI JSON response."""
        try:
            payload = json.loads(raw_response.lstrip("\ufeff"))
        except json.JSONDecodeError as error:
            raise ValueError("AI extraction response must be valid JSON.") from error

        if not isinstance(payload, dict):
            raise ValueError("AI extraction response must be a JSON object.")

        keys = set(payload)
        missing_keys = EvidenceBoundedAIExtractor._required_payload_keys - keys
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(f"AI extraction response is missing required keys: {missing}")

        extra_keys = keys - EvidenceBoundedAIExtractor._required_payload_keys
        if extra_keys:
            extra = ", ".join(sorted(extra_keys))
            raise ValueError(f"AI extraction response has unsupported keys: {extra}")

        return payload

    @classmethod
    def _entities(cls, payload: dict[str, Any]) -> tuple[ExtractedEntity, ...]:
        """Parse entity candidates from a payload."""
        return tuple(
            ExtractedEntity(
                entity_id=cls._required_str(item, "entity_id"),
                entity_type=cls._required_str(item, "entity_type"),
                display_name=cls._required_str(item, "display_name"),
                evidence_anchor_id=cls._required_str(item, "evidence_anchor_id"),
                confidence=cls._required_confidence(item),
            )
            for item in cls._items(payload, "entities")
        )

    @classmethod
    def _facts(cls, payload: dict[str, Any]) -> tuple[ExtractedFact, ...]:
        """Parse fact candidates from a payload."""
        return tuple(
            ExtractedFact(
                fact_id=cls._required_str(item, "fact_id"),
                entity_id=cls._required_str(item, "entity_id"),
                attribute=cls._required_str(item, "attribute"),
                value=cls._required_str(item, "value"),
                evidence_anchor_id=cls._required_str(item, "evidence_anchor_id"),
                confidence=cls._required_confidence(item),
            )
            for item in cls._items(payload, "facts")
        )

    @classmethod
    def _relationships(cls, payload: dict[str, Any]) -> tuple[ExtractedRelationship, ...]:
        """Parse relationship candidates from a payload."""
        return tuple(
            ExtractedRelationship(
                source_entity_id=cls._required_str(item, "source_entity_id"),
                relationship_type=cls._required_str(item, "relationship_type"),
                target_entity_id=cls._required_str(item, "target_entity_id"),
                evidence_anchor_id=cls._required_str(item, "evidence_anchor_id"),
                confidence=cls._required_confidence(item),
            )
            for item in cls._items(payload, "relationships")
        )

    @classmethod
    def _state_changes(cls, payload: dict[str, Any]) -> tuple[ExtractedStateChange, ...]:
        """Parse state-change candidates from a payload."""
        return tuple(
            ExtractedStateChange(
                entity_id=cls._required_str(item, "entity_id"),
                attribute=cls._required_str(item, "attribute"),
                value=cls._required_str(item, "value"),
                valid_from_anchor_id=cls._required_str(item, "valid_from_anchor_id"),
                valid_until_anchor_id=cls._optional_str(item, "valid_until_anchor_id"),
                confidence=cls._required_confidence(item),
            )
            for item in cls._items(payload, "state_changes")
        )

    @staticmethod
    def _items(payload: dict[str, Any], key: str) -> tuple[dict[str, Any], ...]:
        """Return object items from a payload list."""
        value = payload.get(key, [])
        if not isinstance(value, list):
            raise ValueError(f"AI extraction field must be a list: {key}")

        items: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                raise ValueError(f"AI extraction list item must be an object: {key}")
            items.append(item)

        return tuple(items)

    @staticmethod
    def _required_str(item: dict[str, Any], key: str) -> str:
        """Read a required string from a payload item."""
        value = item.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"AI extraction field must be a non-empty string: {key}")
        return EvidenceBoundedAIExtractor._normalize_text(value)

    @staticmethod
    def _optional_str(item: dict[str, Any], key: str) -> str | None:
        """Read an optional string from a payload item."""
        value = item.get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"AI extraction field must be a string or null: {key}")
        return EvidenceBoundedAIExtractor._normalize_text(value)

    @staticmethod
    def _required_confidence(item: dict[str, Any]) -> float:
        """Read a required confidence value from a payload item."""
        value = item.get("confidence")
        if not isinstance(value, int | float):
            raise ValueError("AI extraction confidence must be numeric.")
        confidence = float(value)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("AI extraction confidence must be between 0.0 and 1.0.")

        return confidence

    @staticmethod
    def _normalize_text(value: str) -> str:
        """Normalize common text encoding artifacts in AI candidate strings."""
        repaired = value
        for broken, replacement in EvidenceBoundedAIExtractor._mojibake_replacements.items():
            repaired = repaired.replace(broken, replacement)

        for _attempt in range(3):
            if not any(
                marker in repaired
                for marker in EvidenceBoundedAIExtractor._mojibake_markers
            ):
                break

            try:
                next_repair = repaired.encode("cp1252").decode("utf-8")
            except UnicodeError:
                break

            if next_repair == repaired:
                break

            repaired = next_repair

        return repaired

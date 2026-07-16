"""Evidence-bounded AI extraction adapter."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from aevryn.extraction.models import (
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractedStateChange,
    ExtractionResult,
    SceneExtractionInput,
)
from aevryn.json_utils import loads_json_without_duplicate_keys

logger = logging.getLogger(__name__)


class AIExtractionClient(Protocol):
    """Protocol for AI clients used by evidence-bounded extraction."""

    def complete(self, prompt: str) -> str:
        """Return a JSON extraction response for the prompt."""


class OpenAIResponsesTransport(Protocol):
    """Transport boundary for OpenAI Responses API calls."""

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> dict[str, Any]:
        """POST JSON and return a decoded JSON object."""


class UrllibOpenAIResponsesTransport:
    """Standard-library HTTP transport for OpenAI Responses API calls."""

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> dict[str, Any]:
        """POST JSON and return a decoded JSON object."""
        parsed_url = urlparse(url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise ValueError("OpenAI extraction endpoint must be an HTTPS URL.")
        request = Request(
            url,
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            headers=dict(headers),
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
                raw_response = response.read(max_response_bytes + 1)
        except TimeoutError as error:
            raise ValueError("OpenAI extraction request timed out.") from error
        except HTTPError as error:
            raise ValueError(
                f"OpenAI extraction request failed with HTTP {error.code}."
            ) from error
        except URLError as error:
            raise ValueError("OpenAI extraction request failed.") from error

        if len(raw_response) > max_response_bytes:
            raise ValueError("OpenAI extraction response exceeded the size limit.")
        if not raw_response:
            raise ValueError("OpenAI extraction response was empty.")

        try:
            decoded = raw_response.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("OpenAI extraction response must be UTF-8 JSON.") from error

        try:
            response_payload = loads_json_without_duplicate_keys(decoded)
        except json.JSONDecodeError as error:
            raise ValueError("OpenAI extraction response must be valid JSON.") from error
        if not isinstance(response_payload, dict):
            raise ValueError("OpenAI extraction response must be a JSON object.")

        return response_payload


class OpenAIResponsesAIExtractionClient:
    """AI extraction client backed by the OpenAI Responses API."""

    _default_endpoint = "https://api.openai.com/v1/responses"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        endpoint: str = _default_endpoint,
        timeout_seconds: float = 30.0,
        max_response_bytes: int = 1_048_576,
        transport: OpenAIResponsesTransport | None = None,
    ) -> None:
        """Create an OpenAI Responses API extraction client."""
        self._api_key = _required_text(api_key, "OpenAI API key")
        self._model = _required_text(model, "OpenAI model")
        self._endpoint = _required_text(endpoint, "OpenAI endpoint")
        if isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
            raise ValueError("OpenAI timeout_seconds must be positive.")
        if isinstance(max_response_bytes, bool) or max_response_bytes < 1:
            raise ValueError("OpenAI max_response_bytes must be positive.")
        self._timeout_seconds = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._transport = transport or UrllibOpenAIResponsesTransport()

    def complete(self, prompt: str) -> str:
        """Return a JSON extraction response for the prompt."""
        prompt_text = _required_text(prompt, "OpenAI extraction prompt")
        try:
            response_payload = self._transport.post_json(
                url=self._endpoint,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                payload={
                    "model": self._model,
                    "input": prompt_text,
                    "store": False,
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "aevryn_scene_extraction",
                            "strict": True,
                            "schema": _extraction_response_schema(),
                        }
                    },
                },
                timeout_seconds=self._timeout_seconds,
                max_response_bytes=self._max_response_bytes,
            )
        except TimeoutError as error:
            raise ValueError("OpenAI extraction request timed out.") from error
        output_text = _responses_output_text(response_payload)
        logger.info(
            "openai_extraction_response_received",
            extra={"model": self._model},
        )
        return output_text


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
    _entity_item_keys = frozenset(
        {"entity_id", "entity_type", "display_name", "evidence_anchor_id", "confidence"}
    )
    _fact_item_keys = frozenset(
        {"fact_id", "entity_id", "attribute", "value", "evidence_anchor_id", "confidence"}
    )
    _relationship_item_keys = frozenset(
        {
            "source_entity_id",
            "relationship_type",
            "target_entity_id",
            "evidence_anchor_id",
            "confidence",
        }
    )
    _state_change_item_keys = frozenset(
        {"entity_id", "attribute", "value", "valid_from_anchor_id", "confidence"}
    )
    _state_change_optional_item_keys = frozenset({"valid_until_anchor_id"})
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
                "You extract candidates for aevryn.",
                "The AI may propose. Canon decides.",
                "Use only the provided evidence anchors.",
                "Do not infer unsupported claims.",
                "If information is not stated, omit it. Unknown stays unknown.",
                "Use entity_type=character for named people or persons.",
                (
                    "For characters, capture explicit identity facts when stated, "
                    "especially gender, race, species, age, role, title, profession, "
                    "appearance, family, relationships, equipment, abilities, assets, "
                    "goals, limitations, and current status."
                ),
                (
                    "Gendered relationship or title words such as sister, brother, "
                    "mother, father, wife, husband, princess, or prince are explicit "
                    "gender evidence only for the character being described. Race or "
                    "species labels such as Half-Beastman are explicit race/species "
                    "evidence only for the character being described. Do not infer "
                    "gender or race from another character, from a group merely being "
                    "discussed, or from a chapter title/question. Gendered group "
                    "phrases such as female soldiers or male recruits describe the "
                    "group, not a separate named character."
                ),
                (
                    "Use stable character fact attributes such as gender, race, species, "
                    "role, profession, appearance, family_context, relationship_context, "
                    "current_equipment, current_abilities, current_assets, current_goal, "
                    "current_limitation, and status."
                ),
                (
                    "Use entity_type=system only for named power systems, interfaces, "
                    "game-like systems, or other non-physical governing mechanisms. "
                    "Use entity_type=skill only for usable abilities, techniques, spells, "
                    "talents, or powers. Use item, weapon, armor, vehicle, or building "
                    "for physical things even when a system grants, prices, stores, or "
                    "describes them."
                ),
                (
                    "Allowed entity_type values: armor, building, character, creature, "
                    "item, location, organization, skill, system, timeline_event, vehicle, "
                    "weapon."
                ),
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
            payload = loads_json_without_duplicate_keys(raw_response)
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
                entity_id=cls._required_machine_str(item, "entity_id"),
                entity_type=cls._required_machine_str(item, "entity_type"),
                display_name=cls._required_str(item, "display_name"),
                evidence_anchor_id=cls._required_machine_str(
                    item,
                    "evidence_anchor_id",
                ),
                confidence=cls._required_confidence(item),
            )
            for item in cls._items(
                payload,
                "entities",
                required_keys=cls._entity_item_keys,
            )
        )

    @classmethod
    def _facts(cls, payload: dict[str, Any]) -> tuple[ExtractedFact, ...]:
        """Parse fact candidates from a payload."""
        return tuple(
            ExtractedFact(
                fact_id=cls._required_machine_str(item, "fact_id"),
                entity_id=cls._required_machine_str(item, "entity_id"),
                attribute=cls._required_machine_str(item, "attribute"),
                value=cls._required_str(item, "value"),
                evidence_anchor_id=cls._required_machine_str(
                    item,
                    "evidence_anchor_id",
                ),
                confidence=cls._required_confidence(item),
            )
            for item in cls._items(
                payload,
                "facts",
                required_keys=cls._fact_item_keys,
            )
        )

    @classmethod
    def _relationships(cls, payload: dict[str, Any]) -> tuple[ExtractedRelationship, ...]:
        """Parse relationship candidates from a payload."""
        return tuple(
            ExtractedRelationship(
                source_entity_id=cls._required_machine_str(item, "source_entity_id"),
                relationship_type=cls._required_machine_str(item, "relationship_type"),
                target_entity_id=cls._required_machine_str(item, "target_entity_id"),
                evidence_anchor_id=cls._required_machine_str(
                    item,
                    "evidence_anchor_id",
                ),
                confidence=cls._required_confidence(item),
            )
            for item in cls._items(
                payload,
                "relationships",
                required_keys=cls._relationship_item_keys,
            )
        )

    @classmethod
    def _state_changes(cls, payload: dict[str, Any]) -> tuple[ExtractedStateChange, ...]:
        """Parse state-change candidates from a payload."""
        return tuple(
            ExtractedStateChange(
                entity_id=cls._required_machine_str(item, "entity_id"),
                attribute=cls._required_machine_str(item, "attribute"),
                value=cls._required_str(item, "value"),
                valid_from_anchor_id=cls._required_machine_str(
                    item,
                    "valid_from_anchor_id",
                ),
                valid_until_anchor_id=cls._optional_machine_str(
                    item,
                    "valid_until_anchor_id",
                ),
                confidence=cls._required_confidence(item),
            )
            for item in cls._items(
                payload,
                "state_changes",
                required_keys=cls._state_change_item_keys,
                optional_keys=cls._state_change_optional_item_keys,
            )
        )

    @staticmethod
    def _items(
        payload: dict[str, Any],
        key: str,
        *,
        required_keys: frozenset[str],
        optional_keys: frozenset[str] = frozenset(),
    ) -> tuple[dict[str, Any], ...]:
        """Return object items from a payload list."""
        value = payload.get(key, [])
        if not isinstance(value, list):
            raise ValueError(f"AI extraction field must be a list: {key}")

        items: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                raise ValueError(f"AI extraction list item must be an object: {key}")
            EvidenceBoundedAIExtractor._validate_item_keys(
                item=item,
                key=key,
                required_keys=required_keys,
                optional_keys=optional_keys,
            )
            items.append(item)

        return tuple(items)

    @staticmethod
    def _validate_item_keys(
        item: dict[str, Any],
        key: str,
        required_keys: frozenset[str],
        optional_keys: frozenset[str],
    ) -> None:
        """Validate the schema keys for one extraction candidate item."""
        keys = set(item)
        missing_keys = required_keys - keys
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(
                f"AI extraction item is missing required fields in {key}: {missing}"
            )

        unsupported_keys = keys - required_keys - optional_keys
        if unsupported_keys:
            unsupported = ", ".join(sorted(unsupported_keys))
            raise ValueError(
                f"AI extraction item has unsupported fields in {key}: {unsupported}"
            )

    @staticmethod
    def _required_str(item: dict[str, Any], key: str) -> str:
        """Read a required string from a payload item."""
        value = item.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"AI extraction field must be a non-empty string: {key}")
        return EvidenceBoundedAIExtractor._normalize_text(value.strip())

    @staticmethod
    def _required_machine_str(item: dict[str, Any], key: str) -> str:
        """Read a required machine-token string from a payload item."""
        value = EvidenceBoundedAIExtractor._required_str(item, key)
        EvidenceBoundedAIExtractor._validate_machine_token(value=value, key=key)
        return value

    @staticmethod
    def _optional_str(item: dict[str, Any], key: str) -> str | None:
        """Read an optional string from a payload item."""
        value = item.get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"AI extraction field must be a string or null: {key}")
        return EvidenceBoundedAIExtractor._normalize_text(value.strip())

    @staticmethod
    def _optional_machine_str(item: dict[str, Any], key: str) -> str | None:
        """Read an optional machine-token string from a payload item."""
        value = EvidenceBoundedAIExtractor._optional_str(item, key)
        if value is None:
            return None
        EvidenceBoundedAIExtractor._validate_machine_token(value=value, key=key)
        return value

    @staticmethod
    def _validate_machine_token(value: str, key: str) -> None:
        """Validate that a machine field has no whitespace."""
        if any(character.isspace() for character in value):
            raise ValueError(f"AI extraction machine field cannot contain spaces: {key}")

    @staticmethod
    def _required_confidence(item: dict[str, Any]) -> float:
        """Read a required confidence value from a payload item."""
        value = item.get("confidence")
        if isinstance(value, bool) or not isinstance(value, int | float):
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


def _responses_output_text(response_payload: Mapping[str, Any]) -> str:
    """Return concatenated output text from an OpenAI Responses API payload."""
    direct_output = response_payload.get("output_text")
    if isinstance(direct_output, str) and direct_output.strip():
        return direct_output.strip()

    output_parts: list[str] = []
    output = response_payload.get("output")
    if isinstance(output, list):
        for output_item in output:
            if not isinstance(output_item, dict):
                continue
            content = output_item.get("content")
            if not isinstance(content, list):
                continue
            for content_item in content:
                if not isinstance(content_item, dict):
                    continue
                if content_item.get("type") != "output_text":
                    continue
                text = content_item.get("text")
                if isinstance(text, str) and text.strip():
                    output_parts.append(text.strip())

    if not output_parts:
        raise ValueError("OpenAI extraction response did not include output text.")
    return "\n".join(output_parts)


def _required_text(value: str, field_name: str) -> str:
    """Return a nonblank text value."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} cannot be blank.")
    return value.strip()


def _extraction_response_schema() -> dict[str, object]:
    """Return the provider schema for evidence-bounded extraction JSON."""
    machine_token = {"type": "string", "pattern": r"^\S+$"}
    entity_type = {
        "type": "string",
        "enum": [
            "armor",
            "building",
            "character",
            "creature",
            "item",
            "location",
            "organization",
            "skill",
            "system",
            "timeline_event",
            "vehicle",
            "weapon",
        ],
    }
    entity = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "entity_id": machine_token,
            "entity_type": entity_type,
            "display_name": {"type": "string"},
            "evidence_anchor_id": machine_token,
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
        "required": [
            "entity_id",
            "entity_type",
            "display_name",
            "evidence_anchor_id",
            "confidence",
        ],
    }
    fact = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "fact_id": machine_token,
            "entity_id": machine_token,
            "attribute": machine_token,
            "value": {"type": "string"},
            "evidence_anchor_id": machine_token,
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
        "required": [
            "fact_id",
            "entity_id",
            "attribute",
            "value",
            "evidence_anchor_id",
            "confidence",
        ],
    }
    relationship = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "source_entity_id": machine_token,
            "relationship_type": machine_token,
            "target_entity_id": machine_token,
            "evidence_anchor_id": machine_token,
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
        "required": [
            "source_entity_id",
            "relationship_type",
            "target_entity_id",
            "evidence_anchor_id",
            "confidence",
        ],
    }
    state_change = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "entity_id": machine_token,
            "attribute": machine_token,
            "value": {"type": "string"},
            "valid_from_anchor_id": machine_token,
            "valid_until_anchor_id": {
                "anyOf": [
                    machine_token,
                    {"type": "null"},
                ]
            },
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
        "required": [
            "entity_id",
            "attribute",
            "value",
            "valid_from_anchor_id",
            "valid_until_anchor_id",
            "confidence",
        ],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "entities": {"type": "array", "items": entity},
            "facts": {"type": "array", "items": fact},
            "relationships": {"type": "array", "items": relationship},
            "state_changes": {"type": "array", "items": state_change},
        },
        "required": [
            "entities",
            "facts",
            "relationships",
            "state_changes",
        ],
    }

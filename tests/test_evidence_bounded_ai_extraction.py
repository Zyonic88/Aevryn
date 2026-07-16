"""Tests for evidence-bounded AI extraction."""

import json
from collections.abc import Mapping
from typing import Any, cast

import pytest

from aevryn import (
    EntityExtractionEngine,
    EvidenceBoundedAIExtractor,
    ExtractedFact,
    ExtractedStateChange,
    OpenAIResponsesAIExtractionClient,
    StoryImporter,
)


class JsonClient:
    """AI client test double that returns a fixed JSON response."""

    def __init__(self, response: str) -> None:
        """Create the client."""
        self.response = response
        self.prompt = ""

    def complete(self, prompt: str) -> str:
        """Return the configured response and remember the prompt."""
        self.prompt = prompt
        return self.response


class RecordingOpenAITransport:
    """Transport test double for OpenAI Responses client tests."""

    def __init__(self, response_payload: dict[str, object]) -> None:
        """Create the transport."""
        self.response_payload = response_payload
        self.url = ""
        self.headers: dict[str, str] = {}
        self.payload: dict[str, object] = {}
        self.timeout_seconds = 0.0
        self.max_response_bytes = 0

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> dict[str, object]:
        """Record the request and return the configured payload."""
        self.url = url
        self.headers = dict(headers)
        self.payload = dict(payload)
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        return self.response_payload


class TimeoutOpenAITransport:
    """Transport test double that simulates a provider read timeout."""

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> dict[str, object]:
        """Raise a deterministic timeout."""
        raise TimeoutError("The read operation timed out")


def imported_source_text() -> str:
    """Return source text for AI extraction tests."""
    return """Chapter 1
Mark bought an iron sword.

Luna watched from the doorway."""


def test_ai_extractor_returns_evidence_bounded_candidates() -> None:
    """AI extraction parses entities, facts, relationships, and state changes."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    anchor_id = imported.anchors[0].anchor_id
    client = JsonClient(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "character_mark",
                        "entity_type": "character",
                        "display_name": "Mark",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.95,
                    }
                ],
                "facts": [
                    {
                        "fact_id": "fact_character_mark_current_weapon_iron_sword",
                        "entity_id": "character_mark",
                        "attribute": "current_weapon",
                        "value": "Iron Sword",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.9,
                    }
                ],
                "relationships": [
                    {
                        "source_entity_id": "character_mark",
                        "relationship_type": "owns",
                        "target_entity_id": "item_iron_sword",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.85,
                    }
                ],
                "state_changes": [
                    {
                        "entity_id": "character_mark",
                        "attribute": "current_weapon",
                        "value": "Iron Sword",
                        "valid_from_anchor_id": anchor_id,
                        "valid_until_anchor_id": None,
                        "confidence": 0.9,
                    }
                ],
            }
        )
    )
    engine = EntityExtractionEngine(extractor=EvidenceBoundedAIExtractor(client))

    result = engine.extract_imported_source(imported)[0]

    assert isinstance(result.facts[0], ExtractedFact)
    assert isinstance(result.state_changes[0], ExtractedStateChange)
    assert "Unknown stays unknown." in client.prompt
    assert "Use entity_type=character for named people or persons." in client.prompt
    assert "especially gender, race, species" in client.prompt
    assert "sister, brother" in client.prompt
    assert "Half-Beastman" in client.prompt
    assert "gender, race, species, role" in client.prompt
    assert "Use entity_type=system only for named power systems" in client.prompt
    assert "Use entity_type=skill only for usable abilities" in client.prompt
    assert anchor_id in client.prompt


def test_openai_responses_client_returns_output_text_without_network() -> None:
    """OpenAI client should adapt Responses payloads into extraction JSON text."""
    transport = RecordingOpenAITransport(
        {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(
                                {
                                    "entities": [],
                                    "facts": [],
                                    "relationships": [],
                                    "state_changes": [],
                                }
                            ),
                        }
                    ],
                }
            ]
        }
    )
    client = OpenAIResponsesAIExtractionClient(
        api_key="test-key",
        model="test-model",
        transport=transport,
    )

    output = client.complete("extract this scene")

    assert json.loads(output) == {
        "entities": [],
        "facts": [],
        "relationships": [],
        "state_changes": [],
    }
    assert transport.url == "https://api.openai.com/v1/responses"
    assert transport.headers["Authorization"] == "Bearer test-key"
    payload = cast(dict[str, Any], transport.payload)
    text_config = cast(dict[str, Any], payload["text"])
    format_config = cast(dict[str, Any], text_config["format"])
    assert payload["model"] == "test-model"
    assert payload["input"] == "extract this scene"
    assert payload["store"] is False
    assert format_config["type"] == "json_schema"
    assert format_config["name"] == "aevryn_scene_extraction"
    assert format_config["strict"] is True
    schema = format_config["schema"]
    relationship_schema = schema["properties"]["relationships"]["items"]
    assert relationship_schema["properties"]["relationship_type"] == {
        "type": "string",
        "pattern": r"^\S+$",
    }
    entity_schema = schema["properties"]["entities"]["items"]
    assert "character" in entity_schema["properties"]["entity_type"]["enum"]
    assert "system" in entity_schema["properties"]["entity_type"]["enum"]
    assert transport.timeout_seconds == 30.0
    assert transport.max_response_bytes == 1_048_576


def test_openai_responses_client_rejects_missing_output_text() -> None:
    """OpenAI client should fail cleanly when the response lacks text."""
    client = OpenAIResponsesAIExtractionClient(
        api_key="test-key",
        model="test-model",
        transport=RecordingOpenAITransport({"output": []}),
    )

    with pytest.raises(ValueError, match="did not include output text"):
        client.complete("extract this scene")


def test_openai_responses_client_reports_timeouts_without_transport_details() -> None:
    """OpenAI client should normalize provider read timeouts."""
    client = OpenAIResponsesAIExtractionClient(
        api_key="test-key",
        model="test-model",
        transport=TimeoutOpenAITransport(),
    )

    with pytest.raises(ValueError, match="OpenAI extraction request timed out"):
        client.complete("extract this scene")


def test_openai_responses_transport_requires_https_endpoint() -> None:
    """OpenAI transport should reject non-HTTPS endpoints before network I/O."""
    client = OpenAIResponsesAIExtractionClient(
        api_key="test-key",
        model="test-model",
        endpoint="http://api.openai.local/v1/responses",
    )

    with pytest.raises(ValueError, match="endpoint must be an HTTPS URL"):
        client.complete("extract this scene")


def test_ai_extractor_rejects_unknown_evidence_anchor() -> None:
    """AI candidates cannot cite anchors outside the imported scene."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    client = JsonClient(
        json.dumps(
            {
                "facts": [
                    {
                        "fact_id": "fact_character_mark_current_weapon_iron_sword",
                        "entity_id": "character_mark",
                        "attribute": "current_weapon",
                        "value": "Iron Sword",
                        "evidence_anchor_id": "missing_anchor",
                        "confidence": 0.9,
                    }
                ],
                "entities": [],
                "relationships": [],
                "state_changes": [],
            }
        )
    )
    engine = EntityExtractionEngine(extractor=EvidenceBoundedAIExtractor(client))

    with pytest.raises(ValueError, match="Unknown evidence anchor"):
        engine.extract_imported_source(imported)


def test_ai_extractor_rejects_invalid_json() -> None:
    """AI responses must be machine-readable candidate JSON."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(JsonClient("not json"))
    )

    with pytest.raises(ValueError, match="valid JSON"):
        engine.extract_imported_source(imported)


def test_ai_extractor_accepts_utf8_bom_json() -> None:
    """AI response files saved with a UTF-8 BOM are accepted."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(
            JsonClient(
                '\ufeff{"entities": [], "facts": [], '
                '"relationships": [], "state_changes": []}'
            )
        )
    )

    result = engine.extract_imported_source(imported)[0]

    assert result.entities == ()


def test_ai_extractor_repairs_candidate_mojibake() -> None:
    """AI candidate strings are normalized before Canon sees them."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    anchor_id = imported.anchors[0].anchor_id
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(
            JsonClient(
                json.dumps(
                    {
                        "entities": [
                            {
                                "entity_id": "character_jiang_shasha",
                                "entity_type": "character",
                                "display_name": "Jiang Shasha",
                                "evidence_anchor_id": anchor_id,
                                "confidence": 1.0,
                            }
                        ],
                        "facts": [
                            {
                                "fact_id": "fact_jiang_relationship",
                                "entity_id": "character_jiang_shasha",
                                "attribute": "relationship_context",
                                "value": "Zhao Chen's fiancÃƒÂ©e",
                                "evidence_anchor_id": anchor_id,
                                "confidence": 1.0,
                            }
                        ],
                        "relationships": [],
                        "state_changes": [],
                    }
                )
            )
        )
    )

    result = engine.extract_imported_source(imported)[0]

    assert result.facts[0].value == "Zhao Chen's fiancée"


def test_ai_extractor_trims_candidate_strings() -> None:
    """AI candidate strings are stripped before Canon sees them."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    anchor_id = imported.anchors[0].anchor_id
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(
            JsonClient(
                json.dumps(
                    {
                        "entities": [
                            {
                                "entity_id": " character_mark ",
                                "entity_type": " character ",
                                "display_name": " Mark ",
                                "evidence_anchor_id": f" {anchor_id} ",
                                "confidence": 1.0,
                            }
                        ],
                        "facts": [
                            {
                                "fact_id": " fact_character_mark_current_weapon ",
                                "entity_id": " character_mark ",
                                "attribute": " current_weapon ",
                                "value": " Iron Sword ",
                                "evidence_anchor_id": f" {anchor_id} ",
                                "confidence": 1.0,
                            }
                        ],
                        "relationships": [],
                        "state_changes": [],
                    }
                )
            )
        )
    )

    result = engine.extract_imported_source(imported)[0]

    assert result.entities[0].entity_id == "character_mark"
    assert result.entities[0].entity_type == "character"
    assert result.entities[0].display_name == "Mark"
    assert result.facts[0].fact_id == "fact_character_mark_current_weapon"
    assert result.facts[0].value == "Iron Sword"


def test_ai_extractor_rejects_machine_fields_with_spaces() -> None:
    """AI machine fields must remain stable whitespace-free tokens."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    anchor_id = imported.anchors[0].anchor_id
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(
            JsonClient(
                json.dumps(
                    {
                        "entities": [],
                        "facts": [
                            {
                                "fact_id": "fact_character_mark_current_weapon",
                                "entity_id": "character_mark",
                                "attribute": "current weapon",
                                "value": "Iron Sword",
                                "evidence_anchor_id": anchor_id,
                                "confidence": 1.0,
                            }
                        ],
                        "relationships": [],
                        "state_changes": [],
                    }
                )
            )
        )
    )

    with pytest.raises(ValueError, match="machine field cannot contain spaces"):
        engine.extract_imported_source(imported)


def test_ai_extractor_rejects_missing_required_payload_keys() -> None:
    """AI responses must include the full candidate payload shape."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(JsonClient('{"entities": []}'))
    )

    with pytest.raises(ValueError, match="missing required keys"):
        engine.extract_imported_source(imported)


def test_ai_extractor_rejects_unsupported_payload_keys() -> None:
    """AI responses cannot include unsupported top-level fields."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(
            JsonClient(
                json.dumps(
                    {
                        "entities": [],
                        "facts": [],
                        "relationships": [],
                        "state_changes": [],
                        "summary": "unsupported",
                    }
                )
            )
        )
    )

    with pytest.raises(ValueError, match="unsupported keys"):
        engine.extract_imported_source(imported)


def test_ai_extractor_rejects_duplicate_json_keys() -> None:
    """AI JSON objects cannot rely on last-key-wins parsing."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(
            JsonClient(
                '{"entities": [], "entities": [], '
                '"facts": [], "relationships": [], "state_changes": []}'
            )
        )
    )

    with pytest.raises(ValueError, match="duplicate key"):
        engine.extract_imported_source(imported)


def test_ai_extractor_rejects_unsupported_candidate_fields() -> None:
    """AI candidate items cannot include unsupported explanatory fields."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    anchor_id = imported.anchors[0].anchor_id
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(
            JsonClient(
                json.dumps(
                    {
                        "entities": [
                            {
                                "entity_id": "character_mark",
                                "entity_type": "character",
                                "display_name": "Mark",
                                "evidence_anchor_id": anchor_id,
                                "confidence": 0.95,
                                "reasoning": "unsupported",
                            }
                        ],
                        "facts": [],
                        "relationships": [],
                        "state_changes": [],
                    }
                )
            )
        )
    )

    with pytest.raises(ValueError, match="unsupported fields in entities"):
        engine.extract_imported_source(imported)


def test_ai_extractor_rejects_missing_candidate_fields() -> None:
    """AI candidate items must include the complete required schema."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    anchor_id = imported.anchors[0].anchor_id
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(
            JsonClient(
                json.dumps(
                    {
                        "entities": [],
                        "facts": [
                            {
                                "fact_id": "fact_character_mark_current_weapon",
                                "entity_id": "character_mark",
                                "attribute": "current_weapon",
                                "value": "Iron Sword",
                                "evidence_anchor_id": anchor_id,
                            }
                        ],
                        "relationships": [],
                        "state_changes": [],
                    }
                )
            )
        )
    )

    with pytest.raises(ValueError, match="missing required fields in facts"):
        engine.extract_imported_source(imported)


def test_ai_extractor_rejects_out_of_range_confidence() -> None:
    """AI confidence must be bounded before Canon Updating sees candidates."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    anchor_id = imported.anchors[0].anchor_id
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(
            JsonClient(
                json.dumps(
                    {
                        "entities": [
                            {
                                "entity_id": "character_mark",
                                "entity_type": "character",
                                "display_name": "Mark",
                                "evidence_anchor_id": anchor_id,
                                "confidence": 1.5,
                            }
                        ],
                        "facts": [],
                        "relationships": [],
                        "state_changes": [],
                    }
                )
            )
        )
    )

    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        engine.extract_imported_source(imported)


def test_ai_extractor_rejects_boolean_confidence() -> None:
    """AI confidence must be a real numeric score, not a boolean."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    anchor_id = imported.anchors[0].anchor_id
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(
            JsonClient(
                json.dumps(
                    {
                        "entities": [
                            {
                                "entity_id": "character_mark",
                                "entity_type": "character",
                                "display_name": "Mark",
                                "evidence_anchor_id": anchor_id,
                                "confidence": True,
                            }
                        ],
                        "facts": [],
                        "relationships": [],
                        "state_changes": [],
                    }
                )
            )
        )
    )

    with pytest.raises(ValueError, match="confidence must be numeric"):
        engine.extract_imported_source(imported)


def test_ai_extractor_repairs_cjk_bracket_mojibake() -> None:
    """AI candidate strings receive the same bracket repair as Story Import."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    anchor_id = imported.anchors[0].anchor_id
    engine = EntityExtractionEngine(
        extractor=EvidenceBoundedAIExtractor(
            JsonClient(
                json.dumps(
                    {
                        "entities": [
                            {
                                "entity_id": "system_super_starfleet_system",
                                "entity_type": "system",
                                "display_name": (
                                    "\u00e3\u20ac\u0090Super Starfleet System"
                                    "\u00e3\u20ac\u0091"
                                ),
                                "evidence_anchor_id": anchor_id,
                                "confidence": 1.0,
                            }
                        ],
                        "facts": [],
                        "relationships": [],
                        "state_changes": [],
                    }
                )
            )
        )
    )

    result = engine.extract_imported_source(imported)[0]

    assert result.entities[0].display_name == "【Super Starfleet System】"

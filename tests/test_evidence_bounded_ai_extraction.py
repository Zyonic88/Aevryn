"""Tests for evidence-bounded AI extraction."""

import json

import pytest

from scenesmith import (
    EntityExtractionEngine,
    EvidenceBoundedAIExtractor,
    ExtractedFact,
    ExtractedStateChange,
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
    assert anchor_id in client.prompt


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

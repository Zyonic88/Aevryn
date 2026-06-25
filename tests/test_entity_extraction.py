"""Tests for Phase 4 Entity Extraction."""

import pytest

from scenesmith import (
    EntityExtractionEngine,
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionResult,
    SceneExtractionInput,
    StoryImporter,
)


class FakeExtractor:
    """Test extractor that behaves like an AI boundary without calling AI."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return deterministic candidates for tests."""
        first_anchor = scene.evidence_anchor_ids[0]
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="character_mark",
                    entity_type="character",
                    display_name="Mark",
                    evidence_anchor_id=first_anchor,
                    confidence=0.95,
                ),
                ExtractedEntity(
                    entity_id="item_iron_sword",
                    entity_type="item",
                    display_name="Iron Sword",
                    evidence_anchor_id=first_anchor,
                    confidence=0.9,
                ),
            ),
            relationships=(
                ExtractedRelationship(
                    source_entity_id="character_mark",
                    relationship_type="owns",
                    target_entity_id="item_iron_sword",
                    evidence_anchor_id=first_anchor,
                    confidence=0.85,
                ),
            ),
        )


class BadAnchorExtractor:
    """Extractor that returns an unsupported evidence anchor."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return a candidate with an invalid anchor."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="character_mark",
                    entity_type="character",
                    display_name="Mark",
                    evidence_anchor_id="missing_anchor",
                    confidence=0.95,
                ),
            ),
        )


class BadConfidenceExtractor:
    """Extractor that returns an invalid confidence score."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return a candidate with invalid confidence."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="character_mark",
                    entity_type="character",
                    display_name="Mark",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=1.5,
                ),
            ),
        )


def imported_source_text() -> str:
    """Return source text for extraction tests."""
    return """Chapter 1
Mark lifted the iron sword.

The bridge was silent."""


def test_extract_imported_source_returns_candidates_with_evidence() -> None:
    """Entity Extraction proposes candidates tied to Story Import anchors."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=FakeExtractor())

    results = engine.extract_imported_source(imported)

    assert len(results) == 1
    assert results[0].entities[0].entity_id == "character_mark"
    assert results[0].entities[0].evidence_anchor_id == imported.anchors[0].anchor_id
    assert results[0].relationships[0].relationship_type == "owns"


def test_extraction_result_does_not_update_canon() -> None:
    """Extraction returns candidates only; Canon Updating happens later."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=FakeExtractor())

    result = engine.extract_imported_source(imported)[0]

    assert isinstance(result, ExtractionResult)
    assert result.entities
    assert result.relationships


def test_extraction_rejects_candidates_without_known_anchor() -> None:
    """Extractor candidates must reference Story Import evidence anchors."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=BadAnchorExtractor())

    with pytest.raises(ValueError, match="Unknown evidence anchor"):
        engine.extract_imported_source(imported)


def test_extraction_rejects_invalid_confidence() -> None:
    """Extractor candidates must include valid confidence."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=BadConfidenceExtractor())

    with pytest.raises(ValueError, match="confidence"):
        engine.extract_imported_source(imported)

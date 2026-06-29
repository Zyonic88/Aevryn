"""Tests for Phase 4 Entity Extraction."""

from typing import Any, cast

import pytest

from aevryn import (
    EntityExtractionEngine,
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractedStateChange,
    ExtractionResult,
    SceneEvidenceAnchor,
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


class MixedAnchorExtractor:
    """Extractor that returns grounded and ungrounded candidates."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return mixed candidates for tolerant provider workflow tests."""
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
                    entity_id="character_ghost",
                    entity_type="character",
                    display_name="Ghost",
                    evidence_anchor_id="missing_anchor",
                    confidence=0.95,
                ),
            ),
            facts=(
                ExtractedFact(
                    fact_id="fact_mark_weapon",
                    entity_id="character_mark",
                    attribute="current_weapon",
                    value="Iron Sword",
                    evidence_anchor_id=first_anchor,
                    confidence=0.9,
                ),
                ExtractedFact(
                    fact_id="fact_ghost_weapon",
                    entity_id="character_ghost",
                    attribute="current_weapon",
                    value="Shadow Blade",
                    evidence_anchor_id="missing_anchor",
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
                ExtractedRelationship(
                    source_entity_id="character_ghost",
                    relationship_type="owns",
                    target_entity_id="item_shadow_blade",
                    evidence_anchor_id="missing_anchor",
                    confidence=0.85,
                ),
            ),
            state_changes=(
                ExtractedStateChange(
                    entity_id="character_mark",
                    attribute="current_weapon",
                    value="Iron Sword",
                    valid_from_anchor_id=first_anchor,
                    confidence=0.9,
                ),
                ExtractedStateChange(
                    entity_id="character_ghost",
                    attribute="current_weapon",
                    value="Shadow Blade",
                    valid_from_anchor_id="missing_anchor",
                    confidence=0.9,
                ),
            ),
        )


class ReusedFactIdExtractor:
    """Extractor that reuses one generic fact ID across scenes."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return a scene-specific fact with a generic reused ID."""
        first_anchor = scene.evidence_anchor_ids[0]
        scene_suffix = scene.scene_id.rsplit("_", maxsplit=1)[-1]
        entity_id = f"character_mark_{scene_suffix}"
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id=entity_id,
                    entity_type="character",
                    display_name=f"Mark {scene_suffix}",
                    evidence_anchor_id=first_anchor,
                    confidence=0.95,
                ),
            ),
            facts=(
                ExtractedFact(
                    fact_id="fact_1",
                    entity_id=entity_id,
                    attribute="current_weapon",
                    value=f"Iron Sword {scene_suffix}",
                    evidence_anchor_id=first_anchor,
                    confidence=0.9,
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


class WrongSceneIdExtractor:
    """Extractor that returns candidates under the wrong scene ID."""

    def extract_scene(self, _scene: SceneExtractionInput) -> ExtractionResult:
        """Return a result that does not match the requested scene."""
        return ExtractionResult(scene_id="source_demo_chapter_999_scene_001")


class DuplicateCandidateExtractor:
    """Extractor that returns duplicate candidate identities."""

    def __init__(self, duplicate_kind: str) -> None:
        """Create a duplicate-candidate extractor."""
        self._duplicate_kind = duplicate_kind

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return duplicate candidates of the configured kind."""
        first_anchor = scene.evidence_anchor_ids[0]
        if self._duplicate_kind == "entity":
            entity = ExtractedEntity(
                entity_id="character_mark",
                entity_type="character",
                display_name="Mark",
                evidence_anchor_id=first_anchor,
                confidence=0.95,
            )
            return ExtractionResult(scene_id=scene.scene_id, entities=(entity, entity))
        if self._duplicate_kind == "fact":
            fact = ExtractedFact(
                fact_id="fact_mark_weapon",
                entity_id="character_mark",
                attribute="current_weapon",
                value="Iron Sword",
                evidence_anchor_id=first_anchor,
                confidence=0.95,
            )
            return ExtractionResult(scene_id=scene.scene_id, facts=(fact, fact))
        if self._duplicate_kind == "relationship":
            relationship = ExtractedRelationship(
                source_entity_id="character_mark",
                relationship_type="owns",
                target_entity_id="item_iron_sword",
                evidence_anchor_id=first_anchor,
                confidence=0.95,
            )
            return ExtractionResult(
                scene_id=scene.scene_id,
                relationships=(relationship, relationship),
            )

        state_change = ExtractedStateChange(
            entity_id="character_mark",
            attribute="current_weapon",
            value="Iron Sword",
            valid_from_anchor_id=first_anchor,
            confidence=0.95,
        )
        return ExtractionResult(
            scene_id=scene.scene_id,
            state_changes=(state_change, state_change),
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


def test_extraction_can_filter_candidates_without_known_anchor() -> None:
    """Provider workflow can quarantine ungrounded candidates."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(
        extractor=MixedAnchorExtractor(),
        unknown_anchor_policy="reject_candidate",
    )

    result = engine.extract_imported_source(imported)[0]

    assert tuple(entity.entity_id for entity in result.entities) == ("character_mark",)
    assert tuple(fact.fact_id for fact in result.facts) == ("fact_mark_weapon",)
    assert tuple(
        relationship.source_entity_id for relationship in result.relationships
    ) == ("character_mark",)
    assert tuple(
        state_change.entity_id for state_change in result.state_changes
    ) == ("character_mark",)


def test_extraction_rewrites_cross_scene_fact_id_collisions() -> None:
    """Generic AI fact IDs are made unique before Canon sees them."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=(
            "Chapter 1\n"
            "Mark lifted the iron sword.\n\n"
            "Chapter 2\n"
            "Mark lowered the iron sword."
        ),
    )
    engine = EntityExtractionEngine(extractor=ReusedFactIdExtractor())

    results = engine.extract_imported_source(imported)

    fact_ids = tuple(
        fact.fact_id
        for result in results
        for fact in result.facts
    )
    assert len(fact_ids) == 2
    assert len(set(fact_ids)) == 2
    assert "fact_1" not in fact_ids
    assert all(fact_id.startswith("fact_character_mark_") for fact_id in fact_ids)


def test_extraction_rejects_invalid_unknown_anchor_policy() -> None:
    """Unknown anchor policy names are explicit configuration errors."""
    with pytest.raises(ValueError, match="Unknown anchor policy"):
        EntityExtractionEngine(
            extractor=FakeExtractor(),
            unknown_anchor_policy=cast(Any, "ignore"),
        )


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


def test_extraction_rejects_wrong_result_scene_id() -> None:
    """Extractor results must belong to the scene being processed."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=WrongSceneIdExtractor())

    with pytest.raises(ValueError, match="wrong scene_id"):
        engine.extract_imported_source(imported)


@pytest.mark.parametrize(
    ("duplicate_kind", "message"),
    (
        ("entity", "duplicate entity IDs"),
        ("fact", "duplicate fact IDs"),
        ("state_change", "duplicate state-change candidates"),
    ),
)
def test_extraction_rejects_duplicate_candidates(
    duplicate_kind: str,
    message: str,
) -> None:
    """Extractor results must not repeat candidate identities."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(
        extractor=DuplicateCandidateExtractor(duplicate_kind)
    )

    with pytest.raises(ValueError, match=message):
        engine.extract_imported_source(imported)


def test_extraction_dedupes_duplicate_relationship_candidates() -> None:
    """Repeated semantic relationships should not fail an AI-backed run."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(
        extractor=DuplicateCandidateExtractor("relationship")
    )

    results = engine.extract_imported_source(imported)

    assert len(results[0].relationships) == 1
    assert results[0].relationships[0].relationship_type == "owns"


def test_extraction_models_reject_invalid_machine_fields() -> None:
    """Extraction candidate IDs and attributes are whitespace-free tokens."""
    with pytest.raises(ValueError, match="Extracted fact attribute"):
        ExtractedFact(
            fact_id="fact_mark_weapon",
            entity_id="character_mark",
            attribute="current weapon",
            value="Iron Sword",
            evidence_anchor_id="anchor_001",
            confidence=0.95,
        )


def test_extraction_models_reject_invalid_confidence() -> None:
    """Extraction candidate confidence is bounded at model construction."""
    with pytest.raises(ValueError, match="Extraction confidence"):
        ExtractedStateChange(
            entity_id="character_mark",
            attribute="current_weapon",
            value="Iron Sword",
            valid_from_anchor_id="anchor_001",
            confidence=1.5,
        )


def test_extraction_models_reject_boolean_confidence() -> None:
    """Extraction candidate confidence must be numeric and not boolean."""
    with pytest.raises(ValueError, match="Extraction confidence"):
        ExtractedEntity(
            entity_id="character_mark",
            entity_type="character",
            display_name="Mark",
            evidence_anchor_id="anchor_001",
            confidence=True,
        )


def test_extraction_models_reject_non_numeric_confidence() -> None:
    """Extraction candidate confidence rejects non-numeric runtime values."""
    with pytest.raises(ValueError, match="Extraction confidence"):
        ExtractedEntity(
            entity_id="character_mark",
            entity_type="character",
            display_name="Mark",
            evidence_anchor_id="anchor_001",
            confidence=cast(Any, "high"),
        )


def test_extraction_models_normalize_human_text_fields() -> None:
    """Extraction candidates normalize text used by downstream canon updates."""
    anchor = SceneEvidenceAnchor(anchor_id="anchor_001", quote=" Mark   draws sword. ")
    scene_input = SceneExtractionInput(
        scene_id="source_chapter_001_scene_001",
        text=" Mark   draws sword. ",
        evidence_anchor_ids=("anchor_001",),
        evidence_anchors=(anchor,),
    )
    entity = ExtractedEntity(
        entity_id="character_mark",
        entity_type="character",
        display_name=" Mark   Stone ",
        evidence_anchor_id="anchor_001",
        confidence=0.9,
    )
    fact = ExtractedFact(
        fact_id="fact_001_weapon",
        entity_id="character_mark",
        attribute="current_weapon",
        value=" Rusty   Dagger ",
        evidence_anchor_id="anchor_001",
        confidence=0.9,
    )
    state_change = ExtractedStateChange(
        entity_id="character_mark",
        attribute="current_weapon",
        value=" Rusty   Dagger ",
        valid_from_anchor_id="anchor_001",
        confidence=0.9,
    )

    assert anchor.quote == " Mark   draws sword. "
    assert scene_input.text == " Mark   draws sword. "
    assert entity.display_name == "Mark Stone"
    assert fact.value == "Rusty Dagger"
    assert state_change.value == "Rusty Dagger"


def test_extraction_result_rejects_direct_duplicate_candidates() -> None:
    """Extraction results reject duplicate identities even outside the engine."""
    entity = ExtractedEntity(
        entity_id="character_mark",
        entity_type="character",
        display_name="Mark",
        evidence_anchor_id="anchor_001",
        confidence=0.9,
    )

    with pytest.raises(ValueError, match="duplicate entity IDs"):
        ExtractionResult(
            scene_id="source_chapter_001_scene_001",
            entities=(entity, entity),
        )


def test_scene_evidence_anchor_rejects_blank_quote() -> None:
    """Scene evidence anchors sent to extractors must preserve source text."""
    with pytest.raises(ValueError, match="Scene evidence anchor quote"):
        SceneEvidenceAnchor(anchor_id="anchor_001", quote=" ")


def test_scene_extraction_input_rejects_duplicate_anchor_ids() -> None:
    """Scene extraction inputs must not repeat allowed source anchors."""
    with pytest.raises(ValueError, match="evidence anchor IDs must be unique"):
        SceneExtractionInput(
            scene_id="source_chapter_001_scene_001",
            text="Mark draws the sword.",
            evidence_anchor_ids=("anchor_001", "anchor_001"),
        )


def test_scene_extraction_input_rejects_duplicate_evidence_anchors() -> None:
    """Full evidence anchors sent to an extractor must be unique."""
    anchor = SceneEvidenceAnchor(anchor_id="anchor_001", quote="Mark draws the sword.")

    with pytest.raises(ValueError, match="evidence anchors must be unique"):
        SceneExtractionInput(
            scene_id="source_chapter_001_scene_001",
            text="Mark draws the sword.",
            evidence_anchor_ids=("anchor_001",),
            evidence_anchors=(anchor, anchor),
        )


def test_scene_extraction_input_rejects_anchor_object_mismatch() -> None:
    """Prompt anchors and allowed anchor IDs must describe the same source anchors."""
    with pytest.raises(ValueError, match="must match evidence anchor IDs"):
        SceneExtractionInput(
            scene_id="source_chapter_001_scene_001",
            text="Mark draws the sword.",
            evidence_anchor_ids=("anchor_001",),
            evidence_anchors=(
                SceneEvidenceAnchor(
                    anchor_id="anchor_002",
                    quote="Mark draws the sword.",
                ),
            ),
        )

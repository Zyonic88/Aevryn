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
    SceneSentenceUnderstanding,
    StoryImporter,
)


class FakeExtractor:
    """Test extractor that behaves like an AI boundary without calling AI."""

    def __init__(self) -> None:
        """Create the extractor."""
        self.scenes: list[SceneExtractionInput] = []

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return deterministic candidates for tests."""
        self.scenes.append(scene)
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


class ReusedInSceneFactIdExtractor:
    """Extractor that reuses one fact ID for different facts in one scene."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return conflicting fact candidates with one generic ID."""
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
            ),
            facts=(
                ExtractedFact(
                    fact_id="fact_1",
                    entity_id="character_mark",
                    attribute="current_weapon",
                    value="Iron Sword",
                    evidence_anchor_id=first_anchor,
                    confidence=0.9,
                ),
                ExtractedFact(
                    fact_id="fact_1",
                    entity_id="character_mark",
                    attribute="current_equipment",
                    value="Iron Sword",
                    evidence_anchor_id=first_anchor,
                    confidence=0.88,
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


class MisclassifiedSkillExtractor:
    """Extractor that labels a concrete object as a skill."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return an obvious item/skill classification conflict."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="skill_t3_blizzard_blueprint",
                    entity_type="skill",
                    display_name=(
                        "T3 Blizzard-class Light Interstellar Battlecruiser "
                        "technical blueprint"
                    ),
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.95,
                ),
            ),
        )


class MisclassifiedPhysicalContainerSkillExtractor:
    """Extractor that labels a physical knowledge/resource container as a skill."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return an obvious physical-container/skill classification conflict."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="skill_source_crystal",
                    entity_type="skill",
                    display_name="Source Crystal",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.94,
                ),
            ),
        )


class ValidSkillExtractor:
    """Extractor that labels a named ability as a skill."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return a valid skill candidate."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="skill_eye_of_insight",
                    entity_type="skill",
                    display_name="Eye of Insight technique",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.93,
                ),
            ),
        )


class MisclassifiedProfessionSkillExtractor:
    """Extractor that labels a rank or profession as a skill."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return an obvious profession/skill classification conflict."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="skill_chief_engineer",
                    entity_type="skill",
                    display_name="Chief Engineer",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.92,
                ),
            ),
        )


class MisclassifiedQuestRewardSkillExtractor:
    """Extractor that labels a story-management concept as a skill."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return an obvious non-capability/skill classification conflict."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="skill_quarterly_task_reward",
                    entity_type="skill",
                    display_name="Quarterly task reward",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.92,
                ),
            ),
        )


class MisclassifiedOrganizationItemExtractor:
    """Extractor that labels an institution as a physical item."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return an obvious organization/item classification conflict."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="item_north_star_academy",
                    entity_type="item",
                    display_name="North Star Starship Military Academy",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.91,
                ),
            ),
        )


class MisclassifiedLocationSkillExtractor:
    """Extractor that labels a place as a usable skill."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return an obvious location/skill classification conflict."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="skill_training_room",
                    entity_type="skill",
                    display_name="Training Room",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.9,
                ),
            ),
        )


class MisclassifiedSystemExtractor:
    """Extractor that labels a concrete object as a system."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return an obvious item/system classification conflict."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="system_starship_blueprint",
                    entity_type="system",
                    display_name="Starship blueprint",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.95,
                ),
            ),
        )


class MisclassifiedSystemItemExtractor:
    """Extractor that labels a named governing system as a physical item."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return an obvious system/item classification conflict."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="item_super_starfleet_system",
                    entity_type="item",
                    display_name="Super Starfleet System",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.94,
                ),
            ),
        )


class ValidSystemExtractor:
    """Extractor that labels a named interface/mechanic as a system."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return a valid system candidate."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="system_super_starfleet",
                    entity_type="system",
                    display_name="Super Starfleet System interface",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.91,
                ),
            ),
        )


class AnonymousGroupCharacterExtractor:
    """Extractor that labels an anonymous group phrase as a character."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return an obvious group/character classification conflict."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="character_female_soldiers",
                    entity_type="character",
                    display_name="Female Soldiers",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.9,
                ),
            ),
        )


class ValidSystemCreatedItemExtractor:
    """Extractor that labels a system-created physical object as an item."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return a physical item that was produced by a story system."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="item_t3_blizzard_blueprint",
                    entity_type="item",
                    display_name=(
                        "T3 Blizzard-class Light Interstellar Battlecruiser technical blueprint"
                    ),
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.91,
                ),
            ),
        )


class RaceGenderGroupCharacterExtractor:
    """Extractor that labels a plural race/gender group as one character."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return a plural group that should stay out of character cards."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="character_female_half_beastman_slaves",
                    entity_type="character",
                    display_name="Female Half-Beastman Slaves",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.9,
                ),
            ),
        )


class SingularUnnamedCharacterExtractor:
    """Extractor that labels a singular unnamed person reference as a character."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return a valid singular unnamed character candidate."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="character_unnamed_female_crew_member",
                    entity_type="character",
                    display_name="Unnamed female crew member",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.88,
                ),
            ),
        )


class MismatchedEntityPrefixExtractor:
    """Extractor that contradicts its entity ID prefix."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return an entity whose ID prefix and type disagree."""
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="item_fireball",
                    entity_type="skill",
                    display_name="Fireball",
                    evidence_anchor_id=scene.evidence_anchor_ids[0],
                    confidence=0.9,
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
    extractor = FakeExtractor()
    engine = EntityExtractionEngine(extractor=extractor)

    results = engine.extract_imported_source(imported)

    assert len(results) == 1
    assert results[0].entities[0].entity_id == "character_mark"
    assert results[0].entities[0].evidence_anchor_id == imported.anchors[0].anchor_id
    assert results[0].relationships[0].relationship_type == "owns"
    assert extractor.scenes[0].sentence_understanding
    assert extractor.scenes[0].sentence_understanding[0].evidence_anchor_id == (
        imported.anchors[0].anchor_id
    )
    assert "item_reference" in extractor.scenes[0].sentence_understanding[0].signals


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
    assert result.rejected_candidate_count == 4


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


def test_extraction_rejects_obvious_physical_object_as_skill() -> None:
    """Concrete objects must not be accepted as skill entities."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=MisclassifiedSkillExtractor())

    with pytest.raises(ValueError, match="physical object cannot be skill"):
        engine.extract_imported_source(imported)


def test_extraction_rejects_physical_containers_as_skills() -> None:
    """Physical crystals and slips must not be accepted as usable skills."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=MisclassifiedPhysicalContainerSkillExtractor())

    with pytest.raises(ValueError, match="physical object cannot be skill"):
        engine.extract_imported_source(imported)


def test_extraction_accepts_explicit_skill_terms() -> None:
    """Named techniques remain valid skill entities."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=ValidSkillExtractor())

    result = engine.extract_imported_source(imported)[0]

    assert result.entities[0].entity_id == "skill_eye_of_insight"


def test_extraction_rejects_obvious_profession_as_skill() -> None:
    """Ranks and professions must not be accepted as skill entities."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=MisclassifiedProfessionSkillExtractor())

    with pytest.raises(ValueError, match="rank or profession cannot be skill"):
        engine.extract_imported_source(imported)


def test_extraction_rejects_story_management_concepts_as_skills() -> None:
    """Quests, rewards, and similar concepts must not become skill entities."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=MisclassifiedQuestRewardSkillExtractor())

    with pytest.raises(ValueError, match="non-capability story concept cannot be skill"):
        engine.extract_imported_source(imported)


def test_extraction_rejects_organization_as_physical_item() -> None:
    """Institutions must not be accepted as physical item entities."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=MisclassifiedOrganizationItemExtractor())

    with pytest.raises(ValueError, match="place or organization cannot be physical item"):
        engine.extract_imported_source(imported)


def test_extraction_rejects_location_as_skill() -> None:
    """Places must not be accepted as usable skill entities."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=MisclassifiedLocationSkillExtractor())

    with pytest.raises(ValueError, match="place or organization cannot be skill"):
        engine.extract_imported_source(imported)


def test_extraction_rejects_obvious_physical_object_as_system() -> None:
    """Concrete objects must not be accepted as system entities."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=MisclassifiedSystemExtractor())

    with pytest.raises(ValueError, match="physical object cannot be system"):
        engine.extract_imported_source(imported)


def test_extraction_rejects_obvious_system_as_item() -> None:
    """Named governing systems must not be accepted as physical items."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=MisclassifiedSystemItemExtractor())

    with pytest.raises(ValueError, match="governing system cannot be physical item"):
        engine.extract_imported_source(imported)


def test_extraction_accepts_explicit_system_terms() -> None:
    """Named interfaces remain valid system entities."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=ValidSystemExtractor())

    result = engine.extract_imported_source(imported)[0]

    assert result.entities[0].entity_id == "system_super_starfleet"


def test_extraction_accepts_system_created_physical_items() -> None:
    """A system-created object should remain an item when it is physically concrete."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=ValidSystemCreatedItemExtractor())

    result = engine.extract_imported_source(imported)[0]

    assert result.entities[0].entity_type == "item"
    assert result.entities[0].display_name == (
        "T3 Blizzard-class Light Interstellar Battlecruiser technical blueprint"
    )


def test_extraction_rejects_anonymous_group_phrase_as_character() -> None:
    """Anonymous plural groups must not become character cards."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=AnonymousGroupCharacterExtractor())

    with pytest.raises(ValueError, match="anonymous group phrase cannot be character"):
        engine.extract_imported_source(imported)


def test_extraction_rejects_plural_race_gender_group_as_character() -> None:
    """Plural race/gender groups must not become a single character card."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=RaceGenderGroupCharacterExtractor())

    with pytest.raises(ValueError, match="anonymous group phrase cannot be character"):
        engine.extract_imported_source(imported)


def test_extraction_accepts_singular_unnamed_character_reference() -> None:
    """Singular unnamed people can remain character candidates when evidence supports them."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=SingularUnnamedCharacterExtractor())

    result = engine.extract_imported_source(imported)[0]

    assert result.entities[0].entity_id == "character_unnamed_female_crew_member"


def test_extraction_rejects_entity_type_prefix_mismatch() -> None:
    """Entity IDs and entity types must not contradict each other."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=MismatchedEntityPrefixExtractor())

    with pytest.raises(ValueError, match="entity ID prefix"):
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


def test_extraction_dedupes_exact_duplicate_fact_candidates() -> None:
    """Repeated identical facts should not fail a provider-backed run."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=DuplicateCandidateExtractor("fact"))

    result = engine.extract_imported_source(imported)[0]

    assert tuple(fact.fact_id for fact in result.facts) == ("fact_mark_weapon",)


def test_extraction_rewrites_same_scene_fact_id_collisions() -> None:
    """Generic AI fact IDs are made unique inside one scene before Canon sees them."""
    imported = StoryImporter().import_text(
        source_id="source_demo",
        title="Demo",
        text=imported_source_text(),
    )
    engine = EntityExtractionEngine(extractor=ReusedInSceneFactIdExtractor())

    result = engine.extract_imported_source(imported)[0]

    fact_ids = tuple(fact.fact_id for fact in result.facts)
    assert len(fact_ids) == 2
    assert len(set(fact_ids)) == 2
    assert "fact_1" not in fact_ids
    assert all(fact_id.startswith("fact_character_mark_") for fact_id in fact_ids)


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


def test_extraction_result_rejects_invalid_rejected_candidate_count() -> None:
    """Extraction result metadata counts must be honest non-negative integers."""
    with pytest.raises(ValueError, match="rejected candidate count"):
        ExtractionResult(
            scene_id="source_demo_chapter_001_scene_001",
            rejected_candidate_count=-1,
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


def test_scene_extraction_input_rejects_duplicate_sentence_understanding() -> None:
    """Sentence-understanding metadata must not duplicate evidence anchors."""
    understanding = SceneSentenceUnderstanding(
        evidence_anchor_id="anchor_001",
        signals=("item_reference",),
    )

    with pytest.raises(ValueError, match="sentence-understanding anchors"):
        SceneExtractionInput(
            scene_id="source_chapter_001_scene_001",
            text="Mark draws the sword.",
            evidence_anchor_ids=("anchor_001",),
            sentence_understanding=(understanding, understanding),
        )


def test_scene_extraction_input_rejects_sentence_understanding_anchor_mismatch() -> None:
    """Sentence-understanding metadata must stay inside allowed scene anchors."""
    with pytest.raises(ValueError, match="must reference evidence anchor IDs"):
        SceneExtractionInput(
            scene_id="source_chapter_001_scene_001",
            text="Mark draws the sword.",
            evidence_anchor_ids=("anchor_001",),
            sentence_understanding=(
                SceneSentenceUnderstanding(
                    evidence_anchor_id="anchor_002",
                    signals=("item_reference",),
                ),
            ),
        )

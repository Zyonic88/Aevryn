"""Tests for Project Manager proof workflows."""

import json
from pathlib import Path
from typing import Any, cast

import pytest

from aevryn import (
    EvidenceBoundedAIExtractor,
    ExportEngine,
    ExtractedEntity,
    ExtractedFact,
    ExtractionResult,
    GlossaryTerm,
    SceneExtractionInput,
)
from aevryn.core import Story
from aevryn.importing import ImportedSource
from aevryn.projects import (
    AevrynProjectRunner,
    ContinuityRecord,
    ContinuityReport,
    ContinuitySceneReport,
    ProjectRunResult,
)


def source_file() -> Path:
    """Create a small source file for project runner tests."""
    path = Path("build") / "test_project_runner" / "chapter.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Chapter 1",
                "Mark carried a rusty dagger.",
                "",
                "Chapter 2",
                "Mark bought an iron sword.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def single_chapter_source_file() -> Path:
    """Create a one-chapter source file for AI proof tests."""
    path = Path("build") / "test_project_runner" / "single_chapter.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Chapter 1",
                "Mark bought an iron sword.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def two_scene_source_file() -> Path:
    """Create a one-chapter source file with two explicit scenes."""
    path = Path("build") / "test_project_runner" / "two_scene_chapter.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Chapter 1",
                "Mark was calm in the quiet hangar.",
                "",
                "---",
                "",
                "Mark became alarmed as the hangar alarm started.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_runner_imports_text_file() -> None:
    """Project runner imports source files through Story Import."""
    runner = AevrynProjectRunner()

    imported_source = runner.import_text_file(
        path=source_file(),
        source_id="demo",
        title="Demo",
    )

    assert imported_source.title == "Demo"
    assert len(imported_source.story.chapters) == 2


def test_runner_builds_character_card_from_demo_pipeline() -> None:
    """Project runner builds character cards from accepted Canon."""
    runner = AevrynProjectRunner()
    result = runner.run_demo_text_file(path=source_file(), source_id="demo")

    card = runner.build_character_card(result=result, character_id="character_mark")

    assert card.display_name == "Mark"
    assert card.facts[0].evidence.quote == "Mark bought an iron sword."


def test_runner_builds_scene_position_character_card() -> None:
    """Project runner can build character cards at exact scene positions."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(
        path=two_scene_source_file(),
        source_id="demo",
    )
    first_anchor_id = imported_source.anchors[0].anchor_id
    second_anchor_id = imported_source.anchors[-1].anchor_id
    result = runner.run_imported_source_with_scene_payloads(
        imported_source=imported_source,
        payloads_by_scene_id={
            "demo_chapter_001_scene_001": mood_payload(
                anchor_id=first_anchor_id,
                mood="Calm",
            ),
            "demo_chapter_001_scene_002": mood_payload(
                anchor_id=second_anchor_id,
                mood="Alarmed",
            ),
        },
    )

    first_card = runner.build_character_card_at_scene(
        result=result,
        character_id="character_mark",
        scene_id="demo_chapter_001_scene_001",
    )
    second_card = runner.build_character_card_at_scene(
        result=result,
        character_id="character_mark",
        scene_id="demo_chapter_001_scene_002",
    )

    assert tuple(
        fact.value for fact in first_card.facts if fact.attribute == "current_mood"
    ) == ("Calm",)
    assert tuple(
        fact.value for fact in second_card.facts if fact.attribute == "current_mood"
    ) == ("Alarmed",)


def test_runner_builds_prompt_bundle_from_demo_pipeline() -> None:
    """Project runner builds prompt bundles from scene context."""
    runner = AevrynProjectRunner()
    result = runner.run_demo_text_file(path=source_file(), source_id="demo")

    bundle = runner.build_prompt_bundle(result=result)

    assert "Scene ID: demo_chapter_002_scene_001" in bundle.image_prompt
    assert "item_iron_sword" in bundle.animation_prompt


class EmptyExtractor:
    """Extractor test double with no candidates."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return no candidates for the scene."""
        return ExtractionResult(scene_id=scene.scene_id)


class RecordingTextExtractor:
    """Extractor test double that records the scene input it receives."""

    def __init__(self) -> None:
        self.scene_texts: list[str] = []
        self.anchor_ids: list[tuple[str, ...]] = []

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Record text and anchors without producing candidates."""
        self.scene_texts.append(scene.text)
        self.anchor_ids.append(scene.evidence_anchor_ids)
        return ExtractionResult(scene_id=scene.scene_id)


class WrongSceneExtractor:
    """Extractor test double that returns mismatched scene IDs."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return candidates for the wrong scene."""
        return ExtractionResult(scene_id="wrong_scene")


def test_runner_accepts_pluggable_extractor() -> None:
    """Project runner can run any evidence-bounded extractor."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")

    result = runner.run_imported_source(
        imported_source=imported_source,
        extractor=EmptyExtractor(),
    )

    assert result.extraction_results[0].entities == ()
    assert result.update_summaries[0].accepted_entities == ()


def test_runner_feeds_translation_normalized_text_to_extraction() -> None:
    """Extraction may consume normalized text while preserving original anchors."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(
        path=single_chapter_source_file(),
        source_id="demo",
    )
    extractor = RecordingTextExtractor()

    result = runner.run_imported_source(
        imported_source=imported_source,
        extractor=extractor,
        translation_glossary=(
            GlossaryTerm(
                source_term="iron sword",
                preferred_term="Iron Blade",
                evidence_anchor_id=imported_source.anchors[-1].anchor_id,
            ),
        ),
    )

    assert extractor.scene_texts == ["Mark bought an Iron Blade."]
    assert extractor.anchor_ids == [(imported_source.anchors[-1].anchor_id,)]
    assert result.translation_units[0].normalized_text == "Mark bought an Iron Blade."
    assert result.translation_units[0].source_scene_id == "demo_chapter_001_scene_001"
    assert result.extraction_results[0].scene_id == "demo_chapter_001_scene_001"


def test_runner_builds_phase12_translation_and_identity_metadata() -> None:
    """Phase 12 metadata should exist without changing Canon acceptance."""
    runner = AevrynProjectRunner()
    result = runner.run_demo_text_file(path=source_file(), source_id="demo")

    assert len(result.translation_units) == len(result.extraction_results)
    assert result.translation_units[0].source_evidence_anchor_ids
    assert result.identity_resolutions
    assert all(
        decision.reference.evidence_anchor_id
        for decision in result.identity_resolutions
    )
    assert {
        entity_id
        for summary in result.update_summaries
        for entity_id in summary.accepted_entities
    } == {"character_mark", "item_iron_sword", "item_rusty_dagger"}


def test_runner_resolves_later_descriptive_entity_to_prior_identity() -> None:
    """High-confidence cross-scene identity matches should avoid duplicate entities."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(
        path=two_scene_source_file(),
        source_id="demo",
    )
    first_anchor_id = imported_source.anchors[0].anchor_id
    second_anchor_id = imported_source.anchors[-1].anchor_id

    result = runner.run_imported_source_with_scene_payloads(
        imported_source=imported_source,
        payloads_by_scene_id={
            "demo_chapter_001_scene_001": {
                "entities": [
                    {
                        "entity_id": "character_charlotte",
                        "entity_type": "character",
                        "display_name": "Charlotte",
                        "evidence_anchor_id": first_anchor_id,
                        "confidence": 0.95,
                    }
                ],
                "facts": [
                    {
                        "fact_id": "fact_character_charlotte_gender_female",
                        "entity_id": "character_charlotte",
                        "attribute": "gender",
                        "value": "Female",
                        "evidence_anchor_id": first_anchor_id,
                        "confidence": 0.95,
                    },
                    {
                        "fact_id": "fact_character_charlotte_title_general",
                        "entity_id": "character_charlotte",
                        "attribute": "title",
                        "value": "General",
                        "evidence_anchor_id": first_anchor_id,
                        "confidence": 0.95,
                    },
                ],
                "relationships": [],
                "state_changes": [],
            },
            "demo_chapter_001_scene_002": {
                "entities": [
                    {
                        "entity_id": "character_female_general",
                        "entity_type": "character",
                        "display_name": "Female General",
                        "evidence_anchor_id": second_anchor_id,
                        "confidence": 0.9,
                    }
                ],
                "facts": [
                    {
                        "fact_id": "fact_character_female_general_status_alert",
                        "entity_id": "character_female_general",
                        "attribute": "status",
                        "value": "Alert",
                        "evidence_anchor_id": second_anchor_id,
                        "confidence": 0.9,
                    }
                ],
                "relationships": [],
                "state_changes": [],
            },
        },
    )

    assert result.update_summaries[0].accepted_entities == ("character_charlotte",)
    assert result.update_summaries[1].accepted_entities == ()
    assert result.extraction_results[1].entities == ()
    assert result.extraction_results[1].facts[0].entity_id == "character_charlotte"
    assert result.database.retrieve_entity("character_female_general") is None
    status_fact = result.database.retrieve_current_fact("character_charlotte", "status")
    assert status_fact is not None
    assert status_fact.value == "Alert"
    assert any(
        decision.status == "resolved"
        and decision.entity_id == "character_charlotte"
        and decision.reference.text == "Female General"
        for decision in result.identity_resolutions
    )


def test_runner_resolves_same_scene_description_to_named_identity() -> None:
    """Same-scene descriptive aliases should merge when one named profile supports them."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(
        path=single_chapter_source_file(),
        source_id="demo",
    )
    anchor_id = imported_source.anchors[-1].anchor_id

    result = runner.run_imported_source_with_scene_payloads(
        imported_source=imported_source,
        payloads_by_scene_id={
            "demo_chapter_001_scene_001": {
                "entities": [
                    {
                        "entity_id": "character_charlotte",
                        "entity_type": "character",
                        "display_name": "Charlotte",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.95,
                    },
                    {
                        "entity_id": "character_white_haired_beauty",
                        "entity_type": "character",
                        "display_name": "White-haired Beauty",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.9,
                    },
                ],
                "facts": [
                    {
                        "fact_id": "fact_character_charlotte_description_beauty",
                        "entity_id": "character_charlotte",
                        "attribute": "description",
                        "value": "White-haired Beauty",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.95,
                    },
                    {
                        "fact_id": "fact_character_white_haired_beauty_status_smiling",
                        "entity_id": "character_white_haired_beauty",
                        "attribute": "status",
                        "value": "Smiling",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.9,
                    },
                ],
                "relationships": [],
                "state_changes": [],
            },
        },
    )

    assert result.update_summaries[0].accepted_entities == ("character_charlotte",)
    assert result.extraction_results[0].entities[0].entity_id == "character_charlotte"
    assert len(result.extraction_results[0].entities) == 1
    status_fact = result.database.retrieve_current_fact("character_charlotte", "status")
    assert status_fact is not None
    assert status_fact.value == "Smiling"
    assert result.database.retrieve_entity("character_white_haired_beauty") is None
    assert any(
        decision.status == "resolved"
        and decision.entity_id == "character_charlotte"
        and decision.reference.text == "White-haired Beauty"
        for decision in result.identity_resolutions
    )


def test_runner_keeps_same_scene_ambiguous_description_unmerged() -> None:
    """Same-scene descriptions should not merge when multiple characters fit."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(
        path=single_chapter_source_file(),
        source_id="demo",
    )
    anchor_id = imported_source.anchors[-1].anchor_id

    result = runner.run_imported_source_with_scene_payloads(
        imported_source=imported_source,
        payloads_by_scene_id={
            "demo_chapter_001_scene_001": {
                "entities": [
                    {
                        "entity_id": "character_charlotte",
                        "entity_type": "character",
                        "display_name": "Charlotte",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.95,
                    },
                    {
                        "entity_id": "character_elaine",
                        "entity_type": "character",
                        "display_name": "Elaine",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.95,
                    },
                    {
                        "entity_id": "character_female_general",
                        "entity_type": "character",
                        "display_name": "Female General",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.9,
                    },
                ],
                "facts": [
                    {
                        "fact_id": "fact_character_charlotte_gender_female",
                        "entity_id": "character_charlotte",
                        "attribute": "gender",
                        "value": "Female",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.95,
                    },
                    {
                        "fact_id": "fact_character_charlotte_title_general",
                        "entity_id": "character_charlotte",
                        "attribute": "title",
                        "value": "General",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.95,
                    },
                    {
                        "fact_id": "fact_character_elaine_gender_female",
                        "entity_id": "character_elaine",
                        "attribute": "gender",
                        "value": "Female",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.95,
                    },
                    {
                        "fact_id": "fact_character_elaine_title_general",
                        "entity_id": "character_elaine",
                        "attribute": "title",
                        "value": "General",
                        "evidence_anchor_id": anchor_id,
                        "confidence": 0.95,
                    },
                ],
                "relationships": [],
                "state_changes": [],
            },
        },
    )

    assert "character_female_general" in result.update_summaries[0].accepted_entities
    assert result.database.retrieve_entity("character_female_general") is not None
    assert any(
        decision.status == "ambiguous"
        and decision.reference.text == "Female General"
        and {candidate.entity_id for candidate in decision.candidates}
        == {"character_charlotte", "character_elaine"}
        for decision in result.identity_resolutions
    )


def test_runner_rejects_empty_imported_source() -> None:
    """Project runner reports empty imported sources clearly."""
    runner = AevrynProjectRunner()
    imported_source = ImportedSource(
        source_id="empty",
        title="Empty",
        story=Story(story_id="empty", title="Empty"),
        paragraphs=(),
        anchors=(),
    )

    with pytest.raises(ValueError, match="no chapters"):
        runner.run_imported_source(
            imported_source=imported_source,
            extractor=EmptyExtractor(),
        )


def test_runner_can_extract_one_imported_scene() -> None:
    """Project runner can apply an extractor to one selected scene."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")

    result = runner.run_imported_scene(
        imported_source=imported_source,
        extractor=EmptyExtractor(),
        scene_id="demo_chapter_002_scene_001",
    )

    assert result.extraction_results[0].scene_id == "demo_chapter_002_scene_001"


def test_runner_rejects_wrong_scene_extractor_result() -> None:
    """Single-scene workflows require extractor output for the requested scene."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")

    with pytest.raises(ValueError, match="wrong scene"):
        runner.run_imported_scene(
            imported_source=imported_source,
            extractor=WrongSceneExtractor(),
            scene_id="demo_chapter_002_scene_001",
        )


class JsonClient:
    """AI client test double that returns fixed JSON."""

    def __init__(self, response: str) -> None:
        """Create the test client."""
        self.response = response

    def complete(self, prompt: str) -> str:
        """Return configured JSON for the prompt."""
        return self.response


class ChapterWeaponExtractor:
    """Extractor test double that changes Mark's weapon across chapters."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return weapon candidates based on the scene text."""
        anchor_id = scene.evidence_anchor_ids[0]
        if "iron sword" in scene.text.lower():
            weapon_value = "Iron Sword"
            fact_id = "fact_character_mark_current_weapon_iron_sword"
            extra_facts: tuple[ExtractedFact, ...] = ()
        else:
            weapon_value = "Rusty Dagger"
            fact_id = "fact_character_mark_current_weapon_rusty_dagger"
            extra_facts = (
                ExtractedFact(
                    fact_id="fact_character_mark_role_adventurer",
                    entity_id="character_mark",
                    attribute="role",
                    value="Adventurer",
                    evidence_anchor_id=anchor_id,
                    confidence=0.95,
                ),
            )

        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="character_mark",
                    entity_type="character",
                    display_name="Mark",
                    evidence_anchor_id=anchor_id,
                    confidence=0.95,
                ),
            ),
            facts=(
                ExtractedFact(
                    fact_id=fact_id,
                    entity_id="character_mark",
                    attribute="current_weapon",
                    value=weapon_value,
                    evidence_anchor_id=anchor_id,
                    confidence=0.95,
                ),
                *extra_facts,
            ),
        )


def test_runner_updates_character_card_and_prompt_from_ai_candidates() -> None:
    """A chapter can flow from AI candidates into Canon-backed outputs."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(
        path=single_chapter_source_file(),
        source_id="demo",
    )
    anchor_id = imported_source.anchors[-1].anchor_id
    extractor = EvidenceBoundedAIExtractor(
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
                        },
                        {
                            "entity_id": "item_iron_sword",
                            "entity_type": "item",
                            "display_name": "Iron Sword",
                            "evidence_anchor_id": anchor_id,
                            "confidence": 0.9,
                        },
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
                            "confidence": 0.9,
                        }
                    ],
                }
            )
        )
    )

    result = runner.run_imported_source(
        imported_source=imported_source,
        extractor=extractor,
    )
    card = runner.build_character_card(result=result, character_id="character_mark")
    bundle = runner.build_prompt_bundle(result=result)
    world_state = runner.build_world_state(
        result=result,
        entity_ids=("item_iron_sword",),
    )

    assert any(fact.attribute == "current_weapon" for fact in card.facts)
    assert "character_mark retains current_weapon: Iron Sword" in bundle.image_prompt
    assert "Important Objects:" in bundle.image_prompt
    assert world_state.entities[0].display_name == "Iron Sword"


def test_runner_builds_scene_position_world_state() -> None:
    """Project runner can build world state at exact scene positions."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(
        path=two_scene_source_file(),
        source_id="demo",
    )
    first_anchor_id = imported_source.anchors[0].anchor_id
    second_anchor_id = imported_source.anchors[-1].anchor_id
    result = runner.run_imported_source_with_scene_payloads(
        imported_source=imported_source,
        payloads_by_scene_id={
            "demo_chapter_001_scene_001": hangar_payload(
                anchor_id=first_anchor_id,
                condition="Quiet",
            ),
            "demo_chapter_001_scene_002": hangar_payload(
                anchor_id=second_anchor_id,
                condition="Alarm active",
            ),
        },
    )

    first_world = runner.build_world_state_at_scene(
        result=result,
        entity_ids=("location_hangar",),
        scene_id="demo_chapter_001_scene_001",
    )
    second_world = runner.build_world_state_at_scene(
        result=result,
        entity_ids=("location_hangar",),
        scene_id="demo_chapter_001_scene_002",
    )

    assert tuple(
        fact.value for fact in first_world.entities[0].facts if fact.attribute == "condition"
    ) == ("Quiet",)
    assert tuple(
        fact.value
        for fact in second_world.entities[0].facts
        if fact.attribute == "condition"
    ) == (
        "Alarm active",
    )


def test_runner_dedupes_selected_ids_for_views() -> None:
    """Project runner dedupes selected IDs before building downstream views."""
    runner = AevrynProjectRunner()
    result = runner.run_demo_text_file(path=source_file(), source_id="demo")

    context = runner.build_scene_context(
        result=result,
        character_ids=("character_mark", "character_mark"),
    )
    world_state = runner.build_world_state(
        result=result,
        entity_ids=("item_iron_sword", "item_iron_sword"),
    )

    assert len(context.character_cards) == 1
    assert len(world_state.entities) == 1


def test_runner_scene_position_views_reject_unknown_scene() -> None:
    """Scene-position project views require imported scene IDs."""
    runner = AevrynProjectRunner()
    result = runner.run_demo_text_file(path=source_file(), source_id="demo")

    with pytest.raises(ValueError, match="Unknown scene"):
        runner.build_character_card_at_scene(
            result=result,
            character_id="character_mark",
            scene_id="demo_chapter_999_scene_001",
        )

    with pytest.raises(ValueError, match="Unknown scene"):
        runner.build_world_state_at_scene(
            result=result,
            entity_ids=("item_iron_sword",),
            scene_id="demo_chapter_999_scene_001",
        )


def test_runner_builds_continuity_report_across_chapters() -> None:
    """Project runner reports new, updated, still-known, and invalidated canon."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")
    result = runner.run_imported_source(
        imported_source=imported_source,
        extractor=ChapterWeaponExtractor(),
    )

    report = runner.build_continuity_report(result)
    first_scene = report.scenes[0]
    second_scene = report.scenes[1]

    assert report.source_id == "demo"
    assert any(
        record.description == "character_mark current_weapon = Rusty Dagger"
        for record in first_scene.new
    )
    assert any(
        record.description == "character_mark current_weapon = Iron Sword"
        for record in second_scene.updated
    )
    updated_weapon = next(
        record
        for record in second_scene.updated
        if record.description == "character_mark current_weapon = Iron Sword"
    )
    assert updated_weapon.chapter_id == "demo_chapter_002"
    assert updated_weapon.scene_id == "demo_chapter_002_scene_001"
    assert updated_weapon.evidence_quote == "Mark bought an iron sword."
    assert any(
        record.description == "character_mark current_weapon = Rusty Dagger"
        for record in second_scene.invalidated
    )
    assert any(
        record.description == "character_mark role = Adventurer"
        for record in second_scene.still_known
    )


def test_runner_can_apply_multi_scene_ai_payloads() -> None:
    """Project runner can apply precomputed AI payloads across all scenes."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")
    first_anchor_id = imported_source.anchors[0].anchor_id
    second_anchor_id = imported_source.anchors[1].anchor_id

    result = runner.run_imported_source_with_scene_payloads(
        imported_source=imported_source,
        payloads_by_scene_id={
            "demo_chapter_001_scene_001": weapon_payload(
                anchor_id=first_anchor_id,
                weapon="Rusty Dagger",
            ),
            "demo_chapter_002_scene_001": weapon_payload(
                anchor_id=second_anchor_id,
                weapon="Iron Sword",
            ),
        },
    )
    report = runner.build_continuity_report(result)

    assert len(result.extraction_results) == 2
    assert any(
        record.description == "character_mark current_weapon = Iron Sword"
        for record in report.scenes[1].updated
    )


def test_continuity_report_keeps_additive_facts_as_new() -> None:
    """Additive fact attributes accumulate instead of invalidating prior values."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")
    first_anchor_id = imported_source.anchors[0].anchor_id
    second_anchor_id = imported_source.anchors[1].anchor_id

    result = runner.run_imported_source_with_scene_payloads(
        imported_source=imported_source,
        payloads_by_scene_id={
            "demo_chapter_001_scene_001": ability_payload(
                anchor_id=first_anchor_id,
                ability="Fleet Luck Bonus",
            ),
            "demo_chapter_002_scene_001": ability_payload(
                anchor_id=second_anchor_id,
                ability="Eye of Insight",
            ),
        },
    )

    report = runner.build_continuity_report(result)

    assert any(
        record.description == "character_mark ability = Fleet Luck Bonus"
        for record in report.scenes[0].new
    )
    assert any(
        record.description == "character_mark ability = Eye of Insight"
        for record in report.scenes[1].new
    )
    assert not any(
        record.description == "character_mark ability = Eye of Insight"
        for record in report.scenes[1].updated
    )
    assert not any(
        record.description == "character_mark ability = Fleet Luck Bonus"
        for record in report.scenes[1].invalidated
    )


def test_runner_rejects_multi_scene_ai_payloads_missing_scene() -> None:
    """Project runner requires one payload for every imported scene."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")
    first_anchor_id = imported_source.anchors[0].anchor_id

    with pytest.raises(ValueError, match="missing scenes"):
        runner.run_imported_source_with_scene_payloads(
            imported_source=imported_source,
            payloads_by_scene_id={
                "demo_chapter_001_scene_001": weapon_payload(
                    anchor_id=first_anchor_id,
                    weapon="Rusty Dagger",
                ),
            },
        )


def test_runner_rejects_multi_scene_ai_payloads_unknown_scene() -> None:
    """Project runner rejects payloads that do not belong to imported scenes."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")
    first_anchor_id = imported_source.anchors[0].anchor_id
    second_anchor_id = imported_source.anchors[1].anchor_id

    with pytest.raises(ValueError, match="unknown scenes"):
        runner.run_imported_source_with_scene_payloads(
            imported_source=imported_source,
            payloads_by_scene_id={
                "demo_chapter_001_scene_001": weapon_payload(
                    anchor_id=first_anchor_id,
                    weapon="Rusty Dagger",
                ),
                "demo_chapter_002_scene_001": weapon_payload(
                    anchor_id=second_anchor_id,
                    weapon="Iron Sword",
                ),
                "demo_chapter_999_scene_001": weapon_payload(
                    anchor_id=second_anchor_id,
                    weapon="Future Sword",
                ),
            },
        )


def test_runner_rejects_blank_multi_scene_ai_payload_scene_id() -> None:
    """Project runner rejects blank multi-scene payload IDs at the API boundary."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")
    first_anchor_id = imported_source.anchors[0].anchor_id

    with pytest.raises(ValueError, match="scene ID is required"):
        runner.run_imported_source_with_scene_payloads(
            imported_source=imported_source,
            payloads_by_scene_id={
                "": weapon_payload(
                    anchor_id=first_anchor_id,
                    weapon="Rusty Dagger",
                )
            },
        )


def test_runner_rejects_non_string_multi_scene_ai_payload_scene_id() -> None:
    """Project runner rejects non-string multi-scene payload IDs cleanly."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")
    first_anchor_id = imported_source.anchors[0].anchor_id
    payloads = cast(
        dict[str, dict[str, Any]],
        {
            1: weapon_payload(
                anchor_id=first_anchor_id,
                weapon="Rusty Dagger",
            )
        },
    )

    with pytest.raises(ValueError, match="scene IDs must be strings"):
        runner.run_imported_source_with_scene_payloads(
            imported_source=imported_source,
            payloads_by_scene_id=payloads,
        )


def test_runner_rejects_whitespace_multi_scene_ai_payload_scene_id() -> None:
    """Project runner rejects non-machine-safe multi-scene payload IDs."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")
    first_anchor_id = imported_source.anchors[0].anchor_id

    with pytest.raises(ValueError, match="scene ID cannot contain whitespace"):
        runner.run_imported_source_with_scene_payloads(
            imported_source=imported_source,
            payloads_by_scene_id={
                "demo chapter 001 scene 001": weapon_payload(
                    anchor_id=first_anchor_id,
                    weapon="Rusty Dagger",
                )
            },
        )


def test_runner_rejects_malformed_multi_scene_ai_payload() -> None:
    """Project runner uses the strict evidence-bounded AI payload schema."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")
    second_anchor_id = imported_source.anchors[1].anchor_id

    with pytest.raises(ValueError, match="missing required keys"):
        runner.run_imported_source_with_scene_payloads(
            imported_source=imported_source,
            payloads_by_scene_id={
                "demo_chapter_001_scene_001": {
                    "entities": [],
                    "facts": [],
                    "relationships": [],
                },
                "demo_chapter_002_scene_001": weapon_payload(
                    anchor_id=second_anchor_id,
                    weapon="Iron Sword",
                ),
            },
        )


def test_continuity_report_exports_as_json_and_markdown() -> None:
    """Continuity reports can be exported for the Canon Test proof."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")
    result = runner.run_imported_source(
        imported_source=imported_source,
        extractor=ChapterWeaponExtractor(),
    )
    report = runner.build_continuity_report(result)
    exporter = ExportEngine()

    exported_json = json.loads(exporter.continuity_report_json(report))
    exported_markdown = exporter.continuity_report_markdown(report)

    assert exported_json["source_id"] == "demo"
    assert exported_json["scenes"][1]["updated"][0]["evidence_id"]
    assert exported_json["scenes"][1]["updated"][0]["chapter_id"]
    assert exported_json["scenes"][1]["updated"][0]["evidence_quote"]
    assert any(
        record["record_type"] == "state_change"
        for record in exported_json["scenes"][0]["new"]
    )
    assert "# Continuity Report: demo" in exported_markdown
    assert "### Updated" in exported_markdown
    assert "character_mark current_weapon = Iron Sword" in exported_markdown
    assert "Mark bought an iron sword." in exported_markdown
    assert "### Summary" in exported_markdown
    assert "- Still known:" in exported_markdown
    assert "state changes recorded; use JSON export" in exported_markdown
    assert "State valid from event" not in exported_markdown


def test_continuity_report_markdown_limits_retained_canon_noise() -> None:
    """Continuity Markdown summarizes retained records while JSON keeps them."""
    runner = AevrynProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")
    result = runner.run_imported_source(
        imported_source=imported_source,
        extractor=ChapterWeaponExtractor(),
    )
    report = runner.build_continuity_report(result)
    exporter = ExportEngine()

    exported_json = json.loads(exporter.continuity_report_json(report))
    exported_markdown = exporter.continuity_report_markdown(report)

    assert exported_json["scenes"][1]["still_known"]
    assert "retained canon records remain active" in exported_markdown
    assert "use JSON export for the full audit trail" not in exported_markdown


def test_continuity_report_markdown_omits_excess_retained_records() -> None:
    """Continuity Markdown keeps retained canon examples bounded."""
    retained_records = tuple(
        ContinuityRecord(
            record_id=f"record_{index:03}",
            record_type="fact",
            description=f"character_mark retained_attribute_{index} = Value",
            evidence_id=f"evidence_{index:03}",
            chapter_id="chapter_001",
            scene_id="chapter_001_scene_001",
            evidence_quote=f"Retained evidence {index}.",
        )
        for index in range(13)
    )
    report = ContinuityReport(
        source_id="demo",
        scenes=(
            ContinuitySceneReport(
                scene_id="demo_chapter_002_scene_001",
                still_known=retained_records,
            ),
        ),
    )

    exported_markdown = ExportEngine().continuity_report_markdown(report)

    assert "- 13 retained canon records remain active." in exported_markdown
    assert "retained_attribute_11" in exported_markdown
    assert "retained_attribute_12" not in exported_markdown
    assert "1 additional retained records omitted from Markdown" in exported_markdown
    assert "Retained evidence" not in exported_markdown


def test_project_run_result_rejects_misaligned_summaries() -> None:
    """Project run results keep extraction results aligned with update summaries."""
    runner = AevrynProjectRunner()
    result = runner.run_demo_text_file(path=source_file(), source_id="demo")

    with pytest.raises(ValueError, match="must align"):
        ProjectRunResult(
            imported_source=result.imported_source,
            database=result.database,
            extraction_results=result.extraction_results,
            update_summaries=(),
        )


def test_continuity_record_rejects_invalid_identity() -> None:
    """Continuity records require machine-safe IDs and visible descriptions."""
    with pytest.raises(ValueError, match="record ID cannot contain whitespace"):
        ContinuityRecord(
            record_id="record one",
            record_type="fact",
            description="Fact accepted.",
        )

    with pytest.raises(ValueError, match="description is required"):
        ContinuityRecord(
            record_id="record_one",
            record_type="fact",
            description=" ",
        )

    with pytest.raises(ValueError, match="evidence quote cannot be blank"):
        ContinuityRecord(
            record_id="record_one",
            record_type="fact",
            description="Fact accepted.",
            evidence_quote=cast(Any, 42),
        )


def test_continuity_scene_report_rejects_duplicate_bucket_records() -> None:
    """One continuity bucket cannot list the same record twice."""
    record = ContinuityRecord(
        record_id="record_one",
        record_type="fact",
        description="Fact accepted.",
    )

    with pytest.raises(ValueError, match="duplicate IDs"):
        ContinuitySceneReport(
            scene_id="scene_001",
            new=(record, record),
        )


def test_continuity_report_rejects_duplicate_scenes() -> None:
    """Continuity reports keep scene entries unique."""
    scene = ContinuitySceneReport(scene_id="scene_001")

    with pytest.raises(ValueError, match="duplicate scenes"):
        ContinuityReport(source_id="demo", scenes=(scene, scene))


def weapon_payload(anchor_id: str, weapon: str) -> dict[str, object]:
    """Build a multi-scene AI payload for a weapon fact."""
    normalized_weapon = weapon.lower().replace(" ", "_")
    return {
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
                "fact_id": f"fact_character_mark_current_weapon_{normalized_weapon}",
                "entity_id": "character_mark",
                "attribute": "current_weapon",
                "value": weapon,
                "evidence_anchor_id": anchor_id,
                "confidence": 0.95,
            }
        ],
        "relationships": [],
        "state_changes": [],
    }


def ability_payload(anchor_id: str, ability: str) -> dict[str, object]:
    """Build a multi-scene AI payload for an additive ability fact."""
    normalized_ability = ability.lower().replace(" ", "_")
    return {
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
                "fact_id": f"fact_character_mark_ability_{normalized_ability}",
                "entity_id": "character_mark",
                "attribute": "ability",
                "value": ability,
                "evidence_anchor_id": anchor_id,
                "confidence": 0.95,
            }
        ],
        "relationships": [],
        "state_changes": [],
    }


def mood_payload(anchor_id: str, mood: str) -> dict[str, object]:
    """Build a multi-scene AI payload for a character mood fact."""
    normalized_mood = mood.lower().replace(" ", "_")
    return {
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
                "fact_id": f"fact_character_mark_current_mood_{normalized_mood}",
                "entity_id": "character_mark",
                "attribute": "current_mood",
                "value": mood,
                "evidence_anchor_id": anchor_id,
                "confidence": 0.95,
            }
        ],
        "relationships": [],
        "state_changes": [],
    }


def hangar_payload(anchor_id: str, condition: str) -> dict[str, object]:
    """Build a multi-scene AI payload for a world condition fact."""
    normalized_condition = condition.lower().replace(" ", "_")
    return {
        "entities": [
            {
                "entity_id": "location_hangar",
                "entity_type": "location",
                "display_name": "Hangar",
                "evidence_anchor_id": anchor_id,
                "confidence": 0.95,
            }
        ],
        "facts": [
            {
                "fact_id": f"fact_location_hangar_condition_{normalized_condition}",
                "entity_id": "location_hangar",
                "attribute": "condition",
                "value": condition,
                "evidence_anchor_id": anchor_id,
                "confidence": 0.95,
            }
        ],
        "relationships": [],
        "state_changes": [],
    }

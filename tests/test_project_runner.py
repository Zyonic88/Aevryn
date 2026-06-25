"""Tests for Project Manager proof workflows."""

import json
from pathlib import Path

import pytest

from scenesmith import (
    EvidenceBoundedAIExtractor,
    ExportEngine,
    ExtractedEntity,
    ExtractedFact,
    ExtractionResult,
    SceneExtractionInput,
)
from scenesmith.core import Story
from scenesmith.importing import ImportedSource
from scenesmith.projects import SceneSmithProjectRunner


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


def test_runner_imports_text_file() -> None:
    """Project runner imports source files through Story Import."""
    runner = SceneSmithProjectRunner()

    imported_source = runner.import_text_file(
        path=source_file(),
        source_id="demo",
        title="Demo",
    )

    assert imported_source.title == "Demo"
    assert len(imported_source.story.chapters) == 2


def test_runner_builds_character_card_from_demo_pipeline() -> None:
    """Project runner builds character cards from accepted Canon."""
    runner = SceneSmithProjectRunner()
    result = runner.run_demo_text_file(path=source_file(), source_id="demo")

    card = runner.build_character_card(result=result, character_id="character_mark")

    assert card.display_name == "Mark"
    assert card.facts[0].evidence.quote == "Mark bought an iron sword."


def test_runner_builds_prompt_bundle_from_demo_pipeline() -> None:
    """Project runner builds prompt bundles from scene context."""
    runner = SceneSmithProjectRunner()
    result = runner.run_demo_text_file(path=source_file(), source_id="demo")

    bundle = runner.build_prompt_bundle(result=result)

    assert "Scene ID: demo_chapter_002_scene_001" in bundle.image_prompt
    assert "character_mark owns item_iron_sword" in bundle.animation_prompt


class EmptyExtractor:
    """Extractor test double with no candidates."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return no candidates for the scene."""
        return ExtractionResult(scene_id=scene.scene_id)


class WrongSceneExtractor:
    """Extractor test double that returns mismatched scene IDs."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return candidates for the wrong scene."""
        return ExtractionResult(scene_id="wrong_scene")


def test_runner_accepts_pluggable_extractor() -> None:
    """Project runner can run any evidence-bounded extractor."""
    runner = SceneSmithProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")

    result = runner.run_imported_source(
        imported_source=imported_source,
        extractor=EmptyExtractor(),
    )

    assert result.extraction_results[0].entities == ()
    assert result.update_summaries[0].accepted_entities == ()


def test_runner_rejects_empty_imported_source() -> None:
    """Project runner reports empty imported sources clearly."""
    runner = SceneSmithProjectRunner()
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
    runner = SceneSmithProjectRunner()
    imported_source = runner.import_text_file(path=source_file(), source_id="demo")

    result = runner.run_imported_scene(
        imported_source=imported_source,
        extractor=EmptyExtractor(),
        scene_id="demo_chapter_002_scene_001",
    )

    assert result.extraction_results[0].scene_id == "demo_chapter_002_scene_001"


def test_runner_rejects_wrong_scene_extractor_result() -> None:
    """Single-scene workflows require extractor output for the requested scene."""
    runner = SceneSmithProjectRunner()
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
    runner = SceneSmithProjectRunner()
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


def test_runner_dedupes_selected_ids_for_views() -> None:
    """Project runner dedupes selected IDs before building downstream views."""
    runner = SceneSmithProjectRunner()
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


def test_runner_builds_continuity_report_across_chapters() -> None:
    """Project runner reports new, updated, still-known, and invalidated canon."""
    runner = SceneSmithProjectRunner()
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
    runner = SceneSmithProjectRunner()
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


def test_runner_rejects_multi_scene_ai_payloads_missing_scene() -> None:
    """Project runner requires one payload for every imported scene."""
    runner = SceneSmithProjectRunner()
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


def test_continuity_report_exports_as_json_and_markdown() -> None:
    """Continuity reports can be exported for the Canon Test proof."""
    runner = SceneSmithProjectRunner()
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
    assert "# Continuity Report: demo" in exported_markdown
    assert "### Updated" in exported_markdown
    assert "character_mark current_weapon = Iron Sword" in exported_markdown
    assert "Mark bought an iron sword." in exported_markdown


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

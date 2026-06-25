"""Tests for Presentation Engine."""

from dataclasses import replace

import pytest

from scenesmith import (
    CanonCharacterCard,
    CanonPromptBuilder,
    CanonSceneContext,
    CharacterCardBuilder,
    ExportEngine,
    PresentationEngine,
    ProductionPack,
    PromptBundle,
    SceneAnalysis,
    SceneAnalyzer,
    SceneContextBuilder,
    WorldStateBuilder,
)
from tests.test_scene_context_builder import build_database, build_imported_source
from tests.test_world_engine import build_database as build_world_database


def build_outputs() -> tuple[CanonCharacterCard, CanonSceneContext, SceneAnalysis, ProductionPack]:
    """Build presentation inputs."""
    database = build_database()
    context = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    ).build_context(
        imported_source=build_imported_source(),
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark",),
    )
    analysis = SceneAnalyzer().analyze(context)
    pack = CanonPromptBuilder().build_production_pack(context)
    return context.character_cards[0], context, analysis, pack


def test_presentation_engine_builds_character_profile() -> None:
    """Presentation Engine groups character facts into human sections."""
    card, _context, _analysis, _pack = build_outputs()

    profile = PresentationEngine().character_profile(card)

    assert profile.display_name == "Mark"
    assert profile.current_equipment.items == ("Iron Sword",)
    assert "verified facts" in profile.evidence_summary


def test_presentation_engine_dedupes_character_profile_items() -> None:
    """Repeated facts do not duplicate human profile items."""
    card, _context, _analysis, _pack = build_outputs()
    duplicate_card = replace(
        card,
        facts=card.facts + card.facts,
    )

    profile = PresentationEngine().character_profile(duplicate_card)

    assert profile.current_equipment.items == ("Iron Sword",)


def test_presentation_engine_builds_scene_sheet() -> None:
    """Presentation Engine builds a scan-friendly scene sheet."""
    _card, context, analysis, _pack = build_outputs()

    scene = PresentationEngine().scene_sheet(context=context, analysis=analysis)

    assert scene.scene_id == "source_demo_chapter_002_scene_001"
    assert scene.characters_present.items == ("Mark",)
    assert scene.purpose.items


def test_presentation_engine_rejects_mismatched_scene_analysis() -> None:
    """Scene sheets require analysis for the same scene."""
    _card, context, analysis, _pack = build_outputs()
    mismatched_analysis = replace(analysis, scene_id="other_scene")

    with pytest.raises(ValueError, match="analysis"):
        PresentationEngine().scene_sheet(context=context, analysis=mismatched_analysis)


def test_presentation_engine_builds_production_pack_view() -> None:
    """Presentation Engine builds prompt-pack views."""
    _card, context, analysis, pack = build_outputs()
    engine = PresentationEngine()
    scene = engine.scene_sheet(context=context, analysis=analysis)

    view = engine.production_pack(pack=pack, scene=scene)

    assert view.image_prompt.title == "Image Prompt"
    assert view.image_prompt.items


def test_presentation_engine_dedupes_and_limits_prompt_lines() -> None:
    """Prompt presentation keeps repeated long lines concise."""
    _card, context, analysis, pack = build_outputs()
    long_line = " ".join(f"word{index}" for index in range(40))
    prompt_bundle = PromptBundle(
        image_prompt="\n".join([long_line, long_line, "short"] * 10),
        narration_prompt=pack.prompt_bundle.narration_prompt,
        camera_prompt=pack.prompt_bundle.camera_prompt,
        animation_prompt=pack.prompt_bundle.animation_prompt,
    )
    compact_pack = replace(pack, prompt_bundle=prompt_bundle)
    engine = PresentationEngine()
    scene = engine.scene_sheet(context=context, analysis=analysis)

    view = engine.production_pack(pack=compact_pack, scene=scene)

    assert len(view.image_prompt.items) == 2
    assert view.image_prompt.items[0].endswith("...")


def test_export_engine_writes_presentation_views() -> None:
    """Export Engine serializes presentation view models."""
    card, context, analysis, pack = build_outputs()
    presentation = PresentationEngine()
    profile = presentation.character_profile(card)
    scene = presentation.scene_sheet(context=context, analysis=analysis)
    view = presentation.production_pack(pack=pack, scene=scene)
    exporter = ExportEngine()

    profile_markdown = exporter.character_profile_markdown(profile)
    scene_markdown = exporter.scene_sheet_view_markdown(scene)
    pack_markdown = exporter.production_pack_view_markdown(view)

    assert "# Mark" in profile_markdown
    assert "## Current Equipment" in profile_markdown
    assert "## Characters Present" in scene_markdown
    assert "## Image Prompt" in pack_markdown


def test_presentation_engine_builds_world_sheet() -> None:
    """Presentation Engine builds scan-friendly world sheets."""
    state = PresentationEngine().world_sheet(
        state=WorldStateBuilder(database=build_world_database()).build_state(
            entity_ids=("location_northern_fortress",),
            chapter_index=6,
        )
    )

    markdown = ExportEngine().world_sheet_view_markdown(state)

    assert "# World Sheet" in markdown
    assert "Northern Fortress (location)" in markdown
    assert "damage: Walls damaged" in markdown

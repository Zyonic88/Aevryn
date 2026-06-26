"""Tests for Presentation Engine."""

from dataclasses import replace

import pytest

from scenesmith import (
    CanonCharacterCard,
    CanonCharacterFact,
    CanonPromptBuilder,
    CanonSceneContext,
    CharacterCardBuilder,
    ExportEngine,
    PresentationEngine,
    PresentationSection,
    ProductionPack,
    ProductionPackView,
    PromptBundle,
    SceneAnalysis,
    SceneAnalyzer,
    SceneContextBuilder,
    SceneSheetView,
    WorldSheetView,
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


def test_presentation_section_rejects_blank_items() -> None:
    """Presentation sections should not contain empty visible rows."""
    with pytest.raises(ValueError, match="Presentation section item"):
        PresentationSection(title="Status", items=("Alive", " "))


def test_presentation_section_rejects_duplicate_items() -> None:
    """Presentation sections should not contain duplicate visible rows."""
    with pytest.raises(ValueError, match="items must be unique"):
        PresentationSection(title="Status", items=("Alive", "Alive"))


def test_scene_sheet_view_rejects_invalid_scene_id() -> None:
    """Presented scene sheets keep machine-token scene IDs."""
    with pytest.raises(ValueError, match="Scene sheet ID"):
        SceneSheetView(
            scene_id="scene 001",
            title="Opening",
            chapter_label="chapter_001",
            location=PresentationSection("Location", ("Unknown",)),
            characters_present=PresentationSection("Characters", ("Unknown",)),
            mood=PresentationSection("Mood", ("Unknown",)),
            purpose=PresentationSection("Purpose", ("Unknown",)),
            visual_highlights=PresentationSection("Visuals", ("Unknown",)),
            continuity_changes=PresentationSection("Continuity", ("Unknown",)),
            environment=PresentationSection("Environment", ("Unknown",)),
            evidence_summary="0 verified evidence references",
        )


def test_presentation_engine_dedupes_character_profile_items() -> None:
    """Repeated facts do not duplicate human profile items."""
    card, _context, _analysis, _pack = build_outputs()
    duplicate_card = replace(
        card,
        facts=card.facts + card.facts,
    )

    profile = PresentationEngine().character_profile(duplicate_card)

    assert profile.current_equipment.items == ("Iron Sword",)


def test_presentation_engine_groups_generic_character_attributes() -> None:
    """Character profiles should not depend on one story's attribute names."""
    card, _context, _analysis, _pack = build_outputs()
    evidence = card.facts[0].evidence
    generic_card = replace(
        card,
        facts=(
            CanonCharacterFact(
                attribute="training_plan",
                value="Win the bakery contest",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_002",
                valid_from_scene_id="source_demo_chapter_002_scene_001",
            ),
            CanonCharacterFact(
                attribute="magic_reward",
                value="Flame Glaze Technique",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_002",
                valid_from_scene_id="source_demo_chapter_002_scene_001",
            ),
            CanonCharacterFact(
                attribute="owned_vehicle",
                value="Delivery Van",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_002",
                valid_from_scene_id="source_demo_chapter_002_scene_001",
            ),
        ),
    )

    profile = PresentationEngine().character_profile(generic_card)

    assert profile.current_goal.items == ("Win the bakery contest",)
    assert profile.current_abilities.items == ("Flame Glaze Technique",)
    assert profile.current_assets.items == ("Delivery Van",)


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


def test_production_pack_view_rejects_duplicate_section_titles() -> None:
    """Production pack prompt sections must have distinct headings."""
    _card, context, analysis, _pack = build_outputs()
    scene = PresentationEngine().scene_sheet(context=context, analysis=analysis)
    section = PresentationSection("Prompt", ("Line.",))

    with pytest.raises(ValueError, match="section titles"):
        ProductionPackView(
            scene=scene,
            image_prompt=section,
            narration_prompt=section,
            camera_prompt=PresentationSection("Camera", ("Line.",)),
            animation_prompt=PresentationSection("Animation", ("Line.",)),
        )


def test_presentation_engine_rejects_mismatched_production_pack_scene() -> None:
    """Production pack views require the pack and scene sheet to agree."""
    _card, _context, _analysis, pack = build_outputs()

    with pytest.raises(ValueError, match="analysis must match"):
        replace(pack, scene_id="other_scene")


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


def test_world_sheet_view_rejects_duplicate_section_titles() -> None:
    """World sheets should not render duplicate entity section headings."""
    section = PresentationSection("Northern Fortress (location)", ("damage: Walls",))

    with pytest.raises(ValueError, match="section titles"):
        WorldSheetView(
            chapter_label="Chapter 1",
            entity_sections=(section, section),
            evidence_summary="1 verified evidence reference",
        )

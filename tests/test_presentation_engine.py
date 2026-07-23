"""Tests for Presentation Engine."""

import json
from dataclasses import replace

import pytest

from aevryn import (
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
    WorldEntityFact,
    WorldEntityState,
    WorldSheetView,
    WorldState,
    WorldStateBuilder,
)
from aevryn.core import Evidence
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


def test_presentation_section_normalizes_display_text() -> None:
    """Presentation sections normalize whitespace before rendering."""
    section = PresentationSection(
        title="  Current   Goal ",
        items=("  Win   the contest  ",),
    )

    assert section.title == "Current Goal"
    assert section.items == ("Win the contest",)


def test_presentation_section_rejects_normalized_duplicate_items() -> None:
    """Presentation sections should reject duplicates after whitespace cleanup."""
    with pytest.raises(ValueError, match="items must be unique"):
        PresentationSection(title="Status", items=("Alive", " Alive "))


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


def test_presentation_engine_routes_identity_and_profile_facts() -> None:
    """Character profile facts should not fall through to recent changes."""
    card, _context, _analysis, _pack = build_outputs()
    evidence = card.facts[0].evidence
    identity_card = replace(
        card,
        display_name="Human male captain Mark",
        facts=(
            CanonCharacterFact(
                attribute="race",
                value="Human",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_001",
                valid_from_scene_id="source_demo_chapter_001_scene_001",
            ),
            CanonCharacterFact(
                attribute="gender",
                value="Male",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_001",
                valid_from_scene_id="source_demo_chapter_001_scene_001",
            ),
            CanonCharacterFact(
                attribute="alias",
                value="Captain Mark",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_001",
                valid_from_scene_id="source_demo_chapter_001_scene_001",
            ),
            CanonCharacterFact(
                attribute="title",
                value="Captain",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_001",
                valid_from_scene_id="source_demo_chapter_001_scene_001",
            ),
            CanonCharacterFact(
                attribute="description",
                value="human male captain",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_001",
                valid_from_scene_id="source_demo_chapter_001_scene_001",
            ),
            CanonCharacterFact(
                attribute="family_background",
                value="Merchant family",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_001",
                valid_from_scene_id="source_demo_chapter_001_scene_001",
            ),
            CanonCharacterFact(
                attribute="current_weapon",
                value="Iron Sword",
                previous_value="Rusty Dagger",
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_002",
                valid_from_scene_id="source_demo_chapter_002_scene_001",
            ),
        ),
    )

    profile = PresentationEngine().character_profile(identity_card)

    assert profile.race.items == ("Human",)
    assert profile.gender.items == ("Male",)
    assert profile.aliases.items == ("Captain Mark",)
    assert profile.titles.items == ("Captain",)
    assert profile.descriptions.items == ("human male captain",)
    assert profile.relationships.items == ("Merchant family",)
    assert profile.current_equipment.items == ("Iron Sword",)
    assert profile.recent_changes.items == (
        "source_demo_chapter_002: current_weapon -> Iron Sword",
    )


def test_presentation_engine_does_not_infer_identity_from_broad_context() -> None:
    """Race and gender should not be inferred from unrelated story context."""
    card, _context, _analysis, _pack = build_outputs()
    evidence = card.facts[0].evidence
    identity_card = replace(
        card,
        display_name="Zhao Chen",
        facts=(
            CanonCharacterFact(
                attribute="race",
                value="Half-Beastman",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_001",
                valid_from_scene_id="source_demo_chapter_001_scene_001",
            ),
            CanonCharacterFact(
                attribute="current_goal",
                value="Find a way to support the Half-Beastman crew",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_001",
                valid_from_scene_id="source_demo_chapter_001_scene_001",
            ),
        ),
    )

    profile = PresentationEngine().character_profile(identity_card)

    assert profile.race.items == ("Unknown",)
    assert profile.gender.items == ("Unknown",)
    assert profile.current_goal.items == ("Find a way to support the Half-Beastman crew",)


def test_presentation_engine_uses_explicit_identity_language() -> None:
    """Explicit kinship and species terms should fill identity sections."""
    card, _context, _analysis, _pack = build_outputs()
    evidence = card.facts[0].evidence
    identity_card = replace(
        card,
        facts=(
            CanonCharacterFact(
                attribute="family_context",
                value="Sister of Zhao Chen",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_001",
                valid_from_scene_id="source_demo_chapter_001_scene_001",
            ),
            CanonCharacterFact(
                attribute="origin_context",
                value="Half-Beastman slave from the frontier",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_001",
                valid_from_scene_id="source_demo_chapter_001_scene_001",
            ),
        ),
    )

    profile = PresentationEngine().character_profile(identity_card)

    assert profile.gender.items == ("Female",)
    assert profile.race.items == ("Half-Beastman",)
    assert profile.relationships.items == (
        "Sister of Zhao Chen",
        "Half-Beastman slave from the frontier",
    )


def test_presentation_engine_uses_character_linked_gender_evidence() -> None:
    """Direct gender facts can be shown when the evidence quote names the character."""
    card, _context, _analysis, _pack = build_outputs()
    evidence = replace(
        card.facts[0].evidence,
        quote="Jiang Shasha is Zhao Chen's fiancee and treats him coldly.",
    )
    identity_card = replace(
        card,
        display_name="Jiang Shasha",
        facts=(
            CanonCharacterFact(
                attribute="gender",
                value="Female",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_002",
                valid_from_scene_id="source_demo_chapter_002_scene_001",
            ),
        ),
    )

    profile = PresentationEngine().character_profile(identity_card)

    assert profile.gender.items == ("Female",)


def test_presentation_engine_rejects_borrowed_group_gender_evidence() -> None:
    """A nearby gendered group should not assign gender to another character."""
    card, _context, _analysis, _pack = build_outputs()
    evidence = replace(
        card.facts[0].evidence,
        quote="The Starfleet Commander said the fleet could only recruit female soldiers.",
    )
    identity_card = replace(
        card,
        display_name="Starfleet Commander",
        facts=(
            CanonCharacterFact(
                attribute="gender",
                value="Female",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_002",
                valid_from_scene_id="source_demo_chapter_002_scene_001",
            ),
        ),
    )

    profile = PresentationEngine().character_profile(identity_card)

    assert profile.gender.items == ("Unknown",)


def test_presentation_engine_does_not_read_male_inside_female() -> None:
    """Female labels should not accidentally satisfy Male support."""
    card, _context, _analysis, _pack = build_outputs()
    evidence = replace(
        card.facts[0].evidence,
        quote="The female half-beastman crew member watched Zhao Chen.",
    )
    identity_card = replace(
        card,
        display_name="Female Half-Beastman crew member",
        facts=(
            CanonCharacterFact(
                attribute="gender",
                value="Male",
                previous_value=None,
                evidence=evidence,
                valid_from_chapter_id="source_demo_chapter_002",
                valid_from_scene_id="source_demo_chapter_002_scene_001",
            ),
        ),
    )

    profile = PresentationEngine().character_profile(identity_card)

    assert profile.gender.items == ("Unknown",)


def test_presentation_engine_hides_conflicting_gender_values() -> None:
    """Character profiles should never show Male and Female at the same time."""
    card, _context, _analysis, _pack = build_outputs()
    male_evidence = replace(
        card.facts[0].evidence,
        quote="Zhao Chen is a male student in the captaincy department.",
    )
    female_evidence = replace(
        card.facts[0].evidence,
        quote="Zhao Chen is called a female soldier by mistake.",
    )
    identity_card = replace(
        card,
        display_name="Zhao Chen",
        facts=(
            CanonCharacterFact(
                attribute="gender",
                value="Male",
                previous_value=None,
                evidence=male_evidence,
                valid_from_chapter_id="source_demo_chapter_002",
                valid_from_scene_id="source_demo_chapter_002_scene_001",
            ),
            CanonCharacterFact(
                attribute="gender",
                value="Female",
                previous_value=None,
                evidence=female_evidence,
                valid_from_chapter_id="source_demo_chapter_002",
                valid_from_scene_id="source_demo_chapter_002_scene_001",
            ),
        ),
    )

    profile = PresentationEngine().character_profile(identity_card)

    assert profile.gender.items == ("Unknown",)


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


def test_presentation_engine_keeps_prompt_safeguards_visible() -> None:
    """Prompt presentation must not trim production safety guidance."""
    _card, context, analysis, pack = build_outputs()
    engine = PresentationEngine()
    scene = engine.scene_sheet(context=context, analysis=analysis)

    view = engine.production_pack(pack=pack, scene=scene)
    prompt_lines = view.image_prompt.items

    assert any("Extra characters" in line for line in prompt_lines)
    assert any("Do not render names" in line for line in prompt_lines)
    assert any("Do not turn department" in line for line in prompt_lines)
    assert any("Style must not override accepted Canon" in line for line in prompt_lines)


def test_presentation_engine_preserves_prompt_safeguards_when_prompt_is_long() -> None:
    """Long prompt presentation keeps Canon guardrails instead of only early filler."""
    _card, context, analysis, pack = build_outputs()
    filler_lines = [f"- Production detail {index:03d}" for index in range(80)]
    prompt_bundle = PromptBundle(
        image_prompt="\n".join(
            [
                "Image generation task.",
                *filler_lines,
                (
                    "- Do not add facts, characters, items, locations, or "
                    "relationships without evidence."
                ),
                (
                    "- Do not render names, entity IDs, project labels, scene titles, "
                    "prompt headings, captions, subtitles, or UI panels."
                ),
                "- Style must not override accepted Canon.",
            ]
        ),
        narration_prompt=pack.prompt_bundle.narration_prompt,
        camera_prompt=pack.prompt_bundle.camera_prompt,
        animation_prompt=pack.prompt_bundle.animation_prompt,
    )
    compact_pack = replace(pack, prompt_bundle=prompt_bundle)
    engine = PresentationEngine()
    scene = engine.scene_sheet(context=context, analysis=analysis)

    view = engine.production_pack(pack=compact_pack, scene=scene)
    prompt_lines = view.image_prompt.items

    assert len(prompt_lines) == 48
    assert any("without evidence" in line for line in prompt_lines)
    assert any("Do not render names" in line for line in prompt_lines)
    assert any("Style must not override accepted Canon" in line for line in prompt_lines)


def test_presentation_engine_removes_prompt_structural_placeholders() -> None:
    """Prompt presentation should not expose structural or internal placeholders."""
    _card, context, analysis, pack = build_outputs()
    prompt_bundle = PromptBundle(
        image_prompt="\n".join(
            [
                "Visual Highlights:",
                "- Unknown",
                "- Iron Sword",
                "Scene ID: source_demo_chapter_002_scene_001",
                "Source ID: aevryn_import_bundle",
                (
                    "Evidence anchor: "
                    "aevryn_import_bundle_chapter_010_scene_001_paragraph_023_"
                    "sentence_002_anchor"
                ),
                "Import ID: import_7d8de6b4_a531_4f4e_b22e_b5c18acd4dbf",
            ]
        ),
        narration_prompt=pack.prompt_bundle.narration_prompt,
        camera_prompt=pack.prompt_bundle.camera_prompt,
        animation_prompt=pack.prompt_bundle.animation_prompt,
    )
    compact_pack = replace(pack, prompt_bundle=prompt_bundle)
    engine = PresentationEngine()
    scene = engine.scene_sheet(context=context, analysis=analysis)

    view = engine.production_pack(pack=compact_pack, scene=scene)

    assert view.image_prompt.items == ("Iron Sword",)


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
    world_state = WorldStateBuilder(database=build_world_database()).build_state(
        entity_ids=("location_northern_fortress",),
        chapter_index=6,
    )
    state = PresentationEngine().world_sheet(state=world_state)

    markdown = ExportEngine().world_sheet_view_markdown(state)

    assert "# World Sheet" in markdown
    assert "Northern Fortress (location)" in markdown
    assert "damage: Walls damaged" in markdown


def test_presentation_engine_merges_duplicate_world_section_titles() -> None:
    """World sheet rendering tolerates duplicate AI-created world labels."""
    world_state = WorldState(
        chapter_index=4,
        entities=(
            WorldEntityState(
                entity_id="location_raven_hall",
                entity_type="location",
                display_name="Raven Hall",
                chapter_index=4,
                facts=(
                    WorldEntityFact(
                        attribute="condition",
                        value="Under curfew",
                        evidence=Evidence(
                            evidence_id="evidence_raven_hall_condition",
                            source_id="source_demo",
                            chapter_id="chapter_004",
                            scene_id="scene_001",
                            paragraph_index=1,
                            sentence_index=1,
                            quote="Raven Hall was under curfew.",
                            confidence=1.0,
                        ),
                        valid_from_chapter_id="chapter_004",
                        valid_from_scene_id="scene_001",
                    ),
                ),
            ),
            WorldEntityState(
                entity_id="location_raven_hall_alias",
                entity_type="location",
                display_name="Raven Hall",
                chapter_index=4,
                facts=(
                    WorldEntityFact(
                        attribute="security",
                        value="Guarded gates",
                        evidence=Evidence(
                            evidence_id="evidence_raven_hall_security",
                            source_id="source_demo",
                            chapter_id="chapter_004",
                            scene_id="scene_002",
                            paragraph_index=1,
                            sentence_index=1,
                            quote="The gates were guarded.",
                            confidence=1.0,
                        ),
                        valid_from_chapter_id="chapter_004",
                        valid_from_scene_id="scene_002",
                    ),
                ),
            ),
        ),
    )

    state = PresentationEngine().world_sheet(state=world_state)

    assert tuple(section.title for section in state.entity_sections) == (
        "Raven Hall (location)",
    )
    assert state.entity_sections[0].items == (
        "condition: Under curfew",
        "security: Guarded gates",
    )


def test_export_engine_writes_world_state_json() -> None:
    """Export Engine writes machine-readable world state JSON."""
    world_state = WorldStateBuilder(database=build_world_database()).build_state(
        entity_ids=("location_northern_fortress",),
        chapter_index=6,
    )

    exported = ExportEngine().world_state_json(world_state)
    data = json.loads(exported)

    assert data["chapter_index"] == 6
    assert data["entities"][0]["entity_id"] == "location_northern_fortress"
    assert data["entities"][0]["facts"][0]["evidence"]["quote"]


def test_world_sheet_view_rejects_duplicate_section_titles() -> None:
    """World sheets should not render duplicate entity section headings."""
    section = PresentationSection("Northern Fortress (location)", ("damage: Walls",))

    with pytest.raises(ValueError, match="section titles"):
        WorldSheetView(
            chapter_label="Chapter 1",
            entity_sections=(section, section),
            evidence_summary="1 verified evidence reference",
        )

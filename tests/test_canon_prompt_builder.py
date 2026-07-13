"""Tests for Phase 8 Prompt Generation."""

import pytest

from aevryn import (
    CanonDatabase,
    CanonPromptBuilder,
    CanonSceneContext,
    CharacterCardBuilder,
    SceneAnalysis,
    SceneAnalyzer,
    SceneContextBuilder,
    StoryImporter,
)
from aevryn.core import Character, Entity, Evidence, Fact, StateChange, TimelineEvent
from tests.test_scene_context_builder import build_database, build_imported_source


def build_context() -> CanonSceneContext:
    """Build scene context for prompt tests."""
    imported_source = build_imported_source()
    database = build_database()
    return SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    ).build_context(
        imported_source=imported_source,
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark",),
    )


def test_canon_prompt_builder_builds_image_prompt_from_scene_context() -> None:
    """Image prompts include accepted scene facts and relationships."""
    prompt = CanonPromptBuilder().build_image_prompt(build_context())

    assert "Generate this image using only accepted Aevryn canon." in prompt
    assert "Scene Summary:" in prompt
    assert "Purpose:" in prompt
    assert "Character: Mark" in prompt
    assert "Character: Mark (character_mark)" not in prompt
    assert "- Current Weapon: Iron Sword" in prompt
    assert "Mark retains Current Weapon: Iron Sword" in prompt


def test_canon_prompt_builder_builds_narration_prompt_without_guessing() -> None:
    """Narration prompts explicitly constrain output to accepted canon."""
    prompt = CanonPromptBuilder().build_narration_prompt(build_context())

    assert "Narrate using only accepted canon facts." in prompt
    assert "Character: Mark" in prompt
    assert "Character: Mark (character_mark)" not in prompt


def test_canon_prompt_builder_builds_camera_prompt_without_new_canon() -> None:
    """Camera prompts do not authorize invented canon."""
    prompt = CanonPromptBuilder().build_camera_prompt(build_context())

    assert "Describe camera framing without inventing new canon." in prompt
    assert "Character: Mark" in prompt
    assert "Character: Mark (character_mark)" not in prompt


def test_canon_prompt_builder_builds_animation_prompt_from_facts() -> None:
    """Animation prompts use accepted scene facts and relationships."""
    prompt = CanonPromptBuilder().build_animation_prompt(build_context())

    assert "Describe motion using only accepted scene facts." in prompt
    assert "Mark retains Current Weapon: Iron Sword" in prompt


def test_canon_prompt_builder_builds_bundle() -> None:
    """Prompt builder returns all prompt types."""
    bundle = CanonPromptBuilder().build_bundle(build_context())

    assert bundle.image_prompt
    assert bundle.narration_prompt
    assert bundle.camera_prompt
    assert bundle.animation_prompt


def test_canon_prompt_builder_does_not_dump_full_scene_text() -> None:
    """Prompt builder keeps source text concise."""
    prompt = CanonPromptBuilder().build_image_prompt(build_context())

    assert "Paragraphs:" not in prompt
    assert len(prompt) < 3600


def test_canon_prompt_builder_includes_current_scene_visual_anchors() -> None:
    """Image prompts prioritize current-scene visual anchors over background objects."""
    imported_source = StoryImporter().import_text(
        source_id="source_visual",
        title="Visual Story",
        text=(
            "Chapter 1\n"
            "Mira sat in a classroom with white desks. "
            "Holographic screens glowed in front of every student. "
            "A floor-to-ceiling window showed a stormy sky. "
            "Later, Mira received a dragon engine blueprint."
        ),
    )
    scene = imported_source.story.chapters[0].scenes[0]
    database = CanonDatabase()
    database.store_character(
        Character(
            entity=Entity(
                entity_id="character_mira",
                entity_type="character",
                display_name="Mira",
            )
        )
    )
    database.store_chapter(imported_source.story.chapters[0])
    database.store_evidence(
        Evidence(
            evidence_id="evidence_visual",
            source_id="source_visual",
            chapter_id=scene.chapter_id,
            scene_id=scene.scene_id,
            paragraph_index=1,
            sentence_index=4,
            quote="Later, Mira received a dragon engine blueprint.",
            confidence=1.0,
        )
    )
    database.store_fact(
        Fact(
            fact_id="fact_mira_blueprint",
            entity_id="character_mira",
            attribute="current_asset",
            value="Dragon engine blueprint",
            evidence_id="evidence_visual",
        )
    )
    database.store_timeline_event(
        TimelineEvent(
            event_id="event_visual",
            chapter_id=scene.chapter_id,
            scene_id=scene.scene_id,
            description="Mira receives blueprint",
            evidence_id="evidence_visual",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_mira_blueprint",
            fact_id="fact_mira_blueprint",
            valid_from_event_id="event_visual",
        )
    )
    context = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    ).build_context(
        imported_source=imported_source,
        scene_id=scene.scene_id,
        character_ids=("character_mira",),
    )

    prompt = CanonPromptBuilder().build_image_prompt(context)

    assert "Scene-grounded visual anchors" in prompt
    assert "Mira sat in a classroom with white desks." in prompt
    assert "Holographic screens glowed in front of every student." in prompt
    assert "A floor-to-ceiling window showed a stormy sky." in prompt
    assert prompt.index("Scene-grounded visual anchors") < prompt.index(
        "Dragon engine blueprint"
    )


def test_canon_prompt_builder_includes_scene_world_context_and_exclusions() -> None:
    """Image prompts include connected world facts and explicit generation exclusions."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_fact(
        Fact(
            fact_id="fact_sword_visual_design",
            entity_id="item_iron_sword",
            attribute="visual_design",
            value="Chipped iron blade with a plain leather grip",
            evidence_id="evidence_relationship",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_sword_visual_design",
            fact_id="fact_sword_visual_design",
            valid_from_event_id="event_008_weapon",
        )
    )
    context = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    ).build_context(
        imported_source=imported_source,
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark",),
    )

    prompt = CanonPromptBuilder().build_image_prompt(context)

    assert "Scene production brief:" in prompt
    assert "World and scene object context:" in prompt
    assert (
        "Iron Sword Visual Design: Chipped iron blade with a plain leather grip"
        in prompt
    )
    assert "Mark Owns Iron Sword" in prompt
    assert "Do not include unless supported by this scene:" in prompt
    assert "Later canon objects or rewards" in prompt


def test_canon_prompt_builder_separates_facts_composition_lighting_and_style() -> None:
    """Image prompts keep story understanding before production style."""
    prompt = CanonPromptBuilder().build_image_prompt(build_context())

    assert "Scene production brief:" in prompt
    assert "World and scene object context:" in prompt
    assert "Composition:" in prompt
    assert "Lighting:" in prompt
    assert "Rendering style:" in prompt
    assert "Style must not override accepted Canon." in prompt
    assert prompt.index("Scene production brief:") < prompt.index("Composition:")
    assert prompt.index("World and scene object context:") < prompt.index(
        "Rendering style:"
    )
    assert prompt.index("Do not include unless supported by this scene:") < prompt.index(
        "Rendering style:"
    )


def test_canon_prompt_builder_prevents_prompt_metadata_as_visible_text() -> None:
    """Image prompts prevent Canon metadata from becoming generated image labels."""
    prompt = CanonPromptBuilder().build_image_prompt(build_context())

    assert "Visible text and labels:" in prompt
    assert "Do not render names, entity IDs" in prompt
    assert "without readable text unless exact text is accepted canon" in prompt
    assert "department, role, goal, or asset names" in prompt
    assert prompt.index("Visible text and labels:") < prompt.index("Rendering style:")


def test_canon_prompt_builder_camera_prompt_separates_composition_from_camera() -> None:
    """Camera prompts distinguish visual arrangement from cinematography."""
    prompt = CanonPromptBuilder().build_camera_prompt(build_context())

    assert "Composition:" in prompt
    assert "Camera direction:" in prompt
    assert "Lighting:" in prompt
    assert prompt.index("Composition:") < prompt.index("Camera direction:")


def test_canon_prompt_builder_camera_and_animation_include_text_guard() -> None:
    """Visual production variants carry the same visible text constraints."""
    builder = CanonPromptBuilder()
    context = build_context()

    assert "Visible text and labels:" in builder.build_camera_prompt(context)
    assert "Visible text and labels:" in builder.build_animation_prompt(context)


def test_canon_prompt_builder_uses_scene_relevant_character_facts() -> None:
    """Prompt character details come from focused scene context, not full cards."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_fact(
        Fact(
            fact_id="fact_001_school_year",
            entity_id="character_mark",
            attribute="school_year",
            value="First Year",
            evidence_id="evidence_001",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_001_school_year",
            fact_id="fact_001_school_year",
            valid_from_event_id="event_001_weapon",
        )
    )
    context = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    ).build_context(
        imported_source=imported_source,
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark",),
    )

    prompt = CanonPromptBuilder().build_image_prompt(context)

    assert "- Current Weapon: Iron Sword" in prompt
    assert "school_year" not in prompt


def test_canon_prompt_builder_omits_mechanical_metadata_from_character_details() -> None:
    """Prompt character details omit task math that belongs in audit views."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_fact(
        Fact(
            fact_id="fact_008_task_reward",
            entity_id="character_mark",
            attribute="active_task_reward",
            value="One contest point",
            evidence_id="evidence_008",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_008_task_reward",
            fact_id="fact_008_task_reward",
            valid_from_event_id="event_008_weapon",
        )
    )
    database.store_fact(
        Fact(
            fact_id="fact_008_task",
            entity_id="character_mark",
            attribute="active_task",
            value="Win the contest",
            evidence_id="evidence_008",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_008_task",
            fact_id="fact_008_task",
            valid_from_event_id="event_008_weapon",
        )
    )
    context = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    ).build_context(
        imported_source=imported_source,
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark",),
    )

    prompt = CanonPromptBuilder().build_image_prompt(context)

    assert "Active Task: Win the contest" in prompt
    assert "active_task_reward" not in prompt
    assert "One contest point" not in prompt


def test_canon_prompt_builder_rejects_duplicate_analysis_bullets() -> None:
    """Prompt sections require duplicate analysis rows to fail upstream."""
    with pytest.raises(ValueError, match="must be unique"):
        CanonPromptBuilder(analyzer=DuplicateAnalysisAnalyzer()).build_image_prompt(
            build_context()
        )


def test_canon_prompt_builder_shortens_long_analysis_text() -> None:
    """Long analyzer text is compressed for production prompts."""
    prompt = CanonPromptBuilder(analyzer=LongAnalysisAnalyzer()).build_image_prompt(
        build_context()
    )

    assert "Sentence 020" not in prompt
    assert len(prompt) < 4600


class DuplicateAnalysisAnalyzer(SceneAnalyzer):
    """Scene Analyzer stub that returns duplicate list values."""

    def analyze(self, context: CanonSceneContext) -> SceneAnalysis:
        """Return duplicate analysis values for prompt formatting tests."""
        return SceneAnalysis(
            scene_id=context.scene.scene_id,
            summary="Summary",
            purpose="Purpose",
            conflict="Conflict",
            mood="Mood",
            visual_highlights=("Same visual", "Same visual"),
            character_goals=("Same goal", "Same goal"),
            character_emotions=(),
            important_objects=("Same object", "Same object"),
            environment_summary="Environment",
            changes_introduced=(),
            continuity_notes=("Same note", "Same note"),
            forbidden_elements=("Same guard", "Same guard"),
        )


class LongAnalysisAnalyzer(SceneAnalyzer):
    """Scene Analyzer stub that returns long free-form text."""

    def analyze(self, context: CanonSceneContext) -> SceneAnalysis:
        """Return long analysis values for prompt compression tests."""
        long_text = " ".join(f"Sentence {index:03d}" for index in range(1, 80))
        return SceneAnalysis(
            scene_id=context.scene.scene_id,
            summary=long_text,
            purpose=long_text,
            conflict=long_text,
            mood=long_text,
            visual_highlights=(),
            character_goals=(),
            character_emotions=(),
            important_objects=(),
            environment_summary=long_text,
            changes_introduced=(),
            continuity_notes=(),
            forbidden_elements=("Do not invent canon.",),
        )

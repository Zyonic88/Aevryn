"""Tests for Phase 8 Prompt Generation."""

import pytest

from aevryn import (
    CanonPromptBuilder,
    CanonSceneContext,
    CharacterCardBuilder,
    SceneAnalysis,
    SceneAnalyzer,
    SceneContextBuilder,
)
from aevryn.core import Fact, StateChange
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
    assert "Character: Mark (character_mark)" in prompt
    assert "- current_weapon: Iron Sword" in prompt
    assert "character_mark retains current_weapon: Iron Sword" in prompt


def test_canon_prompt_builder_builds_narration_prompt_without_guessing() -> None:
    """Narration prompts explicitly constrain output to accepted canon."""
    prompt = CanonPromptBuilder().build_narration_prompt(build_context())

    assert "Narrate using only accepted canon facts." in prompt
    assert "Character: Mark (character_mark)" in prompt


def test_canon_prompt_builder_builds_camera_prompt_without_new_canon() -> None:
    """Camera prompts do not authorize invented canon."""
    prompt = CanonPromptBuilder().build_camera_prompt(build_context())

    assert "Describe camera framing without inventing new canon." in prompt
    assert "Character: Mark (character_mark)" in prompt


def test_canon_prompt_builder_builds_animation_prompt_from_facts() -> None:
    """Animation prompts use accepted scene facts and relationships."""
    prompt = CanonPromptBuilder().build_animation_prompt(build_context())

    assert "Describe motion using only accepted scene facts." in prompt
    assert "character_mark retains current_weapon: Iron Sword" in prompt


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
    assert len(prompt) < 1800


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

    assert "- current_weapon: Iron Sword" in prompt
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

    assert "active_task: Win the contest" in prompt
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
    assert len(prompt) < 2400


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

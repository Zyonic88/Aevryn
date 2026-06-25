"""Tests for Scene Analyzer."""

from dataclasses import replace

import pytest

from scenesmith import (
    CanonDatabase,
    CanonPromptBuilder,
    CanonSceneContext,
    CharacterCardBuilder,
    SceneAnalyzer,
    SceneContextBuilder,
    StoryImporter,
)
from scenesmith.core import Character, Entity, Evidence, Fact, StateChange, TimelineEvent
from tests.test_scene_context_builder import build_database, build_imported_source


def build_context() -> CanonSceneContext:
    """Build scene context for analyzer tests."""
    database = build_database()
    return SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    ).build_context(
        imported_source=build_imported_source(),
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark",),
    )


def test_scene_analyzer_summarizes_scene_meaning() -> None:
    """Scene Analyzer produces compact meaning-focused output."""
    analysis = SceneAnalyzer().analyze(build_context())

    assert analysis.scene_id == "source_demo_chapter_002_scene_001"
    assert "character_mark current_weapon = Iron Sword" in analysis.summary
    assert analysis.purpose == "Establish current character and world state."
    assert analysis.forbidden_elements


def test_prompt_builder_builds_production_pack() -> None:
    """Prompt Builder produces a production pack from scene analysis."""
    pack = CanonPromptBuilder().build_production_pack(build_context())

    assert pack.scene_summary
    assert pack.prompt_bundle.image_prompt
    assert "Generate this image" in pack.prompt_bundle.image_prompt
    assert "Forbidden Elements:" in pack.prompt_bundle.image_prompt


def test_scene_analyzer_prioritizes_current_scene_changes() -> None:
    """Current-scene conflict outranks older retained ability canon."""
    database = CanonDatabase()
    imported = StoryImporter().import_text(
        source_id="story_demo",
        title="Demo Story",
        text="""Chapter 2
Zhao gained Fleet Luck Bonus.

Chapter 3
Zhang Haoran mocked Zhao Chen with contempt.""",
    )
    database.store_character(
        Character(
            entity=Entity(
                entity_id="character_zhao_chen",
                entity_type="character",
                display_name="Zhao Chen",
            )
        )
    )
    database.store_character(
        Character(
            entity=Entity(
                entity_id="character_zhang_haoran",
                entity_type="character",
                display_name="Zhang Haoran",
            )
        )
    )
    for chapter in imported.story.chapters:
        database.store_chapter(chapter)
    database.store_evidence(
        Evidence(
            evidence_id="evidence_story_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor",
            source_id="story_demo",
            chapter_id="story_demo_chapter_002",
            scene_id="story_demo_chapter_002_scene_001",
            paragraph_index=1,
            sentence_index=1,
            quote="Zhao gained Fleet Luck Bonus.",
            confidence=1.0,
        )
    )
    database.store_evidence(
        Evidence(
            evidence_id="evidence_story_demo_chapter_003_scene_001_paragraph_001_sentence_001_anchor",
            source_id="story_demo",
            chapter_id="story_demo_chapter_003",
            scene_id="story_demo_chapter_003_scene_001",
            paragraph_index=1,
            sentence_index=1,
            quote="Zhang Haoran mocked Zhao Chen with contempt.",
            confidence=1.0,
        )
    )
    reward_fact = Fact(
        fact_id="fact_reward",
        entity_id="character_zhao_chen",
        attribute="system_reward_fleet_luck_bonus",
        value="Fleet Luck Bonus",
        evidence_id="evidence_story_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor",
    )
    conflict_fact = Fact(
        fact_id="fact_contempt",
        entity_id="character_zhang_haoran",
        attribute="attitude_toward_zhao_chen",
        value="Contempt",
        evidence_id="evidence_story_demo_chapter_003_scene_001_paragraph_001_sentence_001_anchor",
    )
    database.store_fact(reward_fact)
    database.store_fact(conflict_fact)
    database.store_timeline_event(
        TimelineEvent(
            event_id="event_reward",
            chapter_id="story_demo_chapter_002",
            scene_id="story_demo_chapter_002_scene_001",
            description="Reward gained",
            evidence_id="evidence_story_demo_chapter_002_scene_001_paragraph_001_sentence_001_anchor",
        )
    )
    database.store_timeline_event(
        TimelineEvent(
            event_id="event_contempt",
            chapter_id="story_demo_chapter_003",
            scene_id="story_demo_chapter_003_scene_001",
            description="Mocking begins",
            evidence_id="evidence_story_demo_chapter_003_scene_001_paragraph_001_sentence_001_anchor",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_reward",
            fact_id="fact_reward",
            valid_from_event_id="event_reward",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_contempt",
            fact_id="fact_contempt",
            valid_from_event_id="event_contempt",
        )
    )
    context = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    ).build_context(
        imported_source=imported,
        scene_id="story_demo_chapter_003_scene_001",
        character_ids=("character_zhao_chen", "character_zhang_haoran"),
    )

    analysis = SceneAnalyzer().analyze(context)

    assert analysis.purpose == "Reveal social conflict and relationship tension."
    assert analysis.conflict == "Social humiliation or contempt is present."
    assert analysis.changes_introduced == (
        "character_zhang_haoran attitude_toward_zhao_chen = Contempt",
    )
    assert any("Fleet Luck Bonus" in note for note in analysis.continuity_notes)


def test_scene_analyzer_rejects_mismatched_snapshot_scene() -> None:
    """Scene analysis requires snapshot and scene IDs to match."""
    context = build_context()
    mismatched_context = replace(
        context,
        snapshot=replace(context.snapshot, scene_id="other_scene"),
    )

    with pytest.raises(ValueError, match="snapshot"):
        SceneAnalyzer().analyze(mismatched_context)


def test_scene_analyzer_dedupes_repeated_output_values() -> None:
    """Repeated accepted facts do not inflate analyzer outputs."""
    context = build_context()
    repeated_context = replace(
        context,
        active_facts=(context.active_facts[0], context.active_facts[0]),
    )

    analysis = SceneAnalyzer().analyze(repeated_context)

    assert analysis.changes_introduced == ()
    assert analysis.continuity_notes == (
        "character_mark retains current_weapon: Iron Sword",
    )

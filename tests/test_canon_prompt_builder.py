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


def test_canon_prompt_builder_keeps_machine_scene_ids_out_of_prompt_text() -> None:
    """Prompt text should not expose internal scene identifiers."""
    context = build_context()
    bundle = CanonPromptBuilder().build_bundle(context)
    prompt_text = "\n".join(
        (
            bundle.image_prompt,
            bundle.narration_prompt,
            bundle.camera_prompt,
            bundle.animation_prompt,
        )
    )

    assert context.scene.scene_id not in prompt_text
    assert "Scene ID:" not in prompt_text


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


def test_canon_prompt_builder_includes_bounded_current_scene_action_beats() -> None:
    """Prompts include compact canon-backed beats without storing source prose."""
    context = build_context()

    prompt = CanonPromptBuilder().build_image_prompt(context)
    action_section = prompt.split("Current scene action beats:", 1)[1].split("\n\n", 1)[0]

    assert "Current scene action beats:" in prompt
    assert "Mark Current Weapon: Iron Sword" in action_section
    assert "Scene purpose:" in action_section
    assert "Mark wakes in the forest" not in action_section
    assert action_section.count("\n- ") == 3


def test_canon_prompt_builder_adds_action_beats_to_all_prompt_types() -> None:
    """Every production prompt carries the same bounded scene moment context."""
    builder = CanonPromptBuilder()
    context = build_context()

    assert "Current scene action beats:" in builder.build_image_prompt(context)
    assert "Current scene action beats:" in builder.build_narration_prompt(context)
    assert "Current scene action beats:" in builder.build_camera_prompt(context)
    assert "Current scene action beats:" in builder.build_animation_prompt(context)


def test_canon_prompt_builder_includes_action_visual_anchors() -> None:
    """Image prompts include current-scene body language as visual anchors."""
    imported_source = StoryImporter().import_text(
        source_id="source_action_visual",
        title="Action Visual Story",
        text=(
            "Chapter 1\n"
            "Mira smiled at the warning. "
            "She crossed her arms before Leo entered. "
            "The argument continued without any new equipment."
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
    context = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    ).build_context(
        imported_source=imported_source,
        scene_id=scene.scene_id,
        character_ids=("character_mira",),
    )

    prompt = CanonPromptBuilder().build_image_prompt(context)

    assert "Mira smiled at the warning." in prompt
    assert "She crossed her arms before Leo entered." in prompt


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
    assert "Visual reference requirements:" in prompt
    assert (
        "Iron Sword Visual Design: Chipped iron blade with a plain leather grip"
        in prompt
    )
    assert "World and scene object context:" in prompt
    assert (
        "Iron Sword Visual Design: Chipped iron blade with a plain leather grip"
        in prompt
    )
    assert "Mark Owns Iron Sword" in prompt
    assert "Do not include unless supported by this scene:" in prompt
    assert "Later canon objects or rewards" in prompt


def test_canon_prompt_builder_includes_confirmed_visible_character_traits() -> None:
    """Image prompts include scene-relevant visible traits only when Canon accepts them."""
    imported_source = build_imported_source()
    database = build_database()
    for attribute, value in (
        ("gender", "Male"),
        ("race", "Human"),
        ("species", "Human"),
        ("expression", "Worried"),
        ("posture", "Guarded stance"),
        ("rank", "Cadet"),
    ):
        fact_id = f"fact_mark_{attribute}"
        database.store_fact(
            Fact(
                fact_id=fact_id,
                entity_id="character_mark",
                attribute=attribute,
                value=value,
                evidence_id="evidence_008",
            )
        )
        database.store_state_change(
            StateChange(
                state_change_id=f"state_mark_{attribute}",
                fact_id=fact_id,
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

    assert "- Gender: Male" in prompt
    assert "- Race: Human" in prompt
    assert "- Species: Human" in prompt
    assert "- Expression: Worried" in prompt
    assert "- Posture: Guarded stance" in prompt
    assert "- Rank: Cadet" in prompt
    assert "Appearance: Not specified by accepted canon." not in prompt


def test_canon_prompt_builder_tracks_known_and_unknown_visual_identity_traits() -> None:
    """Image prompts should identify which character visual traits are still unknown."""
    imported_source = build_imported_source()
    database = build_database()
    for attribute, value in (
        ("gender", "Male"),
        ("race", "Human"),
        ("hair_color", "Black"),
    ):
        fact_id = f"fact_mark_visual_identity_{attribute}"
        database.store_fact(
            Fact(
                fact_id=fact_id,
                entity_id="character_mark",
                attribute=attribute,
                value=value,
                evidence_id="evidence_008",
            )
        )
        database.store_state_change(
            StateChange(
                state_change_id=f"state_mark_visual_identity_{attribute}",
                fact_id=fact_id,
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

    assert "Visual ID:" in prompt
    assert "- Mark: known gender,hair,race/species." in prompt
    assert "Missing" in prompt
    assert "gender" not in prompt.split("Missing", 1)[1].split(";", 1)[0]
    assert "race/species" not in prompt.split("Missing", 1)[1].split(
        ";",
        1,
    )[0]
    assert (
        "Do not guess missing visual traits." in prompt
    )


def test_canon_prompt_builder_adds_visual_requirements_to_visual_prompt_types() -> None:
    """Image, camera, and animation prompts carry mandatory canon visual references."""
    imported_source = build_imported_source()
    database = build_database()
    for attribute, value in (
        ("hair_color", "Silver"),
        ("eye_color", "Blue"),
    ):
        fact_id = f"fact_mark_required_visual_{attribute}"
        database.store_fact(
            Fact(
                fact_id=fact_id,
                entity_id="character_mark",
                attribute=attribute,
                value=value,
                evidence_id="evidence_001",
            )
        )
        database.store_state_change(
            StateChange(
                state_change_id=f"state_mark_required_visual_{attribute}",
                fact_id=fact_id,
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
    builder = CanonPromptBuilder()

    image_prompt = builder.build_image_prompt(context)
    camera_prompt = builder.build_camera_prompt(context)
    animation_prompt = builder.build_animation_prompt(context)

    for prompt in (image_prompt, camera_prompt, animation_prompt):
        assert "Visual reference requirements:" in prompt
        assert "Mark appearance: Eye Color: Blue; Hair Color: Silver" in prompt
        assert "keep unspecified traits neutral" in prompt


def test_canon_prompt_builder_marks_missing_visual_identity_neutral() -> None:
    """Missing character appearance should be explicit without rejecting the prompt."""
    prompt = CanonPromptBuilder().build_image_prompt(build_context())

    assert "- Mark: known none." in prompt
    assert "Missing" in prompt
    assert "neutral" in prompt


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


def test_canon_prompt_builder_carries_stable_character_appearance_from_cards() -> None:
    """Visual prompts preserve accepted character-sheet appearance across scenes."""
    imported_source = build_imported_source()
    database = build_database()
    for attribute, value in (
        ("hair_color", "Silver"),
        ("eye_color", "Blue"),
        ("build", "Lean"),
        ("school_year", "First Year"),
    ):
        fact_id = f"fact_001_{attribute}"
        database.store_fact(
            Fact(
                fact_id=fact_id,
                entity_id="character_mark",
                attribute=attribute,
                value=value,
                evidence_id="evidence_001",
            )
        )
        database.store_state_change(
            StateChange(
                state_change_id=f"state_001_{attribute}",
                fact_id=fact_id,
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

    builder = CanonPromptBuilder()
    image_prompt = builder.build_image_prompt(context)
    camera_prompt = builder.build_camera_prompt(context)
    animation_prompt = builder.build_animation_prompt(context)

    assert "- Hair Color: Silver" in image_prompt
    assert "- Eye Color: Blue" in image_prompt
    assert "- Build: Lean" in image_prompt
    assert "School Year: First Year" not in image_prompt
    assert "- Hair Color: Silver" in camera_prompt
    assert "- Eye Color: Blue" in animation_prompt


def test_canon_prompt_builder_carries_stable_identity_references_from_cards() -> None:
    """Production prompts preserve accepted aliases, titles, and descriptions."""
    imported_source = build_imported_source()
    database = build_database()
    for attribute, value in (
        ("alias", "General Mark"),
        ("title", "Commander"),
        ("description", "White-haired academy officer"),
        ("school_year", "First Year"),
    ):
        fact_id = f"fact_001_identity_{attribute}"
        database.store_fact(
            Fact(
                fact_id=fact_id,
                entity_id="character_mark",
                attribute=attribute,
                value=value,
                evidence_id="evidence_001",
            )
        )
        database.store_state_change(
            StateChange(
                state_change_id=f"state_001_identity_{attribute}",
                fact_id=fact_id,
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
    builder = CanonPromptBuilder()

    prompts = (
        builder.build_image_prompt(context),
        builder.build_narration_prompt(context),
        builder.build_camera_prompt(context),
        builder.build_animation_prompt(context),
    )

    for prompt in prompts:
        assert "Character identity references:" in prompt
        assert (
            "- Mark: Alias: General Mark; Description: White-haired academy "
            "officer; Title: Commander"
        ) in prompt
        assert "do not create extra characters from them" in prompt
        assert "School Year: First Year" not in prompt


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


def test_canon_prompt_builder_keeps_generation_context_in_every_prompt_type() -> None:
    """Production prompts preserve scene action, setting, character, and object context."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_fact(
        Fact(
            fact_id="fact_iron_sword_visual_material",
            entity_id="item_iron_sword",
            attribute="visual_material",
            value="Dull iron blade with a worn leather grip",
            evidence_id="evidence_relationship",
        )
    )
    database.store_state_change(
        StateChange(
            state_change_id="state_iron_sword_visual_material",
            fact_id="fact_iron_sword_visual_material",
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

    bundle = CanonPromptBuilder().build_bundle(context)
    prompts = (
        bundle.image_prompt,
        bundle.narration_prompt,
        bundle.camera_prompt,
        bundle.animation_prompt,
    )

    for prompt in prompts:
        assert "Scene production brief:" in prompt
        assert "Current scene action beats:" in prompt
        assert "Character: Mark" in prompt
        assert "World and scene object context:" in prompt
        assert "Iron Sword" in prompt
        assert "Dull iron blade with a worn leather grip" in prompt
        assert "Primary setting:" in prompt

    for visual_prompt in (
        bundle.image_prompt,
        bundle.camera_prompt,
        bundle.animation_prompt,
    ):
        assert "Visual reference requirements:" in visual_prompt
        assert "Iron Sword Visual Material: Dull iron blade with a worn leather grip" in (
            visual_prompt
        )


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
    assert len(prompt) < 5000


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

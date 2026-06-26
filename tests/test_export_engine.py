"""Tests for the SceneSmith Export Engine."""

import csv
import io
import json
from typing import Any, cast

import pytest

from scenesmith import (
    CanonEngine,
    CanonEntity,
    CharacterCard,
    CharacterEngine,
    EntityType,
    Evidence,
    ExportEngine,
    PromptBundle,
    PromptEngine,
    SceneContext,
    SceneEngine,
    StoryPosition,
    TimelineChapter,
    TimelineEngine,
    TimelineEvent,
    TimelineScene,
    TimelineStateChange,
)


def position(chapter_index: int, scene_index: int) -> StoryPosition:
    """Create a story position for tests."""
    return StoryPosition(chapter_index=chapter_index, scene_index=scene_index)


def evidence(
    *,
    chapter: str = "Chapter 14",
    scene: str = "Scene 1",
    quote: str = "The bridge was slick with rain.",
) -> Evidence:
    """Create evidence for export tests."""
    return Evidence(
        chapter=chapter,
        scene=scene,
        quote=quote,
        confidence=1.0,
    )


def build_outputs() -> tuple[CharacterCard, SceneContext, PromptBundle]:
    """Build character, scene, and prompt outputs for export tests."""
    canon_engine = CanonEngine()
    timeline_engine = TimelineEngine()
    character_engine = CharacterEngine(canon_engine, timeline_engine)
    scene_engine = SceneEngine(canon_engine, timeline_engine, character_engine)
    prompt_engine = PromptEngine()

    timeline_engine.register_chapter(TimelineChapter(chapter_index=8, title="Market"))
    timeline_engine.register_chapter(TimelineChapter(chapter_index=14, title="Bridge"))
    timeline_engine.register_scene(
        TimelineScene(position=position(8, 2), title="Blacksmith")
    )
    timeline_engine.register_scene(
        TimelineScene(position=position(14, 1), title="Rain Bridge")
    )
    timeline_engine.record_event(
        TimelineEvent(
            event_id="event_bridge_crossing",
            position=position(14, 1),
            description="Mark crosses the rain bridge.",
        )
    )
    timeline_engine.record_state_change(
        TimelineStateChange(
            change_id="change_mark_weapon_sword",
            subject_id="character_mark",
            attribute="current_weapon",
            value="Iron Sword",
            valid_from=position(8, 2),
        )
    )
    canon_engine.register_entity(
        CanonEntity(
            entity_id="character_mark",
            entity_type=EntityType.CHARACTER,
            display_name="Mark",
        )
    )
    canon_engine.register_entity(
        CanonEntity(
            entity_id="location_rain_bridge",
            entity_type=EntityType.LOCATION,
            display_name="Rain Bridge",
        )
    )
    canon_engine.record_fact(
        entity_id="character_mark",
        attribute="current_weapon",
        value="Iron Sword",
        evidence=evidence(chapter="Chapter 8", scene="Scene 2"),
    )
    canon_engine.record_fact(
        entity_id="location_rain_bridge",
        attribute="weather",
        value="Rain",
        evidence=evidence(),
    )

    scene_context = scene_engine.build_context(
        position=position(14, 1),
        character_ids=("character_mark",),
        environment_entity_ids=("location_rain_bridge",),
    )
    character_card = scene_context.characters[0]
    prompt_bundle = prompt_engine.build_bundle(scene_context)
    return character_card, scene_context, prompt_bundle


def test_character_card_json_is_stable_and_evidence_backed() -> None:
    """Character card JSON includes fact and evidence details."""
    character_card, _scene_context, _prompt_bundle = build_outputs()
    export_engine = ExportEngine()

    exported = json.loads(export_engine.character_card_json(character_card))

    assert exported["character_id"] == "character_mark"
    assert exported["facts"]["current_weapon"]["value"] == "Iron Sword"
    assert exported["facts"]["current_weapon"]["evidence"]["chapter"] == "Chapter 8"


def test_scene_context_json_includes_scene_events_and_environment() -> None:
    """Scene context JSON includes scene, events, and environment data."""
    _character_card, scene_context, _prompt_bundle = build_outputs()
    export_engine = ExportEngine()

    exported = json.loads(export_engine.scene_context_json(scene_context))

    assert exported["scene"]["title"] == "Rain Bridge"
    assert exported["events"][0]["event_id"] == "event_bridge_crossing"
    assert exported["environment"][0]["facts"]["weather"]["value"] == "Rain"


def test_prompt_bundle_json_includes_all_prompt_types() -> None:
    """Prompt bundle JSON includes all V1 prompt fields."""
    _character_card, _scene_context, prompt_bundle = build_outputs()
    export_engine = ExportEngine()

    exported = json.loads(export_engine.prompt_bundle_json(prompt_bundle))

    assert exported["image_prompt"]
    assert exported["narration_prompt"]
    assert exported["camera_prompt"]
    assert exported["animation_prompt"]


def test_json_exports_preserve_unicode_text() -> None:
    """JSON exports preserve repaired Unicode instead of ASCII escaping it."""
    bundle = PromptBundle(
        image_prompt="Show Zhao Chen's fiancée.",
        narration_prompt="Narrate the scene.",
        camera_prompt="Use a medium close-up.",
        animation_prompt="Subtle holographic motion.",
    )

    exported = ExportEngine().prompt_bundle_json(bundle)

    assert "fiancée" in exported
    assert "\\u00e9" not in exported


def test_character_sheet_markdown_exports_character_facts() -> None:
    """Character sheet Markdown includes display name and known facts."""
    character_card, _scene_context, _prompt_bundle = build_outputs()
    export_engine = ExportEngine()

    markdown = export_engine.character_sheet_markdown(character_card)

    assert "# Character Sheet: Mark" in markdown
    assert "- current_weapon: Iron Sword" in markdown
    assert "Evidence: Chapter 8, Scene 2" in markdown


def test_scene_sheet_markdown_exports_scene_context() -> None:
    """Scene sheet Markdown includes characters, environment, and events."""
    _character_card, scene_context, _prompt_bundle = build_outputs()
    export_engine = ExportEngine()

    markdown = export_engine.scene_sheet_markdown(scene_context)

    assert "# Scene Sheet: Rain Bridge" in markdown
    assert "Mark" in markdown
    assert "location_rain_bridge: weather: Rain" in markdown
    assert "Mark crosses the rain bridge." in markdown


def test_prompt_sheet_markdown_exports_prompt_bundle() -> None:
    """Prompt sheet Markdown includes every prompt section."""
    _character_card, _scene_context, prompt_bundle = build_outputs()
    export_engine = ExportEngine()

    markdown = export_engine.prompt_sheet_markdown(prompt_bundle)

    assert "## Image Prompt" in markdown
    assert "## Narration Prompt" in markdown
    assert "## Camera Prompt" in markdown
    assert "## Animation Prompt" in markdown


def test_character_facts_csv_exports_fact_rows() -> None:
    """Character fact CSV includes stable headers and fact values."""
    character_card, _scene_context, _prompt_bundle = build_outputs()
    export_engine = ExportEngine()

    exported = export_engine.character_facts_csv(character_card)
    rows = list(csv.DictReader(io.StringIO(exported)))

    assert rows[0]["character_id"] == "character_mark"
    assert rows[0]["attribute"] == "current_weapon"
    assert rows[0]["value"] == "Iron Sword"


def test_prompt_bundle_csv_exports_prompt_rows() -> None:
    """Prompt bundle CSV includes one row per prompt type."""
    _character_card, _scene_context, prompt_bundle = build_outputs()
    export_engine = ExportEngine()

    exported = export_engine.prompt_bundle_csv(prompt_bundle)
    rows = list(csv.DictReader(io.StringIO(exported)))

    assert [row["prompt_type"] for row in rows] == [
        "image",
        "narration",
        "camera",
        "animation",
    ]


def test_csv_text_rejects_duplicate_headers() -> None:
    """CSV exports require stable, unique headers."""
    with pytest.raises(ValueError, match="fieldnames cannot contain duplicates"):
        ExportEngine._csv_text(
            fieldnames=["attribute", "attribute"],
            rows=[],
        )


def test_csv_text_rejects_missing_row_fields() -> None:
    """CSV rows must match the configured export schema."""
    with pytest.raises(ValueError, match="include every configured field"):
        ExportEngine._csv_text(
            fieldnames=["attribute", "value"],
            rows=[{"attribute": "current_weapon"}],
        )


def test_csv_text_rejects_unexpected_row_fields() -> None:
    """CSV rows cannot silently include fields outside the schema."""
    with pytest.raises(ValueError, match="unexpected fields"):
        ExportEngine._csv_text(
            fieldnames=["attribute"],
            rows=[{"attribute": "current_weapon", "value": "Iron Sword"}],
        )


def test_markdown_list_rejects_blank_values() -> None:
    """Markdown list exports should not emit blank visible rows."""
    with pytest.raises(ValueError, match="cannot be blank"):
        ExportEngine._markdown_list(("Visible", " "))

    with pytest.raises(ValueError, match="cannot be blank"):
        ExportEngine._markdown_list(("Visible", cast(Any, 42)))

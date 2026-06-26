"""Tests for the SceneSmith command line interface."""

import json
import re
import shutil
from pathlib import Path

import pytest
from pytest import CaptureFixture, MonkeyPatch

from scenesmith.cli import main
from scenesmith.importing import StoryImporter
from scenesmith.validation.runner import (
    _extraction_input_digest,
    _extraction_prompt_digest,
    _source_manifest_digest,
    _structure_digest,
)


def source_file() -> Path:
    """Create a small source file for CLI tests."""
    path = Path("build") / "test_cli" / "chapter.txt"
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


def single_scene_source_file() -> Path:
    """Create a one-scene source file for AI JSON CLI tests."""
    path = Path("build") / "test_cli" / "single_scene.txt"
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


def unicode_source_file() -> Path:
    """Create a source file containing multilingual punctuation."""
    path = Path("build") / "test_cli" / "unicode_scene.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Chapter 1",
                "Lin saw 【Entry】 shimmer beside his fiancée.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def two_scene_source_file() -> Path:
    """Create a one-chapter, two-scene source file for scene-position CLI tests."""
    path = Path("build") / "test_cli" / "two_scene.txt"
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


def out_of_order_source_file() -> Path:
    """Create a source file with explicit chapters in the wrong order."""
    path = Path("build") / "test_cli" / "out_of_order.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Chapter 3",
                "Third chapter text.",
                "",
                "Chapter 1",
                "First chapter text.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_cli_help_shows_v1_workflow(capsys: CaptureFixture[str]) -> None:
    """Top-level CLI help should guide a first user through the V1 flow."""
    with pytest.raises(SystemExit) as error:
        main(["--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "SceneSmith V1 proof CLI" in output
    assert "Typical V1 flow:" in output
    assert "scenesmith import chapter_001.txt --source-id my_story" in output
    assert "scenesmith validate --summary-only --snapshot-dir snapshots/run_name" in output


def test_cli_help_describes_current_command_purpose(
    capsys: CaptureFixture[str],
) -> None:
    """Top-level CLI help should describe commands in current V1 terms."""
    with pytest.raises(SystemExit) as error:
        main(["--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Inspect how source text is parsed" in output
    assert "Apply evidence-bounded AI JSON candidates through" in output
    assert "Canon Updating." in output
    assert "Print a canon-backed production prompt pack" in output
    assert "Run the local validation corpus and optional" in output
    assert "deterministic snapshot." in output


def test_import_help_describes_source_arguments(capsys: CaptureFixture[str]) -> None:
    """Import help should explain the source identifiers a user must choose."""
    with pytest.raises(SystemExit) as error:
        main(["import", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Path to a UTF-8 text source file." in output
    assert "Stable machine ID for this imported source." in output
    assert "Human-readable source title" in output


def test_character_help_describes_presentation_and_machine_outputs(
    capsys: CaptureFixture[str],
) -> None:
    """Character help should explain markdown versus JSON and CSV outputs."""
    with pytest.raises(SystemExit) as error:
        main(["character", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Markdown is presentation-first" in output
    assert "JSON/CSV preserve machine detail." in output


def test_scene_help_describes_timeline_safe_arguments(
    capsys: CaptureFixture[str],
) -> None:
    """Scene help should surface timeline-safe scene and extractor options."""
    with pytest.raises(SystemExit) as error:
        main(["scene", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Scene ID to inspect" in output
    assert "Repeat for multiple" in output
    assert "characters." in output
    assert "Evidence-bounded AI JSON response" in output
    assert "Markdown is presentation-first" in output
    assert "preserves machine detail." in output


def test_validate_help_describes_snapshot_and_source_root(
    capsys: CaptureFixture[str],
) -> None:
    """Validate help should make corpus source and snapshot behavior discoverable."""
    with pytest.raises(SystemExit) as error:
        main(["validate", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Directory containing validation case metadata JSON" in output
    assert "files." in output
    assert "Root directory containing local validation chapter" in output
    assert "folders. Overrides SCENESMITH_VALIDATION_ROOT." in output
    assert "List validation cases without importing source files." in output
    assert "deterministic snapshot" in output
    assert "metadata is written." in output
    assert "Text is scan-friendly" in output
    assert "JSON preserves" in output
    assert "machine detail." in output


def test_world_help_describes_presentation_and_machine_outputs(
    capsys: CaptureFixture[str],
) -> None:
    """World help should explain markdown versus JSON outputs."""
    with pytest.raises(SystemExit) as error:
        main(["world", "--help"])
    output = capsys.readouterr().out

    assert error.value.code == 0
    assert "Markdown is presentation-first" in output
    assert "preserves machine detail." in output


def ai_response_file(anchor_id: str) -> Path:
    """Create an evidence-bounded AI JSON response file."""
    path = Path("build") / "test_cli" / "ai_response.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
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
        ),
        encoding="utf-8",
    )
    return path


def multi_scene_ai_response_file() -> Path:
    """Create a multi-scene evidence-bounded AI JSON response file."""
    path = Path("build") / "test_cli" / "multi_scene_ai_response.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "scenes": {
                    "demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_001_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Rusty Dagger",
                    ),
                    "demo_chapter_002_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_002_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Iron Sword",
                    ),
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def scene_position_ai_response_file() -> Path:
    """Create multi-scene AI JSON for scene-position CLI view tests."""
    path = Path("build") / "test_cli" / "scene_position_ai_response.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "scenes": {
                    "demo_chapter_001_scene_001": {
                        "entities": [
                            {
                                "entity_id": "character_mark",
                                "entity_type": "character",
                                "display_name": "Mark",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_001_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                            {
                                "entity_id": "location_hangar",
                                "entity_type": "location",
                                "display_name": "Hangar",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_001_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                        ],
                        "facts": [
                            {
                                "fact_id": "fact_mark_mood_calm",
                                "entity_id": "character_mark",
                                "attribute": "current_mood",
                                "value": "Calm",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_001_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                            {
                                "fact_id": "fact_hangar_condition_quiet",
                                "entity_id": "location_hangar",
                                "attribute": "condition",
                                "value": "Quiet",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_001_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                        ],
                        "relationships": [],
                        "state_changes": [],
                    },
                    "demo_chapter_001_scene_002": {
                        "entities": [
                            {
                                "entity_id": "character_mark",
                                "entity_type": "character",
                                "display_name": "Mark",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_002_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                            {
                                "entity_id": "location_hangar",
                                "entity_type": "location",
                                "display_name": "Hangar",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_002_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                        ],
                        "facts": [
                            {
                                "fact_id": "fact_mark_mood_alarmed",
                                "entity_id": "character_mark",
                                "attribute": "current_mood",
                                "value": "Alarmed",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_002_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                            {
                                "fact_id": "fact_hangar_condition_alarm",
                                "entity_id": "location_hangar",
                                "attribute": "condition",
                                "value": "Alarm active",
                                "evidence_anchor_id": (
                                    "demo_chapter_001_scene_002_paragraph_001_"
                                    "sentence_001_anchor"
                                ),
                                "confidence": 0.95,
                            },
                        ],
                        "relationships": [],
                        "state_changes": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def test_import_command_prints_source_counts(capsys: CaptureFixture[str]) -> None:
    """Import prints stable source structure counts."""
    path = source_file()

    exit_code = main(["import", str(path), "--source-id", "demo", "--title", "Demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"chapters": 2' in output
    assert '"evidence_anchors": 2' in output


def test_cli_reports_missing_file_without_traceback(
    capsys: CaptureFixture[str],
) -> None:
    """CLI reports expected file errors with a nonzero exit code."""
    exit_code = main(["import", "build/test_cli/missing.txt", "--source-id", "demo"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Error: File not found:" in captured.err
    assert "build/test_cli/missing.txt" in captured.err.replace("\\", "/")


def test_import_command_rejects_out_of_order_chapters(
    capsys: CaptureFixture[str],
) -> None:
    """Import reports out-of-order chapters without a traceback."""
    path = out_of_order_source_file()

    exit_code = main(["import", str(path), "--source-id", "demo"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "increasing order" in captured.err


def test_extract_demo_command_prints_candidates(capsys: CaptureFixture[str]) -> None:
    """Demo extraction prints accepted candidate counts."""
    path = source_file()

    exit_code = main(["extract-demo", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"entity_id": "character_mark"' in output
    assert '"accepted_relationships": 2' in output


def test_character_command_prints_character_sheet(capsys: CaptureFixture[str]) -> None:
    """Character command prints a canon-backed character sheet."""
    path = source_file()

    exit_code = main(["character", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# Mark" in output
    assert "## Current Equipment" in output
    assert "- Iron Sword" in output
    assert "## Evidence" in output


def test_scene_command_reports_unknown_scene(
    capsys: CaptureFixture[str],
) -> None:
    """CLI returns a clean error for unknown scene requests."""
    path = source_file()

    exit_code = main(
        [
            "scene",
            str(path),
            "--source-id",
            "demo",
            "--scene-id",
            "missing_scene",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Unknown scene" in captured.err


def test_scene_command_prints_scene_sheet(capsys: CaptureFixture[str]) -> None:
    """Scene command prints a canon-backed scene sheet."""
    path = source_file()

    exit_code = main(["scene", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# Scene 1" in output
    assert "## Characters Present" in output
    assert "- Mark" in output
    assert "## Continuity Changes" in output


def test_scene_command_dedupes_repeated_character_ids(
    capsys: CaptureFixture[str],
) -> None:
    """CLI does not duplicate scene participants from repeated flags."""
    path = source_file()

    exit_code = main(
        [
            "scene",
            str(path),
            "--source-id",
            "demo",
            "--character-id",
            "character_mark",
            "--character-id",
            "character_mark",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Characters Present\n- Mark" in output
    characters_section = output.split("## Characters Present", maxsplit=1)[1].split(
        "## Mood",
        maxsplit=1,
    )[0]
    assert characters_section.count("- Mark") == 1


def test_scene_command_rejects_invalid_character_id(
    capsys: CaptureFixture[str],
) -> None:
    """CLI selected character IDs must be machine-safe."""
    path = source_file()

    exit_code = main(
        [
            "scene",
            str(path),
            "--source-id",
            "demo",
            "--character-id",
            "character mark",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Selected entity ID cannot contain whitespace" in captured.err


def test_prompt_command_prints_prompt_sheet(capsys: CaptureFixture[str]) -> None:
    """Prompt command prints deterministic prompts from scene context."""
    path = source_file()

    exit_code = main(["prompt", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Image Prompt" in output
    assert "Narrate using only accepted canon facts." in output


def test_extraction_prompt_command_prints_anchor_bounded_prompt(
    capsys: CaptureFixture[str],
) -> None:
    """Extraction prompt command prints scene text and allowed anchors."""
    path = single_scene_source_file()

    exit_code = main(["extraction-prompt", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Use only the provided evidence anchors." in output
    assert "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor" in output


def test_extraction_prompt_command_prints_utf8_story_text(
    capsys: CaptureFixture[str],
) -> None:
    """Extraction prompt command preserves UTF-8 story text."""
    path = unicode_source_file()

    exit_code = main(["extraction-prompt", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "【Entry】" in output
    assert "fiancée" in output


def test_extract_ai_json_command_prints_acceptance_summary(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON extraction command applies candidates through Canon Updating."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    output = capsys.readouterr().out
    summary = json.loads(output)

    assert exit_code == 0
    assert summary["accepted_facts"] == 3
    assert summary["accepted_relationships"] == 1
    assert summary["accepted_entity_ids"] == [
        "character_mark",
        "item_iron_sword",
    ]
    assert summary["accepted_relationship_ids"] == [
        "relationship_character_mark_owns_item_iron_sword"
    ]
    assert summary["rejected_candidate_ids"] == []


def test_extract_ai_json_command_can_apply_multi_scene_payloads(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command can apply a scene-keyed response envelope."""
    path = source_file()
    response_path = multi_scene_ai_response_file()

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    output = capsys.readouterr().out
    summary = json.loads(output)

    assert exit_code == 0
    assert [
        result["scene_id"] for result in summary["results"]
    ] == [
        "demo_chapter_001_scene_001",
        "demo_chapter_002_scene_001",
    ]
    assert summary["accepted_facts"] == 3
    assert summary["accepted_entity_ids"] == ["character_mark"]


def test_extract_ai_json_command_can_apply_multi_scene_payload_list(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command can apply a list-form multi-scene response envelope."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "multi_scene_ai_response_list.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": [
                    {
                        "scene_id": "demo_chapter_001_scene_001",
                        **weapon_payload(
                            anchor_id=(
                                "demo_chapter_001_scene_001_paragraph_001_"
                                "sentence_001_anchor"
                            ),
                            weapon="Rusty Dagger",
                        ),
                    },
                    {
                        "scene_id": "demo_chapter_002_scene_001",
                        **weapon_payload(
                            anchor_id=(
                                "demo_chapter_002_scene_001_paragraph_001_"
                                "sentence_001_anchor"
                            ),
                            weapon="Iron Sword",
                        ),
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"scene_id": "demo_chapter_001_scene_001"' in output
    assert '"scene_id": "demo_chapter_002_scene_001"' in output


def test_extract_ai_json_command_rejects_unknown_multi_scene_payload(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects scene payloads outside the imported source."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "unknown_scene_ai_response.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": {
                    "demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_001_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Rusty Dagger",
                    ),
                    "demo_chapter_999_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_001_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Future Sword",
                    ),
                }
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unknown scenes" in captured.err


def test_extract_ai_json_command_rejects_duplicate_list_scene_payloads(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects duplicate scene IDs in list-form envelopes."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "duplicate_scene_ai_response.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": [
                    {
                        "scene_id": "demo_chapter_001_scene_001",
                        **weapon_payload(
                            anchor_id=(
                                "demo_chapter_001_scene_001_paragraph_001_"
                                "sentence_001_anchor"
                            ),
                            weapon="Rusty Dagger",
                        ),
                    },
                    {
                        "scene_id": "demo_chapter_001_scene_001",
                        **weapon_payload(
                            anchor_id=(
                                "demo_chapter_001_scene_001_paragraph_001_"
                                "sentence_001_anchor"
                            ),
                            weapon="Iron Sword",
                        ),
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "duplicate scene" in captured.err


def test_extract_ai_json_command_rejects_extra_multi_scene_envelope_keys(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects unsupported multi-scene envelope fields."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "extra_envelope_ai_response.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": {
                    "demo_chapter_001_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_001_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Rusty Dagger",
                    ),
                    "demo_chapter_002_scene_001": weapon_payload(
                        anchor_id=(
                            "demo_chapter_002_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Iron Sword",
                    ),
                },
                "summary": "unsupported",
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unsupported envelope keys" in captured.err


def test_extract_ai_json_command_rejects_duplicate_multi_scene_keys(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects duplicate JSON object keys in envelopes."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "duplicate_key_ai_response.json"
    response_path.write_text(
        (
            '{"scenes": {"demo_chapter_001_scene_001": '
            '{"entities": [], "facts": [], "relationships": [], "state_changes": []}, '
            '"demo_chapter_001_scene_001": '
            '{"entities": [], "facts": [], "relationships": [], "state_changes": []}}}'
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "duplicate key" in captured.err


def test_extract_ai_json_command_rejects_blank_multi_scene_id(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects blank object-form scene IDs."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "blank_scene_id_ai_response.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": {
                    "": weapon_payload(
                        anchor_id=(
                            "demo_chapter_001_scene_001_paragraph_001_"
                            "sentence_001_anchor"
                        ),
                        weapon="Rusty Dagger",
                    )
                }
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AI multi-scene response scene ID is required" in captured.err


def test_extract_ai_json_command_rejects_whitespace_multi_scene_id(
    capsys: CaptureFixture[str],
) -> None:
    """AI JSON command rejects list-form scene IDs that are not machine-safe."""
    path = source_file()
    response_path = Path("build") / "test_cli" / "whitespace_scene_id_ai_response.json"
    response_path.write_text(
        json.dumps(
            {
                "scenes": [
                    {
                        "scene_id": "demo chapter 001 scene 001",
                        **weapon_payload(
                            anchor_id=(
                                "demo_chapter_001_scene_001_paragraph_001_"
                                "sentence_001_anchor"
                            ),
                            weapon="Rusty Dagger",
                        ),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["extract-ai-json", str(path), str(response_path), "--source-id", "demo"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "AI multi-scene response scene ID cannot contain whitespace" in captured.err


def test_prompt_command_can_use_ai_json_candidates(
    capsys: CaptureFixture[str],
) -> None:
    """Prompt command can use evidence-bounded AI JSON candidates."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "prompt",
            str(path),
            "--source-id",
            "demo",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "character_mark retains current_weapon: Iron Sword" in output


def test_character_command_can_use_ai_json_scene_id(
    capsys: CaptureFixture[str],
) -> None:
    """Character command can apply scene-specific AI JSON candidates."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "character",
            str(path),
            "--source-id",
            "demo",
            "--character-id",
            "character_mark",
            "--scene-id",
            "demo_chapter_001_scene_001",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Current Equipment" in output
    assert "- Iron Sword" in output


def test_character_command_uses_scene_id_for_final_view(
    capsys: CaptureFixture[str],
) -> None:
    """Character command scene ID controls the reconstructed card position."""
    path = two_scene_source_file()
    response_path = scene_position_ai_response_file()

    first_exit_code = main(
        [
            "character",
            str(path),
            "--source-id",
            "demo",
            "--character-id",
            "character_mark",
            "--scene-id",
            "demo_chapter_001_scene_001",
            "--ai-response-file",
            str(response_path),
        ]
    )
    first_output = capsys.readouterr().out
    second_exit_code = main(
        [
            "character",
            str(path),
            "--source-id",
            "demo",
            "--character-id",
            "character_mark",
            "--scene-id",
            "demo_chapter_001_scene_002",
            "--ai-response-file",
            str(response_path),
        ]
    )
    second_output = capsys.readouterr().out

    assert first_exit_code == 0
    assert second_exit_code == 0
    assert "current_mood -> Calm" in first_output
    assert "current_mood -> Alarmed" in second_output


def test_world_command_can_use_ai_json_candidates(
    capsys: CaptureFixture[str],
) -> None:
    """World command prints a presented world sheet from accepted candidates."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "world",
            str(path),
            "--source-id",
            "demo",
            "--entity-id",
            "item_iron_sword",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# World Sheet" in output
    assert "Iron Sword (item)" in output


def test_world_command_can_print_json(capsys: CaptureFixture[str]) -> None:
    """World command can print machine-readable world state JSON."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "world",
            str(path),
            "--source-id",
            "demo",
            "--entity-id",
            "item_iron_sword",
            "--ai-response-file",
            str(response_path),
            "--format",
            "json",
        ]
    )
    output = capsys.readouterr().out
    exported = json.loads(output)

    assert exit_code == 0
    assert exported["entities"][0]["entity_id"] == "item_iron_sword"
    assert exported["entities"][0]["facts"][0]["evidence"]["quote"] == (
        "Mark bought an iron sword."
    )


def test_world_command_uses_scene_id_for_final_view(
    capsys: CaptureFixture[str],
) -> None:
    """World command scene ID controls the reconstructed world position."""
    path = two_scene_source_file()
    response_path = scene_position_ai_response_file()

    first_exit_code = main(
        [
            "world",
            str(path),
            "--source-id",
            "demo",
            "--entity-id",
            "location_hangar",
            "--scene-id",
            "demo_chapter_001_scene_001",
            "--ai-response-file",
            str(response_path),
        ]
    )
    first_output = capsys.readouterr().out
    second_exit_code = main(
        [
            "world",
            str(path),
            "--source-id",
            "demo",
            "--entity-id",
            "location_hangar",
            "--scene-id",
            "demo_chapter_001_scene_002",
            "--ai-response-file",
            str(response_path),
        ]
    )
    second_output = capsys.readouterr().out

    assert first_exit_code == 0
    assert second_exit_code == 0
    assert "condition: Quiet" in first_output
    assert "condition: Alarm active" in second_output


def test_world_command_dedupes_repeated_entity_ids(
    capsys: CaptureFixture[str],
) -> None:
    """CLI world command dedupes repeated selected entities."""
    path = single_scene_source_file()
    response_path = ai_response_file(
        "demo_chapter_001_scene_001_paragraph_001_sentence_001_anchor"
    )

    exit_code = main(
        [
            "world",
            str(path),
            "--source-id",
            "demo",
            "--entity-id",
            "item_iron_sword",
            "--entity-id",
            "item_iron_sword",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output.count("Iron Sword (item)") == 1


def test_continuity_command_prints_report(capsys: CaptureFixture[str]) -> None:
    """Continuity command prints a human-readable continuity report."""
    path = source_file()

    exit_code = main(["continuity", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# Continuity Report: demo" in output
    assert "### New" in output
    assert "### Still Known" in output


def test_continuity_command_can_print_json(capsys: CaptureFixture[str]) -> None:
    """Continuity command can print machine-readable report JSON."""
    path = source_file()

    exit_code = main(
        ["continuity", str(path), "--source-id", "demo", "--format", "json"]
    )
    output = capsys.readouterr().out
    exported = json.loads(output)

    assert exit_code == 0
    assert exported["source_id"] == "demo"
    assert exported["scenes"]


def test_continuity_command_can_use_multi_scene_ai_payloads(
    capsys: CaptureFixture[str],
) -> None:
    """Continuity command can report changes from a multi-scene AI envelope."""
    path = source_file()
    response_path = multi_scene_ai_response_file()

    exit_code = main(
        [
            "continuity",
            str(path),
            "--source-id",
            "demo",
            "--ai-response-file",
            str(response_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "character_mark current_weapon = Iron Sword" in output
    assert "character_mark current_weapon = Rusty Dagger" in output


def test_validate_command_runs_local_validation_suite(capsys: CaptureFixture[str]) -> None:
    """Validate command runs local corpus metadata against local chapter files."""
    source_root = Path("build") / "test_cli_validate" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Demo - Demo" in output
    assert "PASS" in output
    assert "files=2 chapters=2 scenes=2 paragraphs=2 sentences=2 anchors=2" in output
    assert "extraction_inputs=2 extraction_anchors=2" in output
    assert (
        "cases=1 passed=1 failed=0 files=2 chapters=2 scenes=2 "
        "paragraphs=2 sentences=2 anchors=2 extraction_inputs=2 "
        "extraction_anchors=2"
    ) in output
    assert "Validation Digest" in output
    assert "100%" in output


def test_validate_command_uses_environment_source_root(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Validate command uses SCENESMITH_VALIDATION_ROOT when no source root is passed."""
    source_root = Path("build") / "test_cli_validate_env" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_env" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SCENESMITH_VALIDATION_ROOT", str(source_root))

    exit_code = main(["validate", "--case-dir", str(case_dir)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Demo - Demo" in output
    assert "cases=1 passed=1 failed=0" in output


def test_validate_source_root_argument_overrides_environment(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Validate --source-root has priority over SCENESMITH_VALIDATION_ROOT."""
    source_root = Path("build") / "test_cli_validate_arg_over_env" / "sources"
    source_dir = source_root / "Demo Genre"
    env_root = Path("build") / "test_cli_validate_arg_over_env" / "wrong_sources"
    case_dir = Path("build") / "test_cli_validate_arg_over_env" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    env_root.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SCENESMITH_VALIDATION_ROOT", str(env_root))

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Demo - Demo" in output
    assert "cases=1 passed=1 failed=0" in output


def test_validate_rejects_blank_environment_source_root(
    capsys: CaptureFixture[str],
    monkeypatch: MonkeyPatch,
) -> None:
    """Validate command reports blank SCENESMITH_VALIDATION_ROOT clearly."""
    case_dir = Path("build") / "test_cli_validate_blank_env" / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    monkeypatch.setenv("SCENESMITH_VALIDATION_ROOT", "   ")

    exit_code = main(["validate", "--case-dir", str(case_dir)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "SCENESMITH_VALIDATION_ROOT cannot be blank." in captured.err


def test_validate_command_can_print_summary_only(capsys: CaptureFixture[str]) -> None:
    """Validate command can suppress per-case text for quick corpus checks."""
    source_root = Path("build") / "test_cli_validate_summary" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_summary" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--summary-only",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Validation Summary" in output
    assert "Validation Totals" in output
    assert "Validation Digest" in output
    assert "Validation Score" in output
    assert "Demo - Demo" not in output
    assert "PASS" not in output
    assert (
        "cases=1 passed=1 failed=0 files=2 chapters=2 scenes=2 "
        "paragraphs=2 sentences=2 anchors=2 extraction_inputs=2 "
        "extraction_anchors=2"
    ) in output


def test_validate_command_can_print_json(capsys: CaptureFixture[str]) -> None:
    """Validate command can print machine-readable validation results."""
    source_root = Path("build") / "test_cli_validate_json" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_json" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--format",
            "json",
        ]
    )
    output = capsys.readouterr().out
    exported = json.loads(output)

    assert exit_code == 0
    assert exported["passed"] is True
    assert exported["score"] == 100
    assert re.fullmatch(r"[0-9a-f]{64}", exported["suite_digest"])
    assert exported["totals"]["cases"] == 1
    assert exported["totals"]["chapter_files"] == 2
    assert exported["totals"]["evidence_anchors"] == 2
    assert exported["totals"]["extraction_inputs"] == 2
    assert exported["totals"]["extraction_anchors"] == 2
    assert exported["results"][0]["actual_import"]["chapter_files"] == 2
    assert exported["results"][0]["actual_import"]["sentences"] == 2
    assert exported["results"][0]["actual_extraction"]["scene_inputs"] == 2
    assert re.fullmatch(
        r"[0-9a-f]{64}",
        exported["results"][0]["actual_extraction"]["extraction_prompt_digest"],
    )
    assert "Mark found a brass key." not in output
    assert "Mark opened the archive." not in output
    assert "Scene Text:" not in output
    assert "Evidence Anchors:" not in output


def test_validate_command_can_write_snapshot(capsys: CaptureFixture[str]) -> None:
    """Validate command can write deterministic snapshot metadata."""
    source_root = Path("build") / "test_cli_validate_snapshot" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_snapshot" / "cases"
    snapshot_dir = Path("build") / "test_cli_validate_snapshot" / "snapshot"
    shutil.rmtree(snapshot_dir, ignore_errors=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--snapshot-dir",
            str(snapshot_dir),
            "--summary-only",
        ]
    )
    output = capsys.readouterr().out
    snapshot = json.loads(
        (snapshot_dir / "validation_result.json").read_text(encoding="utf-8")
    )
    readme = (snapshot_dir / "README.md").read_text(encoding="utf-8")

    assert exit_code == 0
    assert "Validation Summary" in output
    assert snapshot["passed"] is True
    assert snapshot["totals"]["cases"] == 1
    assert "Mark found a brass key." not in json.dumps(snapshot, ensure_ascii=False)
    assert "Mark opened the archive." not in json.dumps(snapshot, ensure_ascii=False)
    assert "does not store chapter text" in readme
    assert "Mark found a brass key." not in readme
    assert "Mark opened the archive." not in readme
    assert "Scene Text:" not in readme
    assert "Evidence Anchors:" not in readme


def test_validate_snapshot_json_matches_cli_json(capsys: CaptureFixture[str]) -> None:
    """Validation snapshot JSON should match validate --format json output."""
    source_root = Path("build") / "test_cli_validate_snapshot_json" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_snapshot_json" / "cases"
    snapshot_dir = Path("build") / "test_cli_validate_snapshot_json" / "snapshot"
    shutil.rmtree(snapshot_dir, ignore_errors=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--format",
            "json",
            "--snapshot-dir",
            str(snapshot_dir),
        ]
    )
    output = capsys.readouterr().out
    snapshot_output = (snapshot_dir / "validation_result.json").read_text(
        encoding="utf-8"
    )

    assert exit_code == 0
    assert snapshot_output == output


def test_validate_snapshot_rejects_nonempty_directory(
    capsys: CaptureFixture[str],
) -> None:
    """Validate snapshots refuse to overwrite existing reference files."""
    source_root = Path("build") / "test_cli_validate_snapshot_reject" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_snapshot_reject" / "cases"
    snapshot_dir = Path("build") / "test_cli_validate_snapshot_reject" / "snapshot"
    shutil.rmtree(snapshot_dir, ignore_errors=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (snapshot_dir / "existing.txt").write_text("keep me", encoding="utf-8")
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--snapshot-dir",
            str(snapshot_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Validation snapshot directory must be empty or absent" in captured.err
    assert (snapshot_dir / "existing.txt").read_text(encoding="utf-8") == "keep me"


def test_validate_snapshot_rejects_file_path(capsys: CaptureFixture[str]) -> None:
    """Validate snapshots require a directory path."""
    source_root = Path("build") / "test_cli_validate_snapshot_file" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_snapshot_file" / "cases"
    snapshot_path = Path("build") / "test_cli_validate_snapshot_file" / "snapshot.txt"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    snapshot_path.write_text("not a directory", encoding="utf-8")
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--snapshot-dir",
            str(snapshot_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Validation snapshot path must be a directory" in captured.err
    assert snapshot_path.read_text(encoding="utf-8") == "not a directory"


def test_validate_command_can_filter_by_case_id(capsys: CaptureFixture[str]) -> None:
    """Validate command can run a selected validation case."""
    source_root = Path("build") / "test_cli_validate_filter" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_filter" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--case-id",
            "demo_validation_case",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Demo - Demo" in output
    assert "cases=1 passed=1 failed=0" in output
    assert "extraction_inputs=2 extraction_anchors=2" in output


def test_validate_command_can_list_cases(capsys: CaptureFixture[str]) -> None:
    """Validate command can list cases without running imports."""
    case_dir = Path("build") / "test_cli_validate_list" / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    source_dir = Path("build") / "test_cli_validate_list" / "sources" / "Demo Genre"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            "build/test_cli_validate_list/missing_sources",
            "--list-cases",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Validation Cases" in output
    assert "demo_validation_case" in output
    assert "PASS" not in output


def test_validate_command_can_list_cases_as_json(capsys: CaptureFixture[str]) -> None:
    """Validate list-cases command can print machine-readable case metadata."""
    case_dir = Path("build") / "test_cli_validate_list_json" / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    source_dir = Path("build") / "test_cli_validate_list_json" / "sources" / "Demo Genre"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": _cli_validation_expected_import(source_dir),
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            "build/test_cli_validate_list_json/missing_sources",
            "--list-cases",
            "--format",
            "json",
        ]
    )
    output = capsys.readouterr().out
    exported = json.loads(output)

    assert exit_code == 0
    assert exported["cases"][0]["case_id"] == "demo_validation_case"
    assert exported["cases"][0]["genre"] == "Demo"


def test_validate_list_cases_rejects_snapshot_dir(capsys: CaptureFixture[str]) -> None:
    """Validate list-cases cannot silently ignore snapshot requests."""
    case_dir = Path("build") / "test_cli_validate_list_snapshot" / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--list-cases",
            "--snapshot-dir",
            "build/test_cli_validate_list_snapshot/snapshot",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "snapshots cannot be written when listing cases" in captured.err


def test_validate_json_command_fails_nonzero_on_validation_failure(
    capsys: CaptureFixture[str],
) -> None:
    """Validate JSON command reports failures with a nonzero exit code."""
    source_root = Path("build") / "test_cli_validate_json_failure" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_json_failure" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    expected_import = _cli_validation_expected_import(source_dir)
    expected_import["evidence_anchors"] = 999
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": expected_import,
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    exported = json.loads(captured.out)

    assert exit_code == 1
    assert exported["passed"] is False
    assert exported["score"] == 0
    assert "Validation suite failed." in captured.err
    assert exported["results"][0]["errors"] == [
        "import.evidence_anchors: expected 999, got 2"
    ]


def test_validate_text_command_fails_nonzero_on_validation_failure(
    capsys: CaptureFixture[str],
) -> None:
    """Validate text command reports case errors with a nonzero exit code."""
    source_root = Path("build") / "test_cli_validate_text_failure" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_cli_validate_text_failure" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    expected_import = _cli_validation_expected_import(source_dir)
    expected_import["evidence_anchors"] = 999
    (case_dir / "demo_validation_case.json").write_text(
        json.dumps(
            {
                "case_id": "demo_validation_case",
                "title": "Demo",
                "genre": "Demo",
                "source_directory": "Demo Genre",
                "chapter_glob": "*.txt",
                "expected_import": expected_import,
                "expected_extraction": _cli_validation_expected_extraction(source_dir),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--case-dir",
            str(case_dir),
            "--source-root",
            str(source_root),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Demo - Demo" in captured.out
    assert "FAIL" in captured.out
    assert "import.evidence_anchors: expected 999, got 2" in captured.out
    assert "cases=1 passed=0 failed=1" in captured.out
    assert "Validation suite failed." in captured.err


def _cli_validation_expected_import(source_dir: Path) -> dict[str, int | str]:
    """Return expected import metrics for the CLI validation fixture."""
    chapter_files = tuple(sorted(source_dir.glob("*.txt")))
    imported = StoryImporter().import_text(
        source_id="demo_validation_case",
        title="Demo",
        text="\n\n".join(
            (
                "Chapter 1\nMark found a brass key.",
                "Chapter 2\nMark opened the archive.",
            )
        ),
    )
    return {
        "chapter_files": 2,
        "source_manifest_digest": _source_manifest_digest(chapter_files),
        "chapters": len(imported.story.chapters),
        "scenes": sum(len(chapter.scenes) for chapter in imported.story.chapters),
        "paragraphs": len(imported.paragraphs),
        "sentences": sum(len(paragraph.sentences) for paragraph in imported.paragraphs),
        "evidence_anchors": len(imported.anchors),
        "import_digest": _structure_digest(imported),
    }


def _cli_validation_expected_extraction(source_dir: Path) -> dict[str, int | str]:
    """Return expected extraction-readiness metrics for the CLI validation fixture."""
    imported = StoryImporter().import_text(
        source_id="demo_validation_case",
        title="Demo",
        text="\n\n".join(
            (
                "Chapter 1\nMark found a brass key.",
                "Chapter 2\nMark opened the archive.",
            )
        ),
    )
    return {
        "scene_inputs": sum(len(chapter.scenes) for chapter in imported.story.chapters),
        "evidence_anchors": len(imported.anchors),
        "extraction_input_digest": _extraction_input_digest(imported),
        "extraction_prompt_digest": _extraction_prompt_digest(imported),
    }


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

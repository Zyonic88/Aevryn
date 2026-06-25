"""Tests for the SceneSmith command line interface."""

import json
from pathlib import Path

from pytest import CaptureFixture

from scenesmith.cli import main


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
    assert "Error:" in captured.err


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
    assert "# Character Sheet: Mark" in output
    assert "Evidence: Mark bought an iron sword." in output


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
    assert "# Scene Sheet: Scene 1" in output
    assert "character_mark owns item_iron_sword" in output


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
    assert "## Characters\nMark\n\n## Facts" in output


def test_prompt_command_prints_prompt_sheet(capsys: CaptureFixture[str]) -> None:
    """Prompt command prints deterministic prompts from scene context."""
    path = source_file()

    exit_code = main(["prompt", str(path), "--source-id", "demo"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# Prompt Sheet" in output
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

    assert exit_code == 0
    assert '"accepted_facts": 3' in output
    assert '"accepted_relationships": 1' in output


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

    assert exit_code == 0
    assert '"scene_id": "demo_chapter_001_scene_001"' in output
    assert '"scene_id": "demo_chapter_002_scene_001"' in output
    assert '"accepted_facts": 4' in output


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
    assert "current_weapon: Iron Sword" in output


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

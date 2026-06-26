"""Command line interface for SceneSmith proof workflows."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from scenesmith.export import ExportEngine
from scenesmith.extraction import EvidenceBoundedAIExtractor, StaticAIExtractionClient
from scenesmith.json_utils import loads_json_without_duplicate_keys
from scenesmith.presentation import PresentationEngine
from scenesmith.projects import ProjectRunResult, SceneSmithProjectRunner
from scenesmith.validation import (
    ExpectedExtractionMetrics,
    ExpectedImportMetrics,
    ValidationCase,
    ValidationRunner,
    ValidationSuiteResult,
    ValidationTotals,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the SceneSmith command line interface.

    Parameters:
        argv: Optional command arguments. When omitted, process arguments are used.

    Returns:
        Process exit code.
    """
    _configure_utf8_stdio()
    parser = _build_parser()
    args = parser.parse_args(argv)
    command = cast(str, args.command)

    try:
        if command == "import":
            _handle_import(args)
            return 0
        if command == "extract-demo":
            _handle_extract_demo(args)
            return 0
        if command == "extraction-prompt":
            _handle_extraction_prompt(args)
            return 0
        if command == "extract-ai-json":
            _handle_extract_ai_json(args)
            return 0
        if command == "character":
            _handle_character(args)
            return 0
        if command == "scene":
            _handle_scene(args)
            return 0
        if command == "prompt":
            _handle_prompt(args)
            return 0
        if command == "world":
            _handle_world(args)
            return 0
        if command == "continuity":
            _handle_continuity(args)
            return 0
        if command == "validate":
            _handle_validate(args)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {command}")
    return 2


def _configure_utf8_stdio() -> None:
    """Prefer UTF-8 CLI streams for multilingual story text."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="scenesmith",
        description=(
            "SceneSmith V1 proof CLI for importing story text, applying "
            "evidence-bounded extraction, and inspecting canon-backed outputs."
        ),
        epilog=(
            "Typical V1 flow:\n"
            "  scenesmith import chapter_001.txt --source-id my_story\n"
            "  scenesmith extraction-prompt chapter_001.txt --source-id my_story\n"
            "  scenesmith extract-ai-json chapter_001.txt ai_response.json --source-id my_story\n"
            "  scenesmith character chapter_001.txt --source-id my_story "
            "--ai-response-file ai_response.json --character-id character_mark\n"
            "  scenesmith scene chapter_001.txt --source-id my_story "
            "--ai-response-file ai_response.json\n"
            "  scenesmith prompt chapter_001.txt --source-id my_story "
            "--ai-response-file ai_response.json\n"
            "  scenesmith continuity chapter_001.txt --source-id my_story "
            "--ai-response-file ai_response.json\n\n"
            "Validation:\n"
            "  scenesmith validate --summary-only\n"
            "  scenesmith validate --list-cases\n"
            "  scenesmith validate --summary-only --snapshot-dir snapshots/run_name"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    import_parser = subcommands.add_parser(
        "import",
        help="Inspect how source text is parsed into chapters, scenes, and evidence.",
    )
    _add_source_arguments(import_parser)

    extract_parser = subcommands.add_parser(
        "extract-demo",
        help="Run the deterministic demo extractor for tests and examples.",
    )
    _add_source_arguments(extract_parser)

    extraction_prompt_parser = subcommands.add_parser(
        "extraction-prompt",
        help="Print the evidence-bounded AI extraction prompt for one scene.",
    )
    _add_source_arguments(extraction_prompt_parser)
    extraction_prompt_parser.add_argument("--scene-id", default=None)

    extract_ai_parser = subcommands.add_parser(
        "extract-ai-json",
        help="Apply evidence-bounded AI JSON candidates through Canon Updating.",
    )
    _add_source_arguments(extract_ai_parser)
    extract_ai_parser.add_argument("response_path", help="Path to AI JSON response text.")
    extract_ai_parser.add_argument("--scene-id", default=None)

    character_parser = subcommands.add_parser(
        "character",
        help="Print a canon-backed character sheet.",
    )
    _add_source_arguments(character_parser)
    character_parser.add_argument("--character-id", default="character_mark")
    character_parser.add_argument("--chapter-index", type=int, default=None)
    character_parser.add_argument("--scene-id", default=None)
    character_parser.add_argument("--ai-response-file", default=None)
    character_parser.add_argument(
        "--format",
        choices=("markdown", "json", "csv"),
        default="markdown",
    )

    scene_parser = subcommands.add_parser(
        "scene",
        help="Print a timeline-aware scene sheet.",
    )
    _add_source_arguments(scene_parser)
    scene_parser.add_argument("--scene-id", default=None)
    scene_parser.add_argument("--character-id", action="append", default=None)
    scene_parser.add_argument("--ai-response-file", default=None)
    scene_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    prompt_parser = subcommands.add_parser(
        "prompt",
        help="Print a canon-backed production prompt pack.",
    )
    _add_source_arguments(prompt_parser)
    prompt_parser.add_argument("--scene-id", default=None)
    prompt_parser.add_argument("--character-id", action="append", default=None)
    prompt_parser.add_argument("--ai-response-file", default=None)
    prompt_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    world_parser = subcommands.add_parser(
        "world",
        help="Print a canon-backed world sheet for selected non-character entities.",
    )
    _add_source_arguments(world_parser)
    world_parser.add_argument("--entity-id", action="append", required=True)
    world_parser.add_argument("--chapter-index", type=int, default=None)
    world_parser.add_argument("--scene-id", default=None)
    world_parser.add_argument("--ai-response-file", default=None)

    continuity_parser = subcommands.add_parser(
        "continuity",
        help="Print what changed, stayed known, and was invalidated.",
    )
    _add_source_arguments(continuity_parser)
    continuity_parser.add_argument("--ai-response-file", default=None)
    continuity_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    validate_parser = subcommands.add_parser(
        "validate",
        help="Run the local validation corpus and optional deterministic snapshot.",
    )
    validate_parser.add_argument("--case-dir", default="validation/cases")
    validate_parser.add_argument("--source-root", default=None)
    validate_parser.add_argument("--case-id", action="append", default=None)
    validate_parser.add_argument("--list-cases", action="store_true")
    validate_parser.add_argument("--summary-only", action="store_true")
    validate_parser.add_argument("--snapshot-dir", default=None)
    validate_parser.add_argument("--format", choices=("text", "json"), default="text")

    return parser


def _add_source_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common source import arguments to a subcommand."""
    parser.add_argument("path", help="Path to a UTF-8 text source file.")
    parser.add_argument("--source-id", default="source_demo")
    parser.add_argument("--title", default=None)


def _handle_import(args: argparse.Namespace) -> None:
    """Handle the import command."""
    imported_source = _runner().import_text_file(
        path=Path(cast(str, args.path)),
        source_id=cast(str, args.source_id),
        title=cast(str | None, args.title),
    )
    scene_count = sum(len(chapter.scenes) for chapter in imported_source.story.chapters)
    print(
        json.dumps(
            {
                "source_id": imported_source.source_id,
                "title": imported_source.title,
                "chapters": len(imported_source.story.chapters),
                "scenes": scene_count,
                "paragraphs": len(imported_source.paragraphs),
                "evidence_anchors": len(imported_source.anchors),
            },
            indent=2,
            sort_keys=True,
        )
    )


def _handle_extract_demo(args: argparse.Namespace) -> None:
    """Handle the extract-demo command."""
    result = _runner().run_demo_text_file(
        path=Path(cast(str, args.path)),
        source_id=cast(str, args.source_id),
        title=cast(str | None, args.title),
    )
    print(
        json.dumps(
            {
                "results": [
                    {
                        "scene_id": extraction.scene_id,
                        "entities": [
                            {
                                "entity_id": entity.entity_id,
                                "entity_type": entity.entity_type,
                                "display_name": entity.display_name,
                                "confidence": entity.confidence,
                            }
                            for entity in extraction.entities
                        ],
                        "relationships": [
                            {
                                "source_entity_id": relationship.source_entity_id,
                                "relationship_type": relationship.relationship_type,
                                "target_entity_id": relationship.target_entity_id,
                                "confidence": relationship.confidence,
                            }
                            for relationship in extraction.relationships
                        ],
                    }
                    for extraction in result.extraction_results
                ],
                "accepted_entities": sum(
                    len(summary.accepted_entities) for summary in result.update_summaries
                ),
                "accepted_relationships": sum(
                    len(summary.accepted_relationships)
                    for summary in result.update_summaries
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


def _handle_extraction_prompt(args: argparse.Namespace) -> None:
    """Handle the extraction-prompt command."""
    runner = _runner()
    imported_source = runner.import_text_file(
        path=Path(cast(str, args.path)),
        source_id=cast(str, args.source_id),
        title=cast(str | None, args.title),
    )
    extraction_input = runner.build_scene_extraction_input(
        imported_source=imported_source,
        scene_id=cast(str | None, args.scene_id),
    )
    print(
        EvidenceBoundedAIExtractor(
            client=StaticAIExtractionClient("{}")
        ).build_prompt(extraction_input)
    )


def _handle_extract_ai_json(args: argparse.Namespace) -> None:
    """Handle the extract-ai-json command."""
    result = _run_ai_json(args)
    print(
        json.dumps(
            {
                "results": [
                    {
                        "scene_id": extraction.scene_id,
                        "entities": len(extraction.entities),
                        "facts": len(extraction.facts),
                        "relationships": len(extraction.relationships),
                        "state_changes": len(extraction.state_changes),
                    }
                    for extraction in result.extraction_results
                ],
                "accepted_entities": sum(
                    len(summary.accepted_entities) for summary in result.update_summaries
                ),
                "accepted_facts": sum(
                    len(summary.accepted_facts) for summary in result.update_summaries
                ),
                "accepted_relationships": sum(
                    len(summary.accepted_relationships)
                    for summary in result.update_summaries
                ),
                "accepted_state_changes": sum(
                    len(summary.accepted_state_changes)
                    for summary in result.update_summaries
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


def _handle_character(args: argparse.Namespace) -> None:
    """Handle the character command."""
    runner = _runner()
    result = _run_with_selected_extractor(args)
    character_id = cast(str, args.character_id)
    scene_id = cast(str | None, args.scene_id)
    if scene_id is not None:
        card = runner.build_character_card_at_scene(
            result=result,
            character_id=character_id,
            scene_id=scene_id,
        )
    else:
        card = runner.build_character_card(
            result=result,
            character_id=character_id,
            chapter_index=cast(int | None, args.chapter_index),
        )
    exporter = ExportEngine()
    output_format = cast(str, args.format)
    if output_format == "json":
        print(exporter.canon_character_card_json(card))
    elif output_format == "csv":
        print(exporter.canon_character_facts_csv(card), end="")
    else:
        print(exporter.canon_character_sheet_markdown(card))


def _handle_scene(args: argparse.Namespace) -> None:
    """Handle the scene command."""
    runner = _runner()
    result = _run_with_selected_extractor(args)
    context = runner.build_scene_context(
        result=result,
        scene_id=cast(str | None, args.scene_id),
        character_ids=_character_ids(args),
    )
    exporter = ExportEngine()
    output_format = cast(str, args.format)
    if output_format == "json":
        print(exporter.canon_scene_context_json(context))
    else:
        print(exporter.canon_scene_sheet_markdown(context))


def _handle_prompt(args: argparse.Namespace) -> None:
    """Handle the prompt command."""
    runner = _runner()
    result = _run_with_selected_extractor(args)
    bundle = runner.build_prompt_bundle(
        result=result,
        scene_id=cast(str | None, args.scene_id),
        character_ids=_character_ids(args),
    )
    exporter = ExportEngine()
    output_format = cast(str, args.format)
    if output_format == "json":
        print(exporter.prompt_bundle_json(bundle))
    else:
        print(exporter.prompt_sheet_markdown(bundle))


def _handle_world(args: argparse.Namespace) -> None:
    """Handle the world command."""
    runner = _runner()
    result = _run_with_selected_extractor(args)
    scene_id = cast(str | None, args.scene_id)
    if scene_id is not None:
        state = runner.build_world_state_at_scene(
            result=result,
            entity_ids=_dedupe_ids(cast(list[str], args.entity_id)),
            scene_id=scene_id,
        )
    else:
        state = runner.build_world_state(
            result=result,
            entity_ids=_dedupe_ids(cast(list[str], args.entity_id)),
            chapter_index=cast(int | None, args.chapter_index),
        )
    view = PresentationEngine().world_sheet(state)
    print(ExportEngine().world_sheet_view_markdown(view))


def _handle_continuity(args: argparse.Namespace) -> None:
    """Handle the continuity command."""
    runner = _runner()
    result = _run_with_selected_extractor(args)
    report = runner.build_continuity_report(result)
    exporter = ExportEngine()
    output_format = cast(str, args.format)
    if output_format == "json":
        print(exporter.continuity_report_json(report))
    else:
        print(exporter.continuity_report_markdown(report))


def _handle_validate(args: argparse.Namespace) -> None:
    """Handle the validate command."""
    source_root = _validation_source_root(cast(str | None, args.source_root))
    runner = ValidationRunner(
        case_dir=Path(cast(str, args.case_dir)),
        source_root=source_root,
        case_ids=tuple(cast(list[str] | None, args.case_id) or ()),
    )

    output_format = cast(str, args.format)
    snapshot_dir = cast(str | None, args.snapshot_dir)
    if cast(bool, args.list_cases) and snapshot_dir is not None:
        raise ValueError("Validation snapshots cannot be written when listing cases.")
    if cast(bool, args.list_cases):
        _print_validation_cases(runner.list_cases(), output_format)
        return

    result = runner.run()
    if snapshot_dir is not None:
        _write_validation_snapshot(result=result, snapshot_dir=Path(snapshot_dir))

    if output_format == "json":
        print(_validation_result_json_text(result))
        if not result.passed:
            raise ValueError("Validation suite failed.")
        return

    if cast(bool, args.summary_only):
        print("Validation Summary")
        print()
    else:
        print("Running Validation Suite...")
        print()
        for case_result in result.results:
            status = "PASS" if case_result.passed else "FAIL"
            print(f"{case_result.genre} - {case_result.title}")
            print(status)
            if case_result.actual_import is not None:
                print(_validation_metrics_line(case_result.actual_import))
            if case_result.actual_extraction is not None:
                print(_validation_extraction_line(case_result.actual_extraction))
            for error in case_result.errors:
                print(f"  {error}")
            print()

    print("---------------------------------")
    print("Validation Totals")
    print(_validation_totals_line(result.totals))
    print()
    print("Validation Digest")
    print(result.suite_digest)
    print()
    print("Validation Score")
    print(f"{result.score}%")
    if not result.passed:
        raise ValueError("Validation suite failed.")


def _print_validation_cases(cases: tuple[ValidationCase, ...], output_format: str) -> None:
    """Print validation case metadata."""
    if output_format == "json":
        print(
            json.dumps(
                {
                    "cases": [
                        {
                            "case_id": case.case_id,
                            "title": case.title,
                            "genre": case.genre,
                            "source_directory": case.source_directory,
                            "chapter_glob": case.chapter_glob,
                        }
                        for case in cases
                    ]
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return

    print("Validation Cases")
    print()
    for case in cases:
        print(f"{case.case_id}")
        print(f"  genre={case.genre}")
        print(f"  title={case.title}")
        print(f"  source={case.source_directory}")
        print()


def _write_validation_snapshot(result: ValidationSuiteResult, snapshot_dir: Path) -> None:
    """Write deterministic validation snapshot files."""
    if snapshot_dir.exists() and not snapshot_dir.is_dir():
        raise ValueError(
            f"Validation snapshot path must be a directory: {snapshot_dir}"
        )
    if snapshot_dir.exists() and any(snapshot_dir.iterdir()):
        raise ValueError(
            f"Validation snapshot directory must be empty or absent: {snapshot_dir}"
        )

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "validation_result.json").write_text(
        _validation_result_json_text(result) + "\n",
        encoding="utf-8",
    )
    (snapshot_dir / "README.md").write_text(
        "\n".join(
            (
                "# SceneSmith Validation Snapshot",
                "",
                "This snapshot stores deterministic validation metadata only.",
                "",
                "It does not store chapter text or extraction prompt bodies.",
                "",
                "## Result",
                "",
                f"* Passed: {result.passed}",
                f"* Score: {result.score}%",
                f"* Digest: `{result.suite_digest}`",
                "",
                "## Totals",
                "",
                f"`{_validation_totals_line(result.totals)}`",
                "",
            )
        ),
        encoding="utf-8",
    )


def _validation_result_json_text(result: ValidationSuiteResult) -> str:
    """Return deterministic validation result JSON text."""
    return json.dumps(
        _validation_result_json(result),
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )


def _validation_result_json(result: ValidationSuiteResult) -> dict[str, Any]:
    """Return validation result data for JSON output and snapshots."""
    return {
        "passed": result.passed,
        "score": result.score,
        "suite_digest": result.suite_digest,
        "totals": _validation_totals_json(result.totals),
        "results": [
            {
                "case_id": case_result.case_id,
                "title": case_result.title,
                "genre": case_result.genre,
                "passed": case_result.passed,
                "actual_import": (
                    None
                    if case_result.actual_import is None
                    else {
                        "chapter_files": case_result.actual_import.chapter_files,
                        "source_manifest_digest": (
                            case_result.actual_import.source_manifest_digest
                        ),
                        "chapters": case_result.actual_import.chapters,
                        "scenes": case_result.actual_import.scenes,
                        "paragraphs": case_result.actual_import.paragraphs,
                        "sentences": case_result.actual_import.sentences,
                        "evidence_anchors": (
                            case_result.actual_import.evidence_anchors
                        ),
                        "import_digest": case_result.actual_import.import_digest,
                    }
                ),
                "actual_extraction": (
                    None
                    if case_result.actual_extraction is None
                    else {
                        "scene_inputs": case_result.actual_extraction.scene_inputs,
                        "evidence_anchors": (
                            case_result.actual_extraction.evidence_anchors
                        ),
                        "extraction_input_digest": (
                            case_result.actual_extraction.extraction_input_digest
                        ),
                        "extraction_prompt_digest": (
                            case_result.actual_extraction.extraction_prompt_digest
                        ),
                    }
                ),
                "errors": list(case_result.errors),
            }
            for case_result in result.results
        ],
    }


def _validation_metrics_line(metrics: ExpectedImportMetrics) -> str:
    """Return a compact validation metrics line."""
    return (
        f"  files={metrics.chapter_files} "
        f"chapters={metrics.chapters} "
        f"scenes={metrics.scenes} "
        f"paragraphs={metrics.paragraphs} "
        f"sentences={metrics.sentences} "
        f"anchors={metrics.evidence_anchors}"
    )


def _validation_extraction_line(metrics: ExpectedExtractionMetrics) -> str:
    """Return a compact validation extraction-readiness metrics line."""
    return (
        f"  extraction_inputs={metrics.scene_inputs} "
        f"extraction_anchors={metrics.evidence_anchors}"
    )


def _validation_totals_line(totals: ValidationTotals) -> str:
    """Return a compact validation totals line."""
    return (
        f"cases={totals.cases} "
        f"passed={totals.passed} "
        f"failed={totals.failed} "
        f"files={totals.chapter_files} "
        f"chapters={totals.chapters} "
        f"scenes={totals.scenes} "
        f"paragraphs={totals.paragraphs} "
        f"sentences={totals.sentences} "
        f"anchors={totals.evidence_anchors} "
        f"extraction_inputs={totals.extraction_inputs} "
        f"extraction_anchors={totals.extraction_anchors}"
    )


def _validation_totals_json(totals: ValidationTotals) -> dict[str, int]:
    """Return JSON-ready validation totals."""
    return {
        "cases": totals.cases,
        "passed": totals.passed,
        "failed": totals.failed,
        "chapter_files": totals.chapter_files,
        "chapters": totals.chapters,
        "scenes": totals.scenes,
        "paragraphs": totals.paragraphs,
        "sentences": totals.sentences,
        "evidence_anchors": totals.evidence_anchors,
        "extraction_inputs": totals.extraction_inputs,
        "extraction_anchors": totals.extraction_anchors,
    }


def _validation_source_root(source_root: str | None) -> Path:
    """Return the validation source root from args, environment, or default."""
    if source_root is not None:
        return Path(source_root)

    configured_source_root = os.environ.get("SCENESMITH_VALIDATION_ROOT")
    if configured_source_root is not None:
        if not configured_source_root.strip():
            raise ValueError("SCENESMITH_VALIDATION_ROOT cannot be blank.")
        return Path(configured_source_root)

    return Path.home() / "Desktop" / "SceneSmith test chapters"


def _character_ids(args: argparse.Namespace) -> tuple[str, ...]:
    """Return requested character IDs or the default demo character."""
    character_ids = cast(list[str] | None, args.character_id)
    if character_ids is None:
        return ("character_mark",)

    return _dedupe_ids(character_ids)


def _run_with_selected_extractor(args: argparse.Namespace) -> ProjectRunResult:
    """Run the demo extractor or AI JSON extractor based on command arguments."""
    if cast(str | None, args.ai_response_file) is not None:
        return _run_ai_json(args)

    return _runner().run_demo_text_file(
        path=Path(cast(str, args.path)),
        source_id=cast(str, args.source_id),
        title=cast(str | None, args.title),
    )


def _run_ai_json(args: argparse.Namespace) -> ProjectRunResult:
    """Run imported text through a static evidence-bounded AI JSON response."""
    runner = _runner()
    imported_source = runner.import_text_file(
        path=Path(cast(str, args.path)),
        source_id=cast(str, args.source_id),
        title=cast(str | None, args.title),
    )
    response_path = Path(
        cast(str, getattr(args, "response_path", None) or args.ai_response_file)
    )
    response = response_path.read_text(encoding="utf-8")
    scene_payloads = _scene_payloads_from_response(response)
    if scene_payloads is not None:
        return runner.run_imported_source_with_scene_payloads(
            imported_source=imported_source,
            payloads_by_scene_id=scene_payloads,
        )

    return runner.run_imported_scene(
        imported_source=imported_source,
        extractor=EvidenceBoundedAIExtractor(
            client=StaticAIExtractionClient(response)
        ),
        scene_id=cast(str | None, getattr(args, "scene_id", None)),
    )


def _runner() -> SceneSmithProjectRunner:
    """Create a project runner for a command."""
    return SceneSmithProjectRunner()


def _dedupe_ids(entity_ids: Sequence[str]) -> tuple[str, ...]:
    """Return IDs in first-seen order without duplicates."""
    deduped: dict[str, None] = {}
    for entity_id in entity_ids:
        _require_machine_token(entity_id, "Selected entity ID")
        deduped.setdefault(entity_id, None)

    return tuple(deduped)


def _require_text(value: str, field_name: str) -> None:
    """Validate a required CLI text value."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a whitespace-free CLI machine token."""
    _require_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _scene_payloads_from_response(response: str) -> dict[str, dict[str, object]] | None:
    """Return scene payloads from a multi-scene response envelope."""
    try:
        payload = loads_json_without_duplicate_keys(response)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict) or "scenes" not in payload:
        return None

    extra_keys = set(payload) - {"scenes"}
    if extra_keys:
        extra = ", ".join(sorted(extra_keys))
        raise ValueError(
            f"AI multi-scene response has unsupported envelope keys: {extra}"
        )

    scenes = payload["scenes"]
    if isinstance(scenes, dict):
        scene_payloads = scenes
    elif isinstance(scenes, list):
        scene_payloads = _scene_payloads_from_list(scenes)
    else:
        raise ValueError("AI multi-scene response field must be an object or list: scenes")

    parsed: dict[str, dict[str, object]] = {}
    for scene_id, scene_payload in scene_payloads.items():
        if not isinstance(scene_id, str):
            raise ValueError("AI multi-scene response scene IDs must be strings.")
        _require_machine_token(scene_id, "AI multi-scene response scene ID")
        if not isinstance(scene_payload, dict):
            raise ValueError("AI multi-scene response scene payloads must be objects.")
        parsed[scene_id] = dict(scene_payload)

    return parsed


def _scene_payloads_from_list(
    scenes: list[object],
) -> dict[str, dict[str, object]]:
    """Return scene payloads from list-form multi-scene response data."""
    scene_payloads: dict[str, dict[str, object]] = {}
    for item in scenes:
        if not isinstance(item, dict):
            raise ValueError("AI multi-scene response scene entries must be objects.")

        scene_id = item.get("scene_id")
        if not isinstance(scene_id, str):
            raise ValueError(
                "AI multi-scene response scene entries must include string scene_id."
            )
        _require_machine_token(scene_id, "AI multi-scene response scene ID")
        if scene_id in scene_payloads:
            raise ValueError(
                f"AI multi-scene response includes duplicate scene: {scene_id}"
            )

        scene_payload = dict(item)
        scene_payload.pop("scene_id")
        scene_payloads[scene_id] = scene_payload

    return scene_payloads


if __name__ == "__main__":
    sys.exit(main())

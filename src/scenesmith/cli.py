"""Command line interface for SceneSmith proof workflows."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from scenesmith.export import ExportEngine
from scenesmith.extraction import EvidenceBoundedAIExtractor, StaticAIExtractionClient
from scenesmith.presentation import PresentationEngine
from scenesmith.projects import ProjectRunResult, SceneSmithProjectRunner


def main(argv: Sequence[str] | None = None) -> int:
    """Run the SceneSmith command line interface.

    Parameters:
        argv: Optional command arguments. When omitted, process arguments are used.

    Returns:
        Process exit code.
    """
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
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {command}")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="scenesmith",
        description="SceneSmith proof CLI for importing and inspecting canon state.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    import_parser = subcommands.add_parser("import", help="Import source text.")
    _add_source_arguments(import_parser)

    extract_parser = subcommands.add_parser(
        "extract-demo",
        help="Run deterministic demo extraction over imported text.",
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
        help="Apply an evidence-bounded AI JSON response to imported text.",
    )
    _add_source_arguments(extract_ai_parser)
    extract_ai_parser.add_argument("response_path", help="Path to AI JSON response text.")
    extract_ai_parser.add_argument("--scene-id", default=None)

    character_parser = subcommands.add_parser("character", help="Print a character sheet.")
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

    scene_parser = subcommands.add_parser("scene", help="Print a scene sheet.")
    _add_source_arguments(scene_parser)
    scene_parser.add_argument("--scene-id", default=None)
    scene_parser.add_argument("--character-id", action="append", default=None)
    scene_parser.add_argument("--ai-response-file", default=None)
    scene_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    prompt_parser = subcommands.add_parser("prompt", help="Print a prompt sheet.")
    _add_source_arguments(prompt_parser)
    prompt_parser.add_argument("--scene-id", default=None)
    prompt_parser.add_argument("--character-id", action="append", default=None)
    prompt_parser.add_argument("--ai-response-file", default=None)
    prompt_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

    world_parser = subcommands.add_parser("world", help="Print a world sheet.")
    _add_source_arguments(world_parser)
    world_parser.add_argument("--entity-id", action="append", required=True)
    world_parser.add_argument("--chapter-index", type=int, default=None)
    world_parser.add_argument("--scene-id", default=None)
    world_parser.add_argument("--ai-response-file", default=None)

    continuity_parser = subcommands.add_parser(
        "continuity",
        help="Print a continuity report for the imported source.",
    )
    _add_source_arguments(continuity_parser)
    continuity_parser.add_argument("--ai-response-file", default=None)
    continuity_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")

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
    state = runner.build_world_state(
        result=result,
        entity_ids=tuple(cast(list[str], args.entity_id)),
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
        deduped.setdefault(entity_id, None)

    return tuple(deduped)


def _scene_payloads_from_response(response: str) -> dict[str, dict[str, object]] | None:
    """Return scene payloads from a multi-scene response envelope."""
    try:
        payload = json.loads(response.lstrip("\ufeff"))
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict) or "scenes" not in payload:
        return None

    scenes = payload["scenes"]
    if isinstance(scenes, dict):
        scene_payloads = scenes
    elif isinstance(scenes, list):
        scene_payloads = {
            item["scene_id"]: item
            for item in scenes
            if isinstance(item, dict) and isinstance(item.get("scene_id"), str)
        }
    else:
        raise ValueError("AI multi-scene response field must be an object or list: scenes")

    parsed: dict[str, dict[str, object]] = {}
    for scene_id, scene_payload in scene_payloads.items():
        if not isinstance(scene_id, str):
            raise ValueError("AI multi-scene response scene IDs must be strings.")
        if not isinstance(scene_payload, dict):
            raise ValueError("AI multi-scene response scene payloads must be objects.")
        parsed[scene_id] = dict(scene_payload)

    return parsed


if __name__ == "__main__":
    sys.exit(main())

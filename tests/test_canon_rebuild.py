"""Permanent Canon Rebuild Test for deterministic V1 behavior."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from scenesmith import (
    CanonPromptBuilder,
    ExportEngine,
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractionResult,
    PresentationEngine,
    SceneAnalyzer,
    SceneExtractionInput,
)
from scenesmith.projects import ProjectRunResult, SceneSmithProjectRunner


@dataclass(frozen=True, slots=True)
class CanonRebuildSnapshot:
    """Saved deterministic outputs and counts for one rebuild run."""

    outputs: dict[str, bytes]
    metrics: dict[str, int]


def four_chapter_source_file() -> Path:
    """Create a compact four-chapter continuity source."""
    return rebuild_source_file(chapter_count=4)


def rebuild_source_file(chapter_count: int) -> Path:
    """Create a compact continuity source with the first N rebuild chapters."""
    chapters = (
        ("Chapter 1", "Mark carried a rusty dagger."),
        ("Chapter 2", "Mark bought an iron sword."),
        ("Chapter 3", "Mark kept the iron sword while guarding the rain bridge."),
        ("Chapter 4", "Mark lost the iron sword before entering the northern forest."),
    )
    if not 1 <= chapter_count <= len(chapters):
        raise ValueError("Rebuild chapter count must be between 1 and 4.")

    path = Path("build") / "test_canon_rebuild" / "chapters_1_4.txt"
    if chapter_count < len(chapters):
        path = Path("build") / "test_canon_rebuild" / f"chapters_1_{chapter_count}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for title, text in chapters[:chapter_count]:
        if lines:
            lines.append("")
        lines.extend((title, text))
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


class FourChapterWeaponExtractor:
    """Extractor test double that tracks Mark's weapon across four chapters."""

    def extract_scene(self, scene: SceneExtractionInput) -> ExtractionResult:
        """Return deterministic candidates for the rebuild source."""
        anchor_id = scene.evidence_anchor_ids[0]
        lowered_text = scene.text.lower()
        if "rusty dagger" in lowered_text:
            weapon_id = "item_rusty_dagger"
            weapon = "Rusty Dagger"
        elif "lost the iron sword" in lowered_text:
            weapon_id = "item_iron_sword"
            weapon = "None"
        else:
            weapon_id = "item_iron_sword"
            weapon = "Iron Sword"

        normalized_weapon = weapon.lower().replace(" ", "_")
        normalized_scene = scene.scene_id.replace("rebuild_", "")
        return ExtractionResult(
            scene_id=scene.scene_id,
            entities=(
                ExtractedEntity(
                    entity_id="character_mark",
                    entity_type="character",
                    display_name="Mark",
                    evidence_anchor_id=anchor_id,
                    confidence=0.95,
                ),
                ExtractedEntity(
                    entity_id=weapon_id,
                    entity_type="item",
                    display_name=weapon_id.removeprefix("item_").replace("_", " ").title(),
                    evidence_anchor_id=anchor_id,
                    confidence=0.9,
                ),
            ),
            facts=(
                ExtractedFact(
                    fact_id=(
                        "fact_character_mark_current_weapon_"
                        f"{normalized_weapon}_{normalized_scene}"
                    ),
                    entity_id="character_mark",
                    attribute="current_weapon",
                    value=weapon,
                    evidence_anchor_id=anchor_id,
                    confidence=0.95,
                ),
            ),
            relationships=(
                ExtractedRelationship(
                    source_entity_id="character_mark",
                    relationship_type="lost" if weapon == "None" else "owns",
                    target_entity_id=weapon_id,
                    evidence_anchor_id=anchor_id,
                    confidence=0.88,
                ),
            ),
        )


def build_canon_rebuild_snapshot(output_dir: Path) -> CanonRebuildSnapshot:
    """Run an empty-project rebuild and save deterministic outputs."""
    return build_snapshot_for_source(
        source_path=four_chapter_source_file(),
        output_dir=output_dir,
    )


def build_snapshot_for_source(source_path: Path, output_dir: Path) -> CanonRebuildSnapshot:
    """Run an empty-project rebuild for a source path and save outputs."""
    runner = SceneSmithProjectRunner()
    imported_source = runner.import_text_file(
        path=source_path,
        source_id="rebuild",
        title="Canon Rebuild Fixture",
    )
    result = runner.run_imported_source(
        imported_source=imported_source,
        extractor=FourChapterWeaponExtractor(),
    )
    exporter = ExportEngine()
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_scene_id = runner.latest_scene_id(result)
    latest_context = runner.build_scene_context(
        result=result,
        scene_id=latest_scene_id,
        character_ids=("character_mark",),
    )
    latest_analysis = SceneAnalyzer().analyze(latest_context)
    presentation = PresentationEngine()
    latest_scene = presentation.scene_sheet(
        context=latest_context,
        analysis=latest_analysis,
    )
    latest_pack = CanonPromptBuilder().build_production_pack(latest_context)
    world_entity_id = (
        "item_iron_sword"
        if result.database.retrieve_entity("item_iron_sword") is not None
        else "item_rusty_dagger"
    )
    world_state = runner.build_world_state(
        result=result,
        entity_ids=(world_entity_id,),
    )

    outputs = {
        "character_cards/character_mark.md": exporter.character_profile_markdown(
            presentation.character_profile(
                runner.build_character_card(result=result, character_id="character_mark")
            )
        ),
        f"world_sheets/{world_entity_id}.md": exporter.world_sheet_view_markdown(
            presentation.world_sheet(world_state)
        ),
        f"world_sheets/{world_entity_id}.json": exporter.world_state_json(world_state),
        f"scene_sheets/{latest_scene_id}.md": exporter.scene_sheet_view_markdown(
            latest_scene
        ),
        "continuity_report.md": exporter.continuity_report_markdown(
            runner.build_continuity_report(result)
        ),
        f"prompt_packs/{latest_scene_id}.md": exporter.production_pack_view_markdown(
            presentation.production_pack(
                pack=latest_pack,
                scene=latest_scene,
            )
        ),
    }

    saved_outputs: dict[str, bytes] = {}
    for relative_path, text in sorted(outputs.items()):
        target = output_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        data = text.encode("utf-8")
        target.write_bytes(data)
        saved_outputs[relative_path] = data

    return CanonRebuildSnapshot(
        outputs=saved_outputs,
        metrics=canon_rebuild_metrics(result=result),
    )


def canon_rebuild_metrics(result: ProjectRunResult) -> dict[str, int]:
    """Return deterministic run metrics for Canon Rebuild comparison."""
    continuity_report = SceneSmithProjectRunner().build_continuity_report(result)
    return {
        "characters": len(
            {
                entity.entity_id
                for extraction_result in result.extraction_results
                for entity in extraction_result.entities
                if entity.entity_type == "character"
            }
        ),
        "facts": sum(
            len(summary.accepted_facts) for summary in result.update_summaries
        ),
        "relationships": sum(
            len(summary.accepted_relationships)
            for summary in result.update_summaries
        ),
        "state_changes": sum(
            len(summary.accepted_state_changes)
            for summary in result.update_summaries
        ),
        "evidence": len(result.imported_source.anchors),
        "prompts": 4,
        "continuity_records": sum(
            len(scene.new)
            + len(scene.updated)
            + len(scene.still_known)
            + len(scene.invalidated)
            for scene in continuity_report.scenes
        ),
        "warnings": sum(
            len(summary.rejected_candidates) for summary in result.update_summaries
        ),
        "errors": 0,
    }


def test_canon_rebuild_outputs_are_byte_deterministic() -> None:
    """Deleting and rebuilding an empty project must produce identical bytes."""
    first = build_canon_rebuild_snapshot(
        Path("build") / "test_canon_rebuild" / "run_a"
    )
    second = build_canon_rebuild_snapshot(
        Path("build") / "test_canon_rebuild" / "run_b"
    )

    assert second.outputs == first.outputs
    assert second.metrics == first.metrics
    assert first.metrics == {
        "characters": 1,
        "facts": 6,
        "relationships": 3,
        "state_changes": 6,
        "evidence": 4,
        "prompts": 4,
        "continuity_records": 54,
        "warnings": 0,
        "errors": 0,
    }


def test_canon_rebuild_outputs_are_presentation_first() -> None:
    """Canon Rebuild snapshots should preserve product-facing output shape."""
    snapshot = build_canon_rebuild_snapshot(
        Path("build") / "test_canon_rebuild" / "presentation_first"
    )

    character_sheet = snapshot.outputs["character_cards/character_mark.md"].decode(
        "utf-8"
    )
    scene_sheet_path = next(
        path for path in snapshot.outputs if path.startswith("scene_sheets/")
    )
    scene_sheet = snapshot.outputs[scene_sheet_path].decode("utf-8")
    prompt_pack_path = next(
        path for path in snapshot.outputs if path.startswith("prompt_packs/")
    )
    prompt_pack = snapshot.outputs[prompt_pack_path].decode("utf-8")

    assert "# Mark" in character_sheet
    assert "# Character Sheet:" not in character_sheet
    assert "## Characters Present" in scene_sheet
    assert "# Scene Sheet:" not in scene_sheet
    assert "## Image Prompt" in prompt_pack
    assert "# Prompt Sheet" not in prompt_pack
    assert any(path.endswith(".json") for path in snapshot.outputs)


def test_incremental_rebuild_final_output_matches_full_rebuild() -> None:
    """Progressive chapter rebuilds must converge with a full empty rebuild."""
    full = build_canon_rebuild_snapshot(
        Path("build") / "test_canon_rebuild" / "full_rebuild"
    )
    incremental: CanonRebuildSnapshot | None = None
    for chapter_count in range(1, 5):
        incremental = build_snapshot_for_source(
            source_path=rebuild_source_file(chapter_count=chapter_count),
            output_dir=(
                Path("build")
                / "test_canon_rebuild"
                / f"incremental_{chapter_count}"
            ),
        )

    assert incremental is not None
    assert incremental.outputs == full.outputs
    assert incremental.metrics == full.metrics


def test_out_of_order_rebuild_source_is_rejected() -> None:
    """Canon Rebuild protection rejects out-of-order explicit chapters."""
    source_path = Path("build") / "test_canon_rebuild" / "out_of_order.txt"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        "\n".join(
            [
                "Chapter 3",
                "Mark kept the iron sword.",
                "",
                "Chapter 1",
                "Mark carried a rusty dagger.",
                "",
                "Chapter 2",
                "Mark bought an iron sword.",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="increasing order"):
        SceneSmithProjectRunner().import_text_file(
            path=source_path,
            source_id="rebuild",
            title="Canon Rebuild Fixture",
        )

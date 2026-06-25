"""Permanent Canon Rebuild Test for deterministic V1 behavior."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scenesmith import (
    ExportEngine,
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractionResult,
    PresentationEngine,
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
    path = Path("build") / "test_canon_rebuild" / "chapters_1_4.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Chapter 1",
                "Mark carried a rusty dagger.",
                "",
                "Chapter 2",
                "Mark bought an iron sword.",
                "",
                "Chapter 3",
                "Mark kept the iron sword while guarding the rain bridge.",
                "",
                "Chapter 4",
                "Mark lost the iron sword before entering the northern forest.",
            ]
        ),
        encoding="utf-8",
    )
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
    runner = SceneSmithProjectRunner()
    imported_source = runner.import_text_file(
        path=four_chapter_source_file(),
        source_id="rebuild",
        title="Canon Rebuild Fixture",
    )
    result = runner.run_imported_source(
        imported_source=imported_source,
        extractor=FourChapterWeaponExtractor(),
    )
    exporter = ExportEngine()
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "character_cards/character_mark.md": exporter.canon_character_sheet_markdown(
            runner.build_character_card(result=result, character_id="character_mark")
        ),
        "world_sheets/item_iron_sword.md": exporter.world_sheet_view_markdown(
            PresentationEngine().world_sheet(
                runner.build_world_state(
                    result=result,
                    entity_ids=("item_iron_sword",),
                )
            )
        ),
        "scene_sheets/rebuild_chapter_004_scene_001.md": (
            exporter.canon_scene_sheet_markdown(
                runner.build_scene_context(
                    result=result,
                    scene_id="rebuild_chapter_004_scene_001",
                    character_ids=("character_mark",),
                )
            )
        ),
        "continuity_report.md": exporter.continuity_report_markdown(
            runner.build_continuity_report(result)
        ),
        "prompt_packs/rebuild_chapter_004_scene_001.md": exporter.prompt_sheet_markdown(
            runner.build_prompt_bundle(
                result=result,
                scene_id="rebuild_chapter_004_scene_001",
                character_ids=("character_mark",),
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
        "facts": 12,
        "relationships": 3,
        "state_changes": 12,
        "evidence": 4,
        "prompts": 4,
        "continuity_records": 82,
        "warnings": 0,
        "errors": 0,
    }

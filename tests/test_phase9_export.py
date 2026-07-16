"""Tests for Phase 9 Export."""

import csv
import io
import json
from dataclasses import replace

from aevryn import (
    CanonCharacterCard,
    CanonPromptBuilder,
    CanonSceneContext,
    CharacterCardBuilder,
    ExportEngine,
    SceneContextBuilder,
)
from aevryn.core import Entity, Relationship
from aevryn.prompts import PromptBundle
from tests.test_scene_context_builder import build_database, build_imported_source


def build_phase9_outputs() -> tuple[CanonCharacterCard, CanonSceneContext, PromptBundle]:
    """Build clean Phase 9 export inputs."""
    imported_source = build_imported_source()
    database = build_database()
    context = SceneContextBuilder(
        database=database,
        character_cards=CharacterCardBuilder(database=database),
    ).build_context(
        imported_source=imported_source,
        scene_id="source_demo_chapter_002_scene_001",
        character_ids=("character_mark",),
    )
    prompt_bundle = CanonPromptBuilder().build_bundle(context)
    return context.character_cards[0], context, prompt_bundle


def test_canon_character_sheet_markdown_exports_accepted_card() -> None:
    """Character sheet Markdown exports accepted Phase 6 card state."""
    card, _context, _bundle = build_phase9_outputs()

    markdown = ExportEngine().canon_character_sheet_markdown(card)

    assert "# Character Sheet: Mark" in markdown
    assert "- current_weapon: Iron Sword" in markdown
    assert "Evidence: Mark bought an iron sword." in markdown


def test_canon_scene_sheet_markdown_exports_context() -> None:
    """Scene sheet Markdown exports Phase 7 scene context."""
    _card, context, _bundle = build_phase9_outputs()

    markdown = ExportEngine().canon_scene_sheet_markdown(context)

    assert "# Scene Sheet: Scene 1" in markdown
    assert "Mark" in markdown
    assert "- character_mark current_weapon: Iron Sword" in markdown
    assert "character_mark owns item_iron_sword" in markdown


def test_canon_character_card_json_exports_evidence() -> None:
    """Character card JSON includes evidence details."""
    card, _context, _bundle = build_phase9_outputs()

    exported = json.loads(ExportEngine().canon_character_card_json(card))

    assert exported["character_id"] == "character_mark"
    assert exported["facts"][0]["value"] == "Iron Sword"
    assert exported["facts"][0]["evidence"]["quote"] == "Mark bought an iron sword."


def test_canon_scene_context_json_exports_snapshot() -> None:
    """Scene context JSON includes snapshot IDs and active facts."""
    _card, context, _bundle = build_phase9_outputs()

    exported = json.loads(ExportEngine().canon_scene_context_json(context))

    assert exported["snapshot"]["scene_id"] == "source_demo_chapter_002_scene_001"
    assert "location_ids" in exported["snapshot"]
    assert "event_ids" in exported["snapshot"]
    assert exported["active_facts"][0]["fact_id"] == "fact_008_weapon"


def test_canon_scene_context_json_sorts_relationships() -> None:
    """Scene context JSON exports relationships in stable ID order."""
    imported_source = build_imported_source()
    database = build_database()
    database.store_entity(
        Entity(
            entity_id="location_academy",
            entity_type="location",
            display_name="Academy",
        )
    )
    database.store_relationship(
        Relationship(
            relationship_id="relationship_aaa_mark_located_at_academy",
            source_entity_id="character_mark",
            relationship_type="located_at",
            target_entity_id="location_academy",
            evidence_id="evidence_relationship",
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

    exported = json.loads(ExportEngine().canon_scene_context_json(context))

    assert exported["relationships"][0]["relationship_id"] == (
        "relationship_aaa_mark_located_at_academy"
    )
    assert exported["snapshot"]["location_ids"] == ["location_academy"]


def test_canon_character_card_json_sorts_facts() -> None:
    """Character card JSON exports facts in stable attribute order."""
    card, _context, _bundle = build_phase9_outputs()
    reversed_card = replace(card, facts=tuple(reversed(card.facts)))

    exported = json.loads(ExportEngine().canon_character_card_json(reversed_card))

    assert [fact["attribute"] for fact in exported["facts"]] == sorted(
        fact["attribute"] for fact in exported["facts"]
    )


def test_canon_character_facts_csv_exports_rows() -> None:
    """Character fact CSV exports stable fact rows."""
    card, _context, _bundle = build_phase9_outputs()

    exported = ExportEngine().canon_character_facts_csv(card)
    rows = list(csv.DictReader(io.StringIO(exported)))

    assert rows[0]["character_id"] == "character_mark"
    assert rows[0]["attribute"] == "current_weapon"
    assert rows[0]["value"] == "Iron Sword"


def test_prompt_sheet_markdown_exports_clean_prompt_bundle() -> None:
    """Prompt sheet Markdown can export Phase 8 prompt bundles."""
    _card, _context, bundle = build_phase9_outputs()

    markdown = ExportEngine().prompt_sheet_markdown(bundle)

    assert "## Image Prompt" in markdown
    assert "Character: Mark" in markdown
    assert "Character: Mark (character_mark)" not in markdown


def test_production_pack_markdown_exports_scene_analysis() -> None:
    """Production pack Markdown exports analysis and prompt sections."""
    _card, context, _bundle = build_phase9_outputs()
    pack = CanonPromptBuilder().build_production_pack(context)

    markdown = ExportEngine().production_pack_markdown(pack)

    assert "# Production Pack: source_demo_chapter_002_scene_001" in markdown
    assert "## Scene Summary" in markdown
    assert "## Forbidden Elements" in markdown
    assert "## Image Prompt" in markdown

"""Export Engine implementation."""

from __future__ import annotations

import csv
import io
import json
import logging
from collections.abc import Iterable
from typing import Any

from aevryn.canon import CanonFactVersion, CanonRelationship, Evidence, StoryPosition
from aevryn.characters import (
    CanonCharacterCard,
    CanonCharacterFact,
    CharacterCard,
    CharacterFact,
)
from aevryn.core import Fact, Relationship
from aevryn.presentation import (
    CharacterProfileView,
    PresentationSection,
    ProductionPackView,
    SceneSheetView,
    WorldSheetView,
)
from aevryn.projects import ContinuityRecord, ContinuityReport, ContinuitySceneReport
from aevryn.prompts import ProductionPack, PromptBundle
from aevryn.scenes import CanonSceneContext, SceneContext, SceneEnvironmentSnapshot
from aevryn.timeline import TimelineEvent, TimelineStateChange
from aevryn.world import WorldState

logger = logging.getLogger(__name__)

MAX_STILL_KNOWN_MARKDOWN_RECORDS = 12


class ExportEngine:
    """Serialize Aevryn outputs into portable text formats."""

    def canon_character_sheet_markdown(self, card: CanonCharacterCard) -> str:
        """Export a Phase 6 character card as Markdown."""
        lines = [
            f"# Character Sheet: {card.display_name}",
            "",
            f"Character ID: {card.character_id}",
            f"Chapter Index: {card.chapter_index}",
            "",
            "## Facts",
        ]
        if card.facts:
            for fact in self._sorted_canon_character_facts(card.facts):
                lines.extend(self._canon_character_fact_markdown(fact))
        else:
            lines.append("Unknown")

        return "\n".join(lines)

    def canon_scene_sheet_markdown(self, context: CanonSceneContext) -> str:
        """Export a Phase 7 scene context as Markdown."""
        lines = [
            f"# Scene Sheet: {context.scene.title}",
            "",
            f"Scene ID: {context.scene.scene_id}",
            "",
            "## Characters",
        ]
        if context.character_cards:
            lines.extend(card.display_name for card in context.character_cards)
        else:
            lines.append("Unknown")

        lines.extend(["", "## Facts"])
        if context.active_facts:
            lines.extend(
                f"- {fact.entity_id} {fact.attribute}: {fact.value}"
                for fact in self._sorted_core_facts(context.active_facts)
            )
        else:
            lines.append("Unknown")

        lines.extend(["", "## Relationships"])
        if context.relationships:
            lines.extend(
                self._core_relationship_label(relationship)
                for relationship in self._sorted_core_relationships(
                    context.relationships
                )
            )
        else:
            lines.append("Unknown")

        return "\n".join(lines)

    def canon_character_card_json(self, card: CanonCharacterCard) -> str:
        """Export a Phase 6 character card as JSON text."""
        return self._to_json(self._canon_character_card_dict(card))

    def canon_scene_context_json(self, context: CanonSceneContext) -> str:
        """Export a Phase 7 scene context as JSON text."""
        return self._to_json(self._canon_scene_context_dict(context))

    def canon_character_facts_csv(self, card: CanonCharacterCard) -> str:
        """Export a Phase 6 character card facts as CSV text."""
        rows = [
            {
                "character_id": card.character_id,
                "attribute": fact.attribute,
                "value": fact.value,
                "previous_value": fact.previous_value or "",
                "chapter_id": fact.valid_from_chapter_id,
                "scene_id": fact.valid_from_scene_id,
                "evidence_quote": fact.evidence.quote,
            }
            for fact in self._sorted_canon_character_facts(card.facts)
        ]
        return self._csv_text(
            fieldnames=[
                "character_id",
                "attribute",
                "value",
                "previous_value",
                "chapter_id",
                "scene_id",
                "evidence_quote",
            ],
            rows=rows,
        )

    def character_sheet_markdown(self, card: CharacterCard) -> str:
        """Export a character card as Markdown.

        Parameters:
            card: Character card to export.

        Returns:
            Markdown character sheet.
        """
        lines = [
            f"# Character Sheet: {card.display_name}",
            "",
            f"Character ID: {card.character_id}",
            f"Position: {self._position_label(card.position)}",
            "",
            "## Facts",
        ]
        if card.facts:
            for fact in self._sorted_character_facts(card.facts):
                lines.extend(self._character_fact_markdown(fact))
        else:
            lines.append("Unknown")

        lines.extend(["", "## Relationships"])
        if card.relationships:
            lines.extend(
                self._relationship_label(relationship)
                for relationship in card.relationships
            )
        else:
            lines.append("Unknown")

        return "\n".join(lines)

    def scene_sheet_markdown(self, context: SceneContext) -> str:
        """Export scene context as Markdown.

        Parameters:
            context: Scene context to export.

        Returns:
            Markdown scene sheet.
        """
        lines = [
            f"# Scene Sheet: {context.scene.title}",
            "",
            f"Position: {self._position_label(context.position)}",
            "",
            "## Characters",
        ]
        if context.characters:
            lines.extend(character.display_name for character in context.characters)
        else:
            lines.append("Unknown")

        lines.extend(["", "## Environment"])
        if context.environment:
            lines.extend(self._environment_markdown(snapshot) for snapshot in context.environment)
        else:
            lines.append("Unknown")

        lines.extend(["", "## Events"])
        if context.events:
            lines.extend(event.description for event in context.events)
        else:
            lines.append("Unknown")

        return "\n".join(lines)

    def prompt_sheet_markdown(self, bundle: PromptBundle) -> str:
        """Export prompt bundle as Markdown.

        Parameters:
            bundle: Prompt bundle to export.

        Returns:
            Markdown prompt sheet.
        """
        return "\n".join(
            [
                "# Prompt Sheet",
                "",
                "## Image Prompt",
                bundle.image_prompt,
                "",
                "## Narration Prompt",
                bundle.narration_prompt,
                "",
                "## Camera Prompt",
                bundle.camera_prompt,
                "",
                "## Animation Prompt",
                bundle.animation_prompt,
            ]
        ).strip()

    def production_pack_markdown(self, pack: ProductionPack) -> str:
        """Export a production pack as Markdown."""
        return "\n".join(
            [
                f"# Production Pack: {pack.scene_id}",
                "",
                "## Scene Summary",
                pack.scene_summary,
                "",
                "## Purpose",
                pack.purpose,
                "",
                "## Conflict",
                pack.conflict,
                "",
                "## Mood",
                pack.mood,
                "",
                "## Visual Highlights",
                *self._markdown_list(pack.visual_highlights),
                "",
                "## Character Goals",
                *self._markdown_list(pack.character_goals),
                "",
                "## Important Objects",
                *self._markdown_list(pack.important_objects),
                "",
                "## Environment",
                pack.environment_summary,
                "",
                "## Continuity Notes",
                *self._markdown_list(pack.continuity_notes),
                "",
                "## Forbidden Elements",
                *self._markdown_list(pack.forbidden_elements),
                "",
                self.prompt_sheet_markdown(pack.prompt_bundle),
            ]
        )

    def continuity_report_markdown(self, report: ContinuityReport) -> str:
        """Export a continuity report as Markdown."""
        lines = [
            f"# Continuity Report: {report.source_id}",
            "",
        ]
        for scene_report in report.scenes:
            lines.extend(
                [
                    f"## {scene_report.scene_id}",
                    "",
                    "### Summary",
                    *self._continuity_summary_lines(scene_report),
                    "",
                    "### New",
                    *self._continuity_record_lines(scene_report.new),
                    "",
                    "### Updated",
                    *self._continuity_record_lines(scene_report.updated),
                    "",
                    "### Still Known",
                    *self._continuity_still_known_lines(scene_report.still_known),
                    "",
                    "### Invalidated",
                    *self._continuity_record_lines(scene_report.invalidated),
                    "",
                ]
            )

        return "\n".join(lines).strip()

    def character_profile_markdown(self, profile: CharacterProfileView) -> str:
        """Export a presented character profile as Markdown."""
        lines = [
            f"# {profile.display_name}",
            "",
            profile.subtitle,
            "",
        ]
        sections = (
            profile.race,
            profile.gender,
            profile.status,
            profile.current_goal,
            profile.current_equipment,
            profile.current_abilities,
            profile.current_assets,
            profile.territory,
            profile.relationships,
            profile.current_limitations,
            profile.recent_changes,
        )
        for section in sections:
            lines.extend(self._presentation_section_markdown(section))
            lines.append("")
        lines.extend(["## Evidence", profile.evidence_summary])
        return "\n".join(lines)

    def scene_sheet_view_markdown(self, scene: SceneSheetView) -> str:
        """Export a presented scene sheet as Markdown."""
        lines = [
            f"# {scene.title}",
            "",
            scene.chapter_label,
            "",
        ]
        sections = (
            scene.location,
            scene.characters_present,
            scene.mood,
            scene.purpose,
            scene.visual_highlights,
            scene.continuity_changes,
            scene.environment,
        )
        for section in sections:
            lines.extend(self._presentation_section_markdown(section))
            lines.append("")
        lines.extend(["## Evidence", scene.evidence_summary])
        return "\n".join(lines)

    def production_pack_view_markdown(self, view: ProductionPackView) -> str:
        """Export a presented production pack as Markdown."""
        lines = [
            self.scene_sheet_view_markdown(view.scene),
            "",
        ]
        for section in (
            view.image_prompt,
            view.narration_prompt,
            view.camera_prompt,
            view.animation_prompt,
        ):
            lines.extend(self._presentation_section_markdown(section))
            lines.append("")

        return "\n".join(lines).strip()

    def world_sheet_view_markdown(self, view: WorldSheetView) -> str:
        """Export a presented world sheet as Markdown."""
        lines = [
            "# World Sheet",
            "",
            view.chapter_label,
            "",
        ]
        for section in view.entity_sections:
            lines.extend(self._presentation_section_markdown(section))
            lines.append("")
        lines.extend(["## Evidence", view.evidence_summary])
        return "\n".join(lines)

    def world_state_json(self, state: WorldState) -> str:
        """Export canon-backed world state as JSON text."""
        return self._to_json(
            {
                "chapter_index": state.chapter_index,
                "entities": [
                    {
                        "entity_id": entity.entity_id,
                        "entity_type": entity.entity_type,
                        "display_name": entity.display_name,
                        "chapter_index": entity.chapter_index,
                        "facts": [
                            {
                                "attribute": fact.attribute,
                                "value": fact.value,
                                "valid_from_chapter_id": fact.valid_from_chapter_id,
                                "valid_from_scene_id": fact.valid_from_scene_id,
                                "evidence": {
                                    "evidence_id": fact.evidence.evidence_id,
                                    "source_id": fact.evidence.source_id,
                                    "chapter_id": fact.evidence.chapter_id,
                                    "scene_id": fact.evidence.scene_id,
                                    "paragraph_index": fact.evidence.paragraph_index,
                                    "sentence_index": fact.evidence.sentence_index,
                                    "quote": fact.evidence.quote,
                                    "confidence": fact.evidence.confidence,
                                },
                            }
                            for fact in sorted(
                                entity.facts,
                                key=lambda fact: (
                                    fact.attribute,
                                    fact.valid_from_chapter_id,
                                    fact.valid_from_scene_id,
                                    fact.value,
                                ),
                            )
                        ],
                        "relationships": [
                            {
                                "relationship_id": relationship.relationship_id,
                                "source_entity_id": relationship.source_entity_id,
                                "relationship_type": relationship.relationship_type,
                                "target_entity_id": relationship.target_entity_id,
                                "evidence_id": relationship.evidence_id,
                            }
                            for relationship in sorted(
                                entity.relationships,
                                key=lambda relationship: relationship.relationship_id,
                            )
                        ],
                    }
                    for entity in sorted(
                        state.entities,
                        key=lambda entity: entity.entity_id,
                    )
                ],
            }
        )

    def character_card_json(self, card: CharacterCard) -> str:
        """Export a character card as JSON text."""
        return self._to_json(self._character_card_dict(card))

    def scene_context_json(self, context: SceneContext) -> str:
        """Export scene context as JSON text."""
        return self._to_json(self._scene_context_dict(context))

    def prompt_bundle_json(self, bundle: PromptBundle) -> str:
        """Export prompt bundle as JSON text."""
        return self._to_json(
            {
                "image_prompt": bundle.image_prompt,
                "narration_prompt": bundle.narration_prompt,
                "camera_prompt": bundle.camera_prompt,
                "animation_prompt": bundle.animation_prompt,
            }
        )

    def continuity_report_json(self, report: ContinuityReport) -> str:
        """Export a continuity report as JSON text."""
        return self._to_json(
            {
                "source_id": report.source_id,
                "scenes": [
                    {
                        "scene_id": scene_report.scene_id,
                        "new": [
                            self._continuity_record_dict(record)
                            for record in scene_report.new
                        ],
                        "updated": [
                            self._continuity_record_dict(record)
                            for record in scene_report.updated
                        ],
                        "still_known": [
                            self._continuity_record_dict(record)
                            for record in scene_report.still_known
                        ],
                        "invalidated": [
                            self._continuity_record_dict(record)
                            for record in scene_report.invalidated
                        ],
                    }
                    for scene_report in report.scenes
                ],
            }
        )

    def character_facts_csv(self, card: CharacterCard) -> str:
        """Export character facts as CSV text."""
        rows = [
            {
                "character_id": card.character_id,
                "attribute": fact.attribute,
                "value": fact.value,
                "previous_value": fact.previous_value or "",
                "chapter": fact.evidence.chapter,
                "scene": fact.evidence.scene,
                "confidence": str(fact.evidence.confidence),
            }
            for fact in self._sorted_character_facts(card.facts)
        ]
        return self._csv_text(
            fieldnames=[
                "character_id",
                "attribute",
                "value",
                "previous_value",
                "chapter",
                "scene",
                "confidence",
            ],
            rows=rows,
        )

    def prompt_bundle_csv(self, bundle: PromptBundle) -> str:
        """Export prompt bundle as CSV text."""
        return self._csv_text(
            fieldnames=["prompt_type", "prompt"],
            rows=[
                {"prompt_type": "image", "prompt": bundle.image_prompt},
                {"prompt_type": "narration", "prompt": bundle.narration_prompt},
                {"prompt_type": "camera", "prompt": bundle.camera_prompt},
                {"prompt_type": "animation", "prompt": bundle.animation_prompt},
            ],
        )

    @classmethod
    def _canon_character_card_dict(cls, card: CanonCharacterCard) -> dict[str, Any]:
        """Convert a Phase 6 character card to a JSON-ready dictionary."""
        return {
            "character_id": card.character_id,
            "display_name": card.display_name,
            "chapter_index": card.chapter_index,
            "facts": [
                cls._canon_character_fact_dict(fact)
                for fact in cls._sorted_canon_character_facts(card.facts)
            ],
        }

    @classmethod
    def _canon_scene_context_dict(cls, context: CanonSceneContext) -> dict[str, Any]:
        """Convert a Phase 7 scene context to a JSON-ready dictionary."""
        return {
            "snapshot": {
                "snapshot_id": context.snapshot.snapshot_id,
                "scene_id": context.snapshot.scene_id,
                "character_ids": list(context.snapshot.character_ids),
                "location_ids": list(context.snapshot.location_ids),
                "fact_ids": list(context.snapshot.fact_ids),
                "relationship_ids": list(context.snapshot.relationship_ids),
                "event_ids": list(context.snapshot.event_ids),
            },
            "scene": {
                "scene_id": context.scene.scene_id,
                "chapter_id": context.scene.chapter_id,
                "scene_index": context.scene.scene_index,
                "title": context.scene.title,
                "paragraphs": list(context.scene.paragraphs),
            },
            "character_cards": [
                cls._canon_character_card_dict(card)
                for card in sorted(
                    context.character_cards,
                    key=lambda card: card.character_id,
                )
            ],
            "active_facts": [
                {
                    "fact_id": fact.fact_id,
                    "entity_id": fact.entity_id,
                    "attribute": fact.attribute,
                    "value": fact.value,
                    "evidence_id": fact.evidence_id,
                }
                for fact in cls._sorted_core_facts(context.active_facts)
            ],
            "relationships": [
                {
                    "relationship_id": relationship.relationship_id,
                    "source_entity_id": relationship.source_entity_id,
                    "relationship_type": relationship.relationship_type,
                    "target_entity_id": relationship.target_entity_id,
                    "evidence_id": relationship.evidence_id,
                }
                for relationship in cls._sorted_core_relationships(context.relationships)
            ],
        }

    @staticmethod
    def _canon_character_fact_dict(fact: CanonCharacterFact) -> dict[str, Any]:
        """Convert a Phase 6 character fact to a JSON-ready dictionary."""
        return {
            "attribute": fact.attribute,
            "value": fact.value,
            "previous_value": fact.previous_value,
            "valid_from_chapter_id": fact.valid_from_chapter_id,
            "valid_from_scene_id": fact.valid_from_scene_id,
            "evidence": {
                "evidence_id": fact.evidence.evidence_id,
                "source_id": fact.evidence.source_id,
                "chapter_id": fact.evidence.chapter_id,
                "scene_id": fact.evidence.scene_id,
                "paragraph_index": fact.evidence.paragraph_index,
                "sentence_index": fact.evidence.sentence_index,
                "quote": fact.evidence.quote,
                "confidence": fact.evidence.confidence,
            },
        }

    @staticmethod
    def _canon_character_fact_markdown(fact: CanonCharacterFact) -> list[str]:
        """Convert a Phase 6 character fact to Markdown lines."""
        return [
            f"- {fact.attribute}: {fact.value}",
            f"  - Previous: {fact.previous_value or 'Unknown'}",
            f"  - Valid From: {fact.valid_from_chapter_id}, {fact.valid_from_scene_id}",
            f"  - Evidence: {fact.evidence.quote}",
        ]

    @classmethod
    def _character_card_dict(cls, card: CharacterCard) -> dict[str, Any]:
        """Convert a character card to a JSON-ready dictionary."""
        return {
            "character_id": card.character_id,
            "display_name": card.display_name,
            "position": cls._position_dict(card.position),
            "facts": {
                attribute: cls._character_fact_dict(fact)
                for attribute, fact in sorted(card.facts.items())
            },
            "relationships": [
                cls._relationship_dict(relationship)
                for relationship in sorted(
                    card.relationships,
                    key=lambda relationship: (
                        relationship.source_entity_id,
                        relationship.relationship_type,
                        relationship.target_entity_id,
                    ),
                )
            ],
        }

    @classmethod
    def _scene_context_dict(cls, context: SceneContext) -> dict[str, Any]:
        """Convert scene context to a JSON-ready dictionary."""
        return {
            "position": cls._position_dict(context.position),
            "scene": {
                "title": context.scene.title,
                "position": cls._position_dict(context.scene.position),
            },
            "characters": [
                cls._character_card_dict(character)
                for character in sorted(
                    context.characters,
                    key=lambda character: character.character_id,
                )
            ],
            "environment": [
                cls._environment_dict(snapshot)
                for snapshot in sorted(
                    context.environment,
                    key=lambda snapshot: snapshot.entity_id,
                )
            ],
            "events": [
                cls._event_dict(event)
                for event in sorted(
                    context.events,
                    key=lambda event: (event.position, event.event_id),
                )
            ],
            "active_state_changes": [
                cls._state_change_dict(state_change)
                for state_change in sorted(
                    context.active_state_changes,
                    key=lambda state_change: (
                        state_change.valid_from,
                        state_change.subject_id,
                        state_change.attribute,
                        state_change.change_id,
                    ),
                )
            ],
        }

    @classmethod
    def _character_fact_dict(cls, fact: CharacterFact) -> dict[str, Any]:
        """Convert a character fact to a JSON-ready dictionary."""
        return {
            "attribute": fact.attribute,
            "value": fact.value,
            "previous_value": fact.previous_value,
            "evidence": cls._evidence_dict(fact.evidence),
            "valid_from": cls._position_dict(fact.valid_from),
            "valid_until": cls._position_dict(fact.valid_until),
        }

    @classmethod
    def _canon_fact_dict(cls, fact: CanonFactVersion) -> dict[str, Any]:
        """Convert a canon fact to a JSON-ready dictionary."""
        return {
            "entity_id": fact.entity_id,
            "attribute": fact.attribute,
            "value": fact.value,
            "previous_value": fact.previous_value,
            "evidence": cls._evidence_dict(fact.evidence),
        }

    @classmethod
    def _environment_dict(cls, snapshot: SceneEnvironmentSnapshot) -> dict[str, Any]:
        """Convert an environment snapshot to a JSON-ready dictionary."""
        return {
            "entity_id": snapshot.entity_id,
            "facts": {
                attribute: cls._canon_fact_dict(fact)
                for attribute, fact in sorted(snapshot.facts.items())
            },
        }

    @classmethod
    def _relationship_dict(cls, relationship: CanonRelationship) -> dict[str, Any]:
        """Convert a relationship to a JSON-ready dictionary."""
        return {
            "source_entity_id": relationship.source_entity_id,
            "relationship_type": relationship.relationship_type,
            "target_entity_id": relationship.target_entity_id,
            "evidence": cls._evidence_dict(relationship.evidence),
        }

    @classmethod
    def _event_dict(cls, event: TimelineEvent) -> dict[str, Any]:
        """Convert a timeline event to a JSON-ready dictionary."""
        return {
            "event_id": event.event_id,
            "position": cls._position_dict(event.position),
            "description": event.description,
        }

    @classmethod
    def _state_change_dict(cls, state_change: TimelineStateChange) -> dict[str, Any]:
        """Convert a state change to a JSON-ready dictionary."""
        return {
            "change_id": state_change.change_id,
            "subject_id": state_change.subject_id,
            "attribute": state_change.attribute,
            "value": state_change.value,
            "valid_from": cls._position_dict(state_change.valid_from),
            "valid_until": cls._position_dict(state_change.valid_until),
            "event_id": state_change.event_id,
        }

    @classmethod
    def _evidence_dict(cls, evidence: Evidence) -> dict[str, Any]:
        """Convert evidence to a JSON-ready dictionary."""
        return {
            "chapter": evidence.chapter,
            "scene": evidence.scene,
            "quote": evidence.quote,
            "confidence": evidence.confidence,
            "position": cls._position_dict(evidence.position),
        }

    @staticmethod
    def _position_dict(position: StoryPosition | None) -> dict[str, int] | None:
        """Convert a story position to a JSON-ready dictionary."""
        if position is None:
            return None

        return {
            "chapter_index": position.chapter_index,
            "scene_index": position.scene_index,
        }

    @staticmethod
    def _position_label(position: StoryPosition | None) -> str:
        """Convert a story position to human-readable text."""
        if position is None:
            return "Current"

        return f"Chapter {position.chapter_index}, Scene {position.scene_index}"

    @staticmethod
    def _sorted_character_facts(facts: dict[str, CharacterFact]) -> tuple[CharacterFact, ...]:
        """Return character facts sorted by attribute."""
        return tuple(fact for _attribute, fact in sorted(facts.items()))

    def _character_fact_markdown(self, fact: CharacterFact) -> list[str]:
        """Convert a character fact to Markdown lines."""
        return [
            f"- {fact.attribute}: {fact.value}",
            f"  - Previous: {fact.previous_value or 'Unknown'}",
            f"  - Valid From: {self._position_label(fact.valid_from)}",
            f"  - Evidence: {fact.evidence.chapter}, {fact.evidence.scene}",
        ]

    @classmethod
    def _environment_markdown(cls, snapshot: SceneEnvironmentSnapshot) -> str:
        """Convert an environment snapshot to Markdown text."""
        facts = ", ".join(
            f"{attribute}: {fact.value}"
            for attribute, fact in sorted(snapshot.facts.items())
        )
        if not facts:
            facts = "Unknown"

        return f"{snapshot.entity_id}: {facts}"

    @staticmethod
    def _relationship_label(relationship: CanonRelationship) -> str:
        """Convert a relationship to human-readable text."""
        return (
            f"{relationship.source_entity_id} "
            f"{relationship.relationship_type} "
            f"{relationship.target_entity_id}"
        )

    @staticmethod
    def _core_relationship_label(relationship: Relationship) -> str:
        """Convert a core relationship-like object to human-readable text."""
        return (
            f"{relationship.source_entity_id} "
            f"{relationship.relationship_type} "
            f"{relationship.target_entity_id}"
        )

    @staticmethod
    def _to_json(value: dict[str, Any]) -> str:
        """Serialize a dictionary as stable JSON text."""
        serialized = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
        logger.debug("export_json_serialized")
        return serialized

    @staticmethod
    def _csv_text(fieldnames: list[str], rows: list[dict[str, str]]) -> str:
        """Serialize rows as CSV text."""
        if len(fieldnames) != len(set(fieldnames)):
            raise ValueError("CSV fieldnames cannot contain duplicates.")
        fieldname_set = set(fieldnames)
        for row in rows:
            row_keys = set(row)
            missing_keys = fieldname_set - row_keys
            extra_keys = row_keys - fieldname_set
            if missing_keys:
                raise ValueError("CSV rows must include every configured field.")
            if extra_keys:
                raise ValueError("CSV rows cannot include unexpected fields.")

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    @staticmethod
    def _markdown_list(values: tuple[str, ...]) -> list[str]:
        """Return Markdown bullet list lines."""
        if not values:
            return ["- Unknown"]
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("Markdown list values cannot be blank.")

        return [
            f"- {value}"
            for value in ExportEngine._unique_values(
                " ".join(value.split()) for value in values
            )
        ]

    @classmethod
    def _presentation_section_markdown(cls, section: PresentationSection) -> list[str]:
        """Return Markdown lines for a presentation section."""
        return [
            f"## {section.title}",
            *cls._markdown_list(section.items),
        ]

    @staticmethod
    def _continuity_record_dict(record: ContinuityRecord) -> dict[str, str]:
        """Convert a continuity record to a JSON-ready dictionary."""
        return {
            "record_id": record.record_id,
            "record_type": record.record_type,
            "description": record.description,
            "evidence_id": record.evidence_id,
            "chapter_id": record.chapter_id,
            "scene_id": record.scene_id,
            "evidence_quote": record.evidence_quote,
        }

    @classmethod
    def _continuity_record_lines(
        cls,
        records: tuple[ContinuityRecord, ...],
    ) -> list[str]:
        """Return Markdown lines for continuity records."""
        if not records:
            return ["Unknown"]

        sorted_records = tuple(sorted(records, key=lambda record: record.record_id))
        visible_records = tuple(
            record for record in sorted_records if record.record_type != "state_change"
        )
        state_change_count = len(sorted_records) - len(visible_records)

        lines = [
            cls._continuity_record_line(record)
            for record in visible_records
        ]
        if state_change_count > 0:
            lines.append(
                "- "
                f"{state_change_count} state changes recorded; "
                "use JSON export for exact validity events."
            )
        return lines or ["Unknown"]

    @staticmethod
    def _continuity_summary_lines(scene_report: ContinuitySceneReport) -> list[str]:
        """Return concise continuity counts for one scene."""
        return [
            f"- New: {len(scene_report.new)}",
            f"- Updated: {len(scene_report.updated)}",
            f"- Still known: {len(scene_report.still_known)}",
            f"- Invalidated: {len(scene_report.invalidated)}",
        ]

    @classmethod
    def _continuity_still_known_lines(
        cls,
        records: tuple[ContinuityRecord, ...],
    ) -> list[str]:
        """Return retained canon records without flooding the human report."""
        if not records:
            return ["Unknown"]

        sorted_records = tuple(sorted(records, key=lambda record: record.record_id))
        state_change_count = sum(
            1 for record in sorted_records if record.record_type == "state_change"
        )
        display_records = tuple(
            record for record in sorted_records if record.record_type != "state_change"
        )
        visible_records = display_records[:MAX_STILL_KNOWN_MARKDOWN_RECORDS]
        hidden_count = len(display_records) - len(visible_records)

        lines = [f"- {len(sorted_records)} retained canon records remain active."]
        if state_change_count > 0:
            lines.append(
                "- "
                f"{state_change_count} retained state changes omitted from Markdown; "
                "use JSON export for exact validity events."
            )
        lines.extend(
            cls._continuity_record_summary_line(record) for record in visible_records
        )
        if hidden_count > 0:
            lines.append(
                "- "
                f"{hidden_count} additional retained records omitted from Markdown; "
                "use JSON export for the full audit trail."
            )
        return lines

    @staticmethod
    def _continuity_record_line(record: ContinuityRecord) -> str:
        """Return one Markdown line for a continuity record."""
        evidence_parts = [
            value
            for value in (
                record.chapter_id,
                record.scene_id,
                record.evidence_quote,
            )
            if value
        ]
        evidence = f" Evidence: {' | '.join(evidence_parts)}" if evidence_parts else ""
        return f"- [{record.record_type}] {record.description}.{evidence}"

    @staticmethod
    def _continuity_record_summary_line(record: ContinuityRecord) -> str:
        """Return one concise Markdown line for a retained continuity record."""
        return f"- [{record.record_type}] {record.description}."

    @staticmethod
    def _sorted_canon_character_facts(
        facts: Iterable[CanonCharacterFact],
    ) -> tuple[CanonCharacterFact, ...]:
        """Return canon character facts in stable display order."""
        return tuple(
            sorted(
                facts,
                key=lambda fact: (
                    fact.attribute,
                    fact.valid_from_chapter_id,
                    fact.valid_from_scene_id,
                    fact.value,
                ),
            )
        )

    @staticmethod
    def _sorted_core_facts(facts: Iterable[Fact]) -> tuple[Fact, ...]:
        """Return core facts in stable export order."""
        return tuple(sorted(facts, key=lambda fact: fact.fact_id))

    @staticmethod
    def _sorted_core_relationships(
        relationships: Iterable[Relationship],
    ) -> tuple[Relationship, ...]:
        """Return core relationships in stable export order."""
        return tuple(
            sorted(
                relationships,
                key=lambda relationship: relationship.relationship_id,
            )
        )

    @staticmethod
    def _unique_values(values: Iterable[str]) -> list[str]:
        """Return non-empty values in first-seen order without duplicates."""
        unique: dict[str, None] = {}
        for value in values:
            if value:
                unique.setdefault(value, None)

        return list(unique)

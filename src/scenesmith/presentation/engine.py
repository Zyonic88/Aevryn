"""Presentation Engine implementation."""

from __future__ import annotations

import logging
import textwrap
from collections.abc import Iterable

from scenesmith.characters import CanonCharacterCard, CanonCharacterFact
from scenesmith.presentation.models import (
    CharacterProfileView,
    PresentationSection,
    ProductionPackView,
    SceneSheetView,
    WorldSheetView,
)
from scenesmith.prompts import ProductionPack
from scenesmith.scenes import CanonSceneContext, SceneAnalysis
from scenesmith.world import WorldEntityState, WorldState

logger = logging.getLogger(__name__)


class PresentationEngine:
    """Convert internal SceneSmith truth into human-readable view models."""

    def character_profile(self, card: CanonCharacterCard) -> CharacterProfileView:
        """Build a human-readable character profile.

        Parameters:
            card: Canon-backed character card.

        Returns:
            Character profile view optimized for fast human scanning.
        """
        facts_by_attribute = self._facts_by_attribute(card.facts)
        profile = CharacterProfileView(
            character_id=card.character_id,
            display_name=card.display_name,
            subtitle=self._subtitle(facts_by_attribute),
            status=self._section("Status", facts_by_attribute, ("status", "role")),
            current_goal=self._section(
                "Current Goal",
                facts_by_attribute,
                ("current_task", "starship_plan", "next_semester_requirement"),
            ),
            current_equipment=self._section(
                "Current Equipment",
                facts_by_attribute,
                ("current_weapon", "equipment", "inventory"),
            ),
            current_abilities=self._section(
                "Current Abilities",
                facts_by_attribute,
                (
                    "profession",
                    "system_reward_fleet_luck_bonus",
                    "system_reward_eye_of_insight",
                    "eye_of_insight_effect",
                ),
            ),
            current_assets=self._section(
                "Current Assets",
                facts_by_attribute,
                ("warehouse", "starships_owned", "territory"),
            ),
            territory=self._section(
                "Territory",
                facts_by_attribute,
                (
                    "noble_title",
                    "territory",
                    "territory_condition",
                    "territory_limitation",
                    "territory_security",
                ),
            ),
            relationships=self._section(
                "Relationships",
                facts_by_attribute,
                ("relationship_context", "family_context", "origin_context"),
            ),
            current_limitations=self._section(
                "Current Limitations",
                facts_by_attribute,
                ("current_limitation", "territory_limitation"),
            ),
            recent_changes=self._recent_changes(card.facts),
            evidence_summary=self._evidence_summary(card.facts),
        )
        logger.debug(
            "character_profile_view_built",
            extra={"character_id": card.character_id},
        )
        return profile

    def scene_sheet(
        self,
        context: CanonSceneContext,
        analysis: SceneAnalysis,
    ) -> SceneSheetView:
        """Build a human-readable scene sheet.

        Parameters:
            context: Canon-backed scene context.
            analysis: Meaning-focused scene analysis.

        Returns:
            Scene sheet view optimized for fast human scanning.

        Raises:
            ValueError: If analysis belongs to a different scene.
        """
        if context.scene.scene_id != analysis.scene_id:
            raise ValueError("Scene analysis must match the presented scene.")

        return SceneSheetView(
            scene_id=context.scene.scene_id,
            title=context.scene.title,
            chapter_label=context.scene.chapter_id,
            location=PresentationSection(
                title="Location",
                items=self._location_items(context),
            ),
            characters_present=PresentationSection(
                title="Characters Present",
                items=tuple(self._unique_values(
                    card.display_name for card in context.character_cards
                )),
            ),
            mood=PresentationSection(title="Mood", items=(analysis.mood,)),
            purpose=PresentationSection(title="Purpose", items=(analysis.purpose,)),
            visual_highlights=PresentationSection(
                title="Visual Highlights",
                items=analysis.visual_highlights,
            ),
            continuity_changes=PresentationSection(
                title="Continuity Changes",
                items=analysis.changes_introduced,
            ),
            environment=PresentationSection(
                title="Environment",
                items=(analysis.environment_summary,),
            ),
            evidence_summary=self._scene_evidence_summary(context),
        )

    def production_pack(self, pack: ProductionPack, scene: SceneSheetView) -> ProductionPackView:
        """Build a human-readable production pack view.

        Parameters:
            pack: Internal production pack.
            scene: Presented scene sheet view.

        Returns:
            Production pack view with concise prompt sections.
        """
        return ProductionPackView(
            scene=scene,
            image_prompt=PresentationSection(
                title="Image Prompt",
                items=self._prompt_lines(pack.prompt_bundle.image_prompt),
            ),
            narration_prompt=PresentationSection(
                title="Narration Prompt",
                items=self._prompt_lines(pack.prompt_bundle.narration_prompt),
            ),
            camera_prompt=PresentationSection(
                title="Camera Prompt",
                items=self._prompt_lines(pack.prompt_bundle.camera_prompt),
            ),
            animation_prompt=PresentationSection(
                title="Animation Prompt",
                items=self._prompt_lines(pack.prompt_bundle.animation_prompt),
            ),
        )

    def world_sheet(self, state: WorldState) -> WorldSheetView:
        """Build a human-readable world sheet.

        Parameters:
            state: Canon-backed world state.

        Returns:
            World sheet view optimized for fast human scanning.
        """
        return WorldSheetView(
            chapter_label=f"Chapter {state.chapter_index}",
            entity_sections=tuple(
                PresentationSection(
                    title=f"{entity.display_name} ({entity.entity_type})",
                    items=self._world_entity_items(entity),
                )
                for entity in state.entities
            ),
            evidence_summary=self._world_evidence_summary(state),
        )

    @staticmethod
    def _facts_by_attribute(
        facts: tuple[CanonCharacterFact, ...],
    ) -> dict[str, tuple[CanonCharacterFact, ...]]:
        """Group character facts by attribute."""
        grouped: dict[str, list[CanonCharacterFact]] = {}
        for fact in facts:
            grouped.setdefault(fact.attribute, []).append(fact)

        return {
            attribute: tuple(attribute_facts)
            for attribute, attribute_facts in grouped.items()
        }

    @staticmethod
    def _subtitle(facts_by_attribute: dict[str, tuple[CanonCharacterFact, ...]]) -> str:
        """Build a compact character subtitle."""
        parts: list[str] = []
        for attribute in ("role", "department", "academic_year"):
            facts = facts_by_attribute.get(attribute, ())
            if facts:
                parts.append(facts[-1].value)

        return " | ".join(parts) or "Unknown"

    @staticmethod
    def _section(
        title: str,
        facts_by_attribute: dict[str, tuple[CanonCharacterFact, ...]],
        attributes: tuple[str, ...],
    ) -> PresentationSection:
        """Build a section from matching fact attributes."""
        items = tuple(
            fact.value
            for attribute in attributes
            for fact in facts_by_attribute.get(attribute, ())
        )
        return PresentationSection(
            title=title,
            items=PresentationEngine._items_or_unknown(items),
        )

    @staticmethod
    def _recent_changes(facts: tuple[CanonCharacterFact, ...]) -> PresentationSection:
        """Build recent changes section from valid-from chapters."""
        items = tuple(
            f"{fact.valid_from_chapter_id}: {fact.attribute} -> {fact.value}"
            for fact in facts[-8:]
        )
        return PresentationSection(
            title="Recent Changes",
            items=PresentationEngine._items_or_unknown(items),
        )

    @staticmethod
    def _evidence_summary(facts: tuple[CanonCharacterFact, ...]) -> str:
        """Return compact evidence summary."""
        if not facts:
            return "0 verified facts"

        average_confidence = sum(fact.evidence.confidence for fact in facts) / len(facts)
        return f"{len(facts)} verified facts | Confidence {average_confidence:.0%}"

    @staticmethod
    def _scene_evidence_summary(context: CanonSceneContext) -> str:
        """Return compact scene evidence summary."""
        evidence_ids = {fact.evidence_id for fact in context.active_facts}
        evidence_ids.update(relationship.evidence_id for relationship in context.relationships)
        return f"{len(evidence_ids)} verified evidence references"

    @staticmethod
    def _location_items(context: CanonSceneContext) -> tuple[str, ...]:
        """Return likely location labels from active facts."""
        locations = tuple(
            fact.value
            for fact in context.active_facts
            if fact.attribute in {"current_location", "location", "territory"}
        )
        return PresentationEngine._items_or_unknown(locations)

    @staticmethod
    def _prompt_lines(prompt: str) -> tuple[str, ...]:
        """Return compact prompt lines for presentation."""
        lines = (
            PresentationEngine._shorten(line.strip())
            for line in prompt.splitlines()
            if line.strip()
        )
        return tuple(PresentationEngine._unique_values(lines)[:15])

    @staticmethod
    def _world_entity_items(entity: WorldEntityState) -> tuple[str, ...]:
        """Return readable world entity facts and relationships."""
        fact_items = tuple(
            f"{fact.attribute}: {fact.value}"
            for fact in entity.facts
        )
        relationship_items = tuple(
            (
                f"{relationship.source_entity_id} "
                f"{relationship.relationship_type} "
                f"{relationship.target_entity_id}"
            )
            for relationship in entity.relationships
        )
        return PresentationEngine._items_or_unknown(fact_items + relationship_items)

    @staticmethod
    def _world_evidence_summary(state: WorldState) -> str:
        """Return compact world evidence summary."""
        evidence_ids = {
            fact.evidence.evidence_id
            for entity in state.entities
            for fact in entity.facts
        }
        evidence_ids.update(
            relationship.evidence_id
            for entity in state.entities
            for relationship in entity.relationships
        )
        return f"{len(evidence_ids)} verified evidence references"

    @staticmethod
    def _items_or_unknown(items: Iterable[str]) -> tuple[str, ...]:
        """Return deduplicated display items or Unknown."""
        unique_items = PresentationEngine._unique_values(items)
        return tuple(unique_items) or ("Unknown",)

    @staticmethod
    def _shorten(value: str, width: int = 160) -> str:
        """Return compact one-line presentation text."""
        normalized_value = " ".join(value.split())
        if not normalized_value:
            return "Unknown"

        return textwrap.shorten(normalized_value, width=width, placeholder="...")

    @staticmethod
    def _unique_values(values: Iterable[str]) -> list[str]:
        """Return non-empty values in first-seen order without duplicates."""
        unique: dict[str, None] = {}
        for value in values:
            if value:
                unique.setdefault(value, None)

        return list(unique)

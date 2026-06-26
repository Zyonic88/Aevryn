"""Phase 8 prompt builder over Canon Scene Context."""

from __future__ import annotations

import logging
import textwrap
from collections.abc import Iterable

from scenesmith.characters import CanonCharacterCard
from scenesmith.core import Fact, Relationship
from scenesmith.prompts.models import ProductionPack, PromptBundle
from scenesmith.scenes import CanonSceneContext, SceneAnalysis, SceneAnalyzer

logger = logging.getLogger(__name__)

PROMPT_METADATA_ATTRIBUTE_PARTS = frozenset(
    {
        "failure_penalty",
        "penalty",
        "reward",
        "feasibility",
    }
)


class CanonPromptBuilder:
    """Build deterministic prompts from accepted scene context."""

    def __init__(self, analyzer: SceneAnalyzer | None = None) -> None:
        """Create a Canon Prompt Builder.

        Parameters:
            analyzer: Optional Scene Analyzer used for production-focused prompts.
        """
        self._analyzer = analyzer or SceneAnalyzer()

    def build_bundle(self, context: CanonSceneContext) -> PromptBundle:
        """Build all prompt types from scene context.

        Parameters:
            context: Scene context built from accepted Canon state.

        Returns:
            Prompt bundle with image, narration, camera, and animation prompts.
        """
        analysis = self._analyzer.analyze(context)
        bundle = PromptBundle(
            image_prompt=self.build_image_prompt(context, analysis),
            narration_prompt=self.build_narration_prompt(context, analysis),
            camera_prompt=self.build_camera_prompt(context, analysis),
            animation_prompt=self.build_animation_prompt(context, analysis),
        )
        logger.debug(
            "canon_prompt_bundle_built",
            extra={"scene_id": context.scene.scene_id},
        )
        return bundle

    def build_production_pack(self, context: CanonSceneContext) -> ProductionPack:
        """Build a complete production pack from scene context."""
        analysis = self._analyzer.analyze(context)
        bundle = PromptBundle(
            image_prompt=self.build_image_prompt(context, analysis),
            narration_prompt=self.build_narration_prompt(context, analysis),
            camera_prompt=self.build_camera_prompt(context, analysis),
            animation_prompt=self.build_animation_prompt(context, analysis),
        )
        return ProductionPack(
            scene_id=analysis.scene_id,
            scene_summary=analysis.summary,
            purpose=analysis.purpose,
            conflict=analysis.conflict,
            mood=analysis.mood,
            visual_highlights=analysis.visual_highlights,
            character_goals=analysis.character_goals,
            important_objects=analysis.important_objects,
            environment_summary=analysis.environment_summary,
            continuity_notes=analysis.continuity_notes,
            forbidden_elements=analysis.forbidden_elements,
            prompt_bundle=bundle,
            analysis=analysis,
        )

    def build_image_prompt(
        self,
        context: CanonSceneContext,
        analysis: SceneAnalysis | None = None,
    ) -> str:
        """Build an image prompt from scene context."""
        analysis = analysis or self._analyzer.analyze(context)
        return self._join_sections(
            (
                "Generate this image using only accepted SceneSmith canon.",
                self._analysis_section(analysis),
                self._character_section(context),
                self._visual_section(analysis),
                self._continuity_guard_section(analysis),
            )
        )

    def build_narration_prompt(
        self,
        context: CanonSceneContext,
        analysis: SceneAnalysis | None = None,
    ) -> str:
        """Build a narration prompt from scene context."""
        analysis = analysis or self._analyzer.analyze(context)
        return self._join_sections(
            (
                "Create narration using only accepted SceneSmith canon.",
                self._analysis_section(analysis),
                "Narrate using only accepted canon facts.",
                self._character_section(context),
                self._continuity_guard_section(analysis),
            )
        )

    def build_camera_prompt(
        self,
        context: CanonSceneContext,
        analysis: SceneAnalysis | None = None,
    ) -> str:
        """Build a camera prompt from scene context."""
        analysis = analysis or self._analyzer.analyze(context)
        return self._join_sections(
            (
                "Create camera direction using only accepted SceneSmith canon.",
                self._analysis_section(analysis),
                "Describe camera framing without inventing new canon.",
                self._character_section(context),
                self._visual_section(analysis),
            )
        )

    def build_animation_prompt(
        self,
        context: CanonSceneContext,
        analysis: SceneAnalysis | None = None,
    ) -> str:
        """Build an animation prompt from scene context."""
        analysis = analysis or self._analyzer.analyze(context)
        return self._join_sections(
            (
                "Create animation direction using only accepted SceneSmith canon.",
                self._analysis_section(analysis),
                "Describe motion using only accepted scene facts.",
                self._visual_section(analysis),
                self._continuity_guard_section(analysis),
            )
        )

    @staticmethod
    def _scene_section(context: CanonSceneContext) -> str:
        """Return scene identity section."""
        return (
            f"Scene: {context.scene.title}\n"
            f"Scene ID: {context.scene.scene_id}\n"
            f"Source Summary: {CanonPromptBuilder._source_summary(context)}"
        )

    @staticmethod
    def _source_summary(context: CanonSceneContext) -> str:
        """Return a concise source summary without replaying the full scene."""
        source_text = " ".join(context.scene.paragraphs).strip()
        if not source_text:
            return "Unknown"

        normalized_text = " ".join(source_text.split())
        return textwrap.shorten(
            normalized_text,
            width=240,
            placeholder="...",
        )

    @staticmethod
    def _analysis_section(analysis: SceneAnalysis) -> str:
        """Return scene analysis section."""
        return "\n".join(
            [
                f"Scene ID: {analysis.scene_id}",
                f"Scene Summary: {CanonPromptBuilder._shorten(analysis.summary)}",
                f"Purpose: {CanonPromptBuilder._shorten(analysis.purpose)}",
                f"Conflict: {CanonPromptBuilder._shorten(analysis.conflict)}",
                f"Mood: {CanonPromptBuilder._shorten(analysis.mood)}",
                f"Environment: {CanonPromptBuilder._shorten(analysis.environment_summary)}",
            ]
        )

    @staticmethod
    def _visual_section(analysis: SceneAnalysis) -> str:
        """Return visual production details."""
        return "\n".join(
            [
                "Visual Highlights:",
                *CanonPromptBuilder._bullet_lines(analysis.visual_highlights),
                "Important Objects:",
                *CanonPromptBuilder._bullet_lines(analysis.important_objects),
                "Character Goals:",
                *CanonPromptBuilder._bullet_lines(analysis.character_goals),
            ]
        )

    @staticmethod
    def _continuity_guard_section(analysis: SceneAnalysis) -> str:
        """Return continuity guardrails."""
        return "\n".join(
            [
                "Continuity Notes:",
                *CanonPromptBuilder._bullet_lines(analysis.continuity_notes[:8]),
                "Forbidden Elements:",
                *CanonPromptBuilder._bullet_lines(analysis.forbidden_elements),
            ]
        )

    @staticmethod
    def _bullet_lines(values: Iterable[str]) -> list[str]:
        """Return bullet lines or Unknown placeholder."""
        lines = [
            f"- {CanonPromptBuilder._shorten(value)}"
            for value in CanonPromptBuilder._unique_values(values)
        ]
        if not lines:
            return ["- Unknown"]

        return lines

    def _character_section(self, context: CanonSceneContext) -> str:
        """Return character section."""
        lines: list[str] = []
        scene_fact_keys = self._scene_fact_keys(context.active_facts)
        for card in context.character_cards:
            lines.append(f"Character: {card.display_name} ({card.character_id})")
            lines.extend(
                self._character_fact_lines(
                    card=card,
                    scene_fact_keys=scene_fact_keys,
                )
            )

        if not lines:
            return "Characters: Unknown"

        return "\n".join(lines)

    @staticmethod
    def _scene_fact_keys(facts: Iterable[Fact]) -> dict[str, set[tuple[str, str]]]:
        """Return scene-relevant fact keys by entity ID."""
        keys: dict[str, set[tuple[str, str]]] = {}
        for fact in facts:
            keys.setdefault(fact.entity_id, set()).add((fact.attribute, fact.value))

        return keys

    @staticmethod
    def _character_fact_lines(
        card: CanonCharacterCard,
        scene_fact_keys: dict[str, set[tuple[str, str]]],
    ) -> list[str]:
        """Return character fact lines."""
        relevant_fact_keys = scene_fact_keys.get(card.character_id, set())
        lines = (
            f"- {fact.attribute}: {CanonPromptBuilder._shorten(fact.value)}"
            for fact in sorted(card.facts, key=lambda fact: fact.attribute)
            if (fact.attribute, fact.value) in relevant_fact_keys
            and not CanonPromptBuilder._is_prompt_metadata_attribute(fact.attribute)
        )
        return CanonPromptBuilder._unique_values(lines)

    @staticmethod
    def _is_prompt_metadata_attribute(attribute: str) -> bool:
        """Return whether an attribute is mechanical metadata for prompt details."""
        normalized_attribute = attribute.lower()
        return any(
            part in normalized_attribute
            for part in PROMPT_METADATA_ATTRIBUTE_PARTS
        )

    @staticmethod
    def _fact_section(facts: Iterable[Fact]) -> str:
        """Return active fact section."""
        lines = [
            f"Fact: {fact.entity_id} {fact.attribute} = {fact.value}"
            for fact in sorted(facts, key=lambda fact: fact.fact_id)
        ]
        if not lines:
            return "Facts: Unknown"

        return "\n".join(lines)

    @staticmethod
    def _relationship_section(relationships: Iterable[Relationship]) -> str:
        """Return relationship section."""
        lines = [
            f"Relationship: {relationship.source_entity_id} "
            f"{relationship.relationship_type} {relationship.target_entity_id}"
            for relationship in sorted(
                relationships,
                key=lambda relationship: relationship.relationship_id,
            )
        ]
        if not lines:
            return "Relationships: Unknown"

        return "\n".join(lines)

    @staticmethod
    def _join_sections(sections: Iterable[str]) -> str:
        """Join prompt sections into stable text."""
        return "\n\n".join(section for section in sections if section.strip())

    @staticmethod
    def _shorten(value: str, width: int = 140) -> str:
        """Return compact one-line prompt text."""
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

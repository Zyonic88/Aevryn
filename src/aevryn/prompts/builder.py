"""Phase 8 prompt builder over Canon Scene Context."""

from __future__ import annotations

import logging
import re
import textwrap
from collections.abc import Iterable

from aevryn.characters import CanonCharacterCard
from aevryn.core import Fact, Relationship
from aevryn.prompts.models import ProductionPack, PromptBundle
from aevryn.scenes import CanonSceneContext, SceneAnalysis, SceneAnalyzer

logger = logging.getLogger(__name__)

PROMPT_METADATA_ATTRIBUTE_PARTS = frozenset(
    {
        "failure_penalty",
        "penalty",
        "reward",
        "feasibility",
    }
)

APPEARANCE_ATTRIBUTE_PARTS = frozenset(
    {
        "appearance",
        "build",
        "clothing",
        "color",
        "complexion",
        "ear",
        "eye",
        "face",
        "hair",
        "height",
        "look",
        "marking",
        "texture",
        "uniform",
        "wing",
    }
)

SCENE_VISUAL_ANCHOR_TERMS = frozenset(
    {
        "armor",
        "banner",
        "bed",
        "blade",
        "bridge",
        "building",
        "car",
        "carriage",
        "cave",
        "chair",
        "city",
        "classroom",
        "clothing",
        "corridor",
        "courtyard",
        "desk",
        "door",
        "dress",
        "field",
        "forest",
        "gate",
        "hall",
        "hangar",
        "hologram",
        "holographic",
        "house",
        "jacket",
        "light",
        "market",
        "podium",
        "projection",
        "room",
        "screen",
        "ship",
        "starship",
        "street",
        "table",
        "teacher",
        "temple",
        "tower",
        "uniform",
        "vehicle",
        "wall",
        "warship",
        "window",
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
                (
                    "Generate this image using only accepted Aevryn canon.\n"
                    "Image generation task: Create one scene image using only "
                    "accepted Aevryn canon. Show the confirmed subjects, setting, "
                    "mood, and objects below. Do not invent character appearance, "
                    "vehicle design, logos, colors, or scenery details that are not "
                    "listed as known canon."
                ),
                self._scene_visual_anchor_section(context),
                self._scene_directive_section(analysis),
                self._image_subject_section(context),
                self._image_setting_section(analysis),
                self._visual_direction_section(analysis),
                self._unknown_visuals_section(context=context, analysis=analysis),
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
                (
                    "Narration task: Write narration using only accepted Aevryn "
                    "canon. Use the scene mood and purpose below to guide tone. "
                    "Do not add backstory, thoughts, dialogue, or descriptions "
                    "that are not supported by canon.\n"
                    "Narrate using only accepted canon facts."
                ),
                self._scene_directive_section(analysis),
                self._narration_direction_section(analysis),
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
                (
                    "Camera direction task: Plan framing and camera movement using "
                    "only accepted Aevryn canon. Let the mood, setting, subject "
                    "relationships, and known objects drive shot choice. Do not "
                    "invent new physical details.\n"
                    "Describe camera framing without inventing new canon."
                ),
                self._scene_directive_section(analysis),
                self._camera_direction_section(analysis),
                self._scene_visual_anchor_section(context),
                self._character_section(context),
                self._visual_direction_section(analysis),
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
                (
                    "Animation direction task: Describe motion, pacing, and animated "
                    "beats using only accepted Aevryn canon. Animate known actions, "
                    "objects, emotions, and environment details. Keep unspecified "
                    "motion minimal and neutral.\n"
                    "Describe motion using only accepted scene facts."
                ),
                self._scene_directive_section(analysis),
                self._animation_direction_section(analysis),
                self._scene_visual_anchor_section(context),
                self._character_section(context),
                self._visual_direction_section(analysis),
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
    def _scene_directive_section(analysis: SceneAnalysis) -> str:
        """Return scene direction shared by prompt types."""
        return "\n".join(
            [
                f"Scene Summary: {CanonPromptBuilder._shorten(analysis.summary, width=220)}",
                f"Scene ID: {analysis.scene_id}",
                f"Purpose: {CanonPromptBuilder._shorten(analysis.purpose)}",
                f"Conflict: {CanonPromptBuilder._shorten(analysis.conflict)}",
                f"Mood and tone: {CanonPromptBuilder._shorten(analysis.mood)}",
                f"Setting: {CanonPromptBuilder._shorten(analysis.environment_summary)}",
            ]
        )

    def _image_subject_section(self, context: CanonSceneContext) -> str:
        """Return subject details for image prompts."""
        lines = ["Subjects and known appearance:"]
        scene_fact_keys = self._scene_fact_keys(context.active_facts)
        for card in context.character_cards:
            lines.append(f"Character: {card.display_name} ({card.character_id})")
            character_lines = self._character_fact_lines(
                card=card,
                scene_fact_keys=scene_fact_keys,
            )
            appearance_lines = [
                line
                for line in character_lines
                if self._is_appearance_attribute(line)
            ]
            other_lines = [
                line
                for line in character_lines
                if not self._is_appearance_attribute(line)
            ][:6]
            if appearance_lines:
                lines.extend(f"  {line}" for line in appearance_lines[:6])
            else:
                lines.append("  - Appearance: Not specified by accepted canon.")
            lines.extend(f"  {line}" for line in other_lines)

        if len(lines) == 1:
            lines.append("- Unknown subjects.")

        return "\n".join(lines)

    @staticmethod
    def _image_setting_section(analysis: SceneAnalysis) -> str:
        """Return image setting guidance."""
        return "\n".join(
            [
                "Setting and atmosphere:",
                f"- Environment: {CanonPromptBuilder._shorten(analysis.environment_summary)}",
                f"- Mood: {CanonPromptBuilder._shorten(analysis.mood)}",
                f"- Conflict pressure: {CanonPromptBuilder._shorten(analysis.conflict)}",
            ]
        )

    @staticmethod
    def _scene_visual_anchor_section(context: CanonSceneContext) -> str:
        """Return compact current-scene visual anchors from source structure."""
        return "\n".join(
            [
                (
                    "Scene-grounded visual anchors "
                    "(prioritize these over retained background facts):"
                ),
                *CanonPromptBuilder._bullet_lines(
                    CanonPromptBuilder._scene_visual_anchors(context)
                ),
            ]
        )

    @staticmethod
    def _scene_visual_anchors(context: CanonSceneContext) -> tuple[str, ...]:
        """Return short visual/action anchors from the current scene only."""
        anchors: list[str] = []
        for sentence in CanonPromptBuilder._scene_sentences(context.scene.paragraphs):
            normalized_sentence = sentence.lower()
            if any(term in normalized_sentence for term in SCENE_VISUAL_ANCHOR_TERMS):
                anchors.append(CanonPromptBuilder._shorten(sentence, width=170))
            if len(anchors) >= 6:
                break

        return tuple(CanonPromptBuilder._unique_values(anchors))

    @staticmethod
    def _scene_sentences(paragraphs: Iterable[str]) -> tuple[str, ...]:
        """Return compact sentence-like units from scene paragraphs."""
        sentences: list[str] = []
        for paragraph in paragraphs:
            normalized_paragraph = " ".join(paragraph.split())
            if not normalized_paragraph:
                continue
            for sentence in re.split(r"(?<=[.!?])\s+", normalized_paragraph):
                stripped_sentence = sentence.strip()
                if stripped_sentence:
                    sentences.append(stripped_sentence)

        return tuple(sentences)

    @staticmethod
    def _visual_direction_section(analysis: SceneAnalysis) -> str:
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
    def _narration_direction_section(analysis: SceneAnalysis) -> str:
        """Return narration-specific direction."""
        return "\n".join(
            [
                "Narration direction:",
                f"- Tone: {CanonPromptBuilder._shorten(analysis.mood)}",
                f"- Focus: {CanonPromptBuilder._shorten(analysis.purpose)}",
                f"- Tension: {CanonPromptBuilder._shorten(analysis.conflict)}",
                "- Style: Clear, scene-focused narration. Explain only what canon supports.",
                "Emotional cues:",
                *CanonPromptBuilder._bullet_lines(analysis.character_emotions),
            ]
        )

    @staticmethod
    def _camera_direction_section(analysis: SceneAnalysis) -> str:
        """Return camera-specific direction."""
        return "\n".join(
            [
                "Camera direction:",
                (
                    "- Establish the setting: "
                    f"{CanonPromptBuilder._shorten(analysis.environment_summary)}"
                ),
                f"- Frame the scene purpose: {CanonPromptBuilder._shorten(analysis.purpose)}",
                f"- Support the mood: {CanonPromptBuilder._shorten(analysis.mood)}",
                "- Use neutral shot language when canon does not specify exact layout.",
                "Camera-visible details:",
                *CanonPromptBuilder._bullet_lines(
                    (
                        *analysis.visual_highlights,
                        *analysis.important_objects,
                    )
                ),
            ]
        )

    @staticmethod
    def _animation_direction_section(analysis: SceneAnalysis) -> str:
        """Return animation-specific direction."""
        return "\n".join(
            [
                "Animation direction:",
                f"- Motion should express: {CanonPromptBuilder._shorten(analysis.purpose)}",
                f"- Pacing and tone: {CanonPromptBuilder._shorten(analysis.mood)}",
                f"- Scene pressure: {CanonPromptBuilder._shorten(analysis.conflict)}",
                "Animate only known changes and details:",
                *CanonPromptBuilder._bullet_lines(
                    (
                        *analysis.changes_introduced,
                        *analysis.visual_highlights,
                        *analysis.important_objects,
                    )
                ),
            ]
        )

    def _unknown_visuals_section(
        self,
        *,
        context: CanonSceneContext,
        analysis: SceneAnalysis,
    ) -> str:
        """Return explicit handling for unknown visual details."""
        unknowns: list[str] = []
        if not any(
            self._is_appearance_attribute(line)
            for card in context.character_cards
            for line in self._character_fact_lines(
                card=card,
                scene_fact_keys=self._scene_fact_keys(context.active_facts),
            )
        ):
            unknowns.append("Character physical appearance is not specified.")
        if not analysis.visual_highlights:
            unknowns.append("Specific visual composition is not specified.")
        if not analysis.environment_summary or analysis.environment_summary == "Unknown":
            unknowns.append("Environment layout is not specified.")
        if not unknowns:
            unknowns.append("Any unlisted visual detail remains unspecified.")
        return "\n".join(
            [
                "Unknown visual handling:",
                *[f"- {unknown}" for unknown in unknowns],
                "- Keep unknown details neutral and do not turn them into new canon.",
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
    def _is_appearance_attribute(line: str) -> bool:
        """Return whether a prompt fact line describes visible appearance."""
        normalized_line = line.lower()
        return any(part in normalized_line for part in APPEARANCE_ATTRIBUTE_PARTS)

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

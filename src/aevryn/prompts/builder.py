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
        "age",
        "appearance",
        "build",
        "clothing",
        "color",
        "complexion",
        "ear",
        "eye",
        "expression",
        "face",
        "gender",
        "hair",
        "height",
        "injury",
        "look",
        "marking",
        "posture",
        "race",
        "scar",
        "species",
        "texture",
        "uniform",
        "wing",
    }
)
VISUAL_IDENTITY_ATTRIBUTE_GROUPS = {
    "age": frozenset({"age"}),
    "build": frozenset({"build", "height"}),
    "clothing": frozenset({"clothing", "uniform"}),
    "eyes": frozenset({"eye"}),
    "face": frozenset({"complexion", "face", "scar"}),
    "gender": frozenset({"gender"}),
    "hair": frozenset({"hair"}),
    "pose": frozenset({"expression", "posture"}),
    "race/species": frozenset({"race", "species"}),
}

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
        "crossed",
        "desk",
        "door",
        "dress",
        "entered",
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
        "looked",
        "market",
        "podium",
        "projection",
        "room",
        "screen",
        "sat",
        "ship",
        "smiled",
        "starship",
        "stood",
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

VISUAL_PRODUCTION_ATTRIBUTE_PARTS = frozenset(
    {
        "appearance",
        "asset",
        "blueprint",
        "condition",
        "design",
        "environment",
        "equipment",
        "expression",
        "gender",
        "item",
        "location",
        "object",
        "posture",
        "race",
        "rank",
        "species",
        "status",
        "territory",
        "title",
        "vehicle",
        "visual",
        "weapon",
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
                    "Image generation task: Create one scene image showing the "
                    "confirmed subjects, setting, mood, and objects below. Do not "
                    "invent character appearance, vehicle design, logos, colors, or "
                    "scenery details that are not listed as known canon."
                ),
                self._scene_production_brief_section(context, analysis),
                self._scene_visual_anchor_section(context),
                self._scene_action_beats_section(context, analysis),
                self._scene_directive_section(analysis),
                self._image_subject_section(context),
                self._visual_identity_known_unknown_section(context),
                self._visual_reference_requirements_section(context),
                self._world_context_section(context),
                self._image_setting_section(analysis),
                self._visual_direction_section(analysis),
                self._composition_section(context, analysis),
                self._lighting_section(analysis),
                self._unknown_visuals_section(context=context, analysis=analysis),
                self._do_not_include_section(context, analysis),
                self._visible_text_guard_section(),
                self._rendering_style_section(),
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
                self._scene_production_brief_section(context, analysis),
                self._scene_action_beats_section(context, analysis),
                self._scene_directive_section(analysis),
                self._narration_direction_section(analysis),
                self._character_section(context),
                self._world_context_section(context),
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
                self._scene_production_brief_section(context, analysis),
                self._scene_action_beats_section(context, analysis),
                self._scene_directive_section(analysis),
                self._composition_section(context, analysis),
                self._camera_direction_section(analysis),
                self._scene_visual_anchor_section(context),
                self._character_section(context),
                self._visual_identity_known_unknown_section(context),
                self._visual_reference_requirements_section(context),
                self._world_context_section(context),
                self._visual_direction_section(analysis),
                self._lighting_section(analysis),
                self._visible_text_guard_section(),
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
                self._scene_production_brief_section(context, analysis),
                self._scene_action_beats_section(context, analysis),
                self._scene_directive_section(analysis),
                self._animation_direction_section(analysis),
                self._scene_visual_anchor_section(context),
                self._character_section(context),
                self._visual_identity_known_unknown_section(context),
                self._visual_reference_requirements_section(context),
                self._world_context_section(context),
                self._visual_direction_section(analysis),
                self._do_not_include_section(context, analysis),
                self._visible_text_guard_section(),
                self._continuity_guard_section(analysis),
            )
        )

    @staticmethod
    def _scene_section(context: CanonSceneContext) -> str:
        """Return scene identity section."""
        return (
            f"Scene: {context.scene.title}\n"
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
            lines.append(f"Character: {card.display_name}")
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

    def _visual_identity_known_unknown_section(self, context: CanonSceneContext) -> str:
        """Return per-character visual identity coverage without inventing details."""
        if not context.character_cards:
            return "Visual identity coverage:\n- No confirmed character visual identity yet."

        lines = ["Visual ID:"]
        scene_fact_keys = self._scene_fact_keys(context.active_facts)
        for card in context.character_cards:
            character_lines = self._character_fact_lines(
                card=card,
                scene_fact_keys=scene_fact_keys,
            )
            known_groups = self._known_visual_identity_groups(character_lines)
            missing_groups = tuple(
                group_name
                for group_name in VISUAL_IDENTITY_ATTRIBUTE_GROUPS
                if group_name not in known_groups
            )
            known_text = (
                ",".join(sorted(known_groups))
                if known_groups
                else "none"
            )
            missing_text = ",".join(missing_groups[:4])
            if len(missing_groups) > 4:
                missing_text = f"{missing_text},other"
            line = f"- {card.display_name}: known {known_text}."
            if missing_text:
                line = f"{line} Missing {missing_text}; neutral."
            lines.append(line)

        lines.append(
            "- Do not guess missing visual traits."
        )
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
    def _scene_production_brief_section(
        context: CanonSceneContext,
        analysis: SceneAnalysis,
    ) -> str:
        """Return a production-first scene brief for generation tools."""
        character_names = tuple(card.display_name for card in context.character_cards)
        visual_anchors = CanonPromptBuilder._scene_visual_anchors(context)
        current_scene = (
            visual_anchors[0]
            if visual_anchors
            else CanonPromptBuilder._source_summary(context)
        )
        return "\n".join(
            [
                "Scene production brief:",
                f"- Current scene moment: {CanonPromptBuilder._shorten(current_scene, width=190)}",
                f"- Primary setting: {CanonPromptBuilder._shorten(analysis.environment_summary)}",
                (
                    "- Characters present: "
                    f"{', '.join(character_names) if character_names else 'Unknown'}"
                ),
                f"- Scene purpose: {CanonPromptBuilder._shorten(analysis.purpose)}",
                (
                    "- Generation priority: depict the current scene moment before "
                    "retained background canon."
                ),
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
    def _scene_action_beats_section(
        context: CanonSceneContext,
        analysis: SceneAnalysis,
    ) -> str:
        """Return bounded canon-backed action beats for production prompts."""
        return "\n".join(
            [
                "Current scene action beats:",
                *CanonPromptBuilder._bullet_lines(
                    CanonPromptBuilder._scene_action_beats(context, analysis)
                ),
            ]
        )

    @staticmethod
    def _scene_action_beats(
        context: CanonSceneContext,
        analysis: SceneAnalysis,
    ) -> tuple[str, ...]:
        """Return short canon-backed beats without storing source prose."""
        display_names = CanonPromptBuilder._entity_display_names(context)
        beats: list[str] = []
        for fact in sorted(context.active_facts, key=lambda fact: fact.fact_id):
            if CanonPromptBuilder._is_prompt_metadata_attribute(fact.attribute):
                continue
            beats.append(
                CanonPromptBuilder._shorten(
                    CanonPromptBuilder._world_fact_line(fact, display_names=display_names),
                    width=96,
                )
            )
            if len(beats) >= 3:
                break
        if len(beats) < 3:
            beats.extend(
                (
                    f"Scene purpose: {CanonPromptBuilder._shorten(analysis.purpose)}",
                    f"Scene pressure: {CanonPromptBuilder._shorten(analysis.conflict)}",
                    f"Scene tone: {CanonPromptBuilder._shorten(analysis.mood)}",
                )
            )

        return tuple(CanonPromptBuilder._unique_values(beats)[:3])

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

    def _world_context_section(self, context: CanonSceneContext) -> str:
        """Return scene-relevant world, location, item, and relationship context."""
        character_ids = {card.character_id for card in context.character_cards}
        display_names = self._entity_display_names(context)
        lines = ["World and scene object context:"]
        world_fact_lines = [
            self._world_fact_line(fact, display_names=display_names)
            for fact in sorted(context.active_facts, key=lambda fact: fact.fact_id)
            if fact.entity_id not in character_ids
            and self._is_visual_production_attribute(fact.attribute)
        ]
        relationship_lines = [
            self._relationship_prompt_line(relationship, display_names=display_names)
            for relationship in sorted(
                context.relationships,
                key=lambda relationship: relationship.relationship_id,
            )
        ]
        lines.extend(
            f"- {line}"
            for line in self._unique_values((*world_fact_lines, *relationship_lines))[:10]
        )

        if len(lines) == 1:
            lines.append("- No scene-specific world details accepted yet.")

        return "\n".join(lines)

    def _visual_reference_requirements_section(self, context: CanonSceneContext) -> str:
        """Return mandatory visual references when Canon provides concrete details."""
        display_names = self._entity_display_names(context)
        scene_fact_keys = self._scene_fact_keys(context.active_facts)
        lines: list[str] = []
        scene_anchors = self._scene_visual_anchors(context)
        if scene_anchors:
            lines.append("Setting anchors: " + "; ".join(scene_anchors[:3]))
        for card in context.character_cards:
            appearance_lines = [
                line.removeprefix("- ")
                for line in self._character_fact_lines(
                    card=card,
                    scene_fact_keys=scene_fact_keys,
                )
                if self._is_appearance_attribute(line)
            ][:4]
            if appearance_lines:
                lines.append(
                    f"{card.display_name} appearance: " + "; ".join(appearance_lines)
                )

        character_ids = {card.character_id for card in context.character_cards}
        world_visual_lines = [
            self._world_fact_line(fact, display_names=display_names)
            for fact in sorted(context.active_facts, key=lambda fact: fact.fact_id)
            if fact.entity_id not in character_ids
            and self._is_visual_production_attribute(fact.attribute)
        ][:4]
        lines.extend(world_visual_lines)
        unique_lines = self._unique_values(lines)
        if not unique_lines:
            return ""

        return "\n".join(
            [
                "Visual reference requirements:",
                *[f"- {self._shorten(line, width=150)}" for line in unique_lines],
                "- Treat these as required references; keep unspecified traits neutral.",
            ]
        )

    @staticmethod
    def _composition_section(
        context: CanonSceneContext,
        analysis: SceneAnalysis,
    ) -> str:
        """Return composition guidance without inventing layout details."""
        character_count = len(context.character_cards)
        subject_guidance = (
            "Frame the confirmed character as the primary subject."
            if character_count == 1
            else "Frame the confirmed characters without adding extras."
            if character_count > 1
            else "Frame the confirmed scene environment without adding characters."
        )
        visual_anchors = CanonPromptBuilder._scene_visual_anchors(context)
        anchor_focus = (
            CanonPromptBuilder._shorten(visual_anchors[0])
            if visual_anchors
            else CanonPromptBuilder._shorten(analysis.environment_summary)
        )
        return "\n".join(
            [
                "Composition:",
                f"- Primary visual focus: {anchor_focus}",
                f"- Subject placement: {subject_guidance}",
                "- Arrange important objects only if they are listed as scene-relevant.",
                "- Keep the scene readable instead of adding decorative background detail.",
            ]
        )

    @staticmethod
    def _lighting_section(analysis: SceneAnalysis) -> str:
        """Return physical lighting guidance that does not redefine mood."""
        return "\n".join(
            [
                "Lighting:",
                (
                    "- Use physical lighting implied by the accepted setting: "
                    f"{CanonPromptBuilder._shorten(analysis.environment_summary)}"
                ),
                "- If lighting is not stated by canon, use neutral readable lighting.",
                (
                    "- Support the mood without changing facts: "
                    f"{CanonPromptBuilder._shorten(analysis.mood)}"
                ),
            ]
        )

    @staticmethod
    def _rendering_style_section() -> str:
        """Return style guidance that stays subordinate to canon facts."""
        return "\n".join(
            [
                "Rendering style:",
                "- Canon-preserving production image.",
                "- Clear subject and environment separation.",
                "- Style must not override accepted Canon.",
                "- Do not add watermark, credits, decorative text, or UI overlays.",
            ]
        )

    @staticmethod
    def _visible_text_guard_section() -> str:
        """Return guidance that prevents prompt metadata from becoming image text."""
        return "\n".join(
            [
                "Visible text and labels:",
                (
                    "- Do not render names, entity IDs, project labels, scene titles, "
                    "prompt headings, captions, subtitles, or UI panels."
                ),
                (
                    "- If a screen, sign, book, interface, or blueprint is canon, show it "
                    "without readable text unless exact text is accepted canon."
                ),
                (
                    "- Do not turn department, role, goal, or asset names into badges, "
                    "signs, hologram labels, or clothing text."
                ),
            ]
        )

    @staticmethod
    def _world_fact_line(fact: Fact, *, display_names: dict[str, str]) -> str:
        """Return a compact world fact line for production prompts."""
        return (
            f"{CanonPromptBuilder._entity_label(fact.entity_id, display_names)} "
            f"{CanonPromptBuilder._attribute_label(fact.attribute)}: "
            f"{CanonPromptBuilder._shorten(fact.value)}"
        )

    @staticmethod
    def _relationship_prompt_line(
        relationship: Relationship,
        *,
        display_names: dict[str, str],
    ) -> str:
        """Return a compact relationship line for production prompts."""
        return (
            f"{CanonPromptBuilder._entity_label(relationship.source_entity_id, display_names)} "
            f"{CanonPromptBuilder._attribute_label(relationship.relationship_type)} "
            f"{CanonPromptBuilder._entity_label(relationship.target_entity_id, display_names)}"
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
    def _known_visual_identity_groups(character_lines: Iterable[str]) -> tuple[str, ...]:
        """Return visual identity groups backed by prompt-visible character facts."""
        known_groups: list[str] = []
        for line in character_lines:
            normalized_line = line.lower()
            for group_name, attribute_parts in VISUAL_IDENTITY_ATTRIBUTE_GROUPS.items():
                if any(part in normalized_line for part in attribute_parts):
                    known_groups.append(group_name)

        return tuple(CanonPromptBuilder._unique_values(known_groups))

    @staticmethod
    def _do_not_include_section(
        context: CanonSceneContext,
        analysis: SceneAnalysis,
    ) -> str:
        """Return generation exclusions that protect scene fidelity."""
        del context
        return "\n".join(
            [
                "Do not include unless supported by this scene:",
                "- Later canon objects or rewards that are not visible in the current scene.",
                "- Extra characters, officers, crowds, logos, uniforms, or vehicles.",
                (
                    "- Detailed faces, hair, body type, race, or gender markers "
                    "unless canon states them."
                ),
                "- Background battles, exterior vistas, or technical diagrams unless listed above.",
                *CanonPromptBuilder._bullet_lines(analysis.forbidden_elements),
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
            lines.append(f"Character: {card.display_name}")
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
        """Return character fact lines for prompt context.

        Stable visual identity facts come from the character card even when they
        were established in an earlier scene. Other facts remain scene-relevant
        so production prompts preserve appearance without replaying the whole
        character sheet.
        """
        relevant_fact_keys = scene_fact_keys.get(card.character_id, set())
        lines = (
            (
                "- "
                f"{CanonPromptBuilder._attribute_label(fact.attribute)}: "
                f"{CanonPromptBuilder._shorten(fact.value)}"
            )
            for fact in sorted(card.facts, key=lambda fact: fact.attribute)
            if (
                (fact.attribute, fact.value) in relevant_fact_keys
                or CanonPromptBuilder._is_appearance_attribute(fact.attribute)
            )
            and not CanonPromptBuilder._is_prompt_metadata_attribute(fact.attribute)
        )
        return CanonPromptBuilder._unique_values(lines)

    @staticmethod
    def _is_appearance_attribute(line: str) -> bool:
        """Return whether a prompt fact line describes visible appearance."""
        tokens = tuple(
            token
            for token in re.split(r"[^a-z0-9]+", line.lower())
            if token
        )
        return any(
            token == part or token.startswith(part)
            for token in tokens
            for part in APPEARANCE_ATTRIBUTE_PARTS
        )

    @staticmethod
    def _is_prompt_metadata_attribute(attribute: str) -> bool:
        """Return whether an attribute is mechanical metadata for prompt details."""
        normalized_attribute = attribute.lower()
        return any(
            part in normalized_attribute
            for part in PROMPT_METADATA_ATTRIBUTE_PARTS
        )

    @staticmethod
    def _is_visual_production_attribute(attribute: str) -> bool:
        """Return whether a world fact helps image or video generation."""
        normalized_attribute = attribute.lower()
        return any(
            part in normalized_attribute
            for part in VISUAL_PRODUCTION_ATTRIBUTE_PARTS
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
    def _entity_display_names(context: CanonSceneContext) -> dict[str, str]:
        """Return human display names for entities available in scene context."""
        display_names = {
            card.character_id: card.display_name
            for card in context.character_cards
            if card.display_name
        }
        for fact in context.active_facts:
            if fact.attribute == "display_name" and fact.value.strip():
                display_names.setdefault(fact.entity_id, fact.value.strip())

        return display_names

    @staticmethod
    def _entity_label(entity_id: str, display_names: dict[str, str]) -> str:
        """Return a prompt-safe human label for an entity."""
        display_name = display_names.get(entity_id)
        if display_name:
            return CanonPromptBuilder._shorten(display_name)

        return CanonPromptBuilder._attribute_label(entity_id)

    @staticmethod
    def _attribute_label(attribute: str) -> str:
        """Return a human-readable prompt label from a machine token."""
        words = [
            word
            for word in re.split(r"[_\s]+", attribute.strip())
            if word and word not in {"character", "entity", "item", "location"}
        ]
        if not words:
            return attribute

        return " ".join(word.capitalize() for word in words)

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

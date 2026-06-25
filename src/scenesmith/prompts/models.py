"""Core data models for the Prompt Engine."""

from __future__ import annotations

from dataclasses import dataclass

from scenesmith.scenes import SceneAnalysis


@dataclass(frozen=True, slots=True)
class PromptBundle:
    """Production-ready prompts derived from one scene context.

    Parameters:
        image_prompt: Prompt text for image generation tools.
        narration_prompt: Prompt text for narration tools.
        camera_prompt: Prompt text for camera direction.
        animation_prompt: Prompt text for animation direction.
    """

    image_prompt: str
    narration_prompt: str
    camera_prompt: str
    animation_prompt: str


@dataclass(frozen=True, slots=True)
class ProductionPack:
    """Production-ready scene package derived from Canon and Scene Analysis."""

    scene_id: str
    scene_summary: str
    purpose: str
    conflict: str
    mood: str
    visual_highlights: tuple[str, ...]
    character_goals: tuple[str, ...]
    important_objects: tuple[str, ...]
    environment_summary: str
    continuity_notes: tuple[str, ...]
    forbidden_elements: tuple[str, ...]
    prompt_bundle: PromptBundle
    analysis: SceneAnalysis

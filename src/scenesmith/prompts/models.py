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

    def __post_init__(self) -> None:
        """Validate generated prompt text fields."""
        _require_text(self.image_prompt, "Image prompt")
        _require_text(self.narration_prompt, "Narration prompt")
        _require_text(self.camera_prompt, "Camera prompt")
        _require_text(self.animation_prompt, "Animation prompt")


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

    def __post_init__(self) -> None:
        """Validate production-pack identity and required human fields."""
        _require_machine_token(self.scene_id, "Production pack scene ID")
        if self.analysis.scene_id != self.scene_id:
            raise ValueError("Production pack analysis must match scene ID.")
        _require_text(self.scene_summary, "Production pack scene summary")
        _require_text(self.purpose, "Production pack purpose")
        _require_text(self.conflict, "Production pack conflict")
        _require_text(self.mood, "Production pack mood")
        for field_name, values in (
            ("Production pack visual highlight", self.visual_highlights),
            ("Production pack character goal", self.character_goals),
            ("Production pack important object", self.important_objects),
            ("Production pack continuity note", self.continuity_notes),
            ("Production pack forbidden element", self.forbidden_elements),
        ):
            for value in values:
                _require_text(value, field_name)
            _require_unique_values(values, f"{field_name}s")
        _require_text(
            self.environment_summary,
            "Production pack environment summary",
        )


def _require_text(value: str, field_name: str) -> None:
    """Validate a required human-readable text field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a required whitespace-free machine token."""
    _require_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _require_unique_values(values: tuple[str, ...], field_name: str) -> None:
    """Validate that visible production-pack rows are not duplicated."""
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique.")

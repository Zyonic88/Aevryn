"""Human-readable view models for SceneSmith presentation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PresentationSection:
    """Named section in a human-readable SceneSmith view."""

    title: str
    items: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CharacterProfileView:
    """Human-readable character profile view model."""

    character_id: str
    display_name: str
    subtitle: str
    status: PresentationSection
    current_goal: PresentationSection
    current_equipment: PresentationSection
    current_abilities: PresentationSection
    current_assets: PresentationSection
    territory: PresentationSection
    relationships: PresentationSection
    current_limitations: PresentationSection
    recent_changes: PresentationSection
    evidence_summary: str


@dataclass(frozen=True, slots=True)
class SceneSheetView:
    """Human-readable scene sheet view model."""

    scene_id: str
    title: str
    chapter_label: str
    location: PresentationSection
    characters_present: PresentationSection
    mood: PresentationSection
    purpose: PresentationSection
    visual_highlights: PresentationSection
    continuity_changes: PresentationSection
    environment: PresentationSection
    evidence_summary: str


@dataclass(frozen=True, slots=True)
class ProductionPackView:
    """Human-readable production pack view model."""

    scene: SceneSheetView
    image_prompt: PresentationSection
    narration_prompt: PresentationSection
    camera_prompt: PresentationSection
    animation_prompt: PresentationSection


@dataclass(frozen=True, slots=True)
class WorldSheetView:
    """Human-readable world sheet view model."""

    chapter_label: str
    entity_sections: tuple[PresentationSection, ...]
    evidence_summary: str

"""Human-readable view models for Aevryn presentation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PresentationSection:
    """Named section in a human-readable Aevryn view."""

    title: str
    items: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate section title and display items."""
        normalized_title = _normalized_text(self.title, "Presentation section title")
        normalized_items = tuple(
            _normalized_text(item, "Presentation section item")
            for item in self.items
        )
        object.__setattr__(self, "title", normalized_title)
        object.__setattr__(self, "items", normalized_items)
        if len(normalized_items) != len(set(normalized_items)):
            raise ValueError("Presentation section items must be unique.")


@dataclass(frozen=True, slots=True)
class CharacterProfileView:
    """Human-readable character profile view model."""

    character_id: str
    display_name: str
    subtitle: str
    race: PresentationSection
    gender: PresentationSection
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

    def __post_init__(self) -> None:
        """Validate required character profile view fields."""
        _require_machine_token(self.character_id, "Character profile ID")
        _require_text(self.display_name, "Character profile display name")
        _require_text(self.subtitle, "Character profile subtitle")
        _require_text(self.evidence_summary, "Character profile evidence summary")


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

    def __post_init__(self) -> None:
        """Validate required scene sheet view fields."""
        _require_machine_token(self.scene_id, "Scene sheet ID")
        _require_text(self.title, "Scene sheet title")
        _require_machine_token(self.chapter_label, "Scene sheet chapter label")
        _require_text(self.evidence_summary, "Scene sheet evidence summary")


@dataclass(frozen=True, slots=True)
class ProductionPackView:
    """Human-readable production pack view model."""

    scene: SceneSheetView
    image_prompt: PresentationSection
    narration_prompt: PresentationSection
    camera_prompt: PresentationSection
    animation_prompt: PresentationSection

    def __post_init__(self) -> None:
        """Validate prompt-pack section titles are unique."""
        _require_unique_section_titles(
            (
                self.image_prompt,
                self.narration_prompt,
                self.camera_prompt,
                self.animation_prompt,
            ),
            "Production pack",
        )


@dataclass(frozen=True, slots=True)
class WorldSheetView:
    """Human-readable world sheet view model."""

    chapter_label: str
    entity_sections: tuple[PresentationSection, ...]
    evidence_summary: str

    def __post_init__(self) -> None:
        """Validate required world sheet view fields."""
        _require_text(self.chapter_label, "World sheet chapter label")
        _require_text(self.evidence_summary, "World sheet evidence summary")
        _require_unique_section_titles(self.entity_sections, "World sheet")


def _require_text(value: str, field_name: str) -> None:
    """Validate a required human-readable text field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


def _normalized_text(value: str, field_name: str) -> str:
    """Return normalized human-readable text or raise if it is blank."""
    _require_text(value, field_name)
    return " ".join(value.split())


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate a required whitespace-free machine token."""
    _require_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _require_unique_section_titles(
    sections: tuple[PresentationSection, ...],
    view_name: str,
) -> None:
    """Validate that one view does not repeat visible section titles."""
    titles = [section.title for section in sections]
    if len(titles) != len(set(titles)):
        raise ValueError(f"{view_name} section titles must be unique.")

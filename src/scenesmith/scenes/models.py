"""Core data models for the Scene Engine."""

from __future__ import annotations

from dataclasses import dataclass

from scenesmith.canon import CanonFactVersion, StoryPosition
from scenesmith.characters import CharacterCard
from scenesmith.timeline import TimelineEvent, TimelineScene, TimelineStateChange


@dataclass(frozen=True, slots=True)
class SceneEnvironmentSnapshot:
    """Canon-backed environment state for a scene.

    Parameters:
        entity_id: Permanent canon ID for the environment entity.
        facts: Canon facts active at the scene position.
    """

    entity_id: str
    facts: dict[str, CanonFactVersion]

    def __post_init__(self) -> None:
        """Validate environment snapshot identity and fact mapping."""
        _require_machine_token(self.entity_id, "Scene environment entity ID")
        for attribute, fact in self.facts.items():
            _require_machine_token(attribute, "Scene environment fact key")
            if attribute != fact.attribute:
                raise ValueError(
                    "Scene environment fact keys must match fact attributes."
                )


@dataclass(frozen=True, slots=True)
class SceneContext:
    """Scene-ready context assembled from core engines.

    Parameters:
        position: Story position represented by the context.
        scene: Timeline scene metadata.
        characters: Character cards present in the scene.
        environment: Environment snapshots relevant to the scene.
        events: Timeline events at the scene position.
        active_state_changes: Timeline state changes active at the scene position.
    """

    position: StoryPosition
    scene: TimelineScene
    characters: tuple[CharacterCard, ...]
    environment: tuple[SceneEnvironmentSnapshot, ...]
    events: tuple[TimelineEvent, ...]
    active_state_changes: tuple[TimelineStateChange, ...]

    def __post_init__(self) -> None:
        """Validate scene context consistency."""
        if self.scene.position != self.position:
            raise ValueError("Scene context position must match scene position.")

        character_ids = [character.character_id for character in self.characters]
        if len(character_ids) != len(set(character_ids)):
            raise ValueError("Scene context cannot contain duplicate characters.")
        for character in self.characters:
            if character.position != self.position:
                raise ValueError(
                    "Scene context character cards must match context position."
                )

        environment_ids = [snapshot.entity_id for snapshot in self.environment]
        if len(environment_ids) != len(set(environment_ids)):
            raise ValueError("Scene context cannot contain duplicate environments.")

        for event in self.events:
            if event.position != self.position:
                raise ValueError("Scene context events must match context position.")

        for state_change in self.active_state_changes:
            if state_change.valid_from > self.position:
                raise ValueError(
                    "Scene context active state changes cannot start in the future."
                )
            if (
                state_change.valid_until is not None
                and state_change.valid_until <= self.position
            ):
                raise ValueError(
                    "Scene context active state changes cannot be expired."
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

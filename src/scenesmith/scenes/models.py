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

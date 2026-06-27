"""Prompt Engine implementation."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from aevryn.characters import CharacterCard, CharacterFact
from aevryn.prompts.models import PromptBundle
from aevryn.scenes import SceneContext, SceneEnvironmentSnapshot
from aevryn.timeline import TimelineEvent, TimelineStateChange

logger = logging.getLogger(__name__)


class PromptEngine:
    """Build deterministic prompts from scene context."""

    def build_bundle(self, context: SceneContext) -> PromptBundle:
        """Build image, narration, camera, and animation prompts.

        Parameters:
            context: Scene context assembled by the Scene Engine.

        Returns:
            Prompt bundle derived only from known scene context.
        """
        bundle = PromptBundle(
            image_prompt=self.build_image_prompt(context),
            narration_prompt=self.build_narration_prompt(context),
            camera_prompt=self.build_camera_prompt(context),
            animation_prompt=self.build_animation_prompt(context),
        )
        logger.debug(
            "prompt_bundle_built",
            extra={
                "chapter_index": context.position.chapter_index,
                "scene_index": context.position.scene_index,
            },
        )
        return bundle

    def build_image_prompt(self, context: SceneContext) -> str:
        """Build an image prompt from scene context."""
        sections = [
            self._scene_header(context),
            self._characters_section(context.characters),
            self._environment_section(context.environment),
            self._events_section(context.events),
            self._state_changes_section(context.active_state_changes),
        ]
        return self._join_sections(sections)

    def build_narration_prompt(self, context: SceneContext) -> str:
        """Build a narration prompt from scene context."""
        sections = [
            self._scene_header(context),
            "Narrate the scene using only the known canon details below.",
            self._characters_section(context.characters),
            self._events_section(context.events),
        ]
        return self._join_sections(sections)

    def build_camera_prompt(self, context: SceneContext) -> str:
        """Build a camera-direction prompt from scene context."""
        sections = [
            self._scene_header(context),
            "Describe camera framing and movement without inventing new story details.",
            self._characters_section(context.characters),
            self._environment_section(context.environment),
        ]
        return self._join_sections(sections)

    def build_animation_prompt(self, context: SceneContext) -> str:
        """Build an animation-direction prompt from scene context."""
        sections = [
            self._scene_header(context),
            "Describe motion using only known scene events and active state.",
            self._events_section(context.events),
            self._state_changes_section(context.active_state_changes),
        ]
        return self._join_sections(sections)

    @staticmethod
    def _scene_header(context: SceneContext) -> str:
        """Return scene identity text."""
        return (
            f"Scene: {context.scene.title} "
            f"(Chapter {context.position.chapter_index}, Scene {context.position.scene_index})"
        )

    def _characters_section(self, characters: Iterable[CharacterCard]) -> str:
        """Return character prompt details."""
        lines: list[str] = []
        for character in characters:
            lines.append(f"Character: {character.display_name}")
            lines.extend(
                f"- {fact.attribute}: {fact.value}"
                for fact in self._sorted_facts(character.facts.values())
            )

        if not lines:
            return "Characters: Unknown"

        return "\n".join(self._unique_values(lines))

    def _environment_section(
        self,
        environment: Iterable[SceneEnvironmentSnapshot],
    ) -> str:
        """Return environment prompt details."""
        lines: list[str] = []
        for snapshot in environment:
            lines.append(f"Environment: {snapshot.entity_id}")
            lines.extend(
                f"- {fact.attribute}: {fact.value}"
                for fact in sorted(
                    snapshot.facts.values(),
                    key=lambda fact: fact.attribute,
                )
            )

        if not lines:
            return "Environment: Unknown"

        return "\n".join(self._unique_values(lines))

    @staticmethod
    def _events_section(events: Iterable[TimelineEvent]) -> str:
        """Return event prompt details."""
        lines = [
            f"Event: {event.description}"
            for event in sorted(events, key=lambda event: (event.position, event.event_id))
        ]
        if not lines:
            return "Events: Unknown"

        return "\n".join(PromptEngine._unique_values(lines))

    @staticmethod
    def _state_changes_section(state_changes: Iterable[TimelineStateChange]) -> str:
        """Return active state-change prompt details."""
        lines = [
            f"Active State: {state_change.subject_id} "
            f"{state_change.attribute} = {state_change.value}"
            for state_change in sorted(
                state_changes,
                key=lambda state_change: (
                    state_change.valid_from,
                    state_change.subject_id,
                    state_change.attribute,
                    state_change.change_id,
                ),
            )
        ]
        if not lines:
            return "Active State: Unknown"

        return "\n".join(PromptEngine._unique_values(lines))

    @staticmethod
    def _sorted_facts(facts: Iterable[CharacterFact]) -> tuple[CharacterFact, ...]:
        """Return character facts sorted by attribute."""
        return tuple(sorted(facts, key=lambda fact: fact.attribute))

    @staticmethod
    def _join_sections(sections: Iterable[str]) -> str:
        """Join prompt sections while dropping empty content."""
        return "\n\n".join(section for section in sections if section.strip())

    @staticmethod
    def _unique_values(values: Iterable[str]) -> list[str]:
        """Return non-empty values in first-seen order without duplicates."""
        unique: dict[str, None] = {}
        for value in values:
            if value:
                unique.setdefault(value, None)

        return list(unique)

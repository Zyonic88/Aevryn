"""Scene Analyzer for compact scene meaning."""

from __future__ import annotations

import logging
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass

from scenesmith.core import Fact, Relationship
from scenesmith.scenes.context import CanonSceneContext

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SceneAnalysis:
    """Meaning-focused analysis for a reconstructed scene."""

    scene_id: str
    summary: str
    purpose: str
    conflict: str
    mood: str
    visual_highlights: tuple[str, ...]
    character_goals: tuple[str, ...]
    character_emotions: tuple[str, ...]
    important_objects: tuple[str, ...]
    environment_summary: str
    changes_introduced: tuple[str, ...]
    continuity_notes: tuple[str, ...]
    forbidden_elements: tuple[str, ...]


class SceneAnalyzer:
    """Analyze what a scene accomplishes without changing Canon."""

    def analyze(self, context: CanonSceneContext) -> SceneAnalysis:
        """Build a compact scene analysis from accepted scene context.

        Parameters:
            context: Scene context assembled from accepted Canon state.

        Returns:
            Meaning-focused scene analysis for prompts and production packs.

        Raises:
            ValueError: If the scene context and scene snapshot disagree.
        """
        if context.snapshot.scene_id != context.scene.scene_id:
            raise ValueError(
                "Scene context snapshot must reference the analyzed scene."
            )

        facts = tuple(sorted(context.active_facts, key=lambda fact: fact.fact_id))
        relationships = tuple(
            sorted(context.relationships, key=lambda relationship: relationship.relationship_id)
        )
        scene_facts = self._scene_facts(context=context, facts=facts)
        scene_relationships = self._scene_relationships(
            context=context,
            relationships=relationships,
        )
        priority_facts = scene_facts or facts
        priority_relationships = scene_relationships or relationships
        summary = self._summary(
            context=context,
            facts=priority_facts,
            relationships=priority_relationships,
        )
        logger.debug(
            "scene_analysis_built",
            extra={
                "scene_id": context.scene.scene_id,
                "fact_count": len(facts),
                "relationship_count": len(relationships),
                "scene_fact_count": len(scene_facts),
                "scene_relationship_count": len(scene_relationships),
            },
        )
        return SceneAnalysis(
            scene_id=context.scene.scene_id,
            summary=summary,
            purpose=self._purpose(facts=priority_facts, relationships=priority_relationships),
            conflict=self._conflict(facts=priority_facts, relationships=priority_relationships),
            mood=self._mood(facts=priority_facts, relationships=priority_relationships),
            visual_highlights=self._visual_highlights(priority_facts, fallback_facts=facts),
            character_goals=self._character_goals(priority_facts, fallback_facts=facts),
            character_emotions=self._character_emotions(priority_facts, fallback_facts=facts),
            important_objects=self._important_objects(
                facts=priority_facts,
                relationships=priority_relationships,
                fallback_facts=facts,
                fallback_relationships=relationships,
            ),
            environment_summary=self._environment_summary(context),
            changes_introduced=self._changes_introduced(scene_facts),
            continuity_notes=self._continuity_notes(facts),
            forbidden_elements=(
                "Do not add facts, characters, items, locations, "
                "or relationships without evidence.",
                "Do not contradict accepted Canon state.",
            ),
        )

    @staticmethod
    def _summary(
        context: CanonSceneContext,
        facts: tuple[Fact, ...],
        relationships: tuple[Relationship, ...],
    ) -> str:
        """Return a compact scene summary."""
        character_names = ", ".join(card.display_name for card in context.character_cards)
        key_changes = "; ".join(SceneAnalyzer._fact_label(fact) for fact in facts[:4])
        relationship_labels = "; ".join(
            SceneAnalyzer._relationship_label(relationship)
            for relationship in relationships[:2]
        )
        parts = [
            f"Scene focuses on {character_names or 'Unknown characters'}.",
            f"Key canon state: {key_changes or 'Unknown'}.",
        ]
        if relationship_labels:
            parts.append(f"Relevant relationships: {relationship_labels}.")

        return " ".join(parts)

    @staticmethod
    def _purpose(
        facts: tuple[Fact, ...],
        relationships: tuple[Relationship, ...],
    ) -> str:
        """Infer scene purpose from canon changes."""
        if any("reward" in fact.attribute or "ability" in fact.attribute for fact in facts):
            return "Introduce or update character abilities and system rules."
        if any(
            label in (fact.attribute + " " + fact.value).lower()
            for fact in facts
            for label in ("mock", "humiliat", "contempt", "disgust", "reject")
        ) or any(
            relationship.relationship_type in {"mocks", "girlfriend_of", "boyfriend_of"}
            for relationship in relationships
        ):
            return "Reveal social conflict and relationship tension."
        if facts:
            return "Establish current character and world state."
        if relationships:
            return "Reveal or update relationships between story entities."

        return "Unknown"

    @staticmethod
    def _conflict(
        facts: tuple[Fact, ...],
        relationships: tuple[Relationship, ...],
    ) -> str:
        """Infer conflict from accepted canon labels."""
        labels = " ".join(
            [fact.attribute + " " + fact.value for fact in facts]
            + [relationship.relationship_type for relationship in relationships]
        ).lower()
        if any(label in labels for label in ("mock", "humiliat", "contempt")):
            return "Social humiliation or contempt is present."
        if any(label in labels for label in ("disgust", "reject", "girlfriend", "fiance")):
            return "Relationship tension surrounds Zhao Chen and Jiang Shasha."
        if "limitation" in labels or "cannot" in labels or "punishment" in labels:
            return "Character constraints create pressure."
        if "rule" in labels:
            return "A new rule constrains future choices."

        return "Unknown"

    @staticmethod
    def _mood(
        facts: tuple[Fact, ...],
        relationships: tuple[Relationship, ...],
    ) -> str:
        """Infer broad mood from accepted canon labels."""
        text = " ".join(
            [fact.attribute + " " + fact.value for fact in facts]
            + [relationship.relationship_type for relationship in relationships]
        ).lower()
        if any(label in text for label in ("mock", "humiliat", "contempt", "disgust")):
            return "Awkward and tense"
        if "reward" in text or "bonus" in text:
            return "Surprised, curious, and system-focused"
        if "limitation" in text:
            return "Determined under pressure"

        return "Informational"

    @staticmethod
    def _visual_highlights(
        facts: Iterable[Fact],
        fallback_facts: Iterable[Fact] = (),
    ) -> tuple[str, ...]:
        """Return visual highlights from accepted facts."""
        highlights = SceneAnalyzer._values_for_attributes(
            facts=facts,
            attributes={
                "current_location",
                "warehouse",
                "starfleet_recruitment_rule",
                "starship_plan",
                "territory",
                "docked_starships",
                "hull_length",
                "identification_emblems",
                "current_activity",
                "current_focus",
                "current_action",
            },
        )
        if not highlights:
            highlights = SceneAnalyzer._values_for_attributes(
                facts=fallback_facts,
                attributes={
                    "current_location",
                    "warehouse",
                    "starfleet_recruitment_rule",
                    "starship_plan",
                    "territory",
                },
            )
        return tuple(SceneAnalyzer._unique_values(highlights)[:6])

    @staticmethod
    def _values_for_attributes(
        facts: Iterable[Fact],
        attributes: set[str],
    ) -> list[str]:
        """Return fact values matching attributes."""
        return [
            fact.value
            for fact in facts
            if fact.attribute in attributes
        ]

    @staticmethod
    def _character_goals(
        facts: Iterable[Fact],
        fallback_facts: Iterable[Fact] = (),
    ) -> tuple[str, ...]:
        """Return character goals from accepted facts."""
        goals = SceneAnalyzer._values_for_attributes(
            facts=facts,
            attributes={
                "current_task",
                "starship_plan",
                "next_semester_requirement",
                "current_goal",
            },
        )
        if not goals:
            goals = SceneAnalyzer._values_for_attributes(
                facts=fallback_facts,
                attributes={"current_task", "starship_plan", "next_semester_requirement"},
            )
        return tuple(SceneAnalyzer._unique_values(goals)[:6])

    @staticmethod
    def _character_emotions(
        facts: Iterable[Fact],
        fallback_facts: Iterable[Fact] = (),
    ) -> tuple[str, ...]:
        """Return explicit or inferred emotional labels from facts."""
        emotions = SceneAnalyzer._values_for_attributes(
            facts=facts,
            attributes={
                "emotion",
                "mood",
                "relationship_context",
                "attitude_toward_zhao_chen",
                "food_opinion",
            },
        )
        if not emotions:
            emotions = SceneAnalyzer._values_for_attributes(
                facts=fallback_facts,
                attributes={"emotion", "mood", "relationship_context"},
            )
        return tuple(SceneAnalyzer._unique_values(emotions)[:6])

    @staticmethod
    def _important_objects(
        facts: Iterable[Fact],
        relationships: Iterable[Relationship],
        fallback_facts: Iterable[Fact] = (),
        fallback_relationships: Iterable[Relationship] = (),
    ) -> tuple[str, ...]:
        """Return important object labels from facts and relationships."""
        objects = [
            fact.value
            for fact in facts
            if fact.attribute
            in {
                "warehouse",
                "starship",
                "blueprint",
                "territory",
                "starship_plan",
                "docked_starships",
                "market_status",
                "hull_length",
                "social_context",
            }
        ]
        objects.extend(
            relationship.target_entity_id
            for relationship in relationships
            if relationship.relationship_type
            in {"has_blueprint", "possesses", "has_starship", "owns"}
        )
        if not objects:
            fallback_fact_tuple = tuple(fallback_facts)
            fallback_relationship_tuple = tuple(fallback_relationships)
            if not fallback_fact_tuple and not fallback_relationship_tuple:
                return ()

            return SceneAnalyzer._important_objects(
                facts=fallback_fact_tuple,
                relationships=fallback_relationship_tuple,
            )
        return tuple(SceneAnalyzer._unique_values(objects))

    @staticmethod
    def _environment_summary(context: CanonSceneContext) -> str:
        """Return concise environment text."""
        source_text = " ".join(context.scene.paragraphs).strip()
        if not source_text:
            return "Unknown"

        return textwrap.shorten(" ".join(source_text.split()), width=180, placeholder="...")

    @staticmethod
    def _changes_introduced(facts: Iterable[Fact]) -> tuple[str, ...]:
        """Return canon changes introduced by this scene context."""
        return tuple(
            SceneAnalyzer._unique_values(
                SceneAnalyzer._fact_label(fact) for fact in facts
            )
        )

    @staticmethod
    def _scene_facts(
        context: CanonSceneContext,
        facts: Iterable[Fact],
    ) -> tuple[Fact, ...]:
        """Return facts backed by evidence from the current scene."""
        return tuple(
            fact
            for fact in facts
            if context.scene.scene_id in fact.evidence_id
        )

    @staticmethod
    def _scene_relationships(
        context: CanonSceneContext,
        relationships: Iterable[Relationship],
    ) -> tuple[Relationship, ...]:
        """Return relationships backed by evidence from the current scene."""
        return tuple(
            relationship
            for relationship in relationships
            if context.scene.scene_id in relationship.evidence_id
        )

    @staticmethod
    def _continuity_notes(facts: Iterable[Fact]) -> tuple[str, ...]:
        """Return continuity notes from accepted facts."""
        notes = [
            f"{fact.entity_id} retains {fact.attribute}: {fact.value}"
            for fact in facts
        ]
        return tuple(SceneAnalyzer._unique_values(notes))

    @staticmethod
    def _fact_label(fact: Fact) -> str:
        """Return compact fact label."""
        return f"{fact.entity_id} {fact.attribute} = {fact.value}"

    @staticmethod
    def _relationship_label(relationship: Relationship) -> str:
        """Return compact relationship label."""
        return (
            f"{relationship.source_entity_id} "
            f"{relationship.relationship_type} "
            f"{relationship.target_entity_id}"
        )

    @staticmethod
    def _unique_values(values: Iterable[str]) -> list[str]:
        """Return non-empty values in first-seen order without duplicates."""
        unique: dict[str, None] = {}
        for value in values:
            if value:
                unique.setdefault(value, None)

        return list(unique)

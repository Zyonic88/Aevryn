"""Scene Analyzer for compact scene meaning."""

from __future__ import annotations

import logging
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass

from aevryn.core import Fact, Relationship
from aevryn.scenes.context import CanonSceneContext

logger = logging.getLogger(__name__)

ANALYSIS_METADATA_ATTRIBUTE_PARTS = frozenset(
    {
        "failure_penalty",
        "penalty",
        "task_reward",
        "feasibility",
    }
)


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

    def __post_init__(self) -> None:
        """Validate required scene analysis fields."""
        _require_machine_token(self.scene_id, "Scene analysis scene ID")
        _require_text(self.summary, "Scene analysis summary")
        _require_text(self.purpose, "Scene analysis purpose")
        _require_text(self.conflict, "Scene analysis conflict")
        _require_text(self.mood, "Scene analysis mood")
        _require_text(self.environment_summary, "Scene analysis environment summary")
        for attribute_name, field_name, values in (
            ("visual_highlights", "Scene analysis visual highlights", self.visual_highlights),
            ("character_goals", "Scene analysis character goals", self.character_goals),
            (
                "character_emotions",
                "Scene analysis character emotions",
                self.character_emotions,
            ),
            ("important_objects", "Scene analysis important objects", self.important_objects),
            (
                "changes_introduced",
                "Scene analysis changes introduced",
                self.changes_introduced,
            ),
            ("continuity_notes", "Scene analysis continuity notes", self.continuity_notes),
            (
                "forbidden_elements",
                "Scene analysis forbidden elements",
                self.forbidden_elements,
            ),
        ):
            normalized_values = tuple(
                _normalized_text(value, "Scene analysis list item")
                for value in values
            )
            object.__setattr__(self, attribute_name, normalized_values)
            _require_unique_values(normalized_values, field_name)


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
        production_facts = self._production_facts(priority_facts)
        production_scene_facts = self._production_facts(scene_facts)
        production_all_facts = self._production_facts(facts)
        display_names = self._entity_display_names(context=context, facts=facts)
        summary = self._summary(
            context=context,
            facts=production_facts,
            relationships=priority_relationships,
            display_names=display_names,
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
            purpose=self._purpose(facts=production_facts, relationships=priority_relationships),
            conflict=self._conflict(facts=production_facts, relationships=priority_relationships),
            mood=self._mood(facts=production_facts, relationships=priority_relationships),
            visual_highlights=self._visual_highlights(
                production_facts,
                fallback_facts=production_all_facts,
            ),
            character_goals=self._character_goals(
                production_facts,
                fallback_facts=production_all_facts,
            ),
            character_emotions=self._character_emotions(
                production_facts,
                fallback_facts=production_all_facts,
            ),
            important_objects=self._important_objects(
                facts=production_facts,
                relationships=priority_relationships,
                fallback_facts=production_all_facts,
                fallback_relationships=relationships,
                display_names=display_names,
            ),
            environment_summary=self._environment_summary(context),
            changes_introduced=self._changes_introduced(
                production_scene_facts,
                display_names=display_names,
            ),
            continuity_notes=self._continuity_notes(
                production_all_facts,
                display_names=display_names,
            ),
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
        display_names: dict[str, str],
    ) -> str:
        """Return a compact scene summary."""
        character_names = ", ".join(card.display_name for card in context.character_cards)
        key_changes = "; ".join(
            SceneAnalyzer._fact_label(fact, display_names=display_names)
            for fact in facts[:4]
        )
        relationship_labels = "; ".join(
            SceneAnalyzer._relationship_label(
                relationship,
                display_names=display_names,
            )
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
    def _production_facts(facts: Iterable[Fact]) -> tuple[Fact, ...]:
        """Return facts suitable for production-facing scene analysis."""
        return tuple(
            fact
            for fact in facts
            if not SceneAnalyzer._is_analysis_metadata_attribute(fact.attribute)
        )

    @staticmethod
    def _is_analysis_metadata_attribute(attribute: str) -> bool:
        """Return whether an attribute is mechanical metadata for analysis."""
        normalized_attribute = attribute.lower()
        return any(
            part in normalized_attribute
            for part in ANALYSIS_METADATA_ATTRIBUTE_PARTS
        )

    @staticmethod
    def _purpose(
        facts: tuple[Fact, ...],
        relationships: tuple[Relationship, ...],
    ) -> str:
        """Infer scene purpose from canon changes."""
        labels = SceneAnalyzer._combined_labels(facts=facts, relationships=relationships)
        if any(label in labels for label in ("challenge", "duel", "contest")):
            return "Advance a direct challenge and the character's current objective."
        if any(label in labels for label in ("trial training", "training", "operation")):
            return "Show active operations, preparation, or readiness."
        if any(label in labels for label in ("crew", "team", "unit", "group")) and any(
            relationship.relationship_type in {"recruits", "commands", "serves_under"}
            for relationship in relationships
        ):
            return "Establish group structure, command, or service obligations."
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
        labels = SceneAnalyzer._combined_labels(facts=facts, relationships=relationships)
        if any(label in labels for label in ("challenge", "duel", "contest")):
            return "A direct challenge creates immediate pressure."
        if "make money" in labels or "resource" in labels or "support" in labels:
            return "Resource pressure affects the character's ability to support others."
        if any(label in labels for label in ("mock", "humiliat", "contempt")):
            return "Social humiliation or contempt is present."
        if any(label in labels for label in ("disgust", "reject", "girlfriend", "fiance")):
            return "Relationship tension affects the characters involved."
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
        text = SceneAnalyzer._combined_labels(facts=facts, relationships=relationships)
        if any(label in text for label in ("trial training", "training", "operation")):
            return "Focused and operational"
        if "light and breezy" in text:
            return "Confident and casual"
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
        highlights = SceneAnalyzer._values_for_attribute_categories(
            facts=facts,
            exact_attributes={
                "current_location",
                "warehouse",
                "territory",
                "hull_length",
                "identification_emblems",
                "current_activity",
                "current_focus",
                "current_action",
            },
            partial_attributes={
                "activity",
                "action",
                "appearance",
                "asset",
                "condition",
                "environment",
                "focus",
                "location",
                "plan",
                "rule",
                "territory",
                "vehicle",
                "visual",
                "warehouse",
            },
        )
        if not highlights:
            highlights = SceneAnalyzer._values_for_attribute_categories(
                facts=fallback_facts,
                exact_attributes={
                    "current_location",
                    "warehouse",
                    "territory",
                },
                partial_attributes={
                    "activity",
                    "environment",
                    "location",
                    "plan",
                    "rule",
                    "territory",
                    "vehicle",
                    "visual",
                    "warehouse",
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
    def _values_for_attribute_categories(
        facts: Iterable[Fact],
        exact_attributes: set[str],
        partial_attributes: set[str],
    ) -> list[str]:
        """Return fact values matching generic attribute categories."""
        values: list[str] = []
        for fact in facts:
            attribute = fact.attribute.lower()
            if attribute in exact_attributes or any(
                partial in attribute for partial in partial_attributes
            ):
                values.append(fact.value)

        return values

    @staticmethod
    def _character_goals(
        facts: Iterable[Fact],
        fallback_facts: Iterable[Fact] = (),
    ) -> tuple[str, ...]:
        """Return character goals from accepted facts."""
        goals = SceneAnalyzer._values_for_attribute_categories(
            facts=facts,
            exact_attributes={
                "active_task",
                "current_task",
                "next_semester_requirement",
                "current_goal",
            },
            partial_attributes={
                "goal",
                "objective",
                "plan",
                "requirement",
                "task",
            },
        )
        if not goals:
            goals = SceneAnalyzer._values_for_attribute_categories(
                facts=fallback_facts,
                exact_attributes={
                    "active_task",
                    "current_task",
                    "next_semester_requirement",
                },
                partial_attributes={
                    "goal",
                    "objective",
                    "plan",
                    "requirement",
                    "task",
                },
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
                "food_opinion",
            },
        )
        emotions.extend(
            SceneAnalyzer._values_for_attribute_categories(
                facts=facts,
                exact_attributes=set(),
                partial_attributes={"attitude_toward"},
            )
        )
        if not emotions:
            emotions = SceneAnalyzer._values_for_attributes(
                facts=fallback_facts,
                attributes={"emotion", "mood", "relationship_context"},
            )
            emotions.extend(
                SceneAnalyzer._values_for_attribute_categories(
                    facts=fallback_facts,
                    exact_attributes=set(),
                    partial_attributes={"attitude_toward"},
                )
            )
        return tuple(SceneAnalyzer._unique_values(emotions)[:6])

    @staticmethod
    def _important_objects(
        facts: Iterable[Fact],
        relationships: Iterable[Relationship],
        fallback_facts: Iterable[Fact] = (),
        fallback_relationships: Iterable[Relationship] = (),
        display_names: dict[str, str] | None = None,
    ) -> tuple[str, ...]:
        """Return important object labels from facts and relationships."""
        display_names = display_names or {}
        objects = [
            fact.value
            for fact in facts
            if SceneAnalyzer._attribute_matches(
                attribute=fact.attribute,
                exact_attributes={
                    "asset",
                    "blueprint",
                    "equipment",
                    "item",
                    "market_status",
                    "social_context",
                    "territory",
                    "vehicle",
                    "warehouse",
                    "weapon",
                },
                partial_attributes={
                    "asset",
                    "blueprint",
                    "equipment",
                    "item",
                    "object",
                    "plan",
                    "prop",
                    "territory",
                    "vehicle",
                    "warehouse",
                    "weapon",
                },
            )
        ]
        objects.extend(
            SceneAnalyzer._entity_label(
                relationship.target_entity_id,
                display_names=display_names,
            )
            for relationship in relationships
            if SceneAnalyzer._relationship_marks_object(relationship.relationship_type)
        )
        if not objects:
            fallback_fact_tuple = tuple(fallback_facts)
            fallback_relationship_tuple = tuple(fallback_relationships)
            if not fallback_fact_tuple and not fallback_relationship_tuple:
                return ()

            return SceneAnalyzer._important_objects(
                facts=fallback_fact_tuple,
                relationships=fallback_relationship_tuple,
                display_names=display_names,
            )
        return tuple(SceneAnalyzer._unique_values(objects))

    @staticmethod
    def _attribute_matches(
        attribute: str,
        exact_attributes: set[str],
        partial_attributes: set[str],
    ) -> bool:
        """Return whether an attribute matches a generic category."""
        normalized_attribute = attribute.lower()
        return normalized_attribute in exact_attributes or any(
            partial in normalized_attribute for partial in partial_attributes
        )

    @staticmethod
    def _relationship_marks_object(relationship_type: str) -> bool:
        """Return whether a relationship points to an important object."""
        normalized_type = relationship_type.lower()
        return normalized_type in {
            "has",
            "has_blueprint",
            "has_equipment",
            "has_item",
            "owns",
            "possesses",
            "uses",
            "wields",
        } or any(
            marker in normalized_type
            for marker in (
                "warehouse",
                "blueprint",
                "equipment",
                "item",
                "object",
                "tool",
                "vehicle",
                "weapon",
            )
        )

    @staticmethod
    def _environment_summary(context: CanonSceneContext) -> str:
        """Return concise environment text."""
        source_text = " ".join(context.scene.paragraphs).strip()
        if not source_text:
            return "Unknown"

        return textwrap.shorten(" ".join(source_text.split()), width=180, placeholder="...")

    @staticmethod
    def _changes_introduced(
        facts: Iterable[Fact],
        *,
        display_names: dict[str, str],
    ) -> tuple[str, ...]:
        """Return canon changes introduced by this scene context."""
        return tuple(
            SceneAnalyzer._unique_values(
                SceneAnalyzer._fact_label(fact, display_names=display_names)
                for fact in facts
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
    def _continuity_notes(
        facts: Iterable[Fact],
        *,
        display_names: dict[str, str],
    ) -> tuple[str, ...]:
        """Return continuity notes from accepted facts."""
        notes = [
            (
                f"{SceneAnalyzer._entity_label(fact.entity_id, display_names=display_names)} "
                f"retains {SceneAnalyzer._attribute_label(fact.attribute)}: {fact.value}"
            )
            for fact in facts
        ]
        return tuple(SceneAnalyzer._unique_values(notes))

    @staticmethod
    def _fact_label(fact: Fact, *, display_names: dict[str, str]) -> str:
        """Return compact fact label."""
        return (
            f"{SceneAnalyzer._entity_label(fact.entity_id, display_names=display_names)} "
            f"{SceneAnalyzer._attribute_label(fact.attribute)} = {fact.value}"
        )

    @staticmethod
    def _relationship_label(
        relationship: Relationship,
        *,
        display_names: dict[str, str],
    ) -> str:
        """Return compact relationship label."""
        source = SceneAnalyzer._entity_label(
            relationship.source_entity_id,
            display_names=display_names,
        )
        target = SceneAnalyzer._entity_label(
            relationship.target_entity_id,
            display_names=display_names,
        )
        return (
            f"{source} "
            f"{SceneAnalyzer._attribute_label(relationship.relationship_type)} "
            f"{target}"
        )

    @staticmethod
    def _entity_display_names(
        *,
        context: CanonSceneContext,
        facts: Iterable[Fact],
    ) -> dict[str, str]:
        """Return human display names for entities visible to analysis."""
        display_names = {
            card.character_id: card.display_name
            for card in context.character_cards
            if card.display_name
        }
        for fact in facts:
            if fact.attribute == "display_name" and fact.value.strip():
                display_names.setdefault(fact.entity_id, fact.value.strip())

        return display_names

    @staticmethod
    def _entity_label(entity_id: str, *, display_names: dict[str, str]) -> str:
        """Return a human-readable entity label."""
        display_name = display_names.get(entity_id)
        if display_name:
            return display_name

        return SceneAnalyzer._attribute_label(entity_id)

    @staticmethod
    def _attribute_label(attribute: str) -> str:
        """Return a human-readable label from a machine token."""
        words = [
            word
            for word in attribute.strip().replace("-", "_").split("_")
            if word and word not in {"character", "entity", "item", "location"}
        ]
        if not words:
            return attribute

        return " ".join(word.capitalize() for word in words)

    @staticmethod
    def _combined_labels(
        facts: tuple[Fact, ...],
        relationships: tuple[Relationship, ...],
    ) -> str:
        """Return searchable fact and relationship labels."""
        return " ".join(
            [fact.attribute + " " + fact.value for fact in facts]
            + [relationship.relationship_type for relationship in relationships]
        ).lower()

    @staticmethod
    def _unique_values(values: Iterable[str]) -> list[str]:
        """Return non-empty values in first-seen order without duplicates."""
        unique: dict[str, None] = {}
        for value in values:
            if value:
                unique.setdefault(value, None)

        return list(unique)


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


def _require_unique_values(values: tuple[str, ...], field_name: str) -> None:
    """Validate that visible analysis rows are not duplicated."""
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique.")

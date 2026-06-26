"""Canon policy helpers for state reconstruction."""

from __future__ import annotations

ADDITIVE_FACT_ATTRIBUTES = frozenset(
    {
        "ability",
        "skill",
    }
)

TRANSIENT_RELATIONSHIP_TYPES = frozenset(
    {
        "antagonizes",
        "arranges",
        "defends",
        "observes",
        "uses",
    }
)

CURRENT_STATE_RELATIONSHIP_TYPES = frozenset(
    {
        "located_at",
    }
)

SCENE_CONTEXT_FACT_ATTRIBUTES = frozenset(
    {
        "ability",
        "active_project",
        "active_task",
        "appearance",
        "authority",
        "clothing",
        "current_activity",
        "current_assets",
        "current_equipment",
        "current_goal",
        "current_interest",
        "current_limitation",
        "current_location",
        "current_mood",
        "current_weapon",
        "display_name",
        "hostility_status",
        "injury",
        "location",
        "mood",
        "promise",
        "role",
        "species",
        "status",
        "title",
        "weapon",
    }
)

SCENE_CONTEXT_FACT_ATTRIBUTE_PARTS = frozenset(
    {
        "activity",
        "armor",
        "asset",
        "condition",
        "equipment",
        "goal",
        "injury",
        "interest",
        "inventory",
        "limitation",
        "location",
        "mood",
        "objective",
        "plan",
        "project",
        "promise",
        "reward",
        "rule",
        "skill",
        "task",
        "vehicle",
        "weapon",
    }
)


def is_additive_fact_attribute(attribute: str) -> bool:
    """Return whether a fact attribute can have multiple active values."""
    return attribute in ADDITIVE_FACT_ATTRIBUTES


def is_transient_relationship_type(relationship_type: str) -> bool:
    """Return whether a relationship should only appear near its evidence."""
    return relationship_type in TRANSIENT_RELATIONSHIP_TYPES


def is_current_state_relationship_type(relationship_type: str) -> bool:
    """Return whether a relationship describes current scene state."""
    return relationship_type in CURRENT_STATE_RELATIONSHIP_TYPES


def is_scene_context_fact_attribute(attribute: str) -> bool:
    """Return whether a fact attribute belongs in scene context views."""
    normalized_attribute = attribute.lower()
    return normalized_attribute in SCENE_CONTEXT_FACT_ATTRIBUTES or any(
        part in normalized_attribute for part in SCENE_CONTEXT_FACT_ATTRIBUTE_PARTS
    )

"""In-memory Canon Database built on the core data model."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from collections.abc import Sequence
from typing import TypeVar

from scenesmith.core import (
    Chapter,
    Character,
    Entity,
    Evidence,
    Fact,
    Relationship,
    StateChange,
    TimelineEvent,
)

T = TypeVar("T")

logger = logging.getLogger(__name__)


class CanonDatabase:
    """Store and version evidence-backed canon records.

    The Canon Database owns storage and retrieval of core canon data. It does
    not extract facts, call AI, parse stories, generate prompts, or write files.
    """

    def __init__(self) -> None:
        """Create an empty in-memory Canon Database."""
        self._chapters: dict[str, Chapter] = {}
        self._entities: dict[str, list[Entity]] = defaultdict(list)
        self._characters: dict[str, list[Character]] = defaultdict(list)
        self._evidence: dict[str, Evidence] = {}
        self._facts: dict[str, Fact] = {}
        self._relationships: dict[str, Relationship] = {}
        self._events: dict[str, TimelineEvent] = {}
        self._state_changes: dict[str, StateChange] = {}

    def store_chapter(self, chapter: Chapter) -> None:
        """Store a chapter for timeline-aware state lookup.

        Parameters:
            chapter: Chapter to store.

        Raises:
            ValueError: If the chapter ID already belongs to different data.
        """
        self._store_unique(
            self._chapters,
            chapter.chapter_id,
            chapter,
            "chapter",
        )

    def store_character(self, character: Character) -> None:
        """Store the first version of a character.

        Parameters:
            character: Character to store.

        Raises:
            ValueError: If the character already exists.
        """
        character_id = character.entity.entity_id
        if self._characters[character_id]:
            raise ValueError(f"Character already exists: {character_id}")

        if self.retrieve_entity(character_id) is None:
            self.store_entity(character.entity)
        self._characters[character_id].append(character)

    def retrieve_character(self, character_id: str) -> Character | None:
        """Retrieve the latest version of a character.

        Parameters:
            character_id: Permanent character entity ID.

        Returns:
            Latest character version, or None if unknown.
        """
        versions = self._characters.get(character_id)
        if not versions:
            return None

        return versions[-1]

    def update_character(self, character: Character) -> None:
        """Append a new version of a character.

        Parameters:
            character: New character version.

        Raises:
            ValueError: If the character has not been stored yet.
        """
        character_id = character.entity.entity_id
        if character_id not in self._characters:
            raise ValueError(f"Unknown character: {character_id}")

        if self.retrieve_character(character_id) == character:
            return

        if self.retrieve_entity(character_id) != character.entity:
            self.update_entity(character.entity)
        self._characters[character_id].append(character)

    def version_character(self, character_id: str) -> Sequence[Character]:
        """Return every stored version of a character.

        Parameters:
            character_id: Permanent character entity ID.

        Returns:
            Immutable sequence of character versions.
        """
        return tuple(self._characters.get(character_id, ()))

    def store_entity(self, entity: Entity) -> None:
        """Store the first version of a generic entity.

        Parameters:
            entity: Entity to store.

        Raises:
            ValueError: If the entity already exists.
        """
        if self._entities[entity.entity_id]:
            raise ValueError(f"Entity already exists: {entity.entity_id}")

        self._entities[entity.entity_id].append(entity)

    def retrieve_entity(self, entity_id: str) -> Entity | None:
        """Retrieve the latest version of a generic entity.

        Parameters:
            entity_id: Permanent entity ID.

        Returns:
            Latest entity version, or None if unknown.
        """
        versions = self._entities.get(entity_id)
        if not versions:
            return None

        return versions[-1]

    def update_entity(self, entity: Entity) -> None:
        """Append a new version of a generic entity.

        Parameters:
            entity: New entity version.

        Raises:
            ValueError: If the entity has not been stored yet.
        """
        if entity.entity_id not in self._entities:
            raise ValueError(f"Unknown entity: {entity.entity_id}")

        if self.retrieve_entity(entity.entity_id) == entity:
            return

        self._entities[entity.entity_id].append(entity)

    def version_entity(self, entity_id: str) -> Sequence[Entity]:
        """Return every stored version of a generic entity.

        Parameters:
            entity_id: Permanent entity ID.

        Returns:
            Immutable sequence of entity versions.
        """
        return tuple(self._entities.get(entity_id, ()))

    def store_evidence(self, evidence: Evidence) -> None:
        """Store an evidence anchor.

        Parameters:
            evidence: Evidence to store.

        Raises:
            ValueError: If the evidence ID already belongs to different data.
        """
        self._store_unique(
            self._evidence,
            evidence.evidence_id,
            evidence,
            "evidence",
        )

    def retrieve_evidence(self, evidence_id: str) -> Evidence | None:
        """Retrieve evidence by ID.

        Parameters:
            evidence_id: Permanent evidence identifier.

        Returns:
            Evidence if known, otherwise None.
        """
        return self._evidence.get(evidence_id)

    def store_fact(self, fact: Fact) -> None:
        """Store an evidence-backed fact.

        Parameters:
            fact: Fact to store.

        Raises:
            ValueError: If the fact references unknown evidence or reuses an
                existing fact ID for different data.
        """
        if fact.evidence_id not in self._evidence:
            raise ValueError(f"Unknown evidence: {fact.evidence_id}")

        self._store_unique(
            self._facts,
            fact.fact_id,
            fact,
            "fact",
        )

    def retrieve_fact(self, fact_id: str) -> Fact | None:
        """Retrieve a fact by ID.

        Parameters:
            fact_id: Permanent fact identifier.

        Returns:
            Fact if known, otherwise None.
        """
        return self._facts.get(fact_id)

    def store_relationship(self, relationship: Relationship) -> None:
        """Store an evidence-backed relationship.

        Parameters:
            relationship: Relationship to store.

        Raises:
            ValueError: If the relationship references unknown evidence or
                reuses an existing relationship ID for different data.
        """
        if relationship.evidence_id not in self._evidence:
            raise ValueError(f"Unknown evidence: {relationship.evidence_id}")

        existing_by_id = self._relationships.get(relationship.relationship_id)
        if existing_by_id is not None:
            if existing_by_id != relationship:
                self._raise_conflicting_record(
                    "relationship",
                    relationship.relationship_id,
                )
            return

        existing_relationship = self._find_relationship_by_semantic_key(relationship)
        if existing_relationship is not None:
            return

        self._relationships[relationship.relationship_id] = relationship

    def retrieve_relationship(self, relationship_id: str) -> Relationship | None:
        """Retrieve a relationship by ID.

        Parameters:
            relationship_id: Permanent relationship identifier.

        Returns:
            Relationship if known, otherwise None.
        """
        return self._relationships.get(relationship_id)

    def retrieve_state_change(self, state_change_id: str) -> StateChange | None:
        """Retrieve a state change by ID.

        Parameters:
            state_change_id: Permanent state-change identifier.

        Returns:
            State change if known, otherwise None.
        """
        return self._state_changes.get(state_change_id)

    def list_relationships_for_entity(self, entity_id: str) -> Sequence[Relationship]:
        """Return relationships connected to an entity.

        Parameters:
            entity_id: Entity ID used as source or target.

        Returns:
            Immutable sequence of matching relationships.
        """
        return tuple(
            relationship
            for relationship in self._relationships.values()
            if relationship.source_entity_id == entity_id
            or relationship.target_entity_id == entity_id
        )

    def _find_relationship_by_semantic_key(
        self,
        relationship: Relationship,
    ) -> Relationship | None:
        """Return an existing relationship with the same semantic connection."""
        for existing_relationship in self._relationships.values():
            if (
                existing_relationship.source_entity_id == relationship.source_entity_id
                and existing_relationship.relationship_type == relationship.relationship_type
                and existing_relationship.target_entity_id == relationship.target_entity_id
            ):
                return existing_relationship

        return None

    def retrieve_current_fact(self, entity_id: str, attribute: str) -> Fact | None:
        """Retrieve the latest stored fact for an entity attribute.

        Parameters:
            entity_id: Entity whose fact should be retrieved.
            attribute: Fact attribute to retrieve.

        Returns:
            Latest fact for that attribute, or None if unknown.
        """
        history = self.retrieve_fact_history(entity_id, attribute)
        if not history:
            return None

        return history[-1]

    def retrieve_fact_history(self, entity_id: str, attribute: str) -> Sequence[Fact]:
        """Retrieve all stored facts for an entity attribute.

        Parameters:
            entity_id: Entity whose facts should be returned.
            attribute: Fact attribute to retrieve.

        Returns:
            Immutable sequence of facts sorted by timeline position when
            available, then by fact ID.
        """
        return tuple(
            sorted(
                (
                    fact
                    for fact in self._facts.values()
                    if fact.entity_id == entity_id and fact.attribute == attribute
                ),
                key=self._fact_timeline_sort_key,
            )
        )

    def store_timeline_event(self, event: TimelineEvent) -> None:
        """Store a timeline event.

        Parameters:
            event: Timeline event to store.

        Raises:
            ValueError: If the event references unknown chapter or evidence, or
                reuses an existing event ID for different data.
        """
        if event.chapter_id not in self._chapters:
            raise ValueError(f"Unknown chapter: {event.chapter_id}")
        if event.evidence_id not in self._evidence:
            raise ValueError(f"Unknown evidence: {event.evidence_id}")

        self._store_unique(
            self._events,
            event.event_id,
            event,
            "timeline event",
        )

    def store_state_change(self, state_change: StateChange) -> None:
        """Store a validity window for a fact.

        Parameters:
            state_change: State change to store.

        Raises:
            ValueError: If the state change references unknown facts or events,
                or reuses an existing state change ID for different data.
        """
        if state_change.fact_id not in self._facts:
            raise ValueError(f"Unknown fact: {state_change.fact_id}")
        if state_change.valid_from_event_id not in self._events:
            raise ValueError(f"Unknown event: {state_change.valid_from_event_id}")
        if (
            state_change.valid_until_event_id is not None
            and state_change.valid_until_event_id not in self._events
        ):
            raise ValueError(f"Unknown event: {state_change.valid_until_event_id}")

        self._store_unique(
            self._state_changes,
            state_change.state_change_id,
            state_change,
            "state change",
        )

    def close_open_state_changes(
        self,
        entity_id: str,
        attribute: str,
        valid_until_event_id: str,
    ) -> None:
        """Close currently open state changes for an entity attribute.

        Parameters:
            entity_id: Entity whose previous state changes should close.
            attribute: Fact attribute being replaced.
            valid_until_event_id: Event where the previous facts stop being valid.

        Raises:
            ValueError: If the closing event is unknown.
        """
        if valid_until_event_id not in self._events:
            raise ValueError(f"Unknown event: {valid_until_event_id}")

        for state_change in tuple(self._state_changes.values()):
            fact = self._facts[state_change.fact_id]
            if (
                fact.entity_id == entity_id
                and fact.attribute == attribute
                and state_change.valid_until_event_id is None
            ):
                self._state_changes[state_change.state_change_id] = StateChange(
                    state_change_id=state_change.state_change_id,
                    fact_id=state_change.fact_id,
                    valid_from_event_id=state_change.valid_from_event_id,
                    valid_until_event_id=valid_until_event_id,
                )

    def retrieve_state_at_chapter(
        self,
        entity_id: str,
        chapter_index: int,
    ) -> Sequence[Fact]:
        """Retrieve facts valid for an entity at a chapter.

        Parameters:
            entity_id: Entity whose active facts should be returned.
            chapter_index: One-based chapter index to inspect.

        Returns:
            Immutable sequence of facts active at that chapter.
        """
        active_facts = [
            self._facts[state_change.fact_id]
            for state_change in self._state_changes.values()
            if self._state_change_is_active(state_change, chapter_index)
            and self._facts[state_change.fact_id].entity_id == entity_id
        ]
        return tuple(sorted(active_facts, key=lambda fact: fact.attribute))

    def _state_change_is_active(
        self,
        state_change: StateChange,
        chapter_index: int,
    ) -> bool:
        """Return whether a state change is active at a chapter."""
        valid_from = self._event_chapter_index(state_change.valid_from_event_id)
        if chapter_index < valid_from:
            return False

        if state_change.valid_until_event_id is None:
            return True

        valid_until = self._event_chapter_index(state_change.valid_until_event_id)
        return chapter_index < valid_until

    def _event_chapter_index(self, event_id: str) -> int:
        """Return the chapter index for an event."""
        event = self._events[event_id]
        chapter = self._chapters[event.chapter_id]
        return chapter.chapter_index

    def _fact_timeline_sort_key(self, fact: Fact) -> tuple[int, int, int, str, str]:
        """Return a stable timeline-first sort key for a fact."""
        state_changes = tuple(
            state_change
            for state_change in self._state_changes.values()
            if state_change.fact_id == fact.fact_id
        )
        if not state_changes:
            return (0, 0, 0, "", fact.fact_id)

        latest_state_change = max(
            state_changes,
            key=lambda state_change: self._event_sort_key(
                state_change.valid_from_event_id,
            ),
        )
        chapter_index, scene_index, event_id = self._event_sort_key(
            latest_state_change.valid_from_event_id,
        )
        return (1, chapter_index, scene_index, event_id, fact.fact_id)

    def _event_sort_key(self, event_id: str) -> tuple[int, int, str]:
        """Return a deterministic story-order key for an event."""
        event = self._events[event_id]
        return (
            self._event_chapter_index(event_id),
            self._first_integer(event.scene_id),
            event.event_id,
        )

    @staticmethod
    def _first_integer(value: str) -> int:
        """Return the first integer in a string, or zero when absent."""
        match = re.search(r"\d+", value)
        if match is None:
            return 0

        return int(match.group())

    def _store_unique(
        self,
        collection: dict[str, T],
        key: str,
        value: T,
        record_type: str,
    ) -> None:
        """Store a keyed record without allowing silent mutation."""
        existing_value = collection.get(key)
        if existing_value is not None:
            if existing_value != value:
                self._raise_conflicting_record(record_type, key)
            return

        collection[key] = value

    @staticmethod
    def _raise_conflicting_record(record_type: str, record_id: str) -> None:
        """Raise a conflict error for a reused permanent record ID."""
        logger.warning(
            "canon_database_conflicting_%s_id",
            record_type.replace(" ", "_"),
            extra={"record_id": record_id},
        )
        raise ValueError(f"Conflicting {record_type}: {record_id}")

"""Presentation Engine implementation."""

from __future__ import annotations

import logging
import re
import textwrap
from collections.abc import Iterable

from aevryn.characters import CanonCharacterCard, CanonCharacterFact
from aevryn.presentation.models import (
    CharacterProfileView,
    PresentationSection,
    ProductionPackView,
    SceneSheetView,
    WorldSheetView,
)
from aevryn.prompts import ProductionPack
from aevryn.scenes import CanonSceneContext, SceneAnalysis
from aevryn.world import WorldEntityState, WorldState

logger = logging.getLogger(__name__)

_STATUS_ATTRIBUTES = ("status", "role", "academic_year", "year", "student_status")
_ALIAS_ATTRIBUTES = ("display_name", "name", "alias")
_TITLE_ATTRIBUTES = ("title", "noble_title")
_DESCRIPTION_ATTRIBUTES = ("description", "appearance")
_GOAL_EXACT_ATTRIBUTES = ("current_goal", "current_task", "next_semester_requirement", "intention")
_GOAL_PARTIAL_ATTRIBUTES = (
    "goal",
    "intention",
    "objective",
    "plan",
    "planning",
    "requirement",
    "task",
)
_EQUIPMENT_EXACT_ATTRIBUTES = ("current_equipment", "current_weapon", "equipment", "inventory")
_EQUIPMENT_PARTIAL_ATTRIBUTES = ("armor", "equipment", "inventory", "item", "tool", "weapon")
_ABILITY_EXACT_ATTRIBUTES = (
    "ability",
    "profession",
    "skill",
    "special_attribute",
)
_ABILITY_PARTIAL_ATTRIBUTES = (
    "ability",
    "effect",
    "profession",
    "reward",
    "skill",
    "technique",
)
_ASSET_EXACT_ATTRIBUTES = ("current_assets", "possession", "territory", "warehouse")
_ASSET_PARTIAL_ATTRIBUTES = (
    "asset",
    "owned",
    "possession",
    "resource",
    "territory",
    "vehicle",
    "warehouse",
)
_TERRITORY_ATTRIBUTES = (
    "noble_title",
    "territory",
    "territory_condition",
    "territory_limitation",
    "territory_security",
)
_RELATIONSHIP_ATTRIBUTES = (
    "relationship_context",
    "family_context",
    "origin_context",
)
_RELATIONSHIP_PARTIAL_ATTRIBUTES = (
    "classmate",
    "family",
    "father",
    "feeling_toward",
    "fiance",
    "fiancee",
    "friend",
    "mother",
    "relationship",
)
_LIMITATION_EXACT_ATTRIBUTES = (
    "current_limitation",
    "injury",
    "territory_limitation",
)
_LIMITATION_PARTIAL_ATTRIBUTES = ("disadvantage", "injury", "limitation", "weakness")
_EXPLICIT_GENDER_TERMS = (
    (
        "Female",
        ("sister", "mother", "daughter", "wife", "fiancee", "fiancée", "princess", "empress"),
    ),
    ("Male", ("brother", "father", "son", "husband", "fiance", "fiancé", "prince", "emperor")),
)
_EVIDENCE_GENDER_TERMS = (
    (
        "Female",
        (
            "female",
            "woman",
            "girl",
            "sister",
            "mother",
            "daughter",
            "wife",
            "fiancee",
            "princess",
            "empress",
        ),
    ),
    (
        "Male",
        (
            "male",
            "man",
            "boy",
            "brother",
            "father",
            "son",
            "husband",
            "fiance",
            "prince",
            "emperor",
        ),
    ),
)
_EXPLICIT_RACE_TERMS = (
    ("Half-Beastman", ("half-beastman", "half beastman")),
    ("Beastman", ("beastman", "beast man")),
    ("Beastkin", ("beastkin", "beast kin")),
    ("Human", ("human",)),
    ("Elf", ("elf", "elven")),
    ("Demon", ("demon",)),
    ("Dragon", ("dragon",)),
    ("Vampire", ("vampire",)),
)
_MAX_PROMPT_PRESENTATION_LINES = 48


class PresentationEngine:
    """Convert internal Aevryn truth into human-readable view models."""

    def character_profile(self, card: CanonCharacterCard) -> CharacterProfileView:
        """Build a human-readable character profile.

        Parameters:
            card: Canon-backed character card.

        Returns:
            Character profile view optimized for fast human scanning.
        """
        facts_by_attribute = self._facts_by_attribute(card.facts)
        profile = CharacterProfileView(
            character_id=card.character_id,
            display_name=card.display_name,
            subtitle=self._subtitle(facts_by_attribute),
            aliases=self._section("Aliases", facts_by_attribute, _ALIAS_ATTRIBUTES),
            titles=self._section("Titles", facts_by_attribute, _TITLE_ATTRIBUTES),
            descriptions=self._section(
                "Descriptions",
                facts_by_attribute,
                _DESCRIPTION_ATTRIBUTES,
            ),
            race=self._identity_section(
                "Race",
                facts_by_attribute,
                attributes=("race", "species"),
                character_label=card.display_name,
                term_groups=_EXPLICIT_RACE_TERMS,
            ),
            gender=self._identity_section(
                "Gender",
                facts_by_attribute,
                attributes=("gender", "sex"),
                character_label=card.display_name,
                term_groups=_EXPLICIT_GENDER_TERMS,
            ),
            status=self._section("Status", facts_by_attribute, _STATUS_ATTRIBUTES),
            current_goal=self._section_by_category(
                "Current Goal",
                facts_by_attribute,
                exact_attributes=_GOAL_EXACT_ATTRIBUTES,
                partial_attributes=_GOAL_PARTIAL_ATTRIBUTES,
            ),
            current_equipment=self._section_by_category(
                "Current Equipment",
                facts_by_attribute,
                exact_attributes=_EQUIPMENT_EXACT_ATTRIBUTES,
                partial_attributes=_EQUIPMENT_PARTIAL_ATTRIBUTES,
            ),
            current_abilities=self._section_by_category(
                "Current Abilities",
                facts_by_attribute,
                exact_attributes=_ABILITY_EXACT_ATTRIBUTES,
                partial_attributes=_ABILITY_PARTIAL_ATTRIBUTES,
            ),
            current_assets=self._section_by_category(
                "Current Assets",
                facts_by_attribute,
                exact_attributes=_ASSET_EXACT_ATTRIBUTES,
                partial_attributes=_ASSET_PARTIAL_ATTRIBUTES,
            ),
            territory=self._section(
                "Territory",
                facts_by_attribute,
                _TERRITORY_ATTRIBUTES,
            ),
            relationships=self._section_by_category(
                "Relationships",
                facts_by_attribute,
                exact_attributes=_RELATIONSHIP_ATTRIBUTES,
                partial_attributes=_RELATIONSHIP_PARTIAL_ATTRIBUTES,
            ),
            current_limitations=self._section_by_category(
                "Current Limitations",
                facts_by_attribute,
                exact_attributes=_LIMITATION_EXACT_ATTRIBUTES,
                partial_attributes=_LIMITATION_PARTIAL_ATTRIBUTES,
            ),
            recent_changes=self._recent_changes(card.facts, facts_by_attribute),
            evidence_summary=self._evidence_summary(card.facts),
        )
        logger.debug(
            "character_profile_view_built",
            extra={"character_id": card.character_id},
        )
        return profile

    def scene_sheet(
        self,
        context: CanonSceneContext,
        analysis: SceneAnalysis,
    ) -> SceneSheetView:
        """Build a human-readable scene sheet.

        Parameters:
            context: Canon-backed scene context.
            analysis: Meaning-focused scene analysis.

        Returns:
            Scene sheet view optimized for fast human scanning.

        Raises:
            ValueError: If analysis belongs to a different scene.
        """
        if context.scene.scene_id != analysis.scene_id:
            raise ValueError("Scene analysis must match the presented scene.")

        return SceneSheetView(
            scene_id=context.scene.scene_id,
            title=context.scene.title,
            chapter_label=context.scene.chapter_id,
            location=PresentationSection(
                title="Location",
                items=self._location_items(context),
            ),
            characters_present=PresentationSection(
                title="Characters Present",
                items=tuple(self._unique_values(
                    card.display_name for card in context.character_cards
                )),
            ),
            mood=PresentationSection(title="Mood", items=(analysis.mood,)),
            purpose=PresentationSection(title="Purpose", items=(analysis.purpose,)),
            visual_highlights=PresentationSection(
                title="Visual Highlights",
                items=analysis.visual_highlights,
            ),
            continuity_changes=PresentationSection(
                title="Continuity Changes",
                items=analysis.changes_introduced,
            ),
            environment=PresentationSection(
                title="Environment",
                items=(analysis.environment_summary,),
            ),
            evidence_summary=self._scene_evidence_summary(context),
        )

    def production_pack(self, pack: ProductionPack, scene: SceneSheetView) -> ProductionPackView:
        """Build a human-readable production pack view.

        Parameters:
            pack: Internal production pack.
            scene: Presented scene sheet view.

        Returns:
            Production pack view with concise prompt sections.

        Raises:
            ValueError: If the production pack belongs to a different scene.
        """
        if pack.scene_id != scene.scene_id:
            raise ValueError("Production pack must match the presented scene.")

        return ProductionPackView(
            scene=scene,
            image_prompt=PresentationSection(
                title="Image Prompt",
                items=self._prompt_lines(pack.prompt_bundle.image_prompt),
            ),
            narration_prompt=PresentationSection(
                title="Narration Prompt",
                items=self._prompt_lines(pack.prompt_bundle.narration_prompt),
            ),
            camera_prompt=PresentationSection(
                title="Camera Prompt",
                items=self._prompt_lines(pack.prompt_bundle.camera_prompt),
            ),
            animation_prompt=PresentationSection(
                title="Animation Prompt",
                items=self._prompt_lines(pack.prompt_bundle.animation_prompt),
            ),
        )

    def world_sheet(self, state: WorldState) -> WorldSheetView:
        """Build a human-readable world sheet.

        Parameters:
            state: Canon-backed world state.

        Returns:
            World sheet view optimized for fast human scanning.
        """
        return WorldSheetView(
            chapter_label=f"Chapter {state.chapter_index}",
            entity_sections=self._world_entity_sections(state.entities),
            evidence_summary=self._world_evidence_summary(state),
        )

    @staticmethod
    def _facts_by_attribute(
        facts: tuple[CanonCharacterFact, ...],
    ) -> dict[str, tuple[CanonCharacterFact, ...]]:
        """Group character facts by attribute."""
        grouped: dict[str, list[CanonCharacterFact]] = {}
        for fact in facts:
            grouped.setdefault(fact.attribute, []).append(fact)

        return {
            attribute: tuple(attribute_facts)
            for attribute, attribute_facts in grouped.items()
        }

    @staticmethod
    def _subtitle(facts_by_attribute: dict[str, tuple[CanonCharacterFact, ...]]) -> str:
        """Build a compact character subtitle."""
        parts: list[str] = []
        for attribute in ("role", "department", "academic_year"):
            facts = facts_by_attribute.get(attribute, ())
            if facts:
                parts.append(facts[-1].value)

        return " | ".join(parts) or "Unknown"

    @staticmethod
    def _section(
        title: str,
        facts_by_attribute: dict[str, tuple[CanonCharacterFact, ...]],
        attributes: tuple[str, ...],
    ) -> PresentationSection:
        """Build a section from matching fact attributes."""
        items = tuple(
            fact.value
            for attribute in attributes
            for fact in facts_by_attribute.get(attribute, ())
        )
        return PresentationSection(
            title=title,
            items=PresentationEngine._items_or_unknown(items),
        )

    @staticmethod
    def _identity_section(
        title: str,
        facts_by_attribute: dict[str, tuple[CanonCharacterFact, ...]],
        attributes: tuple[str, ...],
        character_label: str,
        term_groups: tuple[tuple[str, tuple[str, ...]], ...],
    ) -> PresentationSection:
        """Build identity section from direct facts or conservative explicit clues."""
        support_haystacks = PresentationEngine._identity_support_haystacks(
            character_label=character_label,
            facts_by_attribute=facts_by_attribute,
        )
        direct_facts = tuple(
            fact
            for attribute in attributes
            for fact in facts_by_attribute.get(attribute, ())
        )
        direct_items = PresentationEngine._supported_identity_items(
            direct_facts,
            character_label=character_label,
            support_haystacks=support_haystacks,
            term_groups=term_groups,
        )
        if title == "Gender":
            direct_items = PresentationEngine._resolved_gender_items(direct_items)
        return PresentationSection(
            title=title,
            items=PresentationEngine._items_or_unknown(
                direct_items
                or PresentationEngine._explicit_identity_items(
                    support_haystacks,
                    term_groups,
                )
            ),
        )

    @staticmethod
    def _section_by_category(
        title: str,
        facts_by_attribute: dict[str, tuple[CanonCharacterFact, ...]],
        exact_attributes: tuple[str, ...],
        partial_attributes: tuple[str, ...],
    ) -> PresentationSection:
        """Build a section from generic fact attribute categories."""
        exact_attribute_set = set(exact_attributes)
        items = tuple(
            fact.value
            for attribute, facts in facts_by_attribute.items()
            if PresentationEngine._attribute_matches(
                attribute=attribute,
                exact_attributes=exact_attribute_set,
                partial_attributes=partial_attributes,
            )
            for fact in facts
        )
        return PresentationSection(
            title=title,
            items=PresentationEngine._items_or_unknown(items),
        )

    @staticmethod
    def _attribute_matches(
        attribute: str,
        exact_attributes: set[str],
        partial_attributes: tuple[str, ...],
    ) -> bool:
        """Return whether an attribute belongs in a generic presentation section."""
        normalized_attribute = attribute.lower()
        return normalized_attribute in exact_attributes or any(
            partial in normalized_attribute for partial in partial_attributes
        )

    @staticmethod
    def _recent_changes(
        facts: tuple[CanonCharacterFact, ...],
        facts_by_attribute: dict[str, tuple[CanonCharacterFact, ...]],
    ) -> PresentationSection:
        """Build recent changes section from valid-from chapters."""
        presented_attributes = PresentationEngine._presented_character_attributes(
            facts_by_attribute,
        )
        items = tuple(
            f"{fact.valid_from_chapter_id}: {fact.attribute} -> {fact.value}"
            for fact in facts[-8:]
            if fact.previous_value is not None or fact.attribute not in presented_attributes
        )
        return PresentationSection(
            title="Recent Changes",
            items=PresentationEngine._items_or_unknown(items),
        )

    @staticmethod
    def _presented_character_attributes(
        facts_by_attribute: dict[str, tuple[CanonCharacterFact, ...]],
    ) -> set[str]:
        """Return attributes already routed into first-class profile sections."""
        presented: set[str] = set()
        exact_groups = (
            (*_ALIAS_ATTRIBUTES, *_TITLE_ATTRIBUTES, *_DESCRIPTION_ATTRIBUTES),
            ("race", "species", "gender", "sex"),
            _STATUS_ATTRIBUTES,
            _TERRITORY_ATTRIBUTES,
        )
        category_groups = (
            (_GOAL_EXACT_ATTRIBUTES, _GOAL_PARTIAL_ATTRIBUTES),
            (_EQUIPMENT_EXACT_ATTRIBUTES, _EQUIPMENT_PARTIAL_ATTRIBUTES),
            (_ABILITY_EXACT_ATTRIBUTES, _ABILITY_PARTIAL_ATTRIBUTES),
            (_ASSET_EXACT_ATTRIBUTES, _ASSET_PARTIAL_ATTRIBUTES),
            (_RELATIONSHIP_ATTRIBUTES, _RELATIONSHIP_PARTIAL_ATTRIBUTES),
            (_LIMITATION_EXACT_ATTRIBUTES, _LIMITATION_PARTIAL_ATTRIBUTES),
        )
        for attribute in facts_by_attribute:
            normalized_attribute = attribute.lower()
            if any(normalized_attribute in group for group in exact_groups):
                presented.add(attribute)
                continue
            for exact_attributes, partial_attributes in category_groups:
                if PresentationEngine._attribute_matches(
                    attribute=attribute,
                    exact_attributes=set(exact_attributes),
                    partial_attributes=partial_attributes,
                ):
                    presented.add(attribute)
                    break
        return presented

    @staticmethod
    def _identity_support_haystacks(
        *,
        character_label: str,
        facts_by_attribute: dict[str, tuple[CanonCharacterFact, ...]],
    ) -> tuple[str, ...]:
        """Return self-describing identity text, not broad story context."""
        supported_attributes = (
            "display_name",
            "role",
            "status",
            "family_context",
            "relationship_context",
            "origin_context",
        )
        values = [character_label]
        values.extend(
            fact.value
            for attribute in supported_attributes
            for fact in facts_by_attribute.get(attribute, ())
        )
        return tuple(value.lower() for value in values if value.strip())

    @staticmethod
    def _supported_identity_items(
        facts: Iterable[CanonCharacterFact],
        *,
        character_label: str,
        support_haystacks: tuple[str, ...],
        term_groups: tuple[tuple[str, tuple[str, ...]], ...],
    ) -> tuple[str, ...]:
        """Return direct identity values only when self-description supports them."""
        supported_labels = set(
            PresentationEngine._explicit_identity_items(support_haystacks, term_groups)
        )
        return tuple(
            PresentationEngine._unique_values(
                fact.value
                for fact in facts
                if fact.value in supported_labels
                or PresentationEngine._identity_fact_has_support(
                    fact,
                    character_label=character_label,
                    support_haystacks=support_haystacks,
                    term_groups=term_groups,
                )
            )
        )

    @staticmethod
    def _identity_fact_has_support(
        fact: CanonCharacterFact,
        *,
        character_label: str,
        support_haystacks: tuple[str, ...],
        term_groups: tuple[tuple[str, tuple[str, ...]], ...],
    ) -> bool:
        """Return whether a direct identity fact is supported by self-describing text."""
        normalized_value = fact.value.lower()
        if PresentationEngine._identity_value_has_support(
            normalized_value,
            support_haystacks=support_haystacks,
        ):
            return True

        quote = fact.evidence.quote.lower()
        return PresentationEngine._quote_links_identity_to_character(
            quote=quote,
            character_label=character_label,
            identity_value=normalized_value,
            term_groups=term_groups,
        )

    @staticmethod
    def _identity_value_has_support(
        normalized_value: str,
        *,
        support_haystacks: tuple[str, ...],
    ) -> bool:
        """Return whether a direct identity value appears in self-describing text."""
        return any(
            PresentationEngine._contains_identity_term(haystack, normalized_value)
            for haystack in support_haystacks
        )

    @staticmethod
    def _quote_links_identity_to_character(
        *,
        quote: str,
        character_label: str,
        identity_value: str,
        term_groups: tuple[tuple[str, tuple[str, ...]], ...],
    ) -> bool:
        """Return whether a quote connects an identity term to this character."""
        character_terms = PresentationEngine._character_label_terms(character_label)
        if not character_terms or not any(
            PresentationEngine._contains_identity_term(quote, term)
            for term in character_terms
        ):
            return False

        identity_terms: tuple[str, ...] = (identity_value,)
        evidence_term_groups = (
            _EVIDENCE_GENDER_TERMS if term_groups == _EXPLICIT_GENDER_TERMS else term_groups
        )
        for label, terms in evidence_term_groups:
            if identity_value == label.lower():
                identity_terms = terms
                break

        is_gender_terms = evidence_term_groups == _EVIDENCE_GENDER_TERMS
        return any(
            PresentationEngine._quote_contains_supported_identity_term(
                quote,
                term,
                is_gender_term=is_gender_terms,
            )
            for term in identity_terms
        )

    @staticmethod
    def _quote_contains_supported_identity_term(
        quote: str,
        term: str,
        *,
        is_gender_term: bool,
    ) -> bool:
        """Return whether an identity term in a quote can support a character."""
        if not PresentationEngine._contains_identity_term(quote, term):
            return False
        if not is_gender_term:
            return True

        escaped_term = re.escape(term).replace(r"\ ", r"[\s_-]+")
        group_pattern = (
            rf"(?<![a-z0-9]){escaped_term}(?![a-z0-9])"
            r"(?:\s+[a-z0-9-]+){0,2}\s+"
            r"(soldiers|slaves|crew|members|recruits|troops|guards|students)\b"
        )
        return re.search(group_pattern, quote) is None

    @staticmethod
    def _character_label_terms(character_label: str) -> tuple[str, ...]:
        """Return useful non-generic terms that can link evidence to a character."""
        normalized_label = character_label.lower()
        terms = [normalized_label]
        generic_terms = {
            "female",
            "male",
            "human",
            "woman",
            "man",
            "girl",
            "boy",
            "unnamed",
            "unknown",
            "character",
            "crew",
            "member",
            "slave",
            "soldier",
            "commander",
            "captain",
        }
        terms.extend(
            part
            for part in re.findall(r"[a-z0-9]+", normalized_label)
            if len(part) >= 3 and part not in generic_terms
        )
        return tuple(PresentationEngine._unique_values(terms))

    @staticmethod
    def _resolved_gender_items(items: Iterable[str]) -> tuple[str, ...]:
        """Return gender only when supported values do not conflict."""
        unique_items = tuple(PresentationEngine._unique_values(items))
        normalized_items = {item.lower() for item in unique_items}
        if {"male", "female"}.issubset(normalized_items):
            return ()

        return unique_items

    @staticmethod
    def _explicit_identity_items(
        haystacks: tuple[str, ...],
        term_groups: tuple[tuple[str, tuple[str, ...]], ...],
    ) -> tuple[str, ...]:
        """Return identity labels only when self-description explicitly contains them."""
        labels: list[str] = []
        for haystack in haystacks:
            for label, terms in term_groups:
                if any(
                    PresentationEngine._contains_identity_term(haystack, term)
                    for term in terms
                ):
                    labels.append(label)
                    break
        return tuple(PresentationEngine._unique_values(labels))

    @staticmethod
    def _contains_identity_term(value: str, term: str) -> bool:
        """Return whether value contains a standalone identity term."""
        escaped_term = re.escape(term).replace(r"\ ", r"[\s_-]+")
        return re.search(rf"(?<![a-z0-9]){escaped_term}(?![a-z0-9])", value) is not None

    @staticmethod
    def _evidence_summary(facts: tuple[CanonCharacterFact, ...]) -> str:
        """Return compact evidence summary."""
        if not facts:
            return "0 verified facts"

        average_confidence = sum(fact.evidence.confidence for fact in facts) / len(facts)
        return f"{len(facts)} verified facts | Confidence {average_confidence:.0%}"

    @staticmethod
    def _scene_evidence_summary(context: CanonSceneContext) -> str:
        """Return compact scene evidence summary."""
        evidence_ids = {fact.evidence_id for fact in context.active_facts}
        evidence_ids.update(relationship.evidence_id for relationship in context.relationships)
        return f"{len(evidence_ids)} verified evidence references"

    @staticmethod
    def _location_items(context: CanonSceneContext) -> tuple[str, ...]:
        """Return likely location labels from active facts."""
        locations = tuple(
            fact.value
            for fact in context.active_facts
            if fact.attribute in {"current_location", "location", "territory"}
        )
        return PresentationEngine._items_or_unknown(locations)

    @staticmethod
    def _prompt_lines(prompt: str) -> tuple[str, ...]:
        """Return compact prompt lines for presentation."""
        unique_lines = PresentationEngine._unique_values(
            display_line
            for line in prompt.splitlines()
            if (display_line := PresentationEngine._prompt_display_line(line)) is not None
        )
        if len(unique_lines) <= _MAX_PROMPT_PRESENTATION_LINES:
            return tuple(unique_lines)

        safeguard_lines = [
            line
            for line in unique_lines
            if PresentationEngine._is_prompt_safeguard_line(line)
        ]
        selected: list[str] = []
        leading_line_limit = max(
            _MAX_PROMPT_PRESENTATION_LINES - len(safeguard_lines),
            0,
        )
        selected.extend(unique_lines[:leading_line_limit])
        for line in safeguard_lines:
            if line not in selected and len(selected) < _MAX_PROMPT_PRESENTATION_LINES:
                selected.append(line)
        for line in unique_lines[leading_line_limit:]:
            if len(selected) >= _MAX_PROMPT_PRESENTATION_LINES:
                break
            if line not in selected:
                selected.append(line)

        return tuple(selected)

    @staticmethod
    def _prompt_display_line(line: str) -> str | None:
        """Return one displayable prompt line or None for structural placeholders."""
        stripped_line = PresentationEngine._strip_markdown_bullet(line.strip())
        if not stripped_line or stripped_line == "Unknown" or stripped_line.endswith(":"):
            return None

        return PresentationEngine._shorten(stripped_line)

    @staticmethod
    def _is_prompt_safeguard_line(line: str) -> bool:
        """Return whether a prompt line protects Canon or output fidelity."""
        normalized_line = line.lower()
        return any(
            marker in normalized_line
            for marker in (
                "do not add",
                "do not contradict",
                "do not include",
                "do not invent",
                "do not render",
                "do not turn",
                "unless canon",
                "unless exact text",
                "unless listed",
                "unless supported",
                "without evidence",
                "style must not override",
            )
        )

    @staticmethod
    def _strip_markdown_bullet(value: str) -> str:
        """Return prompt text without a leading Markdown bullet marker."""
        stripped_value = value.strip()
        if stripped_value.startswith("- "):
            return stripped_value[2:].strip()

        return stripped_value

    @staticmethod
    def _world_entity_items(entity: WorldEntityState) -> tuple[str, ...]:
        """Return readable world entity facts and relationships."""
        fact_items = tuple(
            f"{fact.attribute}: {fact.value}"
            for fact in entity.facts
        )
        relationship_items = tuple(
            (
                f"{relationship.source_entity_id} "
                f"{relationship.relationship_type} "
                f"{relationship.target_entity_id}"
            )
            for relationship in entity.relationships
        )
        return PresentationEngine._items_or_unknown(fact_items + relationship_items)

    @staticmethod
    def _world_entity_sections(
        entities: tuple[WorldEntityState, ...],
    ) -> tuple[PresentationSection, ...]:
        """Return readable world sections with duplicate titles merged."""
        section_items_by_title: dict[str, list[str]] = {}
        for entity in entities:
            title = f"{entity.display_name} ({entity.entity_type})"
            section_items_by_title.setdefault(title, []).extend(
                PresentationEngine._world_entity_items(entity)
            )

        return tuple(
            PresentationSection(
                title=title,
                items=PresentationEngine._items_or_unknown(items),
            )
            for title, items in section_items_by_title.items()
        )

    @staticmethod
    def _world_evidence_summary(state: WorldState) -> str:
        """Return compact world evidence summary."""
        evidence_ids = {
            fact.evidence.evidence_id
            for entity in state.entities
            for fact in entity.facts
        }
        evidence_ids.update(
            relationship.evidence_id
            for entity in state.entities
            for relationship in entity.relationships
        )
        return f"{len(evidence_ids)} verified evidence references"

    @staticmethod
    def _items_or_unknown(items: Iterable[str]) -> tuple[str, ...]:
        """Return deduplicated display items or Unknown."""
        unique_items = PresentationEngine._unique_values(items)
        return tuple(unique_items) or ("Unknown",)

    @staticmethod
    def _shorten(value: str, width: int = 160) -> str:
        """Return compact one-line presentation text."""
        normalized_value = " ".join(value.split())
        if not normalized_value:
            return "Unknown"

        return textwrap.shorten(normalized_value, width=width, placeholder="...")

    @staticmethod
    def _unique_values(values: Iterable[str]) -> list[str]:
        """Return non-empty values in first-seen order without duplicates."""
        unique: dict[str, None] = {}
        for value in values:
            if value:
                unique.setdefault(value, None)

        return list(unique)

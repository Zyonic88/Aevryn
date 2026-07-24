"""Deterministic Sentence Understanding implementation."""

from __future__ import annotations

import re
from collections.abc import Iterable

from aevryn.importing import EvidenceAnchor, ImportedSentence, ImportedSource
from aevryn.sentences.models import SentenceSignal, SentenceUnderstanding

ACTION_CUES = frozenset(
    {
        "activated",
        "attacked",
        "cast",
        "charged",
        "equipped",
        "fired",
        "lifted",
        "opened",
        "raised",
        "repaired",
        "summoned",
        "triggered",
        "used",
    }
)
DESCRIPTION_CUES = frozenset(
    {
        "appeared",
        "looked",
        "seemed",
        "stood",
        "was",
        "were",
    }
)
IDENTITY_CUES = frozenset(
    {
        "captain",
        "commander",
        "general",
        "he",
        "her",
        "his",
        "man",
        "officer",
        "she",
        "teacher",
        "woman",
    }
)
RELATIONSHIP_CUES = frozenset(
    {
        "brother",
        "classmate",
        "disciple",
        "father",
        "fiance",
        "fiancee",
        "friend",
        "master",
        "mother",
        "sister",
    }
)
LOCATION_CUES = frozenset(
    {
        "academy",
        "base",
        "building",
        "camp",
        "city",
        "classroom",
        "courtyard",
        "forest",
        "fortress",
        "hall",
        "hangar",
        "kingdom",
        "planet",
        "region",
        "room",
        "sector",
        "station",
        "territory",
        "world",
    }
)
LOCATION_PHRASE_CUES = frozenset(
    {
        "captain department",
        "military academy",
        "north star academy",
        "star system",
        "starship academy",
        "training room",
    }
)
ORGANIZATION_CUES = frozenset(
    {
        "academy",
        "army",
        "clan",
        "company",
        "department",
        "empire",
        "faction",
        "fleet",
        "guild",
        "kingdom",
        "sect",
        "starfleet",
    }
)
ORGANIZATION_PHRASE_CUES = frozenset(
    {
        "captain department",
        "galactic alliance",
        "military academy",
        "north star academy",
        "starlight empire",
        "starship academy",
    }
)
ITEM_CUES = frozenset(
    {
        "armor",
        "artifact",
        "battlecruiser",
        "blade",
        "blueprint",
        "book",
        "credits",
        "cruiser",
        "crystal",
        "dagger",
        "equipment",
        "manual",
        "potion",
        "rifle",
        "scroll",
        "ship",
        "slip",
        "spear",
        "starship",
        "sword",
        "token",
        "uniform",
        "vessel",
        "weapon",
    }
)
ITEM_PHRASE_CUES = frozenset(
    {
        "ability crystal",
        "battle cruiser",
        "cultivation manual",
        "jade slip",
        "source crystal",
        "skill book",
        "skill crystal",
        "skill manual",
        "skill scroll",
        "spell book",
        "spell scroll",
        "star ship",
        "starship blueprint",
        "technique scroll",
        "technique manual",
        "technical blueprint",
    }
)
SKILL_CUES = frozenset(
    {
        "ability",
        "art",
        "cast",
        "spell",
        "skill",
        "technique",
    }
)
SKILL_PHRASE_CUES = frozenset(
    {
        "cultivation art",
        "eye of insight",
        "martial art",
        "movement technique",
        "sword technique",
    }
)
SYSTEM_CUES = frozenset(
    {
        "interface",
        "mission",
        "panel",
        "points",
        "quest",
        "reward",
        "status",
        "system",
    }
)
SYSTEM_PHRASE_CUES = frozenset(
    {
        "experience points",
        "mission reward",
        "quest reward",
        "skill points",
        "status panel",
        "system interface",
        "system message",
        "system prompt",
    }
)
TRANSLATION_AMBIGUITY_CUES = frozenset(
    {
        "art",
        "core",
        "dao",
        "qi",
        "realm",
        "seal",
        "spirit",
        "system",
        "vessel",
    }
)
TRANSLATION_AMBIGUITY_PHRASE_CUES = frozenset(
    {
        "cultivation realm",
        "dao seal",
        "spirit core",
        "system panel",
    }
)
SKILL_PHRASE_ITEM_CONTEXT_TERMS = frozenset({"art", "blade", "sword"})
ITEM_PHRASE_SKILL_CONTEXT_TERMS = frozenset({"ability", "skill", "spell", "technique"})
SYSTEM_PHRASE_SKILL_CONTEXT_TERMS = frozenset({"skill"})
DIALOGUE_PATTERN = re.compile(r'["\']|\b(said|asked|replied|shouted|whispered)\b', re.I)


class SentenceUnderstandingEngine:
    """Build metadata-only sentence meaning signals from imported source anchors."""

    def analyze_imported_source(
        self,
        imported_source: ImportedSource,
    ) -> tuple[SentenceUnderstanding, ...]:
        """Analyze every imported sentence without changing Canon."""
        anchors_by_sentence_id = _anchors_by_sentence_id(imported_source.anchors)
        understandings: list[SentenceUnderstanding] = []
        for paragraph in imported_source.paragraphs:
            for sentence in paragraph.sentences:
                anchor = anchors_by_sentence_id.get(sentence.sentence_id)
                if anchor is None:
                    raise ValueError(
                        "Imported sentence cannot be analyzed without evidence anchor."
                    )
                understandings.append(self.analyze_sentence(sentence=sentence, anchor=anchor))
        return tuple(understandings)

    def analyze_sentence(
        self,
        *,
        sentence: ImportedSentence,
        anchor: EvidenceAnchor,
    ) -> SentenceUnderstanding:
        """Analyze one imported sentence into evidence-linked meaning signals."""
        if sentence.sentence_id != anchor.sentence_id:
            raise ValueError("Sentence understanding anchor must match sentence ID.")
        tokens = _sentence_tokens(sentence.text)
        phrase_terms = _sentence_phrase_terms(sentence.text)
        cue_terms: list[str] = []
        signals: list[SentenceSignal] = []
        item_terms = set(tokens & ITEM_CUES) | set(phrase_terms & ITEM_PHRASE_CUES)
        location_terms = set(tokens & LOCATION_CUES) | set(
            phrase_terms & LOCATION_PHRASE_CUES
        )
        organization_terms = set(tokens & ORGANIZATION_CUES) | set(
            phrase_terms & ORGANIZATION_PHRASE_CUES
        )
        skill_terms = set(tokens & SKILL_CUES) | set(phrase_terms & SKILL_PHRASE_CUES)
        system_terms = set(tokens & SYSTEM_CUES) | set(phrase_terms & SYSTEM_PHRASE_CUES)
        item_terms -= _item_terms_owned_by_skill_phrases(
            text=sentence.text,
            phrase_terms=phrase_terms,
            item_terms=item_terms,
        )
        skill_terms -= _skill_terms_owned_by_item_phrases(
            text=sentence.text,
            phrase_terms=phrase_terms,
            skill_terms=skill_terms,
        )
        skill_terms -= _skill_terms_owned_by_system_phrases(
            text=sentence.text,
            phrase_terms=phrase_terms,
            skill_terms=skill_terms,
        )

        _append_signal_if(signals, "dialogue", bool(DIALOGUE_PATTERN.search(sentence.text)))
        _append_signal_if(signals, "action", bool(tokens & ACTION_CUES))
        _append_signal_if(signals, "description", bool(tokens & DESCRIPTION_CUES))
        _append_signal_if(signals, "identity_reference", bool(tokens & IDENTITY_CUES))
        _append_signal_if(signals, "relationship_reference", bool(tokens & RELATIONSHIP_CUES))
        _append_signal_if(signals, "location_reference", bool(location_terms))
        _append_signal_if(signals, "organization_reference", bool(organization_terms))
        _append_signal_if(signals, "item_reference", bool(item_terms))
        _append_signal_if(signals, "skill_reference", bool(skill_terms))
        _append_signal_if(signals, "system_reference", bool(system_terms))

        ambiguity_terms = _ordered_terms(
            set(tokens & TRANSLATION_AMBIGUITY_CUES)
            | set(phrase_terms & TRANSLATION_AMBIGUITY_PHRASE_CUES)
        )
        _append_signal_if(signals, "translation_ambiguity", bool(ambiguity_terms))

        cue_terms.extend(_ordered_intersection(tokens, ACTION_CUES))
        cue_terms.extend(_ordered_terms(location_terms))
        cue_terms.extend(_ordered_terms(organization_terms))
        cue_terms.extend(_ordered_terms(item_terms))
        cue_terms.extend(_ordered_terms(skill_terms))
        cue_terms.extend(_ordered_terms(system_terms))

        if not signals:
            signals.append("description")

        return SentenceUnderstanding(
            sentence_id=sentence.sentence_id,
            evidence_anchor_id=anchor.anchor_id,
            source_chapter_id=anchor.chapter_id,
            source_scene_id=anchor.scene_id,
            paragraph_index=anchor.paragraph_index,
            sentence_index=anchor.sentence_index,
            signals=tuple(signals),
            cue_terms=tuple(dict.fromkeys(cue_terms)),
            ambiguity_terms=ambiguity_terms,
            review_required=_review_required(signals=signals, ambiguity_terms=ambiguity_terms),
        )


def _anchors_by_sentence_id(
    anchors: Iterable[EvidenceAnchor],
) -> dict[str, EvidenceAnchor]:
    """Return evidence anchors keyed by sentence ID."""
    anchors_by_sentence_id: dict[str, EvidenceAnchor] = {}
    for anchor in anchors:
        existing_anchor = anchors_by_sentence_id.get(anchor.sentence_id)
        if existing_anchor is not None:
            raise ValueError("Sentence understanding requires one anchor per sentence.")
        anchors_by_sentence_id[anchor.sentence_id] = anchor
    return anchors_by_sentence_id


def _sentence_tokens(text: str) -> set[str]:
    """Return normalized tokens and compact phrase aliases for one sentence."""
    tokens = {
        token
        for token in "".join(
            character.lower() if character.isalnum() else " "
            for character in text
        ).split()
        if token
    }
    if "battle" in tokens and "cruiser" in tokens:
        tokens.add("battlecruiser")
    if "star" in tokens and "ship" in tokens:
        tokens.add("starship")
    return tokens


def _sentence_phrase_terms(text: str) -> set[str]:
    """Return normalized phrase cues present in one sentence."""
    normalized = " ".join(
        "".join(
            character.lower() if character.isalnum() else " "
            for character in text
        ).split()
    )
    phrase_candidates = (
        ITEM_PHRASE_CUES
        | LOCATION_PHRASE_CUES
        | ORGANIZATION_PHRASE_CUES
        | SKILL_PHRASE_CUES
        | SYSTEM_PHRASE_CUES
        | TRANSLATION_AMBIGUITY_PHRASE_CUES
    )
    return {
        phrase
        for phrase in phrase_candidates
        if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized)
    }


def _item_terms_owned_by_skill_phrases(
    *,
    text: str,
    phrase_terms: set[str],
    item_terms: set[str],
) -> set[str]:
    """Return item-like words that are part of known skill phrases."""
    skill_phrases = phrase_terms & SKILL_PHRASE_CUES
    owned_terms: set[str] = set()
    for phrase in skill_phrases:
        owned_terms.update(set(phrase.split()) & SKILL_PHRASE_ITEM_CONTEXT_TERMS)
    return _exclusively_phrase_owned_terms(
        text=text,
        owned_terms=owned_terms,
        phrase_terms=skill_phrases,
        candidate_terms=item_terms,
    )


def _skill_terms_owned_by_item_phrases(
    *,
    text: str,
    phrase_terms: set[str],
    skill_terms: set[str],
) -> set[str]:
    """Return skill-like words that are part of known physical item phrases."""
    item_phrases = phrase_terms & ITEM_PHRASE_CUES
    owned_terms: set[str] = set()
    for phrase in item_phrases:
        owned_terms.update(set(phrase.split()) & ITEM_PHRASE_SKILL_CONTEXT_TERMS)
    return _exclusively_phrase_owned_terms(
        text=text,
        owned_terms=owned_terms,
        phrase_terms=item_phrases,
        candidate_terms=skill_terms,
    )


def _skill_terms_owned_by_system_phrases(
    *,
    text: str,
    phrase_terms: set[str],
    skill_terms: set[str],
) -> set[str]:
    """Return skill-like words that are part of known system/resource phrases."""
    system_phrases = phrase_terms & SYSTEM_PHRASE_CUES
    owned_terms: set[str] = set()
    for phrase in system_phrases:
        owned_terms.update(set(phrase.split()) & SYSTEM_PHRASE_SKILL_CONTEXT_TERMS)
    return _exclusively_phrase_owned_terms(
        text=text,
        owned_terms=owned_terms,
        phrase_terms=system_phrases,
        candidate_terms=skill_terms,
    )


def _exclusively_phrase_owned_terms(
    *,
    text: str,
    owned_terms: set[str],
    phrase_terms: set[str],
    candidate_terms: set[str],
) -> set[str]:
    """Return terms whose sentence occurrences are fully owned by known phrases."""
    removable_terms = owned_terms & candidate_terms
    if not removable_terms:
        return set()
    word_counts = _sentence_word_counts(text)
    return {
        term
        for term in removable_terms
        if word_counts.get(term, 0) <= _phrase_owned_term_count(phrase_terms, term)
    }


def _sentence_word_counts(text: str) -> dict[str, int]:
    """Return normalized word occurrence counts for one sentence."""
    counts: dict[str, int] = {}
    for token in (
        "".join(
            character.lower() if character.isalnum() else " "
            for character in text
        ).split()
    ):
        counts[token] = counts.get(token, 0) + 1
    return counts


def _phrase_owned_term_count(phrase_terms: set[str], term: str) -> int:
    """Return how many phrase cues contain one owned term."""
    return sum(phrase.split().count(term) for phrase in phrase_terms)


def _append_signal_if(
    signals: list[SentenceSignal],
    signal: SentenceSignal,
    condition: bool,
) -> None:
    """Append a signal once when the condition is true."""
    if condition and signal not in signals:
        signals.append(signal)


def _ordered_intersection(tokens: set[str], candidates: frozenset[str]) -> tuple[str, ...]:
    """Return stable candidate terms present in token set."""
    return tuple(term for term in sorted(candidates) if term in tokens)


def _ordered_terms(values: set[str]) -> tuple[str, ...]:
    """Return stable terms from an unordered set."""
    return tuple(sorted(values))


def _review_required(
    *,
    signals: list[SentenceSignal],
    ambiguity_terms: tuple[str, ...],
) -> bool:
    """Return whether sentence-level meaning should be reviewed or routed carefully."""
    if ambiguity_terms:
        return True
    if "system_reference" in signals and "skill_reference" in signals:
        return True
    return "skill_reference" in signals and "item_reference" in signals

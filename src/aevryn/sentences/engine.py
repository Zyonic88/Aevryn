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
        "dagger",
        "equipment",
        "manual",
        "potion",
        "rifle",
        "ship",
        "spear",
        "starship",
        "sword",
        "token",
        "uniform",
        "vessel",
        "weapon",
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
        "used",
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
        cue_terms: list[str] = []
        signals: list[SentenceSignal] = []

        _append_signal_if(signals, "dialogue", bool(DIALOGUE_PATTERN.search(sentence.text)))
        _append_signal_if(signals, "action", bool(tokens & ACTION_CUES))
        _append_signal_if(signals, "description", bool(tokens & DESCRIPTION_CUES))
        _append_signal_if(signals, "identity_reference", bool(tokens & IDENTITY_CUES))
        _append_signal_if(signals, "relationship_reference", bool(tokens & RELATIONSHIP_CUES))
        _append_signal_if(signals, "item_reference", bool(tokens & ITEM_CUES))
        _append_signal_if(signals, "skill_reference", bool(tokens & SKILL_CUES))
        _append_signal_if(signals, "system_reference", bool(tokens & SYSTEM_CUES))

        ambiguity_terms = _ordered_intersection(tokens, TRANSLATION_AMBIGUITY_CUES)
        _append_signal_if(signals, "translation_ambiguity", bool(ambiguity_terms))

        cue_terms.extend(_ordered_intersection(tokens, ACTION_CUES))
        cue_terms.extend(_ordered_intersection(tokens, ITEM_CUES))
        cue_terms.extend(_ordered_intersection(tokens, SKILL_CUES))
        cue_terms.extend(_ordered_intersection(tokens, SYSTEM_CUES))

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


def _review_required(
    *,
    signals: list[SentenceSignal],
    ambiguity_terms: tuple[str, ...],
) -> bool:
    """Return whether sentence-level meaning should be reviewed or routed carefully."""
    if ambiguity_terms:
        return True
    return "skill_reference" in signals and "item_reference" in signals

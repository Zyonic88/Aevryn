"""Deterministic Translation Foundation implementation."""

from __future__ import annotations

import re

from aevryn.translation.models import (
    GlossaryTerm,
    TranslatedUnit,
    TranslationIssue,
    TranslationMode,
    TranslationUnit,
)


class TranslationEngine:
    """Normalize story text while preserving source evidence links."""

    def normalize_unit(
        self,
        unit: TranslationUnit,
        *,
        glossary: tuple[GlossaryTerm, ...] = (),
        mode: TranslationMode = "clean_english",
    ) -> TranslatedUnit:
        """Return a normalized unit that still points to original source anchors."""
        text = unit.source_text
        issues: list[TranslationIssue] = []
        stable_glossary = _validated_glossary(glossary)

        text = _apply_glossary_once(
            text=text,
            glossary=stable_glossary,
            issues=issues,
            evidence_anchor_ids=unit.evidence_anchor_ids,
        )

        return TranslatedUnit(
            unit_id=unit.unit_id,
            source_language=unit.source_language,
            target_language=unit.target_language,
            mode=mode,
            normalized_text=_normalize_spacing(text),
            source_evidence_anchor_ids=unit.evidence_anchor_ids,
            issues=tuple(issues),
            source_chapter_id=unit.source_chapter_id,
            source_scene_id=unit.source_scene_id,
        )

    def normalize_units(
        self,
        units: tuple[TranslationUnit, ...],
        *,
        glossary: tuple[GlossaryTerm, ...] = (),
        mode: TranslationMode = "clean_english",
    ) -> tuple[TranslatedUnit, ...]:
        """Normalize multiple units deterministically."""
        stable_glossary = _validated_glossary(glossary)
        return tuple(
            self.normalize_unit(unit, glossary=stable_glossary, mode=mode)
            for unit in units
        )


def _validated_glossary(glossary: tuple[GlossaryTerm, ...]) -> tuple[GlossaryTerm, ...]:
    """Reject duplicate source terms before order can affect normalization."""
    seen_source_terms: set[str] = set()
    for term in glossary:
        normalized_source_term = term.source_term.casefold()
        if normalized_source_term in seen_source_terms:
            raise ValueError("Glossary source terms must be unique.")
        seen_source_terms.add(normalized_source_term)
    return glossary


def _apply_glossary_once(
    *,
    text: str,
    glossary: tuple[GlossaryTerm, ...],
    issues: list[TranslationIssue],
    evidence_anchor_ids: tuple[str, ...],
) -> str:
    """Apply glossary terms without cascading replacements into preferred output."""
    if not glossary:
        return text

    terms_by_source = {
        term.source_term.casefold(): term
        for term in sorted(glossary, key=lambda item: item.source_term.casefold())
    }
    reviewed_terms: set[str] = set()
    pattern = _glossary_pattern(glossary)

    def replace_match(match: re.Match[str]) -> str:
        source_text = match.group(0)
        term = terms_by_source[source_text.casefold()]
        if term.review_required or term.possible_meanings:
            reviewed_key = term.source_term.casefold()
            if reviewed_key not in reviewed_terms:
                reviewed_terms.add(reviewed_key)
                message = "Uncertain glossary term preserved for review."
                if term.possible_meanings:
                    message = "Ambiguous glossary term preserved for review."
                issues.append(
                    TranslationIssue(
                        issue_code="translation_review_required",
                        source_term=term.source_term,
                        message=message,
                        evidence_anchor_ids=evidence_anchor_ids,
                        term_kind=term.term_kind,
                        possible_meaning_count=len(term.possible_meanings),
                    )
                )
            return source_text
        return term.preferred_term

    return re.sub(pattern, replace_match, text, flags=re.IGNORECASE)


def _glossary_pattern(glossary: tuple[GlossaryTerm, ...]) -> str:
    """Return a longest-term-first regex for complete Unicode glossary terms."""
    alternatives = "|".join(
        re.escape(term.source_term)
        for term in sorted(
            glossary,
            key=lambda item: (-len(item.source_term), item.source_term.casefold()),
        )
    )
    return rf"(?<!\w)(?:{alternatives})(?!\w)"


def _normalize_spacing(text: str) -> str:
    """Collapse excess whitespace while preserving sentence text."""
    return " ".join(text.split())

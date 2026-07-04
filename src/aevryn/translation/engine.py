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

        for term in sorted(
            stable_glossary,
            key=lambda item: (-len(item.source_term), item.source_term.lower()),
        ):
            if term.review_required:
                if _contains_term(text, term.source_term):
                    issues.append(
                        TranslationIssue(
                            issue_code="translation_review_required",
                            source_term=term.source_term,
                            message="Uncertain glossary term preserved for review.",
                            evidence_anchor_ids=unit.evidence_anchor_ids,
                        )
                    )
                continue
            text = _replace_term(
                text=text,
                source_term=term.source_term,
                preferred_term=term.preferred_term,
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


def _contains_term(text: str, source_term: str) -> bool:
    """Return whether text contains a source term."""
    return re.search(_term_pattern(source_term), text, flags=re.IGNORECASE) is not None


def _replace_term(text: str, source_term: str, preferred_term: str) -> str:
    """Replace a complete glossary term without using ad hoc token splitting."""
    return re.sub(
        _term_pattern(source_term),
        preferred_term,
        text,
        flags=re.IGNORECASE,
    )


def _term_pattern(source_term: str) -> str:
    """Return a regex that matches a complete story term, not a substring."""
    return rf"(?<![A-Za-z0-9]){re.escape(source_term)}(?![A-Za-z0-9])"


def _normalize_spacing(text: str) -> str:
    """Collapse excess whitespace while preserving sentence text."""
    return " ".join(text.split())

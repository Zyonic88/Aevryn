"""Deterministic entity-resolution foundation."""

from __future__ import annotations

from aevryn.entity_resolution.models import (
    EntityIdentityProfile,
    ResolutionCandidate,
    ResolvedReference,
    SurfaceReference,
)

RESOLUTION_THRESHOLD = 0.75


class EntityResolutionEngine:
    """Resolve surface references to known identity profiles without updating Canon."""

    def resolve_reference(
        self,
        reference: SurfaceReference,
        profiles: tuple[EntityIdentityProfile, ...],
        *,
        context_entity_ids: tuple[str, ...] = (),
    ) -> ResolvedReference:
        """Resolve one surface reference against known profiles."""
        if not profiles:
            return ResolvedReference(
                reference=reference,
                status="unresolved",
                reason="No identity profiles are available.",
            )

        candidates = tuple(
            sorted(
                (
                    candidate
                    for profile in profiles
                    if (candidate := self._score_profile(reference, profile)) is not None
                ),
                key=lambda candidate: (-candidate.confidence, candidate.entity_id),
            )
        )
        if not candidates:
            return ResolvedReference(
                reference=reference,
                status="unresolved",
                reason="No supported identity match was found.",
            )

        top = candidates[0]
        if len(candidates) > 1 and top.confidence == candidates[1].confidence:
            return ResolvedReference(
                reference=reference,
                status="ambiguous",
                confidence=top.confidence,
                candidates=candidates,
                reason="Multiple identity profiles have equal confidence.",
            )

        if top.match_kind == "pronoun":
            pronoun_candidates = tuple(
                candidate
                for candidate in candidates
                if candidate.match_kind == "pronoun"
                and (
                    not context_entity_ids
                    or candidate.entity_id in set(context_entity_ids)
                )
            )
            if len(pronoun_candidates) != 1:
                return ResolvedReference(
                    reference=reference,
                    status="ambiguous" if pronoun_candidates else "unresolved",
                    confidence=top.confidence,
                    candidates=candidates,
                    reason="Pronoun reference did not have exactly one contextual candidate.",
                )
            top = pronoun_candidates[0]

        if top.confidence < RESOLUTION_THRESHOLD:
            return ResolvedReference(
                reference=reference,
                status="unresolved",
                confidence=top.confidence,
                candidates=candidates,
                reason="Best identity match was below the resolution threshold.",
            )

        return ResolvedReference(
            reference=reference,
            status="resolved",
            entity_id=top.entity_id,
            confidence=top.confidence,
            candidates=candidates,
            reason=f"Resolved by {top.match_kind} match.",
        )

    def resolve_references(
        self,
        references: tuple[SurfaceReference, ...],
        profiles: tuple[EntityIdentityProfile, ...],
        *,
        context_entity_ids: tuple[str, ...] = (),
    ) -> tuple[ResolvedReference, ...]:
        """Resolve multiple references deterministically."""
        return tuple(
            self.resolve_reference(
                reference,
                profiles,
                context_entity_ids=context_entity_ids,
            )
            for reference in references
        )

    @staticmethod
    def _score_profile(
        reference: SurfaceReference,
        profile: EntityIdentityProfile,
    ) -> ResolutionCandidate | None:
        """Return the best candidate score for one profile."""
        normalized_reference = _normalized_phrase(reference.text)
        if normalized_reference == _normalized_phrase(profile.canonical_name):
            return ResolutionCandidate(
                entity_id=profile.entity_id,
                confidence=0.99,
                match_kind="canonical_name",
                matched_text=profile.canonical_name,
            )
        for alias in profile.aliases:
            if normalized_reference == _normalized_phrase(alias):
                return ResolutionCandidate(
                    entity_id=profile.entity_id,
                    confidence=0.98,
                    match_kind="alias",
                    matched_text=alias,
                )
        for title in profile.titles:
            if normalized_reference == _normalized_phrase(title):
                return ResolutionCandidate(
                    entity_id=profile.entity_id,
                    confidence=0.95,
                    match_kind="title",
                    matched_text=title,
                )
        for description in profile.descriptions:
            if normalized_reference == _normalized_phrase(description):
                return ResolutionCandidate(
                    entity_id=profile.entity_id,
                    confidence=0.92,
                    match_kind="description",
                    matched_text=description,
                )
        for pronoun in profile.pronouns:
            if normalized_reference == _normalized_phrase(pronoun):
                return ResolutionCandidate(
                    entity_id=profile.entity_id,
                    confidence=0.87,
                    match_kind="pronoun",
                    matched_text=pronoun,
                )

        soft_score = _soft_description_score(normalized_reference, profile)
        if soft_score is None:
            return None
        return soft_score


def _normalized_phrase(value: str) -> str:
    """Return a comparison-safe phrase."""
    normalized = "".join(
        character.lower() if character.isalnum() else " "
        for character in value.strip()
    )
    parts = tuple(
        part
        for part in normalized.split()
        if part not in {"a", "an", "the"}
    )
    return " ".join(parts)


def _soft_description_score(
    normalized_reference: str,
    profile: EntityIdentityProfile,
) -> ResolutionCandidate | None:
    """Return a conservative low-confidence description candidate."""
    reference_tokens = set(normalized_reference.split())
    if not reference_tokens:
        return None

    best: ResolutionCandidate | None = None
    for description in profile.descriptions + profile.titles:
        description_tokens = set(_normalized_phrase(description).split())
        if not description_tokens:
            continue
        overlap = len(reference_tokens.intersection(description_tokens))
        if overlap == 0:
            continue
        confidence = round(min(0.74, 0.45 + (overlap / len(reference_tokens)) * 0.2), 2)
        candidate = ResolutionCandidate(
            entity_id=profile.entity_id,
            confidence=confidence,
            match_kind="low_confidence_description",
            matched_text=description,
        )
        if best is None or candidate.confidence > best.confidence:
            best = candidate
    return best


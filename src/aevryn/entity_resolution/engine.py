"""Deterministic entity-resolution foundation."""

from __future__ import annotations

from aevryn.entity_resolution.models import (
    EntityIdentityProfile,
    ResolutionCandidate,
    ResolvedReference,
    SurfaceReference,
)

RESOLUTION_THRESHOLD = 0.75
AMBIGUITY_MARGIN = 0.05


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
        stable_profiles = _validated_profiles(profiles)
        if not stable_profiles:
            return ResolvedReference(
                reference=reference,
                status="unresolved",
                reason="No identity profiles are available.",
            )

        candidates = tuple(
            sorted(
                (
                    candidate
                    for profile in stable_profiles
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
            if not context_entity_ids:
                return ResolvedReference(
                    reference=reference,
                    status="unresolved",
                    confidence=top.confidence,
                    candidates=candidates,
                    reason="Pronoun reference requires contextual identity support.",
                )
            context_entity_id_set = set(context_entity_ids)
            pronoun_candidates = tuple(
                candidate
                for candidate in candidates
                if candidate.match_kind == "pronoun"
                and candidate.entity_id in context_entity_id_set
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

        if (
            len(candidates) > 1
            and top.confidence >= RESOLUTION_THRESHOLD
            and candidates[1].confidence >= RESOLUTION_THRESHOLD
            and top.confidence - candidates[1].confidence <= AMBIGUITY_MARGIN
        ):
            return ResolvedReference(
                reference=reference,
                status="ambiguous",
                confidence=top.confidence,
                candidates=candidates,
                reason="Multiple identity profiles are within the ambiguity margin.",
            )

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
        stable_profiles = _validated_profiles(profiles)
        return tuple(
            self.resolve_reference(
                reference,
                stable_profiles,
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


def _validated_profiles(
    profiles: tuple[EntityIdentityProfile, ...],
) -> tuple[EntityIdentityProfile, ...]:
    """Reject duplicate identity profiles before scoring creates duplicate candidates."""
    seen_entity_ids: set[str] = set()
    for profile in profiles:
        if profile.entity_id in seen_entity_ids:
            raise ValueError("Entity identity profile IDs must be unique.")
        seen_entity_ids.add(profile.entity_id)
    return profiles


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
    reference_tokens = _expanded_identity_tokens(normalized_reference)
    if not reference_tokens:
        return None

    best: ResolutionCandidate | None = None
    for description in profile.descriptions + profile.titles:
        normalized_description = _normalized_phrase(description)
        description_tokens = _expanded_identity_tokens(normalized_description)
        if not description_tokens:
            continue
        overlap = len(reference_tokens.intersection(description_tokens))
        if overlap == 0:
            continue
        confidence = _description_variant_confidence(
            overlap=overlap,
            reference_token_count=len(reference_tokens),
            description_token_count=len(description_tokens),
        )
        candidate = ResolutionCandidate(
            entity_id=profile.entity_id,
            confidence=confidence,
            match_kind=(
                "description_variant"
                if confidence >= RESOLUTION_THRESHOLD
                else "low_confidence_description"
            ),
            matched_text=description,
        )
        if best is None or candidate.confidence > best.confidence:
            best = candidate
    return best


def _description_variant_confidence(
    *,
    overlap: int,
    reference_token_count: int,
    description_token_count: int,
) -> float:
    """Return a conservative score for non-exact description overlap."""
    if (
        overlap >= 2
        and overlap / reference_token_count >= 0.5
        and overlap / description_token_count >= 0.5
    ):
        return 0.82
    return round(min(0.74, 0.45 + (overlap / reference_token_count) * 0.2), 2)


def _expanded_identity_tokens(normalized_phrase: str) -> set[str]:
    """Return normalized tokens plus conservative identity equivalences."""
    tokens = set(normalized_phrase.split())
    expanded = set(tokens)
    for token in tokens:
        expanded.update(_IDENTITY_TOKEN_EQUIVALENTS.get(token, ()))
    return expanded


_IDENTITY_TOKEN_EQUIVALENTS = {
    "female": ("woman", "girl"),
    "woman": ("female",),
    "women": ("female",),
    "girl": ("female",),
    "girls": ("female",),
    "male": ("man", "boy"),
    "man": ("male",),
    "men": ("male",),
    "boy": ("male",),
    "boys": ("male",),
}

"""Entity Resolution boundary."""

from aevryn.entity_resolution.engine import EntityResolutionEngine
from aevryn.entity_resolution.models import (
    EntityIdentityProfile,
    ResolutionCandidate,
    ResolvedReference,
    SurfaceReference,
)

__all__ = [
    "EntityIdentityProfile",
    "EntityResolutionEngine",
    "ResolutionCandidate",
    "ResolvedReference",
    "SurfaceReference",
]


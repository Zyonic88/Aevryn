"""Canon Engine public API.

The Canon Engine maintains evidence-backed story state without generating or
inventing missing canon.
"""

from aevryn.canon.database import CanonDatabase
from aevryn.canon.engine import CanonEngine
from aevryn.canon.exceptions import (
    CanonError,
    DuplicateEntityError,
    MissingEvidenceError,
    UnknownEntityError,
)
from aevryn.canon.models import (
    CanonConflict,
    CanonEntity,
    CanonFactVersion,
    CanonRelationship,
    CanonSnapshot,
    EntityType,
    Evidence,
    StoryPosition,
)
from aevryn.canon.updating import (
    CanonUpdater,
    CanonUpdateSummary,
    RejectedCanonCandidate,
)

__all__ = [
    "CanonConflict",
    "CanonDatabase",
    "CanonEngine",
    "CanonEntity",
    "CanonError",
    "CanonFactVersion",
    "CanonRelationship",
    "CanonSnapshot",
    "CanonUpdateSummary",
    "CanonUpdater",
    "DuplicateEntityError",
    "EntityType",
    "Evidence",
    "MissingEvidenceError",
    "RejectedCanonCandidate",
    "StoryPosition",
    "UnknownEntityError",
]

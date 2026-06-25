"""Canon Engine public API.

The Canon Engine maintains evidence-backed story state without generating or
inventing missing canon.
"""

from scenesmith.canon.database import CanonDatabase
from scenesmith.canon.engine import CanonEngine
from scenesmith.canon.exceptions import (
    CanonError,
    DuplicateEntityError,
    MissingEvidenceError,
    UnknownEntityError,
)
from scenesmith.canon.models import (
    CanonConflict,
    CanonEntity,
    CanonFactVersion,
    CanonRelationship,
    CanonSnapshot,
    EntityType,
    Evidence,
    StoryPosition,
)
from scenesmith.canon.updating import CanonUpdater, CanonUpdateSummary

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
    "StoryPosition",
    "UnknownEntityError",
]

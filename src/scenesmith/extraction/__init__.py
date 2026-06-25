"""Entity Extraction public API.

Entity Extraction proposes candidates from imported source structure. It does
not update Canon or own truth.
"""

from scenesmith.extraction.ai import (
    AIExtractionClient,
    EvidenceBoundedAIExtractor,
    StaticAIExtractionClient,
)
from scenesmith.extraction.engine import EntityExtractionEngine, SceneExtractor
from scenesmith.extraction.models import (
    ExtractedEntity,
    ExtractedFact,
    ExtractedRelationship,
    ExtractedStateChange,
    ExtractionResult,
    SceneEvidenceAnchor,
    SceneExtractionInput,
)

__all__ = [
    "AIExtractionClient",
    "EntityExtractionEngine",
    "EvidenceBoundedAIExtractor",
    "ExtractedEntity",
    "ExtractedFact",
    "ExtractedRelationship",
    "ExtractedStateChange",
    "ExtractionResult",
    "SceneEvidenceAnchor",
    "SceneExtractionInput",
    "SceneExtractor",
    "StaticAIExtractionClient",
]

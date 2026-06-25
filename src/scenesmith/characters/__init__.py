"""Character Engine public API.

The Character Engine builds living character cards from Canon and Timeline.
"""

from scenesmith.characters.cards import (
    CanonCharacterCard,
    CanonCharacterFact,
    CharacterCardBuilder,
)
from scenesmith.characters.engine import CharacterEngine
from scenesmith.characters.exceptions import CharacterEngineError, NotACharacterError
from scenesmith.characters.models import CharacterCard, CharacterFact

__all__ = [
    "CanonCharacterCard",
    "CanonCharacterFact",
    "CharacterCard",
    "CharacterCardBuilder",
    "CharacterEngine",
    "CharacterEngineError",
    "CharacterFact",
    "NotACharacterError",
]

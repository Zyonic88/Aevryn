"""Character Engine public API.

The Character Engine builds living character cards from Canon and Timeline.
"""

from aevryn.characters.cards import (
    CanonCharacterCard,
    CanonCharacterFact,
    CharacterCardBuilder,
)
from aevryn.characters.engine import CharacterEngine
from aevryn.characters.exceptions import CharacterEngineError, NotACharacterError
from aevryn.characters.models import CharacterCard, CharacterFact

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

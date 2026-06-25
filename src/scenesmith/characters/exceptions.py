"""Exceptions raised by the Character Engine."""


class CharacterEngineError(Exception):
    """Base exception for Character Engine failures."""


class NotACharacterError(CharacterEngineError):
    """Raised when a character card is requested for a non-character entity."""

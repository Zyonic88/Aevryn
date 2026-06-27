"""Exceptions raised by the Canon Engine."""


class CanonError(Exception):
    """Base exception for Canon Engine failures."""


class DuplicateEntityError(CanonError):
    """Raised when an entity ID is registered more than once."""


class MissingEvidenceError(CanonError):
    """Raised when a canon update is attempted without usable evidence."""


class UnknownEntityError(CanonError):
    """Raised when a canon operation references an unregistered entity."""

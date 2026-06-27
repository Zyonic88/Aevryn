"""Exceptions raised by the Timeline Engine."""


class TimelineError(Exception):
    """Base exception for Timeline Engine failures."""


class DuplicateChapterError(TimelineError):
    """Raised when a chapter index is registered more than once."""


class DuplicateSceneError(TimelineError):
    """Raised when a scene position is registered more than once."""


class DuplicateEventError(TimelineError):
    """Raised when an event ID is registered more than once."""


class DuplicateStateChangeError(TimelineError):
    """Raised when a state-change ID is registered more than once."""


class InvalidTimelinePositionError(TimelineError):
    """Raised when a timeline operation references an unknown position."""


class OverlappingStateChangeError(TimelineError):
    """Raised when state validity windows overlap for one subject attribute."""

"""Timeline Engine public API.

The Timeline Engine manages story order and validity windows. It does not
extract canon, generate prompts, or decide what is true.
"""

from aevryn.timeline.engine import TimelineEngine
from aevryn.timeline.exceptions import (
    DuplicateChapterError,
    DuplicateEventError,
    DuplicateSceneError,
    DuplicateStateChangeError,
    InvalidTimelinePositionError,
    OverlappingStateChangeError,
    TimelineError,
)
from aevryn.timeline.models import (
    TimelineChapter,
    TimelineEvent,
    TimelineScene,
    TimelineStateChange,
)

__all__ = [
    "DuplicateChapterError",
    "DuplicateEventError",
    "DuplicateSceneError",
    "DuplicateStateChangeError",
    "InvalidTimelinePositionError",
    "OverlappingStateChangeError",
    "TimelineChapter",
    "TimelineEngine",
    "TimelineError",
    "TimelineEvent",
    "TimelineScene",
    "TimelineStateChange",
]

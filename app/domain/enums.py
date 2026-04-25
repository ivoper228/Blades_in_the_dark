from enum import Enum


class Hold(str, Enum):
    WEAK = "weak"
    STRONG = "strong"


class FactionStatus(str, Enum):
    ACTIVE = "active"
    WEAKENED = "weakened"
    DESTROYED = "destroyed"
    HIDDEN = "hidden"


class ClockType(str, Enum):
    PROJECT = "project"
    DANGER = "danger"
    CONFLICT = "conflict"
    CONTROL = "control"
    INVESTIGATION = "investigation"
    REVERSIBLE = "reversible"


class ClockStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class Visibility(str, Enum):
    GM_ONLY = "gm_only"
    PUBLIC = "public"


class EventType(str, Enum):
    WEEK_STARTED = "week_started"
    CLOCK_PROGRESS = "clock_progress"
    CLOCK_COMPLETED = "clock_completed"
    MANUAL_CHANGE = "manual_change"
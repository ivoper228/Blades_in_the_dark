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


class ClockEffectType(str, Enum):
    CHANGE_FACTION_TIER = "change_faction_tier"
    SET_FACTION_TIER = "set_faction_tier"
    SET_FACTION_HOLD = "set_faction_hold"
    SET_FACTION_STATUS = "set_faction_status"
    CHANGE_RELATION = "change_relation"
    TRANSFER_STREET_CONTROL = "transfer_street_control"
    ADVANCE_CLOCK = "advance_clock"
    CHANGE_CREW_HEAT = "change_crew_heat"
    CHANGE_CREW_WANTED_LEVEL = "change_crew_wanted_level"


class Visibility(str, Enum):
    GM_ONLY = "gm_only"
    PUBLIC = "public"


class EventType(str, Enum):
    WEEK_STARTED = "week_started"
    CLOCK_PROGRESS = "clock_progress"
    CLOCK_COMPLETED = "clock_completed"
    CLOCK_EFFECT_APPLIED = "clock_effect_applied"
    MANUAL_CHANGE = "manual_change"
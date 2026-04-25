from enum import Enum


class Hold(str, Enum):
    WEAK = "weak"
    STRONG = "strong"


class FactionStatus(str, Enum):
    ACTIVE = "active"
    WEAKENED = "weakened"
    DESTROYED = "destroyed"
    HIDDEN = "hidden"


class FocusLevel(str, Enum):
    DORMANT = "dormant"
    BACKGROUND = "background"
    ACTIVE = "active"
    SPOTLIGHT = "spotlight"


class ClockType(str, Enum):
    PROJECT = "project"
    DANGER = "danger"
    CONFLICT = "conflict"
    CONTROL = "control"
    INVESTIGATION = "investigation"
    REVERSIBLE = "reversible"


class ClockAdvanceMode(str, Enum):
    AUTO_WEEKLY = "auto_weekly"
    GM_CONFIRM_WEEKLY = "gm_confirm_weekly"
    MANUAL_ONLY = "manual_only"
    CONDITIONAL_WEEKLY = "conditional_weekly"
    REACTION = "reaction"


class ClockActionCategory(str, Enum):
    ATTACK = "attack"
    DEFENSE = "defense"
    INVESTIGATION = "investigation"
    PROJECT = "project"
    RECOVERY = "recovery"
    INFLUENCE = "influence"


class ClockStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    RESOLVED = "resolved"
    PAUSED = "paused"
    FAILED = "failed"


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
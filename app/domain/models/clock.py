from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import (
    ClockActionCategory,
    ClockAdvanceMode,
    ClockEffectType,
    ClockStatus,
    ClockType,
    Visibility,
)


@dataclass
class ClockEffect:
    effect_type: ClockEffectType
    target_faction_id: str | None = None
    secondary_faction_id: str | None = None
    target_clock_id: str | None = None
    street_id: str | None = None
    value: Any = None
    amount: int = 0
    description: str = ""


@dataclass
class Clock:
    id: str
    name: str
    clock_type: ClockType
    max_segments: int
    current_segments: int = 0
    owner_faction_id: str | None = None
    target_faction_id: str | None = None
    district_id: str | None = None
    street_id: str | None = None
    status: ClockStatus = ClockStatus.ACTIVE
    visibility: Visibility = Visibility.GM_ONLY
    trigger_on_complete: str = ""
    notes: str = ""

    advance_mode: ClockAdvanceMode = ClockAdvanceMode.AUTO_WEEKLY
    action_category: ClockActionCategory = ClockActionCategory.PROJECT
    priority: int = 3
    progress_per_week: int = 1
    advance_condition: dict[str, Any] = field(default_factory=dict)

    auto_advance: bool = True
    effects_applied: bool = False
    completion_effects: list[ClockEffect] = field(default_factory=list)
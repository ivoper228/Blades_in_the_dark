from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import (
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
    auto_advance: bool = True
    completion_effects: list[ClockEffect] = field(default_factory=list)
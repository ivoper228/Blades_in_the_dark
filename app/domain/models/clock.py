from dataclasses import dataclass

from app.domain.enums import ClockStatus, ClockType, Visibility


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
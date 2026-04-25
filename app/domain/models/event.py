from dataclasses import dataclass, field

from app.domain.enums import EventType, Visibility


@dataclass
class CityEvent:
    id: str
    week: int
    event_type: EventType
    title: str
    description: str = ""
    faction_ids: list[str] = field(default_factory=list)
    clock_ids: list[str] = field(default_factory=list)
    district_id: str | None = None
    street_id: str | None = None
    visibility: Visibility = Visibility.GM_ONLY
    consequences: list[str] = field(default_factory=list)
    created_by: str = "system"
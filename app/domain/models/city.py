from dataclasses import dataclass, field

from app.domain.models.clock import Clock
from app.domain.models.district import District
from app.domain.models.event import CityEvent
from app.domain.models.faction import Faction
from app.domain.models.relation import Relation
from app.domain.models.street import Street


@dataclass
class City:
    id: str
    name: str
    districts: dict[str, District] = field(default_factory=dict)
    streets: dict[str, Street] = field(default_factory=dict)
    factions: dict[str, Faction] = field(default_factory=dict)
    clocks: dict[str, Clock] = field(default_factory=dict)
    relations: dict[str, Relation] = field(default_factory=dict)
    events: dict[str, CityEvent] = field(default_factory=dict)
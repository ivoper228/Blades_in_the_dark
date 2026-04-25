from dataclasses import dataclass, field
from typing import Any

from app.domain.models.city import City


@dataclass
class Campaign:
    id: str
    name: str
    current_week: int
    city: City
    player_crew_id: str
    settings: dict[str, Any] = field(default_factory=dict)
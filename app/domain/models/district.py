from dataclasses import dataclass, field


@dataclass
class District:
    id: str
    name: str
    description: str = ""
    danger_level: int = 1
    street_ids: list[str] = field(default_factory=list)
    faction_ids: list[str] = field(default_factory=list)
    notes: str = ""
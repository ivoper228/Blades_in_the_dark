from dataclasses import dataclass, field


@dataclass
class Street:
    id: str
    name: str
    district_id: str
    controlling_faction_id: str | None = None
    present_faction_ids: list[str] = field(default_factory=list)
    asset_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    atmosphere: list[str] = field(default_factory=list)
    landmarks: list[str] = field(default_factory=list)
    notes: str = ""
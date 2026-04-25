from dataclasses import dataclass, field

from app.domain.models.faction import Faction


@dataclass
class PlayerCrew(Faction):
    crew_type: str = ""
    reputation: int = 0
    heat: int = 0
    wanted_level: int = 0
    coin: int = 0
    lair_id: str | None = None
    crew_xp: int = 0
    upgrades: list[str] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
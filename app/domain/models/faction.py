from dataclasses import dataclass, field

from app.domain.enums import FactionStatus, Hold


@dataclass
class Faction:
    id: str
    name: str
    faction_type: str
    tier: int = 0
    hold: Hold = Hold.STRONG
    status: FactionStatus = FactionStatus.ACTIVE
    district_ids: list[str] = field(default_factory=list)
    street_ids: list[str] = field(default_factory=list)
    asset_ids: list[str] = field(default_factory=list)
    clock_ids: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class NpcFaction(Faction):
    leader: str = ""
    public_goal: str = ""
    hidden_goal: str = ""
    preferred_actions: list[str] = field(default_factory=list)
    enemies: list[str] = field(default_factory=list)
    allies: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    vulnerabilities: list[str] = field(default_factory=list)
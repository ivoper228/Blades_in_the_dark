class Faction:
    id: str
    name: str
    faction_type: str
    tier: int
    hold: str              # weak / strong
    status: str            # active / weakened / destroyed / hidden
    district_ids: list[str]
    street_ids: list[str]
    asset_ids: list[str]
    clock_ids: list[str]
    notes: str

    class NpcFaction(Faction):
        leader: str
        public_goal: str
        hidden_goal: str
        preferred_actions: list[str]
        enemies: list[str]
        allies: list[str]
        resources: list[str]
        vulnerabilities: list[str]
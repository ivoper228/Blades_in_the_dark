class Faction:
    id
    name
    faction_type
    tier
    hold
    status
    district_ids
    street_ids
    asset_ids
    clock_ids
    relation_ids
    is_active
    notes


class NpcFaction(Faction):
    leader
    public_goal
    hidden_goal
    preferred_actions
    resources
    vulnerabilities


class PlayerCrew(Faction):
    crew_type
    reputation
    heat
    wanted_level
    coin
    lair_id
    crew_xp
    upgrades
    claims
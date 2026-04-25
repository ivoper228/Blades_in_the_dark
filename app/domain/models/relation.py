from dataclasses import dataclass


@dataclass
class Relation:
    id: str
    faction_a_id: str
    faction_b_id: str
    value: int = 0
    reason: str = ""
    is_public: bool = False
    notes: str = ""
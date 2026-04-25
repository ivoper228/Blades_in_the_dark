class Clock:
    id
    name
    clock_type
    max_segments
    current_segments
    owner_faction_id
    target_faction_id
    district_id
    street_id
    status
    visibility
    trigger_on_complete
    notes

class ClockType:
    PROJECT = "project"           # долгосрочная цель
    DANGER = "danger"             # угроза
    CONFLICT = "conflict"         # конфликт организаций
    CONTROL = "control"           # контроль улицы / района
    INVESTIGATION = "investigation"
    REVERSIBLE = "reversible"
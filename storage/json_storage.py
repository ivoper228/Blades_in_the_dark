import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from app.domain.enums import (
    ClockActionCategory,
    ClockAdvanceMode,
    ClockEffectType,
    ClockStatus,
    ClockType,
    EventType,
    FactionStatus,
    FocusLevel,
    Hold,
    Visibility,
)
from app.domain.models import (
    Campaign,
    City,
    CityEvent,
    Clock,
    ClockEffect,
    District,
    Faction,
    NpcFaction,
    PlayerCrew,
    Relation,
    Street,
)


class JsonStorage:
    def save_campaign(self, campaign: Campaign, path: str) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(
                self._to_jsonable(campaign),
                file,
                ensure_ascii=False,
                indent=2,
            )

    def load_campaign(self, path: str) -> Campaign:
        input_path = Path(path)

        with input_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return self._build_campaign(data)

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def _to_jsonable(self, value: Any) -> Any:
        if is_dataclass(value):
            return self._to_jsonable(asdict(value))

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, dict):
            return {
                str(key): self._to_jsonable(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [self._to_jsonable(item) for item in value]

        return value

    def _build_campaign(self, data: dict) -> Campaign:
        city = self._build_city(data["city"])

        return Campaign(
            id=data["id"],
            name=data["name"],
            current_week=data.get("current_week", 0),
            city=city,
            player_crew_id=data["player_crew_id"],
            settings=data.get("settings", {}),
        )

    def _build_city(self, data: dict) -> City:
        city = City(
            id=data["id"],
            name=data["name"],
        )

        city.districts = {
            district_id: self._build_district(district_data)
            for district_id, district_data in data.get("districts", {}).items()
        }

        city.streets = {
            street_id: self._build_street(street_data)
            for street_id, street_data in data.get("streets", {}).items()
        }

        city.factions = {
            faction_id: self._build_faction(faction_data)
            for faction_id, faction_data in data.get("factions", {}).items()
        }

        city.clocks = {
            clock_id: self._build_clock(clock_data)
            for clock_id, clock_data in data.get("clocks", {}).items()
        }

        city.relations = {
            relation_id: self._build_relation(relation_data)
            for relation_id, relation_data in data.get("relations", {}).items()
        }

        city.events = {
            event_id: self._build_event(event_data)
            for event_id, event_data in data.get("events", {}).items()
        }

        return city

    def _build_district(self, data: dict) -> District:
        return District(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            danger_level=data.get("danger_level", 1),
            street_ids=data.get("street_ids", []),
            faction_ids=data.get("faction_ids", []),
            notes=data.get("notes", ""),
        )

    def _build_street(self, data: dict) -> Street:
        return Street(
            id=data["id"],
            name=data["name"],
            district_id=data["district_id"],
            controlling_faction_id=data.get("controlling_faction_id"),
            present_faction_ids=data.get("present_faction_ids", []),
            asset_ids=data.get("asset_ids", []),
            tags=data.get("tags", []),
            atmosphere=data.get("atmosphere", []),
            landmarks=data.get("landmarks", []),
            notes=data.get("notes", ""),
        )

    def _build_faction(self, data: dict) -> Faction:
        base_data = {
            "id": data["id"],
            "name": data["name"],
            "faction_type": data["faction_type"],
            "tier": data.get("tier", 0),
            "hold": Hold(data.get("hold", Hold.STRONG.value)),
            "status": FactionStatus(data.get("status", FactionStatus.ACTIVE.value)),
            "focus_level": FocusLevel(data.get("focus_level", FocusLevel.ACTIVE.value)),
            "district_ids": data.get("district_ids", []),
            "street_ids": data.get("street_ids", []),
            "asset_ids": data.get("asset_ids", []),
            "clock_ids": data.get("clock_ids", []),
            "notes": data.get("notes", ""),
        }

        if data.get("faction_type") == "crew" or "crew_type" in data:
            return PlayerCrew(
                **base_data,
                crew_type=data.get("crew_type", ""),
                reputation=data.get("reputation", 0),
                heat=data.get("heat", 0),
                wanted_level=data.get("wanted_level", 0),
                coin=data.get("coin", 0),
                lair_id=data.get("lair_id"),
                crew_xp=data.get("crew_xp", 0),
                upgrades=data.get("upgrades", []),
                claims=data.get("claims", []),
            )

        return NpcFaction(
            **base_data,
            leader=data.get("leader", ""),
            public_goal=data.get("public_goal", ""),
            hidden_goal=data.get("hidden_goal", ""),
            preferred_actions=data.get("preferred_actions", []),
            enemies=data.get("enemies", []),
            allies=data.get("allies", []),
            resources=data.get("resources", []),
            vulnerabilities=data.get("vulnerabilities", []),
        )

    def _build_clock(self, data: dict) -> Clock:
        completion_effects = [
            self._build_clock_effect(effect_data)
            for effect_data in data.get("completion_effects", [])
        ]

        return Clock(
            id=data["id"],
            name=data["name"],
            clock_type=ClockType(data.get("clock_type", ClockType.PROJECT.value)),
            max_segments=data["max_segments"],
            current_segments=data.get("current_segments", 0),
            owner_faction_id=data.get("owner_faction_id"),
            target_faction_id=data.get("target_faction_id"),
            district_id=data.get("district_id"),
            street_id=data.get("street_id"),
            status=ClockStatus(data.get("status", ClockStatus.ACTIVE.value)),
            visibility=Visibility(data.get("visibility", Visibility.GM_ONLY.value)),
            trigger_on_complete=data.get("trigger_on_complete", ""),
            notes=data.get("notes", ""),
            advance_mode=ClockAdvanceMode(
                data.get("advance_mode", ClockAdvanceMode.AUTO_WEEKLY.value)
            ),
            action_category=ClockActionCategory(
                data.get("action_category", ClockActionCategory.PROJECT.value)
            ),
            priority=data.get("priority", 3),
            progress_per_week=data.get("progress_per_week", 1),
            advance_condition=data.get("advance_condition", {}),
            auto_advance=data.get("auto_advance", True),
            effects_applied=data.get("effects_applied", False),
            completion_effects=completion_effects,
        )

    def _build_clock_effect(self, data: dict) -> ClockEffect:
        return ClockEffect(
            effect_type=ClockEffectType(data["effect_type"]),
            target_faction_id=data.get("target_faction_id"),
            secondary_faction_id=data.get("secondary_faction_id"),
            target_clock_id=data.get("target_clock_id"),
            street_id=data.get("street_id"),
            value=data.get("value"),
            amount=data.get("amount", 0),
            description=data.get("description", ""),
        )

    def _build_relation(self, data: dict) -> Relation:
        return Relation(
            id=data["id"],
            faction_a_id=data["faction_a_id"],
            faction_b_id=data["faction_b_id"],
            value=data.get("value", 0),
            reason=data.get("reason", ""),
            is_public=data.get("is_public", False),
            notes=data.get("notes", ""),
        )

    def _build_event(self, data: dict) -> CityEvent:
        return CityEvent(
            id=data["id"],
            week=data["week"],
            event_type=EventType(data.get("event_type", EventType.MANUAL_CHANGE.value)),
            title=data["title"],
            description=data.get("description", ""),
            faction_ids=data.get("faction_ids", []),
            clock_ids=data.get("clock_ids", []),
            district_id=data.get("district_id"),
            street_id=data.get("street_id"),
            visibility=Visibility(data.get("visibility", Visibility.GM_ONLY.value)),
            consequences=data.get("consequences", []),
            created_by=data.get("created_by", "system"),
        )
from uuid import uuid4

from app.domain.enums import (
    ClockStatus,
    EventType,
    FactionStatus,
    Hold,
    Visibility,
)
from app.domain.models import (
    Campaign,
    CityEvent,
    Clock,
    Faction,
    NpcFaction,
    Relation,
)
from services.clock_service import ClockService


class GMActionService:
    def __init__(self) -> None:
        self.clock_service = ClockService()

    def get_relation_value(
        self,
        campaign: Campaign,
        faction_a_id: str,
        faction_b_id: str,
    ) -> int:
        relation = self._find_relation(campaign, faction_a_id, faction_b_id)

        if relation is None:
            return 0

        return relation.value

    def set_relation_with_crew(
        self,
        campaign: Campaign,
        faction_id: str,
        new_value: int,
        reason: str = "",
    ) -> CityEvent:
        crew_id = campaign.player_crew_id

        if faction_id == crew_id:
            raise ValueError("Нельзя менять отношение команды игроков к самой себе.")

        faction = self._get_faction(campaign, faction_id)
        crew = self._get_faction(campaign, crew_id)

        relation = self._find_relation(campaign, crew_id, faction_id)
        old_value = relation.value if relation is not None else 0
        new_value = self._clamp_relation(new_value)

        if relation is None:
            relation = Relation(
                id=f"rel_{crew_id}_{faction_id}",
                faction_a_id=crew_id,
                faction_b_id=faction_id,
                value=new_value,
                reason=reason,
            )
            campaign.city.relations[relation.id] = relation
        else:
            relation.value = new_value
            relation.reason = reason or relation.reason

        event = self._create_event(
            campaign=campaign,
            event_type=EventType.MANUAL_CHANGE,
            title=f"Изменено отношение: {crew.name} и {faction.name}",
            description=(
                f"Отношение изменено с {old_value} на {new_value}. "
                f"Причина: {reason or 'не указана'}."
            ),
            faction_ids=[crew_id, faction_id],
            consequences=[f"relation {old_value} -> {new_value}"],
            created_by="gm_action",
        )

        self._add_event(campaign, event)

        return event

    def set_faction_tier(
        self,
        campaign: Campaign,
        faction_id: str,
        new_tier: int,
        reason: str = "",
    ) -> CityEvent:
        faction = self._get_faction(campaign, faction_id)

        old_tier = faction.tier
        faction.tier = max(0, min(new_tier, 6))

        event = self._create_event(
            campaign=campaign,
            event_type=EventType.MANUAL_CHANGE,
            title=f"{faction.name}: изменен ранг",
            description=(
                f"Ранг изменен с {old_tier} на {faction.tier}. "
                f"Причина: {reason or 'не указана'}."
            ),
            faction_ids=[faction.id],
            consequences=[f"tier {old_tier} -> {faction.tier}"],
            created_by="gm_action",
        )

        self._add_event(campaign, event)

        return event

    def set_faction_hold(
        self,
        campaign: Campaign,
        faction_id: str,
        new_hold: Hold,
        reason: str = "",
    ) -> CityEvent:
        faction = self._get_faction(campaign, faction_id)

        old_hold = faction.hold
        faction.hold = new_hold

        event = self._create_event(
            campaign=campaign,
            event_type=EventType.MANUAL_CHANGE,
            title=f"{faction.name}: изменен контроль",
            description=(
                f"Контроль изменен с {old_hold.value} на {new_hold.value}. "
                f"Причина: {reason or 'не указана'}."
            ),
            faction_ids=[faction.id],
            consequences=[f"hold {old_hold.value} -> {new_hold.value}"],
            created_by="gm_action",
        )

        self._add_event(campaign, event)

        return event

    def set_faction_status(
        self,
        campaign: Campaign,
        faction_id: str,
        new_status: FactionStatus,
        reason: str = "",
    ) -> CityEvent:
        faction = self._get_faction(campaign, faction_id)

        old_status = faction.status
        faction.status = new_status

        event = self._create_event(
            campaign=campaign,
            event_type=EventType.MANUAL_CHANGE,
            title=f"{faction.name}: изменен статус",
            description=(
                f"Статус изменен с {old_status.value} на {new_status.value}. "
                f"Причина: {reason or 'не указана'}."
            ),
            faction_ids=[faction.id],
            consequences=[f"status {old_status.value} -> {new_status.value}"],
            created_by="gm_action",
        )

        self._add_event(campaign, event)

        return event

    def set_faction_notes(
        self,
        campaign: Campaign,
        faction_id: str,
        new_notes: str,
        reason: str = "",
    ) -> CityEvent:
        faction = self._get_faction(campaign, faction_id)

        faction.notes = new_notes

        event = self._create_event(
            campaign=campaign,
            event_type=EventType.MANUAL_CHANGE,
            title=f"{faction.name}: обновлены заметки",
            description=(
                f"Заметки фракции обновлены. "
                f"Причина: {reason or 'не указана'}."
            ),
            faction_ids=[faction.id],
            consequences=["notes updated"],
            created_by="gm_action",
        )

        self._add_event(campaign, event)

        return event

    def set_npc_public_goal(
        self,
        campaign: Campaign,
        faction_id: str,
        new_goal: str,
        reason: str = "",
    ) -> CityEvent:
        faction = self._get_npc_faction(campaign, faction_id)

        old_goal = faction.public_goal
        faction.public_goal = new_goal

        event = self._create_event(
            campaign=campaign,
            event_type=EventType.MANUAL_CHANGE,
            title=f"{faction.name}: изменена публичная цель",
            description=(
                f"Старая цель: {old_goal or 'не указана'}. "
                f"Новая цель: {new_goal or 'не указана'}. "
                f"Причина: {reason or 'не указана'}."
            ),
            faction_ids=[faction.id],
            consequences=["public goal updated"],
            created_by="gm_action",
        )

        self._add_event(campaign, event)

        return event

    def set_npc_hidden_goal(
        self,
        campaign: Campaign,
        faction_id: str,
        new_goal: str,
        reason: str = "",
    ) -> CityEvent:
        faction = self._get_npc_faction(campaign, faction_id)

        old_goal = faction.hidden_goal
        faction.hidden_goal = new_goal

        event = self._create_event(
            campaign=campaign,
            event_type=EventType.MANUAL_CHANGE,
            title=f"{faction.name}: изменена скрытая цель",
            description=(
                f"Старая цель: {old_goal or 'не указана'}. "
                f"Новая цель: {new_goal or 'не указана'}. "
                f"Причина: {reason or 'не указана'}."
            ),
            faction_ids=[faction.id],
            consequences=["hidden goal updated"],
            created_by="gm_action",
        )

        self._add_event(campaign, event)

        return event

    def advance_faction_clock(
        self,
        campaign: Campaign,
        faction_id: str,
        clock_id: str,
        amount: int,
        reason: str = "",
    ) -> list[CityEvent]:
        faction = self._get_faction(campaign, faction_id)
        clock = self._get_clock(campaign, clock_id)

        old_progress = clock.current_segments
        completed = self.clock_service.advance(clock, amount)

        events = []

        progress_event = self._create_event(
            campaign=campaign,
            event_type=EventType.MANUAL_CHANGE,
            title=f"{faction.name}: счетчик продвинут вручную",
            description=(
                f"Счетчик '{clock.name}' изменен с "
                f"{old_progress}/{clock.max_segments} на "
                f"{clock.current_segments}/{clock.max_segments}. "
                f"Причина: {reason or 'не указана'}."
            ),
            faction_ids=[faction.id],
            clock_ids=[clock.id],
            district_id=clock.district_id,
            street_id=clock.street_id,
            consequences=[f"clock +{amount}"],
            created_by="gm_action",
        )

        self._add_event(campaign, progress_event)
        events.append(progress_event)

        if completed:
            completed_event = self._create_event(
                campaign=campaign,
                event_type=EventType.CLOCK_COMPLETED,
                title=f"{faction.name}: счетчик заполнен",
                description=(
                    f"Счетчик '{clock.name}' заполнен. "
                    "Ведущий должен выбрать итоговое последствие."
                ),
                faction_ids=[faction.id],
                clock_ids=[clock.id],
                district_id=clock.district_id,
                street_id=clock.street_id,
                consequences=[clock.trigger_on_complete],
                created_by="gm_action",
            )

            self._add_event(campaign, completed_event)
            events.append(completed_event)

        return events

    def reduce_faction_clock(
        self,
        campaign: Campaign,
        faction_id: str,
        clock_id: str,
        amount: int,
        reason: str = "",
    ) -> CityEvent:
        faction = self._get_faction(campaign, faction_id)
        clock = self._get_clock(campaign, clock_id)

        old_progress = clock.current_segments
        self.clock_service.reduce(clock, amount)

        event = self._create_event(
            campaign=campaign,
            event_type=EventType.MANUAL_CHANGE,
            title=f"{faction.name}: счетчик откатан вручную",
            description=(
                f"Счетчик '{clock.name}' изменен с "
                f"{old_progress}/{clock.max_segments} на "
                f"{clock.current_segments}/{clock.max_segments}. "
                f"Причина: {reason or 'не указана'}."
            ),
            faction_ids=[faction.id],
            clock_ids=[clock.id],
            district_id=clock.district_id,
            street_id=clock.street_id,
            consequences=[f"clock -{amount}"],
            created_by="gm_action",
        )

        self._add_event(campaign, event)

        return event

    def _get_faction(self, campaign: Campaign, faction_id: str) -> Faction:
        faction = campaign.city.factions.get(faction_id)

        if faction is None:
            raise ValueError(f"Фракция не найдена: {faction_id}")

        return faction

    def _get_npc_faction(self, campaign: Campaign, faction_id: str) -> NpcFaction:
        faction = self._get_faction(campaign, faction_id)

        if not isinstance(faction, NpcFaction):
            raise ValueError(f"Фракция не является NPC-фракцией: {faction_id}")

        return faction

    def _get_clock(self, campaign: Campaign, clock_id: str) -> Clock:
        clock = campaign.city.clocks.get(clock_id)

        if clock is None:
            raise ValueError(f"Счетчик не найден: {clock_id}")

        return clock

    def _find_relation(
        self,
        campaign: Campaign,
        faction_a_id: str,
        faction_b_id: str,
    ) -> Relation | None:
        for relation in campaign.city.relations.values():
            direct_match = (
                relation.faction_a_id == faction_a_id
                and relation.faction_b_id == faction_b_id
            )
            reverse_match = (
                relation.faction_a_id == faction_b_id
                and relation.faction_b_id == faction_a_id
            )

            if direct_match or reverse_match:
                return relation

        return None

    def _clamp_relation(self, value: int) -> int:
        return max(-3, min(value, 3))

    def _create_event(
        self,
        campaign: Campaign,
        event_type: EventType,
        title: str,
        description: str = "",
        faction_ids: list[str] | None = None,
        clock_ids: list[str] | None = None,
        district_id: str | None = None,
        street_id: str | None = None,
        consequences: list[str] | None = None,
        created_by: str = "system",
    ) -> CityEvent:
        return CityEvent(
            id=str(uuid4()),
            week=campaign.current_week,
            event_type=event_type,
            title=title,
            description=description,
            faction_ids=faction_ids or [],
            clock_ids=clock_ids or [],
            district_id=district_id,
            street_id=street_id,
            visibility=Visibility.GM_ONLY,
            consequences=consequences or [],
            created_by=created_by,
        )

    def _add_event(self, campaign: Campaign, event: CityEvent) -> None:
        campaign.city.events[event.id] = event
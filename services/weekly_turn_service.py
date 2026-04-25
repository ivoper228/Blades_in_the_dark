from uuid import uuid4

from app.domain.enums import ClockStatus, EventType, Visibility
from app.domain.models import Campaign, CityEvent, NpcFaction

from services.clock_service import ClockService


class WeeklyTurnService:
    def __init__(self) -> None:
        self.clock_service = ClockService()

    def run_week(self, campaign: Campaign) -> list[CityEvent]:
        campaign.current_week += 1

        created_events: list[CityEvent] = []

        week_event = self._create_event(
            week=campaign.current_week,
            event_type=EventType.WEEK_STARTED,
            title=f"Началась неделя {campaign.current_week}",
            description="Город делает новый ход.",
            created_by="weekly_turn",
        )

        self._add_event(campaign, week_event)
        created_events.append(week_event)

        active_factions = self._get_active_npc_factions(campaign)

        for faction in active_factions:
            clock = self._get_first_active_clock(campaign, faction.clock_ids)

            if clock is None:
                continue

            completed = self.clock_service.advance(clock, amount=1)

            progress_event = self._create_event(
                week=campaign.current_week,
                event_type=EventType.CLOCK_PROGRESS,
                title=f"{faction.name}: счетчик продвинулся",
                description=(
                    f"Счетчик '{clock.name}' продвинут на 1. "
                    f"Прогресс: {clock.current_segments}/{clock.max_segments}."
                ),
                faction_ids=[faction.id],
                clock_ids=[clock.id],
                district_id=clock.district_id,
                street_id=clock.street_id,
                consequences=["clock +1"],
                created_by="weekly_turn",
            )

            self._add_event(campaign, progress_event)
            created_events.append(progress_event)

            if completed:
                completed_event = self._create_event(
                    week=campaign.current_week,
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
                    created_by="weekly_turn",
                )

                self._add_event(campaign, completed_event)
                created_events.append(completed_event)

        return created_events

    def _get_active_npc_factions(self, campaign: Campaign) -> list[NpcFaction]:
        factions: list[NpcFaction] = []

        for faction in campaign.city.factions.values():
            if isinstance(faction, NpcFaction) and faction.clock_ids:
                factions.append(faction)

        return factions

    def _get_first_active_clock(self, campaign: Campaign, clock_ids: list[str]):
        for clock_id in clock_ids:
            clock = campaign.city.clocks.get(clock_id)

            if clock is None:
                continue

            if clock.status == ClockStatus.ACTIVE:
                return clock

        return None

    def _create_event(
        self,
        week: int,
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
            week=week,
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
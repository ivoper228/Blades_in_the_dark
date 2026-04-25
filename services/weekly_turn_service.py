from uuid import uuid4

from app.domain.enums import ClockStatus, EventType, FactionStatus, Visibility
from app.domain.models import Campaign, CityEvent, Clock
from services.clock_effect_service import ClockEffectService
from services.clock_service import ClockService


class WeeklyTurnService:
    def __init__(self) -> None:
        self.clock_service = ClockService()
        self.clock_effect_service = ClockEffectService()

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

        active_clocks = self._get_auto_advance_clocks(campaign)

        for clock in active_clocks:
            owner_name = self._get_owner_name(campaign, clock)

            completed = self.clock_service.advance(clock, amount=1)

            progress_event = self._create_event(
                week=campaign.current_week,
                event_type=EventType.CLOCK_PROGRESS,
                title=f"{owner_name}: счетчик продвинулся",
                description=(
                    f"Счетчик '{clock.name}' продвинут на 1. "
                    f"Прогресс: {clock.current_segments}/{clock.max_segments}."
                ),
                faction_ids=[clock.owner_faction_id]
                if clock.owner_faction_id
                else [],
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
                    title=f"{owner_name}: счетчик заполнен",
                    description=(
                        f"Счетчик '{clock.name}' заполнен. "
                        "Автоэффекты будут применены сразу."
                    ),
                    faction_ids=[clock.owner_faction_id]
                    if clock.owner_faction_id
                    else [],
                    clock_ids=[clock.id],
                    district_id=clock.district_id,
                    street_id=clock.street_id,
                    consequences=[clock.trigger_on_complete],
                    created_by="weekly_turn",
                )

                self._add_event(campaign, completed_event)
                created_events.append(completed_event)

                effect_events = self.clock_effect_service.apply_completion_effects(
                    campaign=campaign,
                    source_clock=clock,
                )
                created_events.extend(effect_events)

        return created_events

    def _get_auto_advance_clocks(self, campaign: Campaign) -> list[Clock]:
        clocks = []

        for clock in campaign.city.clocks.values():
            if clock.status != ClockStatus.ACTIVE:
                continue

            if not clock.auto_advance:
                continue

            if clock.owner_faction_id is not None:
                faction = campaign.city.factions.get(clock.owner_faction_id)

                if faction is None:
                    continue

                if faction.status in [
                    FactionStatus.DESTROYED,
                    FactionStatus.HIDDEN,
                ]:
                    continue

            clocks.append(clock)

        return clocks

    def _get_owner_name(self, campaign: Campaign, clock: Clock) -> str:
        if clock.owner_faction_id is None:
            return "Город"

        faction = campaign.city.factions.get(clock.owner_faction_id)

        if faction is None:
            return "Неизвестная фракция"

        return faction.name

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
from typing import Callable
from uuid import uuid4

from app.domain.enums import (
    ClockActionCategory,
    ClockAdvanceMode,
    ClockStatus,
    EventType,
    FactionStatus,
    FocusLevel,
    Hold,
    Visibility,
)
from app.domain.models import Campaign, CityEvent, Clock, Faction
from services.clock_effect_service import ClockEffectService
from services.clock_service import ClockService


ConfirmationCallback = Callable[[Campaign, Clock], bool]


class WeeklyTurnService:
    def __init__(
        self,
        confirmation_callback: ConfirmationCallback | None = None,
    ) -> None:
        self.clock_service = ClockService()
        self.clock_effect_service = ClockEffectService()
        self.confirmation_callback = confirmation_callback

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

        active_factions = self._get_active_factions_sorted(campaign)

        for faction in active_factions:
            selected_clocks = self._select_clocks_for_faction(campaign, faction)

            for clock in selected_clocks:
                if not self._should_advance_clock(campaign, clock):
                    continue

                amount = max(1, clock.progress_per_week)
                completed = self.clock_service.advance(clock, amount=amount)

                progress_event = self._create_event(
                    week=campaign.current_week,
                    event_type=EventType.CLOCK_PROGRESS,
                    title=f"{faction.name}: счетчик продвинулся",
                    description=(
                        f"Счетчик '{clock.name}' продвинут на {amount}. "
                        f"Прогресс: {clock.current_segments}/{clock.max_segments}."
                    ),
                    faction_ids=[faction.id],
                    clock_ids=[clock.id],
                    district_id=clock.district_id,
                    street_id=clock.street_id,
                    consequences=[f"clock +{amount}"],
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
                            "Автоэффекты будут применены сразу."
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

                    effect_events = self.clock_effect_service.apply_completion_effects(
                        campaign=campaign,
                        source_clock=clock,
                    )
                    created_events.extend(effect_events)

        return created_events

    def _get_active_factions_sorted(self, campaign: Campaign) -> list[Faction]:
        factions = []

        for faction in campaign.city.factions.values():
            if faction.id == campaign.player_crew_id:
                continue

            if faction.status in [FactionStatus.DESTROYED, FactionStatus.HIDDEN]:
                continue

            if faction.focus_level == FocusLevel.DORMANT:
                continue

            if not faction.clock_ids:
                continue

            factions.append(faction)

        return sorted(
            factions,
            key=lambda faction: (
                -faction.tier,
                -self._hold_score(faction.hold),
                -self._focus_score(faction.focus_level),
                faction.name,
            ),
        )

    def _select_clocks_for_faction(
        self,
        campaign: Campaign,
        faction: Faction,
    ) -> list[Clock]:
        candidate_clocks = self._get_candidate_clocks(campaign, faction)

        main_clocks = [
            clock
            for clock in candidate_clocks
            if clock.action_category != ClockActionCategory.INVESTIGATION
        ]
        investigation_clocks = [
            clock
            for clock in candidate_clocks
            if clock.action_category == ClockActionCategory.INVESTIGATION
        ]

        action_points = self._get_action_points(faction)
        selected_main_clocks = self._select_main_clocks(main_clocks, action_points)
        selected_investigation_clocks = investigation_clocks[:1]

        return [*selected_main_clocks, *selected_investigation_clocks]

    def _get_candidate_clocks(
        self,
        campaign: Campaign,
        faction: Faction,
    ) -> list[Clock]:
        clocks = []

        for clock_id in faction.clock_ids:
            clock = campaign.city.clocks.get(clock_id)

            if clock is None:
                continue

            if clock.status != ClockStatus.ACTIVE:
                continue

            if not clock.auto_advance:
                continue

            if clock.advance_mode in [
                ClockAdvanceMode.MANUAL_ONLY,
                ClockAdvanceMode.REACTION,
            ]:
                continue

            if clock.advance_mode == ClockAdvanceMode.CONDITIONAL_WEEKLY:
                if not self._conditions_met(campaign, faction, clock):
                    continue

            clocks.append(clock)

        return sorted(
            clocks,
            key=lambda clock: (
                -clock.priority,
                clock.name,
            ),
        )

    def _select_main_clocks(
        self,
        clocks: list[Clock],
        action_points: int,
    ) -> list[Clock]:
        selected = []
        selected_attack = False
        selected_defense = False

        for clock in clocks:
            if len(selected) >= action_points:
                break

            if clock.action_category == ClockActionCategory.ATTACK and selected_defense:
                continue

            if clock.action_category == ClockActionCategory.DEFENSE and selected_attack:
                continue

            selected.append(clock)

            if clock.action_category == ClockActionCategory.ATTACK:
                selected_attack = True

            if clock.action_category == ClockActionCategory.DEFENSE:
                selected_defense = True

        return selected

    def _should_advance_clock(self, campaign: Campaign, clock: Clock) -> bool:
        if clock.advance_mode == ClockAdvanceMode.AUTO_WEEKLY:
            return True

        if clock.advance_mode == ClockAdvanceMode.CONDITIONAL_WEEKLY:
            return True

        if clock.advance_mode == ClockAdvanceMode.GM_CONFIRM_WEEKLY:
            if self.confirmation_callback is None:
                return False

            return self.confirmation_callback(campaign, clock)

        return False

    def _conditions_met(
        self,
        campaign: Campaign,
        faction: Faction,
        clock: Clock,
    ) -> bool:
        if not clock.advance_condition:
            return True

        owner_hold = clock.advance_condition.get("owner_hold")
        if owner_hold is not None and faction.hold.value != owner_hold:
            return False

        owner_status = clock.advance_condition.get("owner_status")
        if owner_status is not None and faction.status.value != owner_status:
            return False

        target_status = clock.advance_condition.get("target_status")
        if target_status is not None:
            target_faction = campaign.city.factions.get(clock.target_faction_id)

            if target_faction is None:
                return False

            if target_faction.status.value != target_status:
                return False

        relation_lte = clock.advance_condition.get("relation_with_target_lte")
        if relation_lte is not None:
            relation_value = self._get_relation_value(
                campaign=campaign,
                faction_a_id=clock.owner_faction_id,
                faction_b_id=clock.target_faction_id,
            )

            if relation_value > relation_lte:
                return False

        relation_gte = clock.advance_condition.get("relation_with_target_gte")
        if relation_gte is not None:
            relation_value = self._get_relation_value(
                campaign=campaign,
                faction_a_id=clock.owner_faction_id,
                faction_b_id=clock.target_faction_id,
            )

            if relation_value < relation_gte:
                return False

        street_controlled_by_owner = clock.advance_condition.get(
            "street_controlled_by_owner"
        )
        if street_controlled_by_owner is not None:
            street = campaign.city.streets.get(clock.street_id)

            if street is None:
                return False

            is_controlled = street.controlling_faction_id == clock.owner_faction_id

            if is_controlled != street_controlled_by_owner:
                return False

        return True

    def _get_action_points(self, faction: Faction) -> int:
        if faction.tier >= 3:
            return 2

        return 1

    def _get_relation_value(
        self,
        campaign: Campaign,
        faction_a_id: str | None,
        faction_b_id: str | None,
    ) -> int:
        if faction_a_id is None or faction_b_id is None:
            return 0

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
                return relation.value

        return 0

    def _hold_score(self, hold: Hold) -> int:
        if hold == Hold.STRONG:
            return 2

        return 1

    def _focus_score(self, focus_level: FocusLevel) -> int:
        if focus_level == FocusLevel.SPOTLIGHT:
            return 4

        if focus_level == FocusLevel.ACTIVE:
            return 3

        if focus_level == FocusLevel.BACKGROUND:
            return 2

        return 1

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
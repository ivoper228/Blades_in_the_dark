from uuid import uuid4

from app.domain.enums import (
    ClockEffectType,
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
    ClockEffect,
    PlayerCrew,
    Relation,
)
from services.clock_service import ClockService


class ClockEffectService:
    def __init__(self) -> None:
        self.clock_service = ClockService()

    def apply_completion_effects(
        self,
        campaign: Campaign,
        source_clock: Clock,
        recursion_depth: int = 0,
    ) -> list[CityEvent]:
        if recursion_depth > 5:
            return []

        if source_clock.effects_applied:
            return []

        events: list[CityEvent] = []

        for effect in source_clock.completion_effects:
            event = self._apply_effect(campaign, source_clock, effect)

            if event is not None:
                self._add_event(campaign, event)
                events.append(event)

            if effect.effect_type == ClockEffectType.ADVANCE_CLOCK:
                nested_events = self._apply_nested_clock_completion(
                    campaign=campaign,
                    effect=effect,
                    recursion_depth=recursion_depth,
                )
                events.extend(nested_events)

        source_clock.effects_applied = True

        if source_clock.status == ClockStatus.COMPLETED:
            source_clock.status = ClockStatus.RESOLVED

        return events

    def _apply_effect(
        self,
        campaign: Campaign,
        source_clock: Clock,
        effect: ClockEffect,
    ) -> CityEvent | None:
        if effect.effect_type == ClockEffectType.CHANGE_FACTION_TIER:
            return self._change_faction_tier(campaign, source_clock, effect)

        if effect.effect_type == ClockEffectType.SET_FACTION_TIER:
            return self._set_faction_tier(campaign, source_clock, effect)

        if effect.effect_type == ClockEffectType.SET_FACTION_HOLD:
            return self._set_faction_hold(campaign, source_clock, effect)

        if effect.effect_type == ClockEffectType.SET_FACTION_STATUS:
            return self._set_faction_status(campaign, source_clock, effect)

        if effect.effect_type == ClockEffectType.CHANGE_RELATION:
            return self._change_relation(campaign, source_clock, effect)

        if effect.effect_type == ClockEffectType.TRANSFER_STREET_CONTROL:
            return self._transfer_street_control(campaign, source_clock, effect)

        if effect.effect_type == ClockEffectType.ADVANCE_CLOCK:
            return self._advance_clock(campaign, source_clock, effect)

        if effect.effect_type == ClockEffectType.CHANGE_CREW_HEAT:
            return self._change_crew_heat(campaign, source_clock, effect)

        if effect.effect_type == ClockEffectType.CHANGE_CREW_WANTED_LEVEL:
            return self._change_crew_wanted_level(campaign, source_clock, effect)

        return None

    def _change_faction_tier(
        self,
        campaign: Campaign,
        source_clock: Clock,
        effect: ClockEffect,
    ) -> CityEvent:
        faction = self._get_faction(campaign, effect.target_faction_id)

        old_value = faction.tier
        faction.tier = self._clamp_tier(faction.tier + effect.amount)

        return self._create_effect_event(
            campaign=campaign,
            source_clock=source_clock,
            effect=effect,
            title=f"{faction.name}: изменен ранг",
            description=(
                f"Из-за завершения счетчика '{source_clock.name}' "
                f"ранг изменен с {old_value} на {faction.tier}."
            ),
            faction_ids=[faction.id],
            consequences=[f"tier {old_value} -> {faction.tier}"],
        )

    def _set_faction_tier(
        self,
        campaign: Campaign,
        source_clock: Clock,
        effect: ClockEffect,
    ) -> CityEvent:
        faction = self._get_faction(campaign, effect.target_faction_id)

        old_value = faction.tier
        faction.tier = self._clamp_tier(int(effect.value))

        return self._create_effect_event(
            campaign=campaign,
            source_clock=source_clock,
            effect=effect,
            title=f"{faction.name}: установлен ранг",
            description=(
                f"Из-за завершения счетчика '{source_clock.name}' "
                f"ранг изменен с {old_value} на {faction.tier}."
            ),
            faction_ids=[faction.id],
            consequences=[f"tier {old_value} -> {faction.tier}"],
        )

    def _set_faction_hold(
        self,
        campaign: Campaign,
        source_clock: Clock,
        effect: ClockEffect,
    ) -> CityEvent:
        faction = self._get_faction(campaign, effect.target_faction_id)

        old_value = faction.hold
        faction.hold = Hold(effect.value)

        return self._create_effect_event(
            campaign=campaign,
            source_clock=source_clock,
            effect=effect,
            title=f"{faction.name}: изменен контроль",
            description=(
                f"Из-за завершения счетчика '{source_clock.name}' "
                f"контроль изменен с {old_value.value} на {faction.hold.value}."
            ),
            faction_ids=[faction.id],
            consequences=[f"hold {old_value.value} -> {faction.hold.value}"],
        )

    def _set_faction_status(
        self,
        campaign: Campaign,
        source_clock: Clock,
        effect: ClockEffect,
    ) -> CityEvent:
        faction = self._get_faction(campaign, effect.target_faction_id)

        old_value = faction.status
        faction.status = FactionStatus(effect.value)

        return self._create_effect_event(
            campaign=campaign,
            source_clock=source_clock,
            effect=effect,
            title=f"{faction.name}: изменен статус",
            description=(
                f"Из-за завершения счетчика '{source_clock.name}' "
                f"статус изменен с {old_value.value} на {faction.status.value}."
            ),
            faction_ids=[faction.id],
            consequences=[f"status {old_value.value} -> {faction.status.value}"],
        )

    def _change_relation(
        self,
        campaign: Campaign,
        source_clock: Clock,
        effect: ClockEffect,
    ) -> CityEvent:
        faction_a = self._get_faction(campaign, effect.target_faction_id)
        faction_b = self._get_faction(campaign, effect.secondary_faction_id)

        relation = self._find_relation(campaign, faction_a.id, faction_b.id)
        old_value = relation.value if relation is not None else 0
        new_value = self._clamp_relation(old_value + effect.amount)

        if relation is None:
            relation = Relation(
                id=f"rel_{faction_a.id}_{faction_b.id}",
                faction_a_id=faction_a.id,
                faction_b_id=faction_b.id,
                value=new_value,
                reason=f"Автоэффект счетчика: {source_clock.name}",
            )
            campaign.city.relations[relation.id] = relation
        else:
            relation.value = new_value
            relation.reason = f"Автоэффект счетчика: {source_clock.name}"

        return self._create_effect_event(
            campaign=campaign,
            source_clock=source_clock,
            effect=effect,
            title=f"Изменены отношения: {faction_a.name} и {faction_b.name}",
            description=(
                f"Из-за завершения счетчика '{source_clock.name}' "
                f"отношение изменено с {old_value} на {new_value}."
            ),
            faction_ids=[faction_a.id, faction_b.id],
            consequences=[f"relation {old_value} -> {new_value}"],
        )

    def _transfer_street_control(
        self,
        campaign: Campaign,
        source_clock: Clock,
        effect: ClockEffect,
    ) -> CityEvent:
        street = campaign.city.streets.get(effect.street_id)

        if street is None:
            raise ValueError(f"Улица не найдена: {effect.street_id}")

        new_owner = self._get_faction(campaign, effect.target_faction_id)
        old_owner_id = street.controlling_faction_id
        old_owner_name = "никто"

        if old_owner_id is not None:
            old_owner = campaign.city.factions.get(old_owner_id)

            if old_owner is not None:
                old_owner_name = old_owner.name

                if street.id in old_owner.street_ids:
                    old_owner.street_ids.remove(street.id)

        street.controlling_faction_id = new_owner.id

        if street.id not in new_owner.street_ids:
            new_owner.street_ids.append(street.id)

        return self._create_effect_event(
            campaign=campaign,
            source_clock=source_clock,
            effect=effect,
            title=f"{new_owner.name}: получен контроль улицы",
            description=(
                f"Из-за завершения счетчика '{source_clock.name}' "
                f"улица '{street.name}' перешла от '{old_owner_name}' "
                f"к '{new_owner.name}'."
            ),
            faction_ids=[new_owner.id],
            street_id=street.id,
            consequences=[f"street control {old_owner_id} -> {new_owner.id}"],
        )

    def _advance_clock(
        self,
        campaign: Campaign,
        source_clock: Clock,
        effect: ClockEffect,
    ) -> CityEvent:
        target_clock = self._get_clock(campaign, effect.target_clock_id)

        old_value = target_clock.current_segments
        self.clock_service.advance(target_clock, effect.amount)

        return self._create_effect_event(
            campaign=campaign,
            source_clock=source_clock,
            effect=effect,
            title=f"Продвинут связанный счетчик: {target_clock.name}",
            description=(
                f"Из-за завершения счетчика '{source_clock.name}' "
                f"счетчик '{target_clock.name}' изменен с "
                f"{old_value}/{target_clock.max_segments} на "
                f"{target_clock.current_segments}/{target_clock.max_segments}."
            ),
            faction_ids=[target_clock.owner_faction_id]
            if target_clock.owner_faction_id
            else [],
            clock_ids=[target_clock.id],
            consequences=[f"clock +{effect.amount}"],
        )

    def _change_crew_heat(
        self,
        campaign: Campaign,
        source_clock: Clock,
        effect: ClockEffect,
    ) -> CityEvent:
        crew = self._get_player_crew(campaign)

        old_value = crew.heat
        crew.heat = max(0, crew.heat + effect.amount)

        return self._create_effect_event(
            campaign=campaign,
            source_clock=source_clock,
            effect=effect,
            title=f"{crew.name}: изменены подозрения",
            description=(
                f"Из-за завершения счетчика '{source_clock.name}' "
                f"подозрения изменены с {old_value} на {crew.heat}."
            ),
            faction_ids=[crew.id],
            consequences=[f"heat {old_value} -> {crew.heat}"],
        )

    def _change_crew_wanted_level(
        self,
        campaign: Campaign,
        source_clock: Clock,
        effect: ClockEffect,
    ) -> CityEvent:
        crew = self._get_player_crew(campaign)

        old_value = crew.wanted_level
        crew.wanted_level = max(0, crew.wanted_level + effect.amount)

        return self._create_effect_event(
            campaign=campaign,
            source_clock=source_clock,
            effect=effect,
            title=f"{crew.name}: изменен уровень розыска",
            description=(
                f"Из-за завершения счетчика '{source_clock.name}' "
                f"уровень розыска изменен с {old_value} на {crew.wanted_level}."
            ),
            faction_ids=[crew.id],
            consequences=[f"wanted {old_value} -> {crew.wanted_level}"],
        )

    def _apply_nested_clock_completion(
        self,
        campaign: Campaign,
        effect: ClockEffect,
        recursion_depth: int,
    ) -> list[CityEvent]:
        target_clock = self._get_clock(campaign, effect.target_clock_id)

        if target_clock.status != ClockStatus.COMPLETED:
            return []

        completion_event = self._create_effect_event(
            campaign=campaign,
            source_clock=target_clock,
            effect=effect,
            title=f"Связанный счетчик заполнен: {target_clock.name}",
            description=(
                f"Счетчик '{target_clock.name}' был заполнен связанным эффектом."
            ),
            faction_ids=[target_clock.owner_faction_id]
            if target_clock.owner_faction_id
            else [],
            clock_ids=[target_clock.id],
            consequences=[target_clock.trigger_on_complete],
        )
        self._add_event(campaign, completion_event)

        nested_events = self.apply_completion_effects(
            campaign=campaign,
            source_clock=target_clock,
            recursion_depth=recursion_depth + 1,
        )

        return [completion_event, *nested_events]

    def _get_faction(self, campaign: Campaign, faction_id: str | None):
        if faction_id is None:
            raise ValueError("Не указан id фракции.")

        faction = campaign.city.factions.get(faction_id)

        if faction is None:
            raise ValueError(f"Фракция не найдена: {faction_id}")

        return faction

    def _get_player_crew(self, campaign: Campaign) -> PlayerCrew:
        crew = self._get_faction(campaign, campaign.player_crew_id)

        if not isinstance(crew, PlayerCrew):
            raise ValueError("Фракция игроков не является PlayerCrew.")

        return crew

    def _get_clock(self, campaign: Campaign, clock_id: str | None) -> Clock:
        if clock_id is None:
            raise ValueError("Не указан id счетчика.")

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

    def _clamp_tier(self, value: int) -> int:
        return max(0, min(value, 6))

    def _clamp_relation(self, value: int) -> int:
        return max(-3, min(value, 3))

    def _create_effect_event(
        self,
        campaign: Campaign,
        source_clock: Clock,
        effect: ClockEffect,
        title: str,
        description: str,
        faction_ids: list[str] | None = None,
        clock_ids: list[str] | None = None,
        street_id: str | None = None,
        consequences: list[str] | None = None,
    ) -> CityEvent:
        description_parts = [description]

        if effect.description:
            description_parts.append(f"Описание эффекта: {effect.description}")

        return CityEvent(
            id=str(uuid4()),
            week=campaign.current_week,
            event_type=EventType.CLOCK_EFFECT_APPLIED,
            title=title,
            description=" ".join(description_parts),
            faction_ids=[
                faction_id
                for faction_id in (faction_ids or [])
                if faction_id is not None
            ],
            clock_ids=clock_ids or [source_clock.id],
            district_id=source_clock.district_id,
            street_id=street_id or source_clock.street_id,
            visibility=Visibility.GM_ONLY,
            consequences=consequences or [],
            created_by="clock_effect",
        )

    def _add_event(self, campaign: Campaign, event: CityEvent) -> None:
        campaign.city.events[event.id] = event
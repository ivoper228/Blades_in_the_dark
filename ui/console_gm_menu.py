from app.domain.enums import (
    ClockActionCategory,
    ClockAdvanceMode,
    ClockEffectType,
    ClockStatus,
    ClockType,
    FactionStatus,
    Hold,
)
from app.domain.models import Campaign, ClockEffect, Faction, NpcFaction
from services.gm_action_service import GMActionService
from services.weekly_turn_service import WeeklyTurnService
from storage.json_storage import JsonStorage


class ConsoleGMMenu:
    def __init__(
        self,
        campaign: Campaign,
        save_path: str = "saves/campaign_current.json",
    ) -> None:
        self.campaign = campaign
        self.save_path = save_path
        self.gm_action_service = GMActionService()
        self.weekly_turn_service = WeeklyTurnService(
            confirmation_callback=self.confirm_clock_advance,
        )
        self.storage = JsonStorage()

    def run(self) -> None:
        while True:
            print()
            print("=== GM MENU ===")
            print(f"Кампания: {self.campaign.name}")
            print(f"Текущая неделя: {self.campaign.current_week}")
            print()
            print("1. Показать фракции")
            print("2. Изменить фракцию")
            print("3. Запустить новую неделю")
            print("4. Показать журнал событий")
            print("5. Сохранить кампанию")
            print("6. Создать счетчик")
            print("7. Добавить эффект к счетчику")
            print("0. Выйти")
            print()

            choice = input("> ").strip()

            if choice == "1":
                self.show_factions()
            elif choice == "2":
                self.edit_faction_menu()
            elif choice == "3":
                self.run_week()
            elif choice == "4":
                self.show_events()
            elif choice == "5":
                self.save_campaign()
            elif choice == "6":
                self.create_clock_menu()
            elif choice == "7":
                self.add_clock_effect_menu()
            elif choice == "0":
                self.exit_menu()
                break
            else:
                print("Неизвестная команда.")

    def show_factions(self) -> None:
        print()
        print("=== ФРАКЦИИ ===")

        for faction in self.campaign.city.factions.values():
            relation_with_crew = self._get_relation_with_crew(faction)

            print()
            print(f"{faction.id}: {faction.name}")
            print(f"  Тип: {faction.faction_type}")
            print(f"  Ранг: {faction.tier}")
            print(f"  Контроль: {faction.hold.value}")
            print(f"  Статус: {faction.status.value}")

            if faction.id != self.campaign.player_crew_id:
                print(f"  Отношение с командой: {relation_with_crew}")

            if faction.clock_ids:
                print("  Счетчики:")

                for clock_id in faction.clock_ids:
                    clock = self.campaign.city.clocks.get(clock_id)

                    if clock is None:
                        continue
                    effects_count = len(clock.completion_effects)

                    print(
                        f"    - {clock.name}: "
                        f"{clock.current_segments}/{clock.max_segments} "
                        f"({clock.status.value}), "
                        f"эффектов: {effects_count}"
                    )

    def edit_faction_menu(self) -> None:
        faction = self._select_faction()

        if faction is None:
            return

        while True:
            self.show_faction_card(faction)

            print()
            print("Что изменить?")
            print("1. Отношение с командой игроков")
            print("2. Ранг")
            print("3. Контроль")
            print("4. Статус")
            print("5. Публичная цель")
            print("6. Скрытая цель")
            print("7. Заметки")
            print("8. Продвинуть счетчик")
            print("9. Откатить счетчик")
            print("0. Назад")
            print()

            choice = input("> ").strip()

            if choice == "1":
                self.change_relation_with_crew(faction)
            elif choice == "2":
                self.change_tier(faction)
            elif choice == "3":
                self.change_hold(faction)
            elif choice == "4":
                self.change_status(faction)
            elif choice == "5":
                self.change_public_goal(faction)
            elif choice == "6":
                self.change_hidden_goal(faction)
            elif choice == "7":
                self.change_notes(faction)
            elif choice == "8":
                self.advance_clock(faction)
            elif choice == "9":
                self.reduce_clock(faction)
            elif choice == "0":
                break
            else:
                print("Неизвестная команда.")

    def show_faction_card(self, faction: Faction) -> None:
        print()
        print("=== КАРТОЧКА ФРАКЦИИ ===")
        print(f"Название: {faction.name}")
        print(f"ID: {faction.id}")
        print(f"Тип: {faction.faction_type}")
        print(f"Ранг: {faction.tier}")
        print(f"Контроль: {faction.hold.value}")
        print(f"Статус: {faction.status.value}")

        if faction.id != self.campaign.player_crew_id:
            print(f"Отношение с командой: {self._get_relation_with_crew(faction)}")

        if isinstance(faction, NpcFaction):
            print(f"Лидер: {faction.leader or 'не указан'}")
            print(f"Публичная цель: {faction.public_goal or 'не указана'}")
            print(f"Скрытая цель: {faction.hidden_goal or 'не указана'}")

        print(f"Заметки: {faction.notes or 'нет'}")

        if faction.clock_ids:
            print("Счетчики:")

            for clock_id in faction.clock_ids:
                clock = self.campaign.city.clocks.get(clock_id)

                if clock is None:
                    continue

                effects_count = len(clock.completion_effects)

                print(
                    f"- {clock.id}: {clock.name} "
                    f"{clock.current_segments}/{clock.max_segments} "
                    f"({clock.status.value}), "
                    f"эффектов: {effects_count}"
                )
        else:
            print("Счетчики: нет")

    def change_relation_with_crew(self, faction: Faction) -> None:
        if faction.id == self.campaign.player_crew_id:
            print("У команды игроков нет отношения к самой себе.")
            return

        new_value = self._input_int(
            prompt="Новое отношение с командой от -3 до 3: ",
            min_value=-3,
            max_value=3,
        )
        reason = self._input_reason()

        event = self.gm_action_service.set_relation_with_crew(
            campaign=self.campaign,
            faction_id=faction.id,
            new_value=new_value,
            reason=reason,
        )

        print(f"Готово: {event.title}")

    def change_tier(self, faction: Faction) -> None:
        new_tier = self._input_int(
            prompt="Новый ранг от 0 до 6: ",
            min_value=0,
            max_value=6,
        )
        reason = self._input_reason()

        event = self.gm_action_service.set_faction_tier(
            campaign=self.campaign,
            faction_id=faction.id,
            new_tier=new_tier,
            reason=reason,
        )

        print(f"Готово: {event.title}")

    def change_hold(self, faction: Faction) -> None:
        print()
        print("Выбери контроль:")
        print("1. weak")
        print("2. strong")

        choice = input("> ").strip()

        if choice == "1":
            new_hold = Hold.WEAK
        elif choice == "2":
            new_hold = Hold.STRONG
        else:
            print("Неизвестный вариант.")
            return

        reason = self._input_reason()

        event = self.gm_action_service.set_faction_hold(
            campaign=self.campaign,
            faction_id=faction.id,
            new_hold=new_hold,
            reason=reason,
        )

        print(f"Готово: {event.title}")

    def change_status(self, faction: Faction) -> None:
        print()
        print("Выбери статус:")
        print("1. active")
        print("2. weakened")
        print("3. destroyed")
        print("4. hidden")

        choice = input("> ").strip()

        if choice == "1":
            new_status = FactionStatus.ACTIVE
        elif choice == "2":
            new_status = FactionStatus.WEAKENED
        elif choice == "3":
            new_status = FactionStatus.DESTROYED
        elif choice == "4":
            new_status = FactionStatus.HIDDEN
        else:
            print("Неизвестный вариант.")
            return

        reason = self._input_reason()

        event = self.gm_action_service.set_faction_status(
            campaign=self.campaign,
            faction_id=faction.id,
            new_status=new_status,
            reason=reason,
        )

        print(f"Готово: {event.title}")

    def change_public_goal(self, faction: Faction) -> None:
        if not isinstance(faction, NpcFaction):
            print("Публичная цель есть только у NPC-фракций.")
            return

        new_goal = input("Новая публичная цель: ").strip()
        reason = self._input_reason()

        event = self.gm_action_service.set_npc_public_goal(
            campaign=self.campaign,
            faction_id=faction.id,
            new_goal=new_goal,
            reason=reason,
        )

        print(f"Готово: {event.title}")

    def change_hidden_goal(self, faction: Faction) -> None:
        if not isinstance(faction, NpcFaction):
            print("Скрытая цель есть только у NPC-фракций.")
            return

        new_goal = input("Новая скрытая цель: ").strip()
        reason = self._input_reason()

        event = self.gm_action_service.set_npc_hidden_goal(
            campaign=self.campaign,
            faction_id=faction.id,
            new_goal=new_goal,
            reason=reason,
        )

        print(f"Готово: {event.title}")

    def change_notes(self, faction: Faction) -> None:
        print("Новые заметки:")
        new_notes = input("> ").strip()
        reason = self._input_reason()

        event = self.gm_action_service.set_faction_notes(
            campaign=self.campaign,
            faction_id=faction.id,
            new_notes=new_notes,
            reason=reason,
        )

        print(f"Готово: {event.title}")

    def advance_clock(self, faction: Faction) -> None:
        clock_id = self._select_faction_clock(faction)

        if clock_id is None:
            return

        amount = self._input_int(
            prompt="На сколько продвинуть счетчик: ",
            min_value=1,
            max_value=12,
        )
        reason = self._input_reason()

        events = self.gm_action_service.advance_faction_clock(
            campaign=self.campaign,
            faction_id=faction.id,
            clock_id=clock_id,
            amount=amount,
            reason=reason,
        )

        for event in events:
            print(f"Готово: {event.title}")

    def reduce_clock(self, faction: Faction) -> None:
        clock_id = self._select_faction_clock(faction)

        if clock_id is None:
            return

        amount = self._input_int(
            prompt="На сколько откатить счетчик: ",
            min_value=1,
            max_value=12,
        )
        reason = self._input_reason()

        event = self.gm_action_service.reduce_faction_clock(
            campaign=self.campaign,
            faction_id=faction.id,
            clock_id=clock_id,
            amount=amount,
            reason=reason,
        )

        print(f"Готово: {event.title}")
    def confirm_clock_advance(self, campaign: Campaign, clock) -> bool:
        owner_name = "Город"

        if clock.owner_faction_id is not None:
            owner = campaign.city.factions.get(clock.owner_faction_id)

            if owner is not None:
                owner_name = owner.name

        print()
        print("=== ПОДТВЕРЖДЕНИЕ СЧЕТЧИКА ===")
        print(f"Фракция: {owner_name}")
        print(f"Счетчик: {clock.name}")
        print(f"Прогресс: {clock.current_segments}/{clock.max_segments}")
        print(f"Категория: {clock.action_category.value}")
        print(f"Приоритет: {clock.priority}")
        print("Продвинуть этот счетчик на этой неделе?")
        print("1. Да")
        print("2. Нет")

        choice = input("> ").strip()

        return choice == "1"
    def add_clock_effect_menu(self) -> None:
        print()
        print("=== ДОБАВЛЕНИЕ ЭФФЕКТА К СЧЕТЧИКУ ===")

        owner = self._select_faction()

        if owner is None:
            return

        clock_id = self._select_faction_clock(owner)

        if clock_id is None:
            return

        effect_type = self._select_clock_effect_type()
        effect = self._build_clock_effect(effect_type)

        if effect is None:
            print("Эффект не создан.")
            return

        effect.description = input(
            "Описание эффекта, можно оставить пустым: "
        ).strip()

        reason = self._input_reason()

        event = self.gm_action_service.add_completion_effect_to_clock(
            campaign=self.campaign,
            clock_id=clock_id,
            effect=effect,
            reason=reason,
        )

        print()
        print(f"Готово: {event.title}")

    def _select_clock_effect_type(self) -> ClockEffectType:
        options = list(ClockEffectType)

        print()
        print("Выбери тип эффекта:")
        print("change_faction_tier - изменить ранг фракции на +N или -N")
        print("set_faction_tier - установить ранг фракции")
        print("set_faction_hold - установить контроль фракции")
        print("set_faction_status - установить статус фракции")
        print("change_relation - изменить отношения двух фракций")
        print("transfer_street_control - передать контроль улицы")
        print("advance_clock - продвинуть другой счетчик")
        print("change_crew_heat - изменить подозрения команды")
        print("change_crew_wanted_level - изменить уровень розыска команды")
        print()

        for index, item in enumerate(options, start=1):
            print(f"{index}. {item.value}")

        choice = self._input_int(
            prompt="> ",
            min_value=1,
            max_value=len(options),
        )

        return options[choice - 1]

    def _build_clock_effect(
        self,
        effect_type: ClockEffectType,
    ) -> ClockEffect | None:
        if effect_type == ClockEffectType.CHANGE_FACTION_TIER:
            target_faction_id = self._select_required_faction_id(
                "Выбери фракцию, чей ранг изменить:"
            )
            if target_faction_id is None:
                return None

            amount = self._input_int(
                prompt="На сколько изменить ранг, например -1 или 1: ",
                min_value=-6,
                max_value=6,
            )

            return ClockEffect(
                effect_type=effect_type,
                target_faction_id=target_faction_id,
                amount=amount,
            )

        if effect_type == ClockEffectType.SET_FACTION_TIER:
            target_faction_id = self._select_required_faction_id(
                "Выбери фракцию, чей ранг установить:"
            )
            if target_faction_id is None:
                return None

            value = self._input_int(
                prompt="Новый ранг от 0 до 6: ",
                min_value=0,
                max_value=6,
            )

            return ClockEffect(
                effect_type=effect_type,
                target_faction_id=target_faction_id,
                value=value,
            )

        if effect_type == ClockEffectType.SET_FACTION_HOLD:
            target_faction_id = self._select_required_faction_id(
                "Выбери фракцию, чей контроль изменить:"
            )
            if target_faction_id is None:
                return None

            hold = self._select_hold()

            return ClockEffect(
                effect_type=effect_type,
                target_faction_id=target_faction_id,
                value=hold.value,
            )

        if effect_type == ClockEffectType.SET_FACTION_STATUS:
            target_faction_id = self._select_required_faction_id(
                "Выбери фракцию, чей статус изменить:"
            )
            if target_faction_id is None:
                return None

            status = self._select_faction_status()

            return ClockEffect(
                effect_type=effect_type,
                target_faction_id=target_faction_id,
                value=status.value,
            )

        if effect_type == ClockEffectType.CHANGE_RELATION:
            target_faction_id = self._select_required_faction_id(
                "Выбери первую фракцию:"
            )
            if target_faction_id is None:
                return None

            secondary_faction_id = self._select_required_faction_id(
                "Выбери вторую фракцию:"
            )
            if secondary_faction_id is None:
                return None

            amount = self._input_int(
                prompt="На сколько изменить отношения, от -3 до 3: ",
                min_value=-3,
                max_value=3,
            )

            return ClockEffect(
                effect_type=effect_type,
                target_faction_id=target_faction_id,
                secondary_faction_id=secondary_faction_id,
                amount=amount,
            )

        if effect_type == ClockEffectType.TRANSFER_STREET_CONTROL:
            target_faction_id = self._select_required_faction_id(
                "Выбери нового владельца улицы:"
            )
            if target_faction_id is None:
                return None

            street_id = self._select_optional_street_id()
            if street_id is None:
                print("Для передачи контроля нужно выбрать улицу.")
                return None

            return ClockEffect(
                effect_type=effect_type,
                target_faction_id=target_faction_id,
                street_id=street_id,
            )

        if effect_type == ClockEffectType.ADVANCE_CLOCK:
            target_clock_id = self._select_any_clock_id()
            if target_clock_id is None:
                return None

            amount = self._input_int(
                prompt="На сколько продвинуть связанный счетчик: ",
                min_value=1,
                max_value=20,
            )

            return ClockEffect(
                effect_type=effect_type,
                target_clock_id=target_clock_id,
                amount=amount,
            )

        if effect_type == ClockEffectType.CHANGE_CREW_HEAT:
            amount = self._input_int(
                prompt="На сколько изменить подозрения команды, например -1 или 2: ",
                min_value=-20,
                max_value=20,
            )

            return ClockEffect(
                effect_type=effect_type,
                amount=amount,
            )

        if effect_type == ClockEffectType.CHANGE_CREW_WANTED_LEVEL:
            amount = self._input_int(
                prompt="На сколько изменить уровень розыска команды, например -1 или 1: ",
                min_value=-6,
                max_value=6,
            )

            return ClockEffect(
                effect_type=effect_type,
                amount=amount,
            )

        return None

    def _select_required_faction_id(self, title: str) -> str | None:
        faction_id = self._select_optional_faction_id(title)

        if faction_id is None:
            print("Фракция не выбрана.")
            return None

        return faction_id

    def _select_hold(self) -> Hold:
        print()
        print("Выбери контроль:")
        print("1. weak")
        print("2. strong")

        choice = self._input_int(
            prompt="> ",
            min_value=1,
            max_value=2,
        )

        if choice == 1:
            return Hold.WEAK

        return Hold.STRONG

    def _select_faction_status(self) -> FactionStatus:
        options = list(FactionStatus)

        print()
        print("Выбери статус фракции:")

        for index, item in enumerate(options, start=1):
            print(f"{index}. {item.value}")

        choice = self._input_int(
            prompt="> ",
            min_value=1,
            max_value=len(options),
        )

        return options[choice - 1]

    def _select_any_clock_id(self) -> str | None:
        clocks = list(self.campaign.city.clocks.values())

        if not clocks:
            print("В кампании нет счетчиков.")
            return None

        print()
        print("Выбери счетчик:")

        for index, clock in enumerate(clocks, start=1):
            owner_name = "Город"

            if clock.owner_faction_id is not None:
                owner = self.campaign.city.factions.get(clock.owner_faction_id)

                if owner is not None:
                    owner_name = owner.name

            print(
                f"{index}. {clock.name} "
                f"{clock.current_segments}/{clock.max_segments} "
                f"({clock.status.value}) - {owner_name}"
            )

        print("0. Назад")

        choice = self._input_int(
            prompt="> ",
            min_value=0,
            max_value=len(clocks),
        )

        if choice == 0:
            return None

        return clocks[choice - 1].id
    def create_clock_menu(self) -> None:
        print()
        print("=== СОЗДАНИЕ СЧЕТЧИКА ===")

        owner = self._select_faction()

        if owner is None:
            return

        name = input("Название счетчика: ").strip()

        if not name:
            print("Название не может быть пустым.")
            return

        clock_type = self._select_clock_type()
        advance_mode = self._select_clock_advance_mode()
        action_category = self._select_clock_action_category()

        max_segments = self._input_int(
            prompt="Размер счетчика, обычно 4, 6 или 8: ",
            min_value=1,
            max_value=20,
        )

        current_segments = self._input_int(
            prompt="Текущий прогресс, обычно 0: ",
            min_value=0,
            max_value=max_segments,
        )

        priority = self._input_int(
            prompt="Приоритет от 1 до 5: ",
            min_value=1,
            max_value=5,
        )

        progress_per_week = self._input_int(
            prompt="Прогресс за неделю, обычно 1: ",
            min_value=1,
            max_value=10,
        )

        target_faction_id = self._select_optional_faction_id(
            title="Выбери цель счетчика, можно пропустить:"
        )

        district_id = self._select_optional_district_id()
        street_id = self._select_optional_street_id()

        trigger_on_complete = input(
            "Что произойдет при завершении, текстом, можно оставить пустым: "
        ).strip()

        notes = input("Заметки, можно оставить пустым: ").strip()
        reason = self._input_reason()

        auto_advance = advance_mode not in [
            ClockAdvanceMode.MANUAL_ONLY,
            ClockAdvanceMode.REACTION,
        ]

        clock, event = self.gm_action_service.create_faction_clock(
            campaign=self.campaign,
            name=name,
            clock_type=clock_type,
            max_segments=max_segments,
            owner_faction_id=owner.id,
            current_segments=current_segments,
            target_faction_id=target_faction_id,
            district_id=district_id,
            street_id=street_id,
            advance_mode=advance_mode,
            action_category=action_category,
            priority=priority,
            progress_per_week=progress_per_week,
            auto_advance=auto_advance,
            trigger_on_complete=trigger_on_complete,
            notes=notes,
            reason=reason,
        )

        print()
        print(f"Счетчик создан: {clock.name}")
        print(f"ID: {clock.id}")
        print(f"Событие: {event.title}")

    def _select_clock_type(self) -> ClockType:
        options = list(ClockType)

        print()
        print("Выбери тип счетчика:")

        for index, item in enumerate(options, start=1):
            print(f"{index}. {item.value}")

        choice = self._input_int(
            prompt="> ",
            min_value=1,
            max_value=len(options),
        )

        return options[choice - 1]

    def _select_clock_advance_mode(self) -> ClockAdvanceMode:
        options = list(ClockAdvanceMode)

        print()
        print("Выбери режим продвижения:")
        print("auto_weekly - двигается каждую неделю")
        print("gm_confirm_weekly - каждую неделю спрашивает мастера")
        print("manual_only - двигается только вручную")
        print("conditional_weekly - двигается по условию")
        print("reaction - двигается только как реакция")
        print()

        for index, item in enumerate(options, start=1):
            print(f"{index}. {item.value}")

        choice = self._input_int(
            prompt="> ",
            min_value=1,
            max_value=len(options),
        )

        return options[choice - 1]

    def _select_clock_action_category(self) -> ClockActionCategory:
        options = list(ClockActionCategory)

        print()
        print("Выбери категорию счетчика:")
        print("attack - атака")
        print("defense - защита")
        print("investigation - расследование")
        print("project - обычный проект")
        print("recovery - восстановление")
        print("influence - влияние")
        print()

        for index, item in enumerate(options, start=1):
            print(f"{index}. {item.value}")

        choice = self._input_int(
            prompt="> ",
            min_value=1,
            max_value=len(options),
        )

        return options[choice - 1]

    def _select_optional_faction_id(self, title: str) -> str | None:
        factions = list(self.campaign.city.factions.values())

        print()
        print(title)

        for index, faction in enumerate(factions, start=1):
            print(f"{index}. {faction.name} ({faction.id})")

        print("0. Пропустить")
        print()

        choice = self._input_int(
            prompt="> ",
            min_value=0,
            max_value=len(factions),
        )

        if choice == 0:
            return None

        return factions[choice - 1].id

    def _select_optional_district_id(self) -> str | None:
        districts = list(self.campaign.city.districts.values())

        if not districts:
            return None

        print()
        print("Выбери район, можно пропустить:")

        for index, district in enumerate(districts, start=1):
            print(f"{index}. {district.name} ({district.id})")

        print("0. Пропустить")
        print()

        choice = self._input_int(
            prompt="> ",
            min_value=0,
            max_value=len(districts),
        )

        if choice == 0:
            return None

        return districts[choice - 1].id

    def _select_optional_street_id(self) -> str | None:
        streets = list(self.campaign.city.streets.values())

        if not streets:
            return None

        print()
        print("Выбери улицу, можно пропустить:")

        for index, street in enumerate(streets, start=1):
            print(f"{index}. {street.name} ({street.id})")

        print("0. Пропустить")
        print()

        choice = self._input_int(
            prompt="> ",
            min_value=0,
            max_value=len(streets),
        )

        if choice == 0:
            return None

        return streets[choice - 1].id
    def run_week(self) -> None:
        events = self.weekly_turn_service.run_week(self.campaign)

        print()
        print(f"Неделя {self.campaign.current_week} завершена.")
        print("События недели:")

        for event in events:
            print(f"- {event.title}")

            if event.description:
                print(f"  {event.description}")

    def show_events(self) -> None:
        print()
        print("=== ЖУРНАЛ СОБЫТИЙ ===")

        events = sorted(
            self.campaign.city.events.values(),
            key=lambda event: event.week,
        )

        if not events:
            print("Событий пока нет.")
            return

        for event in events:
            print()
            print(f"Неделя {event.week}: {event.title}")

            if event.description:
                print(f"  {event.description}")

            if event.consequences:
                consequences = [
                    consequence
                    for consequence in event.consequences
                    if consequence
                ]

                if consequences:
                    print(f"  Последствия: {', '.join(consequences)}")

    def save_campaign(self) -> None:
        self.storage.save_campaign(self.campaign, self.save_path)
        print(f"Кампания сохранена в {self.save_path}")

    def exit_menu(self) -> None:
        print()
        print("Сохранить кампанию перед выходом?")
        print("1. Да")
        print("2. Нет")

        choice = input("> ").strip()

        if choice == "1":
            self.save_campaign()

        print("Выход.")

    def _select_faction(self) -> Faction | None:
        factions = list(self.campaign.city.factions.values())

        print()
        print("Выбери фракцию:")

        for index, faction in enumerate(factions, start=1):
            print(f"{index}. {faction.name} ({faction.id})")

        print("0. Назад")
        print()

        choice = self._input_int(
            prompt="> ",
            min_value=0,
            max_value=len(factions),
        )

        if choice == 0:
            return None

        return factions[choice - 1]

    def _select_faction_clock(self, faction: Faction) -> str | None:
        if not faction.clock_ids:
            print("У фракции нет счетчиков.")
            return None

        clocks = []

        for clock_id in faction.clock_ids:
            clock = self.campaign.city.clocks.get(clock_id)

            if clock is None:
                continue

            clocks.append(clock)

        if not clocks:
            print("У фракции нет доступных счетчиков.")
            return None

        print()
        print("Выбери счетчик:")

        for index, clock in enumerate(clocks, start=1):
            print(
                f"{index}. {clock.name} "
                f"{clock.current_segments}/{clock.max_segments} "
                f"({clock.status.value})"
            )

        print("0. Назад")

        choice = self._input_int(
            prompt="> ",
            min_value=0,
            max_value=len(clocks),
        )

        if choice == 0:
            return None

        return clocks[choice - 1].id

    def _get_relation_with_crew(self, faction: Faction) -> int:
        if faction.id == self.campaign.player_crew_id:
            return 0

        return self.gm_action_service.get_relation_value(
            campaign=self.campaign,
            faction_a_id=self.campaign.player_crew_id,
            faction_b_id=faction.id,
        )

    def _input_int(
        self,
        prompt: str,
        min_value: int,
        max_value: int,
    ) -> int:
        while True:
            raw_value = input(prompt).strip()

            try:
                value = int(raw_value)
            except ValueError:
                print("Нужно ввести число.")
                continue

            if value < min_value or value > max_value:
                print(f"Введите число от {min_value} до {max_value}.")
                continue

            return value

    def _input_reason(self) -> str:
        return input("Причина изменения, можно оставить пустым: ").strip()
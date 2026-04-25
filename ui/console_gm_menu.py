from app.domain.enums import ClockStatus, FactionStatus, Hold
from app.domain.models import Campaign, Faction, NpcFaction
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
        self.weekly_turn_service = WeeklyTurnService()
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

                    print(
                        f"    - {clock.name}: "
                        f"{clock.current_segments}/{clock.max_segments} "
                        f"({clock.status.value})"
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

                print(
                    f"- {clock.id}: {clock.name} "
                    f"{clock.current_segments}/{clock.max_segments} "
                    f"({clock.status.value})"
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
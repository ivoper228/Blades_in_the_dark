from data.initial_campaign import build_initial_campaign
from services.weekly_turn_service import WeeklyTurnService
from storage.json_storage import JsonStorage


def main() -> None:
    campaign = build_initial_campaign()

    weekly_turn_service = WeeklyTurnService()
    events = weekly_turn_service.run_week(campaign)

    print(f"Кампания: {campaign.name}")
    print(f"Текущая неделя: {campaign.current_week}")
    print()

    print("События недели:")
    for event in events:
        print(f"- {event.title}")

        if event.description:
            print(f"  {event.description}")

    storage = JsonStorage()
    storage.save_campaign(campaign, "saves/campaign_week_1.json")

    print()
    print("Состояние кампании сохранено в saves/campaign_week_1.json")


if __name__ == "__main__":
    main()
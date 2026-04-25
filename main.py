from data.initial_campaign import build_initial_campaign
from ui.console_gm_menu import ConsoleGMMenu


def main() -> None:
    campaign = build_initial_campaign()

    menu = ConsoleGMMenu(campaign)
    menu.run()


if __name__ == "__main__":
    main()
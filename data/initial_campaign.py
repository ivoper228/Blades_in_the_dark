from app.domain.enums import (
    ClockActionCategory,
    ClockAdvanceMode,
    ClockEffectType,
    ClockType,
    FocusLevel,
    Hold,
)
from app.domain.models import (
    Campaign,
    City,
    Clock,
    ClockEffect,
    District,
    NpcFaction,
    PlayerCrew,
    Relation,
    Street,
)

def build_initial_campaign() -> Campaign:
    city = City(
        id="doskvol",
        name="Дасквол",
    )

    crows_foot = District(
        id="crows_foot",
        name="Вороний перекресток",
        description="Район банд, притонов, старых домов и борьбы за улицы.",
        danger_level=3,
    )

    city.districts[crows_foot.id] = crows_foot

    black_lamp_alley = Street(
        id="black_lamp_alley",
        name="Переулок Черной Лампы",
        district_id=crows_foot.id,
        controlling_faction_id="lampblacks",
        present_faction_ids=["lampblacks", "red_sashes", "bluecoats"],
        tags=["narrow", "gang_border", "drug_trade"],
        atmosphere=["fog", "oil_puddles", "dim_lamps"],
        landmarks=["old_bridge", "closed_tavern", "warehouse_door"],
        notes="Спорная улица между Гасильщиками и Красными Кушаками.",
    )

    silk_lane = Street(
        id="silk_lane",
        name="Шелковый проход",
        district_id=crows_foot.id,
        controlling_faction_id="red_sashes",
        present_faction_ids=["red_sashes", "lampblacks"],
        tags=["market", "irovian", "tense"],
        atmosphere=["incense", "wet_stone", "watchful_windows"],
        landmarks=["fencing_school", "tea_house"],
        notes="Место, где Красные Кушаки держат влияние через учеников и торговцев.",
    )

    city.streets[black_lamp_alley.id] = black_lamp_alley
    city.streets[silk_lane.id] = silk_lane

    crows_foot.street_ids = [
        black_lamp_alley.id,
        silk_lane.id,
    ]

    player_crew = PlayerCrew(
        id="player_crew",
        name="Команда игроков",
        faction_type="crew",
        tier=0,
        hold=Hold.STRONG,
        district_ids=[crows_foot.id],
        street_ids=[],
        crew_type="unknown",
        reputation=0,
        heat=0,
        wanted_level=0,
        coin=0,
        notes="Команда игроков. Ее действия вводятся вручную по итогам сессий.",
        focus_level=FocusLevel.SPOTLIGHT
    )

    lampblacks = NpcFaction(
        id="lampblacks",
        name="Гасильщики",
        faction_type="gang",
        tier=2,
        hold=Hold.WEAK,
        district_ids=[crows_foot.id],
        street_ids=[black_lamp_alley.id],
        focus_level=FocusLevel.SPOTLIGHT,
        leader="Баззо Баз",
        public_goal="Удержать улицы Вороньего перекрестка.",
        hidden_goal="Сломать Красных Кушаков до того, как вмешаются другие силы.",
        preferred_actions=["attack_enemy", "protect_asset", "expand_territory"],
        enemies=["red_sashes"],
        allies=[],
        resources=["street_toughs", "old_contacts", "fear"],
        vulnerabilities=["weak_control", "many_enemies"],
    )

    red_sashes = NpcFaction(
        id="red_sashes",
        name="Красные Кушаки",
        faction_type="gang",
        tier=2,
        hold=Hold.STRONG,
        district_ids=[crows_foot.id],
        street_ids=[silk_lane.id],
        focus_level=FocusLevel.SPOTLIGHT,
        leader="Майлера Клев",
        public_goal="Вернуть контроль над рынком и улицами.",
        hidden_goal="Переманить торговцев и изолировать Гасильщиков.",
        preferred_actions=["expand_territory", "buy_influence", "attack_enemy"],
        enemies=["lampblacks"],
        allies=[],
        resources=["sword_students", "irovian_contacts", "discipline"],
        vulnerabilities=["pride", "limited_numbers"],
    )

    bluecoats = NpcFaction(
        id="bluecoats",
        name="Синие Мундиры",
        faction_type="law",
        tier=3,
        hold=Hold.STRONG,
        district_ids=[crows_foot.id],
        street_ids=[black_lamp_alley.id, silk_lane.id],
        focus_level=FocusLevel.ACTIVE,
        leader="Капитан районного участка",
        public_goal="Сохранять видимость порядка.",
        hidden_goal="Собрать компромат и выжать деньги со всех сторон.",
        preferred_actions=["investigate", "extort", "protect_asset"],
        enemies=[],
        allies=[],
        resources=["patrols", "cells", "paperwork"],
        vulnerabilities=["corruption", "public_pressure"],
    )

    city.factions[player_crew.id] = player_crew
    city.factions[lampblacks.id] = lampblacks
    city.factions[red_sashes.id] = red_sashes
    city.factions[bluecoats.id] = bluecoats

    crows_foot.faction_ids = [
        player_crew.id,
        lampblacks.id,
        red_sashes.id,
        bluecoats.id,
    ]

    clock_red_sashes_market = Clock(
        id="clock_red_sashes_market",
        name="Красные Кушаки возвращают рынок искры",
        clock_type=ClockType.PROJECT,
        max_segments=6,
        current_segments=2,
        owner_faction_id=red_sashes.id,
        target_faction_id=lampblacks.id,
        district_id=crows_foot.id,
        
        street_id=black_lamp_alley.id,
        advance_mode=ClockAdvanceMode.AUTO_WEEKLY,
        action_category=ClockActionCategory.ATTACK,
        priority=5,
        progress_per_week=1,
        trigger_on_complete=(
            "Красные Кушаки получают сильную позицию на спорной улице. "
            "Ведущий решает, теряют ли Гасильщики актив или контроль."

        ),
        completion_effects=[
            ClockEffect(
                effect_type=ClockEffectType.TRANSFER_STREET_CONTROL,
                target_faction_id=red_sashes.id,
                street_id=black_lamp_alley.id,
                description="Красные Кушаки забирают спорную улицу.",
            ),
            ClockEffect(
                effect_type=ClockEffectType.SET_FACTION_HOLD,
                target_faction_id=lampblacks.id,
                value="weak",
                description="Позиции Гасильщиков проседают.",
            ),
        ],

    )

    clock_lampblacks_counterattack = Clock(
        id="clock_lampblacks_counterattack",
        name="Гасильщики готовят ответный удар",
        clock_type=ClockType.CONFLICT,
        max_segments=6,
        current_segments=1,
        owner_faction_id=lampblacks.id,
        target_faction_id=red_sashes.id,
        district_id=crows_foot.id,
        street_id=silk_lane.id,
         
        advance_mode=ClockAdvanceMode.AUTO_WEEKLY,
        action_category=ClockActionCategory.ATTACK,
        priority=5,
        progress_per_week=1,
        trigger_on_complete=(
            "Гасильщики совершают открытое нападение. "
            "Ведущий выбирает цель удара."
        ),
        completion_effects=[
            ClockEffect(
                effect_type=ClockEffectType.SET_FACTION_HOLD,
                target_faction_id=red_sashes.id,
                value="weak",
                description="Удар Гасильщиков ослабляет контроль Красных Кушаков.",
            ),
            ClockEffect(
                effect_type=ClockEffectType.CHANGE_RELATION,
                target_faction_id=lampblacks.id,
                secondary_faction_id=red_sashes.id,
                amount=-1,
                description="Конфликт становится еще жестче.",
            ),
        ],
    )

    clock_bluecoats_investigation = Clock(
        id="clock_bluecoats_investigation",
        name="Синие Мундиры собирают дело против команды",
        clock_type=ClockType.INVESTIGATION,
        max_segments=8,
        current_segments=0,
        owner_faction_id=bluecoats.id,
        target_faction_id=player_crew.id,
        district_id=crows_foot.id,

        advance_mode=ClockAdvanceMode.AUTO_WEEKLY,
        action_category=ClockActionCategory.INVESTIGATION,
        priority=4,
        progress_per_week=1,
        trigger_on_complete=(
            "Синие Мундиры готовы к арестам, облаве или шантажу команды."
        ),
        completion_effects=[
            ClockEffect(
                effect_type=ClockEffectType.CHANGE_CREW_HEAT,
                amount=2,
                description="Расследование повышает давление на команду.",
            ),
            ClockEffect(
                effect_type=ClockEffectType.CHANGE_RELATION,
                target_faction_id=player_crew.id,
                secondary_faction_id=bluecoats.id,
                amount=-1,
                description="Синие Мундиры становятся опаснее для команды.",
            ),
        ],
    )

    city.clocks[clock_red_sashes_market.id] = clock_red_sashes_market
    city.clocks[clock_lampblacks_counterattack.id] = clock_lampblacks_counterattack
    city.clocks[clock_bluecoats_investigation.id] = clock_bluecoats_investigation

    red_sashes.clock_ids = [clock_red_sashes_market.id]
    lampblacks.clock_ids = [clock_lampblacks_counterattack.id]
    bluecoats.clock_ids = [clock_bluecoats_investigation.id]

    relations = [
        Relation(
            id="rel_player_lampblacks",
            faction_a_id=player_crew.id,
            faction_b_id=lampblacks.id,
            value=0,
            reason="Пока нейтральные отношения.",
        ),
        Relation(
            id="rel_player_red_sashes",
            faction_a_id=player_crew.id,
            faction_b_id=red_sashes.id,
            value=0,
            reason="Пока нейтральные отношения.",
        ),
        Relation(
            id="rel_player_bluecoats",
            faction_a_id=player_crew.id,
            faction_b_id=bluecoats.id,
            value=0,
            reason="Синие Мундиры пока просто наблюдают.",
        ),
        Relation(
            id="rel_lampblacks_red_sashes",
            faction_a_id=lampblacks.id,
            faction_b_id=red_sashes.id,
            value=-3,
            reason="Открытая борьба за Вороний перекресток.",
            is_public=True,
        ),
    ]

    for relation in relations:
        city.relations[relation.id] = relation

    return Campaign(
        id="main_campaign",
        name="Кампания в Даскволе",
        current_week=0,
        city=city,
        player_crew_id=player_crew.id,
        settings={
            "dice_enabled": False,
            "player_mode_enabled": False,
        },
    )
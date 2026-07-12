"""스킬 시스템: 장착형 기본 스킬(W/A/S/D) + 조합 스킬 + 궁극기.

name/desc/usage/level_desc는 다국어 필드(_en/_ja/_zh/_ru)를 갖고,
LocalizedDict가 조회 시 현재 언어로 자동 해석한다 (core.lang 참고).
"""
from core.lang import localize_defs

SKILL_MAX_LEVEL = 3

# ── 장착 가능한 모든 스킬 정의 ──────────────────────────────────────────
ALL_SKILL_DEFS = {
    # ── 기본 장착 스킬 (Default) ──────────────────────────────────────
    'flash_dash': {
        'name': '섬광 돌진', 'name_en': 'Flash Dash', 'name_ja': '閃光ダッシュ',
        'name_zh': '闪光冲刺', 'name_ru': 'Рывок-вспышка',
        'slot_default': 'W',
        'level_req': 5,
        'cooldown_ms': 3000,
        'color': (100, 180, 255),
        'category': 'mobility',
        'desc': '전방으로 고속 돌진, 경로의 적을 경직',
        'desc_en': 'Dash forward at high speed, staggering enemies in the path',
        'desc_ja': '前方へ高速ダッシュ、経路の敵を硬直させる',
        'desc_zh': '向前高速冲刺，僵直路径上的敌人',
        'desc_ru': 'Стремительный рывок вперёд, оглушает врагов на пути',
        'usage': '이동 방향으로 N칸 돌진 · 경로 적 경직',
        'usage_en': 'Dash N tiles in facing direction · staggers enemies in path',
        'usage_ja': '向いている方向へNマス突進 · 経路の敵を硬直',
        'usage_zh': '朝移动方向冲刺N格 · 僵直路径敌人',
        'usage_ru': 'Рывок на N клеток · оглушение врагов на пути',
        'upgrades': [
            {'tiles': 3, 'stagger_ms': 1000, 'cd_ms': 3000,
             'level_desc': '3칸 돌진 · 경직 1.0초 · 쿨 3.0초',
             'level_desc_en': '3-tile dash · 1.0s stagger · 3.0s CD',
             'level_desc_ja': '3マス突進 · 硬直1.0秒 · CD3.0秒',
             'level_desc_zh': '冲刺3格 · 僵直1.0秒 · 冷却3.0秒',
             'level_desc_ru': 'Рывок 3 кл. · оглуш. 1,0с · КД 3,0с'},
            {'tiles': 4, 'stagger_ms': 1200, 'cd_ms': 2500,
             'level_desc': '4칸 돌진 · 경직 1.2초 · 쿨 2.5초',
             'level_desc_en': '4-tile dash · 1.2s stagger · 2.5s CD',
             'level_desc_ja': '4マス突進 · 硬直1.2秒 · CD2.5秒',
             'level_desc_zh': '冲刺4格 · 僵直1.2秒 · 冷却2.5秒',
             'level_desc_ru': 'Рывок 4 кл. · оглуш. 1,2с · КД 2,5с'},
            {'tiles': 5, 'stagger_ms': 1500, 'cd_ms': 2000,
             'level_desc': '5칸 돌진 · 경직 1.5초 · 쿨 2.0초',
             'level_desc_en': '5-tile dash · 1.5s stagger · 2.0s CD',
             'level_desc_ja': '5マス突進 · 硬直1.5秒 · CD2.0秒',
             'level_desc_zh': '冲刺5格 · 僵直1.5秒 · 冷却2.0秒',
             'level_desc_ru': 'Рывок 5 кл. · оглуш. 1,5с · КД 2,0с'},
        ],
        'sp_cost': [5, 10],
    },
    'steel_whirl': {
        'name': '강철 회오리', 'name_en': 'Steel Whirl', 'name_ja': '鋼鉄の旋風',
        'name_zh': '钢铁旋风', 'name_ru': 'Стальной вихрь',
        'slot_default': 'A',
        'level_req': 10,
        'cooldown_ms': 5000,
        'color': (255, 180, 60),
        'category': 'attack',
        'desc': '주변 8방향 적을 모두 휩쓸어 피해',
        'desc_en': 'Sweep all enemies in 8 directions around you',
        'desc_ja': '周囲8方向の敵をすべて薙ぎ払う',
        'desc_zh': '横扫周围8个方向的所有敌人',
        'desc_ru': 'Сметает всех врагов в 8 направлениях',
        'usage': '플레이어 중심 반경 N칸 광역 공격',
        'usage_en': 'AoE attack, radius N around the player',
        'usage_ja': 'プレイヤー中心の半径Nマス範囲攻撃',
        'usage_zh': '以玩家为中心半径N格范围攻击',
        'usage_ru': 'Атака по области радиусом N вокруг игрока',
        'upgrades': [
            {'radius': 1, 'mul': 1.0, 'cd_ms': 5000,
             'level_desc': '반경 1칸 · 100% 피해 · 쿨 5.0초',
             'level_desc_en': 'Radius 1 · 100% DMG · 5.0s CD',
             'level_desc_ja': '半径1 · 100%ダメージ · CD5.0秒',
             'level_desc_zh': '半径1 · 100%伤害 · 冷却5.0秒',
             'level_desc_ru': 'Радиус 1 · 100% урона · КД 5,0с'},
            {'radius': 2, 'mul': 1.0, 'cd_ms': 5000,
             'level_desc': '반경 2칸 · 100% 피해 · 쿨 5.0초',
             'level_desc_en': 'Radius 2 · 100% DMG · 5.0s CD',
             'level_desc_ja': '半径2 · 100%ダメージ · CD5.0秒',
             'level_desc_zh': '半径2 · 100%伤害 · 冷却5.0秒',
             'level_desc_ru': 'Радиус 2 · 100% урона · КД 5,0с'},
            {'radius': 2, 'mul': 1.2, 'cd_ms': 4000,
             'level_desc': '반경 2칸 · 120% 피해 · 쿨 4.0초',
             'level_desc_en': 'Radius 2 · 120% DMG · 4.0s CD',
             'level_desc_ja': '半径2 · 120%ダメージ · CD4.0秒',
             'level_desc_zh': '半径2 · 120%伤害 · 冷却4.0秒',
             'level_desc_ru': 'Радиус 2 · 120% урона · КД 4,0с'},
        ],
        'sp_cost': [5, 10],
    },
    'regen_breath': {
        'name': '재생의 숨결', 'name_en': 'Regen Breath', 'name_ja': '再生の息吹',
        'name_zh': '再生之息', 'name_ru': 'Дыхание жизни',
        'slot_default': 'S',
        'level_req': 6,
        'cooldown_ms': 10000,
        'color': (80, 220, 130),
        'category': 'defense',
        'desc': 'HP를 회복하고 일시적으로 방어력 증가',
        'desc_en': 'Restore HP and temporarily boost defense',
        'desc_ja': 'HPを回復し、一時的に防御力を上げる',
        'desc_zh': '恢复HP并暂时提升防御',
        'desc_ru': 'Восстанавливает HP и временно повышает защиту',
        'usage': '즉시 HP 회복 + 방어 버프',
        'usage_en': 'Instant HP recovery + defense buff',
        'usage_ja': '即時HP回復 + 防御バフ',
        'usage_zh': '立即恢复HP + 防御增益',
        'usage_ru': 'Мгновенное лечение + бафф защиты',
        'upgrades': [
            {'heal_pct': 0.25, 'def_bonus': 3, 'def_ms': 3000, 'cd_ms': 10000,
             'level_desc': 'HP 25% 회복 · 방어+3 (3초) · 쿨 10초',
             'level_desc_en': 'Heal 25% HP · DEF+3 (3s) · 10s CD',
             'level_desc_ja': 'HP25%回復 · 防御+3 (3秒) · CD10秒',
             'level_desc_zh': '恢复25%HP · 防御+3 (3秒) · 冷却10秒',
             'level_desc_ru': '25% HP · ЗАЩ+3 (3с) · КД 10с'},
            {'heal_pct': 0.35, 'def_bonus': 5, 'def_ms': 3000, 'cd_ms': 9000,
             'level_desc': 'HP 35% 회복 · 방어+5 (3초) · 쿨 9초',
             'level_desc_en': 'Heal 35% HP · DEF+5 (3s) · 9s CD',
             'level_desc_ja': 'HP35%回復 · 防御+5 (3秒) · CD9秒',
             'level_desc_zh': '恢复35%HP · 防御+5 (3秒) · 冷却9秒',
             'level_desc_ru': '35% HP · ЗАЩ+5 (3с) · КД 9с'},
            {'heal_pct': 0.50, 'def_bonus': 8, 'def_ms': 5000, 'cd_ms': 7000,
             'level_desc': 'HP 50% 회복 · 방어+8 (5초) · 쿨 7초',
             'level_desc_en': 'Heal 50% HP · DEF+8 (5s) · 7s CD',
             'level_desc_ja': 'HP50%回復 · 防御+8 (5秒) · CD7秒',
             'level_desc_zh': '恢复50%HP · 防御+8 (5秒) · 冷却7秒',
             'level_desc_ru': '50% HP · ЗАЩ+8 (5с) · КД 7с'},
        ],
        'sp_cost': [5, 10],
    },
    'judgment': {
        'name': '심판의 일격', 'name_en': 'Judgment Strike', 'name_ja': '審判の一撃',
        'name_zh': '审判一击', 'name_ru': 'Удар правосудия',
        'slot_default': 'D',
        'level_req': 1,
        'cooldown_ms': 4000,
        'color': (255, 100, 80),
        'category': 'attack',
        'desc': '전방 적에게 강력한 일격, 높은 치명타 확률',
        'desc_en': 'Powerful strike on the enemy ahead with high crit chance',
        'desc_ja': '前方の敵へ強力な一撃、高い会心率',
        'desc_zh': '对前方敌人发动强力一击，高暴击率',
        'desc_ru': 'Мощный удар по врагу впереди с высоким шансом крита',
        'usage': '전방 단일 강타 · 치명타 시 1.5배 추가 피해',
        'usage_en': 'Single target strike · crits deal 1.5x bonus damage',
        'usage_ja': '前方単体強打 · 会心時1.5倍の追加ダメージ',
        'usage_zh': '前方单体重击 · 暴击时1.5倍额外伤害',
        'usage_ru': 'Удар по одной цели · крит даёт x1,5 урона',
        'upgrades': [
            {'mul': 2.0, 'crit': 0.25, 'cd_ms': 4000,
             'level_desc': '200% 피해 · 치명 25% · 쿨 4.0초',
             'level_desc_en': '200% DMG · 25% crit · 4.0s CD',
             'level_desc_ja': '200%ダメージ · 会心25% · CD4.0秒',
             'level_desc_zh': '200%伤害 · 暴击25% · 冷却4.0秒',
             'level_desc_ru': '200% урона · крит 25% · КД 4,0с'},
            {'mul': 2.5, 'crit': 0.30, 'cd_ms': 3500,
             'level_desc': '250% 피해 · 치명 30% · 쿨 3.5초',
             'level_desc_en': '250% DMG · 30% crit · 3.5s CD',
             'level_desc_ja': '250%ダメージ · 会心30% · CD3.5秒',
             'level_desc_zh': '250%伤害 · 暴击30% · 冷却3.5秒',
             'level_desc_ru': '250% урона · крит 30% · КД 3,5с'},
            {'mul': 3.0, 'crit': 0.35, 'cd_ms': 3000,
             'level_desc': '300% 피해 · 치명 35% · 쿨 3.0초',
             'level_desc_en': '300% DMG · 35% crit · 3.0s CD',
             'level_desc_ja': '300%ダメージ · 会心35% · CD3.0秒',
             'level_desc_zh': '300%伤害 · 暴击35% · 冷却3.0秒',
             'level_desc_ru': '300% урона · крит 35% · КД 3,0с'},
        ],
        'sp_cost': [5, 10],
    },

    # ── 추가 장착 스킬 ──────────────────────────────────────────────────
    'shadow_step': {
        'name': '그림자 발걸음', 'name_en': 'Shadow Step', 'name_ja': '影渡り',
        'name_zh': '暗影步', 'name_ru': 'Теневой шаг',
        'slot_default': None,
        'level_req': 3,
        'cooldown_ms': 4000,
        'color': (180, 100, 255),
        'category': 'mobility',
        'desc': '전방으로 순간이동, 도착 지점의 적을 밀쳐냄',
        'desc_en': 'Teleport forward, knocking back enemies at the destination',
        'desc_ja': '前方へ瞬間移動し、着地点の敵を突き飛ばす',
        'desc_zh': '向前瞬移，击退落点的敌人',
        'desc_ru': 'Телепорт вперёд, отбрасывает врагов в точке выхода',
        'usage': '이동 방향으로 N칸 순간이동 · 도달 지점 적 경직',
        'usage_en': 'Teleport N tiles forward · staggers enemies at arrival',
        'usage_ja': '向いている方向へNマス瞬間移動 · 到達点の敵を硬直',
        'usage_zh': '朝移动方向瞬移N格 · 僵直到达点敌人',
        'usage_ru': 'Телепорт на N клеток · оглушение у точки выхода',
        'upgrades': [
            {'tiles': 3, 'cd_ms': 4000,
             'level_desc': '3칸 순간이동 · 도착 적 경직 0.5초 · 쿨 4.0초',
             'level_desc_en': '3-tile teleport · 0.5s stagger · 4.0s CD',
             'level_desc_ja': '3マス瞬間移動 · 硬直0.5秒 · CD4.0秒',
             'level_desc_zh': '瞬移3格 · 僵直0.5秒 · 冷却4.0秒',
             'level_desc_ru': 'Телепорт 3 кл. · оглуш. 0,5с · КД 4,0с'},
            {'tiles': 4, 'cd_ms': 3500,
             'level_desc': '4칸 순간이동 · 도착 적 경직 0.8초 · 쿨 3.5초',
             'level_desc_en': '4-tile teleport · 0.8s stagger · 3.5s CD',
             'level_desc_ja': '4マス瞬間移動 · 硬直0.8秒 · CD3.5秒',
             'level_desc_zh': '瞬移4格 · 僵直0.8秒 · 冷却3.5秒',
             'level_desc_ru': 'Телепорт 4 кл. · оглуш. 0,8с · КД 3,5с'},
            {'tiles': 5, 'cd_ms': 3000,
             'level_desc': '5칸 순간이동 · 도착 적 경직 1.0초 · 쿨 3.0초',
             'level_desc_en': '5-tile teleport · 1.0s stagger · 3.0s CD',
             'level_desc_ja': '5マス瞬間移動 · 硬直1.0秒 · CD3.0秒',
             'level_desc_zh': '瞬移5格 · 僵直1.0秒 · 冷却3.0秒',
             'level_desc_ru': 'Телепорт 5 кл. · оглуш. 1,0с · КД 3,0с'},
        ],
        'sp_cost': [5, 10],
    },
    'iron_shell': {
        'name': '철갑 방벽', 'name_en': 'Iron Shell', 'name_ja': '鉄甲障壁',
        'name_zh': '铁甲壁垒', 'name_ru': 'Железный панцирь',
        'slot_default': None,
        'level_req': 8,
        'cooldown_ms': 12000,
        'color': (180, 200, 230),
        'category': 'defense',
        'desc': '일시적으로 받는 피해를 대폭 감소',
        'desc_en': 'Greatly reduce incoming damage for a short time',
        'desc_ja': '一時的に被ダメージを大幅に軽減する',
        'desc_zh': '短时间内大幅减少受到的伤害',
        'desc_ru': 'Сильно снижает получаемый урон на короткое время',
        'usage': '일정 시간 동안 받는 피해 N% 감소',
        'usage_en': 'Reduce damage taken by N% for a duration',
        'usage_ja': '一定時間、被ダメージをN%軽減',
        'usage_zh': '一定时间内受到的伤害减少N%',
        'usage_ru': 'Снижение урона на N% на время действия',
        'upgrades': [
            {'reduce': 0.50, 'duration_ms': 2000, 'cd_ms': 12000,
             'level_desc': '피해 50% 감소 · 2초 · 쿨 12초',
             'level_desc_en': 'DMG -50% · 2s · 12s CD',
             'level_desc_ja': '被ダメ-50% · 2秒 · CD12秒',
             'level_desc_zh': '伤害-50% · 2秒 · 冷却12秒',
             'level_desc_ru': 'Урон -50% · 2с · КД 12с'},
            {'reduce': 0.65, 'duration_ms': 2500, 'cd_ms': 10000,
             'level_desc': '피해 65% 감소 · 2.5초 · 쿨 10초',
             'level_desc_en': 'DMG -65% · 2.5s · 10s CD',
             'level_desc_ja': '被ダメ-65% · 2.5秒 · CD10秒',
             'level_desc_zh': '伤害-65% · 2.5秒 · 冷却10秒',
             'level_desc_ru': 'Урон -65% · 2,5с · КД 10с'},
            {'reduce': 0.80, 'duration_ms': 3000, 'cd_ms': 8000,
             'level_desc': '피해 80% 감소 · 3초 · 쿨 8초',
             'level_desc_en': 'DMG -80% · 3s · 8s CD',
             'level_desc_ja': '被ダメ-80% · 3秒 · CD8秒',
             'level_desc_zh': '伤害-80% · 3秒 · 冷却8秒',
             'level_desc_ru': 'Урон -80% · 3с · КД 8с'},
        ],
        'sp_cost': [5, 10],
    },
    'flame_strike': {
        'name': '화염 강타', 'name_en': 'Flame Strike', 'name_ja': '火炎強打',
        'name_zh': '烈焰重击', 'name_ru': 'Огненный удар',
        'slot_default': None,
        'level_req': 12,
        'cooldown_ms': 6000,
        'color': (255, 140, 40),
        'category': 'attack',
        'desc': '전방 직선 범위에 강렬한 화염 피해',
        'desc_en': 'Intense fire damage in a straight line ahead',
        'desc_ja': '前方直線範囲に強烈な炎ダメージ',
        'desc_zh': '对前方直线范围造成猛烈火焰伤害',
        'desc_ru': 'Огненный урон по прямой линии впереди',
        'usage': '이동 방향으로 N칸 직선 화염 공격',
        'usage_en': 'Line attack, N tiles in facing direction',
        'usage_ja': '向いている方向へNマスの直線炎攻撃',
        'usage_zh': '朝移动方向N格直线火焰攻击',
        'usage_ru': 'Линейная атака на N клеток вперёд',
        'upgrades': [
            {'range': 3, 'mul': 1.5, 'cd_ms': 6000,
             'level_desc': '전방 3칸 · 150% 피해 · 쿨 6초',
             'level_desc_en': '3 tiles · 150% DMG · 6s CD',
             'level_desc_ja': '前方3マス · 150%ダメージ · CD6秒',
             'level_desc_zh': '前方3格 · 150%伤害 · 冷却6秒',
             'level_desc_ru': '3 клетки · 150% урона · КД 6с'},
            {'range': 4, 'mul': 1.8, 'cd_ms': 5500,
             'level_desc': '전방 4칸 · 180% 피해 · 쿨 5.5초',
             'level_desc_en': '4 tiles · 180% DMG · 5.5s CD',
             'level_desc_ja': '前方4マス · 180%ダメージ · CD5.5秒',
             'level_desc_zh': '前方4格 · 180%伤害 · 冷却5.5秒',
             'level_desc_ru': '4 клетки · 180% урона · КД 5,5с'},
            {'range': 5, 'mul': 2.2, 'cd_ms': 5000,
             'level_desc': '전방 5칸 · 220% 피해 · 쿨 5초',
             'level_desc_en': '5 tiles · 220% DMG · 5s CD',
             'level_desc_ja': '前方5マス · 220%ダメージ · CD5秒',
             'level_desc_zh': '前方5格 · 220%伤害 · 冷却5秒',
             'level_desc_ru': '5 клеток · 220% урона · КД 5с'},
        ],
        'sp_cost': [5, 10],
    },
    'life_steal': {
        'name': '생명 흡수', 'name_en': 'Life Steal', 'name_ja': '生命吸収',
        'name_zh': '生命汲取', 'name_ru': 'Похищение жизни',
        'slot_default': None,
        'level_req': 15,
        'cooldown_ms': 8000,
        'color': (220, 80, 180),
        'category': 'attack',
        'desc': '주변 적을 공격하고 피해량 일부를 HP로 흡수',
        'desc_en': 'Attack nearby enemies and absorb part of the damage as HP',
        'desc_ja': '周囲の敵を攻撃し、ダメージの一部をHPとして吸収',
        'desc_zh': '攻击周围敌人并将部分伤害转化为HP',
        'desc_ru': 'Атакует врагов рядом и поглощает часть урона как HP',
        'usage': '반경 N칸 적 공격 · 피해의 N% HP 흡수',
        'usage_en': 'Attack radius N · absorb N% of damage as HP',
        'usage_ja': '半径Nマスの敵を攻撃 · ダメージのN%をHP吸収',
        'usage_zh': '攻击半径N格敌人 · 吸收伤害N%为HP',
        'usage_ru': 'Атака в радиусе N · поглощение N% урона',
        'upgrades': [
            {'radius': 2, 'steal_pct': 0.30, 'cd_ms': 8000,
             'level_desc': '반경 2칸 · 30% 흡수 · 쿨 8초',
             'level_desc_en': 'Radius 2 · 30% steal · 8s CD',
             'level_desc_ja': '半径2 · 30%吸収 · CD8秒',
             'level_desc_zh': '半径2 · 汲取30% · 冷却8秒',
             'level_desc_ru': 'Радиус 2 · 30% похищения · КД 8с'},
            {'radius': 3, 'steal_pct': 0.40, 'cd_ms': 7000,
             'level_desc': '반경 3칸 · 40% 흡수 · 쿨 7초',
             'level_desc_en': 'Radius 3 · 40% steal · 7s CD',
             'level_desc_ja': '半径3 · 40%吸収 · CD7秒',
             'level_desc_zh': '半径3 · 汲取40% · 冷却7秒',
             'level_desc_ru': 'Радиус 3 · 40% похищения · КД 7с'},
            {'radius': 3, 'steal_pct': 0.50, 'cd_ms': 6000,
             'level_desc': '반경 3칸 · 50% 흡수 · 쿨 6초',
             'level_desc_en': 'Radius 3 · 50% steal · 6s CD',
             'level_desc_ja': '半径3 · 50%吸収 · CD6秒',
             'level_desc_zh': '半径3 · 汲取50% · 冷却6秒',
             'level_desc_ru': 'Радиус 3 · 50% похищения · КД 6с'},
        ],
        'sp_cost': [5, 10],
    },
    'war_cry': {
        'name': '전투 함성', 'name_en': 'War Cry', 'name_ja': '雄叫び',
        'name_zh': '战吼', 'name_ru': 'Боевой клич',
        'slot_default': None,
        'level_req': 18,
        'cooldown_ms': 15000,
        'color': (255, 220, 60),
        'category': 'buff',
        'desc': '잠시 동안 공격력이 크게 증가',
        'desc_en': 'Greatly increase attack power for a short time',
        'desc_ja': 'しばらくの間、攻撃力が大幅に上昇',
        'desc_zh': '短时间内大幅提升攻击力',
        'desc_ru': 'Сильно повышает атаку на короткое время',
        'usage': '일정 시간 동안 공격력 N% 증가',
        'usage_en': 'Increase ATK by N% for a duration',
        'usage_ja': '一定時間、攻撃力をN%上昇',
        'usage_zh': '一定时间内攻击力提升N%',
        'usage_ru': 'Повышение АТК на N% на время',
        'upgrades': [
            {'atk_mul': 0.30, 'duration_ms': 5000, 'cd_ms': 15000,
             'level_desc': '공격력 +30% · 5초 · 쿨 15초',
             'level_desc_en': 'ATK +30% · 5s · 15s CD',
             'level_desc_ja': '攻撃力+30% · 5秒 · CD15秒',
             'level_desc_zh': '攻击+30% · 5秒 · 冷却15秒',
             'level_desc_ru': 'АТК +30% · 5с · КД 15с'},
            {'atk_mul': 0.50, 'duration_ms': 6000, 'cd_ms': 13000,
             'level_desc': '공격력 +50% · 6초 · 쿨 13초',
             'level_desc_en': 'ATK +50% · 6s · 13s CD',
             'level_desc_ja': '攻撃力+50% · 6秒 · CD13秒',
             'level_desc_zh': '攻击+50% · 6秒 · 冷却13秒',
             'level_desc_ru': 'АТК +50% · 6с · КД 13с'},
            {'atk_mul': 0.70, 'duration_ms': 8000, 'cd_ms': 11000,
             'level_desc': '공격력 +70% · 8초 · 쿨 11초',
             'level_desc_en': 'ATK +70% · 8s · 11s CD',
             'level_desc_ja': '攻撃力+70% · 8秒 · CD11秒',
             'level_desc_zh': '攻击+70% · 8秒 · 冷却11秒',
             'level_desc_ru': 'АТК +70% · 8с · КД 11с'},
        ],
        'sp_cost': [5, 10],
    },
    'dark_pulse': {
        'name': '암흑 파동', 'name_en': 'Dark Pulse', 'name_ja': '暗黒波動',
        'name_zh': '黑暗波动', 'name_ru': 'Тёмная волна',
        'slot_default': None,
        'level_req': 20,
        'cooldown_ms': 10000,
        'color': (140, 80, 220),
        'category': 'attack',
        'desc': '주변 적을 밀쳐내고 피해를 입힘',
        'desc_en': 'Damage nearby enemies and push them away',
        'desc_ja': '周囲の敵を突き飛ばしダメージを与える',
        'desc_zh': '击退周围敌人并造成伤害',
        'desc_ru': 'Урон по врагам рядом с отбрасыванием',
        'usage': '반경 N칸 광역 피해 + 적을 N칸 밀쳐냄',
        'usage_en': 'AoE damage radius N + knockback N tiles',
        'usage_ja': '半径Nマスの範囲ダメージ + Nマスノックバック',
        'usage_zh': '半径N格范围伤害 + 击退N格',
        'usage_ru': 'Урон в радиусе N + отброс на N клеток',
        'upgrades': [
            {'radius': 2, 'mul': 0.8, 'push': 1, 'cd_ms': 10000,
             'level_desc': '반경 2칸 · 80% 피해 · 1칸 밀치기 · 쿨 10초',
             'level_desc_en': 'Radius 2 · 80% DMG · push 1 · 10s CD',
             'level_desc_ja': '半径2 · 80%ダメージ · 1マス押し · CD10秒',
             'level_desc_zh': '半径2 · 80%伤害 · 击退1格 · 冷却10秒',
             'level_desc_ru': 'Радиус 2 · 80% урона · отброс 1 · КД 10с'},
            {'radius': 3, 'mul': 1.0, 'push': 2, 'cd_ms': 9000,
             'level_desc': '반경 3칸 · 100% 피해 · 2칸 밀치기 · 쿨 9초',
             'level_desc_en': 'Radius 3 · 100% DMG · push 2 · 9s CD',
             'level_desc_ja': '半径3 · 100%ダメージ · 2マス押し · CD9秒',
             'level_desc_zh': '半径3 · 100%伤害 · 击退2格 · 冷却9秒',
             'level_desc_ru': 'Радиус 3 · 100% урона · отброс 2 · КД 9с'},
            {'radius': 3, 'mul': 1.2, 'push': 2, 'stagger_ms': 800, 'cd_ms': 8000,
             'level_desc': '반경 3칸 · 120% 피해 · 2칸 밀치기 + 경직 · 쿨 8초',
             'level_desc_en': 'Radius 3 · 120% DMG · push 2 + stagger · 8s CD',
             'level_desc_ja': '半径3 · 120%ダメージ · 2マス押し+硬直 · CD8秒',
             'level_desc_zh': '半径3 · 120%伤害 · 击退2格+僵直 · 冷却8秒',
             'level_desc_ru': 'Радиус 3 · 120% урона · отброс 2 + оглуш. · КД 8с'},
        ],
        'sp_cost': [5, 10],
    },
    # ── 궁수 전용 스킬 (원거리) ─────────────────────────────────────────
    'power_shot': {
        'name': '강궁 사격', 'name_en': 'Power Shot', 'name_ja': '剛弓射撃',
        'name_zh': '强弓射击', 'name_ru': 'Мощный выстрел',
        'slot_default': None,
        'level_req': 1,
        'cooldown_ms': 3500,
        'color': (255, 170, 60),
        'category': 'attack',
        'desc': '전방 관통 화살 — 경로의 모든 적을 꿰뚫는다',
        'desc_en': 'A piercing arrow that skewers every enemy in its path',
        'desc_ja': '前方貫通の矢 — 経路の敵をすべて貫く',
        'desc_zh': '前方穿透箭 — 贯穿路径上所有敌人',
        'desc_ru': 'Пробивная стрела, пронзающая всех врагов на пути',
        'usage': '전방 직선 관통 · 높은 배율',
        'usage_en': 'Line-piercing shot · high multiplier',
        'usage_ja': '前方直線貫通 · 高倍率',
        'usage_zh': '前方直线穿透 · 高倍率',
        'usage_ru': 'Пробивной выстрел по прямой · высокий множитель',
        'upgrades': [
            {'mul': 2.2, 'range': 8, 'cd_ms': 3500,
             'level_desc': '220% 관통 · 8칸 · 쿨 3.5초',
             'level_desc_en': '220% pierce · 8 tiles · 3.5s CD',
             'level_desc_ja': '220%貫通 · 8マス · CD3.5秒',
             'level_desc_zh': '220%穿透 · 8格 · 冷却3.5秒',
             'level_desc_ru': '220% пробой · 8 кл. · КД 3,5с'},
            {'mul': 2.7, 'range': 9, 'cd_ms': 3000,
             'level_desc': '270% 관통 · 9칸 · 쿨 3.0초',
             'level_desc_en': '270% pierce · 9 tiles · 3.0s CD',
             'level_desc_ja': '270%貫通 · 9マス · CD3.0秒',
             'level_desc_zh': '270%穿透 · 9格 · 冷却3.0秒',
             'level_desc_ru': '270% пробой · 9 кл. · КД 3,0с'},
            {'mul': 3.3, 'range': 10, 'cd_ms': 2600,
             'level_desc': '330% 관통 · 10칸 · 쿨 2.6초',
             'level_desc_en': '330% pierce · 10 tiles · 2.6s CD',
             'level_desc_ja': '330%貫通 · 10マス · CD2.6秒',
             'level_desc_zh': '330%穿透 · 10格 · 冷却2.6秒',
             'level_desc_ru': '330% пробой · 10 кл. · КД 2,6с'},
        ],
        'sp_cost': [5, 10],
    },
    'arrow_rain': {
        'name': '화살비', 'name_en': 'Arrow Rain', 'name_ja': '矢の雨',
        'name_zh': '箭雨', 'name_ru': 'Дождь стрел',
        'slot_default': None,
        'level_req': 1,
        'cooldown_ms': 6000,
        'color': (120, 200, 255),
        'category': 'attack',
        'desc': '전방 지역에 화살을 퍼부어 광역 피해',
        'desc_en': 'Rain arrows over an area ahead for AoE damage',
        'desc_ja': '前方の地域に矢を降らせて範囲ダメージ',
        'desc_zh': '向前方区域倾泻箭矢造成范围伤害',
        'desc_ru': 'Обрушивает стрелы на область впереди',
        'usage': '전방 반경 N칸 광역 사격',
        'usage_en': 'AoE volley, radius N ahead',
        'usage_ja': '前方半径Nマスの範囲射撃',
        'usage_zh': '前方半径N格范围射击',
        'usage_ru': 'Залп по области радиусом N',
        'upgrades': [
            {'radius': 2, 'mul': 1.1, 'cd_ms': 6000,
             'level_desc': '반경 2칸 · 110% 피해 · 쿨 6초',
             'level_desc_en': 'Radius 2 · 110% DMG · 6s CD',
             'level_desc_ja': '半径2 · 110%ダメージ · CD6秒',
             'level_desc_zh': '半径2 · 110%伤害 · 冷却6秒',
             'level_desc_ru': 'Радиус 2 · 110% урона · КД 6с'},
            {'radius': 2, 'mul': 1.3, 'cd_ms': 5500,
             'level_desc': '반경 2칸 · 130% 피해 · 쿨 5.5초',
             'level_desc_en': 'Radius 2 · 130% DMG · 5.5s CD',
             'level_desc_ja': '半径2 · 130%ダメージ · CD5.5秒',
             'level_desc_zh': '半径2 · 130%伤害 · 冷却5.5秒',
             'level_desc_ru': 'Радиус 2 · 130% урона · КД 5,5с'},
            {'radius': 3, 'mul': 1.5, 'cd_ms': 5000,
             'level_desc': '반경 3칸 · 150% 피해 · 쿨 5초',
             'level_desc_en': 'Radius 3 · 150% DMG · 5s CD',
             'level_desc_ja': '半径3 · 150%ダメージ · CD5秒',
             'level_desc_zh': '半径3 · 150%伤害 · 冷却5秒',
             'level_desc_ru': 'Радиус 3 · 150% урона · КД 5с'},
        ],
        'sp_cost': [5, 10],
    },
}
ALL_SKILL_DEFS = localize_defs(ALL_SKILL_DEFS)

# 기본 장착 슬롯 (전사)
DEFAULT_EQUIPPED: dict[str, str] = {
    slot: sid
    for sid, sdef in ALL_SKILL_DEFS.items()
    if (slot := dict.get(sdef, 'slot_default')) is not None
}

# 궁수 기본 장착 — 이동기 + 원거리 스킬 조합
DEFAULT_EQUIPPED_ARCHER: dict[str, str] = {
    'W': 'flash_dash',    # 구르기(회피 이동)
    'A': 'arrow_rain',    # 광역 사격
    'S': 'regen_breath',  # 회복
    'D': 'power_shot',    # 관통 강사격
}


def default_equipped_for(char_class: str) -> dict:
    return dict(DEFAULT_EQUIPPED_ARCHER if char_class == 'archer'
               else DEFAULT_EQUIPPED)

# 하위 호환 — 기존 SKILL_DEFS 리스트 (W/A/S/D 슬롯 기본 스킬)
SKILL_DEFS = [
    localize_defs({**sdef, 'key': slot})
    for slot, sid in DEFAULT_EQUIPPED.items()
    for sdef in [ALL_SKILL_DEFS[sid]]
]

# 스킬별 레벨업에 필요한 hit 수 (SP 변환용 — 5 hits = 1 SP)
SKILL_XP_REQ = {sid: [15, 30] for sid in ALL_SKILL_DEFS}

# 스킬 레벨별 스탯 (호환용)
SKILL_UPGRADES = {sid: sdef['upgrades'] for sid, sdef in ALL_SKILL_DEFS.items()}

# 기본스킬 해금 레벨 빠른 참조
SKILL_LEVEL_REQS: dict[str, int] = {
    sdef['slot_default']: sdef['level_req']
    for sid, sdef in ALL_SKILL_DEFS.items()
    if sdef.get('slot_default')
}

# 스킬 SP 비용 [Lv1→2, Lv2→3]
SKILL_SP_COST = {sid: sdef['sp_cost'] for sid, sdef in ALL_SKILL_DEFS.items()}

COMBO_SKILL_DEFS = {
    'WS': {
        'name': '성역의 가호', 'name_en': 'Sanctuary Blessing', 'name_ja': '聖域の加護',
        'name_zh': '圣域庇佑', 'name_ru': 'Благодать святилища',
        'cooldown_ms': 20000,
        'color': (255, 205, 50),
        'level_req': 16,
        'skill_level_req': 3,
        'book': 'skillbook_fortify',
        'desc': '공속 +50%  피해감소 20% (10초)',
        'desc_en': 'ATK Spd +50%, DMG taken -20% (10s)',
        'desc_ja': '攻速+50% 被ダメ-20% (10秒)',
        'desc_zh': '攻速+50% 减伤20% (10秒)',
        'desc_ru': 'Скор. атаки +50%, урон -20% (10с)',
        'keys': 'Ctrl+S',
        'atk_speed_bonus': 0.5,
        'defense_bonus': 5,
        'duration_ms': 10000,
    },
    'AD': {
        'name': '뇌신검', 'name_en': 'Thunder God Blade', 'name_ja': '雷神剣',
        'name_zh': '雷神剑', 'name_ru': 'Клинок бога грома',
        'cooldown_ms': 12000,
        'color': (200, 160, 255),
        'level_req': 20,
        'skill_level_req': 3,
        'book': 'skillbook_thunder',
        'desc': '무작위 적 5명에게 낙뢰',
        'desc_en': 'Lightning strikes 5 random enemies',
        'desc_ja': 'ランダムな敵5体に落雷',
        'desc_zh': '雷击5个随机敌人',
        'desc_ru': 'Молнии бьют по 5 случайным врагам',
        'keys': 'Ctrl+A',
    },
    'WA': {
        'name': '서리 폭발', 'name_en': 'Frost Burst', 'name_ja': '霜の爆発',
        'name_zh': '冰霜爆发', 'name_ru': 'Морозный взрыв',
        'cooldown_ms': 8000,
        'color': (100, 220, 255),
        'level_req': 20,
        'skill_level_req': 3,
        'book': 'skillbook_frost',
        'desc': '반경 3칸 빙결+냉기 피해',
        'desc_en': 'Freeze + frost damage in radius 3',
        'desc_ja': '半径3マスに氷結+冷気ダメージ',
        'desc_zh': '半径3格冰冻+冰霜伤害',
        'desc_ru': 'Заморозка + урон холодом в радиусе 3',
        'keys': 'Ctrl+W',
    },
    'WD': {
        'name': '차원참', 'name_en': 'Dimension Slash', 'name_ja': '次元斬',
        'name_zh': '次元斩', 'name_ru': 'Разрез измерений',
        'cooldown_ms': 6000,
        'color': (160, 255, 160),
        'level_req': 15,
        'skill_level_req': 3,
        'book': 'skillbook_wind',
        'desc': '전방 8칸 관통, 궤적 폭발',
        'desc_en': 'Pierce 8 tiles ahead, trail explodes',
        'desc_ja': '前方8マス貫通、軌跡が爆発',
        'desc_zh': '穿透前方8格，轨迹爆炸',
        'desc_ru': 'Пронзает 8 клеток, след взрывается',
        'keys': 'Ctrl+D',
    },
}
COMBO_SKILL_DEFS = localize_defs(COMBO_SKILL_DEFS)

ULTIMATE_SKILL_DEFS = {
    'R': {
        'name': '던전 브레이커', 'name_en': 'Dungeon Breaker', 'name_ja': 'ダンジョンブレイカー',
        'name_zh': '地城破坏者', 'name_ru': 'Разрушитель подземелий',
        'cooldown_ms': 60000,
        'color': (255, 50, 50),
        'level_req': 20,
        'desc': '화면 전체에 검강을 투하하여 초토화',
        'desc_en': 'Rain sword energy on the whole screen',
        'desc_ja': '画面全体に剣気を降らせて殲滅',
        'desc_zh': '剑气覆盖全屏，夷平一切',
        'desc_ru': 'Обрушивает мечи на весь экран',
        'keys': 'R',
    },
    'Ctrl_R': {
        'name': '진(眞): 일도양단', 'name_en': 'True Cut: One Slash', 'name_ja': '真・一刀両断',
        'name_zh': '真·一刀两断', 'name_ru': 'Истинный разруб',
        'cooldown_ms': 90000,
        'color': (255, 255, 255),
        'level_req': 30,
        'desc': '시전 시 무적, 모든 적에게 공격력 10배 일격',
        'desc_en': 'Invincible while casting, hit all enemies for 10x ATK',
        'desc_ja': '詠唱中無敵、全敵に攻撃力10倍の一撃',
        'desc_zh': '施放时无敌，对所有敌人造成10倍攻击',
        'desc_ru': 'Неуязвимость + удар x10 АТК по всем врагам',
        'keys': 'Ctrl+R',
    },
}
ULTIMATE_SKILL_DEFS = localize_defs(ULTIMATE_SKILL_DEFS)


ENCHANT_TYPES = ('power', 'haste', 'efficiency', 'arcane')
ENCHANT_MAX_LEVEL = 3

ENCHANT_DEFS = {
    'power': {
        'name': '위력', 'name_en': 'Power', 'name_ja': '威力', 'name_zh': '威力', 'name_ru': 'Мощь',
        'name_ko': '위력',
        'color': (255, 140, 60),
        'sp_cost': [3, 5, 8],
        'desc': '스킬 피해 +15%/레벨',
        'desc_en': 'Skill DMG +15%/level',
        'desc_ja': 'スキルダメージ+15%/Lv',
        'desc_zh': '技能伤害+15%/级',
        'desc_ru': 'Урон навыков +15%/ур.',
    },
    'haste': {
        'name': '신속', 'name_en': 'Haste', 'name_ja': '神速', 'name_zh': '迅捷', 'name_ru': 'Быстрота',
        'name_ko': '신속',
        'color': (100, 200, 255),
        'sp_cost': [3, 5, 8],
        'desc': '쿨타임 -10%/레벨',
        'desc_en': 'Cooldown -10%/level',
        'desc_ja': 'クールタイム-10%/Lv',
        'desc_zh': '冷却-10%/级',
        'desc_ru': 'КД -10%/ур.',
    },
    'efficiency': {
        'name': '절약', 'name_en': 'Efficiency', 'name_ja': '節約', 'name_zh': '节约', 'name_ru': 'Экономия',
        'name_ko': '절약',
        'color': (80, 220, 130),
        'sp_cost': [3, 5, 8],
        'desc': '스킬 SP 소모 -15%/레벨',
        'desc_en': 'Skill SP cost -15%/level',
        'desc_ja': 'スキルSP消費-15%/Lv',
        'desc_zh': '技能SP消耗-15%/级',
        'desc_ru': 'Затраты SP навыков -15%/ур.',
    },
    'arcane': {
        'name': '오의', 'name_en': 'Arcane', 'name_ja': '奥義', 'name_zh': '奥义', 'name_ru': 'Тайна',
        'name_ko': '오의',
        'color': (200, 100, 255),
        'sp_cost': [5, 10, 20],
        'desc': '오의 연계 개방 (R키)',
        'desc_en': 'Unlock Arcane chain (R key)',
        'desc_ja': '奥義連携を開放 (Rキー)',
        'desc_zh': '开启奥义连锁 (R键)',
        'desc_ru': 'Открывает тайную связку (клавиша R)',
    },
}
ENCHANT_DEFS = localize_defs(ENCHANT_DEFS)


class SkillManager:
    def __init__(self):
        self._cd: dict[str, int] = {sid: 0 for sid in ALL_SKILL_DEFS}
        self._cd.update({k: 0 for k in COMBO_SKILL_DEFS})
        self._cd.update({k: 0 for k in ULTIMATE_SKILL_DEFS})
        self._max_cd_override: dict[str, int] = {}

    def set_cd_override(self, key: str, ms: int):
        self._max_cd_override[key] = ms

    def update(self, dt_ms: int):
        for k in self._cd:
            if self._cd[k] > 0:
                self._cd[k] = max(0, self._cd[k] - dt_ms)

    def ready(self, key: str) -> bool:
        return self._cd.get(key, 0) <= 0

    def cooldown_frac(self, key: str) -> float:
        ms = self._get_max_cd(key)
        return self._cd.get(key, 0) / ms if ms > 0 else 0.0

    def remaining_sec(self, key: str) -> float:
        return self._cd.get(key, 0) / 1000.0

    def trigger(self, key: str):
        ms = self._get_max_cd(key)
        if ms > 0:
            self._cd[key] = ms

    def reset(self, key: str):
        self._cd[key] = 0

    def _get_max_cd(self, key: str) -> int:
        if key in self._max_cd_override:
            return self._max_cd_override[key]
        sdef = ALL_SKILL_DEFS.get(key)
        if sdef:
            return sdef['cooldown_ms']
        cdef = COMBO_SKILL_DEFS.get(key)
        if cdef:
            return cdef['cooldown_ms']
        udef = ULTIMATE_SKILL_DEFS.get(key)
        return udef['cooldown_ms'] if udef else 0

    def to_dict(self) -> dict:
        return dict(self._cd)

    def from_dict(self, d: dict):
        for k in self._cd:
            if k in d:
                self._cd[k] = d[k]

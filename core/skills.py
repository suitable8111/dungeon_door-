"""스킬 시스템: 장착형 기본 스킬(W/A/S/D) + 조합 스킬 + 궁극기."""

SKILL_MAX_LEVEL = 3

# ── 장착 가능한 모든 스킬 정의 ──────────────────────────────────────────
ALL_SKILL_DEFS = {
    # ── 기본 장착 스킬 (Default) ──────────────────────────────────────
    'flash_dash': {
        'name': '섬광 돌진',
        'slot_default': 'W',
        'level_req': 5,
        'cooldown_ms': 3000,
        'color': (100, 180, 255),
        'category': 'mobility',
        'desc': '전방으로 고속 돌진, 경로의 적을 경직',
        'usage': '이동 방향으로 N칸 돌진 · 경로 적 경직',
        'upgrades': [
            {'tiles': 3, 'stagger_ms': 1000, 'cd_ms': 3000,
             'level_desc': '3칸 돌진 · 경직 1.0초 · 쿨 3.0초'},
            {'tiles': 4, 'stagger_ms': 1200, 'cd_ms': 2500,
             'level_desc': '4칸 돌진 · 경직 1.2초 · 쿨 2.5초'},
            {'tiles': 5, 'stagger_ms': 1500, 'cd_ms': 2000,
             'level_desc': '5칸 돌진 · 경직 1.5초 · 쿨 2.0초'},
        ],
        'sp_cost': [5, 10],
    },
    'steel_whirl': {
        'name': '강철 회오리',
        'slot_default': 'A',
        'level_req': 10,
        'cooldown_ms': 5000,
        'color': (255, 180, 60),
        'category': 'attack',
        'desc': '주변 8방향 적을 모두 휩쓸어 피해',
        'usage': '플레이어 중심 반경 N칸 광역 공격',
        'upgrades': [
            {'radius': 1, 'mul': 1.0, 'cd_ms': 5000,
             'level_desc': '반경 1칸 · 100% 피해 · 쿨 5.0초'},
            {'radius': 2, 'mul': 1.0, 'cd_ms': 5000,
             'level_desc': '반경 2칸 · 100% 피해 · 쿨 5.0초'},
            {'radius': 2, 'mul': 1.2, 'cd_ms': 4000,
             'level_desc': '반경 2칸 · 120% 피해 · 쿨 4.0초'},
        ],
        'sp_cost': [5, 10],
    },
    'regen_breath': {
        'name': '재생의 숨결',
        'slot_default': 'S',
        'level_req': 6,
        'cooldown_ms': 10000,
        'color': (80, 220, 130),
        'category': 'defense',
        'desc': 'HP를 회복하고 일시적으로 방어력 증가',
        'usage': '즉시 HP 회복 + 방어 버프',
        'upgrades': [
            {'heal_pct': 0.25, 'def_bonus': 3, 'def_ms': 3000, 'cd_ms': 10000,
             'level_desc': 'HP 25% 회복 · 방어+3 (3초) · 쿨 10초'},
            {'heal_pct': 0.35, 'def_bonus': 5, 'def_ms': 3000, 'cd_ms': 9000,
             'level_desc': 'HP 35% 회복 · 방어+5 (3초) · 쿨 9초'},
            {'heal_pct': 0.50, 'def_bonus': 8, 'def_ms': 5000, 'cd_ms': 7000,
             'level_desc': 'HP 50% 회복 · 방어+8 (5초) · 쿨 7초'},
        ],
        'sp_cost': [5, 10],
    },
    'judgment': {
        'name': '심판의 일격',
        'slot_default': 'D',
        'level_req': 1,
        'cooldown_ms': 4000,
        'color': (255, 100, 80),
        'category': 'attack',
        'desc': '전방 적에게 강력한 일격, 높은 치명타 확률',
        'usage': '전방 단일 강타 · 치명타 시 1.5배 추가 피해',
        'upgrades': [
            {'mul': 2.0, 'crit': 0.25, 'cd_ms': 4000,
             'level_desc': '200% 피해 · 치명 25% · 쿨 4.0초'},
            {'mul': 2.5, 'crit': 0.30, 'cd_ms': 3500,
             'level_desc': '250% 피해 · 치명 30% · 쿨 3.5초'},
            {'mul': 3.0, 'crit': 0.35, 'cd_ms': 3000,
             'level_desc': '300% 피해 · 치명 35% · 쿨 3.0초'},
        ],
        'sp_cost': [5, 10],
    },

    # ── 추가 장착 스킬 ──────────────────────────────────────────────────
    'shadow_step': {
        'name': '그림자 발걸음',
        'slot_default': None,
        'level_req': 3,
        'cooldown_ms': 4000,
        'color': (180, 100, 255),
        'category': 'mobility',
        'desc': '전방으로 순간이동, 도착 지점의 적을 밀쳐냄',
        'usage': '이동 방향으로 N칸 순간이동 · 도달 지점 적 경직',
        'upgrades': [
            {'tiles': 3, 'cd_ms': 4000,
             'level_desc': '3칸 순간이동 · 도착 적 경직 0.5초 · 쿨 4.0초'},
            {'tiles': 4, 'cd_ms': 3500,
             'level_desc': '4칸 순간이동 · 도착 적 경직 0.8초 · 쿨 3.5초'},
            {'tiles': 5, 'cd_ms': 3000,
             'level_desc': '5칸 순간이동 · 도착 적 경직 1.0초 · 쿨 3.0초'},
        ],
        'sp_cost': [5, 10],
    },
    'iron_shell': {
        'name': '철갑 방벽',
        'slot_default': None,
        'level_req': 8,
        'cooldown_ms': 12000,
        'color': (180, 200, 230),
        'category': 'defense',
        'desc': '일시적으로 받는 피해를 대폭 감소',
        'usage': '일정 시간 동안 받는 피해 N% 감소',
        'upgrades': [
            {'reduce': 0.50, 'duration_ms': 2000, 'cd_ms': 12000,
             'level_desc': '피해 50% 감소 · 2초 · 쿨 12초'},
            {'reduce': 0.65, 'duration_ms': 2500, 'cd_ms': 10000,
             'level_desc': '피해 65% 감소 · 2.5초 · 쿨 10초'},
            {'reduce': 0.80, 'duration_ms': 3000, 'cd_ms': 8000,
             'level_desc': '피해 80% 감소 · 3초 · 쿨 8초'},
        ],
        'sp_cost': [5, 10],
    },
    'flame_strike': {
        'name': '화염 강타',
        'slot_default': None,
        'level_req': 12,
        'cooldown_ms': 6000,
        'color': (255, 140, 40),
        'category': 'attack',
        'desc': '전방 직선 범위에 강렬한 화염 피해',
        'usage': '이동 방향으로 N칸 직선 화염 공격',
        'upgrades': [
            {'range': 3, 'mul': 1.5, 'cd_ms': 6000,
             'level_desc': '전방 3칸 · 150% 피해 · 쿨 6초'},
            {'range': 4, 'mul': 1.8, 'cd_ms': 5500,
             'level_desc': '전방 4칸 · 180% 피해 · 쿨 5.5초'},
            {'range': 5, 'mul': 2.2, 'cd_ms': 5000,
             'level_desc': '전방 5칸 · 220% 피해 · 쿨 5초'},
        ],
        'sp_cost': [5, 10],
    },
    'life_steal': {
        'name': '생명 흡수',
        'slot_default': None,
        'level_req': 15,
        'cooldown_ms': 8000,
        'color': (220, 80, 180),
        'category': 'attack',
        'desc': '주변 적을 공격하고 피해량 일부를 HP로 흡수',
        'usage': '반경 N칸 적 공격 · 피해의 N% HP 흡수',
        'upgrades': [
            {'radius': 2, 'steal_pct': 0.30, 'cd_ms': 8000,
             'level_desc': '반경 2칸 · 30% 흡수 · 쿨 8초'},
            {'radius': 3, 'steal_pct': 0.40, 'cd_ms': 7000,
             'level_desc': '반경 3칸 · 40% 흡수 · 쿨 7초'},
            {'radius': 3, 'steal_pct': 0.50, 'cd_ms': 6000,
             'level_desc': '반경 3칸 · 50% 흡수 · 쿨 6초'},
        ],
        'sp_cost': [5, 10],
    },
    'war_cry': {
        'name': '전투 함성',
        'slot_default': None,
        'level_req': 18,
        'cooldown_ms': 15000,
        'color': (255, 220, 60),
        'category': 'buff',
        'desc': '잠시 동안 공격력이 크게 증가',
        'usage': '일정 시간 동안 공격력 N% 증가',
        'upgrades': [
            {'atk_mul': 0.30, 'duration_ms': 5000, 'cd_ms': 15000,
             'level_desc': '공격력 +30% · 5초 · 쿨 15초'},
            {'atk_mul': 0.50, 'duration_ms': 6000, 'cd_ms': 13000,
             'level_desc': '공격력 +50% · 6초 · 쿨 13초'},
            {'atk_mul': 0.70, 'duration_ms': 8000, 'cd_ms': 11000,
             'level_desc': '공격력 +70% · 8초 · 쿨 11초'},
        ],
        'sp_cost': [5, 10],
    },
    'dark_pulse': {
        'name': '암흑 파동',
        'slot_default': None,
        'level_req': 20,
        'cooldown_ms': 10000,
        'color': (140, 80, 220),
        'category': 'attack',
        'desc': '주변 적을 밀쳐내고 피해를 입힘',
        'usage': '반경 N칸 광역 피해 + 적을 N칸 밀쳐냄',
        'upgrades': [
            {'radius': 2, 'mul': 0.8, 'push': 1, 'cd_ms': 10000,
             'level_desc': '반경 2칸 · 80% 피해 · 1칸 밀치기 · 쿨 10초'},
            {'radius': 3, 'mul': 1.0, 'push': 2, 'cd_ms': 9000,
             'level_desc': '반경 3칸 · 100% 피해 · 2칸 밀치기 · 쿨 9초'},
            {'radius': 3, 'mul': 1.2, 'push': 2, 'stagger_ms': 800, 'cd_ms': 8000,
             'level_desc': '반경 3칸 · 120% 피해 · 2칸 밀치기 + 경직 · 쿨 8초'},
        ],
        'sp_cost': [5, 10],
    },
}

# 기본 장착 슬롯
DEFAULT_EQUIPPED: dict[str, str] = {
    slot: sid
    for sid, sdef in ALL_SKILL_DEFS.items()
    if (slot := sdef.get('slot_default')) is not None
}

# 하위 호환 — 기존 SKILL_DEFS 리스트 (W/A/S/D 슬롯 기본 스킬)
SKILL_DEFS = [
    {**sdef, 'key': slot}
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
        'name': '성역의 가호',
        'cooldown_ms': 20000,
        'color': (255, 205, 50),
        'level_req': 16,
        'skill_level_req': 3,
        'book': 'skillbook_fortify',
        'desc': '공속 +50%  피해감소 20% (10초)',
        'keys': 'Ctrl+S',
        'atk_speed_bonus': 0.5,
        'defense_bonus': 5,
        'duration_ms': 10000,
    },
    'AD': {
        'name': '뇌신검',
        'cooldown_ms': 12000,
        'color': (200, 160, 255),
        'level_req': 20,
        'skill_level_req': 3,
        'book': 'skillbook_thunder',
        'desc': '무작위 적 5명에게 낙뢰',
        'keys': 'Ctrl+A',
    },
    'WA': {
        'name': '서리 폭발',
        'cooldown_ms': 8000,
        'color': (100, 220, 255),
        'level_req': 20,
        'skill_level_req': 3,
        'book': 'skillbook_frost',
        'desc': '반경 3칸 빙결+냉기 피해',
        'keys': 'Ctrl+W',
    },
    'WD': {
        'name': '차원참',
        'cooldown_ms': 6000,
        'color': (160, 255, 160),
        'level_req': 15,
        'skill_level_req': 3,
        'book': 'skillbook_wind',
        'desc': '전방 8칸 관통, 궤적 폭발',
        'keys': 'Ctrl+D',
    },
}

ULTIMATE_SKILL_DEFS = {
    'R': {
        'name': '던전 브레이커',
        'cooldown_ms': 60000,
        'color': (255, 50, 50),
        'level_req': 20,
        'desc': '화면 전체에 검강을 투하하여 초토화',
        'keys': 'R',
    },
    'Ctrl_R': {
        'name': '진(眞): 일도양단',
        'cooldown_ms': 90000,
        'color': (255, 255, 255),
        'level_req': 30,
        'desc': '시전 시 무적, 모든 적에게 공격력 10배 일격',
        'keys': 'Ctrl+R',
    },
}


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

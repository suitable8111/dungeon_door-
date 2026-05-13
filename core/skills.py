"""스킬 시스템: 단일 WASD 스킬 + 강화 스킬 + 궁극기."""

SKILL_MAX_LEVEL = 3

# 스킬별 레벨업에 필요한 누적 hit 수 [Lv1→2, Lv2→3]
SKILL_XP_REQ = {
    'W': [15, 30],
    'A': [20, 40],
    'S': [8,  16],
    'D': [15, 30],
}

# 각 스킬의 레벨별 스탯 (index = level - 1)
SKILL_UPGRADES = {
    'W': [
        {'tiles': 3, 'stagger_ms': 1000, 'cd_ms': 3000},
        {'tiles': 4, 'stagger_ms': 1200, 'cd_ms': 2500},
        {'tiles': 5, 'stagger_ms': 1500, 'cd_ms': 2000},
    ],
    'A': [
        {'radius': 1, 'mul': 1.0, 'cd_ms': 5000},
        {'radius': 2, 'mul': 1.0, 'cd_ms': 5000},
        {'radius': 2, 'mul': 1.2, 'cd_ms': 4000},
    ],
    'S': [
        {'heal_pct': 0.25, 'def_bonus': 3, 'def_ms': 3000, 'cd_ms': 10000},
        {'heal_pct': 0.35, 'def_bonus': 5, 'def_ms': 3000, 'cd_ms': 9000},
        {'heal_pct': 0.50, 'def_bonus': 8, 'def_ms': 5000, 'cd_ms': 7000},
    ],
    'D': [
        {'mul': 2.0, 'crit': 0.25, 'cd_ms': 4000},
        {'mul': 2.5, 'crit': 0.30, 'cd_ms': 3500},
        {'mul': 3.0, 'crit': 0.35, 'cd_ms': 3000},
    ],
}

SKILL_DEFS = [
    {'key': 'W', 'name': '섬광 돌진',   'cooldown_ms': 3000,  'color': (100, 180, 255), 'desc': '3칸 전진, 경로상 적 경직'},
    {'key': 'A', 'name': '강철 회오리', 'cooldown_ms': 5000,  'color': (255, 180, 60),  'desc': '주변 8방향 휩쓸기'},
    {'key': 'S', 'name': '재생의 숨결', 'cooldown_ms': 10000, 'color': (80, 220, 130),  'desc': 'HP 25% 회복 + 방어력 상승'},
    {'key': 'D', 'name': '심판의 일격', 'cooldown_ms': 4000,  'color': (255, 100, 80),  'desc': '전방 2.5배 강타'},
]

COMBO_SKILL_DEFS = {
    'WS': {
        'name': '성역의 가호',
        'cooldown_ms': 20000,
        'color': (255, 205, 50),
        'level_req': 5,
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
        'level_req': 12,
        'book': 'skillbook_thunder',
        'desc': '무작위 적 5명에게 낙뢰',
        'keys': 'Ctrl+A',
    },
    'WA': {
        'name': '서리 폭발',
        'cooldown_ms': 8000,
        'color': (100, 220, 255),
        'level_req': 8,
        'book': 'skillbook_frost',
        'desc': '반경 3칸 빙결+냉기 피해',
        'keys': 'Ctrl+W',
    },
    'WD': {
        'name': '차원참',
        'cooldown_ms': 6000,
        'color': (160, 255, 160),
        'level_req': 10,
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
        self._cd: dict[str, int] = {s['key']: 0 for s in SKILL_DEFS}
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
        """0.0 = 사용 가능, 1.0 = 방금 사용."""
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
        for s in SKILL_DEFS:
            if s['key'] == key:
                return s['cooldown_ms']
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

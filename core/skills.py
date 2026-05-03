"""스킬 시스템: 단일 WASD 스킬 + 조합 스킬."""

SKILL_MAX_LEVEL = 3

# 스킬별 레벨업에 필요한 누적 hit 수 [Lv1→2, Lv2→3]
SKILL_XP_REQ = {
    'W': [15, 30],   # 돌진: 사용 횟수 기반
    'A': [20, 40],   # 회오리: 적 타격 수 기반
    'S': [8,  16],   # 치유: 사용 횟수 기반
    'D': [15, 30],   # 파워어택: 적 타격 수 기반
}

# 각 스킬의 레벨별 스탯 (index = level - 1)
SKILL_UPGRADES = {
    'W': [
        {'tiles': 3, 'cd_ms': 3000},
        {'tiles': 4, 'cd_ms': 2500},
        {'tiles': 5, 'cd_ms': 2000},
    ],
    'A': [
        {'radius': 1, 'mul': 1.0, 'cd_ms': 5000},
        {'radius': 2, 'mul': 1.0, 'cd_ms': 5000},
        {'radius': 2, 'mul': 1.2, 'cd_ms': 4000},
    ],
    'S': [
        {'heal_pct': 0.30, 'cd_ms': 8000},
        {'heal_pct': 0.40, 'cd_ms': 8000},
        {'heal_pct': 0.50, 'cd_ms': 6000},
    ],
    'D': [
        {'mul': 2.0, 'crit': 0.25, 'cd_ms': 4000},
        {'mul': 2.5, 'crit': 0.30, 'cd_ms': 3500},
        {'mul': 3.0, 'crit': 0.35, 'cd_ms': 3000},
    ],
}

SKILL_DEFS = [
    {'key': 'W', 'name': '돌진',     'cooldown_ms': 3000, 'color': (100, 180, 255), 'desc': '3칸 전진'},
    {'key': 'A', 'name': '회오리',   'cooldown_ms': 5000, 'color': (255, 180, 60),  'desc': '8방향 공격'},
    {'key': 'S', 'name': '치유',     'cooldown_ms': 8000, 'color': (80, 220, 130),  'desc': 'HP 30% 회복'},
    {'key': 'D', 'name': '파워어택', 'cooldown_ms': 4000, 'color': (255, 100, 80),  'desc': '강타 2배'},
]

# 조합 스킬: combo_id → {name, cooldown_ms, color, level_req, book, desc, keys}
COMBO_SKILL_DEFS = {
    'WS': {
        'name': '파이어볼',
        'cooldown_ms': 6000,
        'color': (255, 140, 40),
        'level_req': 5,
        'book': 'skillbook_fireball',
        'desc': '전방 화염 투사체',
        'keys': 'W+S',
    },
    'AD': {
        'name': '천둥격',
        'cooldown_ms': 9000,
        'color': (200, 160, 255),
        'level_req': 7,
        'book': 'skillbook_thunder',
        'desc': '시야 내 전체 공격',
        'keys': 'A+D',
    },
    'WA': {
        'name': '냉기 폭발',
        'cooldown_ms': 7000,
        'color': (100, 220, 255),
        'level_req': 6,
        'book': 'skillbook_frost',
        'desc': '반경 2칸 범위 피해',
        'keys': 'W+A',
    },
    'WD': {
        'name': '바람 칼날',
        'cooldown_ms': 5000,
        'color': (160, 255, 160),
        'level_req': 4,
        'book': 'skillbook_wind',
        'desc': '직선 관통 6칸',
        'keys': 'W+D',
    },
}


class SkillManager:
    def __init__(self):
        self._cd: dict[str, int] = {s['key']: 0 for s in SKILL_DEFS}
        self._cd.update({k: 0 for k in COMBO_SKILL_DEFS})
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

    def _get_max_cd(self, key: str) -> int:
        if key in self._max_cd_override:
            return self._max_cd_override[key]
        for s in SKILL_DEFS:
            if s['key'] == key:
                return s['cooldown_ms']
        cdef = COMBO_SKILL_DEFS.get(key)
        return cdef['cooldown_ms'] if cdef else 0

    def to_dict(self) -> dict:
        return dict(self._cd)

    def from_dict(self, d: dict):
        for k in self._cd:
            if k in d:
                self._cd[k] = d[k]

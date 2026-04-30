"""스킬 시스템: Q 돌진 / E 회오리 / F 치유."""

SKILL_DEFS = [
    {
        'key': 'Q',
        'name': '돌진',
        'cooldown_ms': 3000,
        'color': (100, 180, 255),
        'desc': '3칸 전진',
    },
    {
        'key': 'E',
        'name': '회오리',
        'cooldown_ms': 5000,
        'color': (255, 180, 60),
        'desc': '8방향 공격',
    },
    {
        'key': 'F',
        'name': '치유',
        'cooldown_ms': 8000,
        'color': (80, 220, 130),
        'desc': 'HP 30% 회복',
    },
]


class SkillManager:
    def __init__(self):
        self._cd = {s['key']: 0 for s in SKILL_DEFS}

    def update(self, dt_ms):
        for k in self._cd:
            if self._cd[k] > 0:
                self._cd[k] = max(0, self._cd[k] - dt_ms)

    def ready(self, key):
        return self._cd.get(key, 0) <= 0

    def cooldown_frac(self, key):
        """0.0 = 사용 가능, 1.0 = 방금 사용."""
        for s in SKILL_DEFS:
            if s['key'] == key:
                if s['cooldown_ms'] == 0:
                    return 0.0
                return self._cd[key] / s['cooldown_ms']
        return 0.0

    def remaining_sec(self, key):
        return self._cd.get(key, 0) / 1000.0

    def trigger(self, key):
        for s in SKILL_DEFS:
            if s['key'] == key:
                self._cd[key] = s['cooldown_ms']
                return

    def to_dict(self):
        return dict(self._cd)

    def from_dict(self, d):
        for k in self._cd:
            if k in d:
                self._cd[k] = d[k]

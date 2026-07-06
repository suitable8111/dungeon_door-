"""도전과제 시스템.

로컬 우선: 진행도/달성을 achievements.json에 저장하고 달성 시 콜백(토스트).
Steam 동기화: SteamworksPy + steam_api 라이브러리가 있으면 자동으로
SetAchievement를 호출한다. 없으면 조용히 로컬로만 동작 (맥 개발 환경 포함).

Steamworks 파트너 사이트의 Stats & Achievements에 아래 API 이름과
동일하게 등록해야 한다 (ACHIEVEMENTS 키 = API Name).
"""
import json
import os

_BASE = os.path.dirname(os.path.abspath(__file__))
ACH_PATH = os.path.join(_BASE, '..', 'achievements.json')

# api_name: (달성 조건 설명용 메타. 표시명/설명은 lang.py의 ach_* 키 사용)
#   stat: 카운터 이름, need: 임계값 — 카운터형 도전과제
#   stat 없음 — 이벤트형 (unlock 직접 호출)
ACHIEVEMENTS = {
    'ACH_FIRST_BLOOD': {'stat': 'kills',       'need': 1},
    'ACH_KILLS_500':   {'stat': 'kills',       'need': 500},
    'ACH_ELITE_25':    {'stat': 'elite_kills', 'need': 25},
    'ACH_BOSS_10':     {'stat': 'boss_kills',  'need': 10},
    'ACH_FLOOR_5':     {},
    'ACH_FLOOR_10':    {},
    'ACH_FLOOR_25':    {},
    'ACH_FLOOR_50':    {},
    'ACH_FIRST_BOSS':  {},
    'ACH_COMBO_15':    {},
    'ACH_LEVEL_20':    {},
    'ACH_ENHANCE_10':  {},
    'ACH_RICH':        {},
    'ACH_BURNING':     {},
    'ACH_ULTIMATE':    {},
    'ACH_DIE':         {},
}

# 층수 도달형: floor → api_name
FLOOR_ACHIEVEMENTS = {
    5: 'ACH_FLOOR_5', 10: 'ACH_FLOOR_10',
    25: 'ACH_FLOOR_25', 50: 'ACH_FLOOR_50',
}


class AchievementManager:
    def __init__(self, on_unlock=None):
        """on_unlock(api_name): 새 달성 시 호출되는 콜백 (토스트 표시용)."""
        self.on_unlock = on_unlock
        self.unlocked: set = set()
        self.stats: dict = {}
        self._load()
        self._steam = self._init_steam()
        if self._steam:
            self._sync_all_to_steam()

    # ── Steam (옵셔널) ────────────────────────────────────────────────
    def _init_steam(self):
        try:
            from steamworks import STEAMWORKS
            sw = STEAMWORKS()
            sw.initialize()   # steam_appid.txt 또는 스팀 실행 환경 필요
            sw.UserStats.RequestCurrentStats()
            return sw
        except Exception:
            return None

    def _steam_set(self, api_name: str):
        if not self._steam:
            return
        try:
            self._steam.UserStats.SetAchievement(api_name.encode())
            self._steam.UserStats.StoreStats()
        except Exception:
            pass

    def _sync_all_to_steam(self):
        """스팀 미실행 중 로컬로 달성한 항목을 재동기화."""
        for api in self.unlocked:
            self._steam_set(api)

    # ── 영속화 ────────────────────────────────────────────────────────
    def _load(self):
        try:
            with open(ACH_PATH, encoding='utf-8') as f:
                d = json.load(f)
            self.unlocked = set(d.get('unlocked', []))
            self.stats    = dict(d.get('stats', {}))
        except Exception:
            pass

    def _save(self):
        try:
            with open(ACH_PATH, 'w', encoding='utf-8') as f:
                json.dump({'unlocked': sorted(self.unlocked),
                           'stats': self.stats}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── 공개 API ──────────────────────────────────────────────────────
    def unlock(self, api_name: str) -> bool:
        """달성 처리. 새로 달성했으면 True."""
        if api_name not in ACHIEVEMENTS or api_name in self.unlocked:
            return False
        self.unlocked.add(api_name)
        self._save()
        self._steam_set(api_name)
        if self.on_unlock:
            self.on_unlock(api_name)
        return True

    def add_stat(self, stat: str, amount: int = 1):
        """누적 카운터 증가 + 임계값 도달 시 자동 달성."""
        self.stats[stat] = self.stats.get(stat, 0) + amount
        self._save()
        for api, meta in ACHIEVEMENTS.items():
            if meta.get('stat') == stat and self.stats[stat] >= meta['need']:
                self.unlock(api)

    def check_floor(self, floor: int):
        for f, api in FLOOR_ACHIEVEMENTS.items():
            if floor >= f:
                self.unlock(api)

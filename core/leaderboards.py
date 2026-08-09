"""리더보드 시스템 — 로컬 우선 + Steam 리더보드 연동.

설계(업적 모듈과 동일 철학):
- **로컬 우선**: 내 최고 점수를 leaderboards.json 에 저장한다. 오프라인/헤드리스에서도
  UI·플로우가 동작하도록, Steam 이 없으면 '내 기록 1줄'을 폴백으로 보여준다.
- **Steam 연동**: SteamworksPy 가 있으면 점수를 업로드(KeepBest)하고 전세계/친구 순위를
  비동기로 내려받아 cache 에 채운다. Steam 리더보드 API 는 콜백 기반이라 조회 결과는
  즉시가 아니라 나중에 cache 로 들어온다 — UI 는 cache 를 읽는다.

Steamworks 파트너 사이트에 아래 LEADERBOARDS 키와 동일한 이름으로 리더보드를 만들어야
한다(정렬=내림차순, 표시=숫자). 이름이 곧 API 이름이다.

주의: Steam 리더보드는 실제 Steam 실행 환경에서만 검증 가능(업적과 동일). 이 모듈의
Steam 경로는 모두 try/except 로 감싸 없으면 조용히 로컬로 동작한다.
"""
import json
import os

_BASE = os.path.dirname(os.path.abspath(__file__))
LB_PATH = os.path.join(_BASE, '..', 'leaderboards.json')

# name(=Steam API 이름): 메타. label=lang 키, cls=직업 필터(없으면 전체)
# 순서 = UI 탭 순서.
LEADERBOARDS = {
    'best_floor':         {'label': 'lb_best_floor',         'cls': None},
    'best_floor_warrior': {'label': 'lb_best_floor_warrior', 'cls': 'warrior'},
    'best_floor_archer':  {'label': 'lb_best_floor_archer',  'cls': 'archer'},
    'best_floor_mage':    {'label': 'lb_best_floor_mage',    'cls': 'mage'},
    'best_level':         {'label': 'lb_best_level',         'cls': None},
}

# 모든 리더보드는 '높을수록 좋음'(내림차순, 최고기록 유지).


_UNSET = object()


class LeaderboardManager:
    def __init__(self, player_name='Hero', steam=_UNSET):
        """steam: 기존 Steam 인스턴스를 넘기면 재사용(중복 initialize 방지).
        업적 매니저가 이미 STEAMWORKS().initialize() 했으므로 그 인스턴스를 공유한다.
        미지정 시 자체 초기화(단독 사용/테스트)."""
        self.player_name = player_name or 'Hero'
        self.local: dict = {}     # name -> 내 최고 점수(int)
        self.cache: dict = {}     # name -> [{'rank','name','score','me'}]  (Steam 조회 결과)
        self._load()
        self._steam = self._init_steam() if steam is _UNSET else steam
        self._handles: dict = {}  # name -> Steam leaderboard handle
        if self._steam:
            for name in LEADERBOARDS:
                self._steam_find(name)

    # ── 영속화 ────────────────────────────────────────────────────────
    def _load(self):
        try:
            with open(LB_PATH, encoding='utf-8') as f:
                d = json.load(f)
            self.local = {k: int(v) for k, v in dict(d.get('local', {})).items()
                          if k in LEADERBOARDS}
        except Exception:
            self.local = {}

    def _save(self):
        try:
            with open(LB_PATH, 'w', encoding='utf-8') as f:
                json.dump({'local': self.local}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── 공개 API ──────────────────────────────────────────────────────
    def submit_run(self, floor: int, level: int, char_class: str):
        """한 판 결과를 관련 리더보드에 반영(최고기록만 유지)."""
        self.submit('best_floor', floor)
        cls_lb = f'best_floor_{char_class}'
        if cls_lb in LEADERBOARDS:
            self.submit(cls_lb, floor)
        self.submit('best_level', level)

    def submit(self, name: str, score) -> bool:
        """점수 제출 — 로컬 최고기록 갱신 + Steam 업로드(KeepBest). 갱신 시 True."""
        if name not in LEADERBOARDS:
            return False
        score = int(score)
        improved = score > self.local.get(name, 0)
        if improved:
            self.local[name] = score
            self._save()
        # Steam 은 KeepBest 이므로 매번 올려도 안전(개선 없어도 무해)
        self._steam_upload(name, score)
        return improved

    def best(self, name: str) -> int:
        return int(self.local.get(name, 0))

    def pump(self):
        """Steam 콜백 디스패치 — 리더보드 조회/업로드 결과가 비동기로 도착.
        업적과 인스턴스를 공유하므로 여기서 한 번만 돌리면 된다."""
        if not self._steam:
            return
        try:
            self._steam.run_callbacks()
        except Exception:
            pass

    def get_entries(self, name: str, mode: str = 'global', count: int = 20) -> list:
        """리더보드 항목 리스트. Steam 캐시가 있으면 그것을, 없으면 로컬 폴백(내 기록).

        반환: [{'rank','name','score','me'}] (순위 오름차순).
        """
        key = (name, mode)
        cached = self.cache.get(key)
        if cached:
            return cached[:count]
        # Steam 조회 요청(비동기) — 다음 프레임 이후 캐시에 채워진다
        self._steam_download(name, mode, count)
        # 폴백: 내 기록만
        if name in self.local and self.local[name] > 0:
            return [{'rank': 0, 'name': self.player_name,
                     'score': self.local[name], 'me': True}]
        return []

    def refresh(self, name: str, mode: str = 'global', count: int = 20):
        """캐시 무효화 후 재조회 요청(UI 새로고침)."""
        self.cache.pop((name, mode), None)
        self._steam_download(name, mode, count)

    # ── Steam (옵셔널, 콜백 기반) ─────────────────────────────────────
    def _init_steam(self):
        try:
            from steamworks import STEAMWORKS
            sw = STEAMWORKS()
            sw.initialize()
            return sw
        except Exception:
            return None

    def _steam_find(self, name: str):
        """리더보드 핸들 확보(비동기). 없으면 무시."""
        if not self._steam:
            return
        try:
            self._steam.UserStats.FindOrCreateLeaderboard(
                name.encode(), 1, 1,  # k_ELeaderboardSortMethodDescending, DisplayType Numeric
                self._on_find_result)
        except Exception:
            pass

    def _on_find_result(self, result):
        try:
            name = getattr(result, 'leaderboardName', b'')
            name = name.decode() if isinstance(name, bytes) else str(name)
            handle = getattr(result, 'leaderboardHandle', None) or getattr(result, 'handle', None)
            if name in LEADERBOARDS and handle:
                self._handles[name] = handle
        except Exception:
            pass

    def _steam_upload(self, name: str, score: int):
        if not self._steam:
            return
        try:
            handle = self._handles.get(name)
            if handle is None:
                return
            # k_ELeaderboardUploadScoreMethodKeepBest = 1
            self._steam.UserStats.UploadLeaderboardScore(handle, 1, int(score), [], 0)
        except Exception:
            pass

    def _steam_download(self, name: str, mode: str, count: int):
        if not self._steam:
            return
        try:
            handle = self._handles.get(name)
            if handle is None:
                return
            # k_ELeaderboardDataRequest: Global=0, GlobalAroundUser=1, Friends=2
            req = {'global': 0, 'around': 1, 'friends': 2}.get(mode, 0)
            lo, hi = (1, count) if req != 1 else (-count // 2, count // 2)
            self._steam.UserStats.DownloadLeaderboardEntries(
                handle, req, lo, hi, self._make_dl_cb(name, mode))
        except Exception:
            pass

    def _make_dl_cb(self, name: str, mode: str):
        def _cb(entries):
            try:
                rows = []
                for i, e in enumerate(entries or []):
                    nm = getattr(e, 'name', None) or getattr(e, 'steamIDUser', '')
                    if isinstance(nm, bytes):
                        nm = nm.decode(errors='replace')
                    rows.append({'rank': int(getattr(e, 'globalRank', i + 1)),
                                 'name': str(nm),
                                 'score': int(getattr(e, 'score', 0)),
                                 'me': bool(getattr(e, 'me', False))})
                self.cache[(name, mode)] = rows
            except Exception:
                pass
        return _cb

"""대체 레이아웃 아키타입 — 던전 골격 자체를 층마다 다르게.

기존 생성기는 '직사각형 방 + L통로' 한 종류(트리)뿐이라 구조가 늘 비슷했다.
여기서는 층/테마/난수로 아래 4종 중 하나를 골라 `dungeon.tiles`를 파고
`rooms`(Room 리스트)를 돌려준다. 문/상점/해저드/바이옴/금고/제단/배치 등
하위 시스템은 전부 `rooms` + FLOOR 위에서 동작하므로 그대로 호환된다.

  rooms   : 흩뿌린 사각방 + L통로 (기존, 트리)
  cavern  : 셀룰러 오토마타 유기적 동굴 (넓고 굽이침)
  arena   : 중앙 대형 투기장 + 위성방 (보스러시 느낌)
  hall    : 대회랑을 따라 늘어선 방들 (선형 갤러리)

공통 계약:
  · rooms[0] = 시작방, rooms[-1] = 출구/보스방
  · 모든 방 중앙이 rooms[0]에서 도달 가능(_ensure_connected로 보정)
"""
import random
from collections import deque
from map.tile import Tile, TileType


def build_layout(dungeon, floor_level):
    """이 층의 레이아웃을 골라 생성. (rooms, layout_name) 반환."""
    name = _pick_layout(floor_level, dungeon.theme_index)
    builder = {
        'rooms':  _layout_rooms,
        'cavern': _layout_cavern,
        'arena':  _layout_arena,
        'hall':   _layout_hall,
    }[name]
    rooms = builder(dungeon, floor_level)
    # 안전장치: 방이 너무 적으면 기본 방 배치로 폴백
    if len(rooms) < 2:
        rooms = _layout_rooms(dungeon, floor_level)
        name = 'rooms'
    _ensure_connected(dungeon, rooms)
    # 루프 연결: 트리형(rooms/cavern)에 추가 통로로 순환을 만들어 퇴로·카이팅 확보
    if name in ('rooms', 'cavern'):
        _add_loops(dungeon, rooms, max(1, len(rooms) // 4))
    elif name == 'hall':
        _add_loops(dungeon, rooms, 1)
    dungeon.layout = name
    return rooms, name


def _add_loops(dungeon, rooms, n):
    """서로 가까운 두 방을 추가로 이어 순환(loop)을 만든다.
    맵을 가로지르는 긴 통로는 피하려고 거리 상한을 둔다."""
    _, _, _connect_rooms, _, _ = _shared()
    if len(rooms) < 3:
        return
    max_d2 = (dungeon.width * 0.42) ** 2
    made = 0
    for _ in range(n * 4):
        if made >= n:
            break
        a, b = random.sample(rooms, 2)
        d2 = (a.center[0] - b.center[0]) ** 2 + (a.center[1] - b.center[1]) ** 2
        if 0 < d2 <= max_d2:
            _connect_rooms(dungeon, a.center, b.center)
            made += 1


def _pick_layout(floor_level, theme_idx):
    """층/테마 기반 가중 선택. 1~2층은 튜토리얼이라 기본 방."""
    if floor_level <= 2:
        return 'rooms'
    # 테마 성향: 자연=동굴↑, 기계/고성=회랑↑, 그 외 고른 분포
    w = {'rooms': 4, 'cavern': 3, 'arena': 2, 'hall': 2}
    if theme_idx in (1, 5, 11, 3):        # 늪/숲/곤충/마그마 → 동굴 성향
        w['cavern'] += 4
    if theme_idx in (2, 4, 6, 7, 10):     # 고성/기계/사원/요새/회로 → 회랑 성향
        w['hall'] += 3
    if theme_idx in (9, 16, 18):          # 심해/성소/무덤 → 투기장 성향
        w['arena'] += 3
    names = list(w); weights = [w[n] for n in names]
    return random.choices(names, weights=weights)[0]


# ── 공용 헬퍼 (generator에서 지연 임포트로 재사용) ──────────────────────
def _shared():
    from map.generator import Room, _carve_room, _connect_rooms, _h_tunnel, _v_tunnel
    return Room, _carve_room, _connect_rooms, _h_tunnel, _v_tunnel


def _walkable_reach(dungeon, start):
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + ox, y + oy
            if ((nx, ny) not in seen and dungeon.in_bounds(nx, ny)
                    and not dungeon.tiles[ny][nx].blocked):
                seen.add((nx, ny))
                q.append((nx, ny))
    return seen


def _ensure_connected(dungeon, rooms):
    """어떤 방 중앙이라도 rooms[0]에서 도달 불가면 가장 가까운
    도달 가능 방으로 통로를 뚫어 연결(고립 제거)."""
    _, _, _connect_rooms, _, _ = _shared()
    if not rooms:
        return
    for _ in range(len(rooms)):
        reach = _walkable_reach(dungeon, rooms[0].center)
        bad = [r for r in rooms if r.center not in reach]
        if not bad:
            return
        r = bad[0]
        # 도달 가능한 방 중 가장 가까운 것과 연결
        good = [rr for rr in rooms if rr.center in reach]
        if not good:
            return
        tgt = min(good, key=lambda g: (g.center[0] - r.center[0]) ** 2
                                      + (g.center[1] - r.center[1]) ** 2)
        _connect_rooms(dungeon, r.center, tgt.center)


# ── 1) rooms : 기존 방+통로 ────────────────────────────────────────────
def _layout_rooms(dungeon, floor_level):
    Room, _carve_room, _connect_rooms, _, _ = _shared()
    rooms = []
    W, H = dungeon.width, dungeon.height
    cap = min(18, 12 + floor_level)
    for _ in range(200):
        if len(rooms) >= cap:
            break
        w = random.randint(5, 12); h = random.randint(5, 12)
        x = random.randint(1, W - w - 2); y = random.randint(1, H - h - 2)
        r = Room(x, y, w, h)
        if any(r.intersects(e) for e in rooms):
            continue
        _carve_room(dungeon, r)
        if rooms:
            _connect_rooms(dungeon, rooms[-1].center, r.center)
        rooms.append(r)
    return rooms


# ── 2) cavern : 셀룰러 오토마타 동굴 ───────────────────────────────────
def _layout_cavern(dungeon, floor_level):
    Room, _carve_room, _connect_rooms, _, _ = _shared()
    W, H = dungeon.width, dungeon.height
    # 초기 무작위 채움(가장자리는 벽)
    grid = [[(random.random() < 0.45) for _ in range(W)] for _ in range(H)]
    for y in range(H):
        grid[y][0] = grid[y][W - 1] = True
    for x in range(W):
        grid[0][x] = grid[H - 1][x] = True

    def wall_count(cx, cy):
        c = 0
        for oy in (-1, 0, 1):
            for ox in (-1, 0, 1):
                if ox == 0 and oy == 0:
                    continue
                nx, ny = cx + ox, cy + oy
                if not (0 <= nx < W and 0 <= ny < H) or grid[ny][nx]:
                    c += 1
        return c

    for _ in range(5):                     # 평활화 반복
        ng = [row[:] for row in grid]
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                ng[y][x] = wall_count(x, y) >= 5
        grid = ng

    # tiles에 반영 (열린 칸=floor)
    for y in range(H):
        for x in range(W):
            dungeon.tiles[y][x] = Tile.wall() if grid[y][x] else Tile.floor()

    # 챔버 앵커 — 넓게 흩뿌린 방 마커 + 강제 개방으로 배치 공간 확보
    cap = min(16, 9 + floor_level // 2)
    rooms = []
    tries = 0
    while len(rooms) < cap and tries < 400:
        tries += 1
        rw = random.randint(3, 5); rh = random.randint(3, 5)
        x = random.randint(2, W - rw - 2); y = random.randint(2, H - rh - 2)
        r = Room(x, y, rw, rh)
        if any(r.intersects(e, pad=2) for e in rooms):
            continue
        _carve_room(dungeon, r)            # 앵커 주변은 확실히 열어둠
        if rooms:
            _connect_rooms(dungeon, rooms[-1].center, r.center)  # 굽이진 통로 보장
        rooms.append(r)
    return rooms


# ── 3) arena : 중앙 대형 투기장 + 위성방 ──────────────────────────────
def _layout_arena(dungeon, floor_level):
    Room, _carve_room, _connect_rooms, _, _ = _shared()
    W, H = dungeon.width, dungeon.height
    # 중앙 투기장
    aw, ah = int(W * random.uniform(0.42, 0.52)), int(H * random.uniform(0.42, 0.52))
    ax, ay = (W - aw) // 2, (H - ah) // 2
    arena = Room(ax, ay, aw, ah)
    _carve_room(dungeon, arena)
    # 위성방 — 가장자리 링에 배치
    sats = []
    cap = min(10, 5 + floor_level // 4)
    tries = 0
    while len(sats) < cap and tries < 300:
        tries += 1
        sw = random.randint(4, 7); sh = random.randint(4, 7)
        x = random.randint(1, W - sw - 2); y = random.randint(1, H - sh - 2)
        r = Room(x, y, sw, sh)
        if r.intersects(arena, pad=2) or any(r.intersects(s, pad=1) for s in sats):
            continue
        _carve_room(dungeon, r)
        _connect_rooms(dungeon, r.center, arena.center)   # 전부 투기장과 연결
        sats.append(r)
    if not sats:
        return [arena]
    # 순서: 시작 위성 → (나머지 위성 + 투기장) → 출구 위성
    start = sats[0]
    exit_room = sats[-1] if len(sats) > 1 else arena
    middle = sats[1:-1] + [arena]
    return [start] + middle + [exit_room]


# ── 4) hall : 대회랑 + 측면 방들 ───────────────────────────────────────
def _layout_hall(dungeon, floor_level):
    Room, _carve_room, _connect_rooms, _h_tunnel, _v_tunnel = _shared()
    W, H = dungeon.width, dungeon.height
    horizontal = random.random() < 0.5
    rooms = []
    if horizontal:
        hy = H // 2
        # 3칸 두께 대회랑
        for yy in (hy - 1, hy, hy + 1):
            _h_tunnel(dungeon, 2, W - 3, yy)
        n = min(10, 5 + floor_level // 4)
        xs = [int(2 + (W - 6) * (i + 0.5) / n) for i in range(n)]
        for i, cxp in enumerate(xs):
            above = (i % 2 == 0)
            rw = random.randint(5, 9); rh = random.randint(4, 7)
            rx = min(max(1, cxp - rw // 2), W - rw - 2)
            ry = (hy - 3 - rh) if above else (hy + 4)
            ry = min(max(1, ry), H - rh - 2)
            r = Room(rx, ry, rw, rh)
            _carve_room(dungeon, r)
            _v_tunnel(dungeon, r.center[1], hy, r.center[0])   # 회랑에 연결
            rooms.append(r)
    else:
        hx = W // 2
        for xx in (hx - 1, hx, hx + 1):
            _v_tunnel(dungeon, 2, H - 3, xx)
        n = min(10, 5 + floor_level // 4)
        ys = [int(2 + (H - 6) * (i + 0.5) / n) for i in range(n)]
        for i, cyp in enumerate(ys):
            left = (i % 2 == 0)
            rw = random.randint(4, 7); rh = random.randint(5, 9)
            ry = min(max(1, cyp - rh // 2), H - rh - 2)
            rx = (hx - 3 - rw) if left else (hx + 4)
            rx = min(max(1, rx), W - rw - 2)
            r = Room(rx, ry, rw, rh)
            _carve_room(dungeon, r)
            _h_tunnel(dungeon, r.center[0], hx, r.center[1])
            rooms.append(r)
    return rooms

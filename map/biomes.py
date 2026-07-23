"""바이옴 지형 변주 — 방+통로 골격 위에 '지형 특징'을 덧입혀
   999층이 전부 똑같은 던전으로 느껴지지 않게 한다.

설계 원칙:
  · 기존 생성(방/통로)·해저드·제단·배치 시스템을 건드리지 않는 '오버레이 패스'.
  · 모든 변경은 연결성 가드(_stamp_guarded)로 감싸 시작→출구/각 방이
    항상 도달 가능하도록 보장(소프트락 방지).
  · 새 타일은 WATER(호수/늪)뿐. 나무·기둥·성벽은 테마색 WALL 재사용.

theme_index → 바이옴:
  1 늪지대   swamp   (물웅덩이 + 통로)
  2 고성     fortress(성벽 홀 + 기둥열)
  4 기계무덤 fortress
  5 보랏빛숲 forest  (나무 군락 + 작은 연못)
  6 사원     fortress
  7 절벽요새 fortress
  9 심해도시 lake    (큰 호수)
  11 곤충군집 forest (빽빽한 나무)
  13 실험실  lake    (작은 시약 웅덩이)
"""
import random
from collections import deque
from map.tile import Tile, TileType


BIOME_BY_THEME = {
    1: 'swamp',   2: 'fortress', 4: 'fortress', 5: 'forest',
    6: 'fortress', 7: 'fortress', 9: 'lake',    11: 'forest',
    13: 'lake',
}


def biome_for(theme_idx: int) -> str:
    return BIOME_BY_THEME.get(theme_idx, 'default')


def apply_biome(dungeon, rooms, floor_level, theme_idx):
    """이 층 테마에 맞는 지형 변주를 적용(연결성 보장). 반환값 없음."""
    biome = biome_for(theme_idx)
    if biome == 'default' or len(rooms) < 3:
        return
    if biome == 'fortress':
        _fortress(dungeon, rooms)
    elif biome == 'forest':
        _forest(dungeon, rooms, dense=(theme_idx == 11))
    elif biome == 'swamp':
        _water_rooms(dungeon, rooms, big=False, count=2)
    elif biome == 'lake':
        _water_rooms(dungeon, rooms, big=True, count=1)


# ── 연결성 가드 ────────────────────────────────────────────────────────
def _reachable(dungeon, start):
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


def _point_targets(dungeon):
    """반드시 도달 가능해야 하는 확정 지점 — 출구/보스방."""
    ts = []
    ex = getattr(dungeon, 'stairs_pos', None)
    if ex:
        ts.append(ex)
    bp = getattr(dungeon, 'boss_room_pos', None)
    if bp:
        ts.append(bp)
    return ts


def _room_has_reach(room, reach):
    """방 영역에 도달 가능한 바닥칸이 하나라도 있는지."""
    for yy in range(room.y, room.y + room.h):
        for xx in range(room.x, room.x + room.w):
            if (xx, yy) in reach:
                return True
    return False


def _stamp_guarded(dungeon, rooms, changes):
    """changes=[(x,y,new_tile)] 를 적용하되, 아래가 깨지면 전체 롤백:
      · 출구/보스방 도달 가능
      · 모든 방이 도달 가능한 바닥칸을 최소 1개 유지
    지형이 방 중앙을 덮어도(호수 등) 방에 남은 통로가 있으면 허용."""
    if not changes:
        return False
    start = rooms[0].center
    if dungeon.tiles[start[1]][start[0]].blocked:
        return False                       # 시작칸을 막는 변경은 즉시 거부
    saved = [(x, y, dungeon.tiles[y][x]) for x, y, _ in changes]
    for x, y, nt in changes:
        dungeon.tiles[y][x] = nt
    reach = _reachable(dungeon, start)
    ok = all(t in reach for t in _point_targets(dungeon)) \
        and all(_room_has_reach(r, reach) for r in rooms)
    if not ok:
        for x, y, ot in saved:
            dungeon.tiles[y][x] = ot
        return False
    return True


def _interior_floor(dungeon, room, margin=1):
    """방 내부(테두리 margin 제외)의 FLOOR 좌표들."""
    out = []
    for yy in range(room.y + margin, room.y + room.h - margin):
        for xx in range(room.x + margin, room.x + room.w - margin):
            if (dungeon.in_bounds(xx, yy)
                    and dungeon.tiles[yy][xx].tile_type == TileType.FLOOR):
                out.append((xx, yy))
    return out


# ── 호수/늪 (WATER) ────────────────────────────────────────────────────
def _water_rooms(dungeon, rooms, big, count):
    """중간 방 몇 개의 내부에 물웅덩이(블롭)를 앉힌다. 테두리는 남겨
    통행로 확보 + 연결성 가드로 안전."""
    cands = [r for r in rooms[1:-1] if r.w >= 6 and r.h >= 5]
    random.shuffle(cands)
    done = 0
    for room in cands:
        if done >= count:
            break
        cells = _interior_floor(dungeon, room, margin=2 if big else 1)
        if len(cells) < 4:
            continue
        # 블롭: 임의 시드에서 자라는 물웅덩이
        seed = random.choice(cells)
        cellset = set(cells)
        blob = _grow_blob(seed, cellset,
                          size=int(len(cells) * (0.6 if big else 0.4)))
        changes = [(x, y, Tile.water()) for (x, y) in blob]
        if _stamp_guarded(dungeon, rooms, changes):
            done += 1


def _grow_blob(seed, allowed, size):
    """allowed 좌표 안에서 seed로부터 size칸까지 자라는 유기적 블롭."""
    blob = {seed}
    frontier = [seed]
    while frontier and len(blob) < size:
        x, y = frontier.pop(random.randrange(len(frontier)))
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + ox, y + oy)
            if n in allowed and n not in blob and random.random() < 0.7:
                blob.add(n)
                frontier.append(n)
    return blob


# ── 요새 (기둥열 + 분할 성벽) ──────────────────────────────────────────
def _fortress(dungeon, rooms):
    """큰 방에 규칙적 기둥열/분할 벽을 세워 '홀·요새' 느낌.
    WALL 재사용(테마색). 연결성 가드로 안전."""
    for room in rooms[1:-1]:
        if room.w < 7 or room.h < 7:
            continue
        changes = []
        if random.random() < 0.6:
            # 기둥 격자 — 2칸 간격
            for yy in range(room.y + 2, room.y + room.h - 2, 3):
                for xx in range(room.x + 2, room.x + room.w - 2, 3):
                    if dungeon.tiles[yy][xx].tile_type == TileType.FLOOR:
                        changes.append((xx, yy, Tile.wall()))
        else:
            # 중앙 분할 성벽 + 통과구(gap)
            cx = room.x + room.w // 2
            gap = random.randint(room.y + 2, room.y + room.h - 3)
            for yy in range(room.y + 1, room.y + room.h - 1):
                if yy == gap or yy == gap + 1:
                    continue
                if dungeon.tiles[yy][cx].tile_type == TileType.FLOOR:
                    changes.append((cx, yy, Tile.wall()))
        _stamp_guarded(dungeon, rooms, changes)


# ── 숲 (나무 군락 + 작은 연못) ─────────────────────────────────────────
def _forest(dungeon, rooms, dense):
    """방 안에 나무(WALL) 군락을 흩뿌려 은폐·미로 느낌 + 선택적 연못.
    나무는 서로 붙지 않게 흩어 통행 여지를 남기고 연결성 가드로 보장."""
    for room in rooms[1:-1]:
        cells = _interior_floor(dungeon, room, margin=1)
        if len(cells) < 6:
            continue
        random.shuffle(cells)
        ratio = 0.28 if dense else 0.16
        n = int(len(cells) * ratio)
        placed = 0
        occupied = set()
        changes = []
        for (x, y) in cells:
            if placed >= n:
                break
            # 이미 인접에 나무가 있으면 건너뜀(빽빽하지 않은 산개)
            if any((x + dx, y + dy) in occupied
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                continue
            changes.append((x, y, Tile.wall()))
            occupied.add((x, y))
            placed += 1
        _stamp_guarded(dungeon, rooms, changes)
    # 숲에는 작은 연못 하나
    _water_rooms(dungeon, rooms, big=False, count=1)

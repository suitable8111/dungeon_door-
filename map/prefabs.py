"""프리팹 세트피스 — 손으로 짠 특수방을 기존 방 하나에 덧씌운다.

절차 생성 방들 사이에 가끔 '눈에 띄는 방' 하나를 넣어 기억에 남게 한다.
모든 변형은 연결성 가드(biomes._stamp_guarded)로 감싸 소프트락을 막는다.

  arena  : 원형 투기장 — 모서리를 벽으로 깎아 둥근 전투 챔버
  pillars: 기둥 십자홀 — 대칭 기둥 격자(엄폐물), 십자 통로 개방
  moat   : 해자 보물방 — 물 해자 + 중앙 섬(보물) + 십자 다리
"""
import random
from map.tile import Tile, TileType
from map.biomes import _stamp_guarded


def place_prefab(dungeon, rooms, floor_level, item_data):
    """이 층에 프리팹 1개를 확률적으로 주입. 성공 시 프리팹명 반환/실패 None."""
    if len(rooms) < 4 or random.random() >= 0.5:
        return None
    # 시작/출구 방은 건드리지 않음
    cands = [r for r in rooms[1:-1] if r.w >= 6 and r.h >= 6]
    random.shuffle(cands)
    kinds = ['arena', 'pillars', 'moat']
    random.shuffle(kinds)
    for room in cands:
        for kind in kinds:
            fn = {'arena': _arena, 'pillars': _pillars, 'moat': _moat}[kind]
            if fn(dungeon, rooms, room, floor_level, item_data):
                dungeon.prefab = kind
                dungeon.prefab_pos = room.center
                return kind
    return None


def _interior(room, margin=0):
    return [(x, y)
            for y in range(room.y + margin, room.y + room.h - margin)
            for x in range(room.x + margin, room.x + room.w - margin)]


# ── 원형 투기장 — 모서리를 깎아 둥글게 ─────────────────────────────────
def _arena(dungeon, rooms, room, floor_level, item_data):
    cx = room.x + (room.w - 1) / 2.0
    cy = room.y + (room.h - 1) / 2.0
    rad = min(room.w, room.h) / 2.0
    changes = []
    for (x, y) in _interior(room):
        # 반지름 밖 → 벽(둥근 윤곽)
        if ((x - cx) / (room.w / 2.0)) ** 2 + ((y - cy) / (room.h / 2.0)) ** 2 > 1.02:
            if dungeon.tiles[y][x].tile_type == TileType.FLOOR:
                changes.append((x, y, Tile.wall()))
    # 중앙 대칭 기둥 4개(엄폐)
    for dx, dy in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        px, py = int(round(cx)) + dx, int(round(cy)) + dy
        if dungeon.in_bounds(px, py) and dungeon.tiles[py][px].tile_type == TileType.FLOOR:
            changes.append((px, py, Tile.wall()))
    return _stamp_guarded(dungeon, rooms, changes)


# ── 기둥 십자홀 — 대칭 기둥 격자 + 십자 통로 ──────────────────────────
def _pillars(dungeon, rooms, room, floor_level, item_data):
    cx = room.x + room.w // 2
    cy = room.y + room.h // 2
    changes = []
    for (x, y) in _interior(room, margin=1):
        # 십자 통로(중앙 가로/세로 줄)는 개방
        if x == cx or y == cy:
            continue
        # 격자 기둥 — 2칸 간격
        if (x - room.x) % 2 == 0 and (y - room.y) % 2 == 0:
            if dungeon.tiles[y][x].tile_type == TileType.FLOOR:
                changes.append((x, y, Tile.wall()))
    if len(changes) < 3:
        return False
    return _stamp_guarded(dungeon, rooms, changes)


# ── 해자 보물방 — 물 해자 + 중앙 섬(보물) + 십자 다리 ─────────────────
def _moat(dungeon, rooms, room, floor_level, item_data):
    from entities.item import Item
    from map.generator import drop_pool
    cx = room.x + room.w // 2
    cy = room.y + room.h // 2
    changes = []
    island = []
    for (x, y) in _interior(room, margin=1):
        ex = min(x - room.x, room.x + room.w - 1 - x)
        ey = min(y - room.y, room.y + room.h - 1 - y)
        edge = min(ex, ey)
        cdist = max(abs(x - cx), abs(y - cy))
        if cdist <= 1:
            island.append((x, y))
            continue                          # 중앙 섬(바닥) 유지
        if x == cx or y == cy:
            continue                          # 십자 다리(바닥) 유지
        if edge >= 1:
            if dungeon.tiles[y][x].tile_type == TileType.FLOOR:
                changes.append((x, y, Tile.water()))
    if len(changes) < 4 or not island:
        return False
    if not _stamp_guarded(dungeon, rooms, changes):
        return False
    # 십자 다리 확정 — 섬↔가장자리 통로를 바닥으로 강제(물에 덮이지 않게)
    for (x, y) in _interior(room, margin=1):
        if x == cx or y == cy:
            if dungeon.tiles[y][x].tile_type == TileType.WATER:
                dungeon.tiles[y][x] = Tile.floor()
    # 섬 보물 — 좋은 장비 2~3 + 강화석
    keys = [k for k in drop_pool(floor_level)
            if k in item_data and k not in ('health_potion', 'enhance_stone')]
    loot = random.sample(keys, min(len(keys), random.randint(2, 3))) if keys else []
    loot += ['enhance_stone']
    random.shuffle(island)
    for (ix, iy), key in zip(island, loot):
        d = dict(item_data[key]); d['key'] = key
        if d.get('type') in ('weapon', 'armor'):
            d['enhance_level'] = min(15, floor_level // 45)
        dungeon.items.append(Item(ix, iy, d))
    return True

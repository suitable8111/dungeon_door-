import random
from map.tile import Tile, TileType
from map.dungeon import Dungeon
from map.theme import theme_index, theme_fx, MAX_FLOOR


class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersects(self, other, pad=1):
        return (self.x - pad <= other.x + other.w and
                self.x + self.w + pad >= other.x and
                self.y - pad <= other.y + other.h and
                self.y + self.h + pad >= other.y)


def _place_burning_door(dungeon, room):
    cx, cy = room.center
    candidates = [
        (cx,           room.y - 1),
        (cx,           room.y + room.h),
        (room.x - 1,   cy),
        (room.x + room.w, cy),
    ]
    random.shuffle(candidates)
    for wx, wy in candidates:
        if dungeon.in_bounds(wx, wy) and dungeon.tiles[wy][wx].tile_type == TileType.WALL:
            dungeon.tiles[wy][wx] = Tile.burning_door()
            dungeon.burning_door_pos = (wx, wy)
            return


def _place_door(dungeon, room):
    cx, cy = room.center
    candidates = [
        (cx,           room.y - 1),
        (cx,           room.y + room.h),
        (room.x - 1,   cy),
        (room.x + room.w, cy),
    ]
    random.shuffle(candidates)
    for wx, wy in candidates:
        if dungeon.in_bounds(wx, wy) and dungeon.tiles[wy][wx].tile_type == TileType.WALL:
            dungeon.tiles[wy][wx] = Tile.door()
            dungeon.stairs_pos = (wx, wy)
            return
    dungeon.tiles[cy][cx] = Tile.door()
    dungeon.stairs_pos = (cx, cy)


def generate_dungeon(width, height, floor_level, enemy_data, item_data):
    floor_level = min(floor_level, MAX_FLOOR)
    dungeon = Dungeon(width, height)
    dungeon.theme_index = theme_index(floor_level)
    rooms = []

    attempts = 200
    min_sz, max_sz = 5, 12

    for _ in range(attempts):
        if len(rooms) >= 12 + floor_level:
            break
        w = random.randint(min_sz, max_sz)
        h = random.randint(min_sz, max_sz)
        x = random.randint(1, width - w - 2)
        y = random.randint(1, height - h - 2)
        r = Room(x, y, w, h)
        if any(r.intersects(existing) for existing in rooms):
            continue
        _carve_room(dungeon, r)
        if rooms:
            _connect_rooms(dungeon, rooms[-1].center, r.center)
        rooms.append(r)

    dungeon.rooms = rooms

    is_boss_floor = (floor_level % 5 == 0)
    is_shop_floor = (floor_level % 3 == 0 and not is_boss_floor)

    if is_boss_floor:
        dungeon.is_boss_floor = True
        boss_cx, boss_cy = rooms[-1].center
        dungeon.boss_room_pos = (boss_cx, boss_cy)
    else:
        _place_door(dungeon, rooms[-1])
        # 버닝 스테이지 문: 50층 이상, 상점층 아님, 30% 확률
        if (floor_level >= 50 and not is_shop_floor and
                random.random() < 0.05 and len(rooms) >= 3):
            mid_room = rooms[len(rooms) // 3]
            _place_burning_door(dungeon, mid_room)

    if is_shop_floor and len(rooms) >= 3:
        shop_room = rooms[len(rooms) // 2]
        scx, scy = shop_room.center
        dungeon.tiles[scy][scx] = Tile.shop()
        dungeon.has_shop = True
        dungeon.shop_items = _make_shop_items(floor_level, item_data)

    # 흐르는 바닥(컨베이어) — 기계/전기 테마 층
    if theme_fx(floor_level).get('conveyor') and len(rooms) >= 3:
        _place_conveyors(dungeon, rooms)

    # 동적 위험: 트랩 + 압력판(모든 층) + 움직이는 벽(shift 테마)
    if not is_boss_floor:
        _place_hazards(dungeon, rooms, floor_level)

    # 균열 벽: 숨겨진 보물방 + 비밀 지름길 (폭탄/강타로 개방)
    if not is_boss_floor:
        _place_secret_areas(dungeon, rooms, floor_level, item_data)

    _populate(dungeon, rooms, floor_level, enemy_data, is_boss_floor)

    return dungeon, rooms[0].center


def _place_conveyors(dungeon, rooms):
    """일부 방에 가로 컨베이어 띠를 깐다 (시작방 제외, 방향 교대)."""
    # 시작방/마지막(보스·문)방은 제외
    candidates = rooms[1:-1] or rooms[1:]
    random.shuffle(candidates)
    direction = 1
    for room in candidates[:max(1, len(candidates) // 2)]:
        ry = room.y + room.h // 2                 # 방 중앙 가로줄
        for rx in range(room.x, room.x + room.w):
            if dungeon.in_bounds(rx, ry) and \
                    dungeon.tiles[ry][rx].tile_type == TileType.FLOOR:
                dungeon.tiles[ry][rx] = Tile.conveyor(direction)
        direction *= -1                            # 방마다 방향 교대


def _place_hazards(dungeon, rooms, floor_level):
    """골목(통로) 중심의 패턴형 위험 배치.

    · 통로에 '주기 가시'와 '이동벽 게이트' — 넓은 방과 달리 우회 불가,
      플레이어가 개폐/발동 패턴을 파악해 타이밍으로 돌파해야 한다.
    · 넓은 방에는 거미줄/저주(회피 가능) + 압력판(보상).
    · shift 테마 층은 방 하나를 '파도 관문'으로 추가 구성.
    · 움직이는 벽은 모든 비-보스 층에 등장(얕은 층은 게이트 수만 적음).
    """
    if len(rooms) < 2:
        return
    interior = set()
    for r in rooms:
        for yy in range(r.y, r.y + r.h):
            for xx in range(r.x, r.x + r.w):
                interior.add((xx, yy))
    protected = set()
    for r in (rooms[0], rooms[-1]):                 # 시작/마지막 방 + 넉넉한 여백
        for yy in range(r.y - 2, r.y + r.h + 2):
            for xx in range(r.x - 2, r.x + r.w + 2):
                protected.add((xx, yy))

    def is_floor(x, y):
        return (dungeon.in_bounds(x, y)
                and dungeon.tiles[y][x].tile_type == TileType.FLOOR)

    def phase_of(x, y):                             # 위치 기반 위상 → 연속 위험이 파도를 이룸
        return (x * 0.13 + y * 0.17) % 1.0

    # 골목 타일 = 방 밖 바닥(통로)
    corridor = [(x, y) for (x, y) in (
                    (xx, yy) for yy in range(dungeon.height)
                    for xx in range(dungeon.width))
                if is_floor(x, y) and (x, y) not in interior and (x, y) not in protected]
    random.shuffle(corridor)
    used = set()

    # 1) 골목 주기 가시 (패턴 타이밍 돌파)
    n_spike = min(16, 5 + floor_level // 25)
    placed = 0
    for x, y in corridor:
        if placed >= n_spike:
            break
        if (x, y) in used:
            continue
        dungeon.tiles[y][x] = Tile.trap(TileType.SPIKE_TRAP, phase_of(x, y))
        used.add((x, y)); placed += 1

    # 2) 골목 이동벽 게이트 (모든 층, 서로 붙지 않게)
    n_gate = min(10, 3 + floor_level // 40)
    placed = 0
    for x, y in corridor:
        if placed >= n_gate:
            break
        if (x, y) in used:
            continue
        if any((x + dx, y + dy) in used for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        dungeon.tiles[y][x] = Tile.shift_wall(phase_of(x, y))
        used.add((x, y)); placed += 1

    # 3) 넓은 방: 거미줄/저주(회피 가능) + 압력판
    room_spots = [(x, y) for r in (rooms[1:-1] or rooms[1:])
                  for y in range(r.y, r.y + r.h) for x in range(r.x, r.x + r.w)
                  if is_floor(x, y) and (x, y) not in protected and (x, y) not in used]
    random.shuffle(room_spots)
    n_room = min(8, 2 + floor_level // 50)
    for x, y in room_spots[:n_room]:
        dungeon.tiles[y][x] = Tile.trap(random.choice((TileType.WEB_TRAP,
                                                       TileType.CURSE_TRAP)))
        used.add((x, y))
    for x, y in room_spots[n_room:n_room + random.randint(1, 2)]:
        if (x, y) not in used:
            dungeon.tiles[y][x] = Tile.button(); used.add((x, y))

    # 4) shift 테마: 방 하나를 파도 관문으로
    if theme_fx(floor_level).get('shift'):
        _place_barrier_room(dungeon, rooms, protected, is_floor)


def _place_barrier_room(dungeon, rooms, protected, is_floor):
    """방을 세로 기둥열로 채워 파도식 관문 — 열들이 시차로 열려 틈이 이동한다."""
    cands = [r for r in (rooms[1:-1] or rooms[1:]) if r.w >= 7 and r.h >= 4]
    if not cands:
        return
    r = random.choice(cands)
    for ci, cx in enumerate(range(r.x + 1, r.x + r.w - 1, 2)):
        ph = (ci * 0.24) % 1.0                       # 열마다 위상 시차 → 파도
        for yy in range(r.y + 1, r.y + r.h - 1):
            if is_floor(cx, yy) and (cx, yy) not in protected:
                dungeon.tiles[yy][cx] = Tile.shift_wall(ph)
                protected.add((cx, yy))


def _place_secret_areas(dungeon, rooms, floor_level, item_data):
    """균열 벽으로 봉인된 숨겨진 보물방 + 비밀 지름길 생성."""
    if len(rooms) >= 3 and random.random() < 0.72:
        _try_secret_room(dungeon, rooms, floor_level, item_data)
    _place_shortcut_cracks(dungeon, rooms, floor_level)


def _try_secret_room(dungeon, rooms, floor_level, item_data):
    """기존 방 옆 빈 벽 공간에 고립된 3×3 금고를 파고, 입구 벽 1칸을 균열 벽으로."""
    from entities.item import Item
    sw = sh = 3

    def all_wall(x0, y0, x1, y1):
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                if not dungeon.in_bounds(xx, yy):
                    return False
                if dungeon.tiles[yy][xx].tile_type != TileType.WALL:
                    return False
        return True

    for base in random.sample(rooms, len(rooms)):
        for dx, dy in random.sample([(1, 0), (-1, 0), (0, 1), (0, -1)], 4):
            if dx > 0:   sx, sy = base.x + base.w + 1, base.y
            elif dx < 0: sx, sy = base.x - 1 - sw,     base.y
            elif dy > 0: sx, sy = base.x, base.y + base.h + 1
            else:        sx, sy = base.x, base.y - 1 - sh
            # 금고 영역 + 1칸 테두리가 전부 빈 벽이어야 (고립 보장)
            if not all_wall(sx - 1, sy - 1, sx + sw + 1, sy + sh + 1):
                continue
            s = Room(sx, sy, sw, sh)
            _carve_room(dungeon, s)
            rooms.append(s)
            # 균열 벽 입구 — base 바닥과 금고 바닥을 잇는 벽 1칸
            if dx != 0:
                gx = base.x + base.w if dx > 0 else base.x - 1
                gy = sy + 1
            else:
                gx = sx + 1
                gy = base.y + base.h if dy > 0 else base.y - 1
            if dungeon.in_bounds(gx, gy):
                dungeon.tiles[gy][gx] = Tile.cracked_wall()
            # 보물 — 좋은 아이템 2~3 + 폭탄
            keys = [k for k in drop_pool(floor_level)
                    if k in item_data and k != 'health_potion']
            spots = [(x, y) for y in range(s.y, s.y + s.h)
                     for x in range(s.x, s.x + s.w)]
            random.shuffle(spots)
            loot = random.sample(keys, min(len(keys), random.randint(2, 3)))
            if 'bomb' in item_data:
                loot.append('bomb')
            for (ix, iy), key in zip(spots, loot):
                d = dict(item_data[key]); d['key'] = key
                dungeon.items.append(Item(ix, iy, d))
            dungeon.secret_room = s.center
            return True
    return False


def _place_shortcut_cracks(dungeon, rooms, floor_level):
    """두 통로/방을 가르는 1칸 벽을 균열 벽으로 — 폭탄으로 뚫는 지름길."""
    n_target = random.randint(1, 2)
    placed = 0
    tries = 0
    W, H = dungeon.width, dungeon.height
    while placed < n_target and tries < 400:
        tries += 1
        x = random.randint(2, W - 3)
        y = random.randint(2, H - 3)
        t = dungeon.tiles[y][x]
        if t.tile_type != TileType.WALL:
            continue
        # 반대편이 모두 바닥인 얇은 벽 (수평 또는 수직)
        def fl(xx, yy):
            return (dungeon.in_bounds(xx, yy)
                    and dungeon.tiles[yy][xx].tile_type == TileType.FLOOR)
        if (fl(x - 1, y) and fl(x + 1, y)) or (fl(x, y - 1) and fl(x, y + 1)):
            dungeon.tiles[y][x] = Tile.cracked_wall()
            placed += 1


def _carve_room(dungeon, room):
    for ry in range(room.y, room.y + room.h):
        for rx in range(room.x, room.x + room.w):
            dungeon.tiles[ry][rx] = Tile.floor()


def _connect_rooms(dungeon, a, b):
    ax, ay = a
    bx, by = b
    if random.random() < 0.5:
        _h_tunnel(dungeon, ax, bx, ay)
        _v_tunnel(dungeon, ay, by, bx)
    else:
        _v_tunnel(dungeon, ay, by, ax)
        _h_tunnel(dungeon, ax, bx, by)


def _h_tunnel(dungeon, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        dungeon.tiles[y][x] = Tile.floor()


def _v_tunnel(dungeon, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        dungeon.tiles[y][x] = Tile.floor()


def _scale_enemy(data, floor_level):
    """층수에 따라 적 능력치를 스케일링한 복사본 반환.

    방어력은 완만하게(0.55배율) 올린다 — 뺄셈 데미지 공식에서
    방어력이 HP와 같은 속도로 오르면 깊은 층에서 '1딜 벽'이 생긴다.
    """
    scale = 1.0 + (floor_level - 1) ** 0.65 * 0.12
    def_scale = 1.0 + (scale - 1.0) * 0.55
    d = dict(data)
    d['hp']       = max(1, int(d['hp']     * scale))
    d['attack']   = max(1, int(d['attack'] * scale))
    d['defense']  = max(0, int(d.get('defense', 0) * def_scale))
    d['xp']       = max(1, int(d['xp']     * scale))
    d['gold_drop']= max(0, int(d.get('gold_drop', 0) * scale))
    return d


def maybe_make_elite(d, floor_level, force=None):
    """4층부터 확률적으로 적을 엘리트 변종으로 승격 (스케일된 dict에 적용)."""
    from entities.enemy import ELITE_AFFIXES, ELITE_XP_MUL, ELITE_GOLD_MUL
    chance = min(0.15, 0.05 + floor_level * 0.002)
    if force is None and (floor_level < 4 or random.random() >= chance):
        return d
    affix = force if force in ELITE_AFFIXES else random.choice(list(ELITE_AFFIXES))
    a = ELITE_AFFIXES[affix]
    d['elite']     = affix
    d['hp']        = max(1, int(d['hp'] * a['hp']))
    d['attack']    = max(1, int(d['attack'] * a['atk']))
    d['defense']   = int(d.get('defense', 0) * a['df']) + a['df_add']
    d['move_ms']   = max(200, int(d.get('move_ms', 900) * a['move']))
    d['attack_ms'] = max(400, int(d.get('attack_ms', 1500) * a['atkspd']))
    d['xp']        = int(d['xp'] * ELITE_XP_MUL)
    d['gold_drop'] = int(d.get('gold_drop', 0) * ELITE_GOLD_MUL)
    return d


def _populate(dungeon, rooms, floor_level, enemy_data, is_boss_floor):
    from entities.enemy import Enemy

    enemy_pool = _enemy_pool(floor_level, dungeon.theme_index)

    pop_rooms = rooms[1:]
    if is_boss_floor and pop_rooms:
        boss_rooms = pop_rooms[:-1]
        boss_room  = pop_rooms[-1]
    else:
        boss_rooms = pop_rooms
        boss_room  = None

    for room in boss_rooms:
        used = set()
        # 3층부터는 빈 방이 나오지 않게 최소 1마리 보장
        lo = 0 if floor_level <= 2 else 1
        count = random.randint(lo, min(4, 1 + floor_level // 3))
        for _ in range(count):
            ex = random.randint(room.x + 1, room.x + room.w - 2)
            ey = random.randint(room.y + 1, room.y + room.h - 2)
            if (ex, ey) not in used:
                used.add((ex, ey))
                key = random.choice(enemy_pool)
                data = _scale_enemy(enemy_data[key], floor_level)
                data['key'] = key
                data = maybe_make_elite(data, floor_level)
                dungeon.enemies.append(Enemy(ex, ey, data))

    if boss_room is not None:
        theme_idx = getattr(dungeon, 'theme_index', 0)
        boss_candidates = _BOSS_POOLS[min(theme_idx, len(_BOSS_POOLS) - 1)]
        boss_key = boss_candidates[(floor_level // 5) % len(boss_candidates)]
        if boss_key not in enemy_data:
            boss_key = boss_candidates[0]
        bdata = _scale_enemy(enemy_data[boss_key], floor_level)
        bdata['key']     = boss_key
        bdata['is_boss'] = True
        bcx, bcy = boss_room.center
        boss = Enemy(bcx, bcy, bdata)
        dungeon.enemies.append(boss)
        dungeon.boss = boss
        guards = _enemy_pool(floor_level, theme_idx)
        for _ in range(2):
            gx = random.randint(boss_room.x+1, boss_room.x+boss_room.w-2)
            gy = random.randint(boss_room.y+1, boss_room.y+boss_room.h-2)
            if (gx, gy) != (bcx, bcy):
                gkey = random.choice(guards)
                gdata = _scale_enemy(enemy_data[gkey], floor_level)
                gdata['key'] = gkey
                dungeon.enemies.append(Enemy(gx, gy, gdata))


def _make_shop_items(floor_level, item_data):
    from entities.item import Item
    # 골드 수입 스케일(1 + (f-1)^0.65 * 0.12)보다 완만한 가격 상승(0.07) —
    # 층이 깊어질수록 상점 이용이 상대적으로 수월해져 진행 보상이 된다
    mul = 1.0 + (floor_level - 1) ** 0.65 * 0.07
    prices = {
        'health_potion':       int(15  * mul),
        'large_health_potion': int(35  * mul),
        'dagger':              int(60  * mul),
        'sword':               int(120 * mul),
        'broad_sword':         int(220 * mul),
        'great_sword':         int(380 * mul),
        'leather_armor':       int(50  * mul),
        'chain_mail':          int(100 * mul),
        'plate_armor':         int(180 * mul),
        'mythril_armor':       int(320 * mul),
        'leather_helm':        int(45  * mul),
        'iron_helm':           int(90  * mul),
        'knight_helm':         int(170 * mul),
        'wooden_shield':       int(45  * mul),
        'iron_shield':         int(100 * mul),
        'tower_shield':        int(190 * mul),
        'silver_ring':         int(80  * mul),
        'war_pendant':         int(110 * mul),
        'magic_stone':         int(200 * mul),
        'teleport_scroll':     int(40  * mul),
        'amulet':              int(90  * mul),
        'whirlwind_potion':    int(60  * mul),
        'return_scroll':       int(30  * mul),
        'repair_kit':          int(45  * mul),
        'bomb':                int(35  * mul),
    }
    if floor_level <= 3:
        keys = ['health_potion', 'dagger', 'leather_armor', 'bomb', 'leather_helm', 'wooden_shield', 'return_scroll', 'repair_kit']
    elif floor_level <= 8:
        keys = ['large_health_potion', 'sword', 'bomb', 'chain_mail', 'iron_helm',
                'iron_shield', 'silver_ring', 'teleport_scroll', 'return_scroll', 'repair_kit']
    elif floor_level <= 20:
        keys = ['large_health_potion', 'sword', 'bomb', 'plate_armor', 'iron_helm',
                'iron_shield', 'war_pendant', 'amulet', 'whirlwind_potion', 'return_scroll', 'repair_kit']
    elif floor_level <= 50:
        keys = ['large_health_potion', 'broad_sword', 'bomb', 'plate_armor', 'knight_helm',
                'tower_shield', 'war_pendant', 'magic_stone', 'whirlwind_potion', 'return_scroll', 'repair_kit']
    else:
        keys = ['large_health_potion', 'great_sword', 'bomb', 'mythril_armor', 'knight_helm',
                'tower_shield', 'magic_stone', 'amulet', 'teleport_scroll', 'whirlwind_potion', 'return_scroll', 'repair_kit']

    result = []
    for key in keys[:5]:
        if key not in item_data:
            continue
        d = dict(item_data[key])
        d['key'] = key
        result.append((Item(0, 0, d), prices.get(key, 50)))
    return result


def drop_pool(floor_level):
    """몬스터 처치 시 드랍 아이템 풀 (게임에서 호출)."""
    stones = ['enhance_stone'] * 2
    if floor_level <= 4:
        return (['health_potion'] * 3 + ['dagger'] + ['leather_armor'] +
                ['leather_helm'] + ['wooden_shield'] + ['silver_ring'] +
                ['leather_boots'] + stones + ['bomb'])
    elif floor_level <= 10:
        return (['health_potion'] * 2 + ['large_health_potion'] + ['dagger'] +
                ['sword'] + ['chain_mail'] + ['leather_helm'] + ['iron_helm'] +
                ['wooden_shield'] + ['silver_ring'] + ['teleport_scroll'] +
                ['leather_boots'] + ['iron_boots'] + stones * 2 + ['bomb'])
    elif floor_level <= 25:
        return (['large_health_potion'] * 2 + ['sword'] * 2 + ['chain_mail'] +
                ['plate_armor'] + ['iron_helm'] + ['iron_shield'] +
                ['silver_ring'] + ['war_pendant'] + ['teleport_scroll'] +
                ['skillbook_wind'] + ['skillbook_fireball'] +
                ['iron_boots'] + stones * 2 + ['bomb'])
    elif floor_level <= 50:
        return (['large_health_potion'] * 2 + ['broad_sword'] + ['plate_armor'] +
                ['knight_helm'] + ['iron_shield'] + ['tower_shield'] +
                ['war_pendant'] + ['magic_stone'] + ['amulet'] +
                ['skillbook_fireball'] + ['skillbook_frost'] + ['skillbook_thunder'] +
                ['iron_boots'] + ['swift_boots'] + stones * 3 + ['bomb'])
    else:
        return (['large_health_potion'] * 2 + ['great_sword'] + ['mythril_armor'] +
                ['knight_helm'] + ['tower_shield'] + ['magic_stone'] * 2 +
                ['war_pendant'] + ['amulet'] + ['whirlwind_potion'] +
                ['skillbook_frost'] + ['skillbook_thunder'] +
                ['swift_boots'] + ['shadow_boots'] + stones * 3 + ['bomb'])


# 테마별 몬스터 풀 (theme_index 0-19)
_THEME_POOLS = [
    # 0: 버려진 지하 감옥 (01-50F) — 층수 직접 처리
    None,
    # 1: 곰팡이 핀 늪지대 (51-100F) — 독성/습지 생물
    ['zombie'] * 2 + ['ghoul'] * 2 + ['corpse_flower'] * 2 + ['prisoner'] * 2 + ['jar_crawler'] + ['slime'],
    # 2: 서리 내린 정적의 고성 (101-150F) — 언데드 기사단
    ['blade_skeleton'] * 2 + ['shield_skeleton'] * 2 + ['archer_skeleton'] * 2 + ['spear_skeleton'] * 2 + ['skeleton'] * 2,
    # 3: 타오르는 마그마 굴 (151-200F) — 강인한 석조/불 생물
    ['rock_golem'] * 3 + ['iron_cage'] * 3 + ['chain_beast'] * 2 + ['orc'] * 2,
    # 4: 기계 장치의 무덤 (201-250F) — 철제 구조물 적
    ['iron_cage'] * 3 + ['chain_beast'] * 3 + ['rock_golem'] * 2 + ['shield_skeleton'] * 2,
    # 5: 환각의 보랏빛 숲 (251-300F) — 마법/환술사
    ['illusionist'] * 3 + ['curse_mage'] * 3 + ['bone_wizard'] * 2 + ['poison_sprite'] * 2,
    # 6: 몰락한 성기사의 사원 (301-350F) — 집행관 잔당
    ['executioner_nov'] * 2 + ['brand_man'] * 2 + ['whip_master'] * 2 + ['torturer'] * 2 + ['spear_skeleton'] * 2,
    # 7: 바람 부는 절벽 요새 (351-400F) — 요새 병사/도적
    ['bandit'] * 2 + ['thief'] * 2 + ['ambusher'] * 2 + ['shadow_stalker'] * 2 + ['assassin'] * 2,
    # 8: 저주받은 도서관 (401-450F) — 저주 마법사
    ['bone_wizard'] * 3 + ['curse_mage'] * 3 + ['illusionist'] * 2 + ['specter'] * 2,
    # 9: 심해의 가라앉은 도시 (451-500F) — 심해 언데드
    ['zombie'] * 2 + ['soul_absorber'] * 3 + ['ghost'] * 2 + ['specter'] * 2 + ['blood_bat'],
    # 10: 전기 회로의 미로 (501-550F) — 강화 기계/구조물
    ['steel_knight'] * 3 + ['iron_cage'] * 2 + ['rock_golem'] * 2 + ['mimic'] * 2 + ['chain_beast'],
    # 11: 거대 곤충의 군집 (551-600F) — 거대 절지류
    ['giant_spider'] * 4 + ['blood_bat'] * 2 + ['centipede'] * 2 + ['corpse_flower'] * 2,
    # 12: 황량한 붉은 사막 (601-650F) — 사막 약탈자
    ['bandit'] * 2 + ['assassin'] * 2 + ['ambusher'] * 2 + ['shadow_stalker'] * 2 + ['thief'] * 2,
    # 13: 연금술사의 실험실 (651-700F) — 돌연변이 실험체
    ['curse_mage'] * 2 + ['poison_sprite'] * 3 + ['soul_absorber'] * 2 + ['mimic'] * 2 + ['illusionist'],
    # 14: 천공의 무너진 섬 (701-750F) — 공중 마법 존재
    ['blood_bat'] * 2 + ['ghost'] * 2 + ['specter'] * 2 + ['death_mage'] * 2 + ['illusionist'] * 2,
    # 15: 그림자의 영역 (751-800F) — 암흑 존재
    ['shadow_stalker'] * 3 + ['assassin'] * 2 + ['specter'] * 2 + ['soul_absorber'] * 2 + ['ambusher'],
    # 16: 핏빛 달의 성소 (801-850F) — 흡혈/거대 전사
    ['blood_bat'] * 2 + ['ghoul'] * 2 + ['giant_zombie'] * 2 + ['grave_titan'] * 2 + ['assassin'] * 2,
    # 17: 왜곡된 시공간의 틈 (851-900F) — 차원 술사
    ['specter'] * 2 + ['death_mage'] * 3 + ['soul_absorber'] * 2 + ['bone_wizard'] * 2 + ['grave_titan'],
    # 18: 고대 신의 무덤 (901-950F) — 고대 거인/언데드
    ['grave_titan'] * 3 + ['giant_zombie'] * 2 + ['steel_knight'] * 2 + ['death_mage'] * 3,
    # 19: 차원의 끝 (951-999F) — 최종 혼돈
    ['grave_titan'] * 2 + ['death_mage'] * 2 + ['soul_absorber'] * 2 + ['giant_spider'] + ['blood_bat'] + ['assassin'] + ['mimic'],
]

# 테마별 보스 후보 (5층마다 보스전)
_BOSS_POOLS = [
    # 0: 지하 감옥 1-50F
    ['dark_knight', 'lich'],
    # 1: 늪지대 51-100F
    ['giant_zombie', 'giant_spider'],
    # 2: 고성 101-150F
    ['steel_knight', 'death_mage'],
    # 3: 마그마 굴 151-200F
    ['grave_titan', 'steel_knight'],
    # 4: 기계 무덤 201-250F
    ['grave_titan', 'mimic'],
    # 5: 보랏빛 숲 251-300F
    ['death_mage', 'mimic'],
    # 6: 성기사 사원 301-350F
    ['jail_captain', 'stomp_exec'],
    # 7: 절벽 요새 351-400F
    ['jail_captain', 'mace_knight'],
    # 8: 저주 도서관 401-450F
    ['mace_knight', 'death_mage'],
    # 9: 심해 도시 451-500F
    ['soul_absorber', 'grave_titan'],
    # 10: 전기 미로 501-550F
    ['stomp_exec', 'grave_titan'],
    # 11: 곤충 군집 551-600F
    ['giant_spider', 'blood_bat'],
    # 12: 붉은 사막 601-650F
    ['mace_knight', 'stomp_exec'],
    # 13: 연금술 실험실 651-700F
    ['mimic', 'death_mage'],
    # 14: 천공 섬 701-750F
    ['death_mage', 'grave_titan'],
    # 15: 그림자 영역 751-800F
    ['dark_knight', 'soul_absorber'],
    # 16: 핏빛 성소 801-850F
    ['grave_titan', 'giant_zombie'],
    # 17: 시공간의 틈 851-900F
    ['lich', 'death_mage'],
    # 18: 고대 신의 무덤 901-950F
    ['lich', 'grave_titan'],
    # 19: 차원의 끝 951-999F
    ['dark_knight', 'lich'],
]


def _enemy_pool(floor_level, theme_idx=0):
    # 테마 0 (01-50F): 층수 세분화로 튜토리얼 난이도
    if theme_idx == 0:
        if floor_level <= 2:
            return ['rat'] * 3 + ['bat'] * 2 + ['centipede']
        elif floor_level <= 5:
            return ['rat'] * 2 + ['bat'] * 2 + ['centipede'] * 2 + ['spider']
        elif floor_level <= 10:
            return ['centipede'] * 2 + ['spider'] * 2 + ['slime'] * 2 + ['blade_skeleton']
        elif floor_level <= 20:
            return ['blade_skeleton'] * 2 + ['shield_skeleton'] * 2 + ['skeleton'] * 2 + ['prisoner'] * 2
        elif floor_level <= 35:
            return ['skeleton'] * 2 + ['zombie'] * 2 + ['ghost'] + ['ghoul'] * 2 + ['chain_beast']
        else:
            return ['ghoul'] * 2 + ['chain_beast'] * 2 + ['iron_cage'] * 2 + ['rock_golem'] * 2 + ['chest_mimic']
    pool = _THEME_POOLS[min(theme_idx, len(_THEME_POOLS) - 1)]
    return list(pool) if pool else _THEME_POOLS[19]


def _item_pool(floor_level):
    if floor_level <= 2:
        return ['health_potion'] * 4 + ['dagger'] + ['leather_armor'] + ['leather_boots']
    elif floor_level <= 3:
        return (['health_potion'] * 2 + ['large_health_potion'] + ['dagger'] +
                ['sword'] + ['chain_mail'] + ['teleport_scroll'] + ['leather_boots'])
    elif floor_level <= 5:
        return (['health_potion'] * 2 + ['large_health_potion'] + ['dagger'] +
                ['sword'] + ['chain_mail'] + ['teleport_scroll'] + ['skillbook_wind'] +
                ['leather_boots'] + ['iron_boots'])
    elif floor_level <= 7:
        return (['large_health_potion'] * 2 + ['sword'] * 2 +
                ['plate_armor'] + ['teleport_scroll'] + ['amulet'] +
                ['whirlwind_potion'] + ['skillbook_wind'] + ['skillbook_fireball'] + ['skillbook_frost'] +
                ['iron_boots'])
    elif floor_level <= 50:
        return (['large_health_potion'] * 2 + ['sword'] * 2 +
                ['plate_armor'] + ['teleport_scroll'] + ['amulet'] +
                ['whirlwind_potion'] + ['skillbook_fireball'] + ['skillbook_frost'] + ['skillbook_thunder'] +
                ['iron_boots'] + ['swift_boots'])
    else:
        return (['large_health_potion'] * 3 + ['plate_armor'] +
                ['sword'] * 2 + ['amulet'] * 2 +
                ['teleport_scroll'] * 2 + ['whirlwind_potion'] +
                ['skillbook_fireball'] + ['skillbook_frost'] + ['skillbook_thunder'] +
                ['swift_boots'] + ['shadow_boots'])

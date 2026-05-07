import random
from map.tile import Tile, TileType
from map.dungeon import Dungeon
from map.theme import theme_index, MAX_FLOOR


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
        last_cx, last_cy = rooms[-1].center
        dungeon.tiles[last_cy][last_cx] = Tile.stairs_down()
        dungeon.stairs_pos = (last_cx, last_cy)

    if is_shop_floor and len(rooms) >= 3:
        shop_room = rooms[len(rooms) // 2]
        scx, scy = shop_room.center
        dungeon.tiles[scy][scx] = Tile.shop()
        dungeon.has_shop = True
        dungeon.shop_items = _make_shop_items(floor_level, item_data)

    _populate(dungeon, rooms, floor_level, enemy_data, is_boss_floor)

    return dungeon, rooms[0].center


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
    """층수에 따라 적 능력치를 스케일링한 복사본 반환."""
    scale = 1.0 + (floor_level - 1) ** 0.65 * 0.12
    d = dict(data)
    d['hp']     = max(1, int(d['hp']     * scale))
    d['attack'] = max(1, int(d['attack'] * scale))
    d['defense']= max(0, int(d.get('defense', 0) * scale))
    d['xp']     = max(1, int(d['xp']     * scale))
    d['gold']   = max(0, int(d.get('gold', 0) * scale))
    return d


def _populate(dungeon, rooms, floor_level, enemy_data, is_boss_floor):
    from entities.enemy import Enemy

    enemy_pool = _enemy_pool(floor_level)

    pop_rooms = rooms[1:]
    if is_boss_floor and pop_rooms:
        boss_rooms = pop_rooms[:-1]
        boss_room  = pop_rooms[-1]
    else:
        boss_rooms = pop_rooms
        boss_room  = None

    for room in boss_rooms:
        used = set()
        count = random.randint(0, min(4, 1 + floor_level // 3))
        for _ in range(count):
            ex = random.randint(room.x + 1, room.x + room.w - 2)
            ey = random.randint(room.y + 1, room.y + room.h - 2)
            if (ex, ey) not in used:
                used.add((ex, ey))
                key = random.choice(enemy_pool)
                data = _scale_enemy(enemy_data[key], floor_level)
                data['key'] = key
                dungeon.enemies.append(Enemy(ex, ey, data))

    if boss_room is not None:
        boss_key = 'lich' if (floor_level // 5) % 2 == 0 else 'dark_knight'
        bdata = _scale_enemy(enemy_data[boss_key], floor_level)
        bdata['key'] = boss_key
        bcx, bcy = boss_room.center
        boss = Enemy(bcx, bcy, bdata)
        dungeon.enemies.append(boss)
        dungeon.boss = boss
        guards = _enemy_pool(floor_level)
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
    tier = 1 + (floor_level - 1) // 50
    mul  = 1 + (tier - 1) * 0.4
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
    }
    if floor_level <= 3:
        keys = ['health_potion', 'dagger', 'leather_armor', 'leather_helm', 'wooden_shield']
    elif floor_level <= 8:
        keys = ['large_health_potion', 'sword', 'chain_mail', 'iron_helm',
                'iron_shield', 'silver_ring', 'teleport_scroll']
    elif floor_level <= 20:
        keys = ['large_health_potion', 'sword', 'plate_armor', 'iron_helm',
                'iron_shield', 'war_pendant', 'amulet', 'whirlwind_potion']
    elif floor_level <= 50:
        keys = ['large_health_potion', 'broad_sword', 'plate_armor', 'knight_helm',
                'tower_shield', 'war_pendant', 'magic_stone', 'whirlwind_potion']
    else:
        keys = ['large_health_potion', 'great_sword', 'mythril_armor', 'knight_helm',
                'tower_shield', 'magic_stone', 'amulet', 'teleport_scroll', 'whirlwind_potion']

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
    if floor_level <= 4:
        return (['health_potion'] * 3 + ['dagger'] + ['leather_armor'] +
                ['leather_helm'] + ['wooden_shield'] + ['silver_ring'])
    elif floor_level <= 10:
        return (['health_potion'] * 2 + ['large_health_potion'] + ['dagger'] +
                ['sword'] + ['chain_mail'] + ['leather_helm'] + ['iron_helm'] +
                ['wooden_shield'] + ['silver_ring'] + ['teleport_scroll'])
    elif floor_level <= 25:
        return (['large_health_potion'] * 2 + ['sword'] * 2 + ['chain_mail'] +
                ['plate_armor'] + ['iron_helm'] + ['iron_shield'] +
                ['silver_ring'] + ['war_pendant'] + ['teleport_scroll'] +
                ['skillbook_wind'] + ['skillbook_fireball'])
    elif floor_level <= 50:
        return (['large_health_potion'] * 2 + ['broad_sword'] + ['plate_armor'] +
                ['knight_helm'] + ['iron_shield'] + ['tower_shield'] +
                ['war_pendant'] + ['magic_stone'] + ['amulet'] +
                ['skillbook_fireball'] + ['skillbook_frost'] + ['skillbook_thunder'])
    else:
        return (['large_health_potion'] * 2 + ['great_sword'] + ['mythril_armor'] +
                ['knight_helm'] + ['tower_shield'] + ['magic_stone'] * 2 +
                ['war_pendant'] + ['amulet'] + ['whirlwind_potion'] +
                ['skillbook_frost'] + ['skillbook_thunder'])


def _enemy_pool(floor_level):
    if floor_level <= 2:
        return ['rat'] * 4 + ['goblin'] * 2
    elif floor_level <= 4:
        return ['rat'] * 2 + ['goblin'] * 3 + ['skeleton'] * 2 + ['wizard']
    elif floor_level <= 6:
        return ['goblin'] + ['skeleton'] * 3 + ['orc'] * 2 + ['wizard'] * 2
    elif floor_level <= 8:
        return ['skeleton'] * 2 + ['orc'] * 3 + ['troll'] * 2 + ['wizard'] * 2
    elif floor_level <= 15:
        return ['orc'] * 2 + ['troll'] * 3 + ['wizard'] * 2 + ['dragon']
    elif floor_level <= 30:
        return ['troll'] * 2 + ['wizard'] * 2 + ['dragon'] * 3 + ['orc']
    elif floor_level <= 50:
        return ['wizard'] * 2 + ['dragon'] * 3 + ['troll'] * 2
    elif floor_level <= 100:
        return ['dragon'] * 3 + ['wizard'] * 2 + ['troll']
    elif floor_level <= 200:
        return ['dragon'] * 3 + ['wizard'] * 3
    elif floor_level <= 400:
        return ['dragon'] * 4 + ['wizard'] * 2
    else:
        return ['dragon'] * 5 + ['wizard']


def _item_pool(floor_level):
    if floor_level <= 2:
        return ['health_potion'] * 4 + ['dagger'] + ['leather_armor']
    elif floor_level <= 3:
        return (['health_potion'] * 2 + ['large_health_potion'] + ['dagger'] +
                ['sword'] + ['chain_mail'] + ['teleport_scroll'])
    elif floor_level <= 5:
        return (['health_potion'] * 2 + ['large_health_potion'] + ['dagger'] +
                ['sword'] + ['chain_mail'] + ['teleport_scroll'] + ['skillbook_wind'])
    elif floor_level <= 7:
        return (['large_health_potion'] * 2 + ['sword'] * 2 +
                ['plate_armor'] + ['teleport_scroll'] + ['amulet'] +
                ['whirlwind_potion'] + ['skillbook_wind'] + ['skillbook_fireball'] + ['skillbook_frost'])
    elif floor_level <= 50:
        return (['large_health_potion'] * 2 + ['sword'] * 2 +
                ['plate_armor'] + ['teleport_scroll'] + ['amulet'] +
                ['whirlwind_potion'] + ['skillbook_fireball'] + ['skillbook_frost'] + ['skillbook_thunder'])
    else:
        # 50층 이상: 고급 아이템 위주 (포션 / 스크롤 / 장비 균형)
        return (['large_health_potion'] * 3 + ['plate_armor'] +
                ['sword'] * 2 + ['amulet'] * 2 +
                ['teleport_scroll'] * 2 + ['whirlwind_potion'] +
                ['skillbook_fireball'] + ['skillbook_frost'] + ['skillbook_thunder'])

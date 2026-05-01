import random
from map.tile import Tile, TileType
from map.dungeon import Dungeon


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
    dungeon = Dungeon(width, height)
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

    _populate(dungeon, rooms, floor_level, enemy_data, is_boss_floor, item_data)

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


def _populate(dungeon, rooms, floor_level, enemy_data, is_boss_floor, item_data=None):
    from entities.enemy import Enemy
    from entities.item import Item

    enemy_pool = _enemy_pool(floor_level)
    item_pool  = _item_pool(floor_level)

    pop_rooms = rooms[1:]
    if is_boss_floor and pop_rooms:
        boss_rooms = pop_rooms[:-1]
        boss_room  = pop_rooms[-1]
    else:
        boss_rooms = pop_rooms
        boss_room  = None

    for room in boss_rooms:
        used = set()
        count = random.randint(0, min(3, 1 + floor_level // 3))
        for _ in range(count):
            ex = random.randint(room.x + 1, room.x + room.w - 2)
            ey = random.randint(room.y + 1, room.y + room.h - 2)
            if (ex, ey) not in used:
                used.add((ex, ey))
                key = random.choice(enemy_pool)
                data = dict(enemy_data[key])
                data['key'] = key
                dungeon.enemies.append(Enemy(ex, ey, data))

        if item_data and random.random() < 0.35:
            ix = random.randint(room.x + 1, room.x + room.w - 2)
            iy = random.randint(room.y + 1, room.y + room.h - 2)
            if (ix, iy) not in used:
                key = random.choice(item_pool)
                if key in item_data:
                    data = dict(item_data[key])
                    data['key'] = key
                    dungeon.items.append(Item(ix, iy, data))

    if boss_room is not None:
        boss_key = 'lich' if (floor_level // 5) % 2 == 0 else 'dark_knight'
        bdata = dict(enemy_data[boss_key])
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
                gdata = dict(enemy_data[gkey])
                gdata['key'] = gkey
                dungeon.enemies.append(Enemy(gx, gy, gdata))


def _make_shop_items(floor_level, item_data):
    from entities.item import Item
    prices = {
        'health_potion': 15, 'large_health_potion': 35,
        'dagger': 60, 'sword': 120,
        'leather_armor': 50, 'chain_mail': 100, 'plate_armor': 180,
        'teleport_scroll': 40, 'amulet': 90, 'whirlwind_potion': 60,
    }
    if floor_level <= 3:
        keys = ['health_potion', 'large_health_potion', 'dagger', 'leather_armor']
    elif floor_level <= 6:
        keys = ['large_health_potion', 'dagger', 'sword', 'chain_mail', 'teleport_scroll']
    else:
        keys = ['large_health_potion', 'sword', 'plate_armor', 'amulet', 'whirlwind_potion']

    result = []
    for key in keys[:5]:
        if key not in item_data:
            continue
        d = dict(item_data[key])
        d['key'] = key
        result.append((Item(0, 0, d), prices.get(key, 50)))
    return result


def _enemy_pool(floor_level):
    if floor_level <= 2:
        return ['rat'] * 4 + ['goblin'] * 2
    elif floor_level <= 4:
        return ['rat'] * 2 + ['goblin'] * 3 + ['skeleton'] * 2 + ['wizard']
    elif floor_level <= 6:
        return ['goblin'] + ['skeleton'] * 3 + ['orc'] * 2 + ['wizard'] * 2
    elif floor_level <= 8:
        return ['skeleton'] * 2 + ['orc'] * 3 + ['troll'] * 2 + ['wizard'] * 2
    else:
        return ['orc'] * 2 + ['troll'] * 3 + ['wizard'] * 2 + ['dragon']


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
    else:
        return (['large_health_potion'] * 2 + ['sword'] * 2 +
                ['plate_armor'] + ['teleport_scroll'] + ['amulet'] +
                ['whirlwind_potion'] + ['skillbook_fireball'] + ['skillbook_frost'] + ['skillbook_thunder'])

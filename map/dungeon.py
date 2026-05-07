from map.tile import Tile


class Dungeon:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[Tile.wall() for _ in range(width)] for _ in range(height)]
        self.rooms = []
        self.enemies = []
        self.items = []
        self.stairs_pos = None

        # Phase 3: 보스 / 상점
        self.is_boss_floor  = False
        self.boss           = None      # 보스 Enemy 참조
        self.boss_room_pos  = None      # 보스 처치 후 계단 위치
        self.shop_items     = []        # [(Item, price), ...]
        self.has_shop       = False

        # 테마 인덱스 (50층마다 변경)
        self.theme_index = 0

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and not self.tiles[y][x].blocked

    def get_enemy_at(self, x, y):
        for e in self.enemies:
            if e.is_alive() and e.x == x and e.y == y:
                return e
        return None

    def get_item_at(self, x, y):
        for item in self.items:
            if item.x == x and item.y == y:
                return item
        return None

    def remove_item(self, item):
        self.items.remove(item)

    def update_visibility(self, px, py, radius=7):
        for row in self.tiles:
            for t in row:
                t.visible = False
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = px + dx, py + dy
                if not self.in_bounds(nx, ny):
                    continue
                if dx * dx + dy * dy <= radius * radius:
                    if self._has_los(px, py, nx, ny):
                        self.tiles[ny][nx].visible = True
                        self.tiles[ny][nx].explored = True

    def _has_los(self, x0, y0, x1, y1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        cx, cy = x0, y0
        while True:
            if cx == x1 and cy == y1:
                return True
            if (cx != x0 or cy != y0) and self.tiles[cy][cx].block_sight:
                return False
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy

import random
from entities.entity import Entity


class Enemy(Entity):
    def __init__(self, x, y, data):
        super().__init__(
            x, y,
            data['name'],
            data['hp'], data['hp'],
            data['attack'], data['defense'],
        )
        self.key          = data.get('key', 'rat')
        self.color        = tuple(data['color'])
        self.xp_value     = data['xp']
        self.gold_drop    = data.get('gold_drop', random.randint(1, 5))
        self.is_boss      = data.get('is_boss', False)
        self.move_ms      = data.get('move_ms',   900)
        self.attack_ms    = data.get('attack_ms', 1500)
        self.attack_range = data.get('attack_range', 1)

        self._move_t   = random.uniform(0, self.move_ms)
        self._attack_t = random.uniform(0, self.attack_ms)

    # ------------------------------------------------------------------ #
    def update(self, dt_ms, dungeon, player, messages):
        dist = abs(player.x - self.x) + abs(player.y - self.y)
        aware_range = 20 if self.is_boss else 14
        if dist > aware_range:
            return

        self._move_t   -= dt_ms
        self._attack_t -= dt_ms

        in_range = dist <= self.attack_range
        has_los  = (self.attack_range <= 1) or dungeon._has_los(self.x, self.y, player.x, player.y)

        if in_range and has_los:
            if self._attack_t <= 0:
                self._do_attack(player, messages)
                self._attack_t = self.attack_ms
        else:
            if self._move_t <= 0:
                chase_range = 18 if self.is_boss else 10
                # 원거리 유닛은 적정 거리 유지 시도
                if dist <= chase_range:
                    if dist > max(1, self.attack_range - 1):
                        self._move_toward(player.x, player.y, dungeon, player)
                elif random.random() < 0.35:
                    self._move_random(dungeon, player)
                self._move_t = self.move_ms

    # ------------------------------------------------------------------ #
    def _do_attack(self, player, messages):
        dmg = max(1, self.attack - player.defense + random.randint(0, 2))
        player.take_damage(dmg)
        messages.append((f"{self.name}이(가) {dmg} 피해를 입혔습니다!", 'bad'))

    def _move_toward(self, tx, ty, dungeon, player):
        dx, dy = tx - self.x, ty - self.y
        steps = []
        if abs(dx) >= abs(dy):
            if dx: steps.append((1 if dx > 0 else -1, 0))
            if dy: steps.append((0, 1 if dy > 0 else -1))
        else:
            if dy: steps.append((0, 1 if dy > 0 else -1))
            if dx: steps.append((1 if dx > 0 else -1, 0))
        self._try_steps(steps, dungeon, player)

    def _move_random(self, dungeon, player):
        dirs = [(0,1),(0,-1),(1,0),(-1,0)]
        random.shuffle(dirs)
        self._try_steps(dirs, dungeon, player)

    def _try_steps(self, steps, dungeon, player):
        for sdx, sdy in steps:
            nx, ny = self.x + sdx, self.y + sdy
            if (dungeon.is_walkable(nx, ny) and
                    not dungeon.get_enemy_at(nx, ny) and
                    (nx, ny) != (player.x, player.y)):
                self.x, self.y = nx, ny
                break

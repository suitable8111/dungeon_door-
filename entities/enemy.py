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
        self.aware_range  = data.get('aware_range',  20 if data.get('is_boss') else 14)
        self.chase_range  = data.get('chase_range',  18 if data.get('is_boss') else 10)

        self.boss_skills  = data.get('boss_skills', [])
        self._skill_cd_ms = data.get('skill_cd_ms', 5000)
        self._skill_t     = random.uniform(3000, 6000)

        self.staggered_ms = 0

        self._move_t   = random.uniform(0, self.move_ms)
        self._attack_t = random.uniform(0, self.attack_ms)

    # ------------------------------------------------------------------ #
    def update(self, dt_ms, dungeon, player, messages):
        dist = abs(player.x - self.x) + abs(player.y - self.y)
        if dist > self.aware_range:
            return None

        if self.staggered_ms > 0:
            self.staggered_ms = max(0, self.staggered_ms - dt_ms)
            return None

        self._move_t   -= dt_ms
        self._attack_t -= dt_ms

        # 보스 스킬 쿨다운
        boss_result = None
        if self.is_boss and self.boss_skills:
            self._skill_t -= dt_ms
            if self._skill_t <= 0:
                boss_result = self._do_boss_skill(dungeon, player, messages)
                self._skill_t = self._skill_cd_ms + random.randint(-1000, 1500)

        in_range = dist <= self.attack_range
        has_los  = (self.attack_range <= 1) or dungeon._has_los(self.x, self.y, player.x, player.y)

        if in_range and has_los:
            if self._attack_t <= 0:
                self._do_attack(player, messages)
                self._attack_t = self.attack_ms
        else:
            if self._move_t <= 0:
                if dist <= self.chase_range:
                    if dist > max(1, self.attack_range - 1):
                        self._move_toward(player.x, player.y, dungeon, player)
                elif random.random() < 0.35:
                    self._move_random(dungeon, player)
                self._move_t = self.move_ms

        return boss_result

    # ------------------------------------------------------------------ #
    def _do_boss_skill(self, dungeon, player, messages):
        skill = random.choice(self.boss_skills)
        if skill == 'charge':
            return self._skill_charge(dungeon, player, messages)
        elif skill == 'whirlwind':
            return self._skill_whirlwind(player, messages)
        elif skill == 'death_nova':
            return self._skill_death_nova(player, messages)
        elif skill == 'summon_undead':
            return self._skill_summon_undead(messages)
        elif skill == 'curse':
            return self._skill_curse(player, messages)
        elif skill == 'slow':
            return self._skill_slow(player, messages)
        elif skill == 'fear':
            return self._skill_fear(player, messages)
        return None

    def _skill_charge(self, dungeon, player, messages):
        px, py = player.x, player.y
        for _ in range(2):
            dx, dy = px - self.x, py - self.y
            if abs(dx) + abs(dy) <= 1:
                break
            step_x = (1 if dx > 0 else -1) if abs(dx) >= abs(dy) else 0
            step_y = (1 if dy > 0 else -1) if abs(dy) > abs(dx) else 0
            nx, ny = self.x + step_x, self.y + step_y
            if (dungeon.is_walkable(nx, ny) and
                    not dungeon.get_enemy_at(nx, ny) and
                    (nx, ny) != (px, py)):
                self.x, self.y = nx, ny
        if abs(px - self.x) + abs(py - self.y) <= 1:
            if random.random() < player.evasion / 100:
                messages.append((f"{self.name}의 돌진을 회피했습니다!", 'good'))
            else:
                dmg = max(1, int(self.attack * 1.7) - player.total_defense + random.randint(0, 3))
                player.take_damage(dmg)
                messages.append((f"{self.name}이(가) 돌진 강타! {dmg} 피해!", 'bad'))
        else:
            messages.append((f"{self.name}이(가) 돌진합니다!", 'warn'))
        return {'skill': 'charge', 'ex': self.x, 'ey': self.y}

    def _skill_whirlwind(self, player, messages):
        dist = abs(player.x - self.x) + abs(player.y - self.y)
        if dist <= 3:
            if random.random() < player.evasion / 100:
                messages.append((f"{self.name}의 회전베기를 회피했습니다!", 'good'))
            else:
                dmg = max(1, int(self.attack * 1.3) - player.total_defense + random.randint(0, 2))
                player.take_damage(dmg)
                messages.append((f"{self.name}이(가) 회전베기! {dmg} 피해!", 'bad'))
        else:
            messages.append((f"{self.name}이(가) 회전베기를 사용했습니다!", 'warn'))
        return {'skill': 'whirlwind', 'ex': self.x, 'ey': self.y}

    def _skill_death_nova(self, player, messages):
        dist = abs(player.x - self.x) + abs(player.y - self.y)
        if dist <= 5:
            if random.random() < player.evasion / 100:
                messages.append((f"{self.name}의 죽음의 파동을 회피했습니다!", 'good'))
            else:
                dmg = max(1, int(self.attack * 1.4) - player.total_defense + random.randint(0, 3))
                player.take_damage(dmg)
                messages.append((f"{self.name}이(가) 죽음의 파동! {dmg} 피해!", 'bad'))
        else:
            messages.append((f"{self.name}이(가) 죽음의 파동을 시전했습니다!", 'warn'))
        return {'skill': 'death_nova', 'ex': self.x, 'ey': self.y}

    def _skill_summon_undead(self, messages):
        messages.append((f"{self.name}이(가) 언데드를 소환했습니다!", 'warn'))
        return {'skill': 'summon_undead', 'ex': self.x, 'ey': self.y, 'spawn_key': 'skeleton'}

    def _skill_curse(self, player, messages):
        player.cursed_ms = 8000
        messages.append((f"{self.name}이(가) 저주를 걸었습니다! 받는 피해 50% 증가", 'bad'))
        return {'skill': 'curse', 'ex': self.x, 'ey': self.y}

    def _skill_slow(self, player, messages):
        player.slowed_ms = 7000
        messages.append((f"{self.name}이(가) 슬로우를 걸었습니다! 이동속도 감소", 'bad'))
        return {'skill': 'slow', 'ex': self.x, 'ey': self.y}

    def _skill_fear(self, player, messages):
        player.feared_ms = 6000
        messages.append((f"{self.name}이(가) 두려움을 심었습니다! 명중률 40%로 저하", 'bad'))
        return {'skill': 'fear', 'ex': self.x, 'ey': self.y}

    # ------------------------------------------------------------------ #
    def _do_attack(self, player, messages):
        # 회피 판정
        if random.random() < player.evasion / 100:
            messages.append((f"{self.name}의 공격을 회피했습니다!", 'good'))
            return
        dmg = max(1, self.attack - player.total_defense + random.randint(0, 2))
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

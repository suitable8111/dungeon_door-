import random
from entities.entity import Entity
from core.combat import roll_damage
from core.constants import TILE_SIZE
from core.lang import t


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
        self.hurt_ms      = 0     # 피격 흰 플래시 잔여 시간
        self.windup_ms    = 0     # 공격 전조(텔레그래프) 잔여 시간
        self.anim_ox      = 0.0   # 렌더 오프셋(px) — 타일 이동 슬라이드/넉백
        self.anim_oy      = 0.0

        self._move_t   = random.uniform(0, self.move_ms)
        self._attack_t = random.uniform(0, self.attack_ms)

    # 공격 전조 시간: 빠른 적일수록 짧게, 원거리는 길게
    @property
    def _windup_total(self) -> int:
        base = 400 if self.attack_range > 1 else 280
        return min(base, int(self.attack_ms * 0.3))

    def _slide_from(self, old_x, old_y):
        """타일 이동 직후 호출 — 이전 위치에서 미끄러져 오는 렌더 오프셋."""
        self.anim_ox += (old_x - self.x) * TILE_SIZE
        self.anim_oy += (old_y - self.y) * TILE_SIZE

    def take_damage(self, amount: int):
        """피격 시 흰 플래시 + 짧은 경직 + 공격 전조 취소 (모든 데미지 공통)."""
        super().take_damage(amount)
        self.hurt_ms = 140
        self.staggered_ms = max(self.staggered_ms, 90)
        self.windup_ms = 0

    def on_hurt(self, from_x, from_y):
        """방향이 있는 피격(근접 등): 공격자 반대편으로 넉백."""
        kdx = 0 if self.x == from_x else (1 if self.x > from_x else -1)
        kdy = 0 if self.y == from_y else (1 if self.y > from_y else -1)
        self.anim_ox += kdx * 7
        self.anim_oy += kdy * 7

    # ------------------------------------------------------------------ #
    def update(self, dt_ms, dungeon, player, messages):
        # 렌더 오프셋 감쇠 (시야 밖/경직 중에도 항상)
        if self.anim_ox or self.anim_oy:
            factor = 0.975 ** dt_ms
            self.anim_ox *= factor
            self.anim_oy *= factor
            if abs(self.anim_ox) < 0.5: self.anim_ox = 0.0
            if abs(self.anim_oy) < 0.5: self.anim_oy = 0.0
        if self.hurt_ms > 0:
            self.hurt_ms = max(0, self.hurt_ms - dt_ms)

        dist = abs(player.x - self.x) + abs(player.y - self.y)
        if dist > self.aware_range:
            self.windup_ms = 0
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

        # 전조 진행 중: 시간이 다 되면 타격 (플레이어가 벗어났으면 헛침)
        if self.windup_ms > 0:
            self.windup_ms -= dt_ms
            if self.windup_ms <= 0:
                self.windup_ms = 0
                self._attack_t = self.attack_ms
                if in_range and has_los:
                    # 런지: 플레이어 쪽으로 튀어나갔다 제자리로
                    ldx = player.x - self.x
                    ldy = player.y - self.y
                    mag = max(1, abs(ldx) + abs(ldy))
                    self.anim_ox += ldx / mag * TILE_SIZE * 0.45
                    self.anim_oy += ldy / mag * TILE_SIZE * 0.45
                    self._do_attack(player, messages)
                else:
                    messages.append((t('enemy_whiff', self.name), 'good'))
            return boss_result

        if in_range and has_los:
            if self._attack_t <= 0:
                self.windup_ms = self._windup_total  # 공격 전조 시작
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
                ox, oy = self.x, self.y
                self.x, self.y = nx, ny
                self._slide_from(ox, oy)
        if abs(px - self.x) + abs(py - self.y) <= 1:
            if random.random() < player.total_evasion / 100:
                messages.append((t('boss_charge_ev', self.name), 'good'))
            else:
                dmg = roll_damage(self.attack, player.total_defense, 1.7)
                player.take_damage(dmg)
                messages.append((t('boss_charge_hit', self.name, dmg), 'bad'))
        else:
            messages.append((t('boss_charge_use', self.name), 'warn'))
        return {'skill': 'charge', 'ex': self.x, 'ey': self.y}

    def _skill_whirlwind(self, player, messages):
        dist = abs(player.x - self.x) + abs(player.y - self.y)
        if dist <= 3:
            if random.random() < player.total_evasion / 100:
                messages.append((t('boss_whirl_ev', self.name), 'good'))
            else:
                dmg = roll_damage(self.attack, player.total_defense, 1.3)
                player.take_damage(dmg)
                messages.append((t('boss_whirl_hit', self.name, dmg), 'bad'))
        else:
            messages.append((t('boss_whirl_use', self.name), 'warn'))
        return {'skill': 'whirlwind', 'ex': self.x, 'ey': self.y}

    def _skill_death_nova(self, player, messages):
        dist = abs(player.x - self.x) + abs(player.y - self.y)
        if dist <= 5:
            if random.random() < player.total_evasion / 100:
                messages.append((t('boss_nova_ev', self.name), 'good'))
            else:
                dmg = roll_damage(self.attack, player.total_defense, 1.4)
                player.take_damage(dmg)
                messages.append((t('boss_nova_hit', self.name, dmg), 'bad'))
        else:
            messages.append((t('boss_nova_use', self.name), 'warn'))
        return {'skill': 'death_nova', 'ex': self.x, 'ey': self.y}

    def _skill_summon_undead(self, messages):
        messages.append((t('boss_summon', self.name), 'warn'))
        return {'skill': 'summon_undead', 'ex': self.x, 'ey': self.y, 'spawn_key': 'skeleton'}

    def _skill_curse(self, player, messages):
        player.cursed_ms = 8000
        messages.append((t('boss_curse', self.name), 'bad'))
        return {'skill': 'curse', 'ex': self.x, 'ey': self.y}

    def _skill_slow(self, player, messages):
        player.slowed_ms = 7000
        messages.append((t('boss_slow', self.name), 'bad'))
        return {'skill': 'slow', 'ex': self.x, 'ey': self.y}

    def _skill_fear(self, player, messages):
        player.feared_ms = 6000
        messages.append((t('boss_fear', self.name), 'bad'))
        return {'skill': 'fear', 'ex': self.x, 'ey': self.y}

    # ------------------------------------------------------------------ #
    def _do_attack(self, player, messages):
        # 회피 판정
        if random.random() < player.total_evasion / 100:
            messages.append((t('enemy_evade', self.name), 'good'))
            return
        dmg = roll_damage(self.attack, player.total_defense)
        player.take_damage(dmg)
        messages.append((t('enemy_atk', self.name, dmg), 'bad'))

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
                ox, oy = self.x, self.y
                self.x, self.y = nx, ny
                self._slide_from(ox, oy)
                break

"""마법사 소환수(정령) — 일정 시간 동안 근처 적을 자동으로 마법 공격.

런타임 전용 엔티티(세이브 X). Game._summons 리스트에서 update/draw 된다.
피해/사망 처리는 game._hurt_enemy 로 라우팅해 처치 보상을 중앙 집계한다.
"""
import math
import pygame

from core.constants import TILE_SIZE
from core.combat import roll_damage
from core.animator import MagicBoltAnim

_RANGE = 5          # 자동 조준 사거리(체비셰프)
_FIRE_CD = 900      # 발사 간격(ms)
_COL = (130, 200, 255)


class Summon:
    def __init__(self, x, y, life_ms, power_mul):
        self.x, self.y = x, y
        self.life_ms = float(life_ms)
        self.power_mul = power_mul
        self.alive = True
        self._fire_t = _FIRE_CD * 0.5
        self._t = 0.0

    def update(self, dt, game):
        self._t += dt
        self.life_ms -= dt
        if self.life_ms <= 0:
            self.alive = False
            return
        self._fire_t -= dt
        if self._fire_t > 0:
            return
        # 최근접 생존 적 조준
        best, bd = None, 999
        for e in game.dungeon.enemies:
            if not e.is_alive():
                continue
            d = max(abs(e.x - self.x), abs(e.y - self.y))
            if d <= _RANGE and d < bd:
                best, bd = e, d
        if best is None:
            return
        self._fire_t = _FIRE_CD
        facing = ('right' if best.x > self.x else 'left' if best.x < self.x
                  else 'down' if best.y > self.y else 'up')
        game.animator.add(MagicBoltAnim(self.x, self.y, best.x, best.y, facing, _COL))
        dmg = roll_damage(game._skill_atk, best.defense, self.power_mul)
        game._hurt_enemy(best, dmg, _COL)
        game._apply_burn(best, dps=max(1, dmg // 4), ms=1500, col=_COL)
        game.audio.play('bow_shoot')

    def draw(self, surf, cam_x, cam_y):
        ts = TILE_SIZE
        bob = int(math.sin(self._t * 0.006) * 3)
        cx = int((self.x - cam_x) * ts + ts // 2)
        cy = int((self.y - cam_y) * ts + ts // 2) + bob
        # 소멸 임박 시 깜빡임
        if self.life_ms < 1500 and (int(self.life_ms) // 150) % 2 == 0:
            return
        glow = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*_COL, 70), (11, 11), 10)
        pygame.draw.circle(glow, (*_COL, 140), (11, 11), 6)
        surf.blit(glow, (cx - 11, cy - 11), special_flags=pygame.BLEND_ADD)
        pygame.draw.circle(surf, (225, 240, 255), (cx, cy), 4)
        pygame.draw.circle(surf, _COL, (cx, cy), 4, 1)
        # 작은 룬 눈
        pygame.draw.circle(surf, (40, 60, 90), (cx - 1, cy - 1), 1)

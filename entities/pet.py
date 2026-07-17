"""펫(동반자) 시스템 — 3타입 · 강화 · 플레이어 추종.

타입:
  buff   : 2초마다 플레이어 공격력 +10% 버프(5초). 강화 레벨당 +1%
  debuff : 2초마다 가장 가까운 적 둔화 -30%(3초). 강화 레벨당 +2%
  attack : 2초마다 가장 가까운 적에 유도 미사일, 플레이어 공격력 30% 피해. 레벨당 +5%

펫 데이터(타입/레벨/해금/강화석)는 Player에 저장되고, 활성 Pet 객체는 Game이 보유한다.
"""
import math
import pygame

from core.constants import TILE_SIZE

# 타입별 메타 (이름 키는 lang.py, 색은 렌더용)
PET_TYPES = ('buff', 'debuff', 'attack')
PET_META = {
    'buff':   {'name_key': 'pet_buff',   'color': (240, 205, 90),  'accent': (255, 235, 150)},
    'debuff': {'name_key': 'pet_debuff', 'color': (150, 120, 230), 'accent': (200, 175, 255)},
    'attack': {'name_key': 'pet_attack', 'color': (235, 110, 90),  'accent': (255, 170, 150)},
}

TICK_MS   = 2000     # 능력 발동 주기
BUFF_MS   = 5000     # 버프 지속
SLOW_MS   = 3000     # 둔화 지속
_RANGE    = 9        # 능력 대상 탐색 사거리(타일, 맨해튼)


class Pet:
    def __init__(self, pet_type='attack', level=1):
        self.type  = pet_type if pet_type in PET_TYPES else 'attack'
        self.level = max(1, int(level))
        self.fx = 0.0                # 픽셀 좌표(부드러운 추종)
        self.fy = 0.0
        self.x = self.y = 0          # 타일 좌표(능력 원점)
        self._ti = 0                 # 트레일(경로) 진행 인덱스
        self._tick = TICK_MS
        self._bob_t = 0.0
        self._flash = 0.0            # 능력 발동 반짝임

    # ── 강화 계수 ────────────────────────────────────────────────────────
    @property
    def buff_pct(self):   return 0.10 + 0.01 * (self.level - 1)
    @property
    def slow_pct(self):   return 0.30 + 0.02 * (self.level - 1)
    @property
    def atk_coeff(self):  return 0.30 + 0.05 * (self.level - 1)

    def next_cost(self):
        """다음 강화 비용 (gold, stones)."""
        return 150 * self.level, self.level
    def success_chance(self):
        return max(0.30, 0.95 - 0.08 * (self.level - 1))

    GAP = 1              # 플레이어보다 몇 타일 뒤에서 따라올지
    _SPEED_MS = 120      # 한 타일 이동 기준 시간(ms) — 뒤처질수록 가속

    # ── 위치 초기화/추종 ─────────────────────────────────────────────────
    def snap_to(self, tile_x, tile_y):
        self.fx = tile_x * TILE_SIZE
        self.fy = tile_y * TILE_SIZE
        self.x, self.y = tile_x, tile_y
        self._ti = 0                         # 트레일 진행 인덱스

    def update(self, dt, game):
        self._bob_t += dt
        if self._flash > 0:
            self._flash = max(0.0, self._flash - dt)
        # 능력 주기
        self._tick -= dt
        if self._tick <= 0:
            self._tick += TICK_MS
            self._activate(game)

        # ── 경로(트레일) 추종: 플레이어가 지나간 타일만 밟는다 (벽 통과 X) ──
        trail = getattr(game, '_pet_trail', None)
        if not trail:
            return
        if self._ti > len(trail) - 1:
            self._ti = len(trail) - 1
        desired = max(0, len(trail) - 1 - self.GAP)   # 이 인덱스까지 전진
        behind = max(0, desired - self._ti)
        # 뒤처질수록 빠르게 (경로는 유지) — 등속 이동 + 캐치업 가속
        speed = TILE_SIZE * dt / self._SPEED_MS * (1.0 + 0.6 * behind)
        guard = 0
        while speed > 0 and guard < 64:
            guard += 1
            tx, ty = trail[self._ti]
            tgx, tgy = tx * TILE_SIZE, ty * TILE_SIZE
            dx, dy = tgx - self.fx, tgy - self.fy
            d = math.hypot(dx, dy)
            if d <= speed:
                self.fx, self.fy = tgx, tgy
                speed -= d
                if self._ti < desired:
                    self._ti += 1
                else:
                    break
            else:
                self.fx += dx / d * speed
                self.fy += dy / d * speed
                speed = 0
        self.x = int(round(self.fx / TILE_SIZE))
        self.y = int(round(self.fy / TILE_SIZE))

    # ── 능력 발동 ────────────────────────────────────────────────────────
    def _nearest_enemy(self, game):
        best, bd = None, 999
        for e in game.dungeon.enemies:
            if not e.is_alive() or not game.dungeon.tiles[e.y][e.x].visible:
                continue
            d = abs(e.x - self.x) + abs(e.y - self.y)
            if d <= _RANGE and d < bd:
                best, bd = e, d
        return best

    def _activate(self, game):
        self._flash = 260
        if self.type == 'buff':
            game._pet_buff(self.buff_pct, BUFF_MS)
        elif self.type == 'debuff':
            e = self._nearest_enemy(game)
            if e:
                game._pet_debuff(e, self.slow_pct, SLOW_MS)
        elif self.type == 'attack':
            e = self._nearest_enemy(game)
            if e:
                game._pet_attack(self, e)

    # ── 렌더 ─────────────────────────────────────────────────────────────
    def draw(self, surf, cam_x, cam_y):
        meta = PET_META[self.type]
        col, acc = meta['color'], meta['accent']
        bob = int(2 * math.sin(self._bob_t * 0.005))
        px = int(self.fx) - cam_x * TILE_SIZE + TILE_SIZE // 2
        py = int(self.fy) - cam_y * TILE_SIZE + TILE_SIZE // 2 + bob
        # 발동 오라
        if self._flash > 0:
            r = 10 + int(6 * (self._flash / 260))
            aura = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura, (*acc, 90), (r, r), r)
            surf.blit(aura, (px - r, py - r))

        def B(gx, gy, c, w=1, h=1):
            pygame.draw.rect(surf, c, (px + gx * 2, py + gy * 2, w * 2, h * 2))
        dark = tuple(max(0, k - 40) for k in col)
        # 작은 정령형 몸체 (블록)
        B(-3, -2, col, 6, 5)
        B(-3, -2, acc, 6, 1)
        B(-3, 2, dark, 6, 1)
        B(-2, -3, col, 4, 1)               # 머리 위 뿔/귀
        B(-2, 0, (30, 30, 40))             # 눈
        B(1, 0, (30, 30, 40))
        # 타입 표식(작은 아이콘)
        if self.type == 'buff':
            B(-1, -5, acc, 2, 2)           # 위로 화살표 느낌
        elif self.type == 'debuff':
            B(-1, -5, (120, 90, 200), 2, 1)
        else:
            B(2, -1, acc, 2, 1)            # 부리/발사구
        # 꼬리
        B(3, 1, dark); B(4, 2, dark)

    # ── 직렬화(값만; 활성 객체는 Game이 재생성) ─────────────────────────
    def to_dict(self):
        return {'type': self.type, 'level': self.level}

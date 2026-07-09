"""도파민 VFX 계층 — 게임 상태와 완전히 분리된 연출 모듈.

설계 원칙: **로직은 즉시 확정, 연출은 오버레이.**
- 골드는 킬 순간 지급되고, 코인 비행은 순수 시각 효과다.
- 드랍 아이템은 스폰 즉시 dungeon.items에 존재한다. 등급 연출(뜸들이기)
  중에도 밟으면 기존 경로로 즉시 픽업된다.
- 자석 픽업은 비행 완료 순간 기존 Game._pickup()을 호출할 뿐이며,
  아이템이 이미 사라졌으면(먼저 밟음) FX가 스스로 소멸한다.

구성:
  JuiceManager  — 화면 흔들림·히트스톱·펀치 줌 프리셋 파사드 (상태는 Game 소유)
  LootFXManager — 코인 분수/자석 + 아이템 산탄 등장 + 등급별 reveal + 자석 픽업
"""
import math
import random

import pygame

from core.constants import TILE_SIZE

_TWO_PI = math.pi * 2


# ═════════════════════════════════════════════════════════════════════════
#  ① Juicy Combat Feedback — 타격감 프리셋 파사드
# ═════════════════════════════════════════════════════════════════════════
class JuiceManager:
    """Game이 이미 소유한 shake/hitstop/punch-zoom 상태를 조작하는 프리셋 모음.

    상태 필드·업데이트 루프는 기존 그대로 두고(로직 무수정),
    콜사이트에 흩어져 있던 매직넘버만 의미 있는 이름으로 모은다.
    사용:  game.juice.crit()  /  game.juice.kill(boss=True)
    """

    def __init__(self, game):
        self._g = game

    # ── 내부 헬퍼 ────────────────────────────────────────────────────
    def _hitstop(self, ms):
        g = self._g
        g._hitstop_ms = max(g._hitstop_ms, ms)

    # ── 프리셋 ───────────────────────────────────────────────────────
    def hit(self):
        """일반 타격 — 짧은 역경직."""
        self._hitstop(30)

    def crit(self):
        """치명타 — 긴 역경직 + 흔들림 + 펀치 줌."""
        self._hitstop(70)
        self._g._start_shake(3, 130)
        self._g._start_punch_zoom(0.05, 120)

    def kill(self, boss=False):
        """처치 — 역경직 + 흔들림 (보스는 펀치 줌 추가)."""
        self._hitstop(60)
        self._g._start_shake(5 if boss else 2, 160)
        if boss:
            self._g._start_punch_zoom(0.07, 170)

    def tier_up(self):
        """콤보 티어 승급."""
        self._g._start_shake(4, 200)
        self._g._start_punch_zoom(0.05, 140)

    def levelup(self):
        """레벨업 셀레브레이션."""
        self._hitstop(110)
        self._g._start_shake(3, 240)
        self._g._gold_flash_ms = 420

    def hurt(self, heavy=False):
        """피격 — 피해 규모별 흔들림."""
        self._g._start_shake(5 if heavy else 3, 220 if heavy else 150)


# ═════════════════════════════════════════════════════════════════════════
#  ③ Variable Reward — 아이템 등급 판정
# ═════════════════════════════════════════════════════════════════════════
# rarity: (색상, 오브 상승 시간 ms, 버스트 파티클 수, 사운드 키)
RARITY_DEFS = {
    'common':   ((225, 225, 225),  280,  8,  'loot_r0'),
    'uncommon': ((110, 235, 120),  450, 14,  'loot_r1'),
    'rare':     (( 95, 175, 255),  650, 20,  'loot_r2'),
    'epic':     ((205, 115, 255),  900, 30,  'loot_r3'),
}


def item_rarity(item) -> str:
    """아이템 등급 판정 — 스폰 순간 확정되는 '결과값' (연출과 무관)."""
    eff = item.effect
    if eff == 'unlock_combo':
        return 'epic'
    if eff == 'enhance_stone':
        return 'rare'
    t = item.item_type
    v = item.value
    if t == 'consumable':
        if eff in ('teleport', 'whirlwind'):
            return 'uncommon'
        return 'uncommon' if (eff == 'heal' and v >= 40) or eff == 'stat_up_all' else 'common'
    if t == 'boots':
        return 'rare' if v >= 0.35 else ('uncommon' if v >= 0.25 else 'common')
    if v >= 8:
        return 'epic'
    if v >= 5:
        return 'rare'
    if v >= 3:
        return 'uncommon'
    return 'common'


# ═════════════════════════════════════════════════════════════════════════
#  ② Loot Explosion & Magnetism
# ═════════════════════════════════════════════════════════════════════════
_GRAV = 900.0          # 코인/바운스 중력 px/s²
_MAGNET_TILES = 2.5    # 자석 발동 반경 (타일)
_MAGNET_MS = 220.0     # 자석 비행 시간


class _Coin:
    """시각 전용 골드 코인 — 포물선 산탄 후 플레이어에게 흡입."""
    __slots__ = ('x', 'y', 'vx', 'vy', 'floor_y', 'age', 'burst_ms', 'phase',
                 'mx', 'my', 'mt', 'r')

    def __init__(self, x, y):
        a = random.uniform(0, _TWO_PI)
        spd = random.uniform(60, 190)
        self.x, self.y = x + random.uniform(-4, 4), y + random.uniform(-4, 4)
        self.vx = math.cos(a) * spd
        self.vy = -random.uniform(160, 320)          # 위로 튀어오름
        self.floor_y = y + random.uniform(2, 10)     # 착지 기준선
        self.age = 0.0
        self.burst_ms = random.uniform(320, 520)     # 흡입 시작까지
        self.phase = 0                               # 0=산탄  1=자석
        self.mx = self.my = 0.0                      # 자석 시작 위치
        self.mt = 0.0                                # 자석 경과
        self.r = random.choice((2, 2, 3))


class _DropFX:
    """드랍 아이템 1개의 연출 상태 오버레이 (아이템 상태와 분리)."""
    __slots__ = ('item', 'rarity', 'state', 't', 'rise_ms', 'bob',
                 'mx', 'my', 'name_t')

    def __init__(self, item, rarity):
        self.item = item
        self.rarity = rarity
        self.state = 'rise'      # rise → idle → magnet
        self.t = 0.0
        self.rise_ms = RARITY_DEFS[rarity][1]
        self.bob = random.uniform(0, _TWO_PI)
        self.mx = self.my = 0.0  # 자석 시작 월드 px
        self.name_t = -1.0       # 이름 팝업 경과 (-1=미시작)


class LootFXManager:
    """전리품 연출 총괄. Game 루프에 update()/draw() 두 줄로 부착된다.

    통합 예시 (core/game.py):
        __init__ : self.vfx_loot = LootFXManager(self.audio)
        킬 처리   : self.vfx_loot.spawn_gold(enemy.x, enemy.y, gold)
        드랍 처리 : self.vfx_loot.spawn_drop(item)          # 등급 자동 판정
        루프      : self.vfx_loot.update(world_dt, self)     # 히트스톱 시 정지
        렌더      : self.vfx_loot.draw(surf, cam_x, cam_y)   # 아이템 글리프 위
    """

    def __init__(self, audio):
        self._audio = audio
        self._coins: list[_Coin] = []
        self._fx: dict[int, _DropFX] = {}          # id(item) → _DropFX
        self._pops: list = []                       # [text, color, wx, wy, age]
        self._font = None                           # lazy (언어별)
        self._last_coin_snd = 0

    # ── 스폰 ─────────────────────────────────────────────────────────
    def spawn_gold(self, tx: int, ty: int, amount: int):
        """골드는 이미 지급된 상태 — 코인 비행은 순수 연출."""
        if amount <= 0:
            return
        cx = tx * TILE_SIZE + TILE_SIZE * 0.5
        cy = ty * TILE_SIZE + TILE_SIZE * 0.5
        n = max(3, min(3 + amount // 4, 14))
        for _ in range(n):
            self._coins.append(_Coin(cx, cy))

    def spawn_drop(self, item):
        """아이템은 이미 dungeon.items에 존재 — 등급 reveal 연출만 부착."""
        rarity = item_rarity(item)
        self._fx[id(item)] = _DropFX(item, rarity)
        return rarity

    def clear(self):
        """층 이동/재시작 시 호출 — 모든 연출 소멸 (상태에는 영향 없음)."""
        self._coins.clear()
        self._fx.clear()
        self._pops.clear()

    def reload_fonts(self):
        self._font = None

    # ── 렌더 협조: 아이템 글리프를 어디에/그릴지 ─────────────────────
    def item_render_state(self, item) -> tuple[float, float, bool]:
        """(ox, oy, draw_glyph). rise 동안은 오브가 대신 그려진다."""
        fx = self._fx.get(id(item))
        if fx is None:
            return 0.0, 0.0, True
        if fx.state == 'rise':
            return 0.0, 0.0, False
        if fx.state == 'magnet':
            ts = TILE_SIZE
            base_x = item.x * ts + ts * 0.5
            base_y = item.y * ts + ts * 0.5
            return fx.mx - base_x, fx.my - base_y, True
        # idle — 둥실거림
        oy = math.sin(pygame.time.get_ticks() * 0.005 + fx.bob) * 2.0
        return 0.0, oy, True

    # ── 갱신 ─────────────────────────────────────────────────────────
    def update(self, dt_ms: float, game):
        if dt_ms <= 0:
            return                          # 히트스톱 — 연출도 얼어붙는다
        dt = dt_ms / 1000.0
        player = game.player
        ts = TILE_SIZE
        px = player.x * ts + ts * 0.5 if player else 0
        py = player.y * ts + ts * 0.5 if player else 0

        self._update_coins(dt, dt_ms, px, py)
        self._update_drops(dt_ms, game, px, py)

        # 이름 팝업 수명
        for p in self._pops:
            p[4] += dt_ms
        self._pops = [p for p in self._pops if p[4] < 950]

    def _update_coins(self, dt, dt_ms, px, py):
        alive = []
        now = pygame.time.get_ticks()
        for c in self._coins:
            c.age += dt_ms
            if c.phase == 0:
                c.vy += _GRAV * dt
                c.x += c.vx * dt
                c.y += c.vy * dt
                if c.y >= c.floor_y and c.vy > 0:   # 바닥 바운스
                    c.y = c.floor_y
                    c.vy *= -0.45
                    c.vx *= 0.6
                if c.age >= c.burst_ms:
                    c.phase = 1
                    c.mx, c.my, c.mt = c.x, c.y, 0.0
                alive.append(c)
            else:
                c.mt += dt_ms
                k = min(1.0, c.mt / 320.0)
                k = k * k                            # 가속 흡입
                c.x = c.mx + (px - c.mx) * k
                c.y = c.my + (py - c.my) * k
                if k >= 1.0:
                    if now - self._last_coin_snd > 65:
                        self._audio.play('coin')
                        self._last_coin_snd = now
                    continue                         # 도착 — 소멸
                alive.append(c)
        self._coins = alive

    def _update_drops(self, dt_ms, game, px, py):
        items_alive = set(map(id, game.dungeon.items)) if game.dungeon else set()
        ts = TILE_SIZE
        dead = []
        for key, fx in self._fx.items():
            # 아이템이 사라졌으면(밟아서 픽업 등) 연출도 소멸
            if key not in items_alive:
                dead.append(key)
                continue
            fx.t += dt_ms
            item = fx.item
            if fx.state == 'rise':
                if fx.t >= fx.rise_ms:
                    fx.state = 'idle'
                    fx.t = 0.0
                    fx.name_t = 0.0
                    color, _, n_part, snd = RARITY_DEFS[fx.rarity]
                    game.animator.particles.emit_combo_tier(item.x, item.y, color)
                    self._audio.play(snd)
                    self._pops.append([item.name, color,
                                       item.x * ts + ts * 0.5,
                                       item.y * ts + ts * 0.2, 0.0])
            elif fx.state == 'idle':
                # 자석: 접근 + 수납 가능 시 발동
                if game.state == 'playing' and self._can_pickup(game, item):
                    d = math.hypot(px - (item.x * ts + ts * 0.5),
                                   py - (item.y * ts + ts * 0.5))
                    if d <= _MAGNET_TILES * ts:
                        fx.state = 'magnet'
                        fx.t = 0.0
                        fx.mx = item.x * ts + ts * 0.5
                        fx.my = item.y * ts + ts * 0.5
            elif fx.state == 'magnet':
                k = min(1.0, fx.t / _MAGNET_MS)
                k = k * k
                sx = item.x * ts + ts * 0.5
                sy = item.y * ts + ts * 0.5
                fx.mx = sx + (px - sx) * k
                fx.my = sy + (py - sy) * k
                if k >= 1.0:
                    dead.append(key)
                    game._pickup(item)               # 기존 픽업 경로 재사용
        for key in dead:
            self._fx.pop(key, None)

    @staticmethod
    def _can_pickup(game, item) -> bool:
        if item.effect in ('enhance_stone', 'unlock_combo'):
            return True                              # 인벤 슬롯 불필요
        return len(game.player.inventory) < game.player.max_inventory

    # ── 렌더 ─────────────────────────────────────────────────────────
    def draw(self, surf, cam_x: int, cam_y: int):
        ts = TILE_SIZE
        ox_cam, oy_cam = cam_x * ts, cam_y * ts
        ticks = pygame.time.get_ticks()

        # 등급 오브 + 빛기둥 (rise) / 바닥 글로우 (idle)
        for fx in self._fx.values():
            item = fx.item
            cx = int(item.x * ts + ts * 0.5 - ox_cam)
            cy = int(item.y * ts + ts * 0.5 - oy_cam)
            color = RARITY_DEFS[fx.rarity][0]
            if fx.state == 'rise':
                frac = min(1.0, fx.t / fx.rise_ms)
                # 빛기둥 — 등급 높을수록 길고 진하게
                pillar_h = int(ts * (0.8 + frac * 1.6))
                pw = 6 + int(4 * frac)
                pillar = pygame.Surface((pw, pillar_h), pygame.SRCALPHA)
                for i in range(pillar_h):
                    a = int(120 * frac * (1 - i / pillar_h))
                    pygame.draw.line(pillar, (*color, a), (0, i), (pw, i))
                surf.blit(pillar, (cx - pw // 2, cy - pillar_h))
                # 떠오르는 오브 (펄스)
                oy = int(frac * ts * 0.45)
                r = 4 + int(2 * math.sin(ticks * 0.02))
                pygame.draw.circle(surf, color, (cx, cy - oy), r)
                pygame.draw.circle(surf, (255, 255, 255), (cx, cy - oy), max(1, r - 2))
            elif fx.state == 'idle' and fx.rarity != 'common':
                # 바닥 등급 글로우 (레어 이상 눈에 띄게)
                pulse = 0.6 + 0.4 * math.sin(ticks * 0.004 + fx.bob)
                gw, gh = ts - 6, 8
                glow = pygame.Surface((gw, gh), pygame.SRCALPHA)
                pygame.draw.ellipse(glow, (*color, int(70 * pulse)), (0, 0, gw, gh))
                surf.blit(glow, (cx - gw // 2, cy + ts // 2 - gh + 2))

        # 코인
        for c in self._coins:
            x, y = int(c.x - ox_cam), int(c.y - oy_cam)
            pygame.draw.circle(surf, (255, 205, 60), (x, y), c.r)
            pygame.draw.circle(surf, (255, 240, 160), (x - 1, y - 1), 1)

        # 등급색 이름 팝업
        if self._pops:
            if self._font is None:
                from core.fonts import load_font
                self._font = load_font(13, bold=True)
            for text, color, wx, wy, age in self._pops:
                frac = age / 950.0
                alpha = max(0, int(255 * (1 - frac * frac)))
                txt = self._font.render(text, True, color)
                txt.set_alpha(alpha)
                surf.blit(txt, (int(wx - ox_cam) - txt.get_width() // 2,
                                int(wy - oy_cam - frac * 18)))

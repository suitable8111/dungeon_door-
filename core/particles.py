"""물리 기반 파티클 시스템.

physics : 중력(GRAVITY) · 공기저항(drag) · 수명(lifetime)에 따른 크기/알파 변화
render  : SRCALPHA 오버레이(일반 페이드) + BLEND_ADD 오버레이(글로우 빛 효과)
shapes  : 'dot' (원형) | 'shard' (회전 직사각형 파편)
"""
import math
import random

import pygame

from core.constants import TILE_SIZE

_TWO_PI  = math.pi * 2
_GRAVITY = 480.0      # px/s², 하강 가속도


# ── 수학 유틸 ────────────────────────────────────────────────────────────
def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_col(c0: tuple, c1: tuple, t: float) -> tuple:
    return (
        max(0, min(255, int(c0[0] + (c1[0] - c0[0]) * t))),
        max(0, min(255, int(c0[1] + (c1[1] - c0[1]) * t))),
        max(0, min(255, int(c0[2] + (c1[2] - c0[2]) * t))),
    )


def _shard_pts(cx: float, cy: float, w: float, h: float, angle: float) -> list:
    """회전된 직사각형 꼭짓점 4개 (월드 픽셀 → 화면 정수)."""
    ca, sa = math.cos(angle), math.sin(angle)
    hw, hh = w * 0.5, h * 0.5
    return [
        (int(cx + (-hw * ca + hh * sa)), int(cy + (-hw * sa - hh * ca))),
        (int(cx + ( hw * ca + hh * sa)), int(cy + ( hw * sa - hh * ca))),
        (int(cx + ( hw * ca - hh * sa)), int(cy + ( hw * sa + hh * ca))),
        (int(cx + (-hw * ca - hh * sa)), int(cy + (-hw * sa + hh * ca))),
    ]


# ── 파티클 데이터 ─────────────────────────────────────────────────────────
class Particle:
    """단일 물리 파티클 (__slots__ 으로 메모리 최소화)."""

    __slots__ = (
        'x', 'y',           # world-pixel 위치 (float)
        'vx', 'vy',         # 속도 px/s
        'drag',             # 초당 속도 감쇠 계수 (클수록 빠른 감속, 예: 2~8)
        'grav',             # 중력 배율 (1=정상, 0=무중력, -0.5=상승)
        'life',             # 남은 수명 ms
        'max_life',         # 전체 수명 ms
        'r0', 'r1',         # 반지름 시작/끝 (dot용)
        'c0', 'c1',         # 색상 (R,G,B) 시작/끝
        'a0', 'a1',         # 알파 시작/끝 (0–255)
        'glow',             # True → BLEND_ADD 글로우 렌더링
        'shape',            # 'dot' | 'shard'
        'angle', 'spin',    # 파편 회전 rad, rad/s
        'sw', 'sh',         # shard 폭/높이 px
    )

    def __init__(self, x, y, vx, vy, drag, grav,
                 life_ms, r0, r1, c0, c1,
                 a0=255, a1=0, glow=False,
                 shape='dot', angle=0.0, spin=0.0, sw=6, sh=2):
        self.x,  self.y  = float(x),  float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.drag  = drag
        self.grav  = grav
        self.life  = self.max_life = float(life_ms)
        self.r0,   self.r1 = r0, r1
        self.c0,   self.c1 = c0, c1
        self.a0,   self.a1 = a0, a1
        self.glow  = glow
        self.shape = shape
        self.angle, self.spin = angle, spin
        self.sw, self.sh = sw, sh


# ── 파티클 시스템 ─────────────────────────────────────────────────────────
class ParticleSystem:
    """Animator에 통합된 파티클 시스템. update/draw를 위임받아 실행."""

    def __init__(self):
        self._particles: list[Particle] = []
        # 렌더링 오버레이 (lazy init)
        self._normal: pygame.Surface | None = None   # SRCALPHA — 일반 알파 페이드
        self._glow:   pygame.Surface | None = None   # BLEND_ADD — 글로우 발광
        self._sz = (0, 0)

    # ── 내부 서피스 초기화 ────────────────────────────────────────────
    def _ensure(self, w: int, h: int):
        if self._sz != (w, h):
            self._normal = pygame.Surface((w, h), pygame.SRCALPHA)
            self._glow   = pygame.Surface((w, h))
            self._sz = (w, h)

    def clear(self):
        self._particles.clear()

    # ── 갱신 (중력 · 공기저항 · 위치 · 회전) ─────────────────────────
    def update(self, dt_ms: int):
        dt = dt_ms / 1000.0
        alive = []
        for p in self._particles:
            # 공기저항: v *= max(0, 1 - drag·dt)
            decay = max(0.0, 1.0 - p.drag * dt)
            p.vx *= decay
            p.vy *= decay
            # 중력
            p.vy += _GRAVITY * p.grav * dt
            # 위치
            p.x  += p.vx * dt
            p.y  += p.vy * dt
            # 파편 회전
            p.angle += p.spin * dt
            # 수명
            p.life -= dt_ms
            if p.life > 0:
                alive.append(p)
        self._particles = alive

    # ── 렌더링 ────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface, cam_x: int, cam_y: int):
        if not self._particles:
            return

        sw, sh = surf.get_size()
        self._ensure(sw, sh)
        n_surf, g_surf = self._normal, self._glow
        n_surf.fill((0, 0, 0, 0))
        g_surf.fill((0, 0, 0))

        ts       = TILE_SIZE
        has_glow = False

        for p in self._particles:
            frac = p.life / p.max_life          # 1=신선  0=소멸
            t    = 1.0 - frac                   # 0=신선  1=소멸

            alpha = max(0, min(255, int(_lerp(p.a0, p.a1, t))))
            if alpha < 4:
                continue

            r   = max(1, int(_lerp(p.r0, p.r1, t)))
            col = _lerp_col(p.c0, p.c1, t)

            # 화면 좌표
            sx = int(p.x - cam_x * ts)
            sy = int(p.y - cam_y * ts)

            # 화면 밖 컬링
            margin = max(r, p.sw) + 4
            if not (-margin <= sx <= sw + margin and -margin <= sy <= sh + margin):
                continue

            if p.glow:
                # ── BLEND_ADD 글로우 ──────────────────────────────
                has_glow = True
                # 색상 × 알파 → 광원 기여값
                gc = (col[0] * alpha // 255,
                      col[1] * alpha // 255,
                      col[2] * alpha // 255)
                if max(gc) < 4:
                    continue
                if p.shape == 'dot':
                    pygame.draw.circle(g_surf, gc, (sx, sy), r)
                    # 외곽 부드러운 할로
                    if r >= 3:
                        og = (gc[0] // 3, gc[1] // 3, gc[2] // 3)
                        if max(og) > 2:
                            pygame.draw.circle(g_surf, og, (sx, sy), r + r // 2)
                else:
                    pts = _shard_pts(sx, sy, max(1.0, p.sw * frac), p.sh, p.angle)
                    try:
                        pygame.draw.polygon(g_surf, gc, pts)
                    except Exception:
                        pass
            else:
                # ── SRCALPHA 일반 알파 ───────────────────────────
                rgba = (*col, alpha)
                if p.shape == 'dot':
                    pygame.draw.circle(n_surf, rgba, (sx, sy), r)
                else:
                    pts = _shard_pts(sx, sy, max(1.0, p.sw * frac), p.sh, p.angle)
                    try:
                        pygame.draw.polygon(n_surf, rgba, pts)
                    except Exception:
                        pass

        surf.blit(n_surf, (0, 0))
        if has_glow:
            surf.blit(g_surf, (0, 0), special_flags=pygame.BLEND_ADD)

    # ═══════════════════════════════════════════════════════════════════
    # 이미터 (스킬별 파티클 생성)
    # ═══════════════════════════════════════════════════════════════════
    def _tile_px(self, tx: int, ty: int) -> tuple[float, float]:
        ts = TILE_SIZE
        return tx * ts + ts * 0.5, ty * ts + ts * 0.5

    def _add(self, p: Particle):
        self._particles.append(p)

    # ── 기본 공격 타격 ────────────────────────────────────────────────
    def emit_basic_hit(self, tx: int, ty: int):
        """기본 공격 / 스킬 범용 타격 파편 — 황금 빛 조각."""
        cx, cy = self._tile_px(tx, ty)
        for _ in range(10):
            a = random.uniform(0, _TWO_PI)
            spd = random.uniform(140, 360)
            self._add(Particle(
                cx, cy, math.cos(a) * spd, math.sin(a) * spd,
                drag=3.5, grav=1.0, life_ms=random.randint(270, 480),
                r0=random.randint(2, 4), r1=1,
                c0=(255, random.randint(180, 240), 50),
                c1=(200, 90, 10),
                a0=230, a1=0, glow=True,
            ))
        for _ in range(6):
            a = random.uniform(0, _TWO_PI)
            spd = random.uniform(100, 260)
            self._add(Particle(
                cx, cy, math.cos(a) * spd, math.sin(a) * spd,
                drag=4.0, grav=1.3, life_ms=random.randint(200, 370),
                r0=2, r1=1,
                c0=(255, 210, 90), c1=(160, 60, 0),
                a0=200, a1=0, glow=False,
                shape='shard', angle=random.uniform(0, _TWO_PI),
                spin=random.uniform(-10, 10),
                sw=random.randint(5, 9), sh=random.randint(1, 3),
            ))

    # ── 강타 (Power Attack) ───────────────────────────────────────────
    def emit_power_hit(self, tx: int, ty: int):
        """강타 — 충격파 글로우 + 무거운 돌 파편."""
        cx, cy = self._tile_px(tx, ty)
        # 충격 글로우 방사
        for _ in range(10):
            a = random.uniform(0, _TWO_PI)
            spd = random.uniform(180, 480)
            self._add(Particle(
                cx, cy, math.cos(a) * spd, math.sin(a) * spd,
                drag=2.5, grav=0.7, life_ms=random.randint(280, 520),
                r0=random.randint(3, 6), r1=1,
                c0=(255, 200, 55), c1=(255, 70, 0),
                a0=255, a1=0, glow=True,
            ))
        # 돌 파편 — 고중력, 회전
        for _ in range(12):
            a = random.uniform(0, _TWO_PI)
            spd = random.uniform(90, 320)
            self._add(Particle(
                cx + random.uniform(-5, 5), cy + random.uniform(-5, 5),
                math.cos(a) * spd, math.sin(a) * spd - 70,
                drag=2.0, grav=2.0, life_ms=random.randint(350, 680),
                r0=2, r1=1,
                c0=(195, 165, 75), c1=(90, 60, 15),
                a0=215, a1=0, glow=False,
                shape='shard', angle=random.uniform(0, _TWO_PI),
                spin=random.uniform(-14, 14),
                sw=random.randint(4, 11), sh=random.randint(2, 4),
            ))

    # ── 돌진 (Dash) 궤적 ─────────────────────────────────────────────
    def emit_dash_trail(self, from_tile: tuple, to_tile: tuple):
        """돌진 궤적 — 청색 속도 입자 + 역방향 잔상."""
        ts = TILE_SIZE
        fx, fy = from_tile[0] * ts + ts // 2, from_tile[1] * ts + ts // 2
        tx2, ty2 = to_tile[0] * ts + ts // 2, to_tile[1] * ts + ts // 2
        if (fx, fy) == (tx2, ty2):
            return
        dash_ang   = math.atan2(ty2 - fy, tx2 - fx)
        trail_ang  = dash_ang + math.pi           # 역방향
        dist       = math.hypot(tx2 - fx, ty2 - fy)
        steps      = max(2, int(dist / (ts * 0.45)))
        for i in range(steps):
            frac_i = i / max(1, steps - 1)
            wx = fx + (tx2 - fx) * frac_i
            wy = fy + (ty2 - fy) * frac_i
            for _ in range(3):
                spread = random.uniform(-0.55, 0.55)
                a      = trail_ang + spread
                spd    = random.uniform(55, 175)
                self._add(Particle(
                    wx + random.uniform(-5, 5), wy + random.uniform(-5, 5),
                    math.cos(a) * spd, math.sin(a) * spd,
                    drag=5.0, grav=0.2, life_ms=random.randint(190, 360),
                    r0=random.randint(2, 4), r1=1,
                    c0=(70, 195, 255), c1=(20, 80, 200),
                    a0=210, a1=0, glow=True,
                ))

    # ── 회오리 (Whirl) ────────────────────────────────────────────────
    def emit_whirl(self, tile_x: int, tile_y: int):
        """회오리 — 원형 궤도 불꽃 파티클."""
        cx, cy = self._tile_px(tile_x, tile_y)
        ts = TILE_SIZE
        for i in range(22):
            a      = random.uniform(0, _TWO_PI)
            r_dist = random.uniform(ts * 0.25, ts * 1.6)
            wx     = cx + math.cos(a) * r_dist
            wy     = cy + math.sin(a) * r_dist
            tang   = a + math.pi / 2
            spd    = random.uniform(90, 220)
            self._add(Particle(
                wx, wy,
                math.cos(tang) * spd + random.uniform(-25, 25),
                math.sin(tang) * spd + random.uniform(-25, 25),
                drag=2.0, grav=0.05, life_ms=random.randint(330, 580),
                r0=random.randint(2, 5), r1=1,
                c0=(255, random.randint(90, 200), 25),
                c1=(255, 40, 0),
                a0=225, a1=0, glow=True,
            ))

    # ── 치유 (Heal) ───────────────────────────────────────────────────
    def emit_heal(self, tile_x: int, tile_y: int):
        """치유 — 녹색 상승 파티클 + 십자 빛 파편 (부력)."""
        cx, cy = self._tile_px(tile_x, tile_y)
        ts = TILE_SIZE
        # 상승 기포
        for _ in range(18):
            a      = random.uniform(0, _TWO_PI)
            r_dist = random.uniform(0, ts * 0.65)
            wx     = cx + math.cos(a) * r_dist
            wy     = cy + random.uniform(-ts * 0.1, ts * 0.3)
            self._add(Particle(
                wx, wy,
                random.uniform(-35, 35), random.uniform(-180, -80),
                drag=1.4, grav=-0.55, life_ms=random.randint(520, 950),
                r0=random.randint(2, 4), r1=1,
                c0=(55, 255, 100), c1=(20, 170, 60),
                a0=240, a1=0, glow=True,
            ))
        # 빛 파편 (반짝임)
        for _ in range(8):
            a = random.uniform(0, _TWO_PI)
            self._add(Particle(
                cx + random.uniform(-8, 8), cy + random.uniform(-8, 8),
                math.cos(a) * random.uniform(35, 95),
                math.sin(a) * random.uniform(35, 95) - 55,
                drag=3.0, grav=-0.35, life_ms=random.randint(380, 680),
                r0=1, r1=1,
                c0=(175, 255, 175), c1=(45, 195, 80),
                a0=195, a1=0, glow=False,
                shape='shard', angle=random.uniform(0, _TWO_PI),
                spin=random.uniform(-5, 5),
                sw=random.randint(6, 13), sh=1,
            ))

    # ── 파이어볼 적중 ──────────────────────────────────────────────────
    def emit_fireball_hit(self, tx: int, ty: int):
        """파이어볼 폭발 — 불꽃 방사 + 불똥 파편 낙하."""
        cx, cy = self._tile_px(tx, ty)
        # 불꽃 (약한 부력으로 위로 퍼짐)
        for _ in range(24):
            a   = random.uniform(0, _TWO_PI)
            spd = random.uniform(110, 440)
            self._add(Particle(
                cx + random.uniform(-5, 5), cy + random.uniform(-5, 5),
                math.cos(a) * spd, math.sin(a) * spd - random.uniform(20, 90),
                drag=1.7, grav=-0.22, life_ms=random.randint(380, 720),
                r0=random.randint(3, 7), r1=1,
                c0=(255, random.randint(70, 155), 8),
                c1=(200, 25, 0),
                a0=255, a1=0, glow=True,
            ))
        # 불똥 파편 (중력 낙하)
        for _ in range(14):
            a   = random.uniform(0, _TWO_PI)
            spd = random.uniform(180, 480)
            self._add(Particle(
                cx, cy, math.cos(a) * spd, math.sin(a) * spd,
                drag=2.3, grav=1.1, life_ms=random.randint(280, 580),
                r0=2, r1=1,
                c0=(255, 130, 15), c1=(170, 35, 0),
                a0=235, a1=0, glow=False,
                shape='shard', angle=random.uniform(0, _TWO_PI),
                spin=random.uniform(-18, 18),
                sw=random.randint(3, 9), sh=random.randint(1, 3),
            ))

    # ── 천둥격 적중 ────────────────────────────────────────────────────
    def emit_thunder_hit(self, tx: int, ty: int):
        """천둥격 — 전기 스파크 + 중앙 섬광 (무중력)."""
        cx, cy = self._tile_px(tx, ty)
        # 전기 스파크 (빠른 회전 파편)
        for _ in range(14):
            a   = random.uniform(0, _TWO_PI)
            spd = random.uniform(90, 320)
            self._add(Particle(
                cx + random.uniform(-3, 3), cy + random.uniform(-3, 3),
                math.cos(a) * spd, math.sin(a) * spd,
                drag=5.5, grav=0.0, life_ms=random.randint(160, 360),
                r0=2, r1=1,
                c0=(random.randint(175, 255), random.randint(155, 255), 255),
                c1=(70, 55, 200),
                a0=255, a1=0, glow=True,
                shape='shard', angle=random.uniform(0, _TWO_PI),
                spin=random.uniform(-30, 30),
                sw=random.randint(4, 13), sh=1,
            ))
        # 중앙 섬광
        for _ in range(6):
            a   = random.uniform(0, _TWO_PI)
            spd = random.uniform(40, 130)
            self._add(Particle(
                cx, cy, math.cos(a) * spd, math.sin(a) * spd,
                drag=6.5, grav=0.0, life_ms=random.randint(110, 230),
                r0=random.randint(3, 6), r1=1,
                c0=(255, 255, 255), c1=(190, 190, 255),
                a0=255, a1=0, glow=True,
            ))

    # ── 냉기 폭발 적중 ────────────────────────────────────────────────
    def emit_frost_hit(self, tx: int, ty: int):
        """냉기 — 얼음 결정 파편 (느린 낙하) + 청색 아우라."""
        cx, cy = self._tile_px(tx, ty)
        # 얼음 파편
        for _ in range(18):
            a   = random.uniform(0, _TWO_PI)
            spd = random.uniform(70, 280)
            self._add(Particle(
                cx + random.uniform(-6, 6), cy + random.uniform(-6, 6),
                math.cos(a) * spd, math.sin(a) * spd,
                drag=4.5, grav=0.55, life_ms=random.randint(480, 900),
                r0=2, r1=1,
                c0=(random.randint(155, 215), 240, 255),
                c1=(70, 150, 215),
                a0=225, a1=0, glow=False,
                shape='shard', angle=random.uniform(0, _TWO_PI),
                spin=random.uniform(-6, 6),
                sw=random.randint(4, 10), sh=random.randint(1, 3),
            ))
        # 냉기 글로우 아우라
        for _ in range(9):
            a   = random.uniform(0, _TWO_PI)
            spd = random.uniform(45, 170)
            self._add(Particle(
                cx, cy, math.cos(a) * spd, math.sin(a) * spd,
                drag=3.2, grav=0.0, life_ms=random.randint(280, 560),
                r0=random.randint(3, 6), r1=1,
                c0=(95, 215, 255), c1=(35, 90, 200),
                a0=195, a1=0, glow=True,
            ))

    # ── 바람 칼날 적중 ────────────────────────────────────────────────
    def emit_wind_hit(self, tx: int, ty: int, dir_x: int, dir_y: int):
        """바람 칼날 — 방향성 녹색 줄기 파편."""
        cx, cy = self._tile_px(tx, ty)
        base_a = math.atan2(dir_y, dir_x)
        for _ in range(16):
            spread = random.uniform(-0.65, 0.65)
            a      = base_a + spread
            spd    = random.uniform(190, 480)
            self._add(Particle(
                cx + random.uniform(-5, 5), cy + random.uniform(-5, 5),
                math.cos(a) * spd, math.sin(a) * spd,
                drag=2.5, grav=0.12, life_ms=random.randint(240, 480),
                r0=2, r1=1,
                c0=(random.randint(70, 175), 255, random.randint(70, 155)),
                c1=(18, 175, 45),
                a0=215, a1=0, glow=True,
                shape='shard', angle=a,
                spin=random.uniform(-5, 5),
                sw=random.randint(6, 15), sh=random.randint(1, 2),
            ))

    # ── 바람 칼날 궤적 (스킬 발동) ────────────────────────────────────
    def emit_wind_sweep(self, from_tile: tuple, to_tile: tuple, dir_x: int, dir_y: int):
        """바람 칼날 — 직선 관통 바람 줄기 (발동 시 전방 휙 이펙트)."""
        ts = TILE_SIZE
        fx = from_tile[0] * ts + ts * 0.5
        fy = from_tile[1] * ts + ts * 0.5
        tx2 = to_tile[0] * ts + ts * 0.5
        ty2 = to_tile[1] * ts + ts * 0.5
        # 벽에 바로 막혀도 최소 1타일 이펙트
        if abs(tx2 - fx) < 2 and abs(ty2 - fy) < 2:
            tx2 = fx + dir_x * ts
            ty2 = fy + dir_y * ts
        dist   = math.hypot(tx2 - fx, ty2 - fy)
        base_a = math.atan2(dir_y, dir_x)
        steps  = max(5, int(dist / (ts * 0.28)))
        for i in range(steps):
            frac = i / max(1, steps - 1)
            wx = fx + (tx2 - fx) * frac
            wy = fy + (ty2 - fy) * frac
            # 칼날형 긴 파편 — 전방 고속 이동
            for _ in range(5):
                spread = random.uniform(-0.20, 0.20)
                a      = base_a + spread
                spd    = random.uniform(440, 820)
                self._add(Particle(
                    wx + random.uniform(-4, 4), wy + random.uniform(-4, 4),
                    math.cos(a) * spd, math.sin(a) * spd,
                    drag=1.4, grav=0.0, life_ms=random.randint(110, 220),
                    r0=2, r1=1,
                    c0=(random.randint(80, 190), 255, random.randint(55, 130)),
                    c1=(22, 185, 48),
                    a0=235, a1=0, glow=True,
                    shape='shard', angle=a,
                    spin=random.uniform(-4, 4),
                    sw=random.randint(14, 24), sh=1,
                ))
            # 작은 공기 입자 — 흐름 표현
            for _ in range(2):
                spread = random.uniform(-0.40, 0.40)
                a      = base_a + spread
                spd    = random.uniform(220, 500)
                self._add(Particle(
                    wx + random.uniform(-7, 7), wy + random.uniform(-7, 7),
                    math.cos(a) * spd, math.sin(a) * spd,
                    drag=2.2, grav=0.0, life_ms=random.randint(80, 170),
                    r0=random.randint(2, 3), r1=1,
                    c0=(120, 255, 110), c1=(18, 145, 38),
                    a0=175, a1=0, glow=False,
                ))

    # ── 파이어볼 궤적 (스킬 발동) ─────────────────────────────────────
    def emit_fireball_trail(self, from_tile: tuple, to_tile: tuple):
        """파이어볼 — 불꽃 직선 궤적 (발동 시 전방 촥 이펙트)."""
        ts = TILE_SIZE
        fx  = from_tile[0] * ts + ts * 0.5
        fy  = from_tile[1] * ts + ts * 0.5
        tx2 = to_tile[0] * ts + ts * 0.5
        ty2 = to_tile[1] * ts + ts * 0.5
        if abs(tx2 - fx) < 2 and abs(ty2 - fy) < 2:
            return
        dist   = math.hypot(tx2 - fx, ty2 - fy)
        base_a = math.atan2(ty2 - fy, tx2 - fx)
        steps  = max(5, int(dist / (ts * 0.32)))
        for i in range(steps):
            frac = i / max(1, steps - 1)
            wx = fx + (tx2 - fx) * frac
            wy = fy + (ty2 - fy) * frac
            # 불꽃 글로우 — 전방 돌진 + 살짝 상승
            for _ in range(4):
                spread = random.uniform(-0.26, 0.26)
                a      = base_a + spread
                spd    = random.uniform(300, 620)
                self._add(Particle(
                    wx + random.uniform(-5, 5), wy + random.uniform(-5, 5),
                    math.cos(a) * spd, math.sin(a) * spd - random.uniform(25, 75),
                    drag=1.8, grav=-0.18, life_ms=random.randint(200, 430),
                    r0=random.randint(3, 6), r1=1,
                    c0=(255, random.randint(85, 170), 10),
                    c1=(215, 22, 0),
                    a0=248, a1=0, glow=True,
                ))
            # 불똥 파편 — 진행 방향 엠버
            for _ in range(3):
                spread = random.uniform(-0.34, 0.34)
                a      = base_a + spread
                spd    = random.uniform(160, 400)
                self._add(Particle(
                    wx + random.uniform(-5, 5), wy + random.uniform(-5, 5),
                    math.cos(a) * spd, math.sin(a) * spd,
                    drag=2.4, grav=0.45, life_ms=random.randint(155, 340),
                    r0=2, r1=1,
                    c0=(255, 128, 18), c1=(155, 28, 0),
                    a0=220, a1=0, glow=False,
                    shape='shard', angle=a,
                    spin=random.uniform(-10, 10),
                    sw=random.randint(4, 10), sh=1,
                ))

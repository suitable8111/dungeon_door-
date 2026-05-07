"""애니메이션: 공격 돌진 / 슬래시 / 피격 플래시 / 데미지 숫자 / 투사체."""
import math
import os
import random
import pygame
from core.constants import TILE_SIZE
from core.particles import ParticleSystem


def _load_font(size):
    for path in [
        '/System/Library/Fonts/AppleSDGothicNeo.ttc',
        'C:/Windows/Fonts/malgun.ttf',
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
    ]:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass
    return pygame.font.SysFont('sans-serif', size, bold=True)


def _smooth(t):
    return t * t * (3 - 2 * t)


class Animator:
    def __init__(self):
        pygame.font.init()
        self._font = _load_font(12)
        self._anims: list[_Anim] = []
        self.particles = ParticleSystem()

    def add(self, anim):
        self._anims.append(anim)

    def update(self, dt_ms):
        for a in self._anims:
            a.update(dt_ms)
        self._anims = [a for a in self._anims if not a.done]
        self.particles.update(dt_ms)

    @property
    def player_offset(self):
        for a in self._anims:
            if isinstance(a, LungeAnim):
                return a.offset
        return (0, 0)

    def draw(self, surf, cam_x, cam_y):
        self.particles.draw(surf, cam_x, cam_y)
        for a in self._anims:
            a.draw(surf, cam_x, cam_y, self._font)


class _Anim:
    def __init__(self, duration_ms):
        self.elapsed = 0
        self.duration = duration_ms

    def update(self, dt_ms):
        self.elapsed = min(self.duration, self.elapsed + dt_ms)

    @property
    def done(self):
        return self.elapsed >= self.duration

    @property
    def t(self):
        return self.elapsed / self.duration

    def draw(self, surf, cam_x, cam_y, font):
        pass


class LungeAnim(_Anim):
    def __init__(self, px, py, tx, ty):
        super().__init__(240)
        self.px, self.py = px, py
        self.tx, self.ty = tx, ty

    @property
    def offset(self):
        t = self.t
        frac = _smooth(t / 0.38) if t < 0.38 else _smooth(1.0 - (t - 0.38) / 0.62)
        max_px = TILE_SIZE * 0.45
        return (int((self.tx - self.px) * max_px * frac),
                int((self.ty - self.py) * max_px * frac))


class SlashAnim(_Anim):
    def __init__(self, ax, ay, tx, ty, color=(255, 235, 80)):
        super().__init__(280)
        self.ax, self.ay = ax, ay
        self.tx, self.ty = tx, ty
        self.color = color

    def draw(self, surf, cam_x, cam_y, font):
        ts = TILE_SIZE
        t = self.t
        cx = (self.tx - cam_x) * ts + ts // 2
        cy = (self.ty - cam_y) * ts + ts // 2

        ddx = self.tx - self.ax
        ddy = self.ty - self.ay
        ln = max(1.0, math.hypot(ddx, ddy))
        ndx, ndy = ddx / ln, ddy / ln
        pdx, pdy = -ndy, ndx

        fade = max(0.0, 1 - t * 1.5)
        r, g, b = self.color

        for sp in (-0.5, -0.25, 0, 0.25, 0.5):
            ox = pdx * sp * ts * 0.6
            oy = pdy * sp * ts * 0.6
            length = ts * 0.5 * (1 - t * 0.35)
            p1 = (int(cx - ndx * length + ox), int(cy - ndy * length + oy))
            p2 = (int(cx + ndx * length * 0.25 + ox), int(cy + ndy * length * 0.25 + oy))
            w = max(1, int(3 * fade))
            col = (int(r * fade), int(g * fade), int(b * fade))
            if any(c > 8 for c in col):
                pygame.draw.line(surf, col, p1, p2, w)

        ring_r = int(ts * 0.38 * _smooth(t))
        if ring_r > 1 and fade > 0.05:
            rc = (int(r * fade * 0.9), int(g * fade * 0.9), int(b * fade * 0.9))
            if any(c > 8 for c in rc):
                pygame.draw.circle(surf, rc, (cx, cy), ring_r, max(1, int(2 * fade)))


class HitFlashAnim(_Anim):
    def __init__(self, x, y, dmg, color=(255, 80, 80)):
        super().__init__(480)
        self.x, self.y = x, y
        self.dmg = dmg
        self.color = color

    def draw(self, surf, cam_x, cam_y, font):
        ts = TILE_SIZE
        t = self.t
        sx = (self.x - cam_x) * ts
        sy = (self.y - cam_y) * ts

        if t < 0.3:
            alpha = int(220 * (1 - t / 0.3))
            flash = pygame.Surface((ts, ts))
            flash.fill(self.color)
            flash.set_alpha(alpha)
            surf.blit(flash, (sx, sy))

        text_alpha = max(0, int(255 * (1 - t * 1.25)))
        if text_alpha > 6:
            float_y = sy - int(t * ts * 1.0)
            r, g, b = self.color
            bright = (min(255, r + 60), min(255, g + 60), min(255, b + 60))
            num_surf = font.render(f"-{self.dmg}", True, bright)
            num_surf.set_alpha(text_alpha)
            nx = sx + ts // 2 - num_surf.get_width() // 2
            surf.blit(num_surf, (nx, float_y))


class BoltAnim(_Anim):
    """원거리 투사체 (마법 볼트 등)."""
    def __init__(self, sx, sy, tx, ty, color=(100, 180, 255)):
        super().__init__(220)
        self.sx, self.sy = sx, sy
        self.tx, self.ty = tx, ty
        self.color = color

    def draw(self, surf, cam_x, cam_y, font):
        ts = TILE_SIZE
        t = self.t
        fade = max(0.0, 1 - t)
        r, g, b = self.color

        wx = self.sx + (self.tx - self.sx) * t
        wy = self.sy + (self.ty - self.sy) * t
        bx = int((wx - cam_x) * ts + ts // 2)
        by = int((wy - cam_y) * ts + ts // 2)

        col = (int(r * fade), int(g * fade), int(b * fade))
        if any(c > 8 for c in col):
            pygame.draw.circle(surf, col, (bx, by), max(1, int(5 * fade)))

        trail_t = max(0.0, t - 0.25)
        wx2 = self.sx + (self.tx - self.sx) * trail_t
        wy2 = self.sy + (self.ty - self.sy) * trail_t
        tx2 = int((wx2 - cam_x) * ts + ts // 2)
        ty2 = int((wy2 - cam_y) * ts + ts // 2)
        trail_col = (int(r * fade * 0.4), int(g * fade * 0.4), int(b * fade * 0.4))
        if any(c > 8 for c in trail_col) and (bx, by) != (tx2, ty2):
            pygame.draw.line(surf, trail_col, (tx2, ty2), (bx, by), max(1, int(2 * fade)))


class AttackSwingAnim(_Anim):
    """기본공격 검 휘두르기 — 7선 160° 부채꼴 + 팁 연결선 + 임팩트 플래시."""
    # 각 방향별 7방향 단위벡터 (±80° 범위)
    _FANS = {
        'right': [(0.174,-0.985),(0.643,-0.766),(0.940,-0.342),(1.0,0.0),(0.940,0.342),(0.643,0.766),(0.174,0.985)],
        'left':  [(-0.174,-0.985),(-0.643,-0.766),(-0.940,-0.342),(-1.0,0.0),(-0.940,0.342),(-0.643,0.766),(-0.174,0.985)],
        'down':  [(-0.985,0.174),(-0.766,0.643),(-0.342,0.940),(0.0,1.0),(0.342,0.940),(0.766,0.643),(0.985,0.174)],
        'up':    [(-0.985,-0.174),(-0.766,-0.643),(-0.342,-0.940),(0.0,-1.0),(0.342,-0.940),(0.766,-0.643),(0.985,-0.174)],
    }

    def __init__(self, px, py, facing='down', hit=True):
        super().__init__(220)
        self.px, self.py = px, py
        self.facing = facing
        self.hit = hit

    def draw(self, surf, cam_x, cam_y, font):
        t = self.t
        # 빠른 등장 → 서서히 페이드
        alpha = _smooth(min(1.0, t / 0.2)) if t < 0.2 else max(0.0, 1.0 - (t - 0.2) / 0.8)
        if alpha <= 0.02:
            return

        ts = TILE_SIZE
        cx = (self.px - cam_x) * ts + ts // 2
        cy = (self.py - cam_y) * ts + ts // 2

        fans = self._FANS.get(self.facing, self._FANS['down'])
        # 길이가 시간에 따라 확장
        base_len = ts * (0.45 + 0.75 * _smooth(min(1.0, t / 0.35)))

        tips = []
        for i, (dx, dy) in enumerate(fans):
            center_dist = abs(i - 3) / 3.0
            intensity = alpha * (1.0 - center_dist * 0.3)
            if self.hit:
                col = (int(255 * intensity), int((185 + int(55*(1-center_dist))) * intensity), int(50 * intensity))
            else:
                col = (int(90 * intensity), int(120 * intensity), int(210 * intensity))
            if not any(c > 6 for c in col):
                continue
            length = base_len * (1.35 if i == 3 else (1.1 if abs(i - 3) == 1 else 0.92))
            ex = int(cx + dx * length)
            ey = int(cy + dy * length)
            tips.append((ex, ey))
            w = 3 if i == 3 else (2 if abs(i - 3) <= 1 else 1)
            try:
                pygame.draw.line(surf, col, (int(cx), int(cy)), (ex, ey), w)
            except Exception:
                pass

        # 팁 연결 호선
        if len(tips) >= 2:
            for i in range(len(tips) - 1):
                if self.hit:
                    ac = (int(220 * alpha * 0.55), int(180 * alpha * 0.55), int(40 * alpha * 0.55))
                else:
                    ac = (int(70 * alpha * 0.55), int(90 * alpha * 0.55), int(180 * alpha * 0.55))
                if any(c > 6 for c in ac):
                    try:
                        pygame.draw.line(surf, ac, tips[i], tips[i + 1], 1)
                    except Exception:
                        pass

        # 명중 시 중앙 팁에 임팩트 플래시
        if self.hit and len(tips) > 3 and alpha > 0.15:
            tip = tips[3]
            impact = _smooth(min(1.0, t / 0.25))
            sr = max(2, int(9 * alpha * impact))
            sc = (int(255 * alpha), int(245 * alpha), int(130 * alpha))
            if any(c > 6 for c in sc):
                pygame.draw.circle(surf, sc, tip, sr)
            if sr > 4:
                rc = (int(255 * alpha * 0.5), int(160 * alpha * 0.5), int(60 * alpha * 0.5))
                if any(c > 6 for c in rc):
                    pygame.draw.circle(surf, rc, tip, sr + 4, 1)


class DashTrailAnim(_Anim):
    """대시 스킬 — 궤적 잔상 + 속도선."""
    def __init__(self, sx, sy, ex, ey):
        super().__init__(320)
        self.sx, self.sy = sx, sy
        self.ex, self.ey = ex, ey

    def draw(self, surf, cam_x, cam_y, font):
        t = self.t
        fade = max(0.0, 1.0 - t * 1.1)
        if fade <= 0.02:
            return

        ts = TILE_SIZE
        spx = (self.sx - cam_x) * ts + ts // 2
        spy = (self.sy - cam_y) * ts + ts // 2
        epx = (self.ex - cam_x) * ts + ts // 2
        epy = (self.ey - cam_y) * ts + ts // 2

        # 주 궤적 선
        lc = (int(80 * fade), int(190 * fade), int(255 * fade))
        if any(c > 6 for c in lc):
            pygame.draw.line(surf, lc, (spx, spy), (epx, epy), max(1, int(3 * fade)))

        # 잔상 사각형 (4개)
        for i in range(4):
            frac = (i + 1) / 5.0
            rx = int(spx + (epx - spx) * frac)
            ry = int(spy + (epy - spy) * frac)
            g_fade = fade * (1.0 - frac * 0.5)
            gc = (int(60 * g_fade), int(150 * g_fade), int(200 * g_fade))
            if any(c > 6 for c in gc):
                hw = max(2, int(ts * 0.32))
                pygame.draw.rect(surf, gc, (rx - hw, ry - hw, hw * 2, hw * 2), 1)

        # 속도선 (시작점 뒤쪽)
        dx = epx - spx
        dy = epy - spy
        dist = max(1.0, math.hypot(dx, dy))
        ndx, ndy = dx / dist, dy / dist
        pdx, pdy = -ndy, ndx
        for i in range(5):
            perp = (i - 2) * (ts * 0.13)
            lx1 = int(spx - ndx * ts * 0.4 + pdx * perp)
            ly1 = int(spy - ndy * ts * 0.4 + pdy * perp)
            lx2 = int(spx + pdx * perp)
            ly2 = int(spy + pdy * perp)
            sc = (int(50 * fade), int(130 * fade), int(180 * fade))
            if any(c > 6 for c in sc):
                pygame.draw.line(surf, sc, (lx1, ly1), (lx2, ly2), 1)


class WhirlAnim(_Anim):
    """휠윈드 스킬 — 회전 슬래시 + 확장 링 3파."""
    def __init__(self, px, py):
        super().__init__(450)
        self.px, self.py = px, py

    def draw(self, surf, cam_x, cam_y, font):
        t = self.t
        if t <= 0 or t >= 1:
            return

        ts = TILE_SIZE
        cx = (self.px - cam_x) * ts + ts // 2
        cy = (self.py - cam_y) * ts + ts // 2

        # 회전 슬래시선 (전반 60%)
        if t < 0.65:
            spin_t = t / 0.65
            angle_base = spin_t * math.pi * 3.0  # 1.5 바퀴
            spin_fade = max(0.0, 1.0 - spin_t * 0.7)
            for i in range(6):
                angle = angle_base + i * (math.pi / 3.0)
                llen = ts * (0.55 + 0.5 * _smooth(spin_t))
                x2 = int(cx + math.cos(angle) * llen)
                y2 = int(cy + math.sin(angle) * llen)
                lc = (int(255 * spin_fade), int(155 * spin_fade), int(35 * spin_fade))
                if any(c > 6 for c in lc):
                    pygame.draw.line(surf, lc, (cx, cy), (x2, y2), 2)

        # 확장 링 3파 (시간차)
        for wave in range(3):
            delay = wave * 0.18
            wt = (t - delay) / (1.0 - delay) if t > delay else 0.0
            if wt <= 0:
                continue
            wt = min(1.0, wt)
            ring_r = int(ts * 1.7 * _smooth(min(1.0, wt * 1.4)))
            ring_fade = max(0.0, 1.0 - wt * 1.3)
            if ring_r > 1 and ring_fade > 0.02:
                rc = (int(255 * ring_fade * 0.9), int(110 * ring_fade), int(40 * ring_fade))
                if any(c > 6 for c in rc):
                    pygame.draw.circle(surf, rc, (cx, cy), ring_r, max(1, int(2 * ring_fade + 1)))


class HealAnim(_Anim):
    """힐 스킬 — 녹색 오라 링 + 상승 파티클 8개."""
    def __init__(self, px, py):
        super().__init__(650)
        self.px, self.py = px, py
        self._sparks = [(random.uniform(0, 2 * math.pi), random.uniform(0.55, 1.0)) for _ in range(8)]

    def draw(self, surf, cam_x, cam_y, font):
        t = self.t
        if t <= 0 or t >= 1:
            return

        ts = TILE_SIZE
        cx = (self.px - cam_x) * ts + ts // 2
        cy = (self.py - cam_y) * ts + ts // 2

        # 확장 오라 링
        ring_r = int(ts * 1.6 * _smooth(min(1.0, t * 2.2)))
        ring_fade = max(0.0, 1.0 - t * 1.2)
        if ring_r > 1 and ring_fade > 0.02:
            rc = (int(55 * ring_fade), int(220 * ring_fade), int(100 * ring_fade))
            if any(c > 6 for c in rc):
                pygame.draw.circle(surf, rc, (cx, cy), ring_r, max(1, int(3 * ring_fade)))
            inner = max(0, ring_r - 7)
            if inner > 1:
                ic = (int(30 * ring_fade * 0.35), int(180 * ring_fade * 0.35), int(70 * ring_fade * 0.35))
                if any(c > 6 for c in ic):
                    pygame.draw.circle(surf, ic, (cx, cy), inner, 1)

        # 상승 스파크 파티클
        for i, (angle, speed) in enumerate(self._sparks):
            delay = i * 0.06
            pt = (t - delay) / (1.0 - delay) if t > delay else 0.0
            if pt <= 0:
                continue
            pt = min(1.0, pt)
            rise = pt * ts * 2.8 * speed
            spark_x = int(cx + math.cos(angle) * ts * 0.38)
            spark_y = int(cy - rise)
            spark_fade = max(0.0, 1.0 - pt * 1.05)
            if spark_fade > 0.02:
                sc = (int(75 * spark_fade), int(255 * spark_fade), int(125 * spark_fade))
                if any(c > 6 for c in sc):
                    pygame.draw.circle(surf, sc, (spark_x, spark_y), max(1, int(3 * spark_fade)))

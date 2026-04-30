"""애니메이션: 공격 돌진 / 슬래시 / 피격 플래시 / 데미지 숫자 / 투사체."""
import math
import os
import pygame
from core.constants import TILE_SIZE


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

    def add(self, anim):
        self._anims.append(anim)

    def update(self, dt_ms):
        for a in self._anims:
            a.update(dt_ms)
        self._anims = [a for a in self._anims if not a.done]

    @property
    def player_offset(self):
        for a in self._anims:
            if isinstance(a, LungeAnim):
                return a.offset
        return (0, 0)

    def draw(self, surf, cam_x, cam_y):
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
    """기본공격 검 휘두르기 이펙트 — 플레이어 앞쪽으로 부채꼴 선 5개."""
    _FANS = {
        'right': [( 0.35,-0.85),( 0.75,-0.50),( 1.0, 0.0),( 0.75, 0.50),( 0.35, 0.85)],
        'left':  [(-0.35,-0.85),(-0.75,-0.50),(-1.0, 0.0),(-0.75, 0.50),(-0.35, 0.85)],
        'down':  [(-0.85, 0.35),(-0.50, 0.75),( 0.0, 1.0),( 0.50, 0.75),( 0.85, 0.35)],
        'up':    [(-0.85,-0.35),(-0.50,-0.75),( 0.0,-1.0),( 0.50,-0.75),( 0.85,-0.35)],
    }

    def __init__(self, px, py, facing='down', hit=True):
        super().__init__(190)
        self.px, self.py = px, py
        self.facing = facing
        self.hit = hit

    def draw(self, surf, cam_x, cam_y, font):
        t = self.t
        fade = max(0.0, 1.0 - t * 1.5)
        if fade <= 0:
            return

        ts = TILE_SIZE
        cx = (self.px - cam_x) * ts + ts // 2
        cy = (self.py - cam_y) * ts + ts // 2

        fans = self._FANS.get(self.facing, self._FANS['down'])
        # 부채꼴이 시간에 따라 퍼져나감
        base_len = ts * (0.55 + 0.55 * t)

        for i, (dx, dy) in enumerate(fans):
            edge_dist = abs(i - 2) / 2.0   # 0=중앙, 1=가장자리
            intensity = fade * (1.0 - edge_dist * 0.4)

            if self.hit:
                col = (int(255 * intensity),
                       int((200 + int(55 * (1 - edge_dist))) * intensity),
                       int(70 * intensity))
            else:
                col = (int(120 * intensity), int(140 * intensity), int(210 * intensity))

            if not any(c > 6 for c in col):
                continue

            length = base_len * (1.25 if i == 2 else 0.88)
            ex = int(cx + dx * length)
            ey = int(cy + dy * length)
            w  = 2 if i == 2 else 1
            try:
                pygame.draw.line(surf, col, (int(cx), int(cy)), (ex, ey), w)
            except Exception:
                pass

        # 명중 시 끝에 스파크
        if self.hit and fade > 0.35:
            cdx, cdy = fans[2]
            sx2 = int(cx + cdx * base_len * 1.25)
            sy2 = int(cy + cdy * base_len * 1.25)
            sr  = max(1, int(4 * fade))
            sc  = (int(255 * fade), int(240 * fade), int(160 * fade))
            pygame.draw.circle(surf, sc, (sx2, sy2), sr)

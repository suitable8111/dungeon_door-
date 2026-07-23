"""애니메이션: 공격 돌진 / 슬래시 / 피격 플래시 / 데미지 숫자 / 투사체."""
import math
import os
import random
import pygame
from core.constants import TILE_SIZE
from core.particles import ParticleSystem


def _load_font(size):
    # 언어별 UI 폰트 (core/fonts.py) — 데미지 숫자·배너 공용
    from core.fonts import load_font
    return load_font(size, bold=True)


def _smooth(t):
    return t * t * (3 - 2 * t)


def _fade_text(txt, alpha):
    """폰트 텍스트 서피스를 alpha로 안전하게 페이드.

    set_alpha는 안티에일리어싱(픽셀 알파) 서피스에서 일부 환경(드라이버/포맷)
    시 투명 배경이 불투명 사각형으로 깨진다 → convert_alpha + 픽셀 알파 곱.
    """
    try:
        txt = txt.convert_alpha()
    except Exception:
        pass
    txt.fill((255, 255, 255, max(0, min(255, alpha))),
             special_flags=pygame.BLEND_RGBA_MULT)
    return txt


class Animator:
    def __init__(self):
        pygame.font.init()
        self._font = _load_font(12)
        self._anims: list[_Anim] = []
        self.particles = ParticleSystem()

    def reload_fonts(self):
        """언어 변경 후 호출 — 데미지 숫자/배너 폰트 재생성."""
        self._font = _load_font(12)
        BannerAnim._font_cache.clear()

    def add(self, anim):
        # 배너는 같은 y 슬롯에 겹치면 글자가 뭉개져 보인다 → 기존 것 교체
        if isinstance(anim, BannerAnim):
            self._anims = [a for a in self._anims
                           if not (isinstance(a, BannerAnim) and a.y == anim.y)]
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
    def __init__(self, x, y, dmg, color=(255, 80, 80), crit=False):
        super().__init__(560 if crit else 480)
        self.x, self.y = x, y
        self.dmg = dmg
        self.color = color
        self.crit = crit
        # 연타 시 숫자가 겹치지 않게 좌우 랜덤 오프셋
        self._jx = random.randint(-6, 6)

    def draw(self, surf, cam_x, cam_y, font):
        ts = TILE_SIZE
        t = self.t
        sx = (self.x - cam_x) * ts
        sy = (self.y - cam_y) * ts

        # 데미지 없는 플래시(상태이상/버프 표시 등): 딱딱한 사각형 대신
        # 부드러운 원형 글로우 펄스로 표시 (네모로 보이던 아티팩트 제거)
        if self.dmg <= 0:
            if t < 0.55:
                prog = t / 0.55
                alpha = int(140 * (1 - prog))
                if alpha > 4:
                    rad = max(2, int(ts * (0.32 + 0.30 * prog)))
                    cxp, cyp = sx + ts // 2, sy + ts // 2
                    glow = pygame.Surface((ts * 2, ts * 2), pygame.SRCALPHA)
                    c = self.color
                    pygame.draw.circle(glow, (c[0], c[1], c[2], alpha), (ts, ts), rad)
                    pygame.draw.circle(glow, (c[0], c[1], c[2], alpha // 2),
                                       (ts, ts), min(ts, rad + 3), 2)
                    surf.blit(glow, (cxp - ts, cyp - ts),
                              special_flags=pygame.BLEND_ADD)
            return

        text_alpha = max(0, int(255 * (1 - t * 1.25)))
        if text_alpha > 6:
            float_y = sy - int(_smooth(t) * ts * 1.1)
            if self.crit:
                bright = (255, 225, 70)
            else:
                r, g, b = self.color
                bright = (min(255, r + 60), min(255, g + 60), min(255, b + 60))
            num_surf = font.render(f"-{self.dmg}", True, bright)
            if self.crit:
                # 크리티컬: 초반에 크게 튀어나왔다 살짝 줄어드는 팝
                pop = 1.7 if t < 0.15 else 1.4
                w, h = num_surf.get_size()
                num_surf = pygame.transform.scale(num_surf, (int(w * pop), int(h * pop)))
            num_surf = _fade_text(num_surf, text_alpha)
            nx = sx + ts // 2 - num_surf.get_width() // 2 + self._jx
            surf.blit(num_surf, (nx, float_y))


_FACING_ANGLE = {'right': 0.0, 'down': 90.0, 'left': 180.0, 'up': 270.0}

# variant: (시작각 오프셋°, 끝각 오프셋°, 반경 배율, 지속 ms)
_SMEAR_DEFS = {
    'slash1':   (-75,  75, 1.00, 140),
    'slash2':   ( 75, -75, 1.00, 130),
    'finisher': (-105, 105, 1.30, 190),
    'backstep': ( 55, -55, 0.85, 120),
    # 도끼 — 더 넓고 묵직한 원호(느린 대신 큰 스윙)
    'axe1':     (-100, 100, 1.28, 200),
    'axe2':     ( 100,-100, 1.28, 190),
    'axefin':   (-145, 145, 1.65, 280),
}


class SmearAnim(_Anim):
    """검 궤적 스미어 — 부채꼴 초승달이 진행 방향으로 와이프되는 잔상.

    포즈 2~3장짜리 절차 애니메이션의 '스미어 프레임' 역할.
    로직과 무관한 순수 연출 (플레이어 타일 기준 월드 좌표).
    """

    def __init__(self, x, y, facing, variant='slash1', color=(255, 240, 180)):
        a0, a1, rmul, dur = _SMEAR_DEFS.get(variant, _SMEAR_DEFS['slash1'])
        super().__init__(dur)
        self.x, self.y = x, y
        base = _FACING_ANGLE.get(facing, 90.0)
        self.a0 = math.radians(base + a0)
        self.a1 = math.radians(base + a1)
        self.radius = TILE_SIZE * rmul
        self.color = color

    def draw(self, surf, cam_x, cam_y, font):
        t = self.t
        wipe = _smooth(min(1.0, t * 1.35))          # 와이프 진행
        fade = max(0.0, 1.0 - t * 1.15)
        if fade <= 0.02 or wipe <= 0.03:
            return
        ts = TILE_SIZE
        cx = (self.x - cam_x) * ts + ts // 2
        cy = (self.y - cam_y) * ts + ts // 2
        # 현재 와이프 구간의 초승달 (뒤꼬리가 좁아짐)
        a_head = self.a0 + (self.a1 - self.a0) * wipe
        a_tail = self.a0 + (self.a1 - self.a0) * max(0.0, wipe - 0.45)
        steps = 7
        r_out, r_in = self.radius, self.radius * 0.45
        outer, inner = [], []
        for i in range(steps + 1):
            a = a_tail + (a_head - a_tail) * (i / steps)
            k = i / steps                            # 꼬리→머리 폭 증가
            ro = r_in + (r_out - r_in) * (0.35 + 0.65 * k)
            outer.append((cx + math.cos(a) * ro, cy + math.sin(a) * ro))
            inner.append((cx + math.cos(a) * r_in, cy + math.sin(a) * r_in))
        pts = outer + inner[::-1]
        ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        r, g, b = self.color
        pygame.draw.polygon(ov, (r, g, b, int(120 * fade)), pts)
        # 흰 코어 라인 (머리쪽 가장자리)
        core = outer[-3:]
        if len(core) >= 2:
            pygame.draw.lines(ov, (255, 255, 255, int(200 * fade)), False,
                              [(int(px), int(py)) for px, py in core], 3)
        surf.blit(ov, (0, 0))


class ThrustSmearAnim(_Anim):
    """찌르기(런지) 스미어 — 전방 직선 스트릭."""

    def __init__(self, x, y, facing, length_tiles=2.2, color=(200, 235, 255)):
        super().__init__(150)
        self.x, self.y = x, y
        a = math.radians(_FACING_ANGLE.get(facing, 90.0))
        self.dx, self.dy = math.cos(a), math.sin(a)
        self.length = TILE_SIZE * length_tiles
        self.color = color

    def draw(self, surf, cam_x, cam_y, font):
        t = self.t
        fade = max(0.0, 1.0 - t * 1.2)
        if fade <= 0.02:
            return
        ts = TILE_SIZE
        cx = (self.x - cam_x) * ts + ts // 2
        cy = (self.y - cam_y) * ts + ts // 2
        reach = self.length * _smooth(min(1.0, t * 2.2))
        px, py = -self.dy, self.dx                   # 수직 벡터
        hw = 5 * fade + 1                            # 반폭 (좁아지며 소멸)
        tipx, tipy = cx + self.dx * reach, cy + self.dy * reach
        pts = [(cx + px * hw, cy + py * hw),
               (tipx + px * 1.5, tipy + py * 1.5),
               (tipx - px * 1.5, tipy - py * 1.5),
               (cx - px * hw, cy - py * hw)]
        ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        r, g, b = self.color
        pygame.draw.polygon(ov, (r, g, b, int(130 * fade)), pts)
        pygame.draw.line(ov, (255, 255, 255, int(210 * fade)),
                         (cx, cy), (tipx, tipy), 2)
        surf.blit(ov, (0, 0))


class AfterimageAnim(_Anim):
    """플레이어 잔상 — 스폰 시점 실루엣 스냅샷이 제자리에서 페이드아웃."""

    def __init__(self, snapshot: pygame.Surface, x, y, tint=None, dur=220):
        super().__init__(dur)
        self.snap = snapshot
        self.x, self.y = x, y                        # 타일 좌표
        self.tint = tint

    def draw(self, surf, cam_x, cam_y, font):
        alpha = int(150 * (1 - self.t))
        if alpha < 6:
            return
        ts = TILE_SIZE
        self.snap.set_alpha(alpha)
        surf.blit(self.snap, ((self.x - cam_x) * ts, (self.y - cam_y) * ts))


class CalloutAnim(_Anim):
    """월드 좌표 소형 콜아웃 텍스트 — 'CANCEL!' 등 (빠른 팝 + 상승)."""

    def __init__(self, x, y, text, color=(120, 230, 255)):
        super().__init__(620)
        self.x, self.y = x, y
        self.text = text
        self.color = color

    def draw(self, surf, cam_x, cam_y, font):
        t = self.t
        alpha = max(0, int(255 * (1 - t * t)))
        if alpha < 8:
            return
        ts = TILE_SIZE
        txt = font.render(self.text, True, self.color)
        if t < 0.18:                                  # 등장 펀치
            w, h = txt.get_size()
            k = 1.6 - 0.6 * (t / 0.18)
            txt = pygame.transform.scale(txt, (int(w * k), int(h * k)))
        txt = _fade_text(txt, alpha)
        sx = (self.x - cam_x) * ts + ts // 2 - txt.get_width() // 2
        sy = (self.y - cam_y) * ts - 6 - int(_smooth(t) * 16)
        surf.blit(txt, (sx, sy))


class GoldPopAnim(_Anim):
    """골드 획득 팝업 — '+N G' 금색 텍스트가 살짝 늦게 떠오른다."""

    def __init__(self, x, y, amount):
        super().__init__(820)
        self.x, self.y = x, y
        self.amount = amount
        self._jx = random.randint(-4, 4)

    def draw(self, surf, cam_x, cam_y, font):
        ts = TILE_SIZE
        t = self.t
        if t < 0.22:            # 데미지 숫자와 겹치지 않게 딜레이 후 등장
            return
        k = (t - 0.22) / 0.78
        alpha = max(0, int(235 * (1 - k * k)))
        if alpha < 8:
            return
        sy = (self.y - cam_y) * ts + ts // 2 - int(_smooth(k) * ts * 0.9)
        txt = font.render(f"+{self.amount} G", True, (255, 214, 84))
        txt = _fade_text(txt, alpha)
        surf.blit(txt, ((self.x - cam_x) * ts + ts // 2
                        - txt.get_width() // 2 + self._jx, sy))


class BannerAnim(_Anim):
    """화면 상단 중앙 대형 콜아웃 — 'RAMPAGE!' 'LEVEL UP!' 등.

    펀치 인(크게 등장 → 제자리) 후 유지, 마지막에 페이드아웃.
    카메라와 무관한 스크린 좌표에 그린다.
    """
    _font_cache: dict[int, pygame.font.Font] = {}

    def __init__(self, text, color, y=64, size=34, duration_ms=1300):
        super().__init__(duration_ms)
        self.text  = text
        self.color = color
        self.y     = y
        self.size  = size

    @classmethod
    def _font(cls, size):
        if size not in cls._font_cache:
            cls._font_cache[size] = _load_font(size)
        return cls._font_cache[size]

    def draw(self, surf, cam_x, cam_y, font):
        t = self.t
        # 등장 펀치: 2.1배 → 1.0배 (첫 14%), 이후 미세 펄스
        if t < 0.14:
            scale = 2.1 - 1.1 * _smooth(t / 0.14)
        else:
            scale = 1.0 + 0.035 * math.sin((t - 0.14) * 22)
        alpha = 255 if t < 0.72 else max(0, int(255 * (1 - (t - 0.72) / 0.28)))
        if alpha < 8:
            return
        f = self._font(self.size)
        base = f.render(self.text, True, self.color)
        w, h = base.get_size()
        sw, sh = max(1, int(w * scale)), max(1, int(h * scale))
        cx = surf.get_width() // 2

        # 외곽 그림자 (4방향) — 가독성 + 두께감
        dark = f.render(self.text, True,
                        tuple(max(0, c // 4) for c in self.color))
        dark = pygame.transform.scale(dark, (sw, sh))
        dark = _fade_text(dark, alpha)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            surf.blit(dark, (cx - sw // 2 + dx, self.y - sh // 2 + dy))

        main = pygame.transform.scale(base, (sw, sh))
        main = _fade_text(main, alpha)
        surf.blit(main, (cx - sw // 2, self.y - sh // 2))


class DeathAnim(_Anim):
    """적 사망 잔상 — 스프라이트가 주저앉으며 페이드아웃."""
    _CKEY = (1, 2, 3)

    def __init__(self, x, y, draw_fn, color, is_boss=False):
        super().__init__(320)
        self.x, self.y = x, y
        self.draw_fn = draw_fn
        self.color = color
        self.is_boss = is_boss

    def draw(self, surf, cam_x, cam_y, font):
        ts = TILE_SIZE
        t = self.t
        tmp = pygame.Surface((ts, ts))
        tmp.fill(self._CKEY); tmp.set_colorkey(self._CKEY)
        # 시체는 색이 바래며 어두워진다
        fade = tuple(max(0, int(c * (1 - t * 0.6))) for c in self.color)
        self.draw_fn(tmp, 0, 0, fade, pygame.time.get_ticks())
        # 세로로 주저앉는 스쿼시
        scale = 2 if self.is_boss else 1
        w = int(ts * scale * (1 + t * 0.25))
        h = max(2, int(ts * scale * (1 - _smooth(t) * 0.8)))
        squashed = pygame.transform.scale(tmp, (w, h))
        squashed.set_colorkey(self._CKEY)
        squashed.set_alpha(int(230 * (1 - t)))
        sx = (self.x - cam_x) * ts + (ts - w) // 2
        sy = (self.y - cam_y) * ts + (ts * scale - h) - (ts // 2 if self.is_boss else 0)
        surf.blit(squashed, (sx, sy))


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


class ArrowAnim(_Anim):
    """궁수 화살 — 발사 지점에서 목표까지 빠르게 날아가는 화살 스프라이트."""
    _FACE_ANG = {'right': 0.0, 'left': math.pi, 'down': math.pi / 2, 'up': -math.pi / 2}

    def __init__(self, sx, sy, tx, ty, facing='right', color=(240, 225, 150)):
        super().__init__(160)
        self.sx, self.sy = sx, sy
        self.tx, self.ty = tx, ty
        self.color = color
        self.ang = self._FACE_ANG.get(facing, 0.0)

    def draw(self, surf, cam_x, cam_y, font):
        ts = TILE_SIZE
        t = self.t
        # 앞머리는 조금 앞서고 꼬리는 뒤따라 — 화살 몸통
        head = min(1.0, t * 1.15)
        tail = max(0.0, t * 1.15 - 0.22)
        hx = int((self.sx + (self.tx - self.sx) * head - cam_x) * ts + ts // 2)
        hy = int((self.sy + (self.ty - self.sy) * head - cam_y) * ts + ts // 2)
        tx = int((self.sx + (self.tx - self.sx) * tail - cam_x) * ts + ts // 2)
        ty = int((self.sy + (self.ty - self.sy) * tail - cam_y) * ts + ts // 2)
        fade = max(0.0, 1.0 - t)
        shaft = tuple(int(c * (0.5 + 0.5 * fade)) for c in (150, 120, 70))
        pygame.draw.line(surf, shaft, (tx, ty), (hx, hy), 2)
        # 촉 (밝은 삼각)
        ca, sa = math.cos(self.ang), math.sin(self.ang)
        px, py = -sa, ca
        tip = (hx + int(ca * 4), hy + int(sa * 4))
        pygame.draw.polygon(surf, self.color, [
            tip, (hx + int(px * 3), hy + int(py * 3)),
            (hx - int(px * 3), hy - int(py * 3))])
        # 깃 (꼬리)
        pygame.draw.line(surf, (220, 220, 230),
                         (tx + int(px * 3), ty + int(py * 3)),
                         (tx - int(px * 3), ty - int(py * 3)), 1)


class MagicBoltAnim(_Anim):
    """마법사 마법 볼트 — 빛나는 원소 구체가 목표까지 날아가며 꼬리를 남긴다."""
    def __init__(self, sx, sy, tx, ty, facing='right', color=(150, 110, 245)):
        super().__init__(170)
        self.sx, self.sy = sx, sy
        self.tx, self.ty = tx, ty
        self.color = color

    def draw(self, surf, cam_x, cam_y, font):
        ts = TILE_SIZE
        t = self.t
        head = min(1.0, t * 1.15)
        tail = max(0.0, head - 0.28)
        hx = int((self.sx + (self.tx - self.sx) * head - cam_x) * ts + ts // 2)
        hy = int((self.sy + (self.ty - self.sy) * head - cam_y) * ts + ts // 2)
        txp = int((self.sx + (self.tx - self.sx) * tail - cam_x) * ts + ts // 2)
        typ = int((self.sy + (self.ty - self.sy) * tail - cam_y) * ts + ts // 2)
        c = self.color
        lite = tuple(min(255, v + 70) for v in c)
        # 꼬리(잔광)
        pygame.draw.line(surf, tuple(v // 2 for v in c), (txp, typ), (hx, hy), 3)
        # 외곽 글로우 → 코어
        glow = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*c, 90), (9, 9), 8)
        pygame.draw.circle(glow, (*c, 150), (9, 9), 5)
        surf.blit(glow, (hx - 9, hy - 9), special_flags=pygame.BLEND_ADD)
        pygame.draw.circle(surf, lite, (hx, hy), 3)


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

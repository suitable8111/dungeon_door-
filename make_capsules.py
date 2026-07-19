#!/usr/bin/env python3
"""
Steam 캡슐 이미지 자동 생성
Usage : python3 make_capsules.py
Output: assets/steam/ 폴더에 4개 PNG
  - header_capsule.png   920 × 430
  - small_capsule.png    462 × 174
  - main_capsule.png    1232 × 706
  - vertical_capsule.png 748 × 896
"""
import os, sys, math, random
import pygame

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
pygame.init()
pygame.display.set_mode((1, 1))

# 새 마인크래프트 스타일 아트 (인게임과 동일 소스)
from entities.avatar import draw_avatar_tile
from entities.mob_sprites import MC_ENEMY_SPRITE_FNS
from entities.hero_hd import draw_hero_hd   # 캡슐용 고해상도 전사

_HERO_APP = {'skin': 1, 'hair': 0, 'haircol': 1}   # 캡슐용 전사 외형


def _scale_tile(draw_into, size):
    """32px 타일에 그린 뒤 size로 최근접 확대(블록 유지)."""
    tile = pygame.Surface((32, 32), pygame.SRCALPHA)
    draw_into(tile)
    return pygame.transform.scale(tile, (size, size))


def _mc_hero_cropped(target_h, facing='right'):
    """전사 아바타를 콘텐츠 bbox로 크롭해 target_h 높이로 확대. (surf, w) 반환."""
    fc = facing if facing in ('down', 'up', 'left', 'right') else 'down'
    tile = pygame.Surface((32, 32), pygame.SRCALPHA)
    draw_avatar_tile(tile, 0, 0, fc, 0, 0, _HERO_APP, 'warrior')
    bb = tile.get_bounding_rect()
    if bb.width == 0 or bb.height == 0:
        bb = pygame.Rect(0, 0, 32, 32)
    crop = tile.subsurface(bb).copy()
    w = max(1, int(bb.width * target_h / bb.height))
    return pygame.transform.scale(crop, (w, target_h)), w


def _mc_mob_surf(key, size, col):
    fn = MC_ENEMY_SPRITE_FNS.get(key)
    return _scale_tile(lambda t: fn(t, 0, 0, col, 600), size)

OUT = os.path.join(BASE, 'assets', 'steam')
os.makedirs(OUT, exist_ok=True)

# ─── 팔레트 ─────────────────────────────────────────────────────────────
GOLD   = (235, 185,  60);  GOLD_L = (255, 222, 105);  GOLD_D = (150, 108,  18)
SIL    = (178, 183, 202);  SIL_D  = (118, 123, 148)
BLUE   = ( 62, 103, 162);  BLUE_D = ( 38,  66, 115)
BELT   = ( 95,  60,  20);  BOOT   = ( 88,  55,  25)
RED    = (200,  48,  48);  PLUME  = (230,  80,  80)
BG     = (  5,   5,  12);  WALL_C = ( 20,  18,  34);  FLOOR_C = ( 13,  12,  23)
CKEY   = (  1,   2,   3)

# ─── 폰트 ───────────────────────────────────────────────────────────────
_PF = os.path.join(BASE, 'assets', 'fonts', 'PressStart2P-Regular.ttf')
_KF = os.path.join(BASE, 'assets', 'fonts', 'DungGeunMo.ttf')

def px(sz):
    return pygame.font.Font(_PF, sz) if os.path.exists(_PF) else \
           pygame.font.SysFont('monospace', sz, bold=True)

def ko(sz):
    return pygame.font.Font(_KF, sz) if os.path.exists(_KF) else \
           pygame.font.SysFont('sans-serif', sz)

# ─── 기본 드로우 헬퍼 ────────────────────────────────────────────────────
def R(s, c, x, y, w, h):
    pygame.draw.rect(s, c, (round(x), round(y), max(1, round(w)), max(1, round(h))))

def C(s, c, x, y, r):
    pygame.draw.circle(s, c, (round(x), round(y)), max(1, round(r)))

def P(s, c, pts):
    pygame.draw.polygon(s, c, [(round(a), round(b)) for a, b in pts])

def L(s, c, x1, y1, x2, y2, w=1):
    pygame.draw.line(s, c, (round(x1), round(y1)), (round(x2), round(y2)), max(1, w))

# ─── 발광 효과 ───────────────────────────────────────────────────────────
def glow(surf, cx, cy, radius, color, steps=12):
    if radius <= 0:
        return
    sz = radius * 2 + 6
    gl = pygame.Surface((sz, sz), pygame.SRCALPHA)
    for i in range(steps, 0, -1):
        ri = max(1, int(radius * i / steps))
        frac = (steps - i + 1) / steps
        ai = int(200 * frac ** 1.6)
        pygame.draw.circle(gl, (*color[:3], ai), (sz // 2, sz // 2), ri)
    surf.blit(gl, (cx - sz // 2, cy - sz // 2))

# ─── 텍스트 헬퍼 ─────────────────────────────────────────────────────────
def txt_glow(surf, text, font, color, gcol, x, y, center=False):
    ts = font.render(text, True, color)
    if center:
        x -= ts.get_width() // 2
    for d in range(3, 0, -1):
        gs = font.render(text, True, gcol)
        gs.set_alpha(max(1, 45 // d))
        for i in range(8):
            a = math.pi * 2 * i / 8
            surf.blit(gs, (x + round(math.cos(a) * d * 1.5),
                           y + round(math.sin(a) * d * 1.5)))
    surf.blit(font.render(text, True, (0, 0, 0)), (x + 2, y + 2))
    surf.blit(ts, (x, y))
    return ts.get_width(), ts.get_height()

def txt_outline(surf, text, font, color, ocol, x, y, center=False, thick=2):
    ts = font.render(text, True, color)
    if center:
        x -= ts.get_width() // 2
    ots = font.render(text, True, ocol)
    for dx in range(-thick, thick + 1):
        for dy in range(-thick, thick + 1):
            if dx or dy:
                surf.blit(ots, (x + dx, y + dy))
    surf.blit(ts, (x, y))
    return ts.get_width(), ts.get_height()

# ─── 배경 / 환경 ─────────────────────────────────────────────────────────
def draw_bg(surf, w, h, rng, wall_frac=0.18):
    surf.fill(BG)
    ts = max(20, min(40, w // 28))
    wh = int(h * wall_frac)

    # 바닥 타일
    for row in range(h // ts + 2):
        for col in range(w // ts + 2):
            v = rng.randint(-3, 3)
            fc = tuple(max(0, min(255, c + v)) for c in FLOOR_C)
            R(surf, fc, col * ts, row * ts, ts - 1, ts - 1)

    # 벽
    for col in range(w // ts + 2):
        v = rng.randint(-4, 4)
        wc = tuple(max(0, min(255, c + v)) for c in WALL_C)
        R(surf, wc, col * ts, 0, ts - 1, wh)

    # 벽 아래 그림자 그라데이션
    ov = pygame.Surface((w, 22), pygame.SRCALPHA)
    for y in range(22):
        a = int(180 * (1 - y / 22) ** 2)
        pygame.draw.line(ov, (0, 0, 0, a), (0, y), (w, y))
    surf.blit(ov, (0, wh - 4))

    # 벽 티끌 / 균열
    for _ in range(rng.randint(30, 55)):
        br = rng.randint(50, 130)
        R(surf, (br, br, min(255, br + 25)),
          rng.randint(0, w), rng.randint(0, wh - 2), 1, 1)

def draw_torch(surf, x, y, s=1.0):
    r = max(1, round(s))
    glow(surf, x, y, int(90 * s), (255, 120, 30), 14)
    glow(surf, x, y, int(36 * s), (255, 230, 80),  7)
    R(surf, (110, 70, 15), x - 2 * r, y + r, 4 * r, 9 * r)
    R(surf, (155, 90, 20), x - 3 * r, y - r, 6 * r, 4 * r)
    C(surf, (255, 190, 55), x, y, 5 * r)
    C(surf, (255, 110, 20), x, y + 2 * r, 3 * r)
    C(surf, (255, 255, 150), x, y - 3 * r, 2 * r)

def draw_vignette(surf, w, h, alpha=210, fade=0.36):
    fw, fh = int(w * fade), int(h * fade)
    for i in range(fw):
        a = int(alpha * (1 - i / fw) ** 2.5)
        ls = pygame.Surface((1, h), pygame.SRCALPHA)
        ls.fill((0, 0, 0, a))
        surf.blit(ls, (i, 0))
        surf.blit(ls, (w - 1 - i, 0))
    for i in range(fh):
        a = int(alpha * (1 - i / fh) ** 2.5)
        ts2 = pygame.Surface((w, 1), pygame.SRCALPHA)
        ts2.fill((0, 0, 0, a))
        surf.blit(ts2, (0, i))
        surf.blit(ts2, (0, h - 1 - i))

# ─── 이끼 낀 고딕 던전 배경 (sample_image 무드) ──────────────────────────
_DG = dict(
    deep=(11, 22, 21), base=(18, 32, 30),
    brick=(30, 52, 46), brick_hi=(46, 74, 64), brick_lo=(19, 35, 31),
    mortar=(13, 25, 23), moss=(60, 108, 62), moss_d=(42, 82, 46),
    arch=(6, 14, 14), teal=(46, 150, 158), vine=(48, 100, 54),
    floor=(22, 40, 34), floor_hi=(34, 58, 48),
)


def _brick_wall(surf, x0, y0, w, h, rng, bw=34, bh=18):
    """이끼 낀 벽돌 텍스처."""
    dg = _DG
    R(surf, dg['base'], x0, y0, w, h)
    for i, ry in enumerate(range(y0, y0 + h, bh)):
        off = (bw // 2) if (i % 2) else 0
        for rx in range(x0 - bw, x0 + w, bw):
            bx = rx + off
            v = rng.randint(-8, 8)
            c = tuple(max(0, min(255, k + v)) for k in dg['brick'])
            R(surf, c, bx + 1, ry + 1, bw - 2, bh - 2)
            L(surf, dg['brick_hi'], bx + 1, ry + 1, bx + bw - 2, ry + 1)   # 상단 광
            L(surf, dg['brick_lo'], bx + 1, ry + bh - 2, bx + bw - 2, ry + bh - 2)
            if rng.random() < 0.18:                                       # 이끼 얼룩
                mc = dg['moss'] if rng.random() < 0.5 else dg['moss_d']
                R(surf, mc, bx + rng.randint(2, bw - 8), ry + bh - 4,
                  rng.randint(4, 10), 4)


def _gothic_arch(surf, cx, top, aw, ah, rng, glow_col=None):
    """고딕 아치 개구부(깊은 어둠 + 벽돌 테두리 + 안쪽 발광)."""
    dg = _DG
    half = aw // 2
    # 아치 실루엣 (사각 몸통 + 반원 상단)
    P(surf, dg['arch'], [(cx - half, top + ah), (cx - half, top + half),
                         (cx, top), (cx + half, top + half), (cx + half, top + ah)])
    pygame.draw.circle(surf, dg['arch'], (cx, top + half), half)
    if glow_col:
        g = pygame.Surface((aw, ah), pygame.SRCALPHA)
        for r in range(half, 0, -3):
            a = int(70 * (r / half))
            pygame.draw.circle(g, (*glow_col, 60 - a // 2),
                               (half, ah - half), r)
        surf.blit(g, (cx - half, top), special_flags=pygame.BLEND_ADD)
    # 벽돌 테두리 (아치 곡선 따라)
    import math as _m
    for a in range(0, 181, 8):
        rad = _m.radians(a)
        bx = cx - int(_m.cos(rad) * half)
        by = top + half - int(_m.sin(rad) * half)
        R(surf, dg['brick_hi'], bx - 2, by - 2, 5, 5)
        R(surf, dg['brick'], bx - 1, by - 1, 3, 3)


def draw_dungeon_bg(surf, w, h, rng, arches=True):
    """어두운 청록 이끼 고딕 던전 — 캡슐 공용 배경."""
    dg = _DG
    # 수직 그라데이션 베이스
    for y in range(h):
        t = y / h
        c = tuple(int(dg['deep'][i] + (dg['base'][i] - dg['deep'][i]) * (t * 0.7))
                  for i in range(3))
        pygame.draw.line(surf, c, (0, y), (w, y))
    # 벽돌 벽 (전면)
    _brick_wall(surf, 0, 0, w, h, rng, bw=max(26, w // 34), bh=max(15, h // 34))
    # 배경 아치(깊이감)
    if arches:
        aw = int(w * 0.30)
        _gothic_arch(surf, int(w * 0.30), int(h * 0.10), int(aw * 0.7),
                     int(h * 0.55), rng)
        _gothic_arch(surf, int(w * 0.62), int(h * 0.06), aw, int(h * 0.7),
                     rng, glow_col=dg['teal'])
    # 천장 매달린 이끼/덩굴
    for _ in range(int(w / 22)):
        vx = rng.randint(0, w)
        vl = rng.randint(int(h * 0.04), int(h * 0.16))
        vc = dg['vine'] if rng.random() < 0.6 else dg['moss_d']
        for k in range(0, vl, 3):
            R(surf, vc, vx + rng.randint(-1, 1), k, 2, 3)
        C(surf, dg['moss'], vx, vl, 2)
    # 바닥 이끼 석재
    fy = int(h * 0.86)
    R(surf, dg['floor'], 0, fy, w, h - fy)
    for rx in range(0, w, max(24, w // 30)):
        L(surf, dg['floor_hi'], rx, fy, rx, h)
        if rng.random() < 0.5:
            R(surf, dg['moss'], rx + rng.randint(0, 12), fy - 2,
              rng.randint(6, 16), 3)
    L(surf, dg['brick_hi'], 0, fy, w, fy)
    # 중앙 청록 대기광
    glow(surf, int(w * 0.6), int(h * 0.42), int(w * 0.22), (24, 70, 74), 12)


# ─── 발광 돌 골렘 보스 (sample_image) ────────────────────────────────────
def draw_golem(surf, cx, cy, s=4, staff=True):
    """이끼 낀 돌 골렘 — 발광 눈 + 지팡이 오브."""
    st = (58, 120, 92);  st_l = (86, 158, 120); st_d = (34, 78, 60)
    moss = (70, 130, 66); eye = (150, 255, 250); eyeg = (60, 220, 220)
    def B(gx, gy, c, wd=1, ht=1):
        R(surf, c, cx + gx * s, cy + gy * s, wd * s, ht * s)
    glow(surf, cx, cy, 30 * s, (20, 90, 90), 10)
    # 다리
    B(-6, 12, st_d, 5, 7); B(2, 12, st_d, 5, 7)
    B(-6, 18, st, 5, 2); B(2, 18, st, 5, 2)
    # 몸통(바위 블록)
    for (bx, by, ww, hh) in [(-8, 2, 16, 11)]:
        B(bx, by, st, ww, hh)
    for gx in range(-8, 8, 3):                       # 블록 균열
        B(gx, 2, st_d, 1, 11)
    for gy in range(2, 13, 3):
        B(-8, gy, st_d, 16, 1)
    B(-8, 2, st_l, 16, 1); B(-8, 2, st_l, 1, 11)     # 상/좌 광
    # 어깨/팔 (거대)
    B(-12, 0, st, 5, 8); B(-13, 0, st_l, 1, 8)       # 왼팔
    B(9, 0, st, 5, 9); B(13, 0, st_d, 1, 9)          # 오른팔(지팡이 쥠)
    B(-12, 8, st_d, 6, 4); B(9, 9, st_d, 6, 4)       # 주먹
    # 머리
    B(-5, -6, st, 10, 8); B(-5, -6, st_l, 10, 1)
    B(-6, -4, st, 1, 5); B(5, -4, st, 1, 5)          # 볼
    # 발광 눈(하나, 사이클롭스)
    glow(surf, cx + 0, cy - 2 * s, 5 * s, eyeg, 7)
    B(-2, -3, eye, 4, 3); B(-1, -3, (255, 255, 255), 2, 2)
    B(-4, -6, st_d, 3, 1); B(2, -6, st_d, 3, 1)      # 눈두덩
    # 이끼 덩굴 (어깨/머리)
    B(-4, -7, moss, 3, 1); B(3, 1, moss, 2, 2); B(-9, 3, moss, 2, 2)
    # 지팡이 + 발광 오브
    if staff:
        for gy in range(-10, 14):
            B(13, gy, (120, 100, 60))
        ox, oy = cx + 13 * s + s // 2, cy - 11 * s
        glow(surf, ox, oy, 9 * s, (70, 230, 230), 9)
        C(surf, (40, 160, 170), ox, oy, 4 * s)
        C(surf, (120, 245, 245), ox, oy, 3 * s)
        C(surf, (255, 255, 255), ox, oy, s + 1)


# ─── 청록 크리스탈 군집 ───────────────────────────────────────────────────
def draw_crystals(surf, x, y, s=4):
    cy_ = (120, 235, 240); cy_l = (200, 255, 255); cy_d = (50, 150, 170)
    glow(surf, x, y, 10 * s, (40, 160, 180), 8)
    shards = [(-4, 0, -6, -10, -1, 0), (0, 2, -1, -16, 2, 2), (3, 1, 5, -9, 6, 1)]
    for (ax, ay, tx, ty, bx, by) in shards:
        P(surf, cy_d, [(x+ax*s, y+ay*s), (x+tx*s, y+ty*s), (x+bx*s, y+by*s)])
        P(surf, cy_, [(x+ax*s+s, y+ay*s), (x+tx*s, y+ty*s),
                      (x+(tx+bx)//2*s, y+(ty+by)//2*s)])
        L(surf, cy_l, x+tx*s, y+ty*s, x+(ax+tx)//2*s, y+(ay+ty)//2*s, max(1, s//2))


def scatter_particles(surf, rng, x, y, w, h, n=60, pal=None):
    pal = pal or [(235, 185, 60), (180, 140, 40), (255, 220, 100),
                  (200, 160, 255), (150, 190, 255)]
    for _ in range(n):
        col = rng.choice(pal)
        r = rng.randint(1, 3)
        a = rng.randint(70, 210)
        gs = pygame.Surface((r * 2 + 1, r * 2 + 1), pygame.SRCALPHA)
        C(gs, (*col, a), r, r, r)
        surf.blit(gs, (rng.randint(x, x + w - 1), rng.randint(y, y + h - 1)))

# ─── 영웅 스프라이트 (실제 assets 로드) ──────────────────────────────────
_HERO_CACHE: dict = {}

def _load_hero(facing: str):
    if facing not in _HERO_CACHE:
        fname = {
            'down':  'hero_down.png',
            'right': 'hero_right.png',
            'left':  'hero_left.png',
            'up':    'hero_up.png',
        }.get(facing, 'hero_down.png')
        path = os.path.join(BASE, 'assets', 'sprites', fname)
        img = pygame.image.load(path).convert_alpha()
        _HERO_CACHE[facing] = img
    return _HERO_CACHE[facing]

def hero_size(target_h: int, facing='down') -> tuple:
    """HD 전사의 (w, h) 반환 (스크래치에 렌더해 폭 측정)."""
    scratch = pygame.Surface((target_h * 2 + 4, target_h + 4), pygame.SRCALPHA)
    w, _ = draw_hero_hd(scratch, 0, 0, target_h)
    return w, target_h

def draw_hero(surf, hx, hy, target_h: int, facing='down') -> tuple:
    """고해상도 전사(갑옷·칼)를 target_h 높이로 그린다. (w, h) 반환."""
    return draw_hero_hd(surf, hx, hy, target_h, facing)

# ─── 적/보스 스프라이트 (마인크래프트 블록) ──────────────────────────────
#  (x, y)=중심,  s=크기 배율.  32px 타일을 약 22*s 크기로 확대해 중앙 배치.
def _blit_mc_mob(surf, key, x, y, s, col):
    size = int(30 * s)
    img = _mc_mob_surf(key, size, col)
    surf.blit(img, (int(x - size / 2), int(y - size / 2)))

def draw_skeleton(surf, x, y, s=3):
    _blit_mc_mob(surf, 'blade_skeleton', x, y, s, (210, 70, 70))

def draw_dark_knight(surf, x, y, s=4):
    glow(surf, x, y, 30 * s, (80, 18, 130), 10)
    glow(surf, x, y, 12 * s, (160, 40, 210), 5)
    _blit_mc_mob(surf, 'dark_knight', x, y, s, (72, 70, 92))

def draw_slime(surf, x, y, s=3, col=(70, 190, 90)):
    _blit_mc_mob(surf, 'slime', x, y, s, col)

def draw_reaper(surf, x, y, s=4):
    glow(surf, x, y, 26 * s, (80, 200, 120), 9)
    _blit_mc_mob(surf, 'lich', x, y, s, (120, 90, 200))


def _draw_skeleton_LEGACY(surf, x, y, s=3):
    bc = (190, 185, 170)
    glow(surf, x, y - 8 * s, 22 * s, (60, 90, 200), 7)
    # 다리
    L(surf, bc, x - 2*s, y + 7*s, x - 5*s, y + 18*s, s)
    L(surf, bc, x + 2*s, y + 7*s, x + 5*s, y + 18*s, s)
    L(surf, bc, x - 5*s, y + 18*s, x - 8*s, y + 18*s, s)
    L(surf, bc, x + 5*s, y + 18*s, x + 8*s, y + 18*s, s)
    R(surf, bc, x - 4*s, y + 5*s, 8*s, 3*s)
    # 척추
    for i in range(5):
        C(surf, bc, x, y - 8*s + i * 4*s, s + 1)
    # 갈비뼈
    for i in range(3):
        ry = y - 6*s + i * 4*s
        L(surf, bc, x, ry, x - 7*s, ry + 2*s, s)
        L(surf, bc, x, ry, x + 7*s, ry + 2*s, s)
    # 팔 + 검
    L(surf, bc, x - 2*s, y - 3*s, x - 10*s, y + 3*s, s)
    L(surf, bc, x + 2*s, y - 3*s, x + 10*s, y - 6*s, s)
    L(surf, SIL, x + 10*s, y - 6*s, x + 16*s, y - 18*s, max(1, s))
    L(surf, GOLD_D, x + 8*s, y - 4*s, x + 13*s, y - 4*s, s)
    # 두개골
    C(surf, bc, x, y - 14*s, 5*s)
    glow(surf, x - 3*s, y - 15*s, 4*s, (80, 130, 255), 5)
    glow(surf, x + 3*s, y - 15*s, 4*s, (80, 130, 255), 5)
    C(surf, (25, 45, 160), x - 3*s, y - 15*s, 2*s)
    C(surf, (25, 45, 160), x + 3*s, y - 15*s, 2*s)
    C(surf, (140, 180, 255), x - 3*s, y - 15*s, s)
    C(surf, (140, 180, 255), x + 3*s, y - 15*s, s)
    R(surf, bc, x - 4*s, y - 10*s, 8*s, 3*s)
    R(surf, (20, 18, 28), x - 2*s, y - 10*s, 2*s, 2*s)
    R(surf, (20, 18, 28), x + 1*s, y - 10*s, 2*s, 2*s)

def _draw_dark_knight_LEGACY(surf, x, y, s=4):
    ac = (28, 25, 45);  al = (55, 50, 80);  agl = (80, 74, 110)
    ec = (220, 45, 45)
    # 오라
    glow(surf, x, y, 45 * s, (80, 18, 130), 10)
    glow(surf, x, y, 18 * s, (160, 40, 210),  5)
    # 망토
    P(surf, (16, 13, 28),
      [(x-9*s,y-2*s), (x+9*s,y-2*s), (x+14*s,y+32*s), (x-14*s,y+32*s)])
    # 다리
    R(surf, ac, x - 7*s, y + 16*s, 6*s, 18*s)
    R(surf, al, x - 6*s, y + 16*s, 4*s,  3*s)
    R(surf, ac, x + 1*s, y + 16*s, 6*s, 18*s)
    R(surf, al, x + 2*s, y + 16*s, 4*s,  3*s)
    R(surf, (16, 14, 26), x - 8*s, y + 29*s, 7*s, 5*s)
    R(surf, (16, 14, 26), x + 1*s, y + 29*s, 7*s, 5*s)
    # 몸
    R(surf, ac, x - 9*s, y - 2*s, 18*s, 20*s)
    R(surf, al, x - 6*s, y,       12*s,  4*s)
    R(surf, agl,x - 5*s, y,       10*s,  2*s)
    # 어깨 갑옷
    for sign in (-1, 1):
        px2 = x + sign * 11 * s
        C(surf, al, px2, y - 4*s, 6*s)
        C(surf, ac, px2, y - 4*s, 5*s)
        C(surf, agl, px2, y - 5*s, 3*s)
        P(surf, al, [(px2 + sign*2*s, y - 9*s),
                     (px2 + sign*4*s, y - 4*s),
                     (px2 - sign*2*s, y - 4*s)])
    # 팔
    R(surf, ac, x - 12*s, y - 1*s, 5*s, 14*s)
    R(surf, ac, x +  7*s, y - 1*s, 5*s, 14*s)
    # 대검
    L(surf, (160, 155, 185), x + 16*s, y - 28*s, x + 16*s, y + 32*s, s * 2 + 1)
    L(surf, SIL,              x + 16*s, y - 28*s, x + 16*s, y + 32*s, s)
    L(surf, GOLD_D, x + 8*s, y - 4*s, x + 24*s, y - 4*s, s + 1)
    L(surf, GOLD,   x + 9*s, y - 4*s, x + 23*s, y - 4*s, s)
    glow(surf, x + 16*s, y - 28*s, 9*s, (180, 200, 255), 6)
    # 투구
    R(surf, ac, x - 9*s, y - 18*s, 18*s, 16*s)
    C(surf, ac, x, y - 18*s, 9*s)
    P(surf, (165, 18, 18),
      [(x-2*s, y-27*s), (x+2*s, y-27*s), (x+1*s, y-18*s), (x-1*s, y-18*s)])
    glow(surf, x - 3*s, y - 14*s, 5*s, (255, 38, 38), 6)
    glow(surf, x + 3*s, y - 14*s, 5*s, (255, 38, 38), 6)
    R(surf, ec, x - 5*s, y - 15*s, 4*s, 2*s)
    R(surf, ec, x + 1*s, y - 15*s, 4*s, 2*s)
    R(surf, al, x - 7*s, y -  6*s, 14*s, 4*s)

def _draw_slime_LEGACY(surf, x, y, s=3, col=(55, 170, 75)):
    lc = tuple(min(255, c + 90) for c in col)
    glow(surf, x, y, 18 * s, col, 6)
    C(surf, tuple(max(0, c-40) for c in col), x,      y,      10*s)
    C(surf, col, x - 4*s, y + 4*s, 8*s)
    C(surf, col, x + 4*s, y + 4*s, 8*s)
    C(surf, col, x,       y,        9*s)
    C(surf, lc,  x - 2*s, y - 5*s,  4*s)
    C(surf, (255, 255, 255), x - 3*s, y - 6*s, 2*s)
    C(surf, (0, 0, 0), x - 4*s, y - 2*s, 2*s)
    C(surf, (0, 0, 0), x + 4*s, y - 2*s, 2*s)
    C(surf, (220, 220, 255), x - 3*s, y - 3*s, s)
    C(surf, (220, 220, 255), x + 5*s, y - 3*s, s)
    for dx, dy in [(-5, 9), (0, 11), (5, 9)]:
        C(surf, col, x + dx*s, y + dy*s, 3*s)

def _draw_reaper_LEGACY(surf, x, y, s=4):
    rc = (18, 16, 28);  rl = (40, 38, 60);  bc = (180, 172, 155)
    glow(surf, x, y - 5*s, 28*s, (80, 200, 80), 9)
    P(surf, rc, [(x-8*s,y),(x+8*s,y),(x+13*s,y+32*s),(x-13*s,y+32*s)])
    P(surf, rl, [(x-8*s,y),(x+8*s,y),(x+6*s,y+5*s),(x-6*s,y+5*s)])
    C(surf, rc, x, y - 10*s, 8*s)
    R(surf, rc, x - 8*s, y - 12*s, 16*s, 12*s)
    C(surf, bc, x, y - 10*s, 5*s)
    glow(surf, x - 3*s, y - 11*s, 4*s, (40, 195, 40), 5)
    glow(surf, x + 3*s, y - 11*s, 4*s, (40, 195, 40), 5)
    C(surf, (18, 155, 28), x - 3*s, y - 11*s, 2*s)
    C(surf, (18, 155, 28), x + 3*s, y - 11*s, 2*s)
    L(surf, (100, 95, 115), x + 6*s, y - 22*s, x + 6*s, y + 8*s, s)
    P(surf, SIL, [(x+6*s,y-22*s),(x+17*s,y-20*s),(x+15*s,y-12*s),(x+6*s,y-14*s)])
    glow(surf, x + 11*s, y - 18*s, 9*s, (160, 210, 255), 6)
    L(surf, bc, x + 6*s, y, x + 8*s, y - 16*s, s)


# ─── 로고 ────────────────────────────────────────────────────────────────
def draw_logo(surf, cx, ty, big_sz, small_sz, right_align_x=None):
    f1, f2 = px(big_sz), px(small_sz)
    t1, t2 = "DUNGEON", "DOOR"
    w1 = f1.render(t1, True, GOLD).get_width()
    w2 = f2.render(t2, True, GOLD).get_width()
    if right_align_x is not None:
        x1, x2 = right_align_x - w1, right_align_x - w2
    else:
        x1, x2 = cx - w1 // 2, cx - w2 // 2
    txt_glow(surf, t1, f1, GOLD_L, GOLD_D, x1, ty)
    h1 = f1.get_height()
    txt_glow(surf, t2, f2, GOLD,   GOLD_D, x2, ty + h1 + 8)
    return h1 + 8 + f2.get_height()

# ═══════════════════════════════════════════════════════════════════════
#  캡슐 생성 함수
# ═══════════════════════════════════════════════════════════════════════

def make_header(rng):
    """920 × 430  가로 배너"""
    W, H = 920, 430
    surf = pygame.Surface((W, H))
    draw_bg(surf, W, H, rng, wall_frac=0.20)

    # 횃불
    draw_torch(surf, 90,  80, 1.4)
    draw_torch(surf, W - 90, 80, 1.4)

    # 천장 분위기 빛
    glow(surf, W // 2, H // 3, 200, (35, 30, 60), 10)

    # 영웅 (왼쪽) — 뒤 오라 → 캐릭터 순서
    TH = 360
    hx = 30
    hw, _ = hero_size(TH, 'right')
    hy = H - TH
    cx, cy = hx + hw // 2, hy + TH // 2
    glow(surf, cx, cy + 30, 90, (55, 75, 175), 9)
    draw_hero(surf, hx, hy, TH, 'right')

    # 적들
    draw_skeleton(surf, 500, H - 150, 3)
    draw_dark_knight(surf, 680, H - 190, 3)
    draw_slime(surf, 410, H - 110, 2, (45, 165, 70))

    # 파티클
    scatter_particles(surf, rng, 200, 70, 600, H - 100, 55,
                      [(235,185,60),(180,140,40),(220,220,255),(150,185,255),(200,100,210)])

    # 로고 (우측 정렬)
    draw_logo(surf, 0, H // 2 - 75, 32, 48, right_align_x=W - 24)

    draw_vignette(surf, W, H, 215, 0.32)
    return surf


def make_small(rng):
    """462 × 174  소형 캡슐"""
    W, H = 462, 174
    surf = pygame.Surface((W, H))
    draw_bg(surf, W, H, rng, wall_frac=0.25)

    draw_torch(surf, W // 2, 30, 0.9)

    # 영웅 (왼쪽)
    TH = 160
    hx = 10
    hw, _ = hero_size(TH, 'right')
    hy = H - TH
    cx, cy = hx + hw // 2, hy + TH // 2
    glow(surf, cx, cy + 16, 46, (55, 75, 175), 6)
    draw_hero(surf, hx, hy, TH, 'right')

    # 로고 (우측)
    f1, f2 = px(16), px(24)
    lx = hx + hw + 18
    ly = H // 2 - (f1.get_height() + 8 + f2.get_height()) // 2
    txt_glow(surf, "DUNGEON", f1, GOLD_L, GOLD_D, lx, ly)
    txt_glow(surf, "DOOR",    f2, GOLD,   GOLD_D, lx, ly + f1.get_height() + 8)

    scatter_particles(surf, rng, lx, 0, W - lx - 10, H, 18)
    draw_vignette(surf, W, H, 200, 0.28)
    return surf


def make_main(rng):
    """1232 × 706  메인 캡슐"""
    W, H = 1232, 706
    surf = pygame.Surface((W, H))
    draw_bg(surf, W, H, rng, wall_frac=0.15)

    # 다수 횃불
    for tx in [100, 380, W // 2, 850, W - 100]:
        draw_torch(surf, tx, int(H * 0.13), 1.6)

    # 천장 분위기
    glow(surf, W // 2, H // 3, 320, (28, 25, 55), 12)

    # 영웅 (좌측, 크게) — 바닥 정렬
    TH = 540
    hx = 70
    hw, _ = hero_size(TH, 'right')
    hy = H - TH
    cx, cy = hx + hw // 2, hy + TH // 2
    glow(surf, cx, cy + 40, 130, ( 60,  80, 190), 11)   # 뒤 오라(캐릭터 뒤로)
    draw_hero(surf, hx, hy, TH, 'right')

    # 보스 다크나이트 (우측)
    draw_dark_knight(surf, W - 210, H // 2 + 10, 5)

    # 스켈레톤 (중앙)
    draw_skeleton(surf, 720, H - 195, 4)

    # 슬라임 (후면, 영웅 우측 밖)
    draw_slime(surf, 580, H - 135, 3, (40, 160, 58))

    # 리퍼 (후면 우측)
    draw_reaper(surf, 940, H - 230, 3)

    # 바닥 광원
    glow(surf, cx, H - 18, 130, (55, 75, 185), 8)
    glow(surf, W - 210,    H - 18, 110, (145, 20, 200), 8)

    # 파티클
    scatter_particles(surf, rng, 100, 80, W - 200, H - 120, 130,
                      [(235,185,60),(180,140,40),(255,220,100),
                       (220,220,255),(150,185,255),(200,100,215)])

    # 로고 (좌상단) — 타이틀만 허용 (Steam 규정)
    f1, f2 = px(54), px(72)
    txt_glow(surf, "DUNGEON", f1, GOLD_L, GOLD_D, 44, 28)
    txt_glow(surf, "DOOR",    f2, GOLD,   GOLD_D, 44, 28 + f1.get_height() + 10)

    draw_vignette(surf, W, H, 225, 0.36)
    return surf


def make_vertical(rng):
    """748 × 896  수직 캡슐"""
    W, H = 748, 896
    surf = pygame.Surface((W, H))
    draw_bg(surf, W, H, rng, wall_frac=0.11)

    # 횃불 (좌우벽)
    for tx, ty, s in [(55, 95, 1.3), (W-55, 95, 1.3),
                      (55, H//2 - 20, 1.0), (W-55, H//2 - 20, 1.0)]:
        draw_torch(surf, tx, ty, s)

    # 상단 분위기
    glow(surf, W // 2, 160, 220, (38, 32, 70), 11)

    # 로고 (상단 중앙)
    f1, f2 = px(28), px(44)
    ty = 38
    txt_glow(surf, "DUNGEON", f1, GOLD_L, GOLD_D, W // 2 - f1.render("DUNGEON",True,GOLD).get_width()//2, ty)
    ty2 = ty + f1.get_height() + 10
    txt_glow(surf, "DOOR",    f2, GOLD,   GOLD_D, W // 2 - f2.render("DOOR",True,GOLD).get_width()//2, ty2)

    # 영웅 (중앙) — 뒤 오라 → 캐릭터
    TH = 430
    hw, _ = hero_size(TH, 'down')
    hx = W // 2 - hw // 2
    hy = H // 2 - TH // 2 + 40
    cx, cy = W // 2, hy + TH // 2
    glow(surf, cx, cy + 30, 130, (60, 82, 185), 11)
    draw_hero(surf, hx, hy, TH, 'down')

    # 측면 적
    draw_dark_knight(surf, W - 115, H // 2 + 55, 3)
    draw_skeleton(surf, 110, H // 2 + 35, 3)
    draw_slime(surf, W // 2 + 160, hy + TH - 80, 2, (40, 155, 65))

    # 바닥 광원
    glow(surf, W // 2, hy + TH, 80, (55, 78, 175), 8)

    # 하단 구분선 + 아이템 아이콘
    sep_y = H - 130
    pygame.draw.line(surf, (48, 45, 78), (55, sep_y), (W - 55, sep_y), 1)

    icon_font = ko(28)
    icons = [("⚔", GOLD),       ("🛡", (120, 155, 200)),
             ("⛑", GOLD_L),     ("👢", (135, 85, 38))]
    total_w = sum(icon_font.render(ic, True, cl).get_width() + 28 for ic, cl in icons)
    ix = W // 2 - total_w // 2
    for icon, col in icons:
        is2 = icon_font.render(icon, True, col)
        surf.blit(is2, (ix, sep_y + 18))
        glow(surf, ix + is2.get_width()//2, sep_y + 18 + is2.get_height()//2,
             20, col, 5)
        ix += is2.get_width() + 28

    # 파티클
    scatter_particles(surf, rng, 80, 155, W - 160, H - 200, 85,
                      [(235,185,60),(180,140,40),(200,100,215),(150,200,255)])

    draw_vignette(surf, W, H, 225, 0.32)
    return surf


def make_icon(rng):
    """512 × 512  바로가기 아이콘"""
    W = H = 512
    surf = pygame.Surface((W, H))

    # 배경 - 어두운 원형 배경
    surf.fill((4, 3, 10))
    ts = 24
    for row in range(H // ts + 2):
        for col in range(W // ts + 2):
            v = rng.randint(-2, 2)
            fc = tuple(max(0, min(255, c + v)) for c in (11, 10, 20))
            R(surf, fc, col * ts, row * ts, ts - 1, ts - 1)

    # 중앙 원형 마스크 (아이콘 느낌)
    cx, cy = W // 2, H // 2
    for r in range(220, 0, -1):
        frac = r / 220
        alpha_fade = int(255 * (1 - frac ** 3))
        dark = tuple(max(0, int(c * frac * 0.4)) for c in (40, 35, 80))
        C(surf, dark, cx, cy, r)

    # 횃불 (좌상 / 우상)
    draw_torch(surf,  80,  90, 1.2)
    draw_torch(surf, W - 80, 90, 1.2)

    # 중앙 빛 아우라
    glow(surf, cx, cy + 30, 200, (50, 40, 110), 14)
    glow(surf, cx, cy + 30, 100, (80, 70, 180),  8)
    glow(surf, cx, cy + 30,  50, (120, 110, 220), 5)

    # 로고 (상단 - 먼저 그려 위치 확보)
    f1 = px(22); f2 = px(34)
    lh = f1.get_height() + 6 + f2.get_height()
    ly = 28
    txt_glow(surf, "DUNGEON", f1, GOLD_L, GOLD_D,
             cx - f1.render("DUNGEON", True, GOLD).get_width() // 2, ly)
    txt_glow(surf, "DOOR",    f2, GOLD,   GOLD_D,
             cx - f2.render("DOOR", True, GOLD).get_width() // 2,
             ly + f1.get_height() + 6)

    # 영웅 중앙 (hero_down)
    TH = 350
    hw, _ = hero_size(TH, 'down')
    hx = cx - hw // 2
    hy = ly + lh + 14
    draw_hero(surf, hx, hy, TH, 'down')

    # 발 아래 그림자 광원
    glow(surf, cx, hy + TH - 20, 90, (60, 80, 200), 9)
    glow(surf, cx, hy + TH - 20, 40, (140, 150, 255), 5)

    # 파티클
    scatter_particles(surf, rng, 60, 100, W - 120, H - 160, 60,
                      [(235, 185, 60), (180, 140, 40), (200, 160, 255), (150, 200, 255)])

    # 비네팅 (강하게 - 원형 아이콘 느낌)
    draw_vignette(surf, W, H, 230, 0.42)
    return surf


def make_library_capsule(rng):
    """600 × 900  라이브러리 캡슐"""
    W, H = 600, 900
    surf = pygame.Surface((W, H))
    draw_bg(surf, W, H, rng, wall_frac=0.10)

    cx = W // 2

    # 횃불 (좌우 상단)
    draw_torch(surf, 55,  110, 1.2)
    draw_torch(surf, W - 55, 110, 1.2)

    # 중앙 아우라
    glow(surf, cx, H // 2 + 60, 260, (38, 30, 80), 14)
    glow(surf, cx, H // 2 + 60, 130, (65, 55, 150),  8)

    # 로고 (상단 — 먼저 레이아웃 확정)
    f1 = px(28); f2 = px(44)
    logo_h = f1.get_height() + 8 + f2.get_height()
    ly = 44
    txt_glow(surf, "DUNGEON", f1, GOLD_L, GOLD_D,
             cx - f1.render("DUNGEON", True, GOLD).get_width() // 2, ly)
    txt_glow(surf, "DOOR",    f2, GOLD,   GOLD_D,
             cx - f2.render("DOOR",    True, GOLD).get_width() // 2, ly + f1.get_height() + 8)

    # 영웅 중앙 크게
    TH = 480
    hw, _ = hero_size(TH, 'down')
    hx = cx - hw // 2
    hy = ly + logo_h + 24
    draw_hero(surf, hx, hy, TH, 'down')

    # 발 바닥 광원
    glow(surf, cx, hy + TH - 30, 110, (55, 80, 200), 10)
    glow(surf, cx, hy + TH - 30,  50, (130, 150, 255),  5)

    # 적들 (하단 좌우)
    enemy_y = hy + TH - 40
    draw_skeleton(surf,  90, enemy_y, 3)
    draw_slime(surf,    W - 90, enemy_y - 20, 2, (45, 165, 70))

    # 다크나이트 (우하단)
    draw_dark_knight(surf, W - 80, H - 100, 3)

    # 파티클
    scatter_particles(surf, rng, 40, 160, W - 80, H - 180, 70,
                      [(235, 185, 60), (180, 140, 40), (200, 160, 255), (150, 200, 255)])

    draw_vignette(surf, W, H, 230, 0.38)
    return surf


def make_library_header(rng):
    """920 × 430  라이브러리 헤더 (header_capsule과 별도 구성)"""
    W, H = 920, 430
    surf = pygame.Surface((W, H))
    draw_bg(surf, W, H, rng, wall_frac=0.22)

    # 횃불
    draw_torch(surf,  70, 85, 1.3)
    draw_torch(surf, W - 70, 85, 1.3)

    # 분위기 조명
    glow(surf, W // 2, H // 3, 220, (35, 28, 65), 11)

    # 영웅 (좌측)
    TH = 380
    hw, _ = hero_size(TH, 'right')
    hx = 24
    hy = H - TH
    glow(surf, hx + hw // 2, hy + TH // 2 + 25, 95, (55, 75, 175), 9)
    draw_hero(surf, hx, hy, TH, 'right')

    # 적들 (중앙~우측)
    draw_skeleton(surf,    520, H - 150, 3)
    draw_dark_knight(surf, 700, H - 190, 3)
    draw_slime(surf,       410, H - 108, 2, (45, 165, 70))

    # 파티클
    scatter_particles(surf, rng, 180, 60, 580, H - 90, 55,
                      [(235, 185, 60), (180, 140, 40), (220, 220, 255), (150, 185, 255)])

    # 로고 (우측 정렬)
    draw_logo(surf, 0, H // 2 - 70, 30, 46, right_align_x=W - 22)

    draw_vignette(surf, W, H, 215, 0.30)
    return surf


def make_library_hero(rng):
    """3840 × 1240  라이브러리 히어로 — 텍스트/로고 없음"""
    W, H = 3840, 1240
    surf = pygame.Surface((W, H))

    # 배경 타일 (더 촘촘하게)
    surf.fill((4, 3, 10))
    ts = 36
    for row in range(H // ts + 2):
        for col in range(W // ts + 2):
            v = rng.randint(-3, 3)
            fc = tuple(max(0, min(255, c + v)) for c in (10, 9, 18))
            R(surf, fc, col * ts, row * ts, ts - 1, ts - 1)

    # 벽 (상단)
    wh = int(H * 0.16)
    for col in range(W // ts + 2):
        v = rng.randint(-4, 4)
        wc = tuple(max(0, min(255, c + v)) for c in (22, 20, 36))
        R(surf, wc, col * ts, 0, ts - 1, wh)
    ov = pygame.Surface((W, 28), pygame.SRCALPHA)
    for y in range(28):
        a = int(180 * (1 - y / 28) ** 2)
        pygame.draw.line(ov, (0, 0, 0, a), (0, y), (W, y))
    surf.blit(ov, (0, wh - 6))

    # 횃불 — 넓은 화면에 균등 배치
    torch_xs = [120, 600, 1200, W // 2 - 200, W // 2 + 200,
                W - 1200, W - 600, W - 120]
    for tx in torch_xs:
        draw_torch(surf, tx, int(H * 0.14), 1.8)

    # 분위기 천장 광원
    for gx in [W // 4, W // 2, W * 3 // 4]:
        glow(surf, gx, H // 3, 400, (30, 25, 60), 13)

    # 바닥 어두운 그라데이션
    fg = pygame.Surface((W, 120), pygame.SRCALPHA)
    for y in range(120):
        a = int(160 * (y / 120) ** 1.5)
        pygame.draw.line(fg, (0, 0, 0, a), (0, y), (W, y))
    surf.blit(fg, (0, H - 120))

    # ── 캐릭터 배치 (안전 영역 중앙 860×380 고려) ──────────────────
    # 영웅 — 화면 중앙보다 약간 왼쪽 (뒤 오라 → 캐릭터)
    TH = 900
    hw, _ = hero_size(TH, 'right')
    hx = W // 2 - hw - 80
    hy = H - TH
    glow(surf, hx + hw // 2, hy + TH // 2 + 60, 200, (55, 75, 175), 12)
    draw_hero(surf, hx, hy, TH, 'right')

    # 다크나이트 보스 — 중앙 오른쪽
    draw_dark_knight(surf, W // 2 + 340, H - 300, 8)
    glow(surf, W // 2 + 340, H - 190, 200, (80, 18, 130), 10)

    # 리치 — 우측
    draw_reaper(surf, W * 3 // 4 + 40, H - 270, 7)

    # 스켈레톤들 — 산발적으로 (영웅과 겹치지 않게)
    draw_skeleton(surf, 820, H - 210, 5)
    draw_skeleton(surf, W * 3 // 4 + 300, H - 190, 4)

    # 슬라임들
    draw_slime(surf, W // 4, H - 160, 4, (45, 165, 70))
    draw_slime(surf, W // 4 + 300, H - 140, 3, (45, 165, 70))
    draw_slime(surf, W - 300, H - 145, 3, (45, 165, 70))

    # 좌우 원경 적들 (멀리, 작게)
    draw_skeleton(surf, 220, H - 170, 3)
    draw_dark_knight(surf, W - 250, H - 240, 4)

    # 파티클 (넓게)
    scatter_particles(surf, rng, 100, 100, W - 200, H - 150, 300,
                      [(235, 185, 60), (180, 140, 40), (255, 220, 100),
                       (200, 160, 255), (150, 190, 255), (200, 100, 215)])

    draw_vignette(surf, W, H, 220, 0.30)
    return surf


def make_library_logo(rng):
    """1280 × 720  라이브러리 로고 — 투명 배경"""
    W, H = 1280, 720
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    cx, cy = W // 2, H // 2

    # 배경 글로우 (반투명)
    for r in range(180, 0, -4):
        frac = r / 180
        a = int(110 * (1 - frac) ** 1.5)
        col = (int(30 * frac), int(20 * frac), int(60 * frac), a)
        gs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, col, (0, 0, r * 2, r * 2))
        surf.blit(gs, (cx - r, cy - r))

    # 로고 텍스트 — 크게
    f1 = px(90); f2 = px(140)
    w1 = f1.render("DUNGEON", True, GOLD).get_width()
    w2 = f2.render("DOOR",    True, GOLD).get_width()
    logo_h = f1.get_height() + 12 + f2.get_height()
    ly = cy - logo_h // 2 - 10

    # 그림자 레이어 (SRCALPHA surface에서 직접)
    for d in range(4, 0, -1):
        gs1 = f1.render("DUNGEON", True, GOLD_D)
        gs2 = f2.render("DOOR",    True, GOLD_D)
        gs1.set_alpha(max(1, 50 // d))
        gs2.set_alpha(max(1, 50 // d))
        import math
        for i in range(8):
            a = math.pi * 2 * i / 8
            ox = round(math.cos(a) * d * 2)
            oy = round(math.sin(a) * d * 2)
            surf.blit(gs1, (cx - w1 // 2 + ox, ly + oy))
            surf.blit(gs2, (cx - w2 // 2 + ox, ly + f1.get_height() + 12 + oy))

    # 메인 텍스트
    surf.blit(f1.render("DUNGEON", True, (30, 30, 30)), (cx - w1 // 2 + 4, ly + 4))
    surf.blit(f2.render("DOOR",    True, (30, 30, 30)), (cx - w2 // 2 + 4, ly + f1.get_height() + 12 + 4))
    surf.blit(f1.render("DUNGEON", True, GOLD_L), (cx - w1 // 2, ly))
    surf.blit(f2.render("DOOR",    True, GOLD),   (cx - w2 // 2, ly + f1.get_height() + 12))

    return surf


def make_trailer_thumbnail(rng):
    """1920 × 1080  예고편 섬네일 (YouTube 16:9)"""
    W, H = 1920, 1080
    surf = pygame.Surface((W, H))

    # ── 배경 ─────────────────────────────────────────────────────────
    surf.fill((3, 2, 8))
    ts = 38
    wh = int(H * 0.20)
    for row in range(H // ts + 2):
        for col in range(W // ts + 2):
            v = rng.randint(-3, 3)
            is_wall = row * ts < wh
            base = (20, 18, 35) if is_wall else (10, 9, 18)
            fc = tuple(max(0, min(255, c + v)) for c in base)
            R(surf, fc, col * ts, row * ts, ts - 1, ts - 1)

    # 벽 하단 그림자
    ov = pygame.Surface((W, 30), pygame.SRCALPHA)
    for yi in range(30):
        a = int(200 * (1 - yi / 30) ** 2)
        pygame.draw.line(ov, (0, 0, 0, a), (0, yi), (W, yi))
    surf.blit(ov, (0, wh - 6))

    # 균열 / 벽 디테일
    for _ in range(rng.randint(60, 100)):
        br = rng.randint(40, 110)
        R(surf, (br, br, min(255, br + 20)),
          rng.randint(0, W), rng.randint(0, wh - 2), 1, 1)

    # ── 분위기 조명 ────────────────────────────────────────────────
    # 중앙 천장 보랏빛
    glow(surf, W // 2, H // 3, 500, (28, 20, 65), 16)
    glow(surf, W // 2, H // 3, 250, (45, 30, 95), 10)

    # 영웅 쪽 파란 빛
    glow(surf, W // 4, H // 2, 300, (25, 40, 110), 12)

    # 보스 쪽 붉은/보라 빛
    glow(surf, W * 3 // 4, H // 2, 320, (80, 15, 110), 12)

    # ── 횃불 ────────────────────────────────────────────────────────
    for tx, ts2 in [(80, 1.6), (380, 1.3), (W // 2 - 60, 1.5),
                    (W // 2 + 60, 1.5), (W - 380, 1.3), (W - 80, 1.6)]:
        draw_torch(surf, tx, int(H * 0.17), ts2)

    # ── 바닥 안개 ───────────────────────────────────────────────────
    fg = pygame.Surface((W, 160), pygame.SRCALPHA)
    for yi in range(160):
        a = int(140 * (yi / 160) ** 1.8)
        pygame.draw.line(fg, (0, 0, 0, a), (0, yi), (W, yi))
    surf.blit(fg, (0, H - 160))

    # ── 캐릭터 ──────────────────────────────────────────────────────
    # 영웅 (좌측, 크게) — 뒤 오라 → 캐릭터
    TH = 780
    hw, _ = hero_size(TH, 'right')
    hx = int(W * 0.06)
    hy = H - TH
    hcx, hcy = hx + hw // 2, hy + TH // 2
    glow(surf, hcx, hcy + 50, 210, (55, 75, 180), 13)
    glow(surf, hcx, H - 30, 140, (50, 70, 190), 9)   # 발 아래 광원
    draw_hero(surf, hx, hy, TH, 'right')

    # 다크나이트 보스 (우측, 매우 크게)
    bkx = int(W * 0.80)
    draw_dark_knight(surf, bkx, H - 320, 9)
    glow(surf, bkx, H - 190, 260, (90, 16, 140), 12)

    # 리퍼 (중앙 오른쪽)
    draw_reaper(surf, int(W * 0.60), H - 260, 6)

    # 스켈레톤 (중앙 왼쪽, 영웅 우측 밖)
    draw_skeleton(surf, int(W * 0.46), H - 210, 5)

    # 배경 소적들 (작게, 분위기)
    draw_slime(surf, int(W * 0.35), H - 130, 3, (40, 155, 65))
    draw_slime(surf, int(W * 0.90), H - 125, 3, (40, 155, 65))
    draw_dark_knight(surf, int(W * 0.94), H - 195, 4)

    # ── 파티클 ─────────────────────────────────────────────────────
    scatter_particles(surf, rng, 100, 100, W - 200, H - 160, 220,
                      [(235, 185, 60), (180, 140, 40), (255, 220, 100),
                       (200, 160, 255), (150, 185, 255), (200, 100, 215),
                       (255, 80, 80)])

    # ── 로고 ────────────────────────────────────────────────────────
    f1 = px(72); f2 = px(108)
    w1 = f1.render("DUNGEON", True, GOLD).get_width()
    w2 = f2.render("DOOR",    True, GOLD).get_width()
    logo_cx = W // 2
    ly = 32
    txt_glow(surf, "DUNGEON", f1, GOLD_L, GOLD_D, logo_cx - w1 // 2, ly)
    ly2 = ly + f1.get_height() + 10
    txt_glow(surf, "DOOR",    f2, GOLD,   GOLD_D, logo_cx - w2 // 2, ly2)

    # 부제
    fs = ko(34)
    sub = "로그라이크 던전 탐험"
    sw = fs.render(sub, True, (200, 205, 240)).get_width()
    txt_outline(surf, sub, fs, (200, 205, 240), (8, 6, 20),
                logo_cx - sw // 2, ly2 + f2.get_height() + 14)

    # ── 예고편 배지 ─────────────────────────────────────────────────
    badge_f  = ko(30)
    badge_s  = badge_f.render("▶  예 고 편", True, (255, 255, 255))
    bw2, bh2 = badge_s.get_width() + 36, badge_s.get_height() + 16
    bx2 = logo_cx - bw2 // 2
    by2 = ly2 + f2.get_height() + 14 + fs.get_height() + 22
    pygame.draw.rect(surf, (160, 30, 30), (bx2, by2, bw2, bh2), border_radius=6)
    pygame.draw.rect(surf, (220, 60, 60), (bx2, by2, bw2, bh2), 2, border_radius=6)
    surf.blit(badge_s, (bx2 + 18, by2 + 8))

    # ── 시네마틱 레터박스 (위아래 얇은 검은 띠) ────────────────────
    bar_h = 38
    R(surf, (0, 0, 0), 0,      0,     W, bar_h)
    R(surf, (0, 0, 0), 0, H - bar_h, W, bar_h)

    # ── 비네팅 ──────────────────────────────────────────────────────
    draw_vignette(surf, W, H, 230, 0.38)
    return surf


# ─── 메인 ─────────────────────────────────────────────────────────────
def main():
    specs = [
        ('header_capsule.png',      920,  430,  make_header),
        ('small_capsule.png',       462,  174,  make_small),
        ('main_capsule.png',       1232,  706,  make_main),
        ('vertical_capsule.png',    748,  896,  make_vertical),
        ('icon_512.png',            512,  512,  make_icon),
        # 라이브러리 에셋
        ('library_capsule.png',     600,  900,  make_library_capsule),
        ('library_header.png',      920,  430,  make_library_header),
        ('library_hero.png',       3840, 1240,  make_library_hero),
        ('library_logo.png',       1280,  720,  make_library_logo),
        ('trailer_thumbnail.png',  1920, 1080,  make_trailer_thumbnail),
    ]

    rng = random.Random(42)
    for fname, ew, eh, fn in specs:
        print(f'  {fname} ({ew}×{eh}) ... ', end='', flush=True)
        surf = fn(rng)
        assert surf.get_size() == (ew, eh), f"size mismatch: {surf.get_size()}"
        path = os.path.join(OUT, fname)
        pygame.image.save(surf, path)
        print('saved')

    print(f'\n완료! → {OUT}')
    pygame.quit()


if __name__ == '__main__':
    main()

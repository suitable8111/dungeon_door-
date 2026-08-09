"""도전과제 아이콘 생성기 — 256×256 달성(컬러) + 미달성(회색) 세트.

게임 픽셀아트 톤에 맞춰 pygame 프리미티브로 심볼을 그린다. 각 업적마다
 assets/steam/achievements/<API>.png        (달성, 컬러)
 assets/steam/achievements/<API>_locked.png  (미달성, 회색+어둡게)
그리고 미리보기 시트 _preview_new.png / _preview_all.png 를 저장한다.

사용: python3 tools/make_achievement_icons.py
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import pygame  # noqa: E402
pygame.init()

OUT = os.path.join(BASE, "assets", "steam", "achievements")
os.makedirs(OUT, exist_ok=True)
_PF = os.path.join(BASE, "assets", "fonts", "PressStart2P-Regular.ttf")
S = 256

# ── 팔레트 ─────────────────────────────────────────────────────────
RED    = (226, 74, 62)
DKRED  = (150, 40, 44)
GOLD   = (255, 200, 92)
STEEL  = (196, 206, 222)
PURPLE = (176, 118, 232)
GREEN  = (120, 224, 148)
BLUE   = (110, 190, 255)
TEAL   = (96, 214, 210)
ORANGE = (255, 150, 74)
STONE  = (176, 168, 150)
CYAN   = (140, 236, 255)
PARCH  = (232, 210, 150)
BRONZE = (208, 142, 92)


def font(sz):
    return pygame.font.Font(_PF, sz)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ── 배경(라운드 패널 + 방사 그라디언트 + 테두리) ────────────────────
def make_bg(accent):
    surf = pygame.Surface((S, S), pygame.SRCALPHA)
    inner = _lerp((16, 18, 30), accent, 0.10)
    outer = (8, 9, 16)
    cx = cy = S / 2
    maxd = S * 0.62
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - cx, y - cy) / maxd
            d = max(0.0, min(1.0, d))
            surf.set_at((x, y), _lerp(inner, outer, d) + (255,))
    # 라운드 마스크
    mask = pygame.Surface((S, S), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (6, 6, S - 12, S - 12), border_radius=34)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    # 상단 하이라이트
    hl = pygame.Surface((S, S), pygame.SRCALPHA)
    pygame.draw.ellipse(hl, (255, 255, 255, 26), (24, 12, S - 48, 90))
    surf.blit(hl, (0, 0))
    # 테두리 2겹
    pygame.draw.rect(surf, _lerp(accent, (255, 255, 255), 0.25),
                     (6, 6, S - 12, S - 12), 5, border_radius=34)
    pygame.draw.rect(surf, (0, 0, 0, 120), (6, 6, S - 12, S - 12), 1, border_radius=34)
    # 모서리 리벳
    for (rx, ry) in ((26, 26), (S - 26, 26), (26, S - 26), (S - 26, S - 26)):
        pygame.draw.circle(surf, _lerp(accent, (255, 255, 255), 0.4), (rx, ry), 4)
        pygame.draw.circle(surf, (0, 0, 0, 90), (rx, ry), 4, 1)
    return surf


def outline_poly(surf, pts, col, oc=(12, 12, 18), w=3):
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, oc, pts, w)


# ── 심볼 프리미티브 ─────────────────────────────────────────────────
def sword(surf, cx, cy, ln, col, ang=0.0):
    """중심(cx,cy) 기준 길이 ln 검 (ang 라디안 회전). 손잡이 아래쪽."""
    ca, sa = math.cos(ang), math.sin(ang)

    def R(px, py):
        return (cx + px * ca - py * sa, cy + px * sa + py * ca)
    half = ln / 2
    blade = [R(-6, -half), R(6, -half + 4), R(6, half - 34), R(-6, half - 34)]
    tip = [R(-6, -half), R(6, -half + 4), R(0, -half - 12)]
    outline_poly(surf, blade, col)
    outline_poly(surf, tip, _lerp(col, (255, 255, 255), 0.4))
    # 가드
    guard = [R(-20, half - 34), R(20, half - 34), R(20, half - 26), R(-20, half - 26)]
    outline_poly(surf, guard, GOLD)
    # 손잡이
    grip = [R(-4, half - 26), R(4, half - 26), R(4, half - 4), R(-4, half - 4)]
    outline_poly(surf, grip, (120, 84, 54))
    pygame.draw.circle(surf, GOLD, (int(R(0, half - 2)[0]), int(R(0, half - 2)[1])), 6)


def crossed_swords(surf, cx, cy, col):
    sword(surf, cx, cy, 150, col, ang=math.radians(35))
    sword(surf, cx, cy, 150, col, ang=math.radians(-35))


def blood_drop(surf, cx, cy, col):
    pts = [(cx, cy - 52), (cx + 34, cy + 20), (cx + 20, cy + 44),
           (cx - 20, cy + 44), (cx - 34, cy + 20)]
    outline_poly(surf, pts, col)
    pygame.draw.circle(surf, _lerp(col, (255, 255, 255), 0.5), (cx - 10, cy + 10), 7)


def horned_skull(surf, cx, cy, col):
    # 뿔
    for sgn in (-1, 1):
        h = [(cx + sgn * 28, cy - 20), (cx + sgn * 62, cy - 66),
             (cx + sgn * 50, cy - 22), (cx + sgn * 40, cy - 8)]
        outline_poly(surf, h, _lerp(col, (240, 235, 220), 0.3))
    # 두개골
    pygame.draw.circle(surf, col, (cx, cy - 4), 46)
    pygame.draw.circle(surf, (12, 12, 18), (cx, cy - 4), 46, 3)
    jaw = [(cx - 30, cy + 24), (cx + 30, cy + 24), (cx + 22, cy + 52), (cx - 22, cy + 52)]
    outline_poly(surf, jaw, col)
    # 눈/코
    pygame.draw.circle(surf, (16, 14, 20), (cx - 18, cy - 6), 12)
    pygame.draw.circle(surf, (16, 14, 20), (cx + 18, cy - 6), 12)
    pygame.draw.polygon(surf, (16, 14, 20),
                        [(cx, cy + 4), (cx - 7, cy + 18), (cx + 7, cy + 18)])
    for i in range(-2, 3):
        pygame.draw.line(surf, (16, 14, 20), (cx + i * 11, cy + 24), (cx + i * 11, cy + 50), 2)


def heart_plus(surf, cx, cy, col):
    r = 30
    pygame.draw.circle(surf, col, (cx - 20, cy - 14), r)
    pygame.draw.circle(surf, col, (cx + 20, cy - 14), r)
    pts = [(cx - 48, cy - 2), (cx + 48, cy - 2), (cx, cy + 58)]
    pygame.draw.polygon(surf, col, pts)
    # 외곽선
    pygame.draw.circle(surf, (12, 12, 18), (cx - 20, cy - 14), r, 3)
    pygame.draw.circle(surf, (12, 12, 18), (cx + 20, cy - 14), r, 3)
    pygame.draw.lines(surf, (12, 12, 18), False,
                      [(cx - 47, cy - 8), (cx, cy + 58), (cx + 47, cy - 8)], 3)
    # 십자(부활)
    pygame.draw.rect(surf, (255, 255, 255), (cx - 6, cy - 22, 12, 44), border_radius=3)
    pygame.draw.rect(surf, (255, 255, 255), (cx - 22, cy - 6, 44, 12), border_radius=3)


def clock(surf, cx, cy, col):
    pygame.draw.circle(surf, _lerp(col, (255, 255, 255), 0.15), (cx, cy), 54)
    pygame.draw.circle(surf, (16, 18, 28), (cx, cy), 54, 5)
    pygame.draw.circle(surf, (16, 18, 28), (cx, cy), 46, 2)
    for i in range(12):
        a = math.radians(i * 30)
        x1 = cx + math.cos(a) * 40; y1 = cy + math.sin(a) * 40
        x2 = cx + math.cos(a) * 46; y2 = cy + math.sin(a) * 46
        pygame.draw.line(surf, (16, 18, 28), (x1, y1), (x2, y2), 3)
    pygame.draw.line(surf, (16, 18, 28), (cx, cy), (cx, cy - 30), 5)
    pygame.draw.line(surf, (16, 18, 28), (cx, cy), (cx + 24, cy + 6), 4)
    pygame.draw.circle(surf, (16, 18, 28), (cx, cy), 6)


def scroll_icon(surf, cx, cy, col):
    w, h = 96, 116
    body = pygame.Rect(cx - w // 2, cy - h // 2 + 8, w, h - 16)
    pygame.draw.rect(surf, col, body, border_radius=6)
    pygame.draw.rect(surf, (120, 96, 48), body, 3, border_radius=6)
    # 말린 상하단
    for oy in (body.top - 8, body.bottom - 8):
        pygame.draw.rect(surf, _lerp(col, (150, 120, 60), 0.5),
                         (body.left - 6, oy, w + 12, 16), border_radius=8)
        pygame.draw.rect(surf, (120, 96, 48), (body.left - 6, oy, w + 12, 16), 3, border_radius=8)
    # 글줄
    for i in range(4):
        yy = body.top + 20 + i * 16
        pygame.draw.line(surf, (110, 90, 60), (body.left + 14, yy), (body.right - 14, yy), 3)
    # 봉인
    pygame.draw.circle(surf, RED, (cx, body.bottom - 6), 13)
    pygame.draw.circle(surf, (12, 12, 18), (cx, body.bottom - 6), 13, 2)


def stairs(surf, cx, cy, col):
    step = 26
    x = cx - 66; y = cy - 52
    for i in range(4):
        r = pygame.Rect(x, y + i * step, 132 - i * 0, step)
        pygame.draw.rect(surf, _lerp(col, (0, 0, 0), i * 0.12), (x + i * 22, y + i * step, 132 - i * 44 + 44, step))
        pygame.draw.rect(surf, (16, 16, 22), (x + i * 22, y + i * step, 132 - i * 44 + 44, step), 3)
    # 하강 화살표
    pygame.draw.polygon(surf, GOLD, [(cx + 44, cy - 30), (cx + 44, cy + 6),
                                     (cx + 58, cy + 6), (cx + 40, cy + 34),
                                     (cx + 22, cy + 6), (cx + 36, cy + 6),
                                     (cx + 36, cy - 30)])


def diamond_aura(surf, cx, cy, col):
    for i, rr in enumerate((66, 54)):
        a = 90 - i * 40
        ring = pygame.Surface((S, S), pygame.SRCALPHA)
        pygame.draw.circle(ring, col + (a,), (cx, cy), rr, 6)
        surf.blit(ring, (0, 0))
    d = [(cx, cy - 46), (cx + 34, cy), (cx, cy + 46), (cx - 34, cy)]
    outline_poly(surf, d, _lerp(col, (255, 255, 255), 0.3))
    pygame.draw.polygon(surf, (255, 255, 255, 180), [(cx, cy - 46), (cx + 14, cy - 8), (cx - 14, cy - 8)])


def hammer(surf, cx, cy, col):
    # 자루
    pygame.draw.line(surf, (150, 108, 60), (cx - 34, cy + 54), (cx + 26, cy - 20), 12)
    pygame.draw.line(surf, (100, 72, 40), (cx - 34, cy + 54), (cx + 26, cy - 20), 2)
    # 머리
    head = pygame.Rect(cx + 4, cy - 58, 66, 40)
    pygame.draw.rect(surf, col, head, border_radius=6)
    pygame.draw.rect(surf, (16, 16, 22), head, 3, border_radius=6)
    pygame.draw.rect(surf, _lerp(col, (255, 255, 255), 0.4), (head.left + 4, head.top + 4, 12, head.height - 8))
    # 모루
    an = pygame.Rect(cx - 62, cy + 44, 74, 22)
    pygame.draw.rect(surf, STEEL, an, border_radius=4)
    pygame.draw.rect(surf, (16, 16, 22), an, 3, border_radius=4)


def coins(surf, cx, cy, col):
    for i, (ox, oy) in enumerate(((-34, 30), (0, 18), (34, 30))):
        for k in range(3):
            e = pygame.Rect(cx + ox - 26, cy + oy - k * 16 - 12, 52, 24)
            pygame.draw.ellipse(surf, _lerp(col, (0, 0, 0), 0.15), e)
            pygame.draw.ellipse(surf, col, (e.x, e.y - 3, e.w, e.h))
            pygame.draw.ellipse(surf, (150, 110, 30), (e.x, e.y - 3, e.w, e.h), 2)
    s = font(20).render("$", True, (150, 110, 30))
    surf.blit(s, (cx - s.get_width() // 2, cy - 4))


def flame(surf, cx, cy, col):
    outer = [(cx, cy - 60), (cx + 40, cy - 6), (cx + 30, cy + 44),
             (cx, cy + 54), (cx - 30, cy + 44), (cx - 40, cy - 6)]
    outline_poly(surf, outer, col)
    inner = [(cx, cy - 26), (cx + 20, cy + 6), (cx + 12, cy + 38),
             (cx - 12, cy + 38), (cx - 20, cy + 6)]
    pygame.draw.polygon(surf, GOLD, inner)
    pygame.draw.polygon(surf, (255, 245, 200), [(cx, cy + 6), (cx + 9, cy + 30), (cx - 9, cy + 30)])


def burst(surf, cx, cy, col):
    pts = []
    for i in range(16):
        a = math.radians(i * 22.5)
        r = 66 if i % 2 == 0 else 30
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    outline_poly(surf, pts, col)
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 16)
    pygame.draw.circle(surf, col, (cx, cy), 16, 3)


def chevrons(surf, cx, cy, col):
    for i, oy in enumerate((-6, 22, 50)):
        c = _lerp(col, (255, 255, 255), 0.2 - i * 0.06)
        pts = [(cx - 46, cy - 40 + oy), (cx, cy - 8 + oy), (cx + 46, cy - 40 + oy),
               (cx + 46, cy - 24 + oy), (cx, cy + 8 + oy), (cx - 46, cy - 24 + oy)]
        outline_poly(surf, pts, c)


def tombstone(surf, cx, cy, col):
    body = pygame.Rect(cx - 46, cy - 40, 92, 96)
    pygame.draw.rect(surf, col, body, border_top_left_radius=44, border_top_right_radius=44)
    pygame.draw.rect(surf, (16, 16, 22), body, 3, border_top_left_radius=44, border_top_right_radius=44)
    # RIP
    r = font(18).render("RIP", True, (70, 72, 84))
    surf.blit(r, (cx - r.get_width() // 2, cy - 20))
    # 잔디
    pygame.draw.rect(surf, GREEN, (cx - 66, cy + 52, 132, 12), border_radius=6)


def combo_blades(surf, cx, cy, col):
    for i in range(3):
        a0 = math.radians(-40 + i * 40)
        arc = pygame.Rect(cx - 70 + i * 8, cy - 70 + i * 8, 140 - i * 16, 140 - i * 16)
        pygame.draw.arc(surf, _lerp(col, (255, 255, 255), 0.1 * i),
                        arc, a0, a0 + math.radians(90), 5)
    sword(surf, cx, cy, 120, col, ang=math.radians(20))


def sprout(surf, cx, cy, col):
    soil = pygame.Rect(cx - 42, cy + 28, 84, 30)
    pygame.draw.rect(surf, (120, 84, 54), soil, border_radius=6)
    pygame.draw.rect(surf, (16, 16, 22), soil, 3, border_radius=6)
    pygame.draw.line(surf, _lerp(col, (0, 0, 0), 0.15), (cx, cy + 30), (cx, cy - 6), 6)
    for sgn in (-1, 1):
        leaf = [(cx, cy + 2), (cx + sgn * 36, cy - 16), (cx + sgn * 10, cy - 30), (cx, cy - 14)]
        outline_poly(surf, leaf, col)
    pygame.draw.circle(surf, _lerp(col, (255, 255, 255), 0.35), (cx, cy - 16), 8)


def fish_sym(surf, cx, cy, col):
    body = [(cx - 44, cy), (cx - 6, cy - 26), (cx + 30, cy - 16),
            (cx + 42, cy), (cx + 30, cy + 16), (cx - 6, cy + 26)]
    outline_poly(surf, body, col)
    tail = [(cx - 44, cy), (cx - 72, cy - 22), (cx - 62, cy), (cx - 72, cy + 22)]
    outline_poly(surf, tail, _lerp(col, (255, 255, 255), 0.2))
    pygame.draw.polygon(surf, _lerp(col, (0, 0, 0), 0.18),
                        [(cx - 2, cy - 24), (cx + 16, cy - 42), (cx + 18, cy - 20)])
    pygame.draw.circle(surf, (255, 255, 255), (cx + 22, cy - 4), 6)
    pygame.draw.circle(surf, (16, 16, 22), (cx + 22, cy - 4), 3)


def egg(surf, cx, cy, col):
    pygame.draw.arc(surf, (150, 110, 60), (cx - 54, cy + 4, 108, 56),
                    math.radians(178), math.radians(362), 9)
    pygame.draw.ellipse(surf, col, (cx - 27, cy - 42, 54, 70))
    pygame.draw.ellipse(surf, (16, 16, 22), (cx - 27, cy - 42, 54, 70), 3)
    hl = pygame.Surface((S, S), pygame.SRCALPHA)
    pygame.draw.ellipse(hl, (255, 255, 255, 120), (cx - 16, cy - 32, 16, 22))
    surf.blit(hl, (0, 0))


def cottage(surf, cx, cy, col):
    wall = pygame.Rect(cx - 42, cy - 4, 84, 56)
    pygame.draw.rect(surf, col, wall)
    pygame.draw.rect(surf, (16, 16, 22), wall, 3)
    outline_poly(surf, [(cx - 54, cy - 4), (cx, cy - 52), (cx + 54, cy - 4)], RED)
    door = pygame.Rect(cx - 11, cy + 20, 22, 32)
    pygame.draw.rect(surf, (120, 84, 54), door)
    pygame.draw.rect(surf, (16, 16, 22), door, 2)
    pygame.draw.rect(surf, GOLD, (cx - 32, cy + 8, 15, 15))
    pygame.draw.rect(surf, GOLD, (cx + 17, cy + 8, 15, 15))
    pygame.draw.rect(surf, (16, 16, 22), (cx - 32, cy + 8, 15, 15), 2)
    pygame.draw.rect(surf, (16, 16, 22), (cx + 17, cy + 8, 15, 15), 2)


def medal_star(surf, cx, cy, col):
    pygame.draw.polygon(surf, RED, [(cx - 18, cy + 16), (cx - 4, cy + 16), (cx - 11, cy + 54)])
    pygame.draw.polygon(surf, DKRED, [(cx + 18, cy + 16), (cx + 4, cy + 16), (cx + 11, cy + 54)])
    pygame.draw.circle(surf, col, (cx, cy - 8), 42)
    pygame.draw.circle(surf, (16, 16, 22), (cx, cy - 8), 42, 4)
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        r = 26 if i % 2 == 0 else 11
        pts.append((cx + math.cos(a) * r, cy - 8 + math.sin(a) * r))
    outline_poly(surf, pts, _lerp(col, (255, 255, 255), 0.45))


# ── 업적 심볼 매핑 ──────────────────────────────────────────────────
def combo_two_swords_skull(surf, cx, cy, col):
    horned_skull(surf, cx, cy - 6, col)
    sword(surf, cx - 66, cy + 40, 92, STEEL, ang=math.radians(50))
    sword(surf, cx + 66, cy + 40, 92, STEEL, ang=math.radians(-50))


def skull_sword(surf, cx, cy, col):
    horned_skull(surf, cx, cy - 8, col)
    sword(surf, cx, cy + 46, 96, GOLD, ang=0)


ICONS = [
    # ── 협동(신규 8) ──
    ("ACH_COOP_KILLS_100", BLUE,   "100", crossed_swords),
    ("ACH_REVIVE",         GREEN,  "",    heart_plus),
    ("ACH_REVIVE_10",      GREEN,  "10",  heart_plus),
    ("ACH_COOP_1H",        BLUE,   "1H",  clock),
    ("ACH_COOP_3H",        TEAL,   "3H",  clock),
    ("ACH_COOP_5H",        GOLD,   "5H",  clock),
    ("ACH_COOP_QUEST",     PARCH,  "",    scroll_icon),
    ("ACH_COOP_BOSS",      PURPLE, "",    combo_two_swords_skull),
    # ── 기존 16 ──
    ("ACH_FIRST_BLOOD",    RED,    "",    blood_drop),
    ("ACH_KILLS_500",      RED,    "500", crossed_swords),
    ("ACH_ELITE_25",       PURPLE, "25",  diamond_aura),
    ("ACH_BOSS_10",        DKRED,  "10",  horned_skull),
    ("ACH_FLOOR_5",        STONE,  "5",   stairs),
    ("ACH_FLOOR_10",       STONE,  "10",  stairs),
    ("ACH_FLOOR_25",       STONE,  "25",  stairs),
    ("ACH_FLOOR_50",       GOLD,   "50",  stairs),
    ("ACH_FIRST_BOSS",     DKRED,  "",    skull_sword),
    ("ACH_COMBO_15",       ORANGE, "15",  combo_blades),
    ("ACH_LEVEL_20",       GOLD,   "20",  chevrons),
    ("ACH_ENHANCE_10",     STEEL,  "10",  hammer),
    ("ACH_RICH",           GOLD,   "",    coins),
    ("ACH_BURNING",        ORANGE, "",    flame),
    ("ACH_ULTIMATE",       CYAN,   "",    burst),
    ("ACH_DIE",            STONE,  "",    tombstone),
    # ── 신규 14: 레벨 심화 / 심층 / 생활 ──
    ("ACH_LEVEL_40",       BRONZE, "40",  chevrons),
    ("ACH_LEVEL_60",       STEEL,  "60",  chevrons),
    ("ACH_LEVEL_80",       GOLD,   "80",  chevrons),
    ("ACH_LEVEL_99",       GOLD,   "99",  medal_star),
    ("ACH_FLOOR_100",      STONE,  "100", stairs),
    ("ACH_FLOOR_250",      TEAL,   "250", stairs),
    ("ACH_FLOOR_500",      PURPLE, "500", stairs),
    ("ACH_FLOOR_999",      RED,    "999", stairs),
    ("ACH_FARM_FIRST",     GREEN,  "",    sprout),
    ("ACH_FARM_100",       GREEN,  "100", sprout),
    ("ACH_FISH_FIRST",     TEAL,   "",    fish_sym),
    ("ACH_FISH_50",        TEAL,   "50",  fish_sym),
    ("ACH_RANCH_FIRST",    PARCH,  "",    egg),
    ("ACH_LIFE_MASTER",    GREEN,  "",    cottage),
]

NEW_KEYS = {i[0] for i in ICONS[:8]}
LIFE_KEYS = {i[0] for i in ICONS[-14:]}


def draw_icon(api, accent, num, sym):
    surf = make_bg(accent)
    cy = 120 if num else 128
    sym(surf, S // 2, cy, accent)
    if num:
        f = font(30 if len(num) <= 2 else 24)
        badge = f.render(num, True, (255, 255, 255))
        bw, bh = badge.get_width() + 22, badge.get_height() + 12
        bx, by = (S - bw) // 2, S - bh - 16
        pill = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(pill, (10, 12, 20, 230), (0, 0, bw, bh), border_radius=bh // 2)
        pygame.draw.rect(pill, _lerp(accent, (255, 255, 255), 0.2),
                         (0, 0, bw, bh), 2, border_radius=bh // 2)
        surf.blit(pill, (bx, by))
        surf.blit(badge, (bx + 11, by + 5))
    return surf


def make_locked(color_surf):
    g = pygame.transform.grayscale(color_surf)
    g.fill((120, 120, 130), special_flags=pygame.BLEND_RGB_MULT)   # 어둡게
    # 자물쇠
    cx, cy = S // 2, S // 2 + 4
    pygame.draw.arc(g, (150, 150, 160), (cx - 24, cy - 40, 48, 48),
                    math.radians(20), math.radians(160), 8)
    body = pygame.Rect(cx - 30, cy - 16, 60, 48)
    pygame.draw.rect(g, (170, 170, 180), body, border_radius=8)
    pygame.draw.rect(g, (60, 60, 68), body, 3, border_radius=8)
    pygame.draw.circle(g, (60, 60, 68), (cx, cy + 4), 6)
    pygame.draw.rect(g, (60, 60, 68), (cx - 3, cy + 4, 6, 16))
    return g


def contact_sheet(items, cols=4, pad=18, label=True):
    rows = (len(items) + cols - 1) // cols
    lh = 26 if label else 0
    cw = S + pad
    ch = S + pad + lh
    sheet = pygame.Surface((cols * cw + pad, rows * ch + pad), pygame.SRCALPHA)
    sheet.fill((22, 24, 34, 255))
    lf = font(9)
    for i, (api, surf) in enumerate(items):
        r, c = divmod(i, cols)
        x = pad + c * cw; y = pad + r * ch
        sheet.blit(surf, (x, y))
        if label:
            t = lf.render(api.replace("ACH_", ""), True, (210, 214, 226))
            sheet.blit(t, (x + (S - t.get_width()) // 2, y + S + 6))
    return sheet


def run():
    color_items = []
    new_items = []
    for api, accent, num, sym in ICONS:
        ci = draw_icon(api, accent, num, sym)
        li = make_locked(ci)
        pygame.image.save(ci, os.path.join(OUT, f"{api}.png"))
        pygame.image.save(li, os.path.join(OUT, f"{api}_locked.png"))
        color_items.append((api, ci))
        if api in NEW_KEYS:
            new_items.append((api, ci))
    life_items = [(api, ci) for api, ci in color_items if api in LIFE_KEYS]
    pygame.image.save(contact_sheet(new_items, cols=4),
                      os.path.join(OUT, "_preview_new.png"))
    pygame.image.save(contact_sheet(life_items, cols=4),
                      os.path.join(OUT, "_preview_life.png"))
    pygame.image.save(contact_sheet(color_items, cols=4),
                      os.path.join(OUT, "_preview_all.png"))
    # 미달성(회색) 미리보기도
    locked_new = [(api, make_locked(ci)) for api, ci in new_items]
    pygame.image.save(contact_sheet(locked_new, cols=4),
                      os.path.join(OUT, "_preview_new_locked.png"))
    print(f"OK — {len(ICONS)} icons ×2 → {OUT}")
    print("preview: _preview_new.png / _preview_new_locked.png / _preview_all.png")


if __name__ == "__main__":
    run()

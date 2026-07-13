"""마인크래프트 풍 블록 적/보스 스프라이트.

각 적 key를 아키타입(archetype)+옵션에 매핑한다. 시그니처는 기존과 동일:
    fn(surf, x, y, col, t)     # col=enemy.color, t=ms
보스는 game._draw_enemy가 colorkey 서피스에 그린 뒤 2배 확대하므로,
여기서는 불투명 블록만 쓰고 per-pixel alpha에 의존하지 않는다.
"""
import math
import pygame
from entities.mc_art import U, L, D, B, bob_offset, checker, eyes

_BONE = (228, 226, 214)
_BONE_D = (150, 148, 138)


# ══════════════════════════════════════════════════════════════════════
#  아키타입
# ══════════════════════════════════════════════════════════════════════
def _weapon(s, x, y, gx, oy, kind, side=1):
    """오른손(side=1) 무기 블록 그리기. gx=손 위치."""
    if kind == 'sword':
        B(s, x, y, gx, 4 + oy, (200, 205, 215), 1, 5)
        B(s, x, y, gx - 1, 8 + oy, (150, 110, 60), 3, 1)
    elif kind == 'axe':
        B(s, x, y, gx, 5 + oy, (110, 80, 46), 1, 5)
        B(s, x, y, gx + 1, 5 + oy, (190, 195, 205), 2, 2)
    elif kind == 'mace':
        B(s, x, y, gx, 5 + oy, (110, 80, 46), 1, 5)
        B(s, x, y, gx, 4 + oy, (150, 150, 160), 2, 2)
    elif kind == 'spear':
        B(s, x, y, gx, 2 + oy, (140, 100, 56), 1, 11)
        B(s, x, y, gx, 1 + oy, (200, 205, 215))
    elif kind == 'whip':
        for i, gy in enumerate((6, 8, 10)):
            B(s, x, y, gx + (i % 2), gy + oy, (90, 60, 40))
    elif kind == 'scythe':
        B(s, x, y, gx, 2 + oy, (90, 70, 50), 1, 10)
        B(s, x, y, gx - 1, 2 + oy, (200, 205, 215), 2, 1)
    elif kind == 'dagger':
        B(s, x, y, gx, 6 + oy, (200, 205, 215), 1, 3)
        B(s, x, y, gx, 9 + oy, (120, 90, 50))


def mc_humanoid(s, x, y, col, t, skin=(150, 190, 110), helmet=None, horns=False,
                weapon=None, shield=False, big=False, hood=None,
                eye=(255, 225, 70), gold=False, tail=False):
    T = t
    oy = int(bob_offset(T, 2.4, 0.8))          # 그리드 단위가 아닌 px지만 근사로 블록 오프셋
    boy = 0 if abs(oy) < 1 else (1 if oy > 0 else -1)
    dark = D(col, 30)
    skin_d = D(skin, 30)
    # 다리 (고정)
    pants = D(col, 55)
    for gx in (5, 6, 9, 10):
        B(s, x, y, gx, 13, pants, 1, 2)
        B(s, x, y, gx, 15, D(pants, 30))       # 발
    # 몸통
    checker(s, x, y, 5, 7 + boy, 6, 5, col, dark)
    # 팔
    for gx in (3, 12):
        B(s, x, y, gx, 7 + boy, dark, 1, 3)
        B(s, x, y, gx, 10 + boy, skin)         # 손
    if big:                                     # 어깨 확장
        B(s, x, y, 4, 7 + boy, col); B(s, x, y, 11, 7 + boy, col)
    # 머리
    hd = hood
    for gy in range(2, 7):
        for gx in range(5, 11):
            B(s, x, y, gx, gy + boy, skin)
    B(s, x, y, 7, 6 + boy, skin_d); B(s, x, y, 8, 6 + boy, skin_d)   # 턱
    if hd:                                       # 후드로 얼굴 상단 덮기
        for gx in range(5, 11):
            B(s, x, y, gx, 2 + boy, hd); B(s, x, y, gx, 3 + boy, hd)
        B(s, x, y, 5, 4 + boy, hd); B(s, x, y, 10, 4 + boy, hd)
        for gy in range(4, 6):                   # 얼굴 그림자
            for gx in range(6, 10):
                B(s, x, y, gx, gy + boy, D(skin, 70))
    eyes(s, x, y, 6, 9, 4 + boy, eye)
    if helmet:
        for gx in range(5, 11):
            B(s, x, y, gx, 2 + boy, helmet)
        B(s, x, y, 5, 3 + boy, helmet); B(s, x, y, 10, 3 + boy, helmet)
        B(s, x, y, 7, 3 + boy, D(helmet, 40), 2, 1)   # 눈틈
    if horns:
        B(s, x, y, 4, 1 + boy, _BONE); B(s, x, y, 11, 1 + boy, _BONE)
        B(s, x, y, 4, 2 + boy, _BONE_D); B(s, x, y, 11, 2 + boy, _BONE_D)
    if gold:
        B(s, x, y, 2, 10 + boy, (240, 200, 70), 2, 3)   # 금자루
        B(s, x, y, 2, 9 + boy, (200, 160, 40), 2, 1)
        B(s, x, y, 7, 8 + boy, (255, 220, 90))          # 벨트 금장
    if tail:
        B(s, x, y, 11, 12, dark); B(s, x, y, 12, 13, dark)
    if weapon:
        _weapon(s, x, y, 13, boy, weapon)
    if shield:
        B(s, x, y, 2, 7 + boy, (150, 120, 70), 2, 4)
        B(s, x, y, 2, 8 + boy, (190, 160, 90), 2, 1)


def mc_skeleton(s, x, y, col, t, weapon=None, shield=False, bow=False, tint=None):
    T = t
    boy = 1 if bob_offset(T, 2.0, 1.0) > 0.3 else 0
    b, bd = _BONE, _BONE_D
    # 다리 뼈
    for gx in (6, 9):
        B(s, x, y, gx, 12, b, 1, 3)
        B(s, x, y, gx, 15, bd)
    # 갈비뼈
    for gy in range(7 + boy, 12):
        B(s, x, y, 6, gy, b); B(s, x, y, 9, gy, b)
    for gy in (8, 10):
        B(s, x, y, 7, gy + boy, bd, 2, 1)
    B(s, x, y, 7, 7 + boy, b, 2, 1)               # 쇄골
    # 팔
    B(s, x, y, 4, 7 + boy, b, 1, 3); B(s, x, y, 11, 7 + boy, b, 1, 3)
    # 두개골
    for gy in range(2, 7):
        for gx in range(5, 11):
            B(s, x, y, gx, gy + boy, b)
    B(s, x, y, 6, 4 + boy, (20, 20, 24)); B(s, x, y, 9, 4 + boy, (20, 20, 24))  # 눈구멍
    B(s, x, y, 7, 6 + boy, bd); B(s, x, y, 8, 6 + boy, bd)                       # 이빨턱
    if tint:                                       # 색 accent (머리 위)
        B(s, x, y, 5, 2 + boy, tint, 6, 1)
    if bow:
        for gy in range(3, 12):
            B(s, x, y, 13, gy + boy, (140, 100, 56))
        B(s, x, y, 12, 7 + boy, (220, 220, 230))   # 시위
    elif weapon:
        _weapon(s, x, y, 13, boy, weapon)
    if shield:
        B(s, x, y, 2, 7 + boy, (150, 120, 70), 2, 4)


def mc_mage(s, x, y, col, t, hat=False, staff=True, eye=(120, 220, 255)):
    T = t
    boy = 1 if bob_offset(T, 1.8, 1.0) > 0 else 0
    dark = D(col, 40)
    # 로브 (아래로 넓어짐)
    B(s, x, y, 6, 6 + boy, col, 4, 1)
    B(s, x, y, 5, 7 + boy, col, 6, 1)
    checker(s, x, y, 5, 8 + boy, 6, 4, col, dark)
    B(s, x, y, 4, 12, col, 8, 3)
    B(s, x, y, 4, 15, dark, 8, 1)                  # 밑단
    # 후드/머리
    for gy in range(2, 7):
        for gx in range(5, 11):
            B(s, x, y, gx, gy + boy, col if gy < 5 else D(col, 60))
    B(s, x, y, 5, 6 + boy, col); B(s, x, y, 10, 6 + boy, col)
    eyes(s, x, y, 6, 9, 5 + boy, eye)
    if hat:                                        # 뾰족 마법사 모자
        B(s, x, y, 5, 2 + boy, dark, 6, 1)
        B(s, x, y, 6, 1 + boy, dark, 4, 1)
        B(s, x, y, 7, 0 + boy, dark, 2, 1)
        B(s, x, y, 5, 3 + boy, L(col, 20), 6, 1)
    if staff:
        for gy in range(3, 13):
            B(s, x, y, 13, gy, (110, 80, 46))
        B(s, x, y, 12, 2, L(eye, 40), 3, 3)        # 오브
        B(s, x, y, 13, 3, (255, 255, 255))


def mc_ghost(s, x, y, col, t, eye=(180, 230, 255)):
    T = t
    fy = int(bob_offset(T, 1.6, 1.6))
    body = L(col, 60)
    # 머리/몸
    for gy in range(3, 11):
        w = 6 if gy < 9 else 8
        gx0 = 8 - w // 2
        for gx in range(gx0, gx0 + w):
            B(s, x, y, gx, gy + fy, body if (gx + gy) % 2 else col)
    # 물결 밑단
    wob = int(math.sin(T * 0.008))
    for i, gx in enumerate(range(4, 12)):
        if (i + (1 if wob else 0)) % 2 == 0:
            B(s, x, y, gx, 11 + fy, col)
    eyes(s, x, y, 6, 9, 5 + fy, eye)
    B(s, x, y, 7, 7 + fy, D(eye, 40), 2, 1)        # 입


def mc_beast(s, x, y, col, t, tail=True, spikes=False):
    T = t
    boy = 1 if bob_offset(T, 5.0, 1.0) > 0 else 0
    dark = D(col, 35)
    # 몸통 (낮게)
    checker(s, x, y, 4, 9 + boy, 7, 3, col, dark)
    # 다리
    for gx in (4, 6, 8, 10):
        B(s, x, y, gx, 12, dark)
    # 머리(오른쪽)
    for gy in range(8 + boy, 12):
        B(s, x, y, 11, gy, col); B(s, x, y, 12, gy, col)
    B(s, x, y, 11, 7 + boy, col, 2, 1)             # 귀
    eyes(s, x, y, 12, 12, 9 + boy, (255, 220, 60))
    B(s, x, y, 13, 10 + boy, (255, 120, 120))      # 코끝
    if tail:
        B(s, x, y, 3, 9 + boy, dark); B(s, x, y, 2, 8 + boy, dark)
    if spikes:
        for gx in (5, 7, 9):
            B(s, x, y, gx, 8 + boy, _BONE)


def mc_flying(s, x, y, col, t, eye=(255, 70, 70)):
    T = t
    flap = bob_offset(T, 9.0, 1.0)
    wy = -1 if flap > 0 else 1
    dark = D(col, 40)
    fy = int(bob_offset(T, 2.5, 1.0))
    # 날개
    for i in range(3):
        B(s, x, y, 4 - i, 7 + wy + fy + i, dark)
        B(s, x, y, 11 + i, 7 + wy + fy + i, dark)
    B(s, x, y, 5, 7 + fy, col, 1, 2); B(s, x, y, 10, 7 + fy, col, 1, 2)
    # 몸
    checker(s, x, y, 6, 7 + fy, 4, 3, col, dark)
    B(s, x, y, 6, 10 + fy, col, 4, 1)
    eyes(s, x, y, 6, 9, 8 + fy, eye)
    B(s, x, y, 6, 6 + fy, dark); B(s, x, y, 9, 6 + fy, dark)  # 귀


def mc_spider(s, x, y, col, t, big=False, eye=(255, 60, 60)):
    T = t
    boy = int(bob_offset(T, 4.0, 1.0))
    dark = D(col, 40)
    step = 1 if bob_offset(T, 8.0, 1.0) > 0 else 0
    # 다리 8
    for i, gy in enumerate((7, 9, 11)):
        B(s, x, y, 3 - (i == 1), gy + boy + (step if i % 2 else 0), dark)
        B(s, x, y, 4, gy + boy, dark)
        B(s, x, y, 11, gy + boy, dark)
        B(s, x, y, 12 + (i == 1), gy + boy + (step if i % 2 == 0 else 0), dark)
    # 복부
    checker(s, x, y, 5, 8 + boy, 6, 4, col, dark)
    # 머리
    B(s, x, y, 6, 6 + boy, D(col, 20), 4, 2)
    eyes(s, x, y, 6, 9, 6 + boy, eye)
    B(s, x, y, 7, 6 + boy, eye); B(s, x, y, 8, 6 + boy, eye)
    if big:
        B(s, x, y, 4, 8 + boy, col); B(s, x, y, 11, 8 + boy, col)


def mc_slime(s, x, y, col, t, eye=(30, 40, 50)):
    T = t
    sq = bob_offset(T, 3.0, 1.0)
    top = 8 + (1 if sq > 0.3 else 0)
    dark = D(col, 45)
    lite = L(col, 60)
    for gy in range(top, 15):
        w = 10 - abs(gy - 12)
        gx0 = 8 - w // 2
        for gx in range(gx0, gx0 + w):
            B(s, x, y, gx, gy, col if (gx + gy) % 2 else dark)
    B(s, x, y, 6, top, lite, 3, 1)                 # 하이라이트
    B(s, x, y, 5, top + 1, lite)
    eyes(s, x, y, 6, 9, 11, eye)
    B(s, x, y, 6, 12, D(eye, 10)); B(s, x, y, 9, 12, D(eye, 10))


def mc_object(s, x, y, col, t, kind='crate', mimic=False):
    dark = D(col, 45); lite = L(col, 30)
    jitter = 0
    if mimic:
        jitter = 1 if bob_offset(t, 6.0, 1.0) > 0.5 else 0
    if kind in ('pot', 'jar'):
        for gy in range(6, 14):
            w = 8 if 7 <= gy <= 12 else 6
            gx0 = 8 - w // 2
            for gx in range(gx0, gx0 + w):
                B(s, x, y, gx, gy - jitter, col if (gx) % 2 else dark)
        B(s, x, y, 6, 5 - jitter, D(col, 20), 4, 1)  # 주둥이
        B(s, x, y, 6, 8 - jitter, lite, 1, 3)        # 광택
    elif kind == 'cage':
        B(s, x, y, 4, 4, (70, 66, 74), 8, 11)
        B(s, x, y, 5, 5, (30, 28, 34), 6, 9)         # 내부
        for gx in range(5, 11, 2):                   # 창살
            B(s, x, y, gx, 5, (120, 116, 126), 1, 9)
        eyes(s, x, y, 6, 9, 8, (255, 80, 80))
    elif kind == 'chest':
        B(s, x, y, 4, 8, (110, 78, 44), 8, 6)        # 하단
        B(s, x, y, 4, 5 - jitter, (130, 92, 52), 8, 3)  # 뚜껑
        B(s, x, y, 4, 8 - jitter, (80, 56, 32), 8, 1)
        B(s, x, y, 7, 9, (230, 200, 90), 2, 2)       # 자물쇠
        if mimic:                                    # 이빨
            for gx in range(4, 12, 2):
                B(s, x, y, gx, 7 - jitter, (240, 240, 245))
            eyes(s, x, y, 5, 10, 5 - jitter, (255, 80, 80))
    else:  # crate
        B(s, x, y, 4, 5, col, 8, 9)
        checker(s, x, y, 4, 5, 8, 9, col, dark)
        B(s, x, y, 4, 5, dark, 8, 1); B(s, x, y, 4, 13, dark, 8, 1)
        B(s, x, y, 4, 5, dark, 1, 9); B(s, x, y, 11, 5, dark, 1, 9)
        B(s, x, y, 7, 8, lite)          # 못/광택


def mc_plant(s, x, y, col, t, petal=(220, 70, 90)):
    T = t
    sway = 1 if bob_offset(T, 2.0, 1.0) > 0 else 0
    stem = (70, 130, 60)
    for gy in range(9, 15):
        B(s, x, y, 8 + (sway if gy < 11 else 0), gy, stem)
    B(s, x, y, 6, 11, (90, 160, 70)); B(s, x, y, 10, 12, (90, 160, 70))  # 잎
    cx = 7 + sway
    for gx in range(cx - 1, cx + 3):               # 꽃잎 링
        B(s, x, y, gx, 4, petal); B(s, x, y, gx, 8, petal)
    B(s, x, y, cx - 2, 5, petal, 1, 3); B(s, x, y, cx + 3, 5, petal, 1, 3)
    B(s, x, y, cx, 5, D(col, 10), 2, 3)            # 중심(입)
    eyes(s, x, y, cx, cx + 1, 6, (255, 240, 60))


def mc_golem(s, x, y, col, t, eye=(255, 170, 40)):
    T = t
    boy = 1 if bob_offset(T, 1.4, 1.0) > 0 else 0
    dark = D(col, 40); lite = L(col, 25)
    # 다리
    B(s, x, y, 5, 12, dark, 2, 3); B(s, x, y, 9, 12, dark, 2, 3)
    # 몸통(큼직)
    checker(s, x, y, 4, 6 + boy, 8, 6, col, dark)
    B(s, x, y, 3, 7 + boy, dark, 1, 4); B(s, x, y, 12, 7 + boy, dark, 1, 4)  # 팔
    B(s, x, y, 6, 9 + boy, lite); B(s, x, y, 9, 10 + boy, lite)   # 균열 광
    # 머리
    B(s, x, y, 6, 3 + boy, col, 4, 3)
    eyes(s, x, y, 6, 9, 4 + boy, eye)


def mc_dragon(s, x, y, col, t, eye=(255, 220, 60)):
    T = t
    flap = bob_offset(T, 4.0, 1.0)
    wy = -1 if flap > 0 else 0
    dark = D(col, 40); lite = L(col, 30)
    # 날개
    for i in range(4):
        B(s, x, y, 3 - i + 3, 5 + wy + i, dark)
        B(s, x, y, 9 + i, 5 + wy + i, dark)
    B(s, x, y, 1, 5 + wy, dark, 2, 4); B(s, x, y, 13, 5 + wy, dark, 2, 4)
    # 몸통
    checker(s, x, y, 5, 8, 6, 5, col, dark)
    B(s, x, y, 6, 13, dark, 2, 2); B(s, x, y, 9, 13, dark, 2, 2)   # 다리
    # 목/머리
    B(s, x, y, 7, 5, col, 2, 3)
    B(s, x, y, 6, 3, col, 4, 3)                    # 머리
    B(s, x, y, 5, 4, col, 1, 2)                    # 주둥이
    B(s, x, y, 6, 2, _BONE); B(s, x, y, 9, 2, _BONE)   # 뿔
    eyes(s, x, y, 6, 9, 4, eye)
    B(s, x, y, 4, 5, (255, 140, 40))              # 콧김


# ══════════════════════════════════════════════════════════════════════
#  key → (archetype, kwargs)
# ══════════════════════════════════════════════════════════════════════
def _H(**k): return (mc_humanoid, k)
def _S(**k): return (mc_skeleton, k)
def _M(**k): return (mc_mage, k)
def _G(**k): return (mc_ghost, k)
def _B(**k): return (mc_beast, k)
def _F(**k): return (mc_flying, k)
def _SP(**k): return (mc_spider, k)
def _SL(**k): return (mc_slime, k)
def _O(**k): return (mc_object, k)
def _P(**k): return (mc_plant, k)
def _GO(**k): return (mc_golem, k)
def _DR(**k): return (mc_dragon, k)

_SPEC = {
    # 야수/벌레
    'rat':        _B(spikes=False),
    'centipede':  _B(tail=True, spikes=True),
    'bat':        _F(),
    'blood_bat':  _F(eye=(255, 40, 40)),
    'spider':     _SP(),
    'giant_spider': _SP(big=True),
    'slime':      _SL(),
    # 고블린류/오크
    'goblin':       _H(skin=(120, 180, 90), weapon='dagger'),
    'treasure_goblin': _H(skin=(120, 180, 90), gold=True),
    'orc':          _H(skin=(110, 160, 90), big=True, weapon='axe', horns=True),
    'troll':        _H(skin=(120, 150, 100), big=True, weapon='mace'),
    'grave_titan':  _H(skin=(120, 120, 130), big=True, helmet=(90, 92, 100)),
    # 좀비/구울
    'zombie':       _H(skin=(120, 150, 90), eye=(200, 60, 60)),
    'giant_zombie': _H(skin=(110, 145, 85), big=True, eye=(200, 60, 60)),
    'ghoul':        _H(skin=(150, 160, 130), eye=(230, 200, 60), tail=False),
    'prisoner':     _H(skin=(200, 175, 150)),
    # 스켈레톤
    'skeleton':        _S(),
    'blade_skeleton':  _S(weapon='sword'),
    'shield_skeleton': _S(weapon='sword', shield=True),
    'archer_skeleton': _S(bow=True),
    'spear_skeleton':  _S(weapon='spear'),
    'bone_wizard':     _S(tint=(150, 90, 220)),
    # 인간 악당
    'bandit':      _H(skin=(200, 170, 140), hood=(90, 70, 60), weapon='dagger'),
    'thief':       _H(skin=(200, 170, 140), hood=(60, 66, 80), weapon='dagger'),
    'assassin':    _H(skin=(180, 160, 140), hood=(40, 42, 52), weapon='dagger'),
    'ambusher':    _H(skin=(190, 165, 140), hood=(60, 70, 55), weapon='dagger'),
    'torturer':    _H(skin=(210, 175, 150), weapon='whip'),
    'whip_master': _H(skin=(205, 170, 145), weapon='whip'),
    'brand_man':   _H(skin=(210, 170, 140), weapon='mace'),
    'executioner_nov': _H(skin=(200, 165, 140), hood=(40, 40, 46), weapon='axe', big=True),
    'stomp_exec':  _H(skin=(200, 165, 140), big=True, helmet=(70, 72, 80)),
    'jail_captain': _H(skin=(205, 170, 145), helmet=(120, 100, 60), weapon='spear'),
    # 갑옷 기사
    'mace_knight':  _H(skin=(180, 160, 150), helmet=(150, 155, 165), weapon='mace', shield=True),
    'steel_knight': _H(skin=(170, 150, 140), helmet=(170, 175, 185), weapon='sword', shield=True),
    'dark_knight':  _H(skin=(120, 110, 120), helmet=(70, 70, 82), weapon='sword', shield=True, horns=True),
    # 마법사/로브
    'wizard':      _M(hat=True),
    'curse_mage':  _M(hat=False, eye=(200, 90, 240)),
    'death_mage':  _M(hat=False, eye=(120, 230, 140)),
    'illusionist': _M(hat=True, eye=(255, 140, 220)),
    'lich':        _M(hat=False, eye=(120, 240, 200)),
    # 유령
    'ghost':         _G(),
    'specter':       _G(eye=(200, 180, 255)),
    'shadow_stalker': _G(eye=(255, 90, 90)),
    'soul_absorber': _G(eye=(160, 255, 220)),
    # 오브젝트
    'pot':          _O(kind='pot'),
    'crate':        _O(kind='crate'),
    'jar_crawler':  _O(kind='jar', mimic=True),
    'chest_mimic':  _O(kind='chest', mimic=True),
    'mimic':        _O(kind='chest', mimic=True),
    'iron_cage':    _O(kind='cage'),
    'chain_beast':  _O(kind='cage'),
    # 식물
    'corpse_flower': _P(petal=(200, 70, 90)),
    'poison_sprite': _P(petal=(130, 220, 90)),
    # 골렘
    'rock_golem':   _GO(),
    # 드래곤
    'dragon':       _DR(),
}


def _make(archetype, kwargs):
    def fn(s, x, y, col, t):
        archetype(s, x, y, col, t, **kwargs)
    return fn


MC_ENEMY_SPRITE_FNS = {key: _make(a, kw) for key, (a, kw) in _SPEC.items()}


def mc_generic(s, x, y, col, t):
    mc_humanoid(s, x, y, col, t, skin=col)


# ══════════════════════════════════════════════════════════════════════
#  친근한 마을 사람 (정면, 걷기 보정은 호출측 y 오프셋)
# ══════════════════════════════════════════════════════════════════════
def mc_villager(s, x, y, t, skin=(240, 200, 165), hair=(90, 60, 35),
                hair_style='short', tunic=(120, 130, 170), pants=(70, 72, 90),
                hat=None, apron=None, prop=None, small=False, bob=True):
    boy = 0
    if bob:
        boy = 1 if bob_offset(t, 2.2, 1.0) > 0.3 else 0
    dy = 1 if small else 0                          # 아이는 살짝 아래·짧게
    skin_d = D(skin, 30)
    ht = 3 + dy                                     # 머리 최상단 행
    bt = ht + 5                                     # 몸통 최상단 행
    # 다리
    for gx in (6, 9):
        B(s, x, y, gx, 13 + dy, pants, 1, 2 - dy)
        B(s, x, y, gx, 15, D(pants, 30))
    # 몸통/튜닉
    checker(s, x, y, 5, bt + boy, 6, 13 - bt, tunic)
    if apron:
        B(s, x, y, 6, bt + 1 + boy, apron, 4, max(1, 12 - bt))
    # 팔
    for gx in (3, 12):
        B(s, x, y, gx, bt + boy, D(tunic, 25), 1, 3)
        B(s, x, y, gx, bt + 3 + boy, skin)
    # 머리 (ht..ht+4)
    for gy in range(ht, ht + 5):
        for gx in range(5, 11):
            B(s, x, y, gx, gy + boy, skin)
    B(s, x, y, 7, ht + 4 + boy, skin_d); B(s, x, y, 8, ht + 4 + boy, skin_d)      # 턱
    B(s, x, y, 6, ht + 2 + boy, (40, 34, 40)); B(s, x, y, 9, ht + 2 + boy, (40, 34, 40))  # 눈
    B(s, x, y, 5, ht + 3 + boy, L(skin, 15)); B(s, x, y, 10, ht + 3 + boy, L(skin, 15))   # 볼
    # 머리카락
    hc_d = D(hair, 22)
    if hair_style != 'bald':
        for gx in range(5, 11):
            B(s, x, y, gx, ht + boy, hair)
        for gx in range(5, 11):
            B(s, x, y, gx, ht + 1 + boy, hair if gx in (5, 10) else hc_d)
        B(s, x, y, 5, ht + 2 + boy, hair); B(s, x, y, 10, ht + 2 + boy, hair)
        if hair_style == 'bun':                     # 할머니 쪽머리
            B(s, x, y, 7, ht - 1 + boy, (210, 210, 215), 2, 1)
        elif hair_style == 'long':
            for gy in range(ht + 1, ht + 6):
                B(s, x, y, 4, gy + boy, hair); B(s, x, y, 11, gy + boy, hair)
    if hat == 'straw':
        for gx in range(4, 12):
            B(s, x, y, gx, ht + boy, (210, 180, 90))
        B(s, x, y, 5, ht - 1 + boy, (225, 195, 105), 6, 1)
    elif isinstance(hat, tuple):
        for gx in range(5, 11):
            B(s, x, y, gx, ht - 1 + boy, hat)
        B(s, x, y, 5, ht + boy, hat, 6, 1)
    # 소품
    if prop == 'hammer':
        B(s, x, y, 13, 9 + boy, (110, 80, 46), 1, 3)
        B(s, x, y, 12, 8 + boy, (150, 150, 160), 3, 2)
    elif prop == 'coin':
        B(s, x, y, 2, 10 + boy, (240, 200, 70), 2, 2)
        B(s, x, y, 2, 9 + boy, (255, 225, 110))
    elif prop == 'bow':
        for gy in range(7, 13):
            B(s, x, y, 2, gy + boy, (140, 100, 56))
        B(s, x, y, 2, 7 + boy, (200, 200, 210)); B(s, x, y, 2, 12 + boy, (200, 200, 210))
    elif prop == 'book':
        B(s, x, y, 12, 10 + boy, (150, 60, 60), 3, 3)
        B(s, x, y, 13, 10 + boy, (240, 240, 230), 1, 3)
    elif prop == 'key':
        B(s, x, y, 13, 10 + boy, (230, 200, 90))
        B(s, x, y, 13, 11 + boy, (230, 200, 90), 1, 2)
    elif prop == 'cane':
        for gy in range(9, 15):
            B(s, x, y, 13, gy + boy, (120, 90, 50))
        B(s, x, y, 12, 8 + boy, (140, 105, 60), 2, 1)


# NPC id → mc_villager kwargs (town.py에서 사용)
VILLAGER_SPEC = {
    'inn':      dict(skin=(238, 198, 162), hair=(120, 84, 44), tunic=(150, 120, 80),
                     apron=(200, 190, 175), prop='key'),
    'smith':    dict(skin=(214, 168, 132), hair=(60, 46, 40), tunic=(90, 92, 104),
                     apron=(80, 62, 48), prop='hammer'),
    'merchant': dict(skin=(240, 200, 160), hair=(70, 50, 34), tunic=(150, 70, 150),
                     hat=(90, 40, 120), prop='coin'),
    'villager_boy':     dict(skin=(245, 205, 168), hair=(150, 100, 50),
                             tunic=(90, 150, 180), pants=(80, 70, 60), small=True),
    'villager_farmer':  dict(skin=(224, 176, 130), hair=(90, 62, 36),
                             tunic=(110, 150, 80), hat='straw', pants=(90, 74, 50)),
    'villager_granny':  dict(skin=(236, 200, 172), hair=(205, 205, 210),
                             hair_style='bun', tunic=(150, 110, 150), prop='cane'),
    'villager_hunter':  dict(skin=(216, 168, 128), hair=(70, 50, 34),
                             tunic=(96, 120, 80), hat=(70, 90, 60), prop='bow'),
    'villager_scholar': dict(skin=(238, 198, 164), hair=(60, 48, 60),
                             hair_style='long', tunic=(90, 80, 150), prop='book'),
}

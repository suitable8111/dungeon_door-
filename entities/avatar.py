"""마인크래프트 풍 픽셀 아바타 — 캐릭터 생성/선택 화면용 프리뷰.

격자(그리드) 위에 사각 픽셀을 찍어 정면 캐릭터를 그린다.
피부색 / 헤어스타일 / 머리색 / 직업(복장색)을 파라미터로 받는다.

appearance = {'skin': int, 'hair': int, 'haircol': int}
"""
import pygame

# ── 팔레트 ──────────────────────────────────────────────────────────────
SKIN_TONES = [
    (255, 224, 189),   # 밝은 살구
    (241, 194, 155),   # 살구
    (215, 165, 125),   # 중간
    (172, 122, 84),    # 구릿빛
    (124, 84, 58),     # 갈색
    (86, 58, 42),      # 짙은 갈색
]
HAIR_COLORS = [
    (38, 30, 26),      # 흑발
    (92, 56, 30),      # 갈색
    (208, 166, 68),    # 금발
    (176, 44, 40),     # 빨강
    (206, 208, 214),   # 은발
    (74, 120, 196),    # 판타지 블루
]
HAIR_STYLES = ['short', 'long', 'spiky', 'ponytail', 'bald']

# 직업별 복장색 (튜닉, 바지, 벨트)
_CLASS_KIT = {
    'warrior': {'tunic': (170, 60, 55), 'trim': (210, 200, 205),
                'pants': (60, 62, 78),  'boot': (72, 52, 40)},
    'archer':  {'tunic': (74, 128, 78), 'trim': (150, 120, 74),
                'pants': (72, 78, 60),  'boot': (86, 62, 42)},
    'mage':    {'tunic': (86, 66, 150), 'trim': (176, 150, 235),
                'pants': (52, 44, 92),  'boot': (60, 50, 84)},
    'axeman':  {'tunic': (150, 92, 44), 'trim': (214, 150, 78),
                'pants': (70, 56, 44),  'boot': (58, 44, 34)},
}

# 2차 전직 — 전직별 복장 색 (전직한 티가 나도록 뚜렷이 구분)
_SUBCLASS_KIT = {
    'dual_blade':      {'tunic': (40, 150, 160), 'trim': (200, 240, 245), 'pants': (40, 60, 78),  'boot': (60, 60, 62)},
    'magic_swordsman': {'tunic': (140, 55, 150), 'trim': (225, 180, 245), 'pants': (55, 40, 80),  'boot': (60, 50, 70)},
    'crossbow_master': {'tunic': (58, 96, 62),   'trim': (205, 168, 96),  'pants': (55, 60, 48),  'boot': (70, 52, 38)},
    'twin_bow':        {'tunic': (120, 192, 96), 'trim': (228, 235, 158), 'pants': (70, 82, 56),  'boot': (86, 62, 42)},
    'battle_mage':     {'tunic': (162, 60, 66),  'trim': (238, 168, 156), 'pants': (72, 40, 44),  'boot': (62, 44, 44)},
    'speed_mage':      {'tunic': (66, 132, 212), 'trim': (182, 216, 255), 'pants': (44, 60, 96),  'boot': (50, 56, 84)},
}

# 전직 오라/기본공격 이펙트 색
SUBCLASS_AURA = {
    'dual_blade': (80, 232, 242), 'magic_swordsman': (212, 130, 250),
    'crossbow_master': (232, 190, 92), 'twin_bow': (182, 242, 120),
    'battle_mage': (255, 112, 92), 'speed_mage': (112, 202, 255),
}


def _shade(col, d):
    return tuple(max(0, min(255, c + d)) for c in col)


def _px(surf, ox, oy, gx, gy, s, col):
    """그리드 좌표(gx,gy)에 s×s 픽셀 사각형."""
    pygame.draw.rect(surf, col, (ox + gx * s, oy + gy * s, s, s))


# 캐릭터 그리드 크기 (칸). 폭 12 × 높이 20.
GRID_W, GRID_H = 12, 20


def draw_avatar(surf, cx, cy, scale, appearance=None, char_class='warrior'):
    """(cx,cy)를 중심으로 scale 픽셀 크기의 정면 아바타를 그린다."""
    a = appearance or {}
    skin = SKIN_TONES[a.get('skin', 0) % len(SKIN_TONES)]
    haircol = HAIR_COLORS[a.get('haircol', 0) % len(HAIR_COLORS)]
    style = HAIR_STYLES[a.get('hair', 0) % len(HAIR_STYLES)]
    kit = _CLASS_KIT.get(char_class, _CLASS_KIT['warrior'])

    s = scale
    ox = cx - (GRID_W * s) // 2
    oy = cy - (GRID_H * s) // 2

    skin_d = _shade(skin, -28)
    tunic, tunic_d = kit['tunic'], _shade(kit['tunic'], -30)
    trim = kit['trim']
    pants, pants_d = kit['pants'], _shade(kit['pants'], -22)
    boot = kit['boot']

    def P(gx, gy, col): _px(surf, ox, oy, gx, gy, s, col)

    # ── 다리 (rows 16-19) ──
    for gy in range(16, 20):
        for gx in (3, 4):
            P(gx, gy, pants if gy < 19 else boot)
        for gx in (7, 8):
            P(gx, gy, pants if gy < 19 else boot)
    P(3, 19, boot); P(4, 19, _shade(boot, -18))
    P(7, 19, boot); P(8, 19, _shade(boot, -18))

    # ── 몸통/튜닉 (rows 9-15, cols 3-8) ──
    for gy in range(9, 16):
        for gx in range(3, 9):
            P(gx, gy, tunic if (gx + gy) % 2 == 0 else tunic_d)
    # 벨트
    for gx in range(3, 9):
        P(gx, 15, trim if gx in (5, 6) else _shade(trim, -30))
    # 가슴 트림 (V)
    P(5, 9, trim); P(6, 9, trim)

    # ── 팔 (cols 1-2, 9-10) : 소매(튜닉) + 손(피부) ──
    for gy in range(9, 14):
        col = tunic_d if gy < 13 else skin
        P(2, gy, col); P(1, gy, _shade(col, -18))
        P(9, gy, col); P(10, gy, _shade(col, -18))

    # ── 머리 (rows 2-8, cols 3-8) ──
    for gy in range(2, 9):
        for gx in range(3, 9):
            P(gx, gy, skin)
    # 턱/목 그림자
    for gx in range(4, 8):
        P(gx, 8, skin_d)
    # 목
    P(5, 8, skin_d); P(6, 8, skin_d)

    # 눈
    eye = (36, 32, 40)
    P(4, 5, (255, 255, 255)); P(4, 6, eye)
    P(7, 5, (255, 255, 255)); P(7, 6, eye)
    # 볼 홍조
    P(3, 6, _shade(skin, 18)); P(8, 6, _shade(skin, 18))

    # ── 머리카락 스타일 ──
    hc_d = _shade(haircol, -24)
    if style == 'bald':
        pass
    elif style == 'short':
        for gx in range(3, 9):        # 앞머리 두 줄
            P(gx, 2, haircol)
        for gx in range(3, 9):
            P(gx, 3, haircol if gx in (3, 8) else hc_d)
        P(3, 4, haircol); P(8, 4, haircol)     # 옆
    elif style == 'spiky':
        for gx in range(3, 9):
            P(gx, 2, hc_d)
        for gx in (3, 5, 7):          # 삐죽삐죽 위로
            P(gx, 1, haircol)
        P(4, 3, haircol); P(7, 3, haircol)
        P(3, 4, haircol); P(8, 4, haircol)
    elif style == 'long':
        for gx in range(3, 9):        # 정수리
            P(gx, 2, haircol)
        P(3, 3, haircol); P(8, 3, haircol)
        for gy in range(3, 11):       # 어깨까지 늘어진 옆머리
            P(2, gy, haircol); P(9, gy, haircol)
        P(3, 3, hc_d)
    elif style == 'ponytail':
        for gx in range(3, 9):
            P(gx, 2, haircol)
        P(3, 3, haircol); P(8, 3, haircol)
        for gy in range(2, 7):        # 뒤로 묶은 꽁지 (오른쪽 위)
            P(9, gy, haircol)
        P(10, 4, haircol); P(10, 5, haircol)

    # 직업 액세서리: 궁수=화살통, 마법사=지팡이+오브, 전사=견장 + 세워 든 검
    if char_class == 'archer':
        for gy in range(9, 13):       # 등 뒤 화살통 암시(왼쪽)
            P(1, gy, (110, 80, 46))
        P(1, 8, (170, 150, 90))
    elif char_class == 'mage':
        P(2, 9, trim); P(9, 9, trim)  # 로브 어깨 장식
        wood, wood_hi = (140, 100, 62), (176, 134, 86)
        for gy in range(5, 16):       # 오른쪽에 세워 든 지팡이
            P(11, gy, wood)
        P(11, 15, wood_hi)
        # 상단 오브(빛나는 보라)
        P(11, 4, (225, 210, 255)); P(10, 4, (170, 130, 245))
        P(11, 3, (170, 130, 245)); P(11, 5, (170, 130, 245)); P(12, 4, (170, 130, 245))
    elif char_class == 'axeman':
        P(2, 9, trim); P(9, 9, trim)  # 견장
        haft, haft_hi = (128, 92, 54), (168, 126, 78)
        blade, blade_hi = (200, 205, 216), (238, 240, 248)
        for gy in range(4, 16):       # 오른쪽에 세워 든 긴 자루
            P(11, gy, haft)
        P(11, 15, haft_hi)
        # 상단 넓은 양손도끼날
        P(10, 4, blade); P(12, 4, blade); P(10, 5, blade); P(12, 5, blade)
        P(10, 3, blade); P(11, 4, blade_hi); P(10, 6, blade)
    else:
        P(2, 9, trim); P(9, 9, trim)  # 견장
        steel, steel_hi = (205, 210, 222), (236, 239, 246)
        guard, grip, pommel = (150, 120, 60), (110, 80, 48), (232, 202, 92)
        for gy in range(4, 12):       # 오른쪽에 세워 든 칼날
            P(11, gy, steel)
        P(11, 4, steel_hi)            # 칼끝
        P(10, 12, guard); P(11, 12, guard)   # 코등이
        P(11, 13, grip); P(11, 14, grip)     # 손잡이
        P(11, 15, pommel)            # 폼멜


# ══════════════════════════════════════════════════════════════════════
#  인게임 타일용 방향별 아바타 (32px 타일, 2px 블록 = 16×16 논리 그리드)
# ══════════════════════════════════════════════════════════════════════
def draw_avatar_tile(surf, x, y, facing='down', frame=0, phase=0,
                     appearance=None, char_class='warrior', subclass=None):
    """(x,y) 타일 좌상단 기준으로 방향·걷기 프레임을 반영해 아바타를 그린다.

    facing: 'down'|'up'|'left'|'right'   frame: 걷기 애니(0/1)   phase: 공격(0 대기,1/2)
    left는 right를 좌우 반전해서 그린다. subclass가 있으면 전직 복장색 사용.
    """
    a = appearance or {}
    skin = SKIN_TONES[a.get('skin', 0) % len(SKIN_TONES)]
    haircol = HAIR_COLORS[a.get('haircol', 0) % len(HAIR_COLORS)]
    style = HAIR_STYLES[a.get('hair', 0) % len(HAIR_STYLES)]
    kit = _SUBCLASS_KIT.get(subclass) or _CLASS_KIT.get(char_class, _CLASS_KIT['warrior'])

    # left면 임시 서피스에 right로 그린 뒤 반전
    if facing == 'left':
        tmp = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_avatar_tile(tmp, 0, 0, 'right', frame, phase, appearance, char_class)
        surf.blit(pygame.transform.flip(tmp, True, False), (x, y))
        return

    skin_d = _shade(skin, -26)
    tunic, tunic_d = kit['tunic'], _shade(kit['tunic'], -28)
    trim = kit['trim']
    pants, pants_d = kit['pants'], _shade(kit['pants'], -20)
    boot = kit['boot']
    hc_d = _shade(haircol, -22)

    # 공격 페이즈 → 진행 방향으로 살짝 전진(lunge)
    lunge = {1: 1, 2: 2}.get(phase, 0)
    fdx, fdy = _DIR_T.get(facing, (0, 1))
    lx, ly = fdx * lunge, fdy * lunge

    def B(gx, gy, col):
        pygame.draw.rect(surf, col, (x + gx * 2 + lx, y + gy * 2 + ly, 2, 2))

    def Bhead(gx, gy, col):   # 머리는 lunge에서 살짝만 이동
        pygame.draw.rect(surf, col, (x + gx * 2 + lx, y + gy * 2 + ly, 2, 2))

    # ── 다리 (rows 13-15) — 걷기 프레임에 따라 앞뒤 스텝 ──
    step = frame % 2
    lo, ro = (0, 1) if step == 0 else (1, 0)   # 왼/오 다리 수직 오프셋
    for gy in range(13, 16):
        for gx in (5, 6):
            B(gx, gy + lo, pants if gy < 15 else boot)
        for gx in (9, 10):
            B(gx, gy + ro, pants if gy < 15 else boot)

    # ── 몸통/튜닉 (rows 8-12, cols 5-10) ──
    for gy in range(8, 13):
        for gx in range(5, 11):
            B(gx, gy, tunic if (gx + gy) % 2 == 0 else tunic_d)
    for gx in range(5, 11):        # 벨트
        B(gx, 12, trim if gx in (7, 8) else _shade(trim, -28))

    # ── 팔 (cols 3-4, 11-12) 소매+손, 걷기시 반대로 스윙 ──
    la, ra = (ro, lo)              # 팔은 다리와 반대 위상
    for gy in range(8, 12):
        col = tunic_d if gy < 11 else skin
        B(4, gy + la, col); B(3, gy + la, _shade(col, -16))
        B(11, gy + ra, col); B(12, gy + ra, _shade(col, -16))

    # ── 머리 (rows 2-7, cols 5-10) ──
    for gy in range(2, 8):
        for gx in range(5, 11):
            Bhead(gx, gy, skin)
    Bhead(7, 7, skin_d); Bhead(8, 7, skin_d)   # 목/턱

    # ── 얼굴 (방향별) ──
    eye = (36, 32, 40)
    if facing == 'down':
        Bhead(6, 5, (255, 255, 255)); Bhead(6, 6, eye)
        Bhead(9, 5, (255, 255, 255)); Bhead(9, 6, eye)
        Bhead(5, 6, _shade(skin, 16)); Bhead(10, 6, _shade(skin, 16))
    elif facing == 'right':
        Bhead(9, 5, (255, 255, 255)); Bhead(9, 6, eye)   # 한쪽 눈(옆모습)
        Bhead(10, 4, skin_d)                              # 코/윤곽
    # up(뒤통수)은 얼굴 없음

    # ── 머리카락 (방향 + 스타일) ──
    def hair_top(front=True):
        for gx in range(5, 11):
            Bhead(gx, 2, haircol)
        for gx in range(5, 11):
            Bhead(gx, 3, haircol if gx in (5, 10) else (hc_d if front else haircol))

    if style == 'bald':
        if facing == 'up':                 # 뒤통수는 머리색 없이 민머리
            pass
    elif style == 'short':
        hair_top(front=(facing != 'up'))
        if facing == 'up':
            for gx in range(5, 11):        # 뒤통수 전체 덮기
                Bhead(gx, 4, haircol)
        Bhead(5, 4, haircol); Bhead(10, 4, haircol)
    elif style == 'spiky':
        for gx in range(5, 11):
            Bhead(gx, 2, hc_d)
        for gx in (5, 7, 9):
            Bhead(gx, 1, haircol)
        Bhead(6, 3, haircol); Bhead(9, 3, haircol)
        Bhead(5, 4, haircol); Bhead(10, 4, haircol)
        if facing == 'up':
            for gx in range(5, 11):
                Bhead(gx, 4, haircol)
    elif style == 'long':
        hair_top(front=(facing != 'up'))
        Bhead(5, 3, haircol); Bhead(10, 3, haircol)
        for gy in range(3, 9):             # 어깨까지 옆/뒷머리
            Bhead(4, gy, haircol); Bhead(11, gy, haircol)
        if facing == 'up':
            for gy in range(4, 8):
                for gx in range(5, 11):
                    Bhead(gx, gy, haircol if (gx + gy) % 2 else hc_d)
    elif style == 'ponytail':
        hair_top(front=(facing != 'up'))
        Bhead(5, 3, haircol); Bhead(10, 3, haircol)
        if facing == 'up':                 # 뒤에서 보면 꽁지가 가운데로
            for gy in range(4, 10):
                Bhead(7, gy, haircol); Bhead(8, gy, haircol)
            for gx in range(5, 11):
                Bhead(gx, 4, haircol)
        else:                              # 정면/측면: 꽁지 살짝 옆으로
            for gy in range(3, 7):
                Bhead(11, gy, haircol)

    # 직업 소품: 궁수 화살통(등 뒤, up일 때 잘 보임)
    if char_class == 'archer' and facing == 'up':
        for gy in range(8, 12):
            B(8, gy, (110, 80, 46))
        B(8, 7, (170, 150, 90))

    # 직업 소품: 전사 검 (오른손) — 방향/공격 프레임 반영. 전직별 색/이중검.
    if char_class == 'warrior':
        if subclass == 'magic_swordsman':     # 마검: 보라 마력검 + 광채
            steel, steel_hi = (176, 120, 235), (226, 190, 252)
        else:
            steel, steel_hi = (205, 210, 222), (236, 239, 246)
        guard, grip, pommel = (150, 120, 60), (110, 80, 48), (232, 202, 92)
        if phase == 2:                        # 앞으로 내려친 슬래시(오른쪽으로 뻗음)
            for gx in range(11, 15):
                B(gx, 9, steel)
            B(14, 9, steel_hi)
            B(11, 8, guard); B(11, 10, guard)
            B(10, 9, grip); B(9, 9, pommel)
        else:                                 # 대기/준비 — 오른쪽에 세워 든 칼
            up = 2 if phase == 1 else 0        # 준비 자세면 살짝 치켜듦
            for gy in range(3 - up, 9 - up):
                B(13, gy, steel)
            B(13, 3 - up, steel_hi)           # 칼끝
            if subclass == 'magic_swordsman' and (frame or phase):  # 마력 광채
                B(12, 4 - up, (150, 90, 230)); B(14, 5 - up, (150, 90, 230))
            B(12, 9 - up, guard); B(13, 9 - up, guard)   # 코등이
            B(13, 10 - up, grip); B(13, 11 - up, grip)   # 손잡이
            B(13, 12 - up, pommel)            # 폼멜
        # 쌍검사: 왼손에 두 번째 검(청록) — 이중검
        if subclass == 'dual_blade':
            cs, cs_hi = (90, 210, 224), (200, 245, 250)
            if phase == 2:                    # 왼쪽으로 뻗은 미러 슬래시
                for gx in range(1, 5):
                    B(gx, 10, cs)
                B(1, 10, cs_hi)
                B(4, 9, guard); B(4, 11, guard)
            else:
                up = 2 if phase == 1 else 0
                for gy in range(3 - up, 9 - up):
                    B(2, gy, cs)
                B(2, 3 - up, cs_hi)
                B(1, 9 - up, guard); B(2, 9 - up, guard)
                B(2, 10 - up, grip); B(2, 11 - up, grip)

    # 직업 소품: 도끼맨 양손도끼 (오른손) — 공격 프레임에 내려침
    if char_class == 'axeman':
        haft, haft_hi = (128, 92, 54), (168, 126, 78)
        blade, blade_hi = (200, 205, 216), (238, 240, 248)
        if phase == 2:                        # 앞으로 내려친 도끼(오른쪽 아래로)
            for gx in range(11, 15):
                B(gx, 10, haft)
            B(14, 9, blade); B(15, 9, blade); B(14, 10, blade); B(15, 10, blade)
            B(14, 8, blade); B(15, 8, blade_hi); B(15, 11, blade)
        else:                                 # 대기/준비 — 세워 든 도끼 + 넓은 날
            up = 2 if phase == 1 else 0
            for gy in range(4 - up, 13 - up):
                B(13, gy, haft)
            B(13, 12 - up, haft_hi)
            B(12, 4 - up, blade); B(14, 4 - up, blade)
            B(12, 5 - up, blade); B(14, 5 - up, blade)
            B(12, 3 - up, blade); B(14, 3 - up, blade_hi); B(12, 6 - up, blade)


_DIR_T = {'right': (1, 0), 'left': (-1, 0), 'down': (0, 1), 'up': (0, -1)}


def avatar_surface(size, appearance=None, char_class='warrior', scale=None):
    """size×size 투명 서피스에 아바타를 그려 반환."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    s = scale if scale else max(1, size // (GRID_H + 2))
    draw_avatar(surf, size // 2, size // 2, s, appearance, char_class)
    return surf


# ── 커스터마이즈 순환 헬퍼 ──────────────────────────────────────────────
def cycle(field, cur, delta):
    n = {'skin': len(SKIN_TONES), 'hair': len(HAIR_STYLES),
         'haircol': len(HAIR_COLORS)}[field]
    return (cur + delta) % n


def default_appearance():
    return {'skin': 0, 'hair': 0, 'haircol': 0}

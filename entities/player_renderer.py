"""
주인공 장비 레이어 렌더링 시스템.
draw_player() 또는 스프라이트 위에 장비 레이어를 순서대로 그린다:
  1. body (갑옷 오버레이)
  2. helmet (투구 오버레이)
  3. shield (방패)
  4. weapon (무기)  ← 마지막에 그려야 항상 최상단
"""
import math
import pygame

_PI = math.pi

# 방향 → (전방 단위벡터)
_DIR = {'right': (1, 0), 'left': (-1, 0), 'down': (0, 1), 'up': (0, -1)}


def draw_archer_bow(surf, tile_x, tile_y, facing, phase, subclass=None):
    """궁수 활 오버레이 — 베이스 스프라이트 위에 활+화살을 그린다.
    전직: crossbow_master=석궁(금색+개머리), twin_bow=쌍궁(녹색+이중시위).
    phase 0=대기, 1=당김(노킹), 2=발사 직후.
    """
    cx, cy = tile_x + 16, tile_y + 16
    dx, dy = _DIR.get(facing, (0, 1))
    px, py = -dy, dx                     # 수직
    bxc = cx + dx * 8
    byc = cy + dy * 8 + (2 if facing == 'down' else -2 if facing == 'up' else 0)
    # ── 석궁 마스터: 짧고 두꺼운 리무 + 개머리(스톡) ──
    if subclass == 'crossbow_master':
        L = 7
        t1 = (int(bxc + px * L), int(byc + py * L)); t2 = (int(bxc - px * L), int(byc - py * L))
        pygame.draw.line(surf, (110, 84, 50),
                         (int(cx + dx * 2), int(cy + dy * 2)),
                         (int(bxc + dx * 5), int(byc + dy * 5)), 3)     # 스톡
        pygame.draw.line(surf, (205, 170, 96), t1, t2, 3)              # 리무(금색·굵게)
        pygame.draw.line(surf, (225, 228, 235), t1, t2, 1)            # 시위
        if phase in (1, 2):                                            # 볼트
            b2 = (int(bxc + dx * 11), int(byc + dy * 11))
            pygame.draw.line(surf, (150, 150, 160), (int(bxc + dx * 5), int(byc + dy * 5)), b2, 2)
            pygame.draw.polygon(surf, (240, 235, 180), [
                (int(b2[0] + dx * 3), int(b2[1] + dy * 3)),
                (int(b2[0] + px * 2), int(b2[1] + py * 2)),
                (int(b2[0] - px * 2), int(b2[1] - py * 2))])
        return
    L = 9
    wood, lite = ((104, 176, 84), (176, 224, 130)) if subclass == 'twin_bow' \
        else ((150, 110, 60), (196, 150, 90))
    t1 = (int(bxc + px * L), int(byc + py * L))
    t2 = (int(bxc - px * L), int(byc - py * L))
    mid = (int(bxc + dx * 4), int(byc + dy * 4))
    pygame.draw.lines(surf, wood, False, [t1, mid, t2], 2)
    pygame.draw.circle(surf, lite, mid, 1)
    pull = {0: 0, 1: 5, 2: -3}.get(phase, 0)
    nock = (int(bxc - dx * pull), int(byc - dy * pull))
    string = (225, 225, 232)
    pygame.draw.line(surf, string, t1, nock, 1)
    pygame.draw.line(surf, string, t2, nock, 1)
    if subclass == 'twin_bow':                       # 두 번째 활(앞쪽 겹침)
        o1 = (int(bxc + dx * 3 + px * (L - 2)), int(byc + dy * 3 + py * (L - 2)))
        o2 = (int(bxc + dx * 3 - px * (L - 2)), int(byc + dy * 3 - py * (L - 2)))
        om = (int(bxc + dx * 7), int(byc + dy * 7))
        pygame.draw.lines(surf, lite, False, [o1, om, o2], 2)
    if phase == 1:                       # 노킹된 화살
        ax = (int(nock[0] + dx * 14), int(nock[1] + dy * 14))
        pygame.draw.line(surf, (150, 120, 70), nock, ax, 2)
        pygame.draw.polygon(surf, (240, 235, 180), [
            (int(ax[0] + dx * 3), int(ax[1] + dy * 3)),
            (int(ax[0] + px * 2), int(ax[1] + py * 2)),
            (int(ax[0] - px * 2), int(ax[1] - py * 2))])


def draw_mage_staff(surf, tile_x, tile_y, facing, phase, t_ms=0, subclass=None):
    """마법사 지팡이 오버레이 — 몸 앞으로 든 지팡이 + 빛나는 오브.
    전직: battle_mage=붉은 오브+단검날, speed_mage=파란 오브(빠른 맥동).
    phase 1=시전 백스윙, 2=시전 직후(오브 밝게 발광).
    """
    import math
    cx, cy = tile_x + 16, tile_y + 16
    dx, dy = _DIR.get(facing, (0, 1))
    # 손 위치(몸 앞), 지팡이는 손에서 위로 뻗음
    hx = cx + dx * 7
    hy = cy + dy * 7 + (2 if facing == 'down' else -2 if facing == 'up' else 0)
    # 지팡이 상단(오브 위치) — 살짝 앞+위
    tipx = int(hx + dx * 3)
    tipy = int(hy - 11)
    pygame.draw.line(surf, (140, 100, 62), (int(hx), int(hy + 6)), (tipx, tipy), 2)
    pygame.draw.line(surf, (176, 134, 86), (int(hx), int(hy + 5)), (tipx, tipy), 1)
    if subclass == 'battle_mage':          # 전투마법사: 지팡이 끝 단검날
        dx, dy = _DIR.get(facing, (0, 1))
        pygame.draw.line(surf, (225, 120, 110), (tipx, tipy),
                         (int(tipx + dx * 5), int(tipy - 5)), 2)
    # 오브: 시전 직후 크게 발광 (전직별 색/속도)
    _spd = 0.016 if subclass == 'speed_mage' else 0.008
    puls = 0.5 + 0.5 * math.sin(t_ms * _spd)
    base_r = 3 + (2 if phase == 2 else 0)
    orb = {'battle_mage': (255, 96, 84), 'speed_mage': (90, 172, 255)}.get(
        subclass, (150, 110, 245))
    glow = pygame.Surface((16, 16), pygame.SRCALPHA)
    a = int(90 + 60 * puls) + (60 if phase == 2 else 0)
    pygame.draw.circle(glow, (*orb, min(255, a)), (8, 8), base_r + 3)
    surf.blit(glow, (tipx - 8, tipy - 8), special_flags=pygame.BLEND_ADD)
    pygame.draw.circle(surf, (225, 210, 255), (tipx, tipy), base_r)
    pygame.draw.circle(surf, orb, (tipx, tipy), base_r, 1)


# ── 공통 드로우 헬퍼 ─────────────────────────────────────────────────────────
def _c(s, col, x, y, r):
    pygame.draw.circle(s, col, (round(x), round(y)), max(1, r))

def _L(col, v=40): return tuple(min(255, c + v) for c in col)
def _D(col, v=40): return tuple(max(0, c - v) for c in col)


# ── 방향별 장비 기준 오프셋 (타일 중심 x+16, y+16 기준) ─────────────────────
# weapon: 무기 손 위치,  shield: 방패 손 위치,  head: 머리 중심
EQUIPMENT_OFFSETS = {
    'down':  {'weapon': ( 9,  1), 'shield': (-9,  3), 'head': ( 0, -9)},
    'up':    {'weapon': ( 9,  2), 'shield': (-9,  2), 'head': ( 0, -9)},
    'left':  {'weapon': (-9,  2), 'shield': ( 7,  2), 'head': ( 0, -8)},
    'right': {'weapon': ( 9,  2), 'shield': (-7,  2), 'head': ( 0, -8)},
}

# 각 방향에서 무기가 향하는 기본 각도 (도, 0=오른쪽, 90=아래)
_FORWARD_ANGLE = {'down': 90, 'up': 270, 'right': 0, 'left': 180}


# ── 액션 변형(variant)별 무기 포즈 키프레임 ─────────────────────────────────
# (선딜 각도차, 선딜 당김px, 스윙 각도차, 스윙 밀기px)
_VARIANT_POSE = {
    'slash1':   (-65, 3,  +25, 4),    # 정베기 (기존)
    'slash2':   (+65, 3,  -25, 4),    # 역베기 (반대 궤적)
    'finisher': (-100, 4, +35, 7),    # 내려찍기 (크게 들어 강하게)
    'lunge':    (-15, 5,    0, 9),    # 찌르기 (정면 관통)
    'backstep': (+45, 2,  -30, 3),    # 이탈 베기
}


# ── update_equipment_pos ─────────────────────────────────────────────────────
def update_equipment_pos(facing, phase, walk_frame, variant='slash1'):
    """
    무기 레이어의 (dx, dy, angle_deg)를 반환한다.
    phase 0=대기, 1=선딜(풍업), 2=스윙
    variant : 액션 종류별 포즈 키프레임 (_VARIANT_POSE)
    walk_frame 0/1 로 유휴 보핑 연출.
    """
    fwd  = _FORWARD_ANGLE.get(facing, 90)
    bob  = math.sin(walk_frame * _PI) * 1.5
    frad = math.radians(fwd)

    if phase == 0:
        return (0, bob, fwd - 25)

    wind_a, wind_pull, swing_a, swing_push = _VARIANT_POSE.get(
        variant, _VARIANT_POSE['slash1'])

    if phase == 1:
        # 후방으로 당기기
        pull_x = -math.cos(frad) * wind_pull
        pull_y = -math.sin(frad) * wind_pull - 2
        return (pull_x, pull_y, fwd + wind_a)

    # phase == 2: 스윙 완료
    push_x = math.cos(frad) * swing_push
    push_y = math.sin(frad) * swing_push + 2
    return (push_x, push_y, fwd + swing_a)


# ── 개별 장비 드로우 함수 ────────────────────────────────────────────────────

def _draw_weapon(surf, col, cx, cy, angle_deg):
    """
    각도(angle_deg) 방향으로 뻗는 검 모양 무기.
    손잡이 → 가드 → 날 순서로 원형 파티클 배치.
    """
    ang = math.radians(angle_deg)
    perp = ang + _PI * 0.5
    lc, dc = _L(col, 70), _D(col, 50)

    # 손잡이 (2개, 짧음)
    for i in range(2):
        t = -1 - i * 1.8
        hx = cx + math.cos(ang) * t
        hy = cy + math.sin(ang) * t
        _c(surf, dc, hx, hy, 2)

    # 크로스가드 (수직 2개)
    for sign in (-1, 1):
        gx = cx + math.cos(perp) * sign * 3.5
        gy = cy + math.sin(perp) * sign * 3.5
        _c(surf, _D(col, 60), gx, gy, 2)
        _c(surf, dc, gx, gy, 1)

    # 날 (6개, 끝으로 갈수록 가늘어짐)
    lengths = [2.0, 4.2, 6.5, 8.8, 11.0, 13.0]
    for i, dist in enumerate(lengths):
        bx = cx + math.cos(ang) * dist
        by = cy + math.sin(ang) * dist
        r = max(1, round(2.2 - i * 0.28))
        blade_col = lc if i == 0 else (col if i < 4 else dc)
        _c(surf, blade_col, bx, by, r)

    # 날 끝 하이라이트
    tx = cx + math.cos(ang) * 14.5
    ty = cy + math.sin(ang) * 14.5
    _c(surf, (240, 240, 255), tx, ty, 1)


def _draw_helmet(surf, col, cx, cy, facing, walk_frame):
    """
    기존 기본 투구(금색) 위에 장착 투구 색상으로 덧그린다.
    """
    bob = math.sin(walk_frame * _PI) * 0.6
    lc, dc = _L(col, 60), _D(col, 40)
    cy = cy + bob

    if facing == 'down':
        _c(surf, dc, cx, cy, 6)
        _c(surf, col, cx, cy - 1, 5)
        _c(surf, lc, cx, cy - 2, 3)
        # 챙 양옆
        _c(surf, dc, cx - 5, cy + 1, 2)
        _c(surf, dc, cx + 5, cy + 1, 2)
        # 바이저 슬릿
        pygame.draw.rect(surf, (0, 0, 0), (round(cx) - 3, round(cy), 6, 1))
        # 정수리 깃털/장식
        _c(surf, _L(col, 100), cx, cy - 5, 2)

    elif facing == 'up':
        _c(surf, dc, cx, cy, 6)
        _c(surf, col, cx, cy - 1, 5)
        _c(surf, lc, cx, cy - 2, 3)
        _c(surf, dc, cx - 5, cy + 1, 2)
        _c(surf, dc, cx + 5, cy + 1, 2)
        _c(surf, _L(col, 100), cx, cy - 5, 2)

    else:  # left / right
        flip = 1 if facing == 'right' else -1
        _c(surf, dc, cx, cy, 5)
        _c(surf, col, cx + flip, cy - 1, 4)
        _c(surf, lc, cx + flip * 2, cy - 2, 3)
        # 챙
        _c(surf, dc, cx + flip * 4, cy, 2)
        # 정수리 장식
        _c(surf, _L(col, 100), cx, cy - 5, 2)


def _draw_body_armor(surf, col, cx, cy, facing, walk_frame):
    """
    갑옷: 가슴/어깨 파티클 오버레이. 기존 파란 몸체 위에 덧그린다.
    """
    bob = math.sin(walk_frame * _PI) * 0.8
    lc, dc = _L(col, 50), _D(col, 40)
    cy = cy + bob

    # 중앙 흉갑
    _c(surf, dc, cx, cy, 5)
    _c(surf, col, cx, cy - 1, 4)
    _c(surf, lc, cx, cy - 2, 2)

    if facing in ('down', 'up'):
        # 양쪽 어깨 폴드론
        _c(surf, dc, cx - 7, cy - 2, 3)
        _c(surf, col, cx - 7, cy - 3, 2)
        _c(surf, dc, cx + 7, cy - 2, 3)
        _c(surf, col, cx + 7, cy - 3, 2)
        # 벨트 버클
        _c(surf, _L(col, 90), cx, cy + 6, 2)
    else:
        flip = 1 if facing == 'right' else -1
        _c(surf, dc, cx + flip * 5, cy - 2, 3)
        _c(surf, col, cx + flip * 5, cy - 3, 2)
        _c(surf, _L(col, 90), cx, cy + 6, 2)


def _draw_boots(surf, col, cx, cy, facing, walk_frame):
    """
    신발: 발 위치에 장화 모양 파티클. 보행 프레임으로 발걸음 연출.
    """
    bob  = math.sin(walk_frame * _PI) * 1.2
    lc   = _L(col, 60)
    dc   = _D(col, 50)
    sole = _D(col, 80)     # 밑창

    if facing in ('down', 'up'):
        # 양발 - walk_frame 0: 왼발↓/오른발↑, 1: 반대
        for side, sign in ((-1, 1), (1, -1)):
            step = bob * (1 if walk_frame == 0 else -1) * sign
            fx = cx + side * 5
            fy = cy + 12 + step
            _c(surf, dc,   fx,         fy,     4)   # 발목
            _c(surf, col,  fx,         fy,     3)
            _c(surf, lc,   fx - 1,     fy - 2, 1)   # 하이라이트
            # 밑창
            _c(surf, sole, fx - 1,     fy + 3, 3)
            _c(surf, sole, fx + 2,     fy + 3, 2)   # 코 방향
    else:
        # 측면 — 앞발 하나만 표시
        flip = 1 if facing == 'right' else -1
        fx = cx + flip * 4
        fy = cy + 12 + bob * 0.5
        _c(surf, dc,   fx,           fy,     4)
        _c(surf, col,  fx,           fy,     3)
        _c(surf, lc,   fx,           fy - 2, 1)
        # 코 (앞쪽으로 튀어나온 발끝)
        _c(surf, dc,   fx + flip*3,  fy + 1, 3)
        _c(surf, col,  fx + flip*3,  fy,     2)
        # 밑창
        _c(surf, sole, fx,           fy + 3, 4)
        _c(surf, sole, fx + flip*2,  fy + 3, 3)


def _draw_shield(surf, col, cx, cy, facing):
    """
    방패: 방향에 따라 원형(정면) 또는 타원형(측면) 실루엣.
    """
    lc, dc = _L(col, 70), _D(col, 50)

    if facing in ('down', 'up'):
        # 정면 원형 방패
        _c(surf, dc, cx, cy, 5)
        _c(surf, col, cx, cy, 4)
        _c(surf, lc, cx - 1, cy - 1, 2)
        # 보스 엠블럼
        _c(surf, (255, 255, 255), cx, cy, 1)
    else:
        # 측면 타원형 (납작하게)
        for dy in range(-3, 4):
            w = max(1, round(3 * (1 - abs(dy) / 4)))
            pygame.draw.rect(surf, col,
                             (round(cx) - w, round(cy) + dy, w * 2 + 1, 1))
        _c(surf, lc, cx, cy - 1, 1)


# ── 메인 레이어드 드로우 ──────────────────────────────────────────────────────
def draw_player_layered(surf, tile_x, tile_y, facing,
                        walk_frame, atk_phase, equipment, atk_variant='slash1'):
    """
    이미 body(draw_player 또는 스프라이트)가 그려진 surf 위에
    장비 5 레이어를 순서대로 덧그린다.

    tile_x, tile_y : 타일 좌상단 좌표 (TILE_SIZE=32 기준)
    equipment      : player.equipment dict
    """
    # 장비 오버레이(투구/갑옷/신발/방패/무기)는 '덮어 입은' 느낌이
    # 좋지 않다는 유저 피드백으로 전부 제거 — 장비 시각화는
    # 페이퍼돌 화면(O키) + 장착 순간 아이템 색 버스트가 담당.
    # 액션 타격감은 SmearAnim/잔상/임팩트 프레임이 유지한다.
    return

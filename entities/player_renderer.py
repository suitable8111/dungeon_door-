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


# ── update_equipment_pos ─────────────────────────────────────────────────────
def update_equipment_pos(facing, phase, walk_frame):
    """
    무기 레이어의 (dx, dy, angle_deg)를 반환한다.
    phase 0=대기, 1=선딜(풍업), 2=스윙
    walk_frame 0/1 로 유휴 보핑 연출.
    """
    fwd  = _FORWARD_ANGLE.get(facing, 90)
    bob  = math.sin(walk_frame * _PI) * 1.5
    frad = math.radians(fwd)

    if phase == 0:
        return (0, bob, fwd - 25)

    if phase == 1:
        # 후방으로 당기기
        pull_x = -math.cos(frad) * 3
        pull_y = -math.sin(frad) * 3 - 2
        return (pull_x, pull_y, fwd - 65)

    # phase == 2: 스윙 완료
    push_x = math.cos(frad) * 4
    push_y = math.sin(frad) * 4 + 2
    return (push_x, push_y, fwd + 25)


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
                        walk_frame, atk_phase, equipment):
    """
    이미 body(draw_player 또는 스프라이트)가 그려진 surf 위에
    장비 5 레이어를 순서대로 덧그린다.

    tile_x, tile_y : 타일 좌상단 좌표 (TILE_SIZE=32 기준)
    equipment      : player.equipment dict
    """
    off = EQUIPMENT_OFFSETS.get(facing, EQUIPMENT_OFFSETS['down'])
    cx  = tile_x + 16
    cy  = tile_y + 16

    # ── 레이어 0: 신발 (몸체 아래에 그려야 발이 몸에 가려짐) ──────────────
    feet_item = equipment.get('feet')
    if feet_item is not None:
        _draw_boots(surf, feet_item.color, cx, cy, facing, walk_frame)

    # ── 레이어 1: 갑옷 ────────────────────────────────────────────────
    body_item = equipment.get('body')
    if body_item is not None:
        _draw_body_armor(surf, body_item.color, cx, cy + 2, facing, walk_frame)

    # ── 레이어 2: 투구 ────────────────────────────────────────────────
    head_item = equipment.get('head')
    if head_item is not None:
        hox, hoy = off['head']
        _draw_helmet(surf, head_item.color, cx + hox, cy + hoy, facing, walk_frame)

    # ── 레이어 3: 방패 (무기 아래에 그려야 z-order 자연스러움) ────────────
    shield_item = equipment.get('off_hand')
    if shield_item is not None:
        sox, soy = off['shield']
        _draw_shield(surf, shield_item.color, cx + sox, cy + soy, facing)

    # ── 레이어 4: 무기 ────────────────────────────────────────────────
    weapon_item = equipment.get('weapon')
    if weapon_item is not None:
        wox, woy = off['weapon']
        dx, dy, angle = update_equipment_pos(facing, atk_phase, walk_frame)
        wx = cx + wox + dx
        wy = cy + woy + dy
        _draw_weapon(surf, weapon_item.color, wx, wy, angle)

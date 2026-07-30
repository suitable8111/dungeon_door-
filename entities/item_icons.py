"""마인크래프트 풍 블록 아이템 아이콘.

draw_mc_item(surf, x, y, size, item_type, col) — (x,y) 좌상단 size×size 영역에 그린다.
item_type: weapon/armor/head/boots/off_hand/accessory/consumable/enhance_stone/skillbook
col: 아이템 고유색(희귀도) — 강조/보석/액체에 사용.
"""
import pygame


def _L(c, v=45): return tuple(min(255, k + v) for k in c)
def _D(c, v=45): return tuple(max(0, k - v) for k in c)

_STEEL = (200, 205, 218)
_STEEL_D = (120, 126, 140)
_WOOD = (140, 100, 56)
_WOOD_D = (96, 68, 38)


def _resolve_icon(key, item_type):
    """아이템 key로 특수 채집품 아이콘 종류를 판별 (없으면 None → 타입 렌더)."""
    if not key:
        return None
    if key.startswith(('grilled', 'deluxe')):
        return 'fish'
    if key.startswith('seed_'):
        return 'seed'
    if key == 'food_bread':
        return 'bread'
    if key in ('food_soup', 'food_stew'):
        return 'bowl'
    if key == 'food_pie':
        return 'pie'
    return None


def draw_mc_item(surf, x, y, size, item_type, col, key=None):
    """16×16 논리 그리드를 size에 맞춰 블록 아이템을 그린다."""
    u = max(1, size // 16)
    ox = x + (size - u * 16) // 2
    oy = y + (size - u * 16) // 2

    def B(gx, gy, c, w=1, h=1):
        pygame.draw.rect(surf, c, (ox + gx * u, oy + gy * u, w * u, h * u))

    def diag(cells, c):
        for gx, gy in cells:
            B(gx, gy, c)

    icon = _resolve_icon(key, item_type)
    if icon == 'fish':                           # 생선 (좌향, 꼬리 우측)
        body, d, l = col, _D(col, 45), _L(col, 35)
        B(5, 7, body, 7, 3)                      # 몸통
        B(6, 6, body, 5, 1); B(6, 10, body, 5, 1)
        B(12, 6, d, 2, 1); B(12, 10, d, 2, 1)    # 꼬리 위/아래
        B(13, 7, d, 1, 3)
        B(5, 7, l, 7, 1)                          # 등 광택
        B(6, 8, (245, 248, 250)); B(6, 8, (30, 34, 44))  # 눈(머리 왼쪽)
        B(5, 9, d, 1, 1)                          # 입
        return
    if icon == 'seed':                           # 씨앗 몇 알 + 새싹
        d, l = _D(col, 40), _L(col, 35)
        B(8, 4, (96, 184, 96)); B(7, 5, (96, 184, 96)); B(9, 5, (120, 206, 120))  # 새싹
        B(6, 8, col, 2, 3); B(6, 8, l, 2, 1); B(6, 10, d, 2, 1)   # 씨앗1
        B(9, 9, col, 2, 3); B(9, 9, l, 2, 1); B(9, 11, d, 2, 1)   # 씨앗2
        B(8, 12, col, 2, 2)                       # 씨앗3
        return
    if icon == 'bread':                          # 빵 덩어리
        d, l = _D(col, 45), _L(col, 30)
        B(4, 7, col, 8, 5)
        B(4, 7, l, 8, 1); B(4, 11, d, 8, 1)
        B(4, 8, col, 1, 3); B(11, 8, col, 1, 3)
        B(6, 7, d, 1, 4); B(9, 7, d, 1, 4)        # 칼집
        return
    if icon == 'bowl':                           # 국/스튜 그릇
        bowl, bd = (214, 216, 226), (150, 152, 164)
        B(6, 7, col, 5, 2); B(6, 7, _L(col, 45), 5, 1)   # 국물
        B(4, 9, bowl, 9, 1)                        # 그릇 테두리
        B(5, 10, bowl, 7, 2); B(6, 12, bd, 5, 1)   # 그릇 몸통
        B(4, 9, _L(bowl, 20), 9, 1)
        return
    if icon == 'pie':                            # 파이
        crust, cd, cl = (214, 172, 112), (168, 128, 78), (236, 200, 150)
        B(4, 9, crust, 8, 3)                      # 바닥 크러스트
        B(4, 9, cl, 8, 1); B(4, 11, cd, 8, 1)
        B(5, 7, col, 6, 2)                         # 속(작물색)
        B(5, 7, _L(col, 40), 6, 1)
        B(6, 7, cd, 1, 2); B(8, 7, cd, 1, 2); B(10, 7, cd, 1, 2)  # 격자
        return

    t = item_type
    if t == 'weapon':
        # 대각선 검 (좌하 → 우상)
        blade = _L(col, 30); bl_d = _D(col, 10)
        for i in range(7):
            B(9 + i - 6, 8 - i + 2, blade)      # 날
            B(9 + i - 6, 9 - i + 2, bl_d)
        B(4, 11, _STEEL); B(3, 12, _STEEL)      # 검끝 하이라이트
        B(10, 3, _L(blade, 60))                 # 팁 반짝
        # 가드 + 손잡이
        B(9, 10, (90, 80, 60), 3, 1)            # 가드
        B(11, 11, _WOOD); B(12, 12, _WOOD_D)    # 손잡이
        B(12, 13, (230, 200, 90))               # 폼멜
    elif t == 'armor':
        c, d = col, _D(col, 40); l = _L(col, 30)
        B(5, 3, c, 6, 2)                        # 어깨선
        B(4, 4, c, 8, 7)                        # 몸판
        B(4, 4, l, 8, 1)
        B(4, 10, d, 8, 1)
        B(7, 5, d, 2, 5)                        # 가슴 홈
        B(4, 4, d, 1, 7); B(11, 4, d, 1, 7)     # 옆선
    elif t == 'head':
        c, d = col, _D(col, 40); l = _L(col, 30)
        B(5, 4, c, 6, 5)                        # 투구
        B(4, 5, c, 1, 3); B(11, 5, c, 1, 3)
        B(5, 4, l, 6, 1)
        B(5, 9, d, 6, 1)                        # 얼굴 구멍 윗선
        B(6, 7, (40, 42, 50), 4, 2)            # T자 시야틈
        B(7, 5, (40, 42, 50), 2, 2)
    elif t == 'boots':
        c, d = col, _D(col, 40)
        B(4, 5, c, 3, 6); B(9, 5, c, 3, 6)      # 두 짝
        B(4, 10, d, 5, 2); B(9, 10, d, 5, 2)    # 발끝
        B(4, 5, _L(col, 25), 3, 1); B(9, 5, _L(col, 25), 3, 1)
    elif t == 'off_hand':                        # 방패
        c, d = col, _D(col, 45); l = _L(col, 30)
        B(4, 3, c, 8, 7)
        B(5, 10, c, 6, 1); B(6, 11, c, 4, 1); B(7, 12, c, 2, 1)  # 아래 뾰족
        B(4, 3, l, 8, 1)
        B(4, 3, d, 1, 7); B(11, 3, d, 1, 7)
        B(7, 5, (230, 200, 90), 2, 4)          # 문장(금)
        B(6, 6, (230, 200, 90), 4, 2)
    elif t == 'accessory':                       # 반지
        gold = (232, 196, 90); gd = _D(gold, 40)
        B(5, 7, gold, 6, 1); B(5, 11, gold, 6, 1)
        B(5, 8, gold, 1, 3); B(10, 8, gold, 1, 3)
        B(6, 8, (30, 30, 40), 4, 3)            # 반지 안쪽 구멍
        B(7, 4, _L(col, 40), 2, 2)             # 보석
        B(7, 4, col); B(8, 5, _D(col, 30))
    elif t == 'consumable':                      # 물약병
        glass = (198, 214, 230)
        B(7, 2, (150, 110, 60), 2, 2)          # 코르크
        B(6, 4, glass, 4, 1)
        B(5, 5, glass, 6, 7)                   # 병
        B(5, 12, glass, 6, 1)
        B(6, 8, col, 4, 4)                     # 액체
        B(6, 8, _L(col, 50), 4, 1)             # 액면
        B(6, 6, (255, 255, 255))               # 반짝
    elif t == 'enhance_stone':                   # 마정석/광석
        c, l, d = col, _L(col, 70), _D(col, 50)
        diag([(8, 3), (7, 4), (9, 4)], l)
        B(6, 5, c, 5, 5)
        B(6, 5, l, 5, 1)
        B(6, 9, d, 5, 1)
        B(8, 6, l, 1, 3)                        # 광택 코어
        B(7, 10, c); B(9, 10, c)
    elif t == 'skillbook':                       # 책
        cover = col if col else (150, 60, 60); cd = _D(cover, 40)
        B(4, 3, cd, 8, 10)                     # 뒤표지
        B(4, 3, cover, 7, 10)                  # 앞표지
        B(10, 3, (240, 238, 228), 1, 10)      # 책배(페이지)
        B(5, 5, (230, 210, 120), 5, 1)        # 금박 제목선
        B(5, 8, _L(cover, 30), 5, 1)
    else:
        # 알 수 없는 타입 — 다이아 토큰
        B(7, 4, col, 2, 2); B(6, 6, col, 4, 2)
        B(5, 8, col, 6, 2); B(6, 10, col, 4, 2); B(7, 12, col, 2, 1)

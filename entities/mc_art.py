"""마인크래프트 풍 블록 아트 공용 헬퍼.

32px 타일 = 16×16 논리 그리드(블록 2px). 적/NPC/아이템 스프라이트가 공유한다.
"""
import math
import pygame

U = 2  # 블록 픽셀 크기


def L(col, v=40): return tuple(min(255, c + v) for c in col)
def D(col, v=40): return tuple(max(0, c - v) for c in col)


def B(s, x, y, gx, gy, col, w=1, h=1):
    """타일 좌상단(x,y) 기준 그리드(gx,gy)에 w×h 블록."""
    pygame.draw.rect(s, col, (x + gx * U, y + gy * U, w * U, h * U))


def bob_offset(t, speed=2.5, amp=1.0, phase=0.0):
    """유휴 상승/하강 애니 오프셋(px)."""
    return math.sin(t * 0.001 * speed + phase) * amp


def checker(s, x, y, gx0, gy0, w, h, col, dark=None):
    """체커 무늬 몸통 블록 채우기."""
    dc = dark if dark else D(col, 26)
    for gy in range(gy0, gy0 + h):
        for gx in range(gx0, gx0 + w):
            B(s, x, y, gx, gy, col if (gx + gy) % 2 == 0 else dc)


def eyes(s, x, y, gx_l, gx_r, gy, col=(255, 60, 60)):
    """블록 눈 한 쌍."""
    B(s, x, y, gx_l, gy, col)
    B(s, x, y, gx_r, gy, col)

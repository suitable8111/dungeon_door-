"""정복 일지용 테마 썸네일 아트.

각 테마의 색 팔레트(벽/바닥/계단/배경)로 '빛나는 던전 문' 미니 씬을 절차적으로
그린다. 팔레트가 구간마다 뚜렷이 달라 20개 테마가 시각적으로 구분된다.

썸네일은 (idx, cleared, w, h) 로 캐싱되어 매 프레임 재생성하지 않는다.
미해금 테마는 어둡게 처리 + 자물쇠 실루엣.
"""
import random
import pygame

_CACHE: dict[tuple, pygame.Surface] = {}


def _lerp(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _bricks(surf, area, dim, lit, top, seed):
    """벽돌 벽 패턴."""
    bw = max(7, area.width // 6)
    bh = max(5, area.height // 4)
    rng = random.Random(seed)
    prev_clip = surf.get_clip()
    surf.set_clip(area)
    y = area.top
    row = 0
    while y < area.bottom:
        x = area.left - (bw // 2 if row % 2 else 0)
        while x < area.right:
            col = lit if rng.random() < 0.30 else dim
            pygame.draw.rect(surf, col, (x, y, bw - 1, bh - 1))
            pygame.draw.line(surf, top, (x, y), (x + bw - 2, y))          # 상단 하이라이트
            x += bw
        y += bh
        row += 1
    surf.set_clip(prev_clip)


def _floor(surf, area, dim, lit, edge):
    """바닥 타일."""
    prev_clip = surf.get_clip()
    surf.set_clip(area)
    surf.fill(dim, area)
    tw = max(10, area.width // 5)
    for i in range(0, area.width + tw, tw):
        pygame.draw.line(surf, edge, (area.left + i, area.top),
                         (area.left + i - tw // 3, area.bottom), 1)
    pygame.draw.line(surf, lit, (area.left, area.top), (area.right, area.top), 2)
    surf.set_clip(prev_clip)


def _door(surf, cx, top, dw, dh, theme):
    """중앙 아치형 문 + 빛나는 계단(테마 계단색)."""
    bg = theme['bg']
    glow = theme['stairs_lit']
    sdim = theme['stairs_dim']
    # 문 안쪽 어둠
    inner = pygame.Rect(int(cx - dw / 2), int(top), int(dw), int(dh))
    pygame.draw.rect(surf, _lerp(bg, (0, 0, 0), 0.3), inner,
                     border_top_left_radius=int(dw / 2),
                     border_top_right_radius=int(dw / 2))
    # 빛나는 후광 (문 안쪽 하단)
    gh = max(6, int(dh * 0.5))
    glow_surf = pygame.Surface((inner.width, gh), pygame.SRCALPHA)
    for i in range(gh):
        a = int(150 * (i / gh))
        pygame.draw.line(glow_surf, (*glow, a), (0, i), (inner.width, i))
    surf.blit(glow_surf, (inner.left, inner.bottom - gh))
    # 계단 3단
    steps = 3
    sh = max(2, int(dh * 0.16))
    for s in range(steps):
        sw = int(dw * (0.5 + 0.16 * s))
        sy = int(inner.bottom - (s + 1) * sh)
        col = _lerp(sdim, glow, 0.3 + 0.25 * s)
        pygame.draw.rect(surf, col, (int(cx - sw / 2), sy, sw, sh))
        pygame.draw.line(surf, glow, (int(cx - sw / 2), sy), (int(cx + sw / 2), sy), 1)
    # 문틀
    pygame.draw.rect(surf, theme['wall_top'], inner, 2,
                     border_top_left_radius=int(dw / 2),
                     border_top_right_radius=int(dw / 2))


def _torch(surf, x, y, t, seed):
    """벽 횃불 (따뜻한 불꽃, 살짝 깜빡임)."""
    rng = random.Random(seed)
    flick = 1.0 + 0.18 * pygame.math.Vector2(1, 0).rotate(
        (t * 0.4 + seed * 60)).x
    pygame.draw.rect(surf, (60, 44, 28), (x - 1, y, 2, 7))               # 자루
    fh = int(6 * flick)
    for i, col in enumerate(((255, 210, 120), (255, 150, 50), (230, 90, 20))):
        r = max(1, (3 - i))
        pygame.draw.circle(surf, col, (x, y - fh + i * 2 + rng.randint(0, 1)), r)


def _render_thumb(w, h, idx, theme, cleared, t=0):
    s = pygame.Surface((w, h)).convert()
    # 배경 그라디언트 (bg → wall_dim)
    for y in range(h):
        s.blit(_solid(w, _lerp(theme['bg'], theme['wall_dim'], y / h)), (0, y))
    floor_y = int(h * 0.62)
    _bricks(s, pygame.Rect(0, 0, w, floor_y), theme['wall_dim'],
            theme['wall_lit'], theme['wall_top'], idx * 97 + 3)
    _floor(s, pygame.Rect(0, floor_y, w, h - floor_y),
           theme['floor_dim'], theme['floor_edge'], theme['floor_lit'])
    # 중앙 문 + 계단
    dw = w * 0.34
    dh = h * 0.66
    _door(s, w / 2, floor_y - dh + h * 0.06, dw, dh, theme)
    # 좌우 횃불
    _torch(s, int(w * 0.18), int(h * 0.40), t, idx * 3 + 1)
    _torch(s, int(w * 0.82), int(h * 0.40), t, idx * 3 + 2)
    # 비네트
    vig = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(vig, (0, 0, 0, 90), (0, 0, w, h), border_radius=4)
    pygame.draw.rect(vig, (0, 0, 0, 0), (3, 3, w - 6, h - 6), border_radius=3)
    s.blit(vig, (0, 0))

    if not cleared:
        # 미해금: 어둡게 + 자물쇠
        dark = pygame.Surface((w, h), pygame.SRCALPHA)
        dark.fill((6, 6, 12, 200))
        s.blit(dark, (0, 0))
        lx, ly = w // 2, int(h * 0.46)
        pygame.draw.rect(s, (150, 150, 165), (lx - 7, ly, 14, 11), border_radius=2)
        pygame.draw.arc(s, (150, 150, 165), (lx - 5, ly - 8, 10, 14),
                        3.14, 6.28, 2)
        pygame.draw.rect(s, (40, 40, 52), (lx - 2, ly + 3, 4, 5))
    return s


_SOLID_CACHE: dict = {}


def _solid(w, color):
    key = (w, color)
    surf = _SOLID_CACHE.get(key)
    if surf is None:
        surf = pygame.Surface((w, 1)).convert()
        surf.fill(color)
        _SOLID_CACHE[key] = surf
    return surf


def draw_theme_thumb(surface, rect, idx, theme, cleared, t=0):
    """rect 위치에 테마 썸네일을 그린다.

    (idx, cleared, w, h) 로 캐싱 — 새 테마를 클리어하면 cleared가 바뀌어 재생성된다.
    """
    w, h = rect.width, rect.height
    key = (idx, cleared, w, h)
    base = _CACHE.get(key)
    if base is None:
        base = _render_thumb(w, h, idx, theme, cleared)
        _CACHE[key] = base
    surface.blit(base, rect.topleft)

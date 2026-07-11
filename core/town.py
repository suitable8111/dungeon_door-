"""마을(Town) 씬 — 던전 사이의 안전한 정비 거점.

TownScene은 자체 Dungeon 객체(맵)를 소유해 기존 렌더링 경로를 그대로
재사용한다. NPC 3종:
  · 주막 주모 (storage) : 영구 창고 (storage.json — 사망해도 유지)
  · 대장장이 (smith)    : 골드 소모 장비 강화
  · 포탈 (portal)       : 던전의 마지막 위치로 재진입

던전 상태 보존은 GameManager 역할을 Game._dungeon_session이 담당 —
Dungeon 객체(적 위치·맵·아이템)와 플레이어 좌표를 통째로 들고 있다가
포탈 재진입 시 그대로 복원한다 (디스크 직렬화 불필요, 완전 무손실).
"""
import math

import pygame

from core.constants import TILE_SIZE
from core.lang import t
from map.dungeon import Dungeon
from map.tile import Tile

TOWN_W, TOWN_H = 23, 15

# 마을 전용 테마 (따뜻한 색)
TOWN_THEME = {
    'name': '마을', 'name_en': 'Town', 'name_ja': '村', 'name_zh': '村庄',
    'name_ru': 'Деревня',
    'bg':         (8, 6, 4),
    'wall_lit':   (96, 74, 52),   'wall_dim': (48, 37, 26),
    'wall_top':   (128, 100, 70), 'wall_bot': (56, 43, 30),
    'floor_lit':  (74, 60, 42),   'floor_dim': (40, 32, 22),
    'floor_edge': (92, 75, 54),
    'stairs_lit': (210, 175, 85), 'stairs_dim': (105, 88, 42),
}


class TownScene:
    """마을 맵 + NPC 배치 + 상호작용 판정 + NPC/포탈 렌더링."""

    def __init__(self):
        self.dungeon = self._build_map()
        # NPC 배치 (id, 타일 좌표, 이름 lang 키)
        cx, cy = TOWN_W // 2, TOWN_H // 2
        self.npcs = [
            {'id': 'storage', 'x': 5,          'y': 4,  'name_key': 'npc_storage'},
            {'id': 'smith',   'x': TOWN_W - 6, 'y': 4,  'name_key': 'npc_smith'},
        ]
        self.portal_pos = (cx, TOWN_H - 4)          # 던전 재진입 포탈
        self.spawn_pos  = (cx, cy)                  # 마을 도착 지점

    # ── 맵 생성: 벽으로 둘러싼 개방 광장 ─────────────────────────────
    def _build_map(self) -> Dungeon:
        d = Dungeon(TOWN_W, TOWN_H)
        for y in range(1, TOWN_H - 1):
            for x in range(1, TOWN_W - 1):
                d.tiles[y][x] = Tile.floor()
        for row in d.tiles:                          # 마을은 항상 밝다
            for tile in row:
                tile.visible = tile.explored = True
        return d

    # ── 상호작용 판정 ─────────────────────────────────────────────────
    def npc_near(self, px: int, py: int):
        """플레이어 인접(체비쇼프 1칸) NPC 반환. 없으면 None."""
        for npc in self.npcs:
            if max(abs(npc['x'] - px), abs(npc['y'] - py)) <= 1:
                return npc
        return None

    # ── 렌더링 ────────────────────────────────────────────────────────
    def draw(self, surf, cam_x: int, cam_y: int, px: int, py: int, font):
        ts = TILE_SIZE
        ticks = pygame.time.get_ticks()
        for npc in self.npcs:
            sx = (npc['x'] - cam_x) * ts
            sy = (npc['y'] - cam_y) * ts
            if npc['id'] == 'storage':
                self._draw_storage_npc(surf, sx, sy, ticks)
            else:
                self._draw_smith_npc(surf, sx, sy, ticks)
            # 이름표 + 근접 시 [E] 프롬프트
            label = t(npc['name_key'])
            near = max(abs(npc['x'] - px), abs(npc['y'] - py)) <= 1
            if near:
                label = t('interact_hint') + ' ' + label
            txt = font.render(label, True,
                              (255, 235, 140) if near else (200, 190, 160))
            surf.blit(txt, (sx + ts // 2 - txt.get_width() // 2, sy - 14))

        self.draw_portal(surf, self.portal_pos, cam_x, cam_y)
        # 포탈 라벨
        sx = (self.portal_pos[0] - cam_x) * ts
        sy = (self.portal_pos[1] - cam_y) * ts
        txt = font.render(t('town_portal_label'), True, (170, 140, 255))
        surf.blit(txt, (sx + ts // 2 - txt.get_width() // 2, sy - 14))

    @staticmethod
    def draw_portal(surf, pos, cam_x, cam_y, color=(160, 90, 255)):
        """소용돌이 포탈 — 던전 귀환 포탈과 공용."""
        ts = TILE_SIZE
        cx = (pos[0] - cam_x) * ts + ts // 2
        cy = (pos[1] - cam_y) * ts + ts // 2
        tk = pygame.time.get_ticks() * 0.004
        # 회전하는 이중 링 + 중심 글로우 (연출 확장 지점: 파티클 흡입 등)
        for i, (r, w) in enumerate(((12, 2), (8, 2))):
            wob = math.sin(tk * 2 + i * 2.1) * 1.5
            pygame.draw.circle(surf, color, (cx, cy), r + wob, w)
        for k in range(4):
            a = tk * 3 + k * math.pi / 2
            pygame.draw.circle(surf, (220, 190, 255),
                               (int(cx + math.cos(a) * 10),
                                int(cy + math.sin(a) * 10)), 2)
        pygame.draw.circle(surf, (235, 220, 255), (cx, cy), 3)

    # ── NPC 스프라이트 (절차 픽셀) ────────────────────────────────────
    @staticmethod
    def _draw_storage_npc(s, x, y, tk):
        bob = int(math.sin(tk * 0.003) * 1.5)
        cx, cy = x + 16, y + 16 + bob
        pygame.draw.circle(s, (150, 100, 60), (cx, cy + 3), 8)     # 치마
        pygame.draw.circle(s, (196, 60, 60), (cx, cy - 1), 6)      # 앞치마(적색)
        pygame.draw.circle(s, (235, 200, 170), (cx, cy - 9), 5)    # 얼굴
        pygame.draw.circle(s, (60, 40, 25), (cx, cy - 12), 4)      # 머리(올림)
        pygame.draw.rect(s, (180, 140, 90), (cx + 6, cy - 4, 6, 8))  # 술병
        pygame.draw.rect(s, (120, 80, 40),  (cx + 7, cy - 7, 4, 3))

    @staticmethod
    def _draw_smith_npc(s, x, y, tk):
        swing = math.sin(tk * 0.006)
        cx, cy = x + 16, y + 16
        pygame.draw.circle(s, (70, 60, 58), (cx, cy + 2), 8)       # 몸(가죽 앞치마)
        pygame.draw.circle(s, (110, 90, 80), (cx, cy - 2), 6)
        pygame.draw.circle(s, (225, 180, 150), (cx, cy - 9), 5)    # 얼굴
        pygame.draw.rect(s, (50, 45, 42), (cx - 6, cy - 14, 12, 4))  # 두건
        # 망치 (위아래 스윙)
        hy = cy - 6 - int(abs(swing) * 6)
        pygame.draw.line(s, (120, 90, 60), (cx + 6, cy + 2), (cx + 10, hy), 3)
        pygame.draw.rect(s, (150, 150, 165), (cx + 7, hy - 4, 8, 5))
        if abs(swing) < 0.15:                                       # 타격 스파크
            pygame.draw.circle(s, (255, 210, 90), (cx + 11, hy + 2), 2)

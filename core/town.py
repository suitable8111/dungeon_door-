"""마을(Town) 씬 — 던전 사이의 안전한 정비 거점.

건물 4채가 있는 실제 마을 구성:
  · 여관 (주모)      : 휴식(HP/SP 회복) + 여관밥 버프 (이번 런 최대 HP +10%)
  · 대장간 (대장장이) : 골드 강화 + 내구도 수리
  · 잡화점 (상인)     : 물약/주문서/수리 키트 — 던전보다 저렴
  · 개인 창고 (상자)  : 영구 보관 (storage.json) + 용량 확장 구매
포탈은 남쪽 광장 — 던전의 마지막 위치로 재진입.

던전 상태 보존은 Game._dungeon_session이 담당 (Dungeon 객체 통째 보관).
"""
import math

import pygame

from core.constants import TILE_SIZE
from core.lang import t
from map.dungeon import Dungeon
from map.tile import Tile

TOWN_W, TOWN_H = 31, 21

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
    """마을 맵(건물/장식) + NPC 배치 + 상호작용 판정 + 렌더링."""

    def __init__(self):
        self._deco = {'tree': [], 'lamp': [], 'well': None}
        self.dungeon = self._build_map()
        # NPC/시설 (id, 타일 좌표, 이름 lang 키) — 각 건물 앞/안
        self.npcs = [
            {'id': 'inn',      'x': 6,  'y': 6,  'name_key': 'npc_storage'},
            {'id': 'chest',    'x': 3,  'y': 4,  'name_key': 'npc_chest'},
            {'id': 'smith',    'x': 24, 'y': 6,  'name_key': 'npc_smith'},
            {'id': 'merchant', 'x': 8,  'y': 14, 'name_key': 'npc_merchant'},
            # 시민 (퀘스트 의뢰인) — 광장 주변
            {'id': 'villager_boy',    'x': 12, 'y': 12, 'quest': 'rat_hunt'},
            {'id': 'villager_farmer', 'x': 20, 'y': 11, 'quest': 'centipede_menace'},
            {'id': 'villager_granny', 'x': 24, 'y': 14, 'quest': 'rescue_girl'},
        ]
        self.portal_pos = (TOWN_W // 2, TOWN_H - 4)
        self.spawn_pos  = (TOWN_W // 2, 13)      # 우물 남쪽 광장

    # ── 맵 생성: 광장 + 건물 3채 + 우물/나무/가로등 ──────────────────
    def _build_map(self) -> Dungeon:
        d = Dungeon(TOWN_W, TOWN_H)
        for y in range(1, TOWN_H - 1):
            for x in range(1, TOWN_W - 1):
                d.tiles[y][x] = Tile.floor()

        def building(x, y, w, h, door_dx):
            """벽 외곽 + 내부 바닥 + 남쪽 문."""
            for by_ in range(y, y + h):
                for bx_ in range(x, x + w):
                    edge = (bx_ in (x, x + w - 1) or by_ in (y, y + h - 1))
                    d.tiles[by_][bx_] = Tile.wall() if edge else Tile.floor()
            d.tiles[y + h - 1][x + door_dx] = Tile.floor()   # 문

        building(2, 2, 8, 5, 4)      # 여관 (NW) — 문 (6,6)
        building(21, 2, 8, 5, 3)     # 대장간 (NE) — 문 (24,6)
        building(4, 10, 7, 4, 4)     # 잡화점 (SW) — 문 (8,13)

        # 우물 (중앙, 2×2 통행 불가)
        wx, wy = TOWN_W // 2 - 1, 9
        for oy in range(2):
            for ox in range(2):
                d.tiles[wy + oy][wx + ox] = Tile.wall()
        self._deco['well'] = (wx, wy)

        # 나무 (통행 불가) / 가로등 (통행 가능, 장식)
        for tx, ty in ((2, 18), (28, 18), (28, 12), (2, 9), (17, 3), (13, 3)):
            d.tiles[ty][tx] = Tile.wall()
            self._deco['tree'].append((tx, ty))
        self._deco['lamp'] = [(11, 17), (19, 17), (5, 8), (25, 9)]

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

        # 장식 (나무/우물/가로등)
        for tx, ty in self._deco['tree']:
            self._draw_tree(surf, (tx - cam_x) * ts, (ty - cam_y) * ts)
        if self._deco['well']:
            wx, wy = self._deco['well']
            self._draw_well(surf, (wx - cam_x) * ts, (wy - cam_y) * ts, ticks)
        for lx, ly in self._deco['lamp']:
            self._draw_lamp(surf, (lx - cam_x) * ts, (ly - cam_y) * ts, ticks)

        _SPRITES = {'inn': self._draw_storage_npc, 'smith': self._draw_smith_npc,
                    'merchant': self._draw_merchant_npc, 'chest': self._draw_chest,
                    'villager_boy': self._draw_boy,
                    'villager_farmer': self._draw_farmer,
                    'villager_granny': self._draw_granny}
        from core.quests import giver_name
        for npc in self.npcs:
            sx = (npc['x'] - cam_x) * ts
            sy = (npc['y'] - cam_y) * ts
            _SPRITES[npc['id']](surf, sx, sy, ticks)
            # 이름표 + 근접 시 [E] 프롬프트 (+퀘스트 상태 마커는 게임이 그림)
            label = (t(npc['name_key']) if 'name_key' in npc
                     else giver_name(npc['id']))
            near = max(abs(npc['x'] - px), abs(npc['y'] - py)) <= 1
            if near:
                label = t('interact_hint') + ' ' + label
            txt = font.render(label, True,
                              (255, 235, 140) if near else (200, 190, 160))
            surf.blit(txt, (sx + ts // 2 - txt.get_width() // 2, sy - 14))

        self.draw_portal(surf, self.portal_pos, cam_x, cam_y)
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
        for i, (r, w) in enumerate(((12, 2), (8, 2))):
            wob = math.sin(tk * 2 + i * 2.1) * 1.5
            pygame.draw.circle(surf, color, (cx, cy), r + wob, w)
        for k in range(4):
            a = tk * 3 + k * math.pi / 2
            pygame.draw.circle(surf, (220, 190, 255),
                               (int(cx + math.cos(a) * 10),
                                int(cy + math.sin(a) * 10)), 2)
        pygame.draw.circle(surf, (235, 220, 255), (cx, cy), 3)

    # ── 장식 스프라이트 ───────────────────────────────────────────────
    @staticmethod
    def _draw_tree(s, x, y):
        cx = x + 16
        pygame.draw.rect(s, (92, 62, 34), (cx - 3, y + 16, 6, 14))       # 줄기
        pygame.draw.circle(s, (36, 88, 40), (cx, y + 12), 12)            # 잎
        pygame.draw.circle(s, (52, 118, 56), (cx - 4, y + 8), 8)
        pygame.draw.circle(s, (66, 140, 66), (cx + 4, y + 9), 7)

    @staticmethod
    def _draw_well(s, x, y, tk):
        # 2×2 타일 크기 우물
        pygame.draw.circle(s, (105, 100, 110), (x + 32, y + 34), 24)     # 석축
        pygame.draw.circle(s, (70, 66, 76), (x + 32, y + 34), 18)
        shim = int(4 * math.sin(tk * 0.002))
        pygame.draw.circle(s, (40, 70, 120 + shim), (x + 32, y + 34), 13)  # 수면
        pygame.draw.rect(s, (110, 78, 44), (x + 10, y + 2, 5, 34))       # 지붕 기둥
        pygame.draw.rect(s, (110, 78, 44), (x + 49, y + 2, 5, 34))
        pygame.draw.polygon(s, (150, 60, 45),
                            [(x + 4, y + 8), (x + 32, y - 6), (x + 60, y + 8)])

    @staticmethod
    def _draw_lamp(s, x, y, tk):
        cx = x + 16
        pygame.draw.rect(s, (60, 58, 66), (cx - 2, y + 6, 4, 24))        # 기둥
        glow = 0.7 + 0.3 * math.sin(tk * 0.005 + x)
        pygame.draw.circle(s, (int(255 * glow), int(200 * glow), 60),
                           (cx, y + 5), 4)
        pygame.draw.circle(s, (255, 240, 170), (cx, y + 5), 2)

    @staticmethod
    def _draw_chest(s, x, y, tk):
        pygame.draw.rect(s, (60, 40, 22), (x + 6, y + 12, 20, 14), border_radius=2)
        pygame.draw.rect(s, (120, 82, 40), (x + 7, y + 13, 18, 12), border_radius=2)
        pygame.draw.rect(s, (60, 40, 22), (x + 6, y + 10, 20, 6), border_radius=2)  # 뚜껑
        pygame.draw.rect(s, (230, 190, 90), (x + 14, y + 16, 4, 6))      # 자물쇠
        shine = (pygame.time.get_ticks() // 700) % 3 == 0
        if shine:
            pygame.draw.circle(s, (255, 250, 200), (x + 23, y + 12), 2)

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
        hy = cy - 6 - int(abs(swing) * 6)
        pygame.draw.line(s, (120, 90, 60), (cx + 6, cy + 2), (cx + 10, hy), 3)
        pygame.draw.rect(s, (150, 150, 165), (cx + 7, hy - 4, 8, 5))
        if abs(swing) < 0.15:                                       # 타격 스파크
            pygame.draw.circle(s, (255, 210, 90), (cx + 11, hy + 2), 2)

    @staticmethod
    def _draw_boy(s, x, y, tk):
        hop = int(abs(math.sin(tk * 0.006)) * -3)              # 폴짝폴짝
        cx, cy = x + 16, y + 19 + hop
        pygame.draw.circle(s, (90, 130, 70), (cx, cy + 1), 6)   # 초록 옷
        pygame.draw.circle(s, (240, 205, 170), (cx, cy - 7), 5) # 얼굴
        pygame.draw.circle(s, (150, 100, 50), (cx, cy - 10), 4) # 갈색 머리
        pygame.draw.rect(s, (120, 90, 60), (cx + 5, cy - 4, 3, 9))  # 나무 막대기

    @staticmethod
    def _draw_farmer(s, x, y, tk):
        bob = int(math.sin(tk * 0.0028) * 1.5)
        cx, cy = x + 16, y + 16 + bob
        pygame.draw.circle(s, (130, 105, 60), (cx, cy + 2), 8)  # 작업복
        pygame.draw.circle(s, (225, 185, 150), (cx, cy - 8), 5) # 얼굴
        pygame.draw.ellipse(s, (200, 165, 80), (cx - 9, cy - 15, 18, 7))  # 밀짚모자
        pygame.draw.rect(s, (140, 105, 60), (cx - 11, cy - 8, 3, 20))     # 쇠스랑 자루
        for i in range(3):
            pygame.draw.rect(s, (160, 160, 175), (cx - 13 + i * 3, cy - 12, 2, 5))

    @staticmethod
    def _draw_granny(s, x, y, tk):
        bob = int(math.sin(tk * 0.002) * 1.0)
        cx, cy = x + 16, y + 17 + bob
        pygame.draw.circle(s, (120, 90, 130), (cx, cy + 2), 8)  # 보라 숄
        pygame.draw.circle(s, (235, 200, 175), (cx, cy - 7), 5) # 얼굴
        pygame.draw.circle(s, (215, 215, 220), (cx, cy - 11), 4)  # 흰 머리
        pygame.draw.rect(s, (140, 105, 60), (cx + 7, cy - 6, 3, 16))  # 지팡이

    @staticmethod
    def _draw_merchant_npc(s, x, y, tk):
        bob = int(math.sin(tk * 0.0035 + 2) * 1.5)
        cx, cy = x + 16, y + 16 + bob
        pygame.draw.circle(s, (46, 84, 130), (cx, cy + 2), 8)      # 푸른 로브
        pygame.draw.circle(s, (60, 110, 165), (cx, cy - 2), 6)
        pygame.draw.circle(s, (230, 190, 160), (cx, cy - 9), 5)    # 얼굴
        pygame.draw.polygon(s, (36, 66, 104),                       # 모자
                            [(cx - 7, cy - 11), (cx + 7, cy - 11), (cx, cy - 20)])
        pygame.draw.rect(s, (200, 160, 70), (cx - 11, cy + 2, 7, 7))  # 금화 주머니
        pygame.draw.circle(s, (255, 220, 110), (cx - 8, cy + 3), 2)

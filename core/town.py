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
from entities.mob_sprites import mc_villager, VILLAGER_SPEC, mc_object
from map.dungeon import Dungeon
from map.tile import Tile

# 마을 NPC를 마인크래프트 블록 스타일로 렌더 (False면 기존 아트)
USE_MC_NPC = True

TOWN_W, TOWN_H = 130, 94      # GTA풍 대형 마을 — 구역·도로·강·다리

_CKEY = (255, 0, 255)         # NPC 좌우 반전용 컬러키


def _rand_wait() -> float:
    import random
    return random.uniform(700, 2600)   # 다음 걸음까지 정지 시간 ms

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
    """마을 맵(건물/장식) + NPC 배회 AI + 상호작용 + 렌더링."""

    def __init__(self):
        self._deco = {'tree': [], 'lamp': [], 'well': None, 'statue': None,
                      'flower': [], 'barrel': [], 'stall': [], 'bench': []}
        self._facility_pos = {}      # 시설 문 앞 좌표 (_build_map이 채움)
        self._quest_spots = []       # 퀘스트 시민 배치 지점
        self._citizen_spots = []     # 배회 엑스트라 시민 지점
        self.portal_pos = (64, 88)   # 남쪽 광장
        self.spawn_pos  = (64, 85)
        self.dungeon = self._build_map()

        ts = TILE_SIZE
        self.npcs = []
        # 시설 NPC — 문 앞 상주 (건물별 좌표는 _build_map에서)
        for nid, nk in (('inn', 'npc_storage'), ('chest', 'npc_chest'),
                        ('smith', 'npc_smith'), ('merchant', 'npc_merchant')):
            x, y = self._facility_pos.get(nid, (64, 45))
            self.npcs.append({'id': nid, 'x': x, 'y': y, 'name_key': nk,
                              'home': (x, y), 'fx': x * ts, 'fy': y * ts,
                              'tx': x, 'ty': y, 'wait': 0.0, 'radius': 0,
                              'facing': 1, 'moving': False})
        # 퀘스트 시민 5명 — 배회
        qids = ['villager_boy', 'villager_farmer', 'villager_granny',
                'villager_hunter', 'villager_scholar']
        for i, nid in enumerate(qids):
            x, y = self._quest_spots[i] if i < len(self._quest_spots) else (64, 50)
            self.npcs.append({'id': nid, 'x': x, 'y': y, 'quest': True,
                              'home': (x, y), 'fx': x * ts, 'fy': y * ts,
                              'tx': x, 'ty': y, 'wait': 0.0, 'radius': 6,
                              'facing': 1, 'moving': False})
        # 배회 엑스트라 시민 — 도시 북적임 (비상호작용)
        import random as _r
        _r.seed(7788)
        amb = ['villager_boy', 'villager_farmer', 'villager_granny',
               'villager_hunter', 'villager_scholar']
        for (x, y) in self._citizen_spots:
            self.npcs.append({'id': _r.choice(amb), 'x': x, 'y': y,
                              'ambient': True, 'name_key': 'townsfolk',
                              'home': (x, y), 'fx': x * ts, 'fy': y * ts,
                              'tx': x, 'ty': y, 'wait': _rand_wait(), 'radius': 7,
                              'facing': _r.choice((-1, 1)), 'moving': False})
        # 등장한 시민 giver 집합 (None = 전부 표시, 예: 테스트)
        self.visible_givers = None

    def _npc_shown(self, npc) -> bool:
        if 'quest' not in npc:
            return True
        return self.visible_givers is None or npc['id'] in self.visible_givers

    def visible_npcs(self):
        return [n for n in self.npcs if self._npc_shown(n)]

    # ── 맵 생성: GTA풍 대형 마을 — 구역/도로/강·다리/공원/광장 ──────────
    def _build_map(self) -> Dungeon:
        import random as _r
        _r.seed(20260724)
        W, H = TOWN_W, TOWN_H
        d = Dungeon(W, H)
        deco = self._deco
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                d.tiles[y][x] = Tile.floor()

        def inb(x, y):
            return 1 <= x < W - 1 and 1 <= y < H - 1

        def wall(x, y):
            if inb(x, y):
                d.tiles[y][x] = Tile.wall()

        def floor(x, y):
            if inb(x, y):
                d.tiles[y][x] = Tile.floor()

        def water(x, y):
            if inb(x, y):
                d.tiles[y][x] = Tile.water()

        def blocked(x, y):
            return not d.is_walkable(x, y)

        def building(x, y, w, h, doors=('S',)):
            """벽 사각형 건물 + 지정 변에 문. 남문 앞 타일 반환."""
            for by in range(y, y + h):
                for bx in range(x, x + w):
                    if bx in (x, x + w - 1) or by in (y, y + h - 1):
                        wall(bx, by)
                    else:
                        floor(bx, by)
            cx, cy = x + w // 2, y + h // 2
            for s in doors:
                if s == 'S': floor(cx, y + h - 1)
                elif s == 'N': floor(cx, y)
                elif s == 'W': floor(x, cy)
                elif s == 'E': floor(x + w - 1, cy)
            return (cx, y + h)          # 남문 밖 타일

        def solid_deco(kind, spots):
            for (x, y) in spots:
                if inb(x, y) and not blocked(x, y) and (x, y) not in (self.portal_pos, self.spawn_pos):
                    wall(x, y); deco[kind].append((x, y))

        def flat_deco(kind, spots):
            for (x, y) in spots:
                if inb(x, y) and not blocked(x, y):
                    deco[kind].append((x, y))

        # ── 강 (수평 밴드 2줄) + 다리 5개 ──────────────────────────────
        RY = 56
        for x in range(5, W - 5):
            water(x, RY); water(x, RY + 1)
        BRIDGES = [18, 42, 65, 88, 112]
        for bx in BRIDGES:
            for w in (-1, 0, 1):
                floor(bx + w, RY); floor(bx + w, RY + 1)
            deco['lamp'] += [(bx - 2, RY - 1), (bx + 2, RY + 2)]

        # ── 북부: 여관 / 시장(상인) / 대장간 ────────────────────────────
        self._facility_pos['inn']      = building(10, 10, 13, 9)          # 여관 NW
        self._facility_pos['smith']    = building(104, 10, 14, 9)         # 대장간 NE
        self._facility_pos['merchant'] = building(58, 8, 14, 9)           # 시장 상점 N-중앙
        # 북부 민가들
        for bx, by, bw, bh in ((30, 8, 9, 7), (42, 12, 8, 6), (84, 10, 10, 7),
                               (26, 24, 9, 7), (92, 26, 10, 7), (12, 30, 9, 6),
                               (114, 32, 8, 6)):
            building(bx, by, bw, bh)

        # ── 중앙 광장: 분수 + 동상 + 벤치 ──────────────────────────────
        fx0, fy0 = 60, 36
        for oy in range(3):
            for ox in range(3):
                wall(fx0 + ox, fy0 + oy)
        deco['well'] = (fx0, fy0)
        deco['statue'] = (66, 40)
        for oy in range(2):
            for ox in range(2):
                wall(66 + ox, 40 + oy)
        solid_deco('bench', [(58, 41), (58, 43), (70, 41), (70, 43)])

        # ── 시장 거리: 좌판 다수 (상인 앞) ─────────────────────────────
        mstalls = [(52, 20), (54, 20), (56, 20), (58, 22), (62, 22), (66, 20),
                   (70, 20), (72, 22), (76, 20), (50, 24), (74, 24)]
        solid_deco('stall', mstalls)

        # ── 남부: 주택가(SW/SE) + 창고(부두) + 공원 ────────────────────
        for bx, by, bw, bh in ((10, 66, 9, 7), (22, 70, 8, 6), (12, 80, 10, 7),
                               (30, 78, 9, 6), (100, 66, 10, 7), (114, 70, 8, 6),
                               (98, 80, 11, 7), (86, 74, 9, 6)):
            building(bx, by, bw, bh)
        # 창고(부두) — 강 남쪽, chest NPC 앞
        chest_door = building(28, 62, 8, 6)
        self._facility_pos['chest'] = chest_door
        solid_deco('barrel', [(24, 62), (24, 64), (38, 62), (38, 64)])

        # 공원(S-중앙) — 연못 + 나무 + 꽃
        for py in range(72, 80):
            for px in range(54, 68):
                if (px - 61) ** 2 + ((py - 76) * 1.6) ** 2 <= 42:
                    water(px, py)
        solid_deco('tree', [(50, 70), (52, 84), (70, 70), (72, 84), (48, 78),
                            (74, 78), (61, 68), (58, 86), (64, 86)])
        flat_deco('flower', [(56, 70), (66, 70), (56, 82), (66, 82), (61, 84)])

        # ── 도로변 가로등 + 대장간 통 + 외곽 나무 ──────────────────────
        flat_deco('lamp', [(28, 20), (44, 20), (82, 20), (98, 20),
                           (28, 46), (52, 48), (78, 48), (98, 46),
                           (40, 66), (90, 66), (20, 84), (108, 84),
                           (64, 30), (64, 50), (48, 34), (80, 34)])
        solid_deco('barrel', [(100, 20), (100, 22), (118, 20)])
        solid_deco('tree', [(3, 12), (3, 24), (3, 40), (3, 72), (3, 86),
                           (126, 12), (126, 24), (126, 40), (126, 72), (126, 86),
                           (44, 4), (64, 4), (86, 4), (20, 90), (44, 90),
                           (86, 90), (110, 90)])
        flat_deco('flower', [(44, 40), (80, 40), (36, 30), (94, 40), (30, 50), (100, 50)])

        # ── NPC 배치 지점 (퀘스트 5 + 배회 시민 다수) ──────────────────
        self._quest_spots = [(46, 44), (82, 44), (34, 36), (96, 44), (64, 24)]
        cit = [(40, 30), (52, 32), (76, 32), (88, 30), (30, 44), (100, 40),
               (46, 50), (82, 50), (24, 68), (108, 68), (40, 82), (94, 82),
               (60, 66), (70, 66), (64, 80), (36, 50), (92, 50), (64, 44)]
        self._citizen_spots = [(x, y) for (x, y) in cit if not blocked(x, y)]

        # 스폰/포탈 주변 확실히 개방 (장식·건물과 겹치지 않게)
        for (sx, sy) in (self.spawn_pos, self.portal_pos):
            for oy in range(-1, 2):
                for ox in range(-1, 2):
                    floor(sx + ox, sy + oy)

        for row in d.tiles:                          # 마을은 항상 밝다
            for tile in row:
                tile.visible = tile.explored = True
        return d

    # ── 배회 AI ───────────────────────────────────────────────────────
    _WANDER_SPEED = 1.5   # 타일/초

    def update(self, dt_ms: float, px: int, py: int):
        """NPC가 home 주변을 자연스럽게 배회. 플레이어가 가까우면 멈춰 바라봄."""
        ts = TILE_SIZE
        step = self._WANDER_SPEED * ts * (dt_ms / 1000.0)
        # 점유 타일 (겹침 방지)
        occ = {(n['tx'], n['ty']) for n in self.npcs}
        occ |= {(n['x'], n['y']) for n in self.npcs}
        occ.add((px, py)); occ.add(self.portal_pos)
        for npc in self.visible_npcs():
            if npc['radius'] <= 0:
                continue
            tgt_x, tgt_y = npc['tx'] * ts, npc['ty'] * ts
            dx, dy = tgt_x - npc['fx'], tgt_y - npc['fy']
            dist = math.hypot(dx, dy)
            if dist > 1.0:                                # 이동 중
                npc['moving'] = True
                mv = min(step, dist)
                npc['fx'] += dx / dist * mv
                npc['fy'] += dy / dist * mv
                if abs(dx) > 1:
                    npc['facing'] = 1 if dx > 0 else -1
                if dist - mv <= 1.0:                      # 도착 → 타일 확정
                    npc['fx'], npc['fy'] = tgt_x, tgt_y
                    npc['x'], npc['y'] = npc['tx'], npc['ty']
                    npc['wait'] = _rand_wait()
            else:                                         # 정지 대기
                npc['moving'] = False
                # 플레이어가 2칸 이내면 배회 멈추고 바라봄
                if max(abs(npc['x'] - px), abs(npc['y'] - py)) <= 2:
                    if px != npc['x']:
                        npc['facing'] = 1 if px > npc['x'] else -1
                    npc['wait'] = 500.0
                    continue
                npc['wait'] -= dt_ms
                if npc['wait'] <= 0:
                    self._pick_target(npc, occ)

    def _pick_target(self, npc, occ):
        import random as _r
        hx, hy = npc['home']
        cands = []
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = npc['x'] + ddx, npc['y'] + ddy
            if not self.dungeon.is_walkable(nx, ny):
                continue
            if abs(nx - hx) + abs(ny - hy) > npc['radius']:
                continue
            if (nx, ny) in occ:
                continue
            cands.append((nx, ny))
        if cands:
            npc['tx'], npc['ty'] = _r.choice(cands)
        else:
            npc['wait'] = _rand_wait()

    # ── 상호작용 판정 ─────────────────────────────────────────────────
    def npc_near(self, px: int, py: int):
        """플레이어 인접(체비쇼프 1칸) NPC 반환 — 등장한 NPC만. 없으면 None."""
        for npc in self.visible_npcs():
            if max(abs(npc['x'] - px), abs(npc['y'] - py)) <= 1:
                return npc
        return None

    # ── 렌더링 ────────────────────────────────────────────────────────
    def draw(self, surf, cam_x: int, cam_y: int, px: int, py: int, font):
        ts = TILE_SIZE
        ticks = pygame.time.get_ticks()
        ox, oy = cam_x * ts, cam_y * ts

        # 바닥 장식 (NPC 아래)
        for fx, fy in self._deco['flower']:
            self._draw_flower(surf, fx * ts - ox, fy * ts - oy, ticks)
        for lx, ly in self._deco['lamp']:
            self._draw_lamp(surf, lx * ts - ox, ly * ts - oy, ticks)
        # 입체 장식 (통행 불가)
        for tx, ty in self._deco['tree']:
            self._draw_tree(surf, tx * ts - ox, ty * ts - oy)
        for bx, by in self._deco['barrel']:
            self._draw_barrel(surf, bx * ts - ox, by * ts - oy)
        for sx, sy in self._deco['stall']:
            self._draw_stall(surf, sx * ts - ox, sy * ts - oy)
        for bx, by in self._deco['bench']:
            self._draw_bench(surf, bx * ts - ox, by * ts - oy)
        if self._deco['well']:
            wx, wy = self._deco['well']
            self._draw_well(surf, wx * ts - ox, wy * ts - oy, ticks)
        if self._deco.get('statue'):
            stx, sty = self._deco['statue']
            self._draw_statue(surf, stx * ts - ox, sty * ts - oy, ticks)

        self.draw_portal(surf, self.portal_pos, cam_x, cam_y)

        _LEGACY = {'inn': self._draw_storage_npc, 'smith': self._draw_smith_npc,
                   'merchant': self._draw_merchant_npc, 'chest': self._draw_chest,
                   'villager_boy': self._draw_boy,
                   'villager_farmer': self._draw_farmer,
                   'villager_granny': self._draw_granny,
                   'villager_hunter': self._draw_hunter,
                   'villager_scholar': self._draw_scholar}

        def _draw_one(target, dx, dy, npc_id):
            if USE_MC_NPC and npc_id == 'chest':
                mc_object(target, dx, dy, (150, 110, 60), ticks, kind='chest')
            elif USE_MC_NPC and npc_id in VILLAGER_SPEC:
                mc_villager(target, dx, dy, ticks, **VILLAGER_SPEC[npc_id])
            else:
                _LEGACY[npc_id](target, dx, dy, ticks)

        from core.quests import giver_name
        # y 정렬 — 아래쪽 NPC가 앞에 그려져 자연스러운 겹침
        for npc in sorted(self.visible_npcs(), key=lambda n: n['fy']):
            sx = int(npc['fx'] - ox)
            sy = int(npc['fy'] - oy)
            walk = int(math.sin(ticks * 0.02)) if npc.get('moving') else 0
            if npc.get('facing', 1) < 0:                 # 좌향 → 좌우 반전
                tmp = pygame.Surface((ts, ts), pygame.SRCALPHA)
                _draw_one(tmp, 0, walk, npc['id'])
                surf.blit(pygame.transform.flip(tmp, True, False), (sx, sy))
            else:
                _draw_one(surf, sx, sy + walk, npc['id'])
            # 이름표 + 근접 시 [E]
            label = (t(npc['name_key']) if 'name_key' in npc
                     else giver_name(npc['id']))
            near = (max(abs(npc['x'] - px), abs(npc['y'] - py)) <= 1
                    and not npc.get('ambient'))     # 배회 시민은 상호작용 없음
            if near:
                label = t('interact_hint') + ' ' + label
            txt = font.render(label, True,
                              (255, 235, 140) if near else (200, 190, 160))
            surf.blit(txt, (sx + ts // 2 - txt.get_width() // 2, sy - 14))

        sx = self.portal_pos[0] * ts - ox
        sy = self.portal_pos[1] * ts - oy
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
    def _draw_statue(s, x, y, tk):
        """영웅 동상 — 2×2 타일. 돌 받침 + 검을 든 석상."""
        cx = x + 32
        # 받침대
        pygame.draw.rect(s, (86, 82, 90), (x + 8, y + 40, 48, 24))
        pygame.draw.rect(s, (110, 106, 116), (x + 8, y + 40, 48, 5))
        pygame.draw.rect(s, (64, 60, 68), (x + 12, y + 46, 40, 3))
        # 석상 몸통(회색 돌)
        stone, stone_hi = (150, 148, 158), (185, 183, 194)
        pygame.draw.rect(s, stone, (cx - 8, y + 20, 16, 22))       # 몸통
        pygame.draw.rect(s, stone_hi, (cx - 8, y + 20, 4, 22))
        pygame.draw.circle(s, stone, (cx, y + 14), 7)              # 머리
        pygame.draw.circle(s, stone_hi, (cx - 2, y + 12), 3)
        # 치켜든 검
        pygame.draw.line(s, (205, 208, 220), (cx + 8, y + 26), (cx + 16, y + 2), 3)
        pygame.draw.line(s, (150, 120, 60), (cx + 5, y + 27), (cx + 11, y + 24), 3)  # 손잡이
        # 은은한 반짝임
        if (tk // 400) % 3 == 0:
            pygame.draw.circle(s, (255, 250, 220), (cx + 16, y + 3), 2)

    @staticmethod
    def _draw_lamp(s, x, y, tk):
        cx = x + 16
        pygame.draw.rect(s, (60, 58, 66), (cx - 2, y + 6, 4, 24))        # 기둥
        glow = 0.7 + 0.3 * math.sin(tk * 0.005 + x)
        pygame.draw.circle(s, (int(255 * glow), int(200 * glow), 60),
                           (cx, y + 5), 4)
        pygame.draw.circle(s, (255, 240, 170), (cx, y + 5), 2)

    @staticmethod
    def _draw_flower(s, x, y, tk):
        cols = ((235, 90, 110), (245, 200, 80), (170, 120, 235), (240, 240, 250))
        for i, (ox, oy) in enumerate(((8, 20), (16, 12), (22, 22), (13, 25))):
            c = cols[i % len(cols)]
            pygame.draw.circle(s, (60, 120, 55), (x + ox, y + oy + 3), 2)  # 잎
            pygame.draw.circle(s, c, (x + ox, y + oy), 2)

    @staticmethod
    def _draw_barrel(s, x, y):
        pygame.draw.rect(s, (90, 60, 32), (x + 8, y + 10, 16, 18), border_radius=3)
        pygame.draw.rect(s, (120, 82, 44), (x + 9, y + 11, 14, 16), border_radius=3)
        pygame.draw.rect(s, (70, 48, 26), (x + 8, y + 14, 16, 2))
        pygame.draw.rect(s, (70, 48, 26), (x + 8, y + 22, 16, 2))

    @staticmethod
    def _draw_stall(s, x, y):
        pygame.draw.rect(s, (110, 78, 44), (x + 4, y + 14, 24, 12))      # 판매대
        for i in range(4):                                              # 줄무늬 차양
            c = (200, 70, 60) if i % 2 == 0 else (235, 225, 210)
            pygame.draw.rect(s, c, (x + 3 + i * 6, y + 4, 6, 7))
        pygame.draw.circle(s, (235, 120, 60), (x + 10, y + 16), 2)      # 과일
        pygame.draw.circle(s, (120, 200, 90), (x + 18, y + 16), 2)

    @staticmethod
    def _draw_bench(s, x, y):
        pygame.draw.rect(s, (110, 78, 44), (x + 5, y + 16, 22, 5))       # 좌판
        pygame.draw.rect(s, (86, 58, 30), (x + 6, y + 21, 3, 6))         # 다리
        pygame.draw.rect(s, (86, 58, 30), (x + 23, y + 21, 3, 6))
        pygame.draw.rect(s, (96, 66, 36), (x + 5, y + 10, 22, 3))        # 등받이

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
    def _draw_hunter(s, x, y, tk):
        bob = int(math.sin(tk * 0.003 + 1) * 1.5)
        cx, cy = x + 16, y + 16 + bob
        pygame.draw.circle(s, (70, 95, 55), (cx, cy + 2), 8)      # 녹색 가죽옷
        pygame.draw.circle(s, (230, 190, 155), (cx, cy - 8), 5)   # 얼굴
        pygame.draw.polygon(s, (90, 70, 40),                       # 뾰족 후드
                            [(cx - 6, cy - 10), (cx + 6, cy - 10), (cx, cy - 19)])
        pygame.draw.arc(s, (150, 120, 70),                         # 활
                        (cx + 5, cy - 12, 12, 24), -1.2, 1.2, 2)
        pygame.draw.line(s, (200, 200, 210), (cx + 6, cy - 11), (cx + 6, cy + 11), 1)

    @staticmethod
    def _draw_scholar(s, x, y, tk):
        bob = int(math.sin(tk * 0.0024 + 3) * 1.2)
        cx, cy = x + 16, y + 16 + bob
        pygame.draw.circle(s, (60, 60, 120), (cx, cy + 2), 8)     # 남색 로브
        pygame.draw.circle(s, (232, 196, 164), (cx, cy - 8), 5)   # 얼굴
        pygame.draw.rect(s, (40, 40, 80), (cx - 6, cy - 13, 12, 4))  # 학사모 챙
        pygame.draw.rect(s, (40, 40, 80), (cx - 3, cy - 17, 6, 5))
        pygame.draw.rect(s, (200, 180, 130), (cx + 5, cy - 4, 6, 8))  # 책
        pygame.draw.line(s, (120, 90, 60), (cx + 8, cy - 4), (cx + 8, cy + 4), 1)

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

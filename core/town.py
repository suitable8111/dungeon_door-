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

# ── 농장(인터랙티브) ─────────────────────────────────────────────────────
FARM_PLOTS = [(x, y) for y in (43, 46, 49) for x in (17, 20, 23, 26)]  # 12개 밭칸
FARM_GROW_MAX = 2             # 심고 마을 N번 재방문하면 수확 가능
# (id, 표시색, 수확 골드) — 심을 때 무작위 선택
CROPS = [('wheat', (224, 198, 96), 30), ('tomato', (226, 84, 66), 45),
         ('pumpkin', (234, 152, 52), 60), ('carrot', (232, 142, 72), 40)]

# ── 낚시(인터랙티브) ─────────────────────────────────────────────────────
RIVER_Y = 56                  # 강 밴드 상단 y (물 타일 56~57)

# ── 목장(가축 사육) ──────────────────────────────────────────────────────
RANCH_PENS = [(x, y) for y in (44, 48) for x in (101, 105, 109)]  # 6개 우리
RANCH_FEED_MAX = 2            # 먹이 주고 마을 N번 재방문하면 생산물 수확


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
                      'flower': [], 'barrel': [], 'stall': [], 'bench': [],
                      'crop': [], 'fence': []}
        self._facility_pos = {}      # 시설 문 앞 좌표 (_build_map이 채움)
        self._quest_spots = []       # 퀘스트 시민 배치 지점
        self._citizen_spots = []     # 배회 엑스트라 시민 지점
        self._animal_spots = []      # 농장 동물 배치 지점
        self._coop_spots = []        # 닭농장 닭 배치 지점
        self._coop_bounds = None     # 닭농장 마당 범위 (배회 가둠)
        self.portal_pos = (64, 88)   # 남쪽 광장
        self.spawn_pos  = (64, 85)
        self.dungeon = self._build_map()

        ts = TILE_SIZE
        self.home_style = 0          # 내 집 인테리어 스타일 (게임이 기록에서 주입)
        self.trophies = {}           # 처치한 테마 보스 전리품 {theme_idx: count} (게임 주입)
        self.farm = [{'crop': None, 'stage': 0} for _ in FARM_PLOTS]  # 밭 상태(게임 주입)
        self.ranch = [{'animal': None, 'fed': False, 'stage': 0}
                      for _ in RANCH_PENS]                             # 목장 상태(게임 주입)
        self.npcs = []
        # 시설 NPC — 문 앞 상주 (건물별 좌표는 _build_map에서)
        for nid, nk in (('inn', 'npc_storage'), ('chest', 'npc_chest'),
                        ('smith', 'npc_smith'), ('merchant', 'npc_merchant')):
            x, y = self._facility_pos.get(nid, (64, 45))
            self.npcs.append({'id': nid, 'x': x, 'y': y, 'name_key': nk,
                              'home': (x, y), 'fx': x * ts, 'fy': y * ts,
                              'tx': x, 'ty': y, 'wait': 0.0, 'radius': 0,
                              'facing': 1, 'moving': False})
        # 내 집 인테리어 관리 보드 (E로 커스터마이즈)
        hx, hy = self._facility_pos.get('home', (39, 50))
        self.npcs.append({'id': 'home_board', 'x': hx, 'y': hy, 'name_key': 'home_board',
                          'home': (hx, hy), 'fx': hx * ts, 'fy': hy * ts,
                          'tx': hx, 'ty': hy, 'wait': 0.0, 'radius': 0,
                          'facing': 1, 'moving': False})
        # 내 집 보관함 (E로 창고 열기, 최대 100)
        for (chx, chy) in ((hx - 3, hy), (hx - 2, hy), (hx + 3, hy)):
            if self.dungeon.is_walkable(chx, chy):
                self.npcs.append({'id': 'home_chest', 'x': chx, 'y': chy,
                                  'name_key': 'home_chest',
                                  'home': (chx, chy), 'fx': chx * ts, 'fy': chy * ts,
                                  'tx': chx, 'ty': chy, 'wait': 0.0, 'radius': 0,
                                  'facing': 1, 'moving': False})
                break
        # 고대 제단지기 — 밭 근처 상주 (E로 희귀식물 교환/영구강화)
        for (ax, ay) in ((30, 46), (30, 43), (30, 49), (14, 46), (32, 46)):
            if self.dungeon.is_walkable(ax, ay):
                self.npcs.append({'id': 'altar', 'x': ax, 'y': ay,
                                  'name_key': 'altar_keeper',
                                  'home': (ax, ay), 'fx': ax * ts, 'fy': ay * ts,
                                  'tx': ax, 'ty': ay, 'wait': 0.0, 'radius': 0,
                                  'facing': 1, 'moving': False})
                break
        # 낚시 노인 — 강둑 상주 (E로 물고기→고대 유물 교환)
        for (fx, fy) in ((50, RIVER_Y - 1), (76, RIVER_Y + 2),
                         (28, RIVER_Y - 1), (100, RIVER_Y + 2)):
            if self.dungeon.is_walkable(fx, fy) and self.water_adjacent(fx, fy):
                self.npcs.append({'id': 'angler', 'x': fx, 'y': fy,
                                  'name_key': 'angler_keeper',
                                  'home': (fx, fy), 'fx': fx * ts, 'fy': fy * ts,
                                  'tx': fx, 'ty': fy, 'wait': 0.0, 'radius': 0,
                                  'facing': 1, 'moving': False})
                break
        # 퀘스트 시민 5명 — 배회
        qids = ['villager_boy', 'villager_farmer', 'villager_granny',
                'villager_hunter', 'villager_scholar']
        for i, nid in enumerate(qids):
            x, y = self._quest_spots[i] if i < len(self._quest_spots) else (64, 50)
            self.npcs.append({'id': nid, 'x': x, 'y': y, 'quest': True,
                              'home': (x, y), 'fx': x * ts, 'fy': y * ts,
                              'tx': x, 'ty': y, 'wait': 0.0, 'radius': 6,
                              'facing': 1, 'moving': False})
        # 용병 길드 게시판 — 광장 근처 상주 (E로 협동 전용 퀘스트, 멀티 중에만 활성)
        for (bx, by) in ((55, 44), (55, 46), (52, 44), (70, 46), (62, 44)):
            if self.dungeon.is_walkable(bx, by) and (bx, by) not in (self.portal_pos, self.spawn_pos):
                self.npcs.append({'id': 'party_board', 'x': bx, 'y': by,
                                  'name_key': 'party_board',
                                  'home': (bx, by), 'fx': bx * ts, 'fy': by * ts,
                                  'tx': bx, 'ty': by, 'wait': 0.0, 'radius': 0,
                                  'facing': 1, 'moving': False})
                break
        # 명예의 전당(랭킹 게시판) — 광장 근처 상주 (E로 전세계 랭킹)
        for (rx, ry) in ((59, 44), (59, 46), (62, 46), (52, 46), (55, 42)):
            if self.dungeon.is_walkable(rx, ry) and (rx, ry) not in (self.portal_pos, self.spawn_pos) \
                    and not any(n['x'] == rx and n['y'] == ry for n in self.npcs):
                self.npcs.append({'id': 'ranking_board', 'x': rx, 'y': ry,
                                  'name_key': 'ranking_board',
                                  'home': (rx, ry), 'fx': rx * ts, 'fy': ry * ts,
                                  'tx': rx, 'ty': ry, 'wait': 0.0, 'radius': 0,
                                  'facing': 1, 'moving': False})
                break
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
        # 농장 동물 — 밭 안(울타리 범위)을 어슬렁 (비상호작용)
        kinds = ['chicken', 'cow', 'sheep', 'pig']
        FARM_BOUNDS = (16, 41, 29, 52)
        for i, (x, y) in enumerate(self._animal_spots):
            self.npcs.append({'id': 'animal', 'animal': kinds[i % len(kinds)],
                              'x': x, 'y': y, 'ambient': True,
                              'home': (x, y), 'fx': x * ts, 'fy': y * ts,
                              'tx': x, 'ty': y, 'wait': _rand_wait(), 'radius': 4,
                              'bounds': FARM_BOUNDS,
                              'facing': _r.choice((-1, 1)), 'moving': False})
        # 닭농장 — 닭 무리가 마당(울타리 안)을 활발히 돌아다님 (비상호작용)
        for (x, y) in self._coop_spots:
            self.npcs.append({'id': 'animal', 'animal': 'chicken',
                              'x': x, 'y': y, 'ambient': True,
                              'home': (x, y), 'fx': x * ts, 'fy': y * ts,
                              'tx': x, 'ty': y, 'wait': _rand_wait() * 0.5, 'radius': 5,
                              'bounds': self._coop_bounds,
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
        self._houses = []
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

        def building(x, y, w, h, kind='house', wing=None, sign=None, home=False):
            """벽 건물(옵션 L자 wing) + 남문 + 지붕/실내용 정보 기록. 남문 앞 타일 반환.
            wing=(wx,wy,ww,wh) 를 주면 두 사각형 합집합의 경계만 벽 → L자 집.
            sign: 간판 아이콘, home=True: 플레이어 집."""
            rects = [(x, y, w, h)] + ([wing] if wing else [])
            cells = set()
            for (rx, ry, rw, rh) in rects:
                for by in range(ry, ry + rh):
                    for bx in range(rx, rx + rw):
                        cells.add((bx, by))
            for (bx, by) in cells:          # 합집합 경계=벽, 내부=바닥
                if any((bx + dx, by + dy) not in cells
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    wall(bx, by)
                else:
                    floor(bx, by)
            cx = x + w // 2
            floor(cx, y + h - 1)            # 남문
            # 실내 타일 집합(합집합의 진짜 내부 = 4방향 이웃이 모두 집 안) + 문
            interior = {(bx, by) for (bx, by) in cells
                        if all((bx + dx, by + dy) in cells
                               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
            interior.add((cx, y + h - 1))
            self._houses.append({'rects': rects, 'door': (cx, y + h - 1),
                                 'inside': interior, 'sign': sign, 'home': home,
                                 'seed': (x * 7 + y * 13) % 1000, 'kind': kind})
            return (cx, y + h)              # 남문 밖 타일

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

        # ── 북부: 여관 / 시장(상인) / 대장간 (L자·용도별 실내) ─────────────
        self._facility_pos['inn']      = building(10, 10, 13, 9, kind='inn',
                                                  wing=(20, 7, 6, 6), sign='inn')  # 여관 L자 NW
        self._facility_pos['smith']    = building(104, 10, 14, 9, kind='smith', sign='smith')  # 대장간 NE
        self._facility_pos['merchant'] = building(58, 8, 14, 9, kind='merchant', sign='merchant')  # 시장 상점
        # 북부 민가들 (일부 L자)
        building(30, 8, 9, 7)
        building(42, 12, 8, 6)
        building(84, 10, 10, 7, wing=(92, 8, 5, 5))     # L자
        building(26, 24, 9, 7)
        building(92, 26, 10, 7, wing=(92, 24, 5, 4))    # L자
        building(12, 30, 9, 6)
        building(114, 32, 8, 6)

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
        building(10, 66, 9, 7, wing=(18, 66, 5, 5))     # L자
        building(22, 74, 8, 6)
        building(12, 80, 10, 7)
        building(30, 78, 9, 6)
        building(100, 66, 10, 7)
        building(114, 70, 8, 6)
        building(98, 80, 11, 7, wing=(107, 80, 5, 5))   # L자
        building(86, 74, 9, 6)
        # 창고(부두) — 강 남쪽, chest NPC 앞
        chest_door = building(28, 62, 9, 6, kind='chest', sign='chest')
        self._facility_pos['chest'] = chest_door
        solid_deco('barrel', [(24, 62), (24, 64), (38, 62), (38, 64)])

        # ── 내 집 (플레이어 소유, 커스터마이즈 가능) — 강 북쪽 중서부 ──────
        self._facility_pos['home'] = building(34, 42, 10, 8, kind='home',
                                              sign='home', home=True)

        # 공원(S-중앙) — 연못 + 나무 + 꽃
        for py in range(72, 80):
            for px in range(54, 68):
                if (px - 61) ** 2 + ((py - 76) * 1.6) ** 2 <= 42:
                    water(px, py)
        solid_deco('tree', [(50, 70), (52, 84), (70, 70), (72, 84), (48, 78),
                            (74, 78), (61, 68), (58, 86), (64, 86)])
        flat_deco('flower', [(56, 70), (66, 70), (56, 82), (66, 82), (61, 84)])

        # ── 농장 (서부, 강 북쪽) — 헛간 + 인터랙티브 밭 + 울타리 + 동물 ──────
        building(6, 40, 8, 7, kind='barn')                     # 헛간
        fence = ([(fx, 40) for fx in range(15, 31)] + [(fx, 53) for fx in range(15, 31)]
                 + [(15, fy) for fy in range(41, 53)] + [(30, fy) for fy in range(41, 53)])
        flat_deco('fence', [(fx, fy) for (fx, fy) in fence if not blocked(fx, fy)])
        self._animal_spots = [(fx, fy) for (fx, fy) in
                              ((18, 44), (24, 46), (20, 50), (27, 43), (17, 48), (22, 51))
                              if not blocked(fx, fy)]

        # ── 목장 (동부, 강 북쪽) — 헛간 + 우리 + 울타리 ────────────────────
        building(115, 40, 8, 7, kind='barn')                   # 목장 헛간(동쪽)
        rfence = ([(fx, 42) for fx in range(99, 114)] + [(fx, 51) for fx in range(99, 114)]
                  + [(99, fy) for fy in range(43, 51)] + [(113, fy) for fy in range(43, 51)])
        # 우리 칸(RANCH_PENS)과 출입구는 울타리에서 제외
        _pens = set(RANCH_PENS)
        flat_deco('fence', [(fx, fy) for (fx, fy) in rfence
                            if not blocked(fx, fy) and (fx, fy) not in _pens
                            and (fx, fy) != (106, 51)])

        # ── 닭농장 (목장 서편) — 닭장 + 울타리 + 닭 무리 ──────────────────
        building(84, 43, 5, 5, kind='barn')                    # 닭장
        cfence = ([(fx, 43) for fx in range(83, 96)] + [(fx, 54) for fx in range(83, 96)]
                  + [(83, fy) for fy in range(44, 54)] + [(95, fy) for fy in range(44, 54)])
        flat_deco('fence', [(fx, fy) for (fx, fy) in cfence
                            if not blocked(fx, fy) and (fx, fy) != (89, 54)])  # 출입구
        self._coop_bounds = (84, 48, 94, 53)   # 닭이 벗어나지 못할 마당 범위
        self._coop_spots = [(fx, fy) for (fx, fy) in
                            ((86, 49), (90, 48), (88, 51), (85, 50),
                             (92, 49), (87, 52), (93, 51), (91, 52))
                            if not blocked(fx, fy)]

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
        bnds = npc.get('bounds')          # (x0,y0,x1,y1) 울타리 안으로 배회 제한
        cands = []
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = npc['x'] + ddx, npc['y'] + ddy
            if not self.dungeon.is_walkable(nx, ny):
                continue
            if abs(nx - hx) + abs(ny - hy) > npc['radius']:
                continue
            if bnds and not (bnds[0] <= nx <= bnds[2] and bnds[1] <= ny <= bnds[3]):
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

    def farm_plot_at(self, px: int, py: int):
        """플레이어가 서 있는 밭칸 인덱스 (없으면 None)."""
        for i, (fx, fy) in enumerate(FARM_PLOTS):
            if (px, py) == (fx, fy):
                return i
        return None

    def pen_at(self, px: int, py: int):
        """플레이어가 서 있는(또는 바로 옆) 목장 우리 인덱스 (없으면 None)."""
        for i, (fx, fy) in enumerate(RANCH_PENS):
            if max(abs(px - fx), abs(py - fy)) == 0:
                return i
        return None

    def water_adjacent(self, px: int, py: int):
        """플레이어 상하좌우에 물 타일이 있으면 (물칸 좌표) 반환 — 낚시터 판정."""
        from map.tile import TileType
        d = self.dungeon
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            wx, wy = px + dx, py + dy
            if 0 <= wy < d.height and 0 <= wx < d.width:
                if d.tiles[wy][wx].tile_type == TileType.WATER:
                    return (wx, wy)
        return None

    # ── 렌더링 ────────────────────────────────────────────────────────
    def draw(self, surf, cam_x: int, cam_y: int, px: int, py: int, font):
        ts = TILE_SIZE
        ticks = pygame.time.get_ticks()
        ox, oy = cam_x * ts, cam_y * ts

        # 집: 지붕(실외) / 실내(플레이어 진입 시) + 문
        self._draw_houses(surf, ox, oy, px, py, ticks)

        # 바닥 장식 (NPC 아래)
        for cx_, cy_ in self._deco['crop']:
            self._draw_crop(surf, cx_ * ts - ox, cy_ * ts - oy, ticks)
        for fx_, fy_ in self._deco['fence']:
            self._draw_fence(surf, fx_ * ts - ox, fy_ * ts - oy)
        self._draw_farm_plots(surf, ox, oy, ticks)      # 인터랙티브 밭
        self._draw_ranch(surf, ox, oy, ticks)           # 목장 우리 + 가축
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
            if npc.get('animal'):                        # 농장 동물 — 이름표 없음
                self._draw_animal(surf, sx, sy + walk, npc['animal'],
                                  npc.get('facing', 1), ticks)
                continue
            if npc['id'] == 'home_board':                # 내 집 커스터마이즈 보드
                self._draw_home_board(surf, sx, sy + walk, ticks)
            elif npc['id'] == 'altar':                   # 고대 제단 (희귀식물 교환)
                self._draw_altar(surf, sx, sy + walk, ticks)
            elif npc['id'] == 'angler':                  # 낚시 노인 (물고기 교환)
                self._draw_angler(surf, sx, sy + walk, npc.get('facing', 1), ticks)
            elif npc['id'] == 'party_board':             # 용병 길드 게시판
                self._draw_party_board(surf, sx, sy + walk, ticks)
            elif npc['id'] == 'ranking_board':           # 명예의 전당(랭킹)
                self._draw_ranking_board(surf, sx, sy + walk, ticks)
            elif npc['id'] == 'home_chest':              # 내 집 보관함
                mc_object(surf, sx, sy + walk, (150, 110, 60), ticks, kind='chest')
            elif npc.get('facing', 1) < 0:               # 좌향 → 좌우 반전
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

        self._draw_farm_prompt(surf, ox, oy, px, py, font)   # 밭칸 [E] 안내
        self._draw_fishing_prompt(surf, ox, oy, px, py, font)  # 강둑 [E] 낚시 안내
        self._draw_ranch_prompt(surf, ox, oy, px, py, font)    # 우리 [E] 목장 안내

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

    def _farm_action_key(self, idx):
        """밭칸 상태에 맞는 안내 문구 키 (심기/물주기/수확/성장중)."""
        st = self.farm[idx] if idx < len(self.farm) else {}
        if not st.get('crop'):
            return 'farm_hint_plant'
        if st.get('stage', 0) >= FARM_GROW_MAX:
            return 'farm_hint_harvest'
        return 'farm_hint_grown' if st.get('watered') else 'farm_hint_water'

    def _draw_farm_prompt(self, surf, ox, oy, px, py, font):
        """플레이어가 선 밭칸 위에 [E] 액션 안내 표시."""
        idx = self.farm_plot_at(px, py)
        if idx is None:
            return
        fx, fy = FARM_PLOTS[idx]
        sx = fx * TILE_SIZE - ox + TILE_SIZE // 2
        sy = fy * TILE_SIZE - oy
        txt = font.render(t('farm_hint_open'), True, (255, 235, 140))
        bg = pygame.Surface((txt.get_width() + 8, txt.get_height() + 3), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 175))
        surf.blit(bg, (sx - txt.get_width() // 2 - 4, sy - 19))
        surf.blit(txt, (sx - txt.get_width() // 2, sy - 17))

    def _draw_fishing_prompt(self, surf, ox, oy, px, py, font):
        """강둑에 서면 [E] 낚시 안내 (인접 NPC/밭칸 없을 때만)."""
        if self.npc_near(px, py) or self.farm_plot_at(px, py) is not None:
            return
        if self.water_adjacent(px, py) is None:
            return
        sx = px * TILE_SIZE - ox + TILE_SIZE // 2
        sy = py * TILE_SIZE - oy
        txt = font.render(t('fish_hint'), True, (150, 220, 255))
        bg = pygame.Surface((txt.get_width() + 8, txt.get_height() + 3), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 175))
        surf.blit(bg, (sx - txt.get_width() // 2 - 4, sy - 19))
        surf.blit(txt, (sx - txt.get_width() // 2, sy - 17))

    def _draw_ranch_prompt(self, surf, ox, oy, px, py, font):
        """우리 위에 서면 [E] 목장 안내 (인접 NPC 없을 때)."""
        if self.npc_near(px, py):
            return
        idx = self.pen_at(px, py)
        if idx is None:
            return
        fx, fy = RANCH_PENS[idx]
        sx = fx * TILE_SIZE - ox + TILE_SIZE // 2
        sy = fy * TILE_SIZE - oy
        txt = font.render(t('ranch_hint_open'), True, (255, 224, 150))
        bg = pygame.Surface((txt.get_width() + 8, txt.get_height() + 3), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 175))
        surf.blit(bg, (sx - txt.get_width() // 2 - 4, sy - 19))
        surf.blit(txt, (sx - txt.get_width() // 2, sy - 17))

    # ── 목장: 우리 + 가축 + 생산물 표시 ──────────────────────────────
    def _draw_ranch(self, surf, ox, oy, ticks):
        ts = TILE_SIZE
        for i, (fx, fy) in enumerate(RANCH_PENS):
            x, y = fx * ts - ox, fy * ts - oy
            st = self.ranch[i] if i < len(self.ranch) else {}
            # 여물통
            pygame.draw.rect(surf, (108, 78, 46), (x + 5, y + ts - 8, ts - 10, 5))
            pygame.draw.rect(surf, (148, 110, 64), (x + 5, y + ts - 8, ts - 10, 2))
            animal = st.get('animal')
            if not animal:
                continue
            # 우리 안을 어슬렁 — 좌우로 서성이며 방향 전환
            phase = ticks * 0.0012 + i * 2.1
            wx = int(14 * math.sin(phase))
            wy = int(4 * math.sin(phase * 1.7 + i * 0.7))
            facing = 1 if math.cos(phase) >= 0 else -1
            ax, ay = x + wx, y - 2 + wy
            self._draw_animal(surf, ax, ay, animal, facing, ticks + i * 90)
            if st.get('stage', 0) >= RANCH_FEED_MAX:      # 생산물 준비 반짝
                by = ay - 4 + int(2 * math.sin(ticks * 0.006 + i))
                pygame.draw.circle(surf, (255, 236, 130), (ax + ts - 7, by), 4)
                pygame.draw.circle(surf, (255, 255, 224), (ax + ts - 8, by - 1), 1)

    # ── 농장: 인터랙티브 밭 / 울타리 / 동물 ──────────────────────────
    def _draw_farm_plots(self, surf, ox, oy, ticks):
        ts = TILE_SIZE
        for i, (fx, fy) in enumerate(FARM_PLOTS):
            x, y = fx * ts - ox, fy * ts - oy
            st = self.farm[i] if i < len(self.farm) else {'crop': None, 'stage': 0}
            watered = st.get('watered')
            soil = (58, 42, 28) if watered else (92, 66, 42)         # 젖은 흙은 어둡게
            pygame.draw.rect(surf, soil, (x + 3, y + 10, ts - 6, ts - 13))   # 흙칸
            pygame.draw.rect(surf, (max(0, soil[0] - 16), max(0, soil[1] - 14),
                                    max(0, soil[2] - 10)), (x + 3, y + 10, ts - 6, 2))
            pygame.draw.line(surf, (72, 48, 30), (x + 3, y + ts - 8), (x + ts - 3, y + ts - 8), 1)
            if watered:                                             # 물방울
                for dx in (8, 17, 25):
                    pygame.draw.circle(surf, (96, 156, 204), (x + dx, y + ts - 5), 1)
            crop = st.get('crop')
            if not crop:
                continue
            stage = st.get('stage', 0)
            ready = stage >= FARM_GROW_MAX
            col = next((c for (cid, c, v) in CROPS if cid == crop), (120, 200, 90))
            sway = int(math.sin(ticks * 0.003 + x) * 1)
            gh = 3 + min(stage, FARM_GROW_MAX) * 6                  # 성장 높이
            for ax in (9, 16, 23):
                gx = x + ax + sway
                pygame.draw.line(surf, (60, 130, 55), (gx, y + ts - 6), (gx, y + ts - 6 - gh), 2)
                pygame.draw.circle(surf, (86, 170, 76), (gx, y + ts - 7 - gh), 2 + (1 if ready else 0))
                if ready:
                    pygame.draw.circle(surf, col, (gx, y + ts - 8 - gh), 3)     # 열매
            if ready and (ticks // 300) % 2 == 0:                  # 수확 준비 반짝임
                pygame.draw.circle(surf, (255, 245, 170), (x + ts // 2, y + 3), 2)

    @staticmethod
    def _draw_crop(s, x, y, tk):
        ts = TILE_SIZE
        pygame.draw.rect(s, (74, 52, 34), (x + 2, y + ts - 13, ts - 4, 11))   # 흙 이랑
        pygame.draw.line(s, (56, 38, 24), (x + 2, y + ts - 8), (x + ts - 2, y + ts - 8), 1)
        sway = int(math.sin(tk * 0.003 + x) * 1)
        for i, ax in enumerate((7, 16, 24)):
            gx = x + ax + sway
            pygame.draw.line(s, (60, 130, 55), (gx, y + ts - 4), (gx, y + ts - 13), 2)
            pygame.draw.circle(s, (86, 170, 76), (gx, y + ts - 14), 3)
            if (x + i) % 3 == 0:
                pygame.draw.circle(s, (230, 90, 70), (gx, y + ts - 14), 2)     # 토마토
            elif (x + i) % 3 == 1:
                pygame.draw.circle(s, (240, 200, 70), (gx, y + ts - 15), 2)    # 옥수수/호박

    @staticmethod
    def _draw_fence(s, x, y):
        ts = TILE_SIZE
        cx = x + ts // 2
        pygame.draw.rect(s, (120, 88, 54), (cx - 2, y + 8, 4, ts - 12))       # 기둥
        pygame.draw.rect(s, (150, 114, 70), (x + 2, y + 12, ts - 4, 3))       # 가로대
        pygame.draw.rect(s, (150, 114, 70), (x + 2, y + 20, ts - 4, 3))

    @staticmethod
    def _draw_animal(s, x, y, kind, facing, tk):
        ts = TILE_SIZE
        bob = int(math.sin(tk * 0.006 + x) * 1)
        cx, cy = x + ts // 2, y + ts // 2 + bob
        if kind == 'chicken':
            pygame.draw.ellipse(s, (246, 246, 246), (cx - 5, cy, 10, 9))
            pygame.draw.circle(s, (246, 246, 246), (cx + 5, cy - 2), 4)
            pygame.draw.polygon(s, (240, 170, 40), [(cx + 9, cy - 3), (cx + 13, cy - 2), (cx + 9, cy)])
            pygame.draw.rect(s, (220, 60, 50), (cx + 4, cy - 7, 3, 3))
            pygame.draw.line(s, (230, 160, 40), (cx - 2, cy + 9), (cx - 2, cy + 13), 1)
            pygame.draw.line(s, (230, 160, 40), (cx + 2, cy + 9), (cx + 2, cy + 13), 1)
        elif kind == 'cow':
            pygame.draw.ellipse(s, (246, 246, 246), (cx - 9, cy - 3, 20, 13))
            pygame.draw.rect(s, (58, 48, 44), (cx - 5, cy, 5, 5))
            pygame.draw.rect(s, (58, 48, 44), (cx + 3, cy + 3, 5, 4))
            pygame.draw.circle(s, (246, 246, 246), (cx + 11, cy - 2), 4)
            pygame.draw.circle(s, (245, 190, 190), (cx + 13, cy), 2)
            for lx in (cx - 6, cx - 1, cx + 5, cx + 9):
                pygame.draw.line(s, (120, 110, 100), (lx, cy + 9), (lx, cy + 14), 2)
        elif kind == 'sheep':
            pygame.draw.circle(s, (242, 238, 230), (cx, cy + 2), 8)
            pygame.draw.circle(s, (242, 238, 230), (cx - 5, cy), 5)
            pygame.draw.circle(s, (242, 238, 230), (cx + 5, cy), 5)
            pygame.draw.circle(s, (70, 62, 60), (cx + 7, cy - 1), 3)
            for lx in (cx - 4, cx + 4):
                pygame.draw.line(s, (70, 62, 60), (lx, cy + 9), (lx, cy + 14), 2)
        else:  # pig
            pygame.draw.ellipse(s, (240, 160, 170), (cx - 8, cy - 2, 18, 12))
            pygame.draw.circle(s, (240, 160, 170), (cx + 9, cy + 2), 4)
            pygame.draw.circle(s, (220, 120, 135), (cx + 12, cy + 3), 2)
            pygame.draw.line(s, (230, 140, 150), (cx - 8, cy + 4), (cx - 11, cy + 2), 2)
            for lx in (cx - 5, cx, cx + 6):
                pygame.draw.line(s, (210, 130, 140), (lx, cy + 8), (lx, cy + 13), 2)

    @staticmethod
    def _draw_ranking_board(surf, x, y, tk):
        """명예의 전당 — 대리석 비석 + 금 트로피/별 + 순위 표식."""
        import math as _m
        ts = TILE_SIZE
        cx = x + ts // 2
        base = y + ts - 2
        # 대리석 받침 + 기둥
        pygame.draw.rect(surf, (206, 210, 224), (cx - 16, base - 6, 32, 6))
        pygame.draw.rect(surf, (170, 176, 194), (cx - 13, y + 8, 26, base - 14))
        pygame.draw.rect(surf, (120, 126, 146), (cx - 13, y + 8, 26, base - 14), 1)
        # 순위 막대 3개 (1·2·3위)
        for i, (h, c) in enumerate(((16, (255, 215, 90)), (11, (208, 214, 224)), (7, (205, 150, 96)))):
            bxr = cx - 9 + i * 8
            pygame.draw.rect(surf, c, (bxr, base - 8 - h, 6, h))
            pygame.draw.rect(surf, (60, 60, 70), (bxr, base - 8 - h, 6, h), 1)
        # 상단 금별 (반짝임)
        gy = y + 4
        pts = []
        for i in range(10):
            a = _m.radians(-90 + i * 36)
            r = 8 if i % 2 == 0 else 3.4
            pts.append((cx + _m.cos(a) * r, gy + _m.sin(a) * r))
        pygame.draw.polygon(surf, (255, 224, 120), pts)
        pygame.draw.polygon(surf, (150, 110, 30), pts, 1)
        if (tk // 300) % 2 == 0:
            pygame.draw.circle(surf, (255, 250, 210), (cx + 6, gy - 4), 1)

    @staticmethod
    def _draw_party_board(surf, x, y, tk):
        """용병 길드 게시판 — 나무 기둥 게시판 + 의뢰지 + 검 상징."""
        ts = TILE_SIZE
        cx = x + ts // 2
        base = y + ts - 2
        # 두 다리 기둥
        pygame.draw.rect(surf, (96, 66, 40), (cx - 10, y + 10, 3, ts - 12))
        pygame.draw.rect(surf, (96, 66, 40), (cx + 7, y + 10, 3, ts - 12))
        # 게시판 널판
        pygame.draw.rect(surf, (120, 84, 50), (cx - 12, y + 4, 24, 16))
        pygame.draw.rect(surf, (150, 108, 66), (cx - 12, y + 4, 24, 16), 1)
        # 의뢰지 두 장
        pygame.draw.rect(surf, (232, 226, 208), (cx - 9, y + 7, 7, 9))
        pygame.draw.rect(surf, (232, 226, 208), (cx + 1, y + 6, 7, 10))
        pygame.draw.line(surf, (150, 140, 120), (cx - 8, y + 10), (cx - 3, y + 10), 1)
        pygame.draw.line(surf, (150, 140, 120), (cx + 2, y + 9), (cx + 7, y + 9), 1)
        # 교차 검 상징(길드 표식) — 상단
        pygame.draw.line(surf, (200, 205, 220), (cx - 4, y + 2), (cx + 4, y + 8), 2)
        pygame.draw.line(surf, (200, 205, 220), (cx + 4, y + 2), (cx - 4, y + 8), 2)
        if (tk // 300) % 2 == 0:
            pygame.draw.circle(surf, (255, 226, 120), (cx + 6, y + 4), 1)
        _ = base

    @staticmethod
    def _draw_home_board(surf, x, y, tk):
        """내 집 인테리어 관리 이젤."""
        ts = TILE_SIZE
        cx = x + ts // 2
        pygame.draw.line(surf, (110, 80, 48), (cx - 6, y + ts - 2), (cx, y + 12), 2)
        pygame.draw.line(surf, (110, 80, 48), (cx + 6, y + ts - 2), (cx, y + 12), 2)
        pygame.draw.rect(surf, (86, 60, 36), (cx - 9, y + 6, 18, 16))
        pygame.draw.rect(surf, (224, 218, 202), (cx - 7, y + 8, 14, 12))
        pygame.draw.polygon(surf, (150, 90, 80), [(cx - 5, y + 15), (cx, y + 10), (cx + 5, y + 15)])
        pygame.draw.rect(surf, (150, 90, 80), (cx - 4, y + 15, 8, 4), 1)
        if (tk // 350) % 2 == 0:
            pygame.draw.circle(surf, (255, 235, 150), (cx + 7, y + 7), 1)

    @staticmethod
    def _draw_altar(surf, x, y, tk):
        """고대 제단 — 돌 받침 + 맥동하는 보랏빛 수정."""
        import math as _m
        ts = TILE_SIZE
        cx = x + ts // 2
        base = y + ts - 3
        # 돌 받침 (2단)
        pygame.draw.rect(surf, (78, 72, 92), (cx - 9, base - 6, 18, 6))
        pygame.draw.rect(surf, (58, 54, 72), (cx - 7, base - 12, 14, 7))
        pygame.draw.rect(surf, (96, 88, 116), (cx - 9, base - 6, 18, 1))
        # 룬 광채
        glow = 0.5 + 0.5 * _m.sin(tk * 0.006)
        halo = int(60 + 90 * glow)
        aura = pygame.Surface((ts, ts), pygame.SRCALPHA)
        pygame.draw.circle(aura, (150, 90, 210, halo), (ts // 2, ts // 2), 9)
        surf.blit(aura, (x, base - 20 - ts // 2))
        # 부유 수정
        cyf = base - 20 - int(2 * _m.sin(tk * 0.005))
        pygame.draw.polygon(surf, (198, 150, 236),
                            [(cx, cyf - 8), (cx - 5, cyf), (cx, cyf + 7), (cx + 5, cyf)])
        pygame.draw.polygon(surf, (238, 214, 252),
                            [(cx, cyf - 8), (cx - 2, cyf - 1), (cx, cyf + 2), (cx + 2, cyf - 1)])
        if (tk // 240) % 2 == 0:
            pygame.draw.circle(surf, (255, 246, 200), (cx + 4, cyf - 4), 1)

    @staticmethod
    def _draw_angler(surf, x, y, facing, tk):
        """낚시 노인 — 밀짚모자 + 낚싯대를 강 쪽으로 드리운 노인."""
        import math as _m
        ts = TILE_SIZE
        cx = x + ts // 2
        # 몸통(외투) + 머리
        pygame.draw.rect(surf, (86, 104, 96), (cx - 5, y + 13, 10, 12))
        pygame.draw.circle(surf, (226, 196, 166), (cx, y + 10), 5)
        pygame.draw.rect(surf, (206, 200, 180), (cx - 3, y + 12, 6, 3))     # 흰 수염
        # 밀짚모자
        pygame.draw.ellipse(surf, (204, 176, 108), (cx - 8, y + 5, 16, 5))
        pygame.draw.ellipse(surf, (224, 198, 128), (cx - 4, y + 2, 8, 5))
        # 낚싯대(앞으로) + 흔들리는 낚싯줄
        rod_x = cx + 8 * facing
        pygame.draw.line(surf, (140, 96, 54), (cx + 2 * facing, y + 15),
                         (rod_x, y + 4), 2)
        bob = y + 20 + int(2 * _m.sin(tk * 0.005))
        pygame.draw.line(surf, (210, 210, 220), (rod_x, y + 4), (rod_x, bob), 1)
        pygame.draw.circle(surf, (228, 96, 84), (rod_x, bob), 2)             # 찌

    def _draw_trophies(self, surf, ix, iy, iw):
        """내 집 실내 상단 선반에 보스 전리품(처치한 보스층 수)을 진열."""
        count = self.trophies if isinstance(self.trophies, int) else \
            sum(1 for v in self.trophies.values() if v)
        if count <= 0:
            return
        from map.theme import get_theme_by_index, theme_index
        sy = iy + 2
        pygame.draw.rect(surf, (110, 80, 48), (ix + 2, sy + 6, iw - 4, 3))     # 선반
        pygame.draw.rect(surf, (140, 104, 64), (ix + 2, sy + 6, iw - 4, 1))
        cap = max(1, (iw - 8) // 9)                 # 선반에 들어갈 최대 개수
        shown = min(count, cap)
        step = max(9, min(15, (iw - 8) // max(1, shown)))
        for i in range(shown):
            tx = ix + 5 + i * step
            th = theme_index((i + 1) * 5)           # i번째 보스층(5,10,...)의 테마색
            col = get_theme_by_index(th).get('stairs_lit', (238, 208, 92))
            pygame.draw.rect(surf, (206, 176, 70), (tx, sy + 4, 6, 2))         # 받침
            pygame.draw.polygon(surf, (238, 208, 92),
                                [(tx - 1, sy - 1), (tx + 7, sy - 1), (tx + 3, sy + 4)])  # 컵
            pygame.draw.circle(surf, col, (tx + 3, sy), 2)                     # 테마 보석

    # ── 집: 지붕 / 실내 / 문 ──────────────────────────────────────────
    def _draw_houses(self, surf, ox, oy, px, py, ticks):
        ts = TILE_SIZE
        for hs in self._houses:
            rects = hs['rects']
            inside = (px, py) in hs['inside']    # 실제 실내 타일 판정(L자 이음새 포함)
            if inside:
                for (rx, ry, rw, rh) in rects:      # 실내 바닥(각 날개)
                    self._draw_interior_floor(surf, rx * ts - ox, ry * ts - oy,
                                              rw * ts, rh * ts)
                rx, ry, rw, rh = max(rects, key=lambda r: r[2] * r[3])   # 큰 날개에 가구
                self._draw_furniture(surf, rx * ts - ox + ts, ry * ts - oy + ts,
                                     (rw - 2) * ts, (rh - 2) * ts, hs, ticks)
            else:
                for (rx, ry, rw, rh) in rects:      # 날개마다 지붕
                    self._draw_roof(surf, rx * ts - ox, ry * ts - oy,
                                    rw * ts, rh * ts, hs)
            dx, dy = hs['door']
            self._draw_house_door(surf, dx * ts - ox, dy * ts - oy, inside)
            if hs.get('sign') and not inside:           # 상점/내집 간판
                self._draw_sign(surf, dx * ts - ox, dy * ts - oy, hs['sign'], ticks)

    def _draw_sign(self, surf, dx, dy, icon, ticks):
        """문 옆에 걸린 나무 간판 + 아이콘 (여관/대장간/상점/창고/내집)."""
        ts = TILE_SIZE
        bx, by = dx + ts + 2, dy - 6           # 문 오른쪽 위
        pygame.draw.rect(surf, (60, 42, 26), (bx + 11, by - 8, 3, 10))   # 걸대
        board = pygame.Rect(bx, by, 26, 16)
        pygame.draw.rect(surf, (120, 84, 48), board, border_radius=3)
        pygame.draw.rect(surf, (78, 54, 32), board, 2, border_radius=3)
        cx, cy = bx + 13, by + 8
        if icon == 'inn':                       # 맥주잔
            pygame.draw.rect(surf, (240, 210, 120), (cx - 4, cy - 4, 7, 9))
            pygame.draw.rect(surf, (255, 245, 220), (cx - 4, cy - 5, 7, 2))
            pygame.draw.line(surf, (200, 170, 90), (cx + 3, cy - 2), (cx + 6, cy + 1), 2)
        elif icon == 'smith':                   # 망치
            pygame.draw.rect(surf, (150, 150, 160), (cx - 2, cy - 5, 8, 4))
            pygame.draw.rect(surf, (120, 84, 48), (cx + 1, cy - 5, 2, 10))
        elif icon == 'merchant':                # 코인
            pygame.draw.circle(surf, (240, 200, 70), (cx, cy), 5)
            pygame.draw.circle(surf, (210, 165, 45), (cx, cy), 5, 1)
        elif icon == 'chest':                   # 상자
            pygame.draw.rect(surf, (170, 120, 66), (cx - 5, cy - 3, 11, 8))
            pygame.draw.rect(surf, (120, 82, 44), (cx - 5, cy - 1, 11, 2))
        elif icon == 'home':                    # 하트(내 집)
            hb = 0.7 + 0.3 * math.sin(ticks * 0.004)
            hc = (int(235 * hb), int(90 * hb), int(110 * hb))
            pygame.draw.circle(surf, hc, (cx - 2, cy - 1), 3)
            pygame.draw.circle(surf, hc, (cx + 2, cy - 1), 3)
            pygame.draw.polygon(surf, hc, [(cx - 5, cy), (cx + 5, cy), (cx, cy + 5)])

    _ROOF_PALETTES = [((176, 72, 56), (140, 50, 38), (206, 100, 82)),   # 붉은 기와
                      ((84, 96, 140), (58, 68, 108), (118, 132, 176)),  # 청기와
                      ((120, 100, 66), (86, 70, 44), (156, 132, 92))]   # 갈색 초가

    @classmethod
    def _draw_roof(cls, surf, sx, sy, pw, ph, hs):
        ts = TILE_SIZE
        roof, roof_d, roof_hi = cls._ROOF_PALETTES[hs['seed'] % len(cls._ROOF_PALETTES)]
        roof_h = ph - ts                   # 바닥 한 줄은 벽 파사드/문
        ex = 5                              # 처마 돌출
        top = sy - 6
        cx = sx + pw // 2
        # 지붕 본체
        pygame.draw.rect(surf, roof, (sx - ex, top + 6, pw + 2 * ex, (sy + roof_h) - (top + 6)))
        # 삼각 박공(gable) — 위로 솟은 삼각 지붕
        pygame.draw.polygon(surf, roof_hi, [(cx, top - 8), (sx - ex, top + 8), (sx + pw + ex, top + 8)])
        pygame.draw.polygon(surf, roof, [(cx, top - 4), (sx - ex + 5, top + 8), (sx + pw + ex - 5, top + 8)])
        # 용마루 + 기와줄
        pygame.draw.line(surf, roof_hi, (sx - ex, top + 8), (sx + pw + ex, top + 8), 2)
        for ry in range(top + 14, sy + roof_h, 7):
            pygame.draw.line(surf, roof_d, (sx - ex, ry), (sx + pw + ex, ry), 1)
        # 벽 파사드 (앞면 한 줄) + 큼직한 창문(문 양옆) + 박공 다락창
        pygame.draw.rect(surf, (126, 96, 64), (sx, sy + roof_h, pw, ts))
        pygame.draw.rect(surf, (152, 118, 82), (sx, sy + roof_h, pw, 3))
        ww, wh = 16, 20                     # 시원한 큰 창
        wy = sy + roof_h + (ts - wh) // 2
        for wx in (sx + pw // 4 - ww // 2, sx + 3 * pw // 4 - ww // 2):
            pygame.draw.rect(surf, (78, 54, 32), (wx - 2, wy - 2, ww + 4, wh + 4))  # 창틀
            pygame.draw.rect(surf, (188, 210, 235), (wx, wy, ww, wh))               # 유리
            pygame.draw.rect(surf, (150, 178, 210), (wx, wy + wh // 2, ww, wh // 2))  # 아래 그늘
            pygame.draw.line(surf, (78, 54, 32), (wx + ww // 2, wy), (wx + ww // 2, wy + wh), 2)  # 세로 창살
            pygame.draw.line(surf, (78, 54, 32), (wx, wy + wh // 2), (wx + ww, wy + wh // 2), 2)  # 가로 창살
            pygame.draw.rect(surf, (240, 248, 255), (wx + 1, wy + 1, ww // 2 - 2, wh // 2 - 2))    # 하이라이트
            for sh, sdx in (((92, 62, 40), -ww // 2 - 4), ((92, 62, 40), ww + 2)):  # 덧문
                pygame.draw.rect(surf, sh, (wx + sdx, wy - 2, 4, wh + 4))
        # 박공(다락)에 동그란 창
        gy = top - 1
        pygame.draw.circle(surf, (78, 54, 32), (cx, gy), 5)
        pygame.draw.circle(surf, (188, 210, 235), (cx, gy), 3)

    @staticmethod
    def _draw_interior_floor(surf, sx, sy, pw, ph):
        ts = TILE_SIZE
        ix, iy = sx + ts, sy + ts
        iw, ih = pw - 2 * ts, ph - 2 * ts
        if iw <= 0 or ih <= 0:
            return
        pygame.draw.rect(surf, (104, 78, 52), (ix, iy, iw, ih))          # 나무 바닥
        for fy in range(iy, iy + ih, 6):
            pygame.draw.line(surf, (86, 62, 40), (ix, fy), (ix + iw, fy), 1)

    def _draw_furniture(self, surf, ix, iy, iw, ih, hs, ticks):
        """용도(kind)·씨앗별로 다른 가구 배치 — 침대/탁자/화로/책장/모루/궤짝 등."""
        if iw < 16 or ih < 10:
            pygame.draw.rect(surf, (150, 70, 66),
                             (ix + iw // 2 - 7, iy + ih // 2 - 5, 14, 10), border_radius=3)
            return
        x2, y2 = ix + iw, iy + ih
        cx, cy = ix + iw // 2, iy + ih // 2

        def rug(w, h, col):
            pygame.draw.rect(surf, col, (cx - w // 2, cy - h // 2, w, h), border_radius=3)
            pygame.draw.rect(surf, tuple(min(255, c + 34) for c in col),
                             (cx - w // 2, cy - h // 2, w, h), 1, border_radius=3)

        def bed(x, y):
            pygame.draw.rect(surf, (120, 64, 60), (x, y, 22, 14))
            pygame.draw.rect(surf, (182, 92, 92), (x + 2, y + 2, 18, 10))
            pygame.draw.rect(surf, (240, 240, 248), (x + 2, y + 2, 6, 10))

        def table(x, y, w=14):
            pygame.draw.rect(surf, (120, 88, 52), (x, y, w, 9))
            pygame.draw.rect(surf, (150, 112, 70), (x, y, w, 2))

        def chair(x, y):
            pygame.draw.rect(surf, (104, 74, 44), (x, y, 6, 6))
            pygame.draw.rect(surf, (128, 94, 58), (x, y - 3, 6, 3))

        def hearth(x, y):
            pygame.draw.rect(surf, (60, 52, 50), (x, y, 18, 12))
            pygame.draw.rect(surf, (24, 20, 20), (x + 3, y + 3, 12, 9))
            f = (ticks // 160) % 2
            pygame.draw.polygon(surf, (255, 150, 40), [(x + 9, y + 4), (x + 6 + f, y + 11), (x + 12 - f, y + 11)])
            pygame.draw.polygon(surf, (255, 224, 130), [(x + 9, y + 7), (x + 7, y + 11), (x + 11, y + 11)])

        def shelf(x, y, h=16):
            pygame.draw.rect(surf, (96, 68, 42), (x, y, 12, h))
            sp = [(210, 80, 60), (80, 140, 210), (90, 180, 110), (220, 200, 90)]
            for i in range(0, h - 4, 5):
                for j in range(3):
                    pygame.draw.rect(surf, sp[(i + j) % 4], (x + 2 + j * 3, y + 2 + i, 2, 4))

        def crate(x, y):
            pygame.draw.rect(surf, (140, 100, 58), (x, y, 12, 12))
            pygame.draw.rect(surf, (100, 72, 40), (x, y, 12, 12), 1)
            pygame.draw.line(surf, (100, 72, 40), (x, y), (x + 12, y + 12), 1)
            pygame.draw.line(surf, (100, 72, 40), (x + 12, y), (x, y + 12), 1)

        def barrel(x, y):
            pygame.draw.rect(surf, (120, 82, 44), (x, y, 11, 14), border_radius=3)
            pygame.draw.rect(surf, (80, 54, 28), (x, y + 4, 11, 2))
            pygame.draw.rect(surf, (80, 54, 28), (x, y + 9, 11, 2))

        def anvil(x, y):
            pygame.draw.rect(surf, (70, 72, 82), (x, y + 6, 18, 6))
            pygame.draw.rect(surf, (92, 94, 106), (x + 2, y + 2, 12, 5))
            pygame.draw.polygon(surf, (92, 94, 106), [(x + 14, y + 3), (x + 21, y + 5), (x + 14, y + 7)])

        def forge(x, y):
            pygame.draw.rect(surf, (48, 42, 40), (x, y, 16, 14))
            g = (ticks // 140) % 2
            pygame.draw.rect(surf, (255, 120, 30) if g else (255, 90, 20), (x + 3, y + 4, 10, 8))
            pygame.draw.rect(surf, (255, 224, 130), (x + 6, y + 6, 4, 4))

        def counter(x, y, w=26):
            pygame.draw.rect(surf, (110, 80, 48), (x, y, w, 8))
            pygame.draw.rect(surf, (140, 104, 64), (x, y, w, 2))

        def plant(x, y):
            pygame.draw.rect(surf, (120, 80, 50), (x + 2, y + 8, 8, 6))
            pygame.draw.circle(surf, (70, 150, 80), (x + 6, y + 5), 5)
            pygame.draw.circle(surf, (95, 180, 100), (x + 4, y + 3), 3)

        def wardrobe(x, y):
            pygame.draw.rect(surf, (108, 78, 48), (x, y, 12, 18))
            pygame.draw.line(surf, (72, 52, 32), (x + 6, y + 1), (x + 6, y + 17), 1)

        kind = hs['kind']
        if kind == 'smith':
            rug(min(iw - 8, 30), min(ih - 8, 18), (92, 84, 74))
            anvil(ix + 4, cy - 4); forge(x2 - 20, iy + 3)
            barrel(ix + 4, y2 - 16); barrel(x2 - 14, y2 - 16)
        elif kind == 'merchant':
            # 마트처럼 진열대 여러 개 + 농산물 바구니 + 계산대
            counter(ix + 4, y2 - 12, min(iw - 8, 34))
            for shx in range(ix + 4, x2 - 12, 13):
                shelf(shx, iy + 3, min(ih - 12, 18))
            for bi, bx in enumerate(range(ix + 6, x2 - 12, 14)):
                pygame.draw.rect(surf, (150, 110, 66), (bx, cy - 1, 11, 7))    # 바구니
                for k in range(3):
                    col = ((230, 80, 60), (240, 200, 70), (90, 180, 90), (210, 130, 220))[(bi + k) % 4]
                    pygame.draw.circle(surf, col, (bx + 2 + k * 3, cy + 1), 2)
        elif kind == 'inn':
            bed(ix + 4, iy + 3); bed(x2 - 26, iy + 3)
            table(cx - 7, y2 - 14); chair(cx - 13, y2 - 13); chair(cx + 9, y2 - 13)
            hearth(x2 - 22, cy - 6)
        elif kind == 'chest':
            # 창고처럼 궤짝 격자 적재 + 통 + 자루
            for row in range(2):
                for col in range(5):
                    bx, by = ix + 3 + col * 13, iy + 3 + row * 13
                    if bx + 12 < x2 and by + 12 < y2:
                        crate(bx, by)
            barrel(x2 - 13, y2 - 16); barrel(x2 - 26, y2 - 16)
            pygame.draw.ellipse(surf, (190, 174, 132), (ix + 4, y2 - 14, 12, 12))  # 자루
        elif kind == 'barn':
            # 헛간 — 건초더미 + 여물통
            for (bx, by) in ((ix + 4, iy + 3), (ix + 4, cy + 3), (x2 - 17, iy + 3)):
                pygame.draw.rect(surf, (214, 184, 92), (bx, by, 14, 11), border_radius=2)
                for hy in range(by + 2, by + 10, 3):
                    pygame.draw.line(surf, (182, 152, 68), (bx, hy), (bx + 14, hy), 1)
            pygame.draw.rect(surf, (110, 80, 48), (cx - 8, y2 - 12, 20, 6))       # 여물통
            pygame.draw.rect(surf, (150, 112, 70), (cx - 8, y2 - 12, 20, 2))
        elif kind == 'home':
            # 내 집 — home_style로 인테리어 커스터마이즈 (5종)
            st = ('cozy', 'noble', 'rustic', 'study', 'garden')[self.home_style % 5]
            if st == 'cozy':
                rug(min(iw - 10, 26), min(ih - 10, 16), (172, 92, 82))
                bed(ix + 4, iy + 3); hearth(x2 - 22, iy + 3)
                plant(ix + 4, y2 - 16); table(cx - 6, y2 - 14)
            elif st == 'noble':
                rug(min(iw - 8, 30), min(ih - 8, 18), (120, 60, 140))
                bed(ix + 4, iy + 3); wardrobe(x2 - 14, iy + 3)
                shelf(cx - 6, iy + 3, min(ih - 10, 16)); plant(x2 - 12, y2 - 16)
            elif st == 'rustic':
                rug(min(iw - 10, 24), min(ih - 10, 14), (120, 96, 62))
                table(cx - 7, cy - 4); chair(cx - 13, cy - 4); chair(cx + 9, cy - 4)
                barrel(ix + 4, iy + 3); hearth(x2 - 22, iy + 3)
            elif st == 'study':
                rug(min(iw - 10, 24), min(ih - 10, 14), (70, 100, 140))
                shelf(ix + 4, iy + 3, min(ih - 8, 16)); shelf(ix + 18, iy + 3, min(ih - 8, 16))
                table(x2 - 20, y2 - 14); plant(ix + 4, y2 - 16)
            else:  # garden
                rug(min(iw - 10, 24), min(ih - 10, 14), (80, 140, 90))
                for (bx, by) in ((ix + 4, iy + 3), (x2 - 12, iy + 3), (ix + 4, y2 - 16),
                                 (x2 - 12, y2 - 16), (cx - 4, cy - 2)):
                    plant(bx, by)
                table(cx - 6, y2 - 14)
            self._draw_trophies(surf, ix, iy, iw)     # 보스 전리품 진열
        else:
            theme = ('bedroom', 'kitchen', 'living', 'study')[hs['seed'] % 4]
            rug(min(iw - 10, 26), min(ih - 10, 16),
                ((150, 70, 66), (90, 120, 160), (120, 90, 150), (80, 130, 90))[hs['seed'] % 4])
            if theme == 'bedroom':
                bed(ix + 4, iy + 3); wardrobe(x2 - 14, iy + 3); plant(ix + 4, y2 - 16)
            elif theme == 'kitchen':
                table(cx - 7, cy - 4); chair(cx - 13, cy - 4); chair(cx + 9, cy - 4)
                hearth(x2 - 22, iy + 3); barrel(ix + 4, y2 - 16)
            elif theme == 'living':
                hearth(cx - 9, iy + 3); table(cx - 6, y2 - 14)
                plant(ix + 4, iy + 3); plant(x2 - 12, y2 - 16)
            else:  # study
                shelf(ix + 4, iy + 3, min(ih - 8, 16)); shelf(ix + 18, iy + 3, min(ih - 8, 16))
                table(x2 - 20, y2 - 14); plant(ix + 4, y2 - 16)

    @staticmethod
    def _draw_house_door(surf, dx, dy, inside):
        ts = TILE_SIZE
        pygame.draw.rect(surf, (74, 48, 28), (dx + 7, dy + 3, 18, ts - 4))       # 문틀
        col = (58, 40, 24) if inside else (132, 88, 50)                          # 열림/닫힘
        pygame.draw.rect(surf, col, (dx + 9, dy + 5, 14, ts - 6))                # 문짝
        pygame.draw.line(surf, (86, 58, 34), (dx + 16, dy + 5), (dx + 16, dy + ts - 1), 1)
        if not inside:
            pygame.draw.circle(surf, (232, 200, 96), (dx + 20, dy + ts // 2), 2)  # 손잡이

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

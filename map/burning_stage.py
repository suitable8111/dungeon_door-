"""
버닝 스테이지 — 60초 생존 보너스 아레나.
generate_arena()  : 넓은 단일 개방 공간 생성
spawn_wave()      : 아레나 외곽에서 적 배치
"""
import random
from map.tile import Tile, TileType
from map.dungeon import Dungeon

# ── 상수 ──────────────────────────────────────────────────────────────────
BURNING_DURATION_MS = 60_000     # 생존 목표 시간
SPAWN_INTERVAL_MS   = 1_500      # 파도 간격 (빠르게)
WAVE_SIZE_BASE      = 18         # 파도 기본 적 수
WAVE_SIZE_GROW      = 3          # 파도마다 증가
MAX_WAVE_SIZE       = 50         # 1회 최대 스폰
MAX_LIVE_ENEMIES    = 150        # 동시 최대 활성 적
BORDER              = 2          # 아레나 벽 두께
ARENA_WIDTH         = 52         # 아레나 타일 너비 (맵보다 좁음)
ARENA_HEIGHT        = 40         # 아레나 타일 높이

# 버닝 스테이지 바닥/배경용 테마
BURNING_THEME = {
    'name':       '불타는 아레나',
    'bg':         (15, 5, 0),
    'wall_lit':   (120, 40, 10),
    'wall_dim':   (60,  20, 5),
    'wall_top':   (180, 70, 20),
    'wall_bot':   (80,  25, 8),
    'floor_lit':  (40,  18, 5),
    'floor_dim':  (20,  8,  2),
    'floor_edge': (70,  30, 10),
    'stairs_lit': (255, 120, 30),
    'stairs_dim': (120, 60, 15),
}

# 버닝 스테이지 전용 적 풀 (강한 적 위주)
_HARD_KEYS = [
    'orc', 'troll', 'giant_zombie', 'ghoul', 'zombie',
    'steel_knight', 'dark_knight', 'mace_knight', 'stomp_exec',
    'death_mage', 'shadow_stalker', 'assassin', 'giant_spider',
    'chain_beast', 'rock_golem', 'blood_bat', 'soul_absorber',
]
_EASY_KEYS = [
    'goblin', 'rat', 'bat', 'centipede', 'spider',
    'skeleton', 'zombie', 'prisoner', 'ghoul', 'slime',
    'bandit', 'thief', 'ambusher',
]


def generate_arena() -> tuple:
    """
    개방형 아레나 생성.  바닥만 있는 단일 직사각형 공간.
    Returns (Dungeon, (start_x, start_y))
    """
    width, height = ARENA_WIDTH, ARENA_HEIGHT
    dungeon = Dungeon(width, height)

    # 내부 전부 바닥으로
    for y in range(BORDER, height - BORDER):
        for x in range(BORDER, width - BORDER):
            dungeon.tiles[y][x] = Tile.floor()

    # 전체 시야 공개
    dungeon.reveal_all()
    dungeon.stairs_pos = None

    center = (width // 2, height // 2)
    return dungeon, center


def spawn_wave(dungeon, enemy_data: dict,
               floor_level: int, wave_num: int) -> list:
    """
    아레나 외곽 경계에서 적 wave 생성.
    Returns list[Enemy]
    """
    from entities.enemy import Enemy
    from map.generator import _scale_enemy

    w, h = dungeon.width, dungeon.height
    spawn_margin = BORDER + 1

    all_keys = [k for k in enemy_data if k != '_comment']

    # 파도가 진행될수록 강한 적 비중 증가
    hard_ratio = min(0.8, wave_num * 0.07)
    pool = []
    for k in all_keys:
        if k in _HARD_KEYS:
            pool += [k] * (3 if random.random() < hard_ratio else 1)
        else:
            pool.append(k)

    n = min(WAVE_SIZE_BASE + wave_num * WAVE_SIZE_GROW, MAX_WAVE_SIZE)
    enemies = []

    for _ in range(n):
        # 외곽 4면 중 한 면에서 스폰
        edge = random.randint(0, 3)
        if edge == 0:   # 위
            x = random.randint(spawn_margin, w - spawn_margin - 1)
            y = spawn_margin
        elif edge == 1:  # 아래
            x = random.randint(spawn_margin, w - spawn_margin - 1)
            y = h - spawn_margin - 1
        elif edge == 2:  # 왼쪽
            x = spawn_margin
            y = random.randint(spawn_margin, h - spawn_margin - 1)
        else:            # 오른쪽
            x = w - spawn_margin - 1
            y = random.randint(spawn_margin, h - spawn_margin - 1)

        key = random.choice(pool)
        raw = dict(_scale_enemy(enemy_data[key], floor_level))
        raw['key'] = key
        # 버닝 스테이지: 이동·공격 속도 2배
        raw['move_ms']    = max(350, raw.get('move_ms',   900) // 2)
        raw['attack_ms']  = max(700, raw.get('attack_ms', 1500) // 2)
        raw['aware_range'] = 999   # 아레나 전체 — 스폰 즉시 플레이어 감지
        raw['chase_range'] = 999

        e = Enemy(x, y, raw)
        enemies.append(e)

    return enemies

"""50층마다 바뀌는 타일/배경 테마 정의 (총 20개, 999층까지)."""

# 각 테마: wall_lit/dim/top/bot, floor_lit/dim/edge, stairs_lit/dim, bg
_THEMES = [
    # ── 0: 1-49F  어둠의 던전 ────────────────────────────────────
    dict(name='어둠의 던전',
         wall_lit=(70,70,92),   wall_dim=(35,35,50),
         wall_top=(100,100,125),wall_bot=(42,42,58),
         floor_lit=(45,45,62),  floor_dim=(25,25,35), floor_edge=(58,58,78),
         stairs_lit=(210,175,85), stairs_dim=(105,88,42), bg=(0,0,0)),

    # ── 1: 50-99F  하수구 ──────────────────────────────────────
    dict(name='하수구',
         wall_lit=(55,75,55),   wall_dim=(28,40,28),
         wall_top=(75,105,65),  wall_bot=(35,50,30),
         floor_lit=(40,60,38),  floor_dim=(20,32,18), floor_edge=(52,75,48),
         stairs_lit=(180,165,60), stairs_dim=(90,82,30), bg=(4,7,4)),

    # ── 2: 100-149F  지하 동굴 ────────────────────────────────
    dict(name='지하 동굴',
         wall_lit=(85,65,45),   wall_dim=(45,35,25),
         wall_top=(115,90,60),  wall_bot=(55,40,28),
         floor_lit=(60,45,30),  floor_dim=(32,24,15), floor_edge=(75,58,40),
         stairs_lit=(220,180,90), stairs_dim=(110,90,45), bg=(4,3,2)),

    # ── 3: 150-199F  이끼 동굴 ───────────────────────────────
    dict(name='이끼 동굴',
         wall_lit=(45,82,50),   wall_dim=(22,42,26),
         wall_top=(60,112,65),  wall_bot=(28,52,32),
         floor_lit=(30,60,35),  floor_dim=(15,32,18), floor_edge=(38,76,45),
         stairs_lit=(190,215,80), stairs_dim=(95,108,40), bg=(2,5,3)),

    # ── 4: 200-249F  지하 사원 ──────────────────────────────
    dict(name='지하 사원',
         wall_lit=(70,55,105),  wall_dim=(38,28,58),
         wall_top=(95,78,140),  wall_bot=(46,35,68),
         floor_lit=(50,40,78),  floor_dim=(26,20,42), floor_edge=(65,52,98),
         stairs_lit=(200,165,255), stairs_dim=(100,82,128), bg=(4,2,8)),

    # ── 5: 250-299F  용암 동굴 ──────────────────────────────
    dict(name='용암 동굴',
         wall_lit=(105,45,25),  wall_dim=(55,22,12),
         wall_top=(142,65,36),  wall_bot=(66,28,15),
         floor_lit=(78,35,18),  floor_dim=(42,18,8),  floor_edge=(98,50,25),
         stairs_lit=(255,140,40), stairs_dim=(128,70,20), bg=(8,2,0)),

    # ── 6: 300-349F  얼음 동굴 ──────────────────────────────
    dict(name='얼음 동굴',
         wall_lit=(85,112,148), wall_dim=(45,58,80),
         wall_top=(120,152,192),wall_bot=(55,72,96),
         floor_lit=(62,86,118), floor_dim=(32,46,64), floor_edge=(80,108,148),
         stairs_lit=(160,222,255), stairs_dim=(80,111,128), bg=(4,6,12)),

    # ── 7: 350-399F  독 늪 ──────────────────────────────────
    dict(name='독 늪',
         wall_lit=(65,88,30),   wall_dim=(32,46,15),
         wall_top=(88,118,42),  wall_bot=(40,56,18),
         floor_lit=(48,66,22),  floor_dim=(25,35,10), floor_edge=(60,84,28),
         stairs_lit=(200,232,50), stairs_dim=(100,116,25), bg=(3,5,1)),

    # ── 8: 400-449F  고대 유적 ──────────────────────────────
    dict(name='고대 유적',
         wall_lit=(100,86,60),  wall_dim=(52,45,30),
         wall_top=(136,116,82), wall_bot=(64,54,38),
         floor_lit=(72,60,42),  floor_dim=(38,32,22), floor_edge=(92,76,55),
         stairs_lit=(215,185,100), stairs_dim=(108,92,50), bg=(6,5,3)),

    # ── 9: 450-499F  심연 ──────────────────────────────────
    dict(name='심연',
         wall_lit=(55,40,82),   wall_dim=(28,20,44),
         wall_top=(76,56,114),  wall_bot=(35,25,54),
         floor_lit=(38,28,62),  floor_dim=(18,12,32), floor_edge=(50,36,80),
         stairs_lit=(180,120,255), stairs_dim=(90,60,128), bg=(2,1,5)),

    # ── 10: 500-549F  지옥불 ────────────────────────────────
    dict(name='지옥불',
         wall_lit=(122,30,30),  wall_dim=(64,15,15),
         wall_top=(168,46,46),  wall_bot=(76,18,18),
         floor_lit=(90,22,22),  floor_dim=(47,10,10), floor_edge=(114,30,30),
         stairs_lit=(255,100,40), stairs_dim=(128,50,20), bg=(8,0,0)),

    # ── 11: 550-599F  수정 동굴 ─────────────────────────────
    dict(name='수정 동굴',
         wall_lit=(40,112,122), wall_dim=(20,58,66),
         wall_top=(56,152,168), wall_bot=(25,70,80),
         floor_lit=(28,82,92),  floor_dim=(14,42,48), floor_edge=(36,102,115),
         stairs_lit=(120,255,240), stairs_dim=(60,128,120), bg=(2,5,6)),

    # ── 12: 600-649F  흑요석 요새 ───────────────────────────
    dict(name='흑요석 요새',
         wall_lit=(48,48,54),   wall_dim=(24,24,30),
         wall_top=(68,68,78),   wall_bot=(30,30,38),
         floor_lit=(32,32,40),  floor_dim=(16,16,22), floor_edge=(42,42,52),
         stairs_lit=(160,160,205), stairs_dim=(80,80,102), bg=(2,2,4)),

    # ── 13: 650-699F  피의 동굴 ─────────────────────────────
    dict(name='피의 동굴',
         wall_lit=(92,25,36),   wall_dim=(48,12,18),
         wall_top=(128,38,52),  wall_bot=(58,15,22),
         floor_lit=(66,18,26),  floor_dim=(35,8,12),  floor_edge=(84,24,34),
         stairs_lit=(232,80,60), stairs_dim=(116,40,30), bg=(5,0,2)),

    # ── 14: 700-749F  어둠의 영역 ───────────────────────────
    dict(name='어둠의 영역',
         wall_lit=(76,66,98),   wall_dim=(38,33,52),
         wall_top=(106,92,136), wall_bot=(46,40,64),
         floor_lit=(56,48,74),  floor_dim=(28,24,38), floor_edge=(70,62,92),
         stairs_lit=(200,160,255), stairs_dim=(100,80,128), bg=(3,2,6)),

    # ── 15: 750-799F  망각의 고분 ───────────────────────────
    dict(name='망각의 고분',
         wall_lit=(80,72,46),   wall_dim=(42,38,23),
         wall_top=(110,100,64), wall_bot=(50,46,28),
         floor_lit=(58,52,32),  floor_dim=(30,27,16), floor_edge=(74,66,42),
         stairs_lit=(210,190,100), stairs_dim=(105,95,50), bg=(4,4,2)),

    # ── 16: 800-849F  어둠의 심연 ───────────────────────────
    dict(name='어둠의 심연',
         wall_lit=(42,38,70),   wall_dim=(22,19,38),
         wall_top=(58,54,98),   wall_bot=(26,24,46),
         floor_lit=(30,26,52),  floor_dim=(15,13,28), floor_edge=(38,34,66),
         stairs_lit=(140,100,232), stairs_dim=(70,50,116), bg=(1,1,4)),

    # ── 17: 850-899F  금빛 심연 ─────────────────────────────
    dict(name='금빛 심연',
         wall_lit=(80,70,36),   wall_dim=(42,36,18),
         wall_top=(116,100,52), wall_bot=(50,44,22),
         floor_lit=(56,48,24),  floor_dim=(28,25,12), floor_edge=(72,62,32),
         stairs_lit=(255,222,80), stairs_dim=(128,111,40), bg=(5,4,1)),

    # ── 18: 900-949F  혼돈의 영역 ───────────────────────────
    dict(name='혼돈의 영역',
         wall_lit=(102,40,102), wall_dim=(54,20,54),
         wall_top=(142,58,142), wall_bot=(64,25,64),
         floor_lit=(74,28,74),  floor_dim=(38,14,38), floor_edge=(92,36,92),
         stairs_lit=(255,100,255), stairs_dim=(128,50,128), bg=(6,2,6)),

    # ── 19: 950-999F  최후의 심연 ───────────────────────────
    dict(name='최후의 심연',
         wall_lit=(30,30,30),   wall_dim=(14,14,14),
         wall_top=(48,48,48),   wall_bot=(18,18,18),
         floor_lit=(20,20,20),  floor_dim=(8,8,8),    floor_edge=(28,28,28),
         stairs_lit=(255,255,255), stairs_dim=(180,180,180), bg=(0,0,0)),
]

MAX_FLOOR = 999


def get_theme(floor_level: int) -> dict:
    idx = min((floor_level - 1) // 50, len(_THEMES) - 1)
    return _THEMES[idx]


def theme_index(floor_level: int) -> int:
    return min((floor_level - 1) // 50, len(_THEMES) - 1)


def is_new_theme(floor_level: int) -> bool:
    """이 층이 새 테마 구간의 첫 층인지."""
    return floor_level > 1 and (floor_level - 1) % 50 == 0

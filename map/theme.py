"""테마 정의 — 50층마다 변경, 총 20구간 (999층까지).

themd.md 기반 배경/타일 색상 + 기믹 메타데이터.
각 테마 dict 키:
  name        — 테마 표시명
  gimmick     — 환경 기믹 설명 (UI 전용, 미래 확장)
  bgm         — BGMPlayer 트랙 키
  wall_lit/dim/top/bot, floor_lit/dim/edge, stairs_lit/dim, bg
"""

_THEMES = [

    # ── 0: 01-50F  버려진 지하 감옥 ─────────────────────────────────
    dict(name='버려진 지하 감옥',
         gimmick='기본 튜토리얼 구역, 좁은 통로',
         bgm='theme_0',
         wall_lit=(72, 70, 92),    wall_dim=(36, 35, 52),
         wall_top=(102,100,125),   wall_bot=(44, 42, 60),
         floor_lit=(46, 44, 62),   floor_dim=(24, 24, 36),  floor_edge=(60, 58, 80),
         stairs_lit=(210,175, 85), stairs_dim=(105, 88, 42), bg=(0, 0, 0)),

    # ── 1: 51-100F  곰팡이 핀 늪지대 ────────────────────────────────
    dict(name='곰팡이 핀 늪지대',
         gimmick='독 구름 지속 피해, 이동 저하',
         bgm='theme_1',
         wall_lit=(48, 68, 36),    wall_dim=(24, 36, 18),
         wall_top=(65, 95, 50),    wall_bot=(30, 44, 22),
         floor_lit=(34, 52, 25),   floor_dim=(16, 28, 12),  floor_edge=(44, 65, 32),
         stairs_lit=(155,205, 58), stairs_dim=(78, 102, 29), bg=(2, 5, 1)),

    # ── 2: 101-150F  서리 내린 정적의 고성 ──────────────────────────
    dict(name='서리 내린 정적의 고성',
         gimmick='미끄러운 바닥, 시야 축소',
         bgm='theme_2',
         wall_lit=(88,108,138),    wall_dim=(45, 56, 76),
         wall_top=(118,148,188),   wall_bot=(55, 68, 92),
         floor_lit=(62, 84,115),   floor_dim=(30, 44, 64),  floor_edge=(78,105,148),
         stairs_lit=(150,222,255), stairs_dim=(75,111,128),  bg=(4, 6, 12)),

    # ── 3: 151-200F  타오르는 마그마 굴 ────────────────────────────
    dict(name='타오르는 마그마 굴',
         gimmick='주기적 화염 분출, 용암 타일',
         bgm='theme_3',
         wall_lit=(110, 44, 18),   wall_dim=(58, 22,  8),
         wall_top=(150, 65, 28),   wall_bot=(68, 26, 10),
         floor_lit=( 82, 32, 12),  floor_dim=(42, 16,  5),  floor_edge=(104, 46, 18),
         stairs_lit=(255,130, 30), stairs_dim=(128, 65, 15), bg=(8, 2, 0)),

    # ── 4: 201-250F  기계 장치의 무덤 ──────────────────────────────
    dict(name='기계 장치의 무덤',
         gimmick='컨베이어 벨트, 움직이는 벽',
         bgm='theme_4',
         wall_lit=( 60, 72, 96),   wall_dim=(30, 36, 52),
         wall_top=( 85,100,132),   wall_bot=(36, 44, 64),
         floor_lit=( 42, 54, 74),  floor_dim=(22, 28, 40),  floor_edge=(56, 68, 92),
         stairs_lit=(168,198,245), stairs_dim=(84, 99,122),  bg=(2, 3, 6)),

    # ── 5: 251-300F  환각의 보랏빛 숲 ──────────────────────────────
    dict(name='환각의 보랏빛 숲',
         gimmick='방향키 반전(혼란), 가짜 벽',
         bgm='theme_5',
         wall_lit=( 78, 45,112),   wall_dim=(40, 22, 62),
         wall_top=(108, 68,155),   wall_bot=(48, 27, 72),
         floor_lit=( 55, 32, 85),  floor_dim=(28, 15, 45),  floor_edge=(70, 42,105),
         stairs_lit=(215,115,255), stairs_dim=(108, 58,128), bg=(3, 1, 8)),

    # ── 6: 301-350F  몰락한 성기사의 사원 ───────────────────────────
    dict(name='몰락한 성기사의 사원',
         gimmick='신성한 빛 (플레이어 위치 노출)',
         bgm='theme_6',
         wall_lit=( 95, 80, 52),   wall_dim=(50, 42, 26),
         wall_top=(132,112, 72),   wall_bot=(58, 48, 30),
         floor_lit=( 68, 56, 36),  floor_dim=(35, 28, 18),  floor_edge=(88, 72, 48),
         stairs_lit=(238,198, 92), stairs_dim=(119, 99, 46), bg=(5, 4, 2)),

    # ── 7: 351-400F  바람 부는 절벽 요새 ────────────────────────────
    dict(name='바람 부는 절벽 요새',
         gimmick='강풍 (플레이어를 한쪽으로 밀어냄)',
         bgm='theme_7',
         wall_lit=(108, 90, 64),   wall_dim=(56, 46, 32),
         wall_top=(148,124, 88),   wall_bot=(64, 52, 36),
         floor_lit=( 78, 64, 44),  floor_dim=(40, 32, 22),  floor_edge=(98, 80, 56),
         stairs_lit=(215,200,142), stairs_dim=(108,100, 71), bg=(5, 5, 3)),

    # ── 8: 401-450F  저주받은 도서관 ────────────────────────────────
    dict(name='저주받은 도서관',
         gimmick='무작위 스킬 쿨타임 증가',
         bgm='theme_8',
         wall_lit=( 78, 58, 38),   wall_dim=(40, 29, 18),
         wall_top=(108, 82, 52),   wall_bot=(48, 34, 22),
         floor_lit=( 55, 40, 25),  floor_dim=(27, 20, 12),  floor_edge=(72, 52, 33),
         stairs_lit=(202,160, 80), stairs_dim=(101, 80, 40), bg=(4, 3, 1)),

    # ── 9: 451-500F  심해의 가라앉은 도시 ───────────────────────────
    dict(name='심해의 가라앉은 도시',
         gimmick='산소 게이트 (시간 제한 느낌)',
         bgm='theme_9',
         wall_lit=( 30, 58, 95),   wall_dim=(15, 29, 52),
         wall_top=( 44, 82,132),   wall_bot=(18, 35, 62),
         floor_lit=( 20, 42, 72),  floor_dim=(10, 21, 38),  floor_edge=(28, 55, 90),
         stairs_lit=( 88,202,232), stairs_dim=(44,101,116),  bg=(1, 3, 7)),

    # ── 10: 501-550F  전기 회로의 미로 ──────────────────────────────
    dict(name='전기 회로의 미로',
         gimmick='바닥에 흐르는 전류 (주기적 경고)',
         bgm='theme_10',
         wall_lit=( 36, 80, 92),   wall_dim=(18, 40, 48),
         wall_top=( 52,112,130),   wall_bot=(22, 48, 58),
         floor_lit=( 24, 58, 72),  floor_dim=(12, 28, 36),  floor_edge=(32, 72, 90),
         stairs_lit=( 98,248,238), stairs_dim=(49,124,119),  bg=(1, 5, 6)),

    # ── 11: 551-600F  거대 곤충의 군집 ──────────────────────────────
    dict(name='거대 곤충의 군집',
         gimmick='거미줄 (이동 불가 구역)',
         bgm='theme_11',
         wall_lit=( 52, 68, 32),   wall_dim=(26, 35, 16),
         wall_top=( 72, 95, 44),   wall_bot=(32, 44, 18),
         floor_lit=( 36, 50, 22),  floor_dim=(18, 25, 10),  floor_edge=(48, 64, 28),
         stairs_lit=(172,218, 48), stairs_dim=(86,109, 24),  bg=(2, 4, 1)),

    # ── 12: 601-650F  황량한 붉은 사막 ──────────────────────────────
    dict(name='황량한 붉은 사막',
         gimmick='모래바람 (명중률 감소)',
         bgm='theme_12',
         wall_lit=(112, 68, 42),   wall_dim=(58, 34, 20),
         wall_top=(155, 95, 58),   wall_bot=(68, 40, 22),
         floor_lit=( 84, 52, 30),  floor_dim=(44, 26, 14),  floor_edge=(106, 66, 38),
         stairs_lit=(242,178, 82), stairs_dim=(121, 89, 41), bg=(6, 3, 1)),

    # ── 13: 651-700F  연금술사의 실험실 ─────────────────────────────
    dict(name='연금술사의 실험실',
         gimmick='무작위 시약 투척 (버프/디버프 혼재)',
         bgm='theme_13',
         wall_lit=( 44, 88, 72),   wall_dim=(22, 44, 36),
         wall_top=( 62,122,100),   wall_bot=(26, 54, 44),
         floor_lit=( 30, 65, 52),  floor_dim=(14, 32, 25),  floor_edge=(40, 82, 65),
         stairs_lit=(128,242,188), stairs_dim=(64,121, 94),  bg=(2, 5, 3)),

    # ── 14: 701-750F  천공의 무너진 섬 ──────────────────────────────
    dict(name='천공의 무너진 섬',
         gimmick='발판 무너짐 주의, 낮은 중력',
         bgm='theme_14',
         wall_lit=( 72, 98,130),   wall_dim=(36, 50, 68),
         wall_top=(100,135,178),   wall_bot=(44, 60, 82),
         floor_lit=( 52, 78,108),  floor_dim=(26, 38, 56),  floor_edge=(66, 95,135),
         stairs_lit=(185,232,255), stairs_dim=(92,116,128),  bg=(4, 7, 12)),

    # ── 15: 751-800F  그림자의 영역 ─────────────────────────────────
    dict(name='그림자의 영역',
         gimmick='완전한 어둠 (횃불 아이템 필요)',
         bgm='theme_15',
         wall_lit=( 40, 32, 58),   wall_dim=(20, 15, 30),
         wall_top=( 58, 48, 82),   wall_bot=(24, 18, 36),
         floor_lit=( 26, 20, 42),  floor_dim=(12,  9, 20),  floor_edge=(34, 26, 55),
         stairs_lit=(148, 96,232), stairs_dim=(74, 48,116),  bg=(1, 0, 3)),

    # ── 16: 801-850F  핏빛 달의 성소 ────────────────────────────────
    dict(name='핏빛 달의 성소',
         gimmick='흡혈 기믹 (피격 시 몬스터 회복)',
         bgm='theme_16',
         wall_lit=( 92, 18, 26),   wall_dim=(48,  8, 12),
         wall_top=(132, 28, 40),   wall_bot=(58, 10, 15),
         floor_lit=( 65, 12, 18),  floor_dim=(34,  5,  8),  floor_edge=(84, 18, 24),
         stairs_lit=(238, 80, 55), stairs_dim=(119, 40, 28), bg=(5, 0, 1)),

    # ── 17: 851-900F  왜곡된 시공간의 틈 ────────────────────────────
    dict(name='왜곡된 시공간의 틈',
         gimmick='무작위 텔레포트 트랩',
         bgm='theme_17',
         wall_lit=( 82, 54,112),   wall_dim=(42, 26, 60),
         wall_top=(115, 78,155),   wall_bot=(50, 32, 72),
         floor_lit=( 58, 38, 85),  floor_dim=(28, 18, 42),  floor_edge=(74, 50,108),
         stairs_lit=(222,158,255), stairs_dim=(111, 79,128), bg=(4, 2, 8)),

    # ── 18: 901-950F  고대 신의 무덤 ────────────────────────────────
    dict(name='고대 신의 무덤',
         gimmick='영구적인 디버프 중첩',
         bgm='theme_18',
         wall_lit=( 90, 72, 40),   wall_dim=(46, 36, 18),
         wall_top=(128,104, 58),   wall_bot=(54, 42, 22),
         floor_lit=( 64, 50, 28),  floor_dim=(32, 25, 12),  floor_edge=(82, 64, 36),
         stairs_lit=(248,212, 96), stairs_dim=(124,106, 48), bg=(4, 3, 1)),

    # ── 19: 951-999F  차원의 끝 (The Void) ──────────────────────────
    dict(name='차원의 끝',
         gimmick='이전 모든 테마의 기믹이 무작위 등장',
         bgm='theme_19',
         wall_lit=( 26, 22, 36),   wall_dim=(12, 10, 18),
         wall_top=( 42, 36, 58),   wall_bot=(16, 12, 22),
         floor_lit=( 16, 14, 24),  floor_dim=( 6,  5, 10),  floor_edge=(24, 20, 34),
         stairs_lit=(255,255,255), stairs_dim=(180,180,180), bg=(0, 0, 0)),
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

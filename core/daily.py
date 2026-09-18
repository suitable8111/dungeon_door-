"""일일 챌린지(Daily Challenge) — 날짜 기반 결정론적 무한 생존 시드.

핵심: '오늘의 시드'는 모든 플레이어에게 동일하다.
- 같은 아레나 지형 + 같은 시작 증강 3택 + 같은 '오늘의 변수(mutator)'
- 캐릭터 레벨은 전원 SURVIVAL_START_LEVEL 로 고정 → 리더보드가 공정
- mutator 는 하루마다 순환하며 전략을 바꾼다(도파민/재방문 동기)

시드는 날짜(YYYYMMDD)에서 파생 → 자정마다 새 챌린지. 로컬 기준일이라
개인 기기 시계를 따르지만, 같은 날이면 같은 시드/변수를 공유한다.
"""
import time

# ── 오늘의 변수(mutator) 목록 ────────────────────────────────────────────
# 각 변수는 적/플레이어에 곱연산으로 붙는 간단한 규칙.
#   enemy_hp / enemy_dmg : 스폰된 적 체력·공격 배율
#   spd       : 적 이동·공격 속도 배율(>1 = 빠름)
#   count     : 스폰 밀도 배율(동시 상한·1회 스폰수)
#   boss_early: True면 이른 웨이브부터 보스 등장
#   player    : 플레이어 시작 보정(None / 'lifesteal' / 'frost' / 'regen' / 'giant')
# label/desc 는 core.lang 키.
MUTATORS = [
    {'id': 'swarm',      'enemy_hp': 0.68, 'enemy_dmg': 1.0,  'spd': 1.0,
     'count': 1.7,  'boss_early': False, 'player': None},
    {'id': 'juggernaut', 'enemy_hp': 1.7,  'enemy_dmg': 1.15, 'spd': 0.85,
     'count': 0.8,  'boss_early': False, 'player': None},
    {'id': 'frenzy',     'enemy_hp': 0.9,  'enemy_dmg': 1.1,  'spd': 1.45,
     'count': 1.05, 'boss_early': False, 'player': 'frost'},
    {'id': 'boss_rush',  'enemy_hp': 1.15, 'enemy_dmg': 1.0,  'spd': 1.0,
     'count': 0.85, 'boss_early': True,  'player': None},
    {'id': 'glass',      'enemy_hp': 0.5,  'enemy_dmg': 1.65, 'spd': 1.2,
     'count': 1.25, 'boss_early': False, 'player': None},
    {'id': 'vampire',    'enemy_hp': 1.3,  'enemy_dmg': 1.0,  'spd': 1.0,
     'count': 1.0,  'boss_early': False, 'player': 'lifesteal'},
    {'id': 'titanfall',  'enemy_hp': 1.4,  'enemy_dmg': 1.1,  'spd': 0.95,
     'count': 0.9,  'boss_early': False, 'player': 'giant'},
]

_MUT_BY_ID = {m['id']: m for m in MUTATORS}


def daily_id(ts=None):
    """오늘 날짜 식별자 'YYYYMMDD' (로컬 기준). 리더보드/기록 키."""
    lt = time.localtime(ts)
    return f"{lt.tm_year:04d}{lt.tm_mon:02d}{lt.tm_mday:02d}"


def daily_seed(ts=None):
    """날짜에서 파생한 결정론적 시드(int). 아레나/시작 증강/변수 선택 공용."""
    return int(daily_id(ts))


def daily_mutator(ts=None):
    """오늘의 변수 — 날짜 시드로 순환 선택(전원 동일)."""
    return MUTATORS[daily_seed(ts) % len(MUTATORS)]


def mutator_by_id(mid):
    return _MUT_BY_ID.get(mid)


def prev_day(day_id):
    """주어진 'YYYYMMDD'의 전날 식별자. streak(연속 도전) 판정용."""
    try:
        tm = time.strptime(day_id, "%Y%m%d")
        return time.strftime("%Y%m%d", time.localtime(time.mktime(tm) - 86400))
    except Exception:
        return None

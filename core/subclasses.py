"""2차 전직(서브클래스) 시스템.

각 기본 직업(전사/궁수/마법사/도끼맨)은 레벨 40 + 전직 마스터 퀘스트 완료 후
2개 중 하나로 전직할 수 있다. **되돌릴 수 없다.**

설계 원칙:
- `player.char_class`(기본 직업)는 그대로 둔다 — 기존 스킬/콤보/궁극 분기가 전부
  기본 직업 기준이라 안전. 전직 정체성은 별도 `player.subclass` 필드로 관리.
- 전직 = 스탯 보너스(영구) + 표시명 변경 + (Phase2) 고유 궁극/패시브.
- 스탯 델타(stats)는 전직 순간 1회 적용된다.

Phase1: 스탯/표시명/전직흐름. Phase2에서 subclass별 고유 스킬·궁극을 채운다.
"""

# subclass_id → 정의
#   base    : 기본 직업
#   stats   : 전직 시 1회 적용되는 스탯 델타 (max_hp/attack/defense/move_speed/
#             attack_speed/evasion/sp_reduce_bonus)
#   name/desc 키는 lang.py의 sub_<id> / sub_<id>_desc
SUBCLASSES = {
    # ── 전사 ──────────────────────────────────────────────────────────
    'dual_blade': {
        'base': 'warrior',
        'stats': {'max_hp': 8, 'attack': 2, 'attack_speed': 0.5, 'evasion': 6},
    },
    'magic_swordsman': {
        'base': 'warrior',
        'stats': {'max_hp': 5, 'attack': 4, 'defense': 1, 'sp_reduce_bonus': 0.06},
    },
    # ── 궁수 ──────────────────────────────────────────────────────────
    'crossbow_master': {
        'base': 'archer',
        'stats': {'max_hp': 6, 'attack': 5, 'defense': 1},
    },
    'twin_bow': {
        'base': 'archer',
        'stats': {'max_hp': 3, 'attack': 1, 'attack_speed': 0.6,
                  'move_speed': 0.3, 'evasion': 6},
    },
    # ── 마법사 ────────────────────────────────────────────────────────
    'battle_mage': {
        'base': 'mage',
        'stats': {'max_hp': 14, 'attack': 3, 'defense': 3},
    },
    'speed_mage': {
        'base': 'mage',
        'stats': {'max_hp': 4, 'attack': 2, 'move_speed': 0.4,
                  'attack_speed': 0.5, 'sp_reduce_bonus': 0.10},
    },
    # 도끼맨: TBD (추후 추가)
}

# 기본 직업 → 선택 가능한 전직 2개 (순서 = 표시 순서)
SUBCLASS_CHOICES = {
    'warrior': ['dual_blade', 'magic_swordsman'],
    'archer':  ['crossbow_master', 'twin_bow'],
    'mage':    ['battle_mage', 'speed_mage'],
    # 'axeman': [...]  # TBD
}

ADVANCE_LEVEL = 40          # 전직 가능 레벨
ADVANCE_KILL_REQ = 300      # 전직 퀘스트: 일반 몬스터 처치 목표
ADVANCE_BOSS_REQ = 3        # 전직 퀘스트: 보스 처치 목표


def choices_for(char_class: str) -> list:
    return list(SUBCLASS_CHOICES.get(char_class, []))


def has_advancement(char_class: str) -> bool:
    return bool(SUBCLASS_CHOICES.get(char_class))


def base_of(subclass_id: str) -> str | None:
    d = SUBCLASSES.get(subclass_id)
    return d['base'] if d else None


def name_key(subclass_id: str) -> str:
    return f'sub_{subclass_id}'


def desc_key(subclass_id: str) -> str:
    return f'sub_{subclass_id}_desc'


def apply_subclass(player, subclass_id: str) -> bool:
    """전직 적용(1회) — 스탯 델타 반영 + player.subclass 설정. 되돌릴 수 없음."""
    d = SUBCLASSES.get(subclass_id)
    if not d or d['base'] != player.char_class or getattr(player, 'subclass', None):
        return False
    s = d['stats']
    player.max_hp += s.get('max_hp', 0)
    player.hp = player.max_hp                       # 전직 시 완전 회복
    player.attack += s.get('attack', 0)
    player.defense += s.get('defense', 0)
    player.move_speed += s.get('move_speed', 0.0)
    player.attack_speed += s.get('attack_speed', 0.0)
    player.evasion += s.get('evasion', 0)
    player.subclass_sp_reduce = getattr(player, 'subclass_sp_reduce', 0.0) \
        + s.get('sp_reduce_bonus', 0.0)
    player.subclass = subclass_id
    return True

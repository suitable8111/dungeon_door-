"""JSON 기반 저장 / 불러오기 / 설정 / 기록."""
import json
import os
import sys


def _get_data_dir():
    if getattr(sys, 'frozen', False):
        if sys.platform == 'darwin':
            base = os.path.expanduser('~/Library/Application Support/DungeonDoor')
        elif sys.platform == 'win32':
            base = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'DungeonDoor')
        else:
            base = os.path.join(os.path.expanduser('~'), '.dungeondoor')
        os.makedirs(base, exist_ok=True)
        return base
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


_DATA_DIR = _get_data_dir()

SAVE_PATH     = os.path.join(_DATA_DIR, 'savegame.json')   # 레거시(단일) 세이브
SETTINGS_PATH = os.path.join(_DATA_DIR, 'settings.json')
RECORDS_PATH  = os.path.join(_DATA_DIR, 'records.json')

# ── 세이브 슬롯 (캐릭터 카드) ────────────────────────────────────────
SLOT_COUNT = 3


def slot_path(slot: int) -> str:
    return os.path.join(_DATA_DIR, f'save_slot{slot}.json')


def migrate_legacy_save():
    """구 단일 savegame.json → 슬롯1로 1회 이관 (최초 실행 호환)."""
    if os.path.exists(SAVE_PATH) and not os.path.exists(slot_path(1)):
        try:
            os.rename(SAVE_PATH, slot_path(1))
        except Exception:
            pass


def list_cards() -> list:
    """슬롯 1..N의 카드 요약. 빈 슬롯은 exists=False."""
    cards = []
    for slot in range(1, SLOT_COUNT + 1):
        d = load_game(slot)
        if d:
            pl = d.get('player', {})
            cards.append({'slot': slot, 'exists': True,
                          'name': d.get('name') or pl.get('name') or 'Hero',
                          'char_class': d.get('char_class', 'warrior'),
                          'appearance': d.get('appearance')
                                        or pl.get('appearance')
                                        or {'skin': 0, 'hair': 0, 'haircol': 0},
                          'floor': d.get('floor', 1),
                          'level': pl.get('level', 1)})
        else:
            cards.append({'slot': slot, 'exists': False})
    return cards

_DEFAULT_SETTINGS = {'bgm_vol': 0.5, 'sfx_vol': 0.8, 'fullscreen': False, 'language': 'en'}
_DEFAULT_RECORDS  = {'best_floor': 0, 'best_kills': 0, 'best_gold': 0, 'total_runs': 0}


# ── 세이브 ──────────────────────────────────────────────────────────
def save_game(player, floor, skill_mgr, unlocked_combos=None, skill_books=None,
              skill_levels=None, skill_xp=None, skill_points=0, equipped_skills=None,
              skill_enchants=None, quests=None, max_floor_reached=0,
              slot=1, name=None, char_class=None):
    data = {
        'floor': floor,
        'name':       name or getattr(player, 'char_name', '') or 'Hero',
        'char_class': char_class or getattr(player, 'char_class', 'warrior'),
        'appearance': dict(getattr(player, 'appearance', None)
                           or {'skin': 0, 'hair': 0, 'haircol': 0}),
        'player': {
            'hp': player.hp, 'max_hp': player.max_hp,
            'attack': player.attack, 'defense': player.defense,
            'level': player.level, 'xp': player.xp, 'xp_next': player.xp_next,
            'gold': player.gold,
            'enhance_stones': player.enhance_stones,
            'attack_speed': player.attack_speed,
            'evasion':      player.evasion,
            'move_speed':   player.move_speed,
            'inventory': [
                {'key': item.key, 'enhance_level': item.enhance_level,
                 'durability': item.durability}
                for item in player.inventory
            ],
            'equipment': {
                slot: ({'key': item.key, 'enhance_level': item.enhance_level,
                        'durability': item.durability} if item else None)
                for slot, item in player.equipment.items()
            },
        },
        'skills': skill_mgr.to_dict(),
        'unlocked_combos': list(unlocked_combos) if unlocked_combos else [],
        'skill_books': list(skill_books) if skill_books else [],
        'skill_levels':  skill_levels  or {},
        'skill_xp':      skill_xp      or {},
        'skill_points':  skill_points,
        'equipped_skills': equipped_skills or {},
        'skill_enchants':  skill_enchants  or {},
        'quests':          quests or {},
        'max_floor_reached': max_floor_reached,
    }
    try:
        with open(slot_path(slot), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def load_game(slot: int = 1):
    try:
        with open(slot_path(slot), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def has_save(slot: int = 1):
    return os.path.exists(slot_path(slot))


def delete_save(slot: int = 1):
    try:
        if os.path.exists(slot_path(slot)):
            os.remove(slot_path(slot))
    except Exception:
        pass


# ── 설정 ──────────────────────────────────────────────────────────
def load_settings():
    try:
        with open(SETTINGS_PATH, encoding='utf-8') as f:
            d = json.load(f)
            return {**_DEFAULT_SETTINGS, **d}
    except Exception:
        return dict(_DEFAULT_SETTINGS)


def save_settings(d):
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ── 영구 창고 (마을 주모) — 사망/새 게임과 무관하게 유지 ────────────
STORAGE_PATH = os.path.join(_DATA_DIR, 'storage.json')


STORAGE_BASE_CAP = 30


def load_storage() -> tuple:
    """(items, capacity). 구버전(list) 포맷은 기본 용량으로 마이그레이션."""
    try:
        with open(STORAGE_PATH, encoding='utf-8') as f:
            d = json.load(f)
        if isinstance(d, list):                      # 구 포맷
            return d, STORAGE_BASE_CAP
        if isinstance(d, dict):
            return (d.get('items', []),
                    int(d.get('capacity', STORAGE_BASE_CAP)))
    except Exception:
        pass
    return [], STORAGE_BASE_CAP


def save_storage(entries: list, capacity: int = STORAGE_BASE_CAP):
    try:
        with open(STORAGE_PATH, 'w', encoding='utf-8') as f:
            json.dump({'items': entries, 'capacity': capacity},
                      f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ── 최고 기록 ─────────────────────────────────────────────────────
def load_records():
    try:
        with open(RECORDS_PATH, encoding='utf-8') as f:
            d = json.load(f)
            return {**_DEFAULT_RECORDS, **d}
    except Exception:
        return dict(_DEFAULT_RECORDS)


def save_records(d):
    try:
        with open(RECORDS_PATH, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def update_records(floor, kills, gold):
    """현재 런 결과로 최고 기록 갱신. 갱신된 records dict 반환."""
    rec = load_records()
    rec['total_runs'] = rec.get('total_runs', 0) + 1
    rec['best_floor'] = max(rec.get('best_floor', 0), floor)
    rec['best_kills'] = max(rec.get('best_kills', 0), kills)
    rec['best_gold']  = max(rec.get('best_gold',  0), gold)
    save_records(rec)
    return rec

"""JSON 기반 저장 / 불러오기 / 설정 / 기록."""
import json
import os

_BASE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.join(_BASE, '..')

SAVE_PATH     = os.path.join(_PARENT, 'savegame.json')
SETTINGS_PATH = os.path.join(_PARENT, 'settings.json')
RECORDS_PATH  = os.path.join(_PARENT, 'records.json')

_DEFAULT_SETTINGS = {'bgm_vol': 0.5, 'sfx_vol': 0.8, 'fullscreen': False, 'language': 'ko'}
_DEFAULT_RECORDS  = {'best_floor': 0, 'best_kills': 0, 'best_gold': 0, 'total_runs': 0}


# ── 세이브 ──────────────────────────────────────────────────────────
def save_game(player, floor, skill_mgr, unlocked_combos=None, skill_books=None,
              skill_levels=None, skill_xp=None, skill_points=0, equipped_skills=None,
              skill_enchants=None):
    data = {
        'floor': floor,
        'player': {
            'hp': player.hp, 'max_hp': player.max_hp,
            'attack': player.attack, 'defense': player.defense,
            'level': player.level, 'xp': player.xp, 'xp_next': player.xp_next,
            'gold': player.gold,
            'enhance_stones': player.enhance_stones,
            'attack_speed': player.attack_speed,
            'evasion':      player.evasion,
            'move_speed':   player.move_speed,
            'arcane_sp':    getattr(player, 'arcane_sp', 0),
            'inventory': [
                {'key': item.key, 'enhance_level': item.enhance_level}
                for item in player.inventory
            ],
            'equipment': {
                slot: ({'key': item.key, 'enhance_level': item.enhance_level} if item else None)
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
    }
    try:
        with open(SAVE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def load_game():
    try:
        with open(SAVE_PATH, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def has_save():
    return os.path.exists(SAVE_PATH)


def delete_save():
    try:
        if os.path.exists(SAVE_PATH):
            os.remove(SAVE_PATH)
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

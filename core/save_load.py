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


def use_test_data(enable: bool = True):
    """테스트 모드: 기록/창고를 격리된 *_test.json 파일로 리다이렉트.

    test_main.py 에서 정복 일지/마스터 정산을 실제 세이브 오염 없이 시험할 때 사용.
    """
    global RECORDS_PATH, STORAGE_PATH
    if enable:
        RECORDS_PATH = os.path.join(_DATA_DIR, 'records_test.json')
        STORAGE_PATH = os.path.join(_DATA_DIR, 'storage_test.json')
    else:
        RECORDS_PATH = os.path.join(_DATA_DIR, 'records.json')
        STORAGE_PATH = os.path.join(_DATA_DIR, 'storage.json')

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

_DEFAULT_SETTINGS = {'bgm_vol': 0.5, 'sfx_vol': 0.8, 'fullscreen': False, 'language': 'en',
                     'tips': True}
_DEFAULT_RECORDS  = {
    'best_floor': 0, 'best_kills': 0, 'best_gold': 0, 'total_runs': 0,
    # ── 정복 일지 / 마스터 정산 (교차-런 프로필) ──
    'theme_clears': {},        # {str(theme_idx): 클리어 횟수}
    'game_cleared': False,     # 999층 최종 클리어 여부
    'unlocked_titles': [],     # 해금 칭호 id 목록
    'active_title': '',        # 현재 표시 칭호 id
    'ng_plus': 0,              # New Game+ 회차 (골드 배율에 사용)
    'classes_unlocked': False, # 궁수·마법사 해금 여부 (전사 Lv20·20층 달성 시)
    'axeman_unlocked': False,  # 도끼맨 해금 여부 (Lv30·40층 달성 시 — 4번째 클래스)
    'home_style': 0,           # 내 집 인테리어 스타일 (마을 커스터마이즈)
    'max_boss_floor': 0,       # 클리어한 최고 보스층 (내 집 전리품 진열용)
    'farm': [],                # 마을 밭 상태 [{crop, stage}…] (인터랙티브 농장)
    'ranch': [],               # 목장 상태 [{animal, fed, stage}…] (가축 사육)
    'harvest_total': 0,        # 누적 수확 횟수 (농사 퀘스트 이정표)
    'rare_plants': {},         # 희귀식물 보유 {sunbloom/ironvine/galeleaf: n}
    'relic_bonus': {},         # 영구 강화 {atk/def/eva: +n} (고대 제단)
    'altar_claimed': [],       # 교환 완료한 고대 무기 key 목록
    'fish_caught': {},         # 낚은 물고기 {어종key: n}
    'fish_total': 0,           # 누적 낚시 성공 횟수
    'angler_claimed': [],      # 교환 완료한 고대 유물(장신구) key 목록
}

# ── 상급 직업 해금 조건 ──────────────────────────────────────────────────
ADVANCED_CLASSES = ('archer', 'mage')
UNLOCK_LEVEL = 20
UNLOCK_FLOOR = 20

# 도끼맨은 4번째 클래스 — 더 높은 조건(직업 무관)
AXEMAN_UNLOCK_LEVEL = 30
AXEMAN_UNLOCK_FLOOR = 40


def axeman_unlocked(records=None) -> bool:
    """도끼맨 생성 가능 여부 — 명시 플래그(axeman_unlocked)로만 판정.
    어떤 캐릭터로든 Lv30 이상 + 40층 이상 클리어 시 해금된다."""
    rec = records if records is not None else load_records()
    return bool(rec.get('axeman_unlocked'))


def advanced_classes_unlocked(records=None) -> bool:
    """궁수·마법사 생성 가능 여부 — 엄격 게이팅.

    오직 명시 플래그(classes_unlocked)로만 판정한다. 이 플래그는 전사로
    Lv20 이상 + 20층 이상 클리어를 달성했을 때(_check_class_unlock) 설정된다.
    과거 best_floor 기록으로는 해금되지 않는다(구제 없음).
    """
    rec = records if records is not None else load_records()
    return bool(rec.get('classes_unlocked'))


# ── 세이브 ──────────────────────────────────────────────────────────
def save_game(player, floor, skill_mgr, unlocked_combos=None, skill_books=None,
              skill_levels=None, skill_xp=None, skill_points=0, equipped_skills=None,
              skill_enchants=None, quests=None, max_floor_reached=0,
              slot=1, name=None, char_class=None, coop_quests=None, in_town=False):
    data = {
        'floor': floor,
        'in_town': bool(in_town),   # 마을에서 저장 시 재접속도 마을로
        'name':       name or getattr(player, 'char_name', '') or 'Hero',
        'char_class': char_class or getattr(player, 'char_class', 'warrior'),
        'subclass':   getattr(player, 'subclass', None),
        'subclass_sp_reduce': getattr(player, 'subclass_sp_reduce', 0.0),
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
            'advance_kills': getattr(player, 'advance_kills', 0),
            'advance_boss':  getattr(player, 'advance_boss', 0),
            'tokens':       dict(getattr(player, 'tokens', {}) or {}),
            # 펫 시스템 (캐릭터 슬롯에 저장 — 런당 지속)
            'is_pet_unlocked': player.is_pet_unlocked,
            'pet_type':  player.pet_type,
            'pet_level': player.pet_level,
            'pet_stones': player.pet_stones,
            'inventory': [
                {'key': item.key, 'enhance_level': item.enhance_level,
                 'durability': item.durability,
                 'count': getattr(item, 'count', 1)}
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
        'coop_quests':     coop_quests or {},
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
    import copy
    rec = copy.deepcopy(_DEFAULT_RECORDS)
    try:
        with open(RECORDS_PATH, encoding='utf-8') as f:
            rec.update(json.load(f))
    except Exception:
        pass
    # 가변 필드 방어 (구버전 세이브 호환)
    if not isinstance(rec.get('theme_clears'), dict):
        rec['theme_clears'] = {}
    if not isinstance(rec.get('unlocked_titles'), list):
        rec['unlocked_titles'] = []
    return rec


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


# ── 정복 일지 / 마스터 정산 ──────────────────────────────────────────────
FINAL_TITLE = 'abyss_sovereign'   # [심연의 지배자]


def record_theme_clear(theme_idx: int, records: dict | None = None) -> dict:
    """지역 테마 한 구간을 완수했을 때 클리어 횟수 +1. 갱신 records 반환."""
    rec = records if records is not None else load_records()
    tc = rec.setdefault('theme_clears', {})
    k = str(theme_idx)
    tc[k] = tc.get(k, 0) + 1
    save_records(rec)
    return rec


def grant_master_completion(records: dict | None = None) -> dict:
    """999층 최종 클리어 영구 보상: 칭호 해금 + NG+ 회차 증가. records 반환.

    종결 무기 지급은 storage(영구 창고)에서 별도 처리한다(게임 로직).
    """
    rec = records if records is not None else load_records()
    rec['game_cleared'] = True
    titles = rec.setdefault('unlocked_titles', [])
    if FINAL_TITLE not in titles:
        titles.append(FINAL_TITLE)
    if not rec.get('active_title'):
        rec['active_title'] = FINAL_TITLE
    rec['ng_plus'] = rec.get('ng_plus', 0) + 1
    save_records(rec)
    return rec


def ng_plus_gold_mult(records: dict | None = None) -> float:
    """New Game+ 영구 골드 배율 (회차당 +50%)."""
    rec = records if records is not None else load_records()
    return 1.0 + 0.5 * rec.get('ng_plus', 0)

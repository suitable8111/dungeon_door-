import math
import os
import random
import sys
import pygame

from core.constants import *
from core.camera import Camera
from core.input_handler import InputHandler
from core.animator import (Animator, LungeAnim, SlashAnim, HitFlashAnim, BoltAnim,
                            AttackSwingAnim, DashTrailAnim, WhirlAnim, HealAnim,
                            DeathAnim, GoldPopAnim, BannerAnim,
                            SmearAnim, ThrustSmearAnim, AfterimageAnim, CalloutAnim,
                            ArrowAnim, MagicBoltAnim, ShockwaveAnim)
from core.audio import AudioManager
from core.skills import (SkillManager, SKILL_DEFS, COMBO_SKILL_DEFS, SKILL_UPGRADES,
                         SKILL_MAX_LEVEL, SKILL_XP_REQ, ULTIMATE_SKILL_DEFS,
                         SKILL_SP_COST, ALL_SKILL_DEFS, DEFAULT_EQUIPPED,
                         ENCHANT_DEFS, ENCHANT_TYPES, ENCHANT_MAX_LEVEL,
                         default_equipped_for, combo_def)
from core.save_load import (save_game, load_game, has_save, delete_save,
                             load_settings, save_settings,
                             load_records, update_records, save_records,
                             record_theme_clear, grant_master_completion,
                             ng_plus_gold_mult, FINAL_TITLE,
                             load_storage, save_storage,
                             list_cards, migrate_legacy_save, SLOT_COUNT)
from core.net_stub import NetworkManager, build_user_profile
from map.theme import theme_index
from core.lang import t, set_lang
from core.combat import roll_damage
from map.generator import generate_dungeon
from map.tile import Tile, TileType, CONVEYOR_DIR
from map.theme import get_theme, is_new_theme, MAX_FLOOR, theme_fx
from entities.player import Player
from entities.pet import Pet, PET_META, PET_TYPES
from ui.hud import HUD
from data_loader import load_enemies, load_items

# ─────────────────────────────────────────────────────────────────────────────
# 색상 상수
# ─────────────────────────────────────────────────────────────────────────────
_GOLD   = (235, 185,  60); _GOLD_D = (150, 108, 18); _GOLD_L = (255, 222, 105)
_SIL    = (178, 183, 202); _SIL_D  = (118, 123, 148)
_BLUE   = ( 62, 103, 162); _BLUE_D = ( 38,  66, 115)
_BELT   = ( 95,  60,  20); _BOOT   = ( 88,  55,  25)
_BLACK  = (  0,   0,   0); _RED    = (200,  48,  48)
_PLUME  = (230,  80,  80)
_CKEY   = (  1,   2,   3)


def _r(s, c, x, y, w, h): pygame.draw.rect(s, c, (x, y, w, h))
def _p(s, c, pts):         pygame.draw.polygon(s, c, pts)

# ─────────────────────────────────────────────────────────────────────────────
# 플레이어 스프라이트
# ─────────────────────────────────────────────────────────────────────────────
def _helm(s, x, y):
    _r(s,_GOLD,  x+10,y+2,12,10); _r(s,_GOLD_L,x+10,y+2,12,2)
    _r(s,_GOLD_D,x+10,y+4,12, 8)
    _r(s,_GOLD_D,x+ 8,y+5, 2, 6); _r(s,_GOLD_D,x+22,y+5,2,6)
    _r(s,_BLACK, x+11,y+6,10, 3); _r(s,_GOLD_D,x+11,y+6,10,1)
    _r(s,_RED,   x+15,y+0, 2, 3); _r(s,_PLUME, x+14,y+1,4,2)

def _helm_back(s, x, y):
    _r(s,_GOLD,  x+10,y+2,12,10); _r(s,_GOLD_L,x+10,y+2,12,2)
    _r(s,_GOLD_D,x+10,y+4,12, 8)
    _r(s,_GOLD_D,x+ 8,y+5, 2, 6); _r(s,_GOLD_D,x+22,y+5,2,6)
    _r(s,_RED,   x+15,y+0, 2, 3); _r(s,_PLUME, x+14,y+1,4,2)

def _body(s, x, y):
    _r(s,_GOLD,  x+ 5,y+11,8,5); _r(s,_GOLD_L,x+ 5,y+11,8,1)
    _r(s,_GOLD,  x+19,y+11,8,5); _r(s,_GOLD_L,x+19,y+11,8,1)
    _r(s,_BLUE,  x+ 9,y+11,14,14)
    _r(s,_BLUE_D,x+10,y+12,12,12)
    _r(s,_SIL,   x+14,y+13, 4, 9); _r(s,_SIL_D,x+15,y+13,2,9)
    _r(s,_BELT,  x+ 9,y+25,14, 3); _r(s,_GOLD, x+14,y+25,4,3)
    _r(s,_GOLD_L,x+15,y+25, 2, 1)

def _legs_front(s, x, y, frame):
    Loff = 0 if frame == 0 else 2; Roff = 2 if frame == 0 else 0
    _r(s,_BLUE, x+10,y+28-Loff,5,3); _r(s,_BOOT,x+ 9,y+29-Loff,6,2); _r(s,_BLACK,x+ 9,y+31-Loff,6,1)
    _r(s,_BLUE, x+17,y+28-Roff,5,3); _r(s,_BOOT,x+17,y+29-Roff,6,2); _r(s,_BLACK,x+17,y+31-Roff,6,1)

def _player_down(s, x, y, frame):
    _r(s,_SIL,  x+24,y+10,3,14); _r(s,_SIL_D,x+24,y+10,1,14)
    _r(s,_GOLD_D,x+21,y+18,8,2); _r(s,_GOLD, x+24,y+20,3,5)
    _p(s,_BLUE_D,[(x+5,y+13),(x+9,y+13),(x+9,y+23),(x+7,y+27),(x+5,y+23)])
    _r(s,_SIL,  x+5,y+13,1,10)
    _body(s,x,y); _legs_front(s,x,y,frame); _helm(s,x,y)

def _player_up(s, x, y, frame):
    _r(s,_SIL,  x+7, y+11,3,14); _r(s,_SIL_D,x+8,y+11,1,14)
    _r(s,_GOLD_D,x+5,y+18,8,2);  _r(s,_GOLD, x+7,y+20,3,5)
    _p(s,_BLUE_D,[(x+23,y+13),(x+27,y+13),(x+27,y+23),(x+25,y+27),(x+23,y+23)])
    _r(s,_SIL,  x+27,y+13,1,10)
    _body(s,x,y); _r(s,_SIL,x+14,y+13,4,9); _r(s,_SIL_D,x+15,y+13,2,9)
    _legs_front(s,x,y,frame); _helm_back(s,x,y)

def _player_left_raw(s, x, y, frame):
    fl_x,bl_x = (x+9,x+16) if frame==0 else (x+16,x+9)
    fl_y,bl_y = y+29, y+27
    _r(s,_BLUE_D,bl_x,bl_y-3,4,3); _r(s,_BOOT,bl_x-1,bl_y,5,2); _r(s,_BLACK,bl_x-1,bl_y+2,5,1)
    _p(s,_BLUE_D,[(x+19,y+14),(x+23,y+14),(x+23,y+23),(x+21,y+26),(x+19,y+23)])
    _r(s,_SIL,x+22,y+14,1,9)
    _r(s,_GOLD_D,x+17,y+11,5,4); _r(s,_GOLD,x+9,y+11,7,5); _r(s,_GOLD_L,x+9,y+11,7,1)
    _r(s,_BLUE,x+10,y+11,12,14); _r(s,_BLUE_D,x+11,y+12,10,12)
    _r(s,_SIL,x+14,y+13,3,9); _r(s,_BELT,x+10,y+25,12,3); _r(s,_GOLD,x+14,y+25,4,3)
    _r(s,_GOLD,x+5,y+14,6,5); _r(s,_GOLD,x+4,y+19,5,7)
    _r(s,_SIL,x+1,y+20,9,2); _r(s,_SIL_D,x+1,y+20,9,1)
    _r(s,_GOLD_D,x+7,y+18,3,6); _r(s,_GOLD,x+8,y+19,5,4); _r(s,_GOLD_L,x+9,y+19,2,1)
    _r(s,_BLUE,fl_x,fl_y-3,5,3); _r(s,_BOOT,fl_x-1,fl_y,7,2); _r(s,_BLACK,fl_x-1,fl_y+2,7,1)
    _r(s,_GOLD,x+8,y+2,16,10); _r(s,_GOLD_L,x+8,y+2,16,2); _r(s,_GOLD_D,x+8,y+4,16,8)
    _r(s,_GOLD_D,x+7,y+5,3,6); _r(s,_BLACK,x+7,y+7,2,3); _r(s,_GOLD,x+21,y+3,5,8)
    _r(s,_GOLD_D,x+8,y+10,5,2); _r(s,_RED,x+14,y+0,2,3); _r(s,_PLUME,x+13,y+1,4,2)

def draw_player(surf, x, y, facing='down', walk_frame=0):
    ts = TILE_SIZE
    if facing in ('left', 'right'):
        tmp = pygame.Surface((ts, ts)); tmp.fill(_CKEY); tmp.set_colorkey(_CKEY)
        _player_left_raw(tmp, 0, 0, walk_frame)
        if facing == 'right':
            tmp = pygame.transform.flip(tmp, True, False); tmp.set_colorkey(_CKEY)
        surf.blit(tmp, (x, y))
    elif facing == 'up':
        _player_up(surf, x, y, walk_frame)
    else:
        _player_down(surf, x, y, walk_frame)

def draw_hp_bar(s, x, y, hp, max_hp):
    bw = TILE_SIZE - 4; ratio = max(0.0, hp / max_hp)
    _r(s,(70,20,20),x+2,y+2,bw,4)
    if ratio > 0:
        _r(s,(200+int(55*(1-ratio)),int(210*ratio),40),x+2,y+2,max(1,int(bw*ratio)),4)

from entities.enemy_sprites import ENEMY_SPRITE_FNS as _SPRITE_FN, draw_generic
from entities.mob_sprites import MC_ENEMY_SPRITE_FNS as _MC_SPRITE_FN, mc_generic
from entities.enemy import ELITE_AFFIXES
from entities.player_renderer import draw_player_layered
from core.skill_effect import SkillEffect
from map.burning_stage import (generate_arena, spawn_wave,
                                BURNING_DURATION_MS, SPAWN_INTERVAL_MS,
                                MAX_LIVE_ENEMIES, BURNING_THEME,
                                ARENA_WIDTH, ARENA_HEIGHT)


# ─────────────────────────────────────────────────────────────────────────────
# 윈도우 아이콘 (32×32 절차적 픽셀아트)
# ─────────────────────────────────────────────────────────────────────────────
def _make_icon():
    surf = pygame.Surface((32, 32))
    surf.fill((10, 10, 20))
    # 별 장식
    for pos in [(4,4),(27,3),(2,25),(29,27),(15,2)]:
        pygame.draw.rect(surf, (180,180,180), (pos[0], pos[1], 1, 1))
    # 투구
    _r(surf,(150,108,18),7,5,18,13); _r(surf,(235,185,60),7,5,18,12)
    _r(surf,(255,222,105),7,5,18,3); _r(surf,(150,108,18),7,8,18,10)
    _r(surf,(0,0,0),9,10,14,4); _r(surf,(150,108,18),9,10,14,1)
    _r(surf,(200,48,48),15,1,2,4); _r(surf,(230,80,80),14,2,4,2)
    # 검
    _r(surf,(178,183,202),13,21,6,9); _r(surf,(118,123,148),13,21,2,9)
    _r(surf,(235,185,60),10,26,12,2); _r(surf,(255,222,105),11,26,2,1)
    return surf


# ═════════════════════════════════════════════════════════════════════════════
#  Game class
# ═════════════════════════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        # 아이콘은 set_mode 전에 설정
        try:
            pygame.display.set_icon(_make_icon())
        except Exception:
            pass

        self._settings = load_settings()
        set_lang(self._settings.get('language', 'en'))
        flags = (pygame.FULLSCREEN | pygame.SCALED) if self._settings.get('fullscreen') else 0
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        pygame.display.set_caption("Dungeon Door")

        self.clock    = pygame.time.Clock()
        self.input    = InputHandler()
        self.hud      = HUD()
        self.animator = Animator()
        self.audio    = AudioManager()
        self.skills   = SkillManager()

        # 도파민 VFX 계층 (core/vfx.py) — 상태와 분리된 연출 오버레이
        from core.vfx import JuiceManager, LootFXManager
        self.juice    = JuiceManager(self)
        self.vfx_loot = LootFXManager(self.audio)

        # 오디오 볼륨 적용
        if self.audio.bgm:
            self.audio.bgm.set_volume(self._settings['bgm_vol'])
        self.audio.set_sfx_volume(self._settings['sfx_vol'])

        self._game_surf  = pygame.Surface((GAME_W, GAME_H))
        self._enemy_data = load_enemies()
        self._item_data  = load_items()
        self._load_sprites()

        self.messages = []
        self.floor    = 1
        self._theme   = get_theme(1)

        # 도전과제 (로컬 저장 + 스팀 자동 동기화)
        from core.achievements import AchievementManager
        self.achievements = AchievementManager(on_unlock=self._on_achievement_unlocked)
        self._facing     = 'down'
        self._walk_frame = 0

        # 화면 흔들림
        self._shake_timer     = 0
        self._shake_intensity = 0
        self._shake_max       = 1

        # 동적 맵 이펙터
        self._distort_amp     = 0.0    # 사인파 화면 왜곡 진폭(px, 0=없음)
        self._conveyor_t      = 0.0    # 컨베이어 밀림 누적 타이머(ms)
        # 동적 위험(이동벽 게이트 / 주기 가시) 상태
        self._shift_walls: list = []   # [{'x','y','phase'}] — 이동벽 게이트/기둥
        self._spikes: list      = []   # [{'x','y','phase','armed'}] — 주기 가시
        self._shift_t         = 0.0    # 개폐/발동 공통 사이클 타이머(ms)
        self._shift_open_ms   = 0.0    # 압력판으로 전부 강제 개방 잔여시간
        # 마법사 DoT 장판 / 소환수 (런타임 전용, 층 이동 시 소멸)
        self._dot_zones: list = []     # [{'x','y','r','dps','ms','col','tick'}]
        self._summons:   list = []     # entities.summon.Summon 목록
        self._bombs:     list = []     # 투척 폭탄 [{'x','y','fuse','r'}]
        # 붕괴 추격 세트피스
        self._collapse_active = False
        self._collapse_t      = 0.0    # 붕괴 진행 타이머(ms)
        self._crumble: dict   = {}     # {(x,y): 무너지는 시각(ms)}
        self._collapse_reward = None   # 제단으로 예약된 탈출 보상(탈출 성공 시 지급)
        self._keys = 0                 # 현재 층에서 주운 금고 열쇠 수
        self._thrown_axe = None        # 도끼맨: 바닥에 던져진 도끼 {x,y} (밟아 회수)
        self._axe_throw_cd_ms = 0      # 회수 안 하고 재투척 시 10초 쿨
        self._ragnarok_ms = 0          # 도끼맨: 라그나로크(무적 돌진) 잔여 ms
        self._ragnarok_aura_t = 0.0    # 라그나로크 접촉 오라 데미지 틱 누적

        # 엔딩 크레딧 / 엔들리스(심연) 모드
        self._credits_scroll  = 0.0

        # 층 전환 페이드
        self._fade_alpha    = 0
        self._fade_dir      = 0   # 1=fade to black, -1=fade from black
        self._fade_speed    = 12
        self._fade_callback = None

        # 이동 슬라이딩 애니메이션 (지수 감쇠)
        self._move_anim_offset = [0.0, 0.0]

        # 공격 스프라이트 애니메이션
        # phase: 0=idle, 1=ready(백스윙), 2=strike(전진)
        self._atk_phase = 0
        self._atk_timer = 0

        # 공격 쿨다운 타이머 (ms) — 0 이하일 때만 공격 가능
        self._atk_cd_timer: float = 0.0

        # 액션 콤보 전투 상태
        self._atk_variant:     str   = 'slash1'  # 현재 공격 포즈 변형
        self._chain_step:      int   = 0         # 3단 콤보 단계 (0/1/2)
        self._chain_window_ms: float = 0.0       # 체인 유지 잔여 시간
        self._cancel_bonus_ms: float = 0.0       # 드라이브 캔슬 데미지 보너스 창
        self._white_flash_ms:  float = 0.0       # 피니셔 임팩트 프레임

        # 스태미나 SP: 마지막 소모 후 지연을 두고 회복 (남발 억제)
        self._stamina_delay_ms: float = 0.0      # 회복 시작까지 대기
        self._last_exhaust_msg: int   = -9999    # 탈진 메시지 쿨다운

        # ── 마을 시스템 (GameManager 역할: 던전 세션 통째 보존) ──────
        from core.town import TownScene
        from core.save_load import load_storage
        self._in_town          = False
        self._town: TownScene | None = None      # lazy 생성
        self._dungeon_session  = None            # {'dungeon','floor','px','py',...}
        self._storage, self._storage_cap = load_storage()  # 영구 창고 + 용량
        self._storage_cursor   = 0               # 창고 UI 커서
        self._storage_pane     = 0               # 0=소지품  1=창고
        self._enhance_mode     = 'stone'         # 'stone'(P키) | 'gold'(대장장이)

        # ── 퀘스트 (시민 의뢰) — 런 단위, 세이브에 포함 ──────────────
        from core.quests import fresh_states
        self._quests: dict = fresh_states()
        self._dialog: dict | None = None         # 하단 대화창 상태
        self._max_floor_reached: int = 1         # 시민 등장·개방 판정용
        self._quest_clear_ms:   float = 0.0      # 클리어 연출 오버레이 타이머
        self._quest_clear_name: str   = ''
        self._quest_clear_font        = None     # lazy

        # 히트스톱 (타격 순간 게임 월드 잠깐 정지) / 피격 비네트
        self._hitstop_ms: float = 0.0
        self._hurt_flash_ms: float = 0.0

        # 처치 연쇄 (4초 윈도우)
        self._combo_count: int = 0
        self._combo_ms: float = 0.0
        self._combo_font = None  # 첫 렌더 시 lazy 생성

        # 펀치 줌 (크리티컬·보스킬 순간 화면 확대 임팩트)
        self._punch_zoom_ms:  float = 0.0
        self._punch_zoom_max: float = 1.0
        self._punch_zoom_amt: float = 0.0

        # 레벨업 골든 플래시
        self._gold_flash_ms: float = 0.0

        # 슬로모션 (보스 막타·층 클리어·잭팟) — world_dt에 배율 적용
        self._slowmo_ms:     float = 0.0
        self._slowmo_factor: float = 1.0

        # 오버킬 콜아웃 쿨다운 (배너 스팸 방지)
        self._last_overkill_t: int = -99999

        # 인벤토리 / 장비 화면 선택 인덱스
        self._inv_sel   = 0
        self._inv_cat   = 0   # 카테고리 탭: 0 전체 · 1 장비 · 2 소모품 · 3 채집품
        self._equip_sel = 0

        # 인벤토리 드래그 상태
        self._inv_drag_idx   = None   # 드래그 중인 슬롯 인덱스
        self._inv_drag_pos   = (0, 0) # 현재 마우스 위치
        self._inv_drag_start = (0, 0) # 드래그 시작 위치

        # 버리기 확인 대화상자
        self._inv_confirm_idx = None  # 버리기 확인 대기 중인 슬롯 인덱스

        # 장비 강화 창
        self._enhance_open   = False
        self._enhance_cursor = 0     # 선택 슬롯 인덱스 (0~5)
        self._enhance_result = None  # ('success'/'fail', time_ms, cursor_idx)

        # 몬스터 리스폰
        self._respawn_max      = 0      # 이 층의 일반 몬스터 최대 수
        self._respawn_timer_ms = 0      # 다음 리스폰까지 남은 시간
        self._RESPAWN_INTERVAL = 10000  # 리스폰 주기 (ms)

        # 스킬 레벨 / XP (skill_id 키)
        self._skill_levels: dict[str, int] = {sid: 1 for sid in ALL_SKILL_DEFS}
        self._skill_xp:     dict[str, int] = {sid: 0 for sid in ALL_SKILL_DEFS}
        self._skill_points: int = 0
        self._equipped_skills: dict[str, str] = DEFAULT_EQUIPPED.copy()

        # 스킬 인챈트 (power/haste/efficiency/arcane 레벨)
        self._skill_enchants: dict[str, dict] = {
            sid: {'power': 0, 'haste': 0, 'efficiency': 0, 'arcane': 0}
            for sid in ALL_SKILL_DEFS
        }
        self._enchant_dmg_mul: float = 1.0   # _use_skill 중 임시 적용

        # 오의 시스템
        self._arcane_window_ms:  int      = 0     # R키 오의 발동 가능 창
        self._arcane_last_skill: str|None = None  # 직전 사용 스킬 id

        # 스킬 도감 (K키)
        self._skillbook_open:           bool     = False
        self._skillbook_cursor:         int      = 0
        self._skillbook_equip_mode:     bool     = False
        self._skillbook_target_slot:    str|None = None   # pick_skill 모드: 변경할 슬롯
        self._skillbook_equip_skill_id: str|None = None   # pick_slot 모드: 장착할 스킬
        self._skillbook_equip_cursor:   int      = 0


        # 조합 스킬 해금 상태
        self._unlocked_combos: set = set()
        self._skill_books: set     = set()   # 스킬북 소지 여부 (레벨 달성 전)

        # 강화술 버프 상태
        self._fortify_effect: SkillEffect | None = None
        self._fortify_def_bonus: int   = 0
        self._fortify_atk_bonus: float = 0.0

        # 버닝 스테이지 상태
        self._burning_active      = False
        self._burning_timer_ms    = 0        # 남은 생존 시간
        self._burning_spawn_timer = 0        # 다음 파도까지 대기
        self._burning_wave        = 0        # 현재 파도 번호
        self._burning_floor       = 1        # 복귀용 원래 층
        self._burning_warned_10s  = False

        # 버닝 HUD 폰트 캐시 (매 프레임 생성 방지, 언어별 폰트)
        from core.fonts import load_font as _lf
        self._font_burning_big   = _lf(28, bold=True)
        self._font_burning_small = _lf(13)
        # 화염 테두리용 재사용 Surface
        self._edge_surf = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)

        # 일시정지
        self._pause_sel = 0

        # 기록 / 정복 일지 / 마스터 정산
        self._run_kills = 0
        self._records   = load_records()
        self._gold_mult = ng_plus_gold_mult(self._records)   # NG+ 영구 골드 배율
        self._title_badge = bool(self._records.get('active_title'))  # 칭호 뱃지 이펙트
        self._journal_return_state = 'playing'
        # 멀티플레이 스텁 (미래용 · 현재 비동작)
        self._net = NetworkManager()

        # 테스트 모드
        self._is_test_mode = False
        self._test_floor: int | None = None  # main.py 에서 세팅, 메뉴 버튼으로 진입

        # 세이브 슬롯(캐릭터 카드) — 레거시 세이브 1회 이관
        migrate_legacy_save()
        self._save_slot         = 1
        self._cards             = list_cards()
        self._save_data         = load_game(self._save_slot)
        self._menu_sel          = 0
        self._menu_page         = 'main'
        self._menu_settings_sel = 0
        self._menu_buttons      = []
        # 캐릭터 생성 화면 상태
        self._create_class      = 'warrior'   # 'warrior' | 'archer'
        self._create_name       = ''
        self._create_slot       = 1
        self._create_skin       = 0
        self._create_hair       = 0
        self._create_haircol    = 0
        # sel: 0=class 1=skin 2=hair 3=haircol 4=name 5=create
        self._create_sel        = 0
        self._CREATE_ROWS       = 6
        # 궁수 발사 연출
        self._shoot_ms          = 0.0
        self.state  = 'menu'
        self.player  = None
        self._pet    = None          # 활성 Pet 객체 (런타임)
        self._pet_sel = 0            # 펫 상태창 커서
        self._pet_trail = []         # 플레이어 경로(타일) — 펫이 밟고 따라감
        self._farm_menu_plot = None  # 농사 팝업 대상 밭칸
        self._farm_menu_idx = 0      # 농사 팝업 커서
        self._altar_idx = 0          # 고대 제단 메뉴 커서
        self._angler_idx = 0         # 낚시 노인 교환 메뉴 커서
        self._fish = None            # 낚시 미니게임 상태
        self._ranch_menu_pen = None  # 목장 팝업 대상 우리
        self._ranch_menu_idx = 0     # 목장 팝업 커서
        self.dungeon = None
        self.camera  = None

        # 멀티플레이 세션 (None=싱글). P1: 마을 co-op(대칭 상태 브로드캐스트).
        self.net = None
        # 메뉴 → co-op 시작 흐름 상태
        self._pending_net    = None   # (role, transport) — 캐릭터 선택 후 부착 대기
        self._mp_ip          = '127.0.0.1'
        self._mp_status      = None   # 멀티 페이지 상태 문구(연결 중/실패)
        self._mp_connecting  = False
        self._mp_connect_result = None  # ('ok', tp) | ('err', msg) — 스레드가 채움
        self._mp_mode_banner = None   # 메인 카드 화면 배너: 'host' | 'join'
        # 던전 co-op (P3)
        self._coop_dungeon = False    # co-op 던전 탐험 중
        self._coop_seed    = None     # 현재 co-op 층 생성 시드(결정론적 공유)
        self._coop_diff    = None     # 난이도 배수 {'hp','atk'} — 싱글보다 강함
        # 마을 co-op 채팅
        self._chat_open    = False
        self._chat_text    = ''
        self._chat_seen    = 0        # net.chat_log 소비 인덱스
        self._chat_bubbles = {}       # pid → {'text','ms'} 머리 위 말풍선
        self._chat_feed    = []       # [[name, text, ms]] 하단 최근 로그

    # ─────────────── 멀티플레이 (P1: 마을 co-op) ──────────────────────
    def _net_local_state(self):
        """내 플레이어의 네트워크 상태 dict — Session provider로 사용."""
        from net import protocol as P
        p = self.player
        if p is None:
            return None
        pid = self.net.tp.local_id() if self.net is not None else 0
        return P.player_state(
            pid, p.x, p.y, self._facing, self._walk_frame,
            p.char_class, getattr(p, 'char_name', 'Hero'),
            getattr(p, 'appearance', None), p.hp, p.max_hp,
            floor=int(self.floor))

    def start_net_session(self, transport, mode='town'):
        """전송 계층을 받아 멀티플레이 세션을 시작한다.

        transport는 LoopbackTransport(테스트) 또는 SteamTransport(프로덕션).
        인터페이스가 같으므로 게임 코드는 어느 쪽이든 동일하게 동작한다.
        """
        from net import Session
        p = self.player
        self.net = Session(
            transport,
            char_class=(p.char_class if p else 'warrior'),
            name=(getattr(p, 'char_name', 'Hero') if p else 'Hero'),
            appearance=(getattr(p, 'appearance', None) if p else None),
            mode=mode,
            local_player_state=self._net_local_state,
            world_provider=self._net_world_state,       # 호스트: 밭·목장 상태
            apply_world=self._net_apply_world,          # 클라: 받은 월드 반영
            on_remote_action=self._net_apply_world_action,  # 호스트: 클라 액션 적용
            on_event=self._net_on_event,                # co-op 던전 입장 등
            world_interval=6,                           # 적 상태 ~10/s 브로드캐스트
        )
        self.net.start()
        return self.net

    # ── 던전 co-op (P3): 입장·난이도·시야 공유 ────────────────────────
    _COOP_HP_PER  = 0.6    # 인원 +1마다 적 체력 배수 가산
    _COOP_ATK_PER = 0.3    # 인원 +1마다 적 공격력 배수 가산
    _COOP_BOSS_HP  = 1.5   # 보스는 추가로 더 단단하게(멀티에서 더 어렵게)
    _COOP_BOSS_ATK = 1.25  # 보스는 추가로 더 아프게

    def _net_on_event(self, from_id, kind, data):
        if kind == 'coop_enter':
            # 호스트가 co-op 던전 입장을 알림 — 같은 시드/층/난이도로 생성
            self._coop_start(int(data.get('floor', 1)),
                             int(data.get('seed', 0)),
                             data.get('diff') or None)

    def _coop_party_size(self):
        return 1 + (len(self.net.remote_players) if self.net else 0)

    def _coop_begin_dungeon(self):
        """호스트: 파티 최저 층 + 공유 시드 + 난이도로 co-op 던전 시작."""
        import random as _r
        floors = [int(self.floor)]
        for rp in self.net.remote_players.values():
            if rp.floor:
                floors.append(int(rp.floor))
        target = max(1, min(floors))
        seed = _r.randrange(1, 2 ** 31)
        n = self._coop_party_size()
        diff = {'hp': round(1 + self._COOP_HP_PER * (n - 1), 2),
                'atk': round(1 + self._COOP_ATK_PER * (n - 1), 2)}
        self.net.send_event('coop_enter', {'floor': target, 'seed': seed, 'diff': diff})
        self._coop_start(target, seed, diff)

    def _coop_start(self, floor, seed, diff):
        """양쪽 공통: co-op 던전 상태 설정 후 결정론적으로 층 생성."""
        self._coop_dungeon = True
        self._coop_seed    = seed
        self._coop_diff    = diff
        self.floor         = floor
        self._in_town      = False
        self._saved_camera = None
        self.messages.append((t('coop_enter_msg', floor), 'good'))
        self._load_floor()

    def _apply_coop_difficulty(self, dungeon):
        """co-op 난이도: 적 체력·공격력을 배수로 강화 (싱글보다 어렵게)."""
        d = self._coop_diff
        if not d:
            return
        hp_m = float(d.get('hp', 1.0))
        atk_m = float(d.get('atk', 1.0))
        for e in dungeon.enemies:
            mh, ma = hp_m, atk_m
            if getattr(e, 'is_boss', False):   # 보스는 추가 배수로 더 강하게
                mh *= self._COOP_BOSS_HP
                ma *= self._COOP_BOSS_ATK
            e.max_hp = max(1, int(round(e.max_hp * mh)))
            e.hp     = e.max_hp
            e.attack = max(1, int(round(e.attack * ma)))

    def _coop_reveal(self):
        """시야 공유: 원격 파티원 위치 주변도 밝힌다(미니맵 포함)."""
        if (self.net is None or self._is_test_mode or self._in_town
                or self.dungeon is None):
            return
        for rp in self.net.remote_players.values():
            if self.dungeon.in_bounds(rp.x, rp.y):
                self.dungeon.update_visibility(rp.x, rp.y)

    # ── 공유 월드(밭 등) 동기화 훅 ────────────────────────────────────
    def _coop_is_client(self):
        return (self.net is not None and not self.net.is_host
                and self._coop_dungeon and not self._in_town)

    def _net_world_state(self):
        """호스트: 현재 공유 월드 상태 dict. 마을=밭/목장, co-op던전=적 상태."""
        if self._in_town and self._town is not None:
            return {'farm': self._town.farm, 'ranch': self._town.ranch}
        if self._coop_dungeon and self.dungeon is not None:
            # 적 상태(권위): [net_id, x, y, hp] — 살아있는 적만
            en = [[e.net_id, e.x, e.y, e.hp]
                  for e in self.dungeon.enemies
                  if getattr(e, 'net_id', None) is not None and e.is_alive()]
            return {'en': en}
        return None

    def _net_apply_world(self, state):
        """클라: 호스트가 보낸 공유 월드 상태를 반영(렌더용, 권위는 호스트)."""
        farm = state.get('farm')
        if isinstance(farm, list) and self._town is not None:
            self._town.farm = farm
        ranch = state.get('ranch')
        if isinstance(ranch, list) and self._town is not None:
            self._town.ranch = ranch
        en = state.get('en')
        if en is not None and self.dungeon is not None:
            self._net_apply_enemies(en)

    def _wrap_client_enemy_damage(self, enemy):
        """클라 전용: 적 take_damage를 가로채 로컬 HP를 바꾸지 않고 호스트에
        피해 인텐트만 보낸다. 모든 공격 경로가 자동으로 인텐트를 태운다."""
        nid = getattr(enemy, 'net_id', None)
        net = self.net

        def _td(amount):
            if net is not None and nid is not None and amount and amount > 0:
                net.send_world_action({'kind': 'dmg', 'id': nid, 'dmg': int(amount)})
            # HP는 호스트 스냅샷이 권위 — 로컬에서 변경하지 않음
        enemy.take_damage = _td

    def _net_apply_dmg(self, action):
        """호스트: 클라가 보낸 피해를 권위 적용(사망 시 처치 처리·전리품)."""
        if self.dungeon is None:
            return
        nid = action.get('id')
        dmg = int(action.get('dmg', 0))
        if dmg <= 0:
            return
        e = next((x for x in self.dungeon.enemies
                  if getattr(x, 'net_id', None) == nid), None)
        if e is not None and e.is_alive():
            self._hurt_enemy(e, dmg)   # 호스트 권위: 피해+사망 라우팅

    def _net_apply_enemies(self, en):
        """클라: 호스트 권위 적 상태를 로컬 적에 반영. 없는 적은 처치된 것으로 제거."""
        by_id = {e.net_id: e for e in self.dungeon.enemies
                 if getattr(e, 'net_id', None) is not None}
        seen = set()
        for nid, x, y, hp in en:
            seen.add(nid)
            e = by_id.get(nid)
            if e is None:
                continue
            e.x, e.y = x, y          # 위치 스냅(그리드) — 부드러움은 추후
            e.anim_ox = e.anim_oy = 0
            e.hp = hp
        # 스냅샷에 없는(=호스트에서 죽은) 적 제거 + 사망 연출
        for e in list(self.dungeon.enemies):
            nid = getattr(e, 'net_id', None)
            if nid is not None and nid not in seen and e.is_alive():
                self.animator.particles.emit_death(e.x, e.y, e.color)
                if e in self.dungeon.enemies:
                    self.dungeon.enemies.remove(e)

    def _net_apply_world_action(self, peer_id, action):
        """호스트: 클라의 월드 변경 액션 적용(밭/목장 상태, 또는 co-op 던전 피해)."""
        kind = action.get('kind')
        if kind == 'dmg':
            self._net_apply_dmg(action)   # co-op 던전(마을 아님)
            return
        if self._town is None:
            return
        if kind == 'farm':
            self._net_apply_farm(action)
        elif kind == 'ranch':
            self._net_apply_ranch(action)

    def _net_apply_farm(self, action):
        farm = self._town.farm
        idx = action.get('plot')
        if not isinstance(idx, int) or not (0 <= idx < len(farm)):
            return
        act = action.get('act')
        plot = farm[idx]
        if act == 'plant':
            from core.town import FARM_GROW_MAX
            plot['crop'] = action.get('crop')
            plot['watered'] = False
            plot['stage'] = FARM_GROW_MAX if self._is_test_mode else 0
        elif act == 'water':
            plot['watered'] = True
        elif act in ('harvest', 'uproot'):
            plot['crop'] = None
            plot['stage'] = 0
            plot['watered'] = False
        farm[idx] = plot
        self._records['farm'] = farm

    def _net_apply_ranch(self, action):
        ranch = self._town.ranch
        idx = action.get('pen')
        if not isinstance(idx, int) or not (0 <= idx < len(ranch)):
            return
        act = action.get('act')
        pen = ranch[idx]
        if act == 'buy':
            from core.town import RANCH_FEED_MAX
            pen['animal'] = action.get('animal')
            pen['fed'] = False
            pen['stage'] = RANCH_FEED_MAX if self._is_test_mode else 0
        elif act == 'feed':
            from core.town import RANCH_FEED_MAX
            pen['fed'] = True
            if self._is_test_mode:
                pen['stage'] = RANCH_FEED_MAX
        elif act == 'collect':
            pen['fed'] = False
            pen['stage'] = 0          # 가축은 남고 재생산 위해 먹이 필요
        elif act == 'sell':
            pen['animal'] = None
            pen['fed'] = False
            pen['stage'] = 0
        ranch[idx] = pen
        self._records['ranch'] = ranch

    # ── 마을 co-op 채팅 ───────────────────────────────────────────────
    _CHAT_BUBBLE_MS = 4500
    _CHAT_FEED_MS   = 6500

    def _handle_chat_key(self, key, uni):
        if key == pygame.K_RETURN:
            text = self._chat_text.strip()
            if text and self.net is not None:
                self.net.send_chat(text[:80])
            self._chat_open = False
            self._chat_text = ''
        elif key == pygame.K_ESCAPE:
            self._chat_open = False
            self._chat_text = ''
        elif key == pygame.K_BACKSPACE:
            self._chat_text = self._chat_text[:-1]
        elif uni and uni.isprintable() and len(self._chat_text) < 80:
            self._chat_text += uni

    def _pump_chat(self):
        """net.chat_log의 새 메시지를 말풍선 + 하단 피드로 반영."""
        if self.net is None:
            return
        log = self.net.chat_log
        while self._chat_seen < len(log):
            sender_id, text = log[self._chat_seen]
            self._chat_seen += 1
            name = self._chat_sender_name(sender_id)
            self._chat_bubbles[sender_id] = {'text': text, 'ms': self._CHAT_BUBBLE_MS}
            self._chat_feed.append([name, text, self._CHAT_FEED_MS])
        if len(self._chat_feed) > 5:
            self._chat_feed = self._chat_feed[-5:]

    def _chat_sender_name(self, sender_id):
        if self.net is not None and sender_id == self.net.tp.local_id():
            return getattr(self.player, 'char_name', '나')
        rp = self.net.remote_players.get(sender_id) if self.net else None
        return rp.char_name if rp is not None else '?'

    def _update_chat_timers(self, dt):
        for pid in list(self._chat_bubbles):
            self._chat_bubbles[pid]['ms'] -= dt
            if self._chat_bubbles[pid]['ms'] <= 0:
                del self._chat_bubbles[pid]
        for row in self._chat_feed:
            row[2] -= dt
        self._chat_feed = [r for r in self._chat_feed if r[2] > 0]

    def _draw_chat_bubbles(self, cx, cy, my_px, my_py):
        """머리 위 말풍선 — 내 플레이어(my_px,my_py) + 원격 플레이어."""
        if not self._chat_bubbles or self.net is None:
            return
        me = self.net.tp.local_id()
        for pid, b in self._chat_bubbles.items():
            if pid == me:
                ax, ay = my_px, my_py
            else:
                rp = self.net.remote_players.get(pid)
                if rp is None:
                    continue
                ax = int(round(rp.render_px - cx * TILE_SIZE))
                ay = int(round(rp.render_py - cy * TILE_SIZE))
            self._draw_bubble(ax + TILE_SIZE // 2, ay - 8, b['text'], b['ms'])

    def _draw_bubble(self, cx_px, top_y, text, ms):
        font = self.hud.font_sm
        surf = font.render(text, True, (30, 30, 40))
        pad = 6
        w = surf.get_width() + pad * 2
        h = surf.get_height() + pad
        alpha = 255 if ms > 700 else max(0, int(255 * ms / 700))
        bx = cx_px - w // 2
        by = top_y - h - 4
        bub = pygame.Surface((w, h + 5), pygame.SRCALPHA)
        pygame.draw.rect(bub, (245, 245, 250, alpha), (0, 0, w, h), border_radius=6)
        pygame.draw.polygon(bub, (245, 245, 250, alpha),
                            [(w // 2 - 5, h - 1), (w // 2 + 5, h - 1), (w // 2, h + 4)])
        surf.set_alpha(alpha)
        bub.blit(surf, (pad, pad // 2))
        self._game_surf.blit(bub, (bx, by))

    def _draw_chat_overlay(self):
        """하단 최근 채팅 피드 + (입력 중) 입력줄. self.screen에 직접 그린다."""
        if self.net is None or not (self._in_town or self._coop_dungeon):
            return
        font = self.hud.font_sm
        base_y = GAME_Y + GAME_H - 24
        # 최근 피드 (입력줄 위로 쌓기)
        y = base_y - (28 if self._chat_open else 0)
        for name, text, ms in reversed(self._chat_feed):
            a = 255 if ms > 900 else max(0, int(255 * ms / 900))
            line = font.render(f"{name}: {text}", True, (225, 230, 245))
            line.set_alpha(a)
            shadow = font.render(f"{name}: {text}", True, (0, 0, 0))
            shadow.set_alpha(a)
            self.screen.blit(shadow, (GAME_X + 13, y + 1))
            self.screen.blit(line, (GAME_X + 12, y))
            y -= 20
        # 입력줄
        if self._chat_open:
            bar = pygame.Surface((GAME_W, 26), pygame.SRCALPHA)
            bar.fill((10, 12, 24, 210))
            self.screen.blit(bar, (GAME_X, base_y - 2))
            caret = '_' if (pygame.time.get_ticks() // 400) % 2 == 0 else ' '
            prompt = font.render(f"{t('chat_prompt')}: {self._chat_text}{caret}",
                                 True, (200, 224, 255))
            self.screen.blit(prompt, (GAME_X + 12, base_y + 3))
        elif not self._chat_feed:
            hint = font.render(t('chat_hint'), True, (120, 130, 155))
            self.screen.blit(hint, (GAME_X + 12, base_y + 3))

    def stop_net_session(self):
        if self.net is not None:
            try:
                self.net.tp.close()
            except Exception:
                pass
            self.net = None

    # ------------------------------------------------------------------ #
    @staticmethod
    def _scale_fit(surf: pygame.Surface, size: int) -> pygame.Surface:
        """종횡비를 유지하며 size×size 캔버스에 letterbox 배치."""
        sw, sh = surf.get_size()
        ratio  = min(size / sw, size / sh)
        nw, nh = max(1, int(sw * ratio)), max(1, int(sh * ratio))
        scaled  = pygame.transform.scale(surf, (nw, nh))
        canvas  = pygame.Surface((size, size), pygame.SRCALPHA)
        canvas.blit(scaled, ((size - nw) // 2, (size - nh) // 2))
        return canvas

    def _load_sprites(self):
        """assets/sprites/*.png 로드. 없으면 빈 딕셔너리."""
        self._sprites: dict[str, pygame.Surface] = {}
        _root   = sys._MEIPASS if (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')) \
                  else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
        spr_dir = os.path.join(_root, 'assets', 'sprites')

        # 종횡비 유지 letterbox: 영웅 + 공격 스프라이트
        fit_names = [
            'hero', 'hero_right', 'hero_left', 'hero_down',
            'hero_up', 'hero_back', 'hero_hurt',
            'hero_attack_ready_left',  'hero_attack_end_left',
            'hero_attack_ready_right', 'hero_attack_end_right',
            'hero_attack_ready_up',    'hero_attack_end_up',
            'hero_attack_ready_down',  'hero_attack_end_down',
        ]
        for name in fit_names:
            path = os.path.join(spr_dir, f'{name}.png')
            if os.path.exists(path):
                try:
                    surf = pygame.image.load(path).convert_alpha()
                    self._sprites[name] = self._scale_fit(surf, TILE_SIZE)
                except Exception:
                    pass

        # 적 스프라이트: 단순 스케일
        enemy_names = [
            'enemy_rat', 'enemy_goblin', 'enemy_skeleton',
            'enemy_orc', 'enemy_troll',
            'boss_dark_knight', 'boss_lich',
        ]
        for name in enemy_names:
            path = os.path.join(spr_dir, f'{name}.png')
            if os.path.exists(path):
                try:
                    surf = pygame.image.load(path).convert_alpha()
                    self._sprites[name] = pygame.transform.scale(surf, (TILE_SIZE, TILE_SIZE))
                except Exception:
                    pass

    # ── 적 key → 스프라이트 key 매핑 ─────────────────────────────────
    _ENEMY_SPRITE_KEY = {
        'rat':         'enemy_rat',
        'goblin':      'enemy_goblin',
        'skeleton':    'enemy_skeleton',
        'orc':         'enemy_orc',
        'troll':       'enemy_troll',
        'dark_knight': 'boss_dark_knight',
        'lich':        'boss_lich',
    }

    # ------------------------------------------------------------------ #
    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            # 히트스톱: 타격 순간 월드(애니메이션·적)만 잠깐 정지
            if self._hitstop_ms > 0:
                self._hitstop_ms = max(0.0, self._hitstop_ms - dt)
                world_dt = 0
            elif self._slowmo_ms > 0:
                # 슬로모션: 월드만 느려지고 입력·연출 타이머는 실시간
                self._slowmo_ms = max(0.0, self._slowmo_ms - dt)
                world_dt = dt * self._slowmo_factor
            else:
                world_dt = dt
            if self._hurt_flash_ms > 0:
                self._hurt_flash_ms = max(0.0, self._hurt_flash_ms - dt)
            if self._punch_zoom_ms > 0:
                self._punch_zoom_ms = max(0.0, self._punch_zoom_ms - dt)
            if self._gold_flash_ms > 0:
                self._gold_flash_ms = max(0.0, self._gold_flash_ms - dt)
            if self._white_flash_ms > 0:
                self._white_flash_ms = max(0.0, self._white_flash_ms - dt)
            if self._quest_clear_ms > 0:
                self._quest_clear_ms = max(0.0, self._quest_clear_ms - dt)
            if self._cancel_bonus_ms > 0:
                self._cancel_bonus_ms = max(0.0, self._cancel_bonus_ms - dt)
            if self._chain_window_ms > 0:
                self._chain_window_ms = max(0.0, self._chain_window_ms - dt)
                if self._chain_window_ms == 0:
                    self._chain_step = 0
            # 드라이브 게이지 회복 (1칸 / 2.5초)
            if self.state == 'playing' and self.player:
                self.player.drive = min(self.player.drive_max,
                                        self.player.drive + dt * 0.0004)
                # 스태미나: 마지막 소모 후 0.9초 지나면 초당 22 회복
                if self._stamina_delay_ms > 0:
                    self._stamina_delay_ms = max(0.0, self._stamina_delay_ms - dt)
                else:
                    self.player.stamina = min(self.player.stamina_max,
                                              self.player.stamina + dt * 0.022)
            self._update_fade(dt)
            self._update_shake(dt)
            if self.camera:
                self.camera.update(dt)          # 동적 지진(카메라 노이즈)
            if self.state == 'credits':
                self._update_credits(dt)
            self._update_move_anim(dt)
            if not self._is_fading:
                self._handle_events(dt)
            self.animator.update(world_dt)
            if self.state == 'playing' and self.player:
                self.vfx_loot.update(world_dt, self)   # 히트스톱 시 함께 정지
            self._update_atk_anim(dt)
            # 공격 쿨다운 감소
            if self._atk_cd_timer > 0:
                self._atk_cd_timer = max(0.0, self._atk_cd_timer - dt)
            # 플레이어 이동속도 → InputHandler 동기화
            if self.player:
                self.input.set_move_speed(self.player.total_move_speed)
            if self.state == 'playing':
                self.skills.update(dt)
                self._update_fortify(dt)
                if self._arcane_window_ms > 0:
                    self._arcane_window_ms = max(0, self._arcane_window_ms - dt)
                    if self._arcane_window_ms == 0:
                        self._arcane_last_skill = None
                if self._burning_active:
                    self._update_burning(dt)
            if self.state == 'playing':
                if self.player:
                    self.player.tick_debuffs(dt)
                    if self.player.char_class == 'archer':
                        self._update_auto_volley(world_dt)
                    if self._pet:                       # 펫: 경로 갱신 → 추종 + 능력
                        self._update_pet_trail()
                        self._pet.update(world_dt, self)
                    if not self._in_town:
                        self._update_conveyor(world_dt)
                        self._update_hazards(world_dt)
                    # 방어구 파손 경고 소비 (Player.take_damage가 기록)
                    for _broken in self.player.just_broken:
                        self.messages.append((t('armor_broken', _broken.name), 'bad'))
                        self.animator.add(CalloutAnim(self.player.x, self.player.y,
                                                      '!', (255, 90, 60)))
                        self.audio.play('break')
                        self._start_shake(4, 220)
                    self.player.just_broken.clear()
                if self._combo_ms > 0:
                    self._combo_ms = max(0.0, self._combo_ms - world_dt)
                    if self._combo_ms == 0:
                        self._combo_count = 0
                self._update_enemies(world_dt)
                if self._axe_throw_cd_ms > 0:
                    self._axe_throw_cd_ms = max(0, self._axe_throw_cd_ms - world_dt)
                if self._ragnarok_ms > 0:
                    self._ragnarok_ms = max(0, self._ragnarok_ms - world_dt)
                    if not self._in_town:
                        self._update_ragnarok_aura(world_dt)
                if not self._in_town:
                    self._update_dots(world_dt)      # 점화 DoT + 화염 장판
                    self._update_summons(world_dt)   # 소환수
                    self._update_bombs(world_dt)     # 투척 폭탄
                    self._update_collapse(world_dt)  # 붕괴 추격
                if self._in_town and self._town:
                    self._town.update(dt, self.player.x, self.player.y)
                # 멀티플레이: 마을·co-op던전에서 상태 브로드캐스트 + 원격 동기화
                if self.net is not None and (self._in_town or self._coop_dungeon):
                    self.net.tick(dt)
                    self._pump_chat()
                    self._update_chat_timers(dt)
                    if self._coop_dungeon and not self._in_town:
                        self._coop_reveal()   # 시야 공유(원격 파티원 주변)
                    if os.environ.get('DD_MP_DEBUG'):
                        self._mp_dbg = getattr(self, '_mp_dbg', 0) + 1
                        if self._mp_dbg % 60 == 0:
                            print(f"[MP] REMOTES={len(self.net.remote_players)} "
                                  f"peers={self.net.tp.peers()}", flush=True)
            elif self.state == 'fishing':
                self._update_fishing(dt)
            if self._mp_connecting:
                self._mp_poll_connect()
            self._update_bgm()
            self._render()

    # ─────────────── 화면 흔들림 ──────────────────────────────────────
    def _start_shake(self, intensity=4, duration_ms=250):
        self._shake_intensity = intensity
        self._shake_timer     = duration_ms
        self._shake_max       = duration_ms

    # ─────────────── 펀치 줌 (임팩트 순간 화면 확대) ──────────────────
    def _start_punch_zoom(self, amount=0.045, duration_ms=110):
        if duration_ms > self._punch_zoom_ms:
            self._punch_zoom_ms  = duration_ms
            self._punch_zoom_max = duration_ms
            self._punch_zoom_amt = amount

    # ─────────────── 처치 연쇄 티어 ──────────────────────────────────
    # (진입 콤보 수, 콜아웃, 색상) — 내림차순
    _COMBO_TIERS = (
        (20, 'GODLIKE!!',    (255, 105, 255)),
        (15, 'UNSTOPPABLE!', (195,  80, 255)),
        (10, 'DOMINATING!',  (255,  70,  60)),
        (5,  'RAMPAGE!',     (255, 150,  35)),
    )

    @classmethod
    def _combo_tier(cls, n):
        for th, name, color in cls._COMBO_TIERS:
            if n >= th:
                return (th, name, color)
        return None

    def _update_shake(self, dt):
        self._shake_timer = max(0, self._shake_timer - dt)

    _ATK_READY_MS  = 90    # 백스윙 유지 시간
    _ATK_STRIKE_MS = 140   # 전진 타격 유지 시간

    def _update_atk_anim(self, dt):
        if self._atk_timer <= 0:
            return
        self._atk_timer -= dt
        if self._atk_timer <= 0:
            if self._atk_phase == 1:
                self._atk_phase = 2
                self._atk_timer = self._ATK_STRIKE_MS
            else:
                self._atk_phase = 0

    def _trigger_atk_anim(self):
        self._atk_phase = 1
        self._atk_timer = self._ATK_READY_MS

    def _update_move_anim(self, dt):
        if self._move_anim_offset[0] == 0.0 and self._move_anim_offset[1] == 0.0:
            return
        # 0.975: 연속 이동 간격(220ms) 안에 잔여 오프셋이 거의 소멸 —
        # 이동이 끌리는 느낌 없이 또렷하게 끊긴다
        factor = 0.975 ** dt
        self._move_anim_offset[0] *= factor
        self._move_anim_offset[1] *= factor
        if abs(self._move_anim_offset[0]) < 0.5:
            self._move_anim_offset[0] = 0.0
        if abs(self._move_anim_offset[1]) < 0.5:
            self._move_anim_offset[1] = 0.0

    @property
    def _shake_offset(self):
        if self._shake_timer <= 0:
            return (0, 0)
        mag = max(0, int(self._shake_intensity * self._shake_timer / self._shake_max))
        return (random.randint(-mag, mag), random.randint(-mag, mag)) if mag > 0 else (0, 0)

    # ─────────────── 동적 맵 이펙터 ──────────────────────────────────
    def _apply_map_fx(self):
        """현재 층 테마의 동적 이펙트를 카메라/렌더러에 설정."""
        fx = {} if self._in_town else theme_fx(self.floor)
        quake = fx.get('quake', 0.0)
        if self.camera:
            self.camera.set_ambient_shake(quake)
            if quake > 0:                       # 층 진입 순간 강한 여진
                self.camera.trigger_earthquake(quake * 4, 900)
        self._distort_amp = fx.get('distort', 0.0)
        self._conveyor_t = 0.0
        # 이 층의 이동벽·주기 가시 수집
        self._shift_walls = []
        self._spikes = []
        self._shift_t = 0.0
        self._shift_open_ms = 0.0
        self._dot_zones = []            # 층 이동 시 장판/소환수/폭탄 소멸
        self._summons = []
        self._bombs = []
        self._secret_found = False      # 이 층 비밀방 발견 연출 1회 플래그
        self._collapse_active = False   # 층 이동 시 붕괴 상태 해제
        self._collapse_t = 0.0
        self._crumble = {}
        self._collapse_reward = None    # 탈출 못하면 제단 보상은 소멸
        self._keys = 0                  # 열쇠는 층 단위(다음 층에서 초기화)
        self._thrown_axe = None         # 던져진 도끼는 층 이동 시 회수(소멸)
        self._axe_throw_cd_ms = 0
        self._ragnarok_ms = 0
        if not self._in_town and self.dungeon:
            for yy, row in enumerate(self.dungeon.tiles):
                for xx, tl in enumerate(row):
                    if tl.tile_type == TileType.SHIFT_WALL:
                        self._shift_walls.append({'x': xx, 'y': yy, 'phase': tl.phase})
                    elif tl.tile_type == TileType.SPIKE_TRAP:
                        self._spikes.append({'x': xx, 'y': yy, 'phase': tl.phase,
                                             'armed': False})

    _CONVEYOR_PUSH_MS = 150     # 컨베이어 밀림 주기(ms) — 빠르고 강하게

    # 이동벽: 닫힘 시간이 길고(개방 40%) 경고가 짧아 타이밍이 빡빡하다
    _SHIFT_PERIOD_MS = 1900     # 개폐 한 주기(ms)
    _SHIFT_OPEN_FRAC = 0.40     # 주기 중 열려 있는 비율(나머지는 닫힘)
    _SHIFT_WARN_MS   = 300      # 닫히기 직전 경고(깜빡) 구간
    # 주기 가시: 골목에서 튀어나오는 타이밍 패턴
    _SPIKE_PERIOD_MS = 1500     # 발동 한 주기(ms)
    _SPIKE_HOT_FRAC  = 0.42     # 가시가 솟아 피해를 주는 비율
    _SPIKE_WARN_MS   = 300      # 솟기 직전 경고 구간

    def _update_conveyor(self, dt):
        """흐르는 바닥 위에 서 있으면 주기적으로 한 칸씩 밀린다."""
        p = self.player
        if not (p and self.dungeon.in_bounds(p.x, p.y)):
            self._conveyor_t = 0.0; return
        d = CONVEYOR_DIR.get(self.dungeon.tiles[p.y][p.x].tile_type)
        if d is None:
            self._conveyor_t = 0.0; return
        self._conveyor_t += dt
        if self._conveyor_t < self._CONVEYOR_PUSH_MS:
            return
        self._conveyor_t = 0.0
        nx, ny = p.x + d, p.y
        if self.dungeon.is_walkable(nx, ny) and not self.dungeon.get_enemy_at(nx, ny):
            self._move_anim_offset[0] = max(-TILE_SIZE, min(TILE_SIZE,
                self._move_anim_offset[0] - d * TILE_SIZE))
            p.x, p.y = nx, ny
            self.camera.center_on(p.x, p.y)
            if not self._is_test_mode and not self._collapse_active:
                self.dungeon.update_visibility(p.x, p.y)
            item = self.dungeon.get_item_at(nx, ny)
            if item:
                self._pickup(item)
            self._on_enter_tile(nx, ny)     # 컨베이어가 트랩·압력판으로 밀 수 있음

    # ─────────────── 동적 위험 (이동벽 + 주기 가시) ──────────────────
    def _update_hazards(self, dt):
        """이동벽 게이트 개폐 + 골목 주기 가시 발동. 실시간 맵 변화."""
        if not (self._shift_walls or self._spikes):
            return
        if self._shift_open_ms > 0:
            self._shift_open_ms = max(0.0, self._shift_open_ms - dt)
        self._shift_t += dt
        self._update_shift_walls()
        self._update_spikes()

    def _update_shift_walls(self):
        per = self._SHIFT_PERIOD_MS
        of  = self._SHIFT_OPEN_FRAC
        warn_frac = self._SHIFT_WARN_MS / per
        force_open = self._shift_open_ms > 0
        px, py = self.player.x, self.player.y
        for sw in self._shift_walls:
            x, y = sw['x'], sw['y']
            if not self.dungeon.in_bounds(x, y):
                continue
            tile = self.dungeon.tiles[y][x]
            local = (self._shift_t / per + sw['phase']) % 1.0
            want_open = force_open or (local < of)
            # 개방 구간이 곧 끝남 → 닫힘 경고(깜빡)
            tile.warn = (not force_open) and want_open and (of - local) < warn_frac
            if not want_open and not tile.blocked:
                if self.dungeon.get_enemy_at(x, y):   # 적 끼임 방지
                    continue
                if (px, py) == (x, y):
                    self._crush_player(x, y)
                tile.blocked = True
                tile.block_sight = True
            elif want_open and tile.blocked:
                tile.blocked = False
                tile.block_sight = False

    def _update_spikes(self):
        per = self._SPIKE_PERIOD_MS
        hf  = self._SPIKE_HOT_FRAC
        warn_frac = self._SPIKE_WARN_MS / per
        px, py = self.player.x, self.player.y
        for sp in self._spikes:
            x, y = sp['x'], sp['y']
            if not self.dungeon.in_bounds(x, y):
                continue
            tile = self.dungeon.tiles[y][x]
            local = (self._shift_t / per + sp['phase']) % 1.0
            hot = local < hf
            tile.hot = hot
            tile.warn = (not hot) and (1.0 - local) < warn_frac   # 솟기 직전
            if hot and (px, py) == (x, y) and not sp['armed']:
                self._spring_spike(x, y)
                sp['armed'] = True
            elif not hot:
                sp['armed'] = False

    def _spring_spike(self, x, y):
        p = self.player
        dmg = max(4, int(p.max_hp * 0.10))
        p.take_damage(dmg)
        self._hurt_flash_ms = 90
        self.animator.add(CalloutAnim(x, y, t('hazard_spike', dmg), (255, 90, 70)))
        self.animator.particles.emit_basic_hit(x, y)
        self._start_shake(5, 200)
        self.audio.play('hit')

    def _crush_player(self, x, y):
        """움직이는 벽이 플레이어를 덮침 — 피해 + 인접 빈칸으로 밀어냄."""
        p = self.player
        dmg = max(4, int(p.max_hp * 0.08))
        p.take_damage(dmg)
        self._hurt_flash_ms = 90
        self.animator.add(CalloutAnim(x, y, t('hazard_crush'), (230, 120, 90)))
        self.animator.particles.emit_death(x, y, (120, 130, 150))
        self._start_shake(6, 260)
        self.audio.play('hit')
        # 인접 빈칸으로 밀어내기
        for ox, oy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx, ny = x + ox, y + oy
            if self.dungeon.is_walkable(nx, ny) and not self.dungeon.get_enemy_at(nx, ny):
                p.x, p.y = nx, ny
                self.camera.center_on(p.x, p.y)
                break

    # ─────────────── 트랩 / 압력판 발동 ──────────────────────────────
    def _on_enter_tile(self, x, y):
        """플레이어가 한 칸에 진입할 때 트랩·압력판·비밀방 발견 처리."""
        if not self.dungeon.in_bounds(x, y):
            return
        # 숨겨진 보물방 최초 진입 연출 (1회)
        sr = getattr(self.dungeon, 'secret_room', None)
        if sr and (x, y) == sr and not getattr(self, '_secret_found', False):
            self._secret_found = True
            self.messages.append((t('secret_found'), 'good'))
            self.animator.add(BannerAnim(t('secret_found'), (235, 200, 90), size=24))
            self.animator.particles.emit_levelup(x, y)
            self.audio.play('levelup')
        tt = self.dungeon.tiles[y][x].tile_type
        # 가시는 주기형(_update_spikes에서 처리) — 여기선 방 트랩만
        if tt == TileType.WEB_TRAP:
            self.player.slowed_ms = max(self.player.slowed_ms, 2400)
            self.animator.add(CalloutAnim(x, y, t('hazard_web'), (220, 235, 245)))
            self.animator.particles.emit_basic_hit(x, y)
            self.audio.play('hit')
        elif tt == TileType.CURSE_TRAP:
            self.player.atk_down_ms = max(self.player.atk_down_ms, 4200)
            self.player.atk_down_pct = 0.30
            self.animator.add(CalloutAnim(x, y, t('hazard_curse'), (190, 120, 235)))
            self.animator.particles.emit_death(x, y, (150, 90, 210))
            self.audio.play('hit')
        elif tt == TileType.BUTTON:
            self._press_button(x, y)
        elif tt == TileType.ALTAR:
            self._trigger_altar(x, y)

    def _press_button(self, x, y):
        """압력판 — 보상(골드+전투 함성 버프) + 이동벽 전부 개방. 1회성."""
        p = self.player
        reward = int(120 * getattr(self, '_gold_mult', 1.0)) + self.floor
        p.gold += reward
        p.atk_bonus_pct = max(p.atk_bonus_pct, 0.30)
        p.atk_bonus_ms = max(p.atk_bonus_ms, 6000)
        self._shift_open_ms = 3600.0                 # 움직이는 벽 잠시 전부 개방
        self._gold_flash_ms = 200
        self.animator.add(BannerAnim(t('hazard_button'), (255, 210, 90), size=26))
        self.animator.particles.emit_levelup(x, y)
        self._start_punch_zoom(0.05, 130)
        self.audio.play('levelup')
        # 압력판은 눌리면 바닥으로 (재발동 방지)
        self.dungeon.tiles[y][x] = Tile.floor()

    # ─────────────── 마법사 DoT (점화 + 화염 장판) ──────────────────────
    def _hurt_enemy(self, enemy, dmg: int, col=(255, 140, 60), flash=True):
        """DoT/장판/소환수 공용 피해 — 사망 시 중앙 처치 처리로 라우팅."""
        if enemy is None or not enemy.is_alive() or dmg <= 0:
            return
        # co-op 클라: HP는 호스트 권위 → 로컬 적용 대신 인텐트 전송 + 타격연출만
        if self._coop_is_client():
            nid = getattr(enemy, 'net_id', None)
            if nid is not None:
                self.net.send_world_action({'kind': 'dmg', 'id': nid, 'dmg': int(dmg)})
            if flash:
                self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, col))
            return
        enemy.hp = max(0, enemy.hp - dmg)
        enemy.hurt_ms = max(enemy.hurt_ms, 70)
        if flash:
            self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, col))
        if not enemy.is_alive():
            self._on_enemy_killed(enemy)

    def _spawn_dot_zone(self, x, y, r, dps, ms, col=(255, 120, 40)):
        self._dot_zones.append({'x': x, 'y': y, 'r': r, 'dps': dps,
                                'ms': float(ms), 'col': col, 'tick': 0.0})

    def _update_dots(self, dt):
        p = self.player
        # 1) 적별 점화(burn) 틱
        for enemy in list(self.dungeon.enemies):
            if not enemy.is_alive():
                continue
            if enemy.burn_ms > 0:
                enemy.burn_ms = max(0, enemy.burn_ms - dt)
                enemy._burn_acc += enemy.burn_dps * dt / 1000.0
                if enemy._burn_acc >= 1.0:
                    d = int(enemy._burn_acc); enemy._burn_acc -= d
                    if (dt > 0 and random.random() < dt / 120.0
                            and self.dungeon.tiles[enemy.y][enemy.x].visible):
                        self.animator.particles.emit_death(enemy.x, enemy.y, enemy.burn_col)
                    self._hurt_enemy(enemy, d, enemy.burn_col, flash=False)
                if enemy.burn_ms == 0:
                    enemy.burn_dps = 0
        # 2) 화염 장판 — 범위 내 적에게 점화 부여/갱신
        for z in self._dot_zones:
            z['ms'] -= dt
            for enemy in self.dungeon.enemies:
                if not enemy.is_alive():
                    continue
                if abs(enemy.x - z['x']) <= z['r'] and abs(enemy.y - z['y']) <= z['r']:
                    self._apply_burn(enemy, dps=z['dps'], ms=700, col=z['col'])
        self._dot_zones = [z for z in self._dot_zones if z['ms'] > 0]

    # ─────────────── 마법사 소환수 ──────────────────────────────────────
    def _spawn_summon(self, count, ms, power_mul):
        from entities.summon import Summon
        p = self.player
        placed = 0
        for ox, oy in ((0, -1), (-1, 0), (1, 0), (0, 1), (-1, -1), (1, 1)):
            if placed >= count:
                break
            sx, sy = p.x + ox, p.y + oy
            if self.dungeon.is_walkable(sx, sy):
                self._summons.append(Summon(sx, sy, ms, power_mul))
                self.animator.particles.emit_heal(sx, sy)
                placed += 1

    def _update_summons(self, dt):
        for s in self._summons:
            s.update(dt, self)
        self._summons = [s for s in self._summons if s.alive]

    # ─────────────── 폭탄: 균열 벽 파괴 + 광역 피해 ─────────────────────
    _BOMB_THROW = 3        # 던지는 최대 거리(칸)
    _BOMB_FUSE  = 620      # 도화선(ms)
    _BOMB_RADIUS = 2       # 폭발 반경(체비셰프)

    def _throw_bomb(self):
        """바라보는 방향으로 폭탄을 던진다 — 벽 앞 마지막 칸에 착지, 도화선 후 폭발."""
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        bx, by = self.player.x, self.player.y
        for i in range(1, self._BOMB_THROW + 1):
            nx, ny = self.player.x + dx * i, self.player.y + dy * i
            if not self.dungeon.in_bounds(nx, ny) or self.dungeon.tiles[ny][nx].blocked:
                break                          # 벽/균열벽 앞에서 멈춤(바로 옆에서 터뜨리기 좋게)
            bx, by = nx, ny
        self._bombs.append({'x': bx, 'y': by, 'fuse': float(self._BOMB_FUSE),
                            'r': self._BOMB_RADIUS})
        self.animator.add(MagicBoltAnim(self.player.x, self.player.y, bx, by,
                                        self._facing, (200, 90, 40)))
        self.audio.play('use_item')

    def _update_bombs(self, dt):
        for b in self._bombs:
            b['fuse'] -= dt
        exploded = [b for b in self._bombs if b['fuse'] <= 0]
        self._bombs = [b for b in self._bombs if b['fuse'] > 0]
        for b in exploded:
            self._explode_bomb(b['x'], b['y'], b['r'])

    def _explode_bomb(self, x, y, r):
        """폭발 — 반경 내 균열 벽 파괴 + 적/플레이어 피해 + 강한 연출."""
        broke = self._break_cracked_walls_near(x, y, r)
        # 광역 피해 (깊이 비례 고정 피해)
        dmg = 30 + self.floor * 3
        for e in list(self.dungeon.enemies):
            if e.is_alive() and max(abs(e.x - x), abs(e.y - y)) <= r:
                self._hurt_enemy(e, dmg, (255, 150, 50))
        # 자해: 폭심 근처면 플레이어도 피해(리스크)
        if max(abs(self.player.x - x), abs(self.player.y - y)) <= r:
            self.player.take_damage(max(6, int(self.player.max_hp * 0.12)))
            self._hurt_flash_ms = 160
        # 연출: 섬광 + 흔들림 + 히트스톱 + 파이어볼 파티클 링
        self.animator.particles.emit_fireball_hit(x, y)
        for ox, oy in ((r, 0), (-r, 0), (0, r), (0, -r), (r, r), (-r, -r)):
            if self.dungeon.in_bounds(x + ox, y + oy):
                self.animator.particles.emit_fireball_hit(x + ox, y + oy)
        self._white_flash_ms = 60
        self._hitstop_ms = max(self._hitstop_ms, 90)
        self._start_shake(9, 460)
        self._start_punch_zoom(0.06, 150)
        self.audio.play('levelup_big')
        if broke:
            self.messages.append((t('bomb_wall_break', broke), 'good'))
        else:
            self.messages.append((t('bomb_boom'), 'warn'))

    def _break_cracked_walls_near(self, x, y, r) -> int:
        """반경 내 균열 벽을 바닥으로 — 파괴 개수 반환 (폭탄·강타 공용)."""
        n = 0
        for oy in range(-r, r + 1):
            for ox in range(-r, r + 1):
                wx, wy = x + ox, y + oy
                if not self.dungeon.in_bounds(wx, wy):
                    continue
                tl = self.dungeon.tiles[wy][wx]
                if tl.tile_type == TileType.CRACKED_WALL:
                    nt = Tile.floor()
                    nt.explored = True
                    nt.visible = tl.visible          # 부서지기 전 밝기 유지
                    self.dungeon.tiles[wy][wx] = nt
                    self.animator.particles.emit_death(wx, wy, (120, 110, 96))
                    n += 1
        # 새로 열린 공간을 즉시 밝힌다 — 단, 테스트/마을은 전체 공개(reveal_all)라 건너뜀
        if n and not self._is_test_mode and not self._in_town:
            self.dungeon.update_visibility(self.player.x, self.player.y)
        return n

    # ─────────────── 붕괴 추격 세트피스 ─────────────────────────────────
    _COLLAPSE_K    = 300      # 거리 1칸당 무너지는 간격(ms) — 작을수록 빠름
    _COLLAPSE_WARN = 700      # 무너지기 직전 경고(균열/흔들림) 구간(ms)
    _COLLAPSE_FALL_PCT = 0.18  # 추락 시 최대 HP 비례 피해

    def _start_collapse(self):
        """출구(계단)에서 먼 곳부터 무너지는 붕괴 파도 시작 — 계단으로 탈출하라."""
        exit_pos = getattr(self.dungeon, 'stairs_pos', None)
        if not exit_pos or self._collapse_active:
            return
        # 출구에서 BFS 거리
        from collections import deque
        dist = {exit_pos: 0}
        q = deque([exit_pos])
        while q:
            x, y = q.popleft()
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + ox, y + oy
                if (nx, ny) not in dist and self.dungeon.is_walkable(nx, ny):
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    q.append((nx, ny))
        dmax = max(dist.values()) if dist else 1
        # 깊은 층일수록 파도가 빨라진다(더 조여옴) — 하한 150ms/칸
        k = max(150, self._COLLAPSE_K - self.floor * 2)
        # 먼 타일(dmax)일수록 t≈0에 무너지고, 출구는 마지막에
        self._crumble = {pos: k * (dmax - d) for pos, d in dist.items()}
        self._collapse_active = True
        self._collapse_t = 0.0
        # 붕괴 중엔 전체 공개 — 시야 제한/어두움 없이 탈출에만 집중(플레이 편의)
        self.dungeon.reveal_all()
        self.animator.add(BannerAnim(t('collapse_start'), (255, 90, 60), size=30))
        self._start_shake(7, 700)
        self.audio.play('boss_appear')

    def _update_collapse(self, dt):
        if not self._collapse_active:
            return
        self._collapse_t += dt
        t_now = self._collapse_t
        px, py = self.player.x, self.player.y
        for (x, y), ct in self._crumble.items():
            if t_now < ct:
                continue
            tile = self.dungeon.tiles[y][x]
            if tile.tile_type == TileType.COLLAPSED:
                continue
            # 문/계단은 무너지지 않음 (탈출구 보존)
            if tile.tile_type in (TileType.DOOR, TileType.STAIRS_DOWN):
                continue
            tile.blocked = True
            self.dungeon.tiles[y][x] = Tile.collapsed()
            if self.dungeon.tiles[y][x].explored:
                pass
            self.dungeon.tiles[y][x].explored = tile.explored
            self.dungeon.tiles[y][x].visible = tile.visible
            # 위에 있던 적은 낙하(제거)
            e = self.dungeon.get_enemy_at(x, y)
            if e and not e.is_boss:
                self.animator.particles.emit_death(x, y, (90, 80, 70))
                if e in self.dungeon.enemies:
                    self.dungeon.enemies.remove(e)
            # 가끔 낙석 파티클
            if random.random() < 0.25 and self.dungeon.tiles[y][x].visible:
                self.animator.particles.emit_death(x, y, (110, 100, 88))
        # 플레이어가 무너진 칸 위면 추락
        if self.dungeon.in_bounds(px, py) and \
                self.dungeon.tiles[py][px].tile_type == TileType.COLLAPSED:
            self._collapse_player_fall()

    # 제단 도박: 탈출전용 무기 후보(직업별, 앞쪽일수록 상위)
    _ALTAR_WEAPON = {
        'warrior': ['great_sword', 'broad_sword'],
        'archer':  ['broad_sword', 'sword'],
        'mage':    ['arcane_staff', 'apprentice_staff'],
        'axeman':  ['great_axe', 'battle_axe'],
    }

    def _try_open_vault(self, x, y):
        """잠긴 금고문 개방 시도 — 열쇠 소지 시 열고 턴 소모, 없으면 막힘."""
        if self._keys > 0:
            self._keys -= 1
            self.dungeon.tiles[y][x] = Tile.floor()
            if not self._is_test_mode and not self._in_town:
                self.dungeon.update_visibility(self.player.x, self.player.y)
            self.animator.add(BannerAnim(t('vault_open'), (245, 215, 90), size=26))
            self.messages.append((t('vault_open'), 'good'))
            self.animator.particles.emit_levelup(x, y)
            self._start_punch_zoom(0.05, 140)
            self.audio.play('levelup')
            return True                 # 문 여는 데 한 턴 사용 (다음 이동으로 진입)
        self.messages.append((t('vault_locked'), 'warn'))
        self.animator.add(CalloutAnim(x, y, t('vault_locked_short'), (230, 120, 90)))
        self.audio.play('hit')
        return False

    def _trigger_altar(self, x, y):
        """붕괴 제단 = 랜덤 상자(도박). 밟으면 운에 따라:
          · 대박(약 45%) → 즉시 엄청난 보상(골드 폭탄 또는 레어 무기)
          · 붕괴(약 55%) → 던전이 무너짐. 계단으로 탈출해야 보상 획득."""
        if self._collapse_active:
            return
        self.dungeon.tiles[y][x] = Tile.floor()          # 상자 소모(재발동 방지)
        if random.random() < 0.45:
            self._altar_jackpot(x, y)
        else:
            mult = getattr(self, '_gold_mult', 1.0)
            self._collapse_reward = {
                'gold':   int(500 * mult) + self.floor * 15,
                'stones': 2,
                'gear':   True,
            }
            self.animator.add(BannerAnim(t('altar_trigger'), (255, 150, 60), size=28))
            self.messages.append((t('altar_trigger'), 'warn'))
            self.animator.particles.emit_death(x, y, (150, 60, 40))
            self._white_flash_ms = 120
            self.audio.play('boss_appear')
            self._start_collapse()

    def _altar_jackpot(self, x, y):
        """제단 대박 — 즉시 골드 폭탄 또는 레어 무기 지급(붕괴 없음)."""
        mult = getattr(self, '_gold_mult', 1.0)
        if random.random() < 0.5:
            gold = int(800 * mult) + self.floor * 25
            self.player.gold += gold
            self._gold_flash_ms = 280
            self.animator.add(BannerAnim(t('altar_jackpot_gold', gold),
                                         (255, 225, 90), size=30))
            self.messages.append((t('altar_jackpot_gold', gold), 'good'))
        else:
            name = self._grant_rare_weapon()
            self.animator.add(BannerAnim(t('altar_jackpot_gear', name),
                                         (140, 230, 255), size=28))
            self.messages.append((t('altar_jackpot_gear', name), 'good'))
        self.animator.particles.emit_levelup(x, y)
        self._white_flash_ms = 140
        self._start_punch_zoom(0.07, 160)
        self.audio.play('levelup_big')

    def _grant_rare_weapon(self):
        """직업 맞춤 상위 무기를 깊이 비례 강화 상태로 지급. 무기명 반환."""
        from entities.item import Item
        p = self.player
        cls = getattr(p, 'char_class', 'warrior')
        pool = [k for k in self._ALTAR_WEAPON.get(cls, self._ALTAR_WEAPON['warrior'])
                if k in self._item_data]
        key = pool[0] if pool else 'sword'
        d = dict(self._item_data[key]); d['key'] = key
        d['enhance_level'] = min(20, 4 + self.floor // 40)   # 레어답게 강화 보정
        it = Item(0, 0, d)
        if len(p.inventory) < p.max_inventory:
            p.inventory.append(it)
        else:
            p.enhance_stones += 3
        return it.name

    def _resolve_collapse_escape(self):
        """붕괴 중 계단 도달 — 탈출 성공 보상 + 상태 해제.
        제단으로 예약된 보상이 있으면 크게, 없으면 기본 탈출 보상."""
        self._collapse_active = False
        self._crumble = {}
        banked = self._collapse_reward
        self._collapse_reward = None
        if banked:
            reward = banked['gold']
            self.player.gold += reward
            self.player.enhance_stones += banked.get('stones', 1)
            if banked.get('gear'):
                self._grant_class_gear(self.floor)
            self.animator.add(BannerAnim(t('altar_escape', reward), (255, 225, 110), size=30))
        else:
            reward = int(200 * getattr(self, '_gold_mult', 1.0)) + self.floor * 5
            self.player.gold += reward
            self.player.enhance_stones += 1
            self.animator.add(BannerAnim(t('collapse_escape', reward), (255, 220, 90), size=28))
        self._gold_flash_ms = 220
        self.animator.particles.emit_levelup(self.player.x, self.player.y)
        self._start_punch_zoom(0.06, 150)
        self.audio.play('levelup_big')

    def _collapse_player_fall(self):
        p = self.player
        p.take_damage(max(8, int(p.max_hp * self._COLLAPSE_FALL_PCT)))
        self._hurt_flash_ms = 200
        self._start_shake(8, 320)
        self.audio.play('player_hit')
        self.animator.add(CalloutAnim(p.x, p.y, t('collapse_fall'), (255, 120, 90)))
        # 아직 안 무너진 인접 칸으로 밀어내기 (출구 쪽 우선)
        best = None
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            nx, ny = p.x + ox, p.y + oy
            if (self.dungeon.is_walkable(nx, ny)
                    and self.dungeon.tiles[ny][nx].tile_type != TileType.COLLAPSED):
                d = self._crumble.get((nx, ny), 1e9)
                if best is None or d > best[0]:   # 가장 늦게 무너질(=출구에 가까운) 칸
                    best = (d, nx, ny)
        if best:
            p.x, p.y = best[1], best[2]
            self.camera.center_on(p.x, p.y)

    def _apply_distortion(self, surf):
        """사인파 수평 왜곡 — 화면 전체가 흐물흐물 일렁이는 착시.

        (셰이더 없이 수평 스트립을 좌우로 밀어 근사. GPU 셰이더 연동 시
         이 함수를 프래그먼트 셰이더 uniform(amp, time)으로 대체하면 된다.)
        """
        amp = self._distort_amp
        if amp <= 0:
            return surf
        w, h = surf.get_size()
        out = pygame.Surface((w, h))
        tphase = pygame.time.get_ticks() * 0.004
        strip = 4                                  # 스트립 높이(성능/품질 절충)
        for sy in range(0, h, strip):
            dx = int(math.sin(sy * 0.05 + tphase) * amp)
            out.blit(surf, (dx, sy), (0, sy, w, strip))
        return out

    # ─────────────── 층 전환 페이드 ──────────────────────────────────
    def _start_fade(self, callback):
        self._fade_alpha    = 0
        self._fade_dir      = 1
        self._fade_callback = callback

    def _update_fade(self, dt):
        if self._fade_dir == 0:
            return
        self._fade_alpha = max(0, min(255, self._fade_alpha + self._fade_dir * self._fade_speed))
        if self._fade_dir == 1 and self._fade_alpha >= 255:
            if self._fade_callback:
                self._fade_callback()
                self._fade_callback = None
            self._fade_dir = -1
        elif self._fade_dir == -1 and self._fade_alpha <= 0:
            self._fade_dir = 0

    @property
    def _is_fading(self):
        return self._fade_dir != 0

    # ─────────────── BGM 제어 ─────────────────────────────────────────
    def _update_bgm(self):
        if not self.audio.bgm:
            return
        if self.state == 'menu':
            self.audio.bgm.play('menu')
        elif self.state in ('playing', 'shop', 'storage', 'paused', 'dead'):
            if self.dungeon is None:
                return
            if self._in_town:
                self.audio.bgm.play('shop')      # 마을 = 평화로운 상점 트랙
            elif self.dungeon.is_boss_floor:
                self.audio.bgm.play('boss')
            elif self.dungeon.has_shop:
                self.audio.bgm.play('shop')
            else:
                self.audio.bgm.play(f'theme_{self.dungeon.theme_index}')

    # ─────────────── 새 게임 / 불러오기 ──────────────────────────────
    def _new_game(self, char_class='warrior', char_name='Hero', slot=None,
                  appearance=None):
        if slot is not None:
            self._save_slot = slot
        self._char_class = char_class if char_class in CLASSES else 'warrior'
        self._char_name  = char_name or 'Hero'
        self._char_appearance = dict(appearance) if appearance else \
            {'skin': 0, 'hair': 0, 'haircol': 0}
        delete_save(self._save_slot)
        self._save_data       = None
        self.floor            = 1
        self._facing          = 'down'
        self._walk_frame      = 0
        self.messages         = []
        self.skills           = SkillManager()
        self._run_kills       = 0
        self._unlocked_combos = set()
        self._skill_books     = set()
        self._skill_levels    = {sid: 1 for sid in ALL_SKILL_DEFS}
        self._skill_xp        = {sid: 0 for sid in ALL_SKILL_DEFS}
        self._equipped_skills = default_equipped_for(self._char_class)
        self._skill_enchants  = {
            sid: {'power': 0, 'haste': 0, 'efficiency': 0, 'arcane': 0}
            for sid in ALL_SKILL_DEFS
        }
        self._arcane_window_ms  = 0
        self._arcane_last_skill = None
        self._combo_count = 0
        self._combo_ms    = 0.0
        # 마을 세션 초기화 (사망 시 던전 소지품만 소실 — 창고는 파일로 유지)
        self._in_town         = False
        self._dungeon_session = None
        from core.quests import fresh_states
        self._quests = fresh_states()
        self._dialog = None
        self._max_floor_reached = 1
        self._load_floor(is_new_game=True)
        # 시작 지원: 귀환 주문서 1장 (창고에 모아둔 유산을 찾으러 갈 수 있게)
        from entities.item import Item
        if 'return_scroll' in self._item_data:
            d = dict(self._item_data['return_scroll']); d['key'] = 'return_scroll'
            self.player.inventory.append(Item(0, 0, d))
        self.state = 'playing'
        self._maybe_begin_coop()   # co-op 대기 중이면 마을 진입 + 세션 부착

    # ─────────────── 테스트 모드 ──────────────────────────────────────
    def start_test_mode(self, floor: int = 1, char_class='warrior'):
        """python3 main.py -test [층수] 로 호출 — 최대 스탯으로 지정 층 시작."""
        self._is_test_mode    = True
        # 기록/창고를 격리된 *_test.json 으로 (실제 세이브 오염 없이 일지/정산 시험)
        from core.save_load import use_test_data
        use_test_data(True)
        self._records = load_records()
        self._storage, self._storage_cap = load_storage()
        self._gold_mult = ng_plus_gold_mult(self._records)
        self._title_badge = bool(self._records.get('active_title'))
        self._save_data       = None
        self._char_class      = char_class if char_class in CLASSES else 'warrior'
        self._char_name       = 'TestHero'
        self._char_appearance = {'skin': 0, 'hair': 0, 'haircol': 0}
        self.floor            = max(1, min(floor, MAX_FLOOR))
        # 테스트 편의: 시작 층 아래 보스층을 클리어한 것으로 간주(전리품 표시 확인용)
        self._records['max_boss_floor'] = max(int(self._records.get('max_boss_floor', 0)),
                                              ((self.floor - 1) // 5) * 5)
        self._facing          = 'down'
        self._walk_frame      = 0
        self.messages         = []
        self.skills           = SkillManager()
        self._run_kills       = 0
        # 모든 스킬 최대 레벨, 조합 스킬 전체 해금
        self._skill_levels    = {sid: SKILL_MAX_LEVEL for sid in ALL_SKILL_DEFS}
        self._skill_xp        = {sid: 0 for sid in ALL_SKILL_DEFS}
        self._equipped_skills = default_equipped_for(self._char_class)
        self._skill_enchants  = {
            sid: {'power': ENCHANT_MAX_LEVEL, 'haste': ENCHANT_MAX_LEVEL,
                  'efficiency': ENCHANT_MAX_LEVEL, 'arcane': ENCHANT_MAX_LEVEL}
            for sid in ALL_SKILL_DEFS
        }
        self._unlocked_combos = set(COMBO_SKILL_DEFS.keys())
        self._skill_books     = set(COMBO_SKILL_DEFS.keys())
        self._load_floor(is_new_game=True)
        self._apply_skill_level_cds()
        # 플레이어 최대 스탯 적용
        p = self.player
        p.level        = 99
        p.max_hp       = 9999
        p.hp           = 9999
        p.attack       = 999
        p.defense      = 99
        p.attack_speed = 10.0   # 공격 쿨다운 100ms (최소)
        p.move_speed   = 5.0    # 이동 간격 60ms (최소)
        p.evasion      = 40     # 회피율 최대
        p.gold         = 99999
        self._skill_points = 99
        # [TEST] 펫 즉시 해금 + 강화석 지급 (B 키로 상태창)
        p.pet_stones = 50
        self.unlock_pet('attack')
        # 강화 시스템 테스트용 아이템
        from entities.item import Item as _Item
        p.enhance_stones = 100
        _sword_data = dict(self._item_data['sword']); _sword_data['key'] = 'sword'
        p.inventory.append(_Item(0, 0, _sword_data))
        _armor_data = dict(self._item_data['leather_armor']); _armor_data['key'] = 'leather_armor'
        p.inventory.append(_Item(0, 0, _armor_data))
        # 테스트 편의: 폭탄 5개 (균열 벽 파괴 실험용)
        if 'bomb' in self._item_data:
            for _ in range(5):
                _bd = dict(self._item_data['bomb']); _bd['key'] = 'bomb'
                p.inventory.append(_Item(0, 0, _bd))
        self.dungeon.reveal_all()
        self.state = 'playing'
        self.messages.append(('[TEST] 테스트 모드 — 격리 기록(*_test.json)', 'info'))
        self.messages.append((f'[TEST] B{self.floor}F  최대 스탯 적용', 'good'))
        self.messages.append(('[TEST] J 정복일지 · [ 테마+1 · ] 999정산 · \\ 리셋 · C 붕괴', 'info'))

    def start_town_test(self, floor: int = 1, char_class='warrior'):
        """python3 test_main.py town [층] — 던전 세션 생성 후 곧장 마을 진입."""
        self.start_test_mode(floor, char_class=char_class)
        self._enter_town()

    def start_journal_test(self, char_class='warrior'):
        """python3 test_main.py journal — 정복 일지/정산 시험용.

        격리 기록에 샘플 데이터를 심고 마을에서 시작 (일지·칭호 뱃지 즉시 확인).
        """
        self.start_test_mode(floor=520, char_class=char_class)
        from core.save_load import save_records
        self._records.update({
            'theme_clears': {'0': 7, '1': 4, '2': 3, '3': 2, '4': 1, '6': 1},
            'best_floor': max(520, self._records.get('best_floor', 0)),
        })
        save_records(self._records)
        self._enter_town()
        self.messages.append(('[TEST] 샘플 일지 로드 — J로 열기, ] 로 999정산', 'good'))

    def start_burning_mode(self, char_class='warrior'):
        """python3 test_main.py bunning — 버닝 스테이지 직행."""
        self.start_test_mode(floor=1, char_class=char_class)
        self._enter_burning_stage()
        self.clock.tick()   # 초기화 누적 시간 소비 — 첫 dt가 타이머를 왜곡하지 않도록

    def _continue_game(self, slot=None):
        if slot is not None:
            self._save_slot = slot
            self._save_data = load_game(slot)
        data = self._save_data
        if not data:
            self._new_game(); return
        self._char_class = data.get('char_class', 'warrior')
        self._char_name  = data.get('name', 'Hero')
        self._char_appearance = dict(
            data.get('appearance')
            or data.get('player', {}).get('appearance')
            or {'skin': 0, 'hair': 0, 'haircol': 0})
        self.floor       = data['floor']
        self._facing     = 'down'
        self._walk_frame = 0
        self.messages    = []
        self.skills           = SkillManager()
        self.skills.from_dict(data.get('skills', {}))
        self._unlocked_combos = set(data.get('unlocked_combos', []))
        from core.quests import fresh_states as _fresh_q
        _saved_q = data.get('quests') or {}
        self._quests = _fresh_q()
        for _qid, _qs in _saved_q.items():
            if _qid in self._quests and isinstance(_qs, dict):
                self._quests[_qid].update(_qs)
        self._max_floor_reached = max(1, data.get('max_floor_reached', self.floor))
        self._skill_books     = set(data.get('skill_books', []))
        # migrate old slot-keyed saves to skill_id-keyed
        _raw_levels = data.get('skill_levels', {})
        _OLD_MAP = {'W': 'flash_dash', 'A': 'steel_whirl', 'S': 'regen_breath', 'D': 'judgment'}
        if _raw_levels and all(k in _OLD_MAP for k in _raw_levels):
            self._skill_levels = {sid: 1 for sid in ALL_SKILL_DEFS}
            for _slot, _lvl in _raw_levels.items():
                self._skill_levels[_OLD_MAP[_slot]] = _lvl
        else:
            self._skill_levels = {sid: _raw_levels.get(sid, 1) for sid in ALL_SKILL_DEFS}
        _raw_xp = data.get('skill_xp', {})
        if _raw_xp and all(k in _OLD_MAP for k in _raw_xp):
            self._skill_xp = {sid: 0 for sid in ALL_SKILL_DEFS}
        else:
            self._skill_xp = {sid: _raw_xp.get(sid, 0) for sid in ALL_SKILL_DEFS}
        self._skill_points    = data.get('skill_points', 0)
        self._equipped_skills = data.get('equipped_skills', DEFAULT_EQUIPPED.copy())
        _raw_enc = data.get('skill_enchants', {})
        self._skill_enchants = {}
        for sid in ALL_SKILL_DEFS:
            enc = dict(_raw_enc.get(sid, {}))
            for etype in ENCHANT_TYPES:
                enc.setdefault(etype, 0)
            self._skill_enchants[sid] = enc
        self._apply_skill_level_cds()
        self._run_kills       = 0
        self.vfx_loot.clear()
        dungeon, start = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, self.floor,
                                          self._enemy_data, self._item_data)
        self.dungeon = dungeon
        self._theme  = get_theme(self.floor)
        self.player  = Player.from_save(start[0], start[1], data['player'], self._item_data,
                                        char_class=self._char_class, char_name=self._char_name,
                                        appearance=self._char_appearance)
        self._attach_pet()
        self._apply_relic_bonus()
        self.camera  = Camera(MAP_WIDTH, MAP_HEIGHT)
        self.camera.center_on(self.player.x, self.player.y)
        if not self._is_test_mode:
            self.dungeon.update_visibility(self.player.x, self.player.y)
        self.messages.append((t('floor_cont', self.floor), 'good'))
        self.state = 'playing'
        self._maybe_begin_coop()   # co-op 대기 중이면 마을 진입 + 세션 부착

    def _load_floor(self, is_new_game=False):
        # 엔들리스(심연): 999 클리어 후엔 999 너머로 하강 허용
        if not self._records.get('game_cleared', False):
            self.floor = min(self.floor, MAX_FLOOR)
        self._quest_on_floor(min(self.floor, MAX_FLOOR))   # reach_floor 퀘스트 추적
        self.vfx_loot.clear()          # 이전 층 전리품 연출 정리
        # co-op: 공유 시드로 결정론적 생성. 프롭·적까지 양쪽 동일하도록 이 층 동안
        # 시드를 유지(엔트로피 복귀는 co-op 종료 시). net_id 인덱스 매칭에 필수.
        if self._coop_seed is not None:
            import random as _r
            _r.seed(self._coop_seed)
        dungeon, start = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, self.floor,
                                          self._enemy_data, self._item_data)
        self.dungeon  = dungeon
        self._apply_coop_difficulty(dungeon)   # co-op이면 적 강화(싱글보다 어렵게)
        self._theme   = get_theme(self.floor)
        if is_new_game:
            self.player = Player(*start,
                                 char_class=getattr(self, '_char_class', 'warrior'),
                                 char_name=getattr(self, '_char_name', 'Hero'))
            self.player.appearance = dict(getattr(self, '_char_appearance', None)
                                          or {'skin': 0, 'hair': 0, 'haircol': 0})
            self._apply_relic_bonus()
            self.messages.append((t('welcome'), 'good'))
            self.messages.append((t('wasd_hint'), 'info'))
            _hint = {'archer': 'archer_hint', 'mage': 'mage_hint',
                     'axeman': 'axeman_hint'}.get(
                self.player.char_class, 'combat_hint')
            self.messages.append((t(_hint), 'info'))
        else:
            self.player.x, self.player.y = start
            self.messages.append((t('floor_arrive', self.floor), 'good'))
            if is_new_theme(self.floor):
                self.messages.append((t('new_theme', self._theme['name']), 'info'))
            if dungeon.is_boss_floor:
                self.messages.append((t('boss_incoming'), 'bad'))
                self.audio.play('boss_appear')
            elif dungeon.has_shop:
                self.messages.append((t('shop_floor'), 'info'))
            if not self._is_test_mode and not self._coop_dungeon:
                save_game(self.player, self.floor, self.skills, self._unlocked_combos, self._skill_books,
                              self._skill_levels, self._skill_xp, self._skill_points,
                              self._equipped_skills, self._skill_enchants, self._quests,
                              self._max_floor_reached, slot=self._save_slot,
                              name=getattr(self,'_char_name','Hero'),
                              char_class=getattr(self,'_char_class','warrior'))
                self.messages.append((t('auto_saved'), 'info'))
                self.audio.play('save')
        self.camera = Camera(MAP_WIDTH, MAP_HEIGHT)
        self.camera.center_on(self.player.x, self.player.y)
        self._apply_map_fx()        # 테마별 지진/왜곡 설정 (컨베이어는 생성기)
        # 펫: 층 이동 시 위치 재동기화 (신규게임이면 아직 미해금)
        if self._pet:
            self._pet.snap_to(self.player.x, self.player.y)
            self._pet_trail = [(self.player.x, self.player.y)]
        elif self.player and self.player.is_pet_unlocked:
            self._attach_pet()
        if self._is_test_mode:
            self.dungeon.reveal_all()
        else:
            self.dungeon.update_visibility(self.player.x, self.player.y)

        # 파괴 가능 프롭 + 보물 고블린 (리스폰 카운트 산정 전에 스폰)
        self._spawn_floor_props()

        # co-op: 결정론적 생성이라 양쪽 적 목록이 동일 → 인덱스로 안정적 net_id 부여
        if self._coop_dungeon:
            for i, e in enumerate(self.dungeon.enemies):
                e.net_id = i
            # 클라: 적 피해를 로컬 적용하지 않고 호스트에 인텐트로 전달(권위=호스트)
            if self.net is not None and not self.net.is_host:
                for e in self.dungeon.enemies:
                    self._wrap_client_enemy_damage(e)

        # 리스폰 설정: 보스·프롭·고블린 제외 초기 몬스터 수를 최대치로 고정
        self._respawn_max      = sum(1 for e in self.dungeon.enemies
                                     if not e.is_boss and not e.is_prop and not e.flee)
        self._respawn_timer_ms = self._RESPAWN_INTERVAL

    def _emit_goblin_sparkle(self, enemy):
        """보물 고블린 주변 금색 반짝임 파티클 (순수 연출)."""
        from core.particles import Particle
        ts = TILE_SIZE
        wx = enemy.x * ts + ts * 0.5 + random.uniform(-8, 8)
        wy = enemy.y * ts + ts * 0.4 + random.uniform(-6, 6)
        self.animator.particles._add(Particle(
            wx, wy, random.uniform(-15, 15), random.uniform(-45, -15),
            drag=2.0, grav=-0.15, life_ms=random.randint(280, 480),
            r0=2, r1=1, c0=(255, 230, 120), c1=(230, 160, 30),
            a0=220, a1=0, glow=True,
        ))

    # ─────────────── 프롭 / 보물 고블린 스폰 ─────────────────────────
    def _spawn_floor_props(self):
        """항아리·나무상자 3~6개 + 8% 확률 보물 고블린 배치."""
        from entities.enemy import Enemy
        dungeon = self.dungeon

        def _free_tile(min_player_dist=0):
            for _ in range(60):
                room = random.choice(dungeon.rooms)
                x = random.randint(room.x + 1, room.x + room.w - 2)
                y = random.randint(room.y + 1, room.y + room.h - 2)
                if (dungeon.is_walkable(x, y)
                        and not dungeon.get_enemy_at(x, y)
                        and not dungeon.get_item_at(x, y)
                        and (x, y) != (self.player.x, self.player.y)
                        and (x, y) != dungeon.stairs_pos
                        and abs(x - self.player.x) + abs(y - self.player.y) >= min_player_dist):
                    return x, y
            return None

        if not dungeon.rooms:
            return
        # ── 항아리/상자 (밟아 부수는 소소한 보상) ──
        for _ in range(random.randint(3, 6)):
            pos = _free_tile()
            if pos is None:
                continue
            key = random.choice(('pot', 'pot', 'crate'))
            d = dict(self._enemy_data[key])
            d['key'] = key
            d['gold_drop'] = random.randint(2, 6) + self.floor // 3
            dungeon.enemies.append(Enemy(pos[0], pos[1], d))
        # ── 보물 고블린 (8%, 보스층 제외) ──
        if not dungeon.is_boss_floor and random.random() < 0.08:
            pos = _free_tile(min_player_dist=12)
            if pos:
                d = dict(self._enemy_data['treasure_goblin'])
                d['key'] = 'treasure_goblin'
                d['hp'] = 12 + self.floor * 3          # 층 비례 — 몇 대는 맞아야 잡힘
                d['gold_drop'] = 60 + self.floor * 25 + random.randint(0, 40)
                dungeon.enemies.append(Enemy(pos[0], pos[1], d))
                self.messages.append((t('goblin_spawn'), 'warn'))
                self.audio.play('shop_open')

    # ─────────────── 이벤트 / 입력 ───────────────────────────────────
    def _handle_events(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 버리기 확인 대화상자 처리 (최우선)
                if self._inv_confirm_idx is not None:
                    _, yes_r, _ = self._inv_confirm_rects()
                    if yes_r.collidepoint(event.pos):
                        self._discard_inventory_item(self._inv_confirm_idx)
                    self._inv_confirm_idx = None
                elif self.state == 'menu':
                    self._handle_menu_click(event.pos)
                elif self.state == 'char_create':
                    self._handle_char_create_click(event.pos)
                elif self.state == 'paused':
                    self._handle_pause_click(event.pos)
                elif self.state == 'inventory':
                    # 카테고리 탭 클릭이면 전환하고 드래그 안 함
                    _tab_hit = next((ci for ci, r in enumerate(self._inv_tab_rects())
                                     if r.collidepoint(event.pos)), None)
                    if _tab_hit is not None:
                        self._inv_set_cat(_tab_hit)
                        self._inv_drag_idx = None
                    else:
                        # 드래그 시작 — 뷰 위치를 실제 인벤 인덱스로 변환해 보관
                        _vp = self._inv_slot_at(event.pos)
                        self._inv_drag_idx = (self._inv_real_idx(_vp)
                                              if _vp is not None else None)
                    self._inv_drag_start = event.pos
                    self._inv_drag_pos   = event.pos
                elif self.state == 'equipment':
                    self._handle_equipment_click(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self._inv_confirm_idx is None and \
                        self.state == 'inventory' and self._inv_drag_idx is not None:
                    moved = max(abs(event.pos[0] - self._inv_drag_start[0]),
                                abs(event.pos[1] - self._inv_drag_start[1]))
                    pw, ph, bx, by = self._inv_layout()
                    in_panel = pygame.Rect(bx, by, pw, ph).collidepoint(event.pos)
                    if self._inv_trash_rect().collidepoint(event.pos):
                        # 버리기 존에 드롭 → 확인 대화상자
                        self._start_discard_confirm(self._inv_drag_idx)
                    elif moved >= 20 and not in_panel:
                        # 패널 밖으로 드래그 → 확인 대화상자
                        self._start_discard_confirm(self._inv_drag_idx)
                    elif moved < 8:
                        # 이동 없음 → 일반 클릭
                        self._handle_inventory_click(event.pos)
                    self._inv_drag_idx = None

            elif event.type == pygame.MOUSEMOTION:
                if self.state == 'inventory' and self._inv_drag_idx is not None:
                    self._inv_drag_pos = event.pos

            elif event.type == pygame.KEYDOWN:
                if self._chat_open:
                    self._handle_chat_key(event.key, event.unicode)
                elif (event.key == pygame.K_t and self.net is not None
                        and (self._in_town or self._coop_dungeon)
                        and self.state == 'playing'
                        and not self._skillbook_open and not self._enhance_open):
                    self._chat_open = True
                    self._chat_text = ''
                elif self._skillbook_open:
                    self._handle_skillbook_key(event.key)
                elif self._enhance_open:
                    self._handle_enhance_key(event.key)
                elif self.state == 'storage' and event.key == pygame.K_u:
                    self._upgrade_storage()       # 창고 용량 확장
                elif self._inv_confirm_idx is not None:
                    if event.key in (pygame.K_y, pygame.K_RETURN):
                        self._discard_inventory_item(self._inv_confirm_idx)
                        self._inv_confirm_idx = None
                    elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                        self._inv_confirm_idx = None
                elif self.state == 'inventory' and event.key == pygame.K_TAB:
                    self._inv_set_cat((self._inv_cat + 1) % len(self._INV_CATS))
                elif self.state == 'inventory' and event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    _ri = self._inv_real_idx(self._inv_sel)
                    if _ri is not None:
                        self._start_discard_confirm(_ri)
                elif self.state == 'char_create':
                    self._handle_char_create_key(event.key, event.unicode)
                elif (self.state == 'menu' and self._menu_page == 'multiplayer'
                        and (event.unicode in '0123456789.'
                             or event.key == pygame.K_BACKSPACE)):
                    self._handle_mp_key(event.key, event.unicode)
                elif (self.state == 'menu' and self._menu_page == 'main'
                        and event.key == pygame.K_DELETE):
                    if self._menu_sel < len(self._cards):
                        c = self._cards[self._menu_sel]
                        if c.get('exists'):
                            self._delete_card(c['slot'])
                elif event.key == pygame.K_j:
                    # 정복 일지 토글 (플레이/마을·창고·주막에서 열람)
                    if self.state == 'journal':
                        self._close_journal()
                    elif self.state in ('playing', 'storage', 'inn'):
                        self._open_journal()
                elif self._is_test_mode and event.key == pygame.K_LEFTBRACKET:
                    # [TEST] 현재 층 테마 클리어 +1
                    self._record_theme_clear_for(self.floor)
                    self.messages.append(('[TEST] 테마 클리어 +1 (일지 J)', 'good'))
                elif self._is_test_mode and event.key == pygame.K_RIGHTBRACKET:
                    # [TEST] 999 마스터 정산 강제 발동
                    self._check_game_complete()
                elif self._is_test_mode and event.key == pygame.K_BACKSLASH:
                    # [TEST] 테스트 기록 초기화
                    from core.save_load import save_records
                    self._records = {**self._records, 'theme_clears': {},
                                     'game_cleared': False, 'unlocked_titles': [],
                                     'active_title': '', 'ng_plus': 0}
                    save_records(self._records)
                    self._gold_mult = 1.0; self._title_badge = False
                    self.messages.append(('[TEST] 기록 초기화됨', 'info'))
                elif self._is_test_mode and event.key == pygame.K_c \
                        and self.state == 'playing' and not self._in_town:
                    self._start_collapse()             # [TEST] 붕괴 추격 발동
                    self.messages.append(('[TEST] 붕괴 시작 (C)', 'bad'))
                elif event.key == pygame.K_b and self.state in ('playing', 'storage', 'inn'):
                    self._open_pet_status()          # 펫 상태창 (B)
                elif event.key == pygame.K_v and self.state == 'playing' and not self._in_town:
                    self._toggle_pet()               # 펫 소환/해제 (V)
                elif self.state == 'pet':
                    self._handle_pet_key(event.key)
                elif self.state == 'credits':        # 크레딧: 아무 키 → 스킵
                    self._finish_credits()

        # 캐릭터 생성 화면은 raw 키 입력 전용 — 액션 처리 건너뜀
        if self.state == 'char_create':
            return

        # 채팅 입력 중에는 이동/행동 억제 (WASD가 글자로 들어가게)
        if self._chat_open:
            self.input.update(dt)   # 내부 타이머 유지용으로 소비만
            return

        for action in self.input.update(dt):
            t = action['type']

            if t == 'escape':
                if self._skillbook_open:
                    if self._skillbook_equip_mode:
                        self._skillbook_equip_mode = False
                        self._skillbook_target_slot = None
                    else:
                        self._skillbook_open = False
                    continue
                if self._enhance_open:
                    self._enhance_open = False
                    continue
                if self._inv_confirm_idx is not None:
                    self._inv_confirm_idx = None
                elif self.state in ('inventory', 'equipment'):
                    self._inv_drag_idx = None
                    self.state = 'playing'
                elif self.state == 'shop':
                    self.state = 'playing'
                elif self.state in ('storage', 'inn', 'questlog', 'farm_menu',
                                    'altar', 'angler', 'fishing', 'ranch_menu'):
                    self.state = 'playing'
                elif self.state == 'journal':
                    self._close_journal()
                elif self.state == 'pet':
                    self._close_pet_status()
                elif self.state == 'dialog':
                    self._dialog_close(declined=True)
                elif self.state == 'paused':
                    self.state = 'playing'
                elif self.state == 'playing':
                    self._pause_sel = 0
                    self.state = 'paused'
                elif self.state == 'menu':
                    if self._menu_page in ('settings', 'multiplayer'):
                        self._menu_page = 'main'
                    elif self._pending_net is not None:
                        self._cancel_pending_net()   # co-op 캐릭터 선택 취소
                    else:
                        pygame.quit(); sys.exit()
                elif self.state == 'dead':
                    pygame.quit(); sys.exit()
                continue

            if self.state == 'menu':
                self._handle_menu_action(action)
            elif self.state == 'paused':
                self._handle_pause_action(action)
            elif self.state == 'shop':
                self._handle_shop_action(action)
            elif self.state == 'storage':
                self._handle_storage_action(action)
            elif self.state == 'farm_menu':
                self._handle_farm_menu_action(action)
            elif self.state == 'altar':
                self._handle_altar_action(action)
            elif self.state == 'angler':
                self._handle_angler_action(action)
            elif self.state == 'fishing':
                self._handle_fishing_action(action)
            elif self.state == 'ranch_menu':
                self._handle_ranch_menu_action(action)
            elif self.state == 'inn':
                self._handle_inn_action(action)
            elif self.state == 'dialog':
                if t in ('confirm', 'attack', 'interact'):
                    self._dialog_confirm()
            elif self.state == 'questlog':
                if t == 'questlog':
                    self.state = 'playing'
            elif self.state == 'inventory':
                self._handle_inventory_action(action)
            elif self.state == 'equipment':
                self._handle_equipment_action(action)
            elif self.state == 'playing':
                if t == 'inventory':
                    self._inv_sel = 0
                    self.state = 'inventory'
                elif t == 'equipment':
                    self._equip_sel = 0
                    self.state = 'equipment'
                elif t == 'enhance':
                    self._enhance_mode = 'stone'   # P키 = 강화석 모드
                    self._enhance_open = True
                    self._enhance_cursor = 0
                elif t == 'interact':
                    if self._in_town:
                        self._town_interact()
                elif t == 'questlog':
                    self.state = 'questlog'
                    self.audio.play('menu_select')
                elif t == 'skillbook':
                    self._skillbook_open   = not self._skillbook_open
                    self._skillbook_cursor = 0
                elif t in ('move', 'wait', 'attack', 'use_item', 'skill', 'combo_skill', 'ultimate'):
                    if not self._skillbook_open:
                        self._process(action)
            elif self.state == 'dead':
                if t == 'ultimate' and action.get('key') == 'R':
                    self._new_game()

    def _handle_menu_action(self, action):
        if self._menu_page == 'settings':
            self._handle_menu_settings_action(action)
            return
        if self._menu_page == 'multiplayer':
            self._handle_menu_mp_action(action)
            return
        typ = action['type']
        n = len(self._cards)
        total = n + 3  # + multiplayer + settings + quit
        if typ == 'move':
            dy = action.get('dy', 0)
            if dy != 0:
                self._menu_sel = (self._menu_sel + dy) % total
                self.audio.play('menu_select')
        elif typ in ('wait', 'confirm', 'load'):
            if self._menu_sel < n:
                self._select_card(self._cards[self._menu_sel])
            elif self._menu_sel == n:
                self._open_multiplayer()
            elif self._menu_sel == n + 1:
                self.audio.play('menu_select')
                self._menu_page = 'settings'
                self._menu_settings_sel = 0
            elif self._menu_sel == n + 2:
                pygame.quit(); sys.exit()

    def _open_multiplayer(self):
        """멀티플레이(beta) 페이지 진입. 실제 로비 연결은 P1에서."""
        self.audio.play('menu_select')
        self._menu_page = 'multiplayer'
        self._menu_settings_sel = 0

    def _handle_menu_mp_action(self, action):
        typ = action['type']
        if typ == 'move':
            dy = action.get('dy', 0)
            if dy != 0:
                self._menu_settings_sel = (self._menu_settings_sel + dy) % 3
                self.audio.play('menu_select')
        elif typ in ('wait', 'confirm', 'load'):
            self._activate_mp_item(self._menu_settings_sel)

    def _activate_mp_item(self, idx):
        if idx == 0:                       # 방 만들기 (호스트)
            self._begin_host()
        elif idx == 1:                     # 친구 참가 (IP 접속)
            self._begin_join()
        else:                              # 뒤로
            self.audio.play('menu_select')
            self._menu_page = 'main'

    def _handle_mp_key(self, key, uni):
        """멀티 페이지 IP 필드 편집 (숫자·점·백스페이스)."""
        if key == pygame.K_BACKSPACE:
            self._mp_ip = self._mp_ip[:-1]
        elif uni in '0123456789.' and len(self._mp_ip) < 21:
            self._mp_ip += uni

    def _begin_host(self):
        """소켓 호스트를 열고 캐릭터 선택 화면으로. 접속 배관은 백그라운드."""
        from net.socket_transport import SocketTransport, DEFAULT_PORT
        if self._mp_connecting:
            return
        try:
            tp = SocketTransport.host(port=DEFAULT_PORT)
        except OSError:
            # 바인드 실패 = 포트 점유(다른 게임 창이 이미 호스트 중 등)
            self._mp_status = t('menu_mp_port_busy')
            return
        self.audio.play('menu_confirm')
        self._pending_net    = ('host', tp)
        self._mp_mode_banner = 'host'
        self._mp_status      = None
        self._menu_page      = 'main'

    def _begin_join(self):
        """입력한 IP로 접속을 백그라운드 스레드에서 시도한다(UI 프리즈 방지)."""
        import threading
        if self._mp_connecting:
            return
        ip = (self._mp_ip.strip() or '127.0.0.1')
        self._mp_connecting     = True
        self._mp_connect_result = None
        self._mp_status         = t('menu_mp_connecting')
        self.audio.play('menu_select')

        def worker():
            from net.socket_transport import SocketTransport, DEFAULT_PORT
            try:
                tp = SocketTransport.connect(ip, DEFAULT_PORT, timeout=12.0)
                self._mp_connect_result = ('ok', tp)
            except Exception as e:  # noqa: BLE001
                self._mp_connect_result = ('err', str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _mp_poll_connect(self):
        """매 프레임 호출 — 접속 스레드 결과를 확인해 상태를 전이한다."""
        res = self._mp_connect_result
        if res is None:
            return
        self._mp_connect_result = None
        self._mp_connecting     = False
        kind, val = res
        if kind == 'ok':
            self._pending_net    = ('join', val)
            self._mp_mode_banner = 'join'
            self._mp_status      = None
            self._menu_page      = 'main'
            self.audio.play('menu_confirm')
        else:
            self._mp_status = t('menu_mp_failed')

    def _cancel_pending_net(self):
        """캐릭터 선택 중 취소 — 열어둔 전송을 닫고 상태 초기화."""
        role_tp = self._pending_net
        self._pending_net    = None
        self._mp_mode_banner = None
        self._mp_status      = None
        if role_tp is not None:
            try:
                role_tp[1].close()
            except Exception:
                pass
        self.audio.play('menu_select')

    def _maybe_begin_coop(self):
        """게임 월드 생성 직후 호출 — co-op 대기 중이면 마을 진입 + 세션 부착."""
        if not self._pending_net:
            return
        role, tp = self._pending_net
        self._pending_net    = None
        self._mp_mode_banner = None
        self._mp_status      = None
        if not self._in_town:
            self._enter_town()
        self.start_net_session(tp, mode='town')

    def _select_card(self, card):
        """카드 선택 — 있으면 이어하기, 비었으면 캐릭터 생성."""
        self.audio.play('menu_confirm')
        if card.get('exists'):
            self._continue_game(card['slot'])
        else:
            self._open_char_create(card['slot'])

    def _delete_card(self, slot):
        delete_save(slot)
        self._cards = list_cards()
        if self._save_slot == slot:
            self._save_data = load_game(slot)
        self.audio.play('menu_select')

    # ── 캐릭터 생성 ────────────────────────────────────────────────────
    def _open_char_create(self, slot):
        self._create_slot   = slot
        self._create_class  = 'warrior'
        self._create_name   = ''
        self._create_skin   = 0
        self._create_hair   = 0
        self._create_haircol = 0
        self._create_sel    = 0
        self.state = 'char_create'
        self.audio.play('menu_select')

    def _create_appearance(self):
        return {'skin': self._create_skin, 'hair': self._create_hair,
                'haircol': self._create_haircol}

    def _class_locked(self, char_class) -> bool:
        from core.save_load import (ADVANCED_CLASSES, advanced_classes_unlocked,
                                    axeman_unlocked)
        if char_class == 'axeman':
            return not axeman_unlocked(self._records)
        return (char_class in ADVANCED_CLASSES
                and not advanced_classes_unlocked(self._records))

    def _do_create_character(self):
        if self._class_locked(self._create_class):
            self.messages.append((t('class_locked_blocked'), 'warn'))
            self.audio.play('player_hit')
            return
        name = (self._create_name or 'Hero').strip() or 'Hero'
        self.audio.play('menu_confirm')
        self._new_game(char_class=self._create_class, char_name=name,
                       slot=self._create_slot,
                       appearance=self._create_appearance())

    def _create_cycle(self, delta):
        """현재 선택된 행의 값을 delta 방향으로 순환."""
        from entities.avatar import cycle
        sel = self._create_sel
        if sel == 0:
            i = (CLASSES.index(self._create_class) + delta) % len(CLASSES)
            self._create_class = CLASSES[i]
        elif sel == 1:
            self._create_skin = cycle('skin', self._create_skin, delta)
        elif sel == 2:
            self._create_hair = cycle('hair', self._create_hair, delta)
        elif sel == 3:
            self._create_haircol = cycle('haircol', self._create_haircol, delta)
        else:
            return
        self.audio.play('menu_select')

    def _handle_char_create_key(self, key, unicode_ch):
        import pygame as _pg
        if key == _pg.K_ESCAPE:
            self.state = 'menu'
            self._cards = list_cards()
            return
        if key == _pg.K_LEFT:
            self._create_cycle(-1); return
        if key == _pg.K_RIGHT:
            self._create_cycle(+1); return
        if key == _pg.K_UP:
            self._create_sel = (self._create_sel - 1) % self._CREATE_ROWS; return
        if key in (_pg.K_DOWN, _pg.K_TAB):
            self._create_sel = (self._create_sel + 1) % self._CREATE_ROWS; return
        if key == _pg.K_RETURN:
            self._do_create_character(); return
        if key == _pg.K_BACKSPACE:
            self._create_name = self._create_name[:-1]; return
        # 이름 문자 입력 (영숫자/공백, 최대 12)
        if unicode_ch and unicode_ch.isprintable() and unicode_ch not in ('\t', '\r'):
            if len(self._create_name) < 12 and (unicode_ch.isalnum() or unicode_ch == ' '):
                self._create_name += unicode_ch

    def _handle_char_create_click(self, pos):
        for rect, tag in getattr(self.hud, '_char_create_buttons', []):
            if rect.collidepoint(pos):
                # row_prev:N / row_next:N — 해당 행 선택 후 순환
                if tag.startswith('row_prev:') or tag.startswith('row_next:'):
                    self._create_sel = int(tag.split(':')[1])
                    self._create_cycle(-1 if tag.startswith('row_prev') else +1)
                elif tag == 'name_field':
                    self._create_sel = 4
                elif tag == 'create':
                    self._do_create_character()
                break

    def _handle_menu_settings_action(self, action):
        typ = action['type']
        if typ == 'move':
            dy = action.get('dy', 0)
            dx = action.get('dx', 0)
            if dy != 0:
                self._menu_settings_sel = (self._menu_settings_sel + dy) % 5
                self.audio.play('menu_select')
            elif dx != 0:
                self._adjust_menu_setting(dx)
        elif typ in ('wait', 'confirm'):
            self.audio.play('menu_select')
            self._confirm_menu_setting()

    def _adjust_menu_setting(self, dx):
        step = 0.1
        if self._menu_settings_sel == 0:
            self._settings['bgm_vol'] = max(0.0, min(1.0, self._settings['bgm_vol'] + dx * step))
            if self.audio.bgm:
                self.audio.bgm.set_volume(self._settings['bgm_vol'])
            save_settings(self._settings)
        elif self._menu_settings_sel == 1:
            self._settings['sfx_vol'] = max(0.0, min(1.0, self._settings['sfx_vol'] + dx * step))
            self.audio.set_sfx_volume(self._settings['sfx_vol'])
            save_settings(self._settings)
        elif self._menu_settings_sel == 2:
            self._toggle_language()
        elif self._menu_settings_sel == 3:
            self._toggle_fullscreen()

    def _confirm_menu_setting(self):
        if self._menu_settings_sel == 2:
            self._toggle_language()
        elif self._menu_settings_sel == 3:
            self._toggle_fullscreen()
        elif self._menu_settings_sel == 4:
            self._menu_page = 'main'

    def _handle_menu_click(self, pos):
        if self._menu_page == 'settings':
            for rect, tag in self._menu_buttons:
                if rect.collidepoint(pos):
                    self._handle_menu_settings_click(tag)
                    break
            return
        if self._menu_page == 'multiplayer':
            _tag_idx = {'mp_host': 0, 'mp_join': 1, 'mp_back': 2}
            for rect, tag in self._menu_buttons:
                if rect.collidepoint(pos):
                    if tag in _tag_idx:
                        self._activate_mp_item(_tag_idx[tag])
                    break
            return
        for rect, action in self._menu_buttons:
            if rect.collidepoint(pos):
                if action.startswith('slot:'):
                    slot = int(action.split(':')[1])
                    card = next((c for c in self._cards if c['slot'] == slot), None)
                    if card:
                        self._select_card(card)
                elif action.startswith('del:'):
                    self._delete_card(int(action.split(':')[1]))
                elif action == 'test_mode' and self._test_floor is not None:
                    self.start_test_mode(self._test_floor)
                elif action == 'multiplayer':
                    self._open_multiplayer()
                elif action == 'settings':
                    self._menu_page = 'settings'
                    self._menu_settings_sel = 0
                elif action == 'quit':
                    pygame.quit(); sys.exit()
                break

    def _handle_menu_settings_click(self, tag):
        tag_to_idx = {'bgm': 0, 'sfx': 1, 'lang': 2, 'fs': 3, 'back': 4}
        if tag == 'back':
            self._menu_page = 'main'
        elif tag == 'lang':
            self._toggle_language()
        elif tag == 'fs':
            self._toggle_fullscreen()
        elif tag in tag_to_idx:
            self._menu_settings_sel = tag_to_idx[tag]

    def _handle_pause_click(self, pos):
        bw = 370; bh = 490
        bx = WINDOW_WIDTH  // 2 - bw // 2
        by = WINDOW_HEIGHT // 2 - bh // 2
        for i in range(8):
            iy = by + 56 + i * 46
            if pygame.Rect(bx+8, iy-3, bw-16, 32).collidepoint(pos):
                self._pause_sel = i
                self._confirm_pause()
                break

    # ── 인벤토리 레이아웃 헬퍼 ────────────────────────────────────────
    _INV_COLS = 5; _INV_CELL = 140; _INV_PAD = 6
    _INV_GRID_DY = 76             # 그리드 상단 오프셋 (제목 + 카테고리 탭 아래)
    _INV_CATS = ('all', 'equip', 'consume', 'gather')
    _EQUIP_TYPES = ('weapon', 'armor', 'head', 'off_hand', 'accessory',
                    'boots', 'feet')

    def _inv_layout(self):
        pw = self._INV_COLS * self._INV_CELL + self._INV_PAD * 2
        ph = self._INV_GRID_DY + 4 * self._INV_CELL + self._INV_PAD * 2 + 60
        bx = WINDOW_WIDTH  // 2 - pw // 2
        by = WINDOW_HEIGHT // 2 - ph // 2
        return pw, ph, bx, by

    def _item_category(self, item):
        """아이템 → 카테고리('equip'/'consume'/'gather')."""
        cat = self._item_data.get(getattr(item, 'key', ''), {}).get('category')
        if cat in ('equip', 'consume', 'gather'):
            return cat
        if item.item_type in self._EQUIP_TYPES:
            return 'equip'
        return 'consume'

    def _inv_view(self, cat=None):
        """현재(또는 지정) 카테고리 탭에 해당하는 실제 인벤 인덱스 리스트.
        '전체'는 카테고리 순(장비→소모품→채집품)으로 정렬해 보여준다."""
        if not self.player:
            return []
        cat = self._INV_CATS[self._inv_cat] if cat is None else cat
        inv = self.player.inventory
        if cat == 'all':
            order = {'equip': 0, 'consume': 1, 'gather': 2}
            return sorted(range(len(inv)),
                          key=lambda i: (order.get(self._item_category(inv[i]), 3), i))
        return [i for i in range(len(inv)) if self._item_category(inv[i]) == cat]

    def _inv_cat_counts(self):
        """카테고리별 보유 개수 {equip,consume,gather} (탭 배지용)."""
        counts = {'equip': 0, 'consume': 0, 'gather': 0}
        if self.player:
            for it in self.player.inventory:
                counts[self._item_category(it)] += 1
        return counts

    def _inv_real_idx(self, view_pos):
        """뷰(격자) 위치 → 실제 인벤 인덱스 (범위 밖이면 None)."""
        view = self._inv_view()
        return view[view_pos] if 0 <= view_pos < len(view) else None

    def _inv_tab_rects(self):
        """카테고리 탭 사각형 4개 (전체/장비/소모품/채집품) — 클릭 판정 공용."""
        pw, ph, bx, by = self._inv_layout()
        tw = (pw - self._INV_PAD * 2) // 4
        ty, th = by + 42, 26
        return [pygame.Rect(bx + self._INV_PAD + i * tw, ty, tw - 4, th)
                for i in range(4)]

    def _inv_set_cat(self, cat_idx):
        if cat_idx != self._inv_cat:
            self._inv_cat = cat_idx % len(self._INV_CATS)
            self._inv_sel = 0
            self.audio.play('menu_select')

    def _inv_slot_at(self, pos):
        _, _, bx, by = self._inv_layout()
        gx = bx + self._INV_PAD; gy = by + self._INV_GRID_DY
        for i in range(self.player.max_inventory if self.player else 20):
            sx = gx + (i % self._INV_COLS) * self._INV_CELL
            sy = gy + (i // self._INV_COLS) * self._INV_CELL
            if pygame.Rect(sx, sy, self._INV_CELL-2, self._INV_CELL-2).collidepoint(pos):
                return i
        return None

    def _inv_trash_rect(self):
        pw, ph, bx, by = self._inv_layout()
        return pygame.Rect(bx + pw - 130, by + ph - 42, 122, 34)

    def _discard_inventory_item(self, idx):
        inv = self.player.inventory
        if not (0 <= idx < len(inv)):
            return
        item = inv[idx]
        for eq in self.player.equipment.values():
            if eq is item:
                item.unequip(self.player)
                break
        inv.pop(idx)
        self._inv_sel = min(self._inv_sel, max(0, len(inv) - 1))
        self.messages.append((t('item_discard', item.name), 'info'))
        self.audio.play('use_item')

    def _start_discard_confirm(self, idx):
        if self.player and 0 <= idx < len(self.player.inventory):
            self._inv_confirm_idx = idx

    def _inv_confirm_rects(self):
        cw, ch = 300, 112
        cx = WINDOW_WIDTH  // 2 - cw // 2
        cy = WINDOW_HEIGHT // 2 - ch // 2
        yes_rect = pygame.Rect(cx + 20,        cy + ch - 46, 118, 34)
        no_rect  = pygame.Rect(cx + cw - 138,  cy + ch - 46, 118, 34)
        panel    = pygame.Rect(cx, cy, cw, ch)
        return panel, yes_rect, no_rect

    def _handle_inventory_click(self, pos):
        # 카테고리 탭 클릭 우선
        for ci, r in enumerate(self._inv_tab_rects()):
            if r.collidepoint(pos):
                self._inv_set_cat(ci)
                return
        i = self._inv_slot_at(pos)
        if i is None:
            return
        view = self._inv_view()
        if i >= len(view):
            return
        real = view[i]
        if i == self._inv_sel:
            self._do_use_inventory_item(self.player.inventory[real])
            self._inv_sel = min(self._inv_sel, max(0, len(self._inv_view()) - 1))
        else:
            self._inv_sel = i

    def _handle_equipment_click(self, pos):
        SW, SH = 110, 54; pw = 520; ph = 516
        bx = WINDOW_WIDTH  // 2 - pw // 2
        by = WINDOW_HEIGHT // 2 - ph // 2
        char_cx = bx + pw // 2
        char_cy = by + 218
        offsets = [(-SW//2, -128), (-SW//2, +48), (+76, -SH//2),
                   (-186, -SH//2), (-SW//2, +122), (-SW//2, +190)]
        for i, (dx, dy) in enumerate(offsets):
            if pygame.Rect(char_cx+dx, char_cy+dy, SW, SH).collidepoint(pos):
                if i == self._equip_sel:
                    slot = self._EQUIP_SLOTS[i]
                    item = self.player.equipment.get(slot)
                    if item:
                        msg = item.unequip(self.player)
                        if msg:
                            self.messages.append((msg, 'info'))
                            self.audio.play('use_item')
                else:
                    self._equip_sel = i
                break

    def _handle_pause_action(self, action):
        act = action['type']
        if act == 'move':
            dy = action.get('dy', 0)
            dx = action.get('dx', 0)
            if dy != 0:
                self._pause_sel = (self._pause_sel + dy) % 8
            elif dx != 0:
                self._adjust_pause_setting(dx)
        elif act in ('wait', 'confirm'):
            self._confirm_pause()

    def _adjust_pause_setting(self, dx):
        step = 0.1
        if self._pause_sel == 2:   # BGM
            self._settings['bgm_vol'] = max(0.0, min(1.0, self._settings['bgm_vol'] + dx*step))
            if self.audio.bgm:
                self.audio.bgm.set_volume(self._settings['bgm_vol'])
            save_settings(self._settings)
        elif self._pause_sel == 3:  # SFX
            self._settings['sfx_vol'] = max(0.0, min(1.0, self._settings['sfx_vol'] + dx*step))
            self.audio.set_sfx_volume(self._settings['sfx_vol'])
            save_settings(self._settings)
        elif self._pause_sel == 4:  # 전체화면
            self._toggle_fullscreen()
        elif self._pause_sel == 5:  # 언어
            self._toggle_language()

    def _confirm_pause(self):
        if self._pause_sel == 0:
            self.state = 'playing'
        elif self._pause_sel == 1:   # 저장하기
            if self.player and not self._is_test_mode:
                save_game(self.player, self.floor, self.skills, self._unlocked_combos, self._skill_books,
                          self._skill_levels, self._skill_xp, self._skill_points,
                          self._equipped_skills, self._skill_enchants, self._quests,
                          self._max_floor_reached, slot=self._save_slot,
                          name=getattr(self,'_char_name','Hero'),
                          char_class=getattr(self,'_char_class','warrior'))
                self.messages.append((t('saved'), 'good'))
                self.audio.play('save')
            self.state = 'playing'
        elif self._pause_sel == 4:
            self._toggle_fullscreen()
        elif self._pause_sel == 5:
            self._toggle_language()
        elif self._pause_sel == 6:
            self.state           = 'menu'
            self._menu_sel       = 0
            self._menu_page      = 'main'
            self._cards          = list_cards()
            self._save_data      = load_game(self._save_slot)
        elif self._pause_sel == 7:
            pygame.quit(); sys.exit()

    def _toggle_language(self):
        from core.lang import next_lang
        from core import fonts
        cur = self._settings.get('language', 'en')
        self._settings['language'] = next_lang(cur)
        set_lang(self._settings['language'])
        save_settings(self._settings)
        # 언어별 폰트 재생성 (ja/zh는 시스템 CJK 폰트로 전환)
        fonts.clear_cache()
        self.hud.reload_fonts()
        self.animator.reload_fonts()
        self.vfx_loot.reload_fonts()
        self._combo_font = None
        self._quest_clear_font = None
        self._font_burning_big   = fonts.load_font(28, bold=True)
        self._font_burning_small = fonts.load_font(13)

    def _toggle_fullscreen(self):
        self._settings['fullscreen'] = not self._settings['fullscreen']
        if self._settings['fullscreen']:
            flags = pygame.FULLSCREEN | pygame.SCALED
        else:
            flags = 0
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        save_settings(self._settings)

    def _handle_shop_action(self, action):
        t = action['type']
        if t == 'use_item':
            self._buy_item(action['slot'])
        elif t in ('move', 'wait', 'confirm'):
            self.state = 'playing'
            if t == 'move':
                self._process(action)

    def _handle_inventory_action(self, action):
        t = action['type']
        inv = self.player.inventory
        cols = 5
        view = self._inv_view()
        if t == 'move':
            dx, dy = action.get('dx', 0), action.get('dy', 0)
            # 좌우 끝에서 좌우 이동 → 카테고리 탭 전환
            if dx and not dy:
                col = self._inv_sel % cols
                if (dx < 0 and col == 0) or (dx > 0 and (col == cols - 1
                                             or self._inv_sel + 1 >= max(1, len(view)))):
                    self._inv_set_cat((self._inv_cat + (1 if dx > 0 else -1))
                                      % len(self._INV_CATS))
                    return
            limit = max(0, len(view) - 1)
            self._inv_sel = max(0, min(limit, self._inv_sel + dx + dy * cols))
        elif t in ('confirm', 'wait', 'attack'):
            if self._inv_sel < len(view):
                self._do_use_inventory_item(inv[view[self._inv_sel]])
                self._inv_sel = min(self._inv_sel, max(0, len(self._inv_view()) - 1))

    # ------------------------------------------------------------------ #
    def _try_enemy_drop(self, enemy, force=False):
        import random
        from map.generator import drop_pool
        from entities.item import Item

        is_boss = getattr(enemy, 'is_boss', False)
        # 엘리트는 70% 드랍 (일반 28%) — 위험을 감수할 이유
        drop_chance = 0.70 if getattr(enemy, 'elite', None) else 0.28
        if not is_boss and not force and random.random() >= drop_chance:
            return

        pool = drop_pool(self.floor)
        if not pool:
            return
        key = random.choice(pool)
        if key not in self._item_data:
            return

        d = dict(self._item_data[key])
        d['key'] = key
        # 같은 타일에 아이템이 겹치면 이름 팝업/글리프가 뭉개짐 → 인접 타일로 산개
        dx, dy = enemy.x, enemy.y
        if self.dungeon.get_item_at(dx, dy):
            neighbors = [(dx+ox, dy+oy) for ox, oy in
                         ((0,-1),(0,1),(-1,0),(1,0),(-1,-1),(1,-1),(-1,1),(1,1))]
            random.shuffle(neighbors)
            for nx, ny in neighbors:
                if (self.dungeon.is_walkable(nx, ny)
                        and not self.dungeon.get_item_at(nx, ny)):
                    dx, dy = nx, ny
                    break
        it = Item(dx, dy, d)
        self.dungeon.items.append(it)          # 상태: 즉시 배치 (밟으면 바로 픽업)
        self.vfx_loot.spawn_drop(it)            # 연출: 등급별 reveal + 자석

    # 슬롯 순서: head=0, body=1, weapon=2, off_hand=3, accessory=4
    _EQUIP_SLOTS = ['head', 'body', 'weapon', 'off_hand', 'accessory', 'feet']
    # (up, down, left, right) → 이동할 슬롯 인덱스 (None = 이동 불가)
    _EQUIP_NAV = {
        0: (None, 1,    3,    2),
        1: (0,    4,    3,    2),
        2: (0,    4,    1,    None),
        3: (0,    4,    None, 1),
        4: (1,    5,    3,    2),
        5: (4,    None, None, None),
    }

    def _handle_equipment_action(self, action):
        t = action['type']
        if t == 'move':
            dx = action.get('dx', 0)
            dy = action.get('dy', 0)
            nav = self._EQUIP_NAV.get(self._equip_sel, (None, None, None, None))
            if dy < 0:    nxt = nav[0]
            elif dy > 0:  nxt = nav[1]
            elif dx < 0:  nxt = nav[2]
            elif dx > 0:  nxt = nav[3]
            else:         nxt = None
            if nxt is not None:
                self._equip_sel = nxt
        elif t in ('confirm', 'wait', 'attack'):
            slot = self._EQUIP_SLOTS[self._equip_sel]
            item = self.player.equipment.get(slot)
            if item:
                msg = item.unequip(self.player)
                if msg:
                    self.messages.append((msg, 'info'))
                    self.audio.play('use_item')

    # ------------------------------------------------------------------ #
    def _process(self, action):
        acted = False
        if   action['type'] == 'move':     acted = self._player_move(action['dx'], action['dy'])
        elif action['type'] == 'wait':     acted = True
        elif action['type'] == 'attack':   acted = self._player_basic_attack()
        elif action['type'] == 'use_item': acted = self._use_item(action['slot'])
        elif action['type'] == 'skill':       acted = self._use_skill(action['skill'])
        elif action['type'] == 'combo_skill': acted = self._use_combo_skill(action['combo'])
        elif action['type'] == 'ultimate':    acted = self._use_ultimate(action['key'])
        if acted:
            if not self._in_town and not self._is_test_mode and not self._collapse_active:
                self.dungeon.update_visibility(self.player.x, self.player.y)
            self.camera.center_on(self.player.x, self.player.y)

    def _player_move(self, dx, dy):
        nx, ny = self.player.x + dx, self.player.y + dy
        if   dx > 0: self._facing = 'right'
        elif dx < 0: self._facing = 'left'
        elif dy > 0: self._facing = 'down'
        elif dy < 0: self._facing = 'up'
        self._walk_frame ^= 1

        enemy = self.dungeon.get_enemy_at(nx, ny)
        if enemy:
            if self._atk_cd_timer > 0:
                return False  # 쿨다운 중: 이동 범프 공격 불가
            if self.player.char_class == 'archer':
                return self._archer_shoot()          # 궁수는 근접 범프도 사격
            if self.player.char_class == 'mage':
                return self._mage_cast()             # 마법사는 근접 범프도 마법 볼트
            return self._chain_attack(dx, dy, enemy)  # 범프도 콤보 체인에 합류
        target_tile = self.dungeon.tiles[ny][nx]

        # 버닝 스테이지 문
        if target_tile.tile_type == TileType.BURNING_DOOR:
            self._enter_burning_stage()
            return True

        # 벽 문: 이동 전에 처리 (blocked=False지만 사실상 벽 안쪽)
        if target_tile.tile_type == TileType.DOOR:
            self.audio.play('stairs')
            if self._collapse_active:
                self._resolve_collapse_escape()
            if self.floor >= MAX_FLOOR:
                self._records = update_records(self.floor, self._run_kills, self.player.gold)
                if not self._records.get('game_cleared', False):
                    # ── 최초 999 클리어 → 마스터 정산 + 엔딩 크레딧 (세이브 유지) ──
                    self._record_theme_clear_for(self.floor)
                    self._check_game_complete()   # game_cleared=True, 보상 지급
                    self.messages.append((t('victory'), 'good'))
                    self._credits_scroll = 0.0
                    self.state = 'credits'
                    self.audio.play('levelup_big')
                else:
                    # ── 엔들리스 심연: 999층 너머로 계속 하강 ──
                    self._grant_floor_clear_reward(self.floor)
                    self.floor += 1
                    self._abyss_reward()
                    self._start_fade(self._load_floor)
            else:
                # 테마 구간 경계를 넘으면(예: 50→51) 방금 완수한 테마 +1
                if theme_index(self.floor + 1) > theme_index(self.floor):
                    self._record_theme_clear_for(self.floor)
                self._grant_floor_clear_reward(self.floor)
                self.floor += 1
                if not self._is_test_mode:
                    self.achievements.check_floor(self.floor)
                self._start_fade(self._load_floor)
            return True

        # 잠긴 금고문 — 열쇠가 있으면 개방(턴 소모), 없으면 막힘
        if target_tile.tile_type == TileType.LOCKED_DOOR:
            return self._try_open_vault(nx, ny)

        if not self.dungeon.is_walkable(nx, ny):
            return False

        # 이동 슬라이딩: 현재 오프셋에 새 방향을 누적 (클램프)
        self._move_anim_offset[0] = max(-TILE_SIZE, min(TILE_SIZE, self._move_anim_offset[0] - dx * TILE_SIZE))
        self._move_anim_offset[1] = max(-TILE_SIZE, min(TILE_SIZE, self._move_anim_offset[1] - dy * TILE_SIZE))

        self.player.x, self.player.y = nx, ny
        # 도끼맨: 던져진 도끼 위에 올라서면 회수 (마을 포함 어디서나)
        if self._thrown_axe is not None and (nx, ny) == (self._thrown_axe['x'], self._thrown_axe['y']):
            self._retrieve_axe()
        item = self.dungeon.get_item_at(nx, ny)
        if item:
            self._pickup(item)
        if not self._in_town:
            self._on_enter_tile(nx, ny)     # 트랩·압력판 발동

        # ── 포탈 밟기: 마을 ↔ 던전 ──────────────────────────────────
        if self._in_town:
            if self._town and (nx, ny) == self._town.portal_pos:
                if self.net is not None:
                    # co-op: 호스트만 던전 입장을 개시(파티 최저 층). 클라는 대기.
                    if self.net.is_host:
                        self._coop_begin_dungeon()
                    else:
                        self.messages.append((t('coop_host_only'), 'info'))
                    return True
                self._start_fade(self._return_from_town)
                return True
        elif (nx, ny) == getattr(self.dungeon, 'town_portal_pos', None):
            self._start_fade(self._enter_town)
            return True

        tile = self.dungeon.tiles[ny][nx]
        if tile.tile_type == TileType.SHOP and self.dungeon.has_shop:
            self.state = 'shop'
            self.audio.play('shop_open')
            return True

        return True

    _DIRS = {'right': (1, 0), 'left': (-1, 0), 'down': (0, 1), 'up': (0, -1)}
    _DIR_NAME = {(1, 0): 'right', (-1, 0): 'left', (0, 1): 'down', (0, -1): 'up'}

    def _held_move_dir(self):
        """현재 눌려 있는 방향키 (커맨드 액션 판정용). 없으면 None."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_KP8]:    return (0, -1)
        if keys[pygame.K_DOWN] or keys[pygame.K_KP2]:  return (0, 1)
        if keys[pygame.K_LEFT] or keys[pygame.K_KP4]:  return (-1, 0)
        if keys[pygame.K_RIGHT] or keys[pygame.K_KP6]: return (1, 0)
        return None

    def _snapshot_player(self):
        """잔상용 현재 플레이어 실루엣 스냅샷."""
        if self._USE_AVATAR:
            from entities.avatar import draw_avatar_tile
            tmp = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            draw_avatar_tile(tmp, 0, 0, self._facing, self._walk_frame, 0,
                             getattr(self.player, 'appearance', None),
                             self.player.char_class)
            return tmp
        tmp = pygame.Surface((TILE_SIZE, TILE_SIZE))
        tmp.fill(_CKEY); tmp.set_colorkey(_CKEY)
        draw_player(tmp, 0, 0, self._facing, self._walk_frame)
        return tmp

    def _spawn_afterimage(self, x, y):
        self.animator.add(AfterimageAnim(self._snapshot_player(), x, y))

    # ── 스태미나 SP: 공격 자원 (남발하면 지친다) ──────────────────────
    _STAMINA_COST = {'slash': 10, 'finisher': 14, 'lunge': 18,
                     'backstep': 14, 'combo_skill': 25}
    _STAMINA_REGEN_DELAY = 900   # 마지막 소모 후 회복 시작까지 ms

    def _spend_stamina(self, cost: float) -> bool:
        """스태미나 소모 시도. 부족하면 탈진 피드백 후 False.

        레벨·장비 SP 경감(total_sp_reduce)이 모든 소모에 일괄 적용된다.
        """
        p = self.player
        cost *= (1.0 - p.total_sp_reduce)
        if p.stamina < cost:
            now = pygame.time.get_ticks()
            if now - self._last_exhaust_msg > 1500:
                self._last_exhaust_msg = now
                self.messages.append((t('exhausted'), 'warn'))
                self.animator.add(CalloutAnim(p.x, p.y, '...',
                                              (200, 200, 140)))
            self.audio.play('exhaust')
            return False
        p.stamina -= cost
        self._stamina_delay_ms = self._STAMINA_REGEN_DELAY
        return True

    # ── 기본 공격: 3단 콤보 체인 + 방향키 커맨드 ──────────────────────
    _CHAIN_MUL   = (1.0, 1.1, 1.6)     # 단계별 데미지 배율
    _CHAIN_CD    = (1.0, 0.82, 1.25)   # 단계별 쿨다운 배율
    _CHAIN_VAR   = ('slash1', 'slash2', 'finisher')
    _CHAIN_WINDOW_MS = 900

    def _player_basic_attack(self):
        """Space: 커맨드 판정 → 3단 콤보 체인.

        - 방향키(전방) + Space  : 런지 스러스트 (전진 관통)
        - 방향키(후방) + Space  : 백스텝 슬래시 (베고 이탈)
        - 방향키(측면) + Space  : 그쪽으로 방향 전환 후 체인
        - Space 연타            : 베기 → 역베기 → 피니셔
        """
        if self._atk_cd_timer > 0:
            return False  # 쿨다운 중
        held = self._held_move_dir()
        if self.player.char_class == 'archer':
            if held:
                self._facing = self._DIR_NAME[held]
            return self._archer_shoot()
        if self.player.char_class == 'mage':
            if held:
                self._facing = self._DIR_NAME[held]
            return self._mage_cast()
        # 라그나로크 발동 중: 도끼맨 휘두르기가 중거리 광역으로 확장
        if self.player.char_class == 'axeman' and self._ragnarok_ms > 0:
            if held:
                self._facing = self._DIR_NAME[held]
            return self._ragnarok_swing()
        fdx, fdy = self._DIRS.get(self._facing, (0, 1))
        if held:
            if held == (fdx, fdy):
                return self._cmd_lunge()
            if held == (-fdx, -fdy):
                return self._cmd_backstep()
            # 측면: 방향 전환 후 일반 체인
            self._facing = self._DIR_NAME[held]
            fdx, fdy = held
        return self._chain_attack(fdx, fdy)

    # ── 궁수 기본 사격 (원거리 히트스캔 + 화살 연출) ────────────────────
    _ARCHER_RANGE = 8

    def _archer_shoot(self):
        if not self._spend_stamina(self._STAMINA_COST['slash']):
            return False
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        self._atk_variant = 'shoot'
        self._trigger_atk_anim()                 # 활 당김 → 발사 프레임
        end = (self.player.x, self.player.y)
        hit = None
        for i in range(1, self._ARCHER_RANGE + 1):
            cx, cy = self.player.x + dx * i, self.player.y + dy * i
            if not self.dungeon.in_bounds(cx, cy) or self.dungeon.tiles[cy][cx].block_sight:
                break
            end = (cx, cy)
            e = self.dungeon.get_enemy_at(cx, cy)
            if e:
                hit = e
                break
        self.animator.add(ArrowAnim(self.player.x, self.player.y,
                                    end[0], end[1], self._facing))
        self.audio.play('bow_shoot')
        if hit:
            self._player_attack(hit)
        self._atk_cd_timer = self.player.atk_cooldown_ms
        return True

    # ── 마법사 기본 마법 볼트 (원거리 히트스캔 + 점화 DoT) ─────────────
    _MAGE_RANGE = 7
    _MAGE_BOLT_COL = (150, 110, 245)

    def _mage_cast(self):
        if not self._spend_stamina(self._STAMINA_COST['slash']):
            return False
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        self._atk_variant = 'cast'
        self._trigger_atk_anim()
        end = (self.player.x, self.player.y)
        hit = None
        for i in range(1, self._MAGE_RANGE + 1):
            cx, cy = self.player.x + dx * i, self.player.y + dy * i
            if not self.dungeon.in_bounds(cx, cy) or self.dungeon.tiles[cy][cx].block_sight:
                break
            end = (cx, cy)
            e = self.dungeon.get_enemy_at(cx, cy)
            if e:
                hit = e
                break
        self.animator.add(MagicBoltAnim(self.player.x, self.player.y,
                                        end[0], end[1], self._facing,
                                        self._MAGE_BOLT_COL))
        self.audio.play('bow_shoot')
        if hit:
            self._player_attack(hit)
            # 기본 볼트도 약한 점화(DoT) 부여 — 마법사 정체성
            self._apply_burn(hit, dps=max(2, self.player.total_attack // 3),
                             ms=2500, col=self._MAGE_BOLT_COL)
        self._atk_cd_timer = self.player.atk_cooldown_ms
        return True

    def _apply_burn(self, enemy, dps: int, ms: int, col=(150, 110, 245)):
        """적에게 점화/중독(DoT) 부여 — 더 강한 dps로 갱신(중첩 아님, 최댓값)."""
        if enemy is None or not enemy.is_alive():
            return
        if getattr(enemy, 'burn_ms', 0) <= 0 or dps >= getattr(enemy, 'burn_dps', 0):
            enemy.burn_dps = dps
            enemy.burn_col = col
        enemy.burn_ms = max(getattr(enemy, 'burn_ms', 0), ms)

    def _chain_attack(self, dx, dy, enemy=None):
        """3단 콤보 본체 (Space 공격·이동 범프 공격 공용)."""
        step = self._chain_step if self._chain_window_ms > 0 else 0
        cost = self._STAMINA_COST['finisher' if step == 2 else 'slash']
        if not self._spend_stamina(cost):
            return False
        is_axe = self.player.char_class == 'axeman'
        variant = ('axe1', 'axe2', 'axefin')[step] if is_axe else self._CHAIN_VAR[step]
        self._atk_variant = variant
        self._trigger_atk_anim()

        if enemy is None:
            enemy = self.dungeon.get_enemy_at(self.player.x + dx,
                                              self.player.y + dy)
        finisher = (step == 2)
        if is_axe:
            smear_col = (255, 130, 55) if finisher else (255, 175, 90)
        else:
            smear_col = (255, 190, 90) if finisher else (255, 240, 180)
        self.animator.add(SmearAnim(
            self.player.x, self.player.y, self._facing, variant, smear_col))
        if is_axe:
            # 도끼 스윙 주위 — 흙먼지 + 충격파(묵직한 무게감)
            px, py = self.player.x, self.player.y
            ix, iy = px + dx, py + dy
            self.animator.particles.emit_death(ix, iy, (150, 135, 108))   # 흙먼지 퍼짐
            self.animator.add(ShockwaveAnim(ix, iy, color=(210, 190, 150),
                                            rmax=2.0 if finisher else 1.4,
                                            dur=380 if finisher else 300))
            if finisher:
                self.animator.particles.emit_death(px, py, (150, 135, 108))
                self._start_shake(4, 170)
        if enemy:
            self._player_attack(enemy, dmg_mul=self._CHAIN_MUL[step])
            if finisher:
                self._finisher_impact(enemy, dx, dy)
        else:
            self.audio.play('finisher' if finisher else 'swing')

        self._atk_cd_timer = self.player.atk_cooldown_ms * self._CHAIN_CD[step]
        self._chain_step = (step + 1) % 3
        self._chain_window_ms = self._CHAIN_WINDOW_MS
        return True

    def _finisher_impact(self, enemy, dx, dy):
        """피니셔 적중 — 넉백 + 경직 + 임팩트 프레임 + 충격파."""
        if enemy.is_alive():
            nx, ny = enemy.x + dx, enemy.y + dy
            if (self.dungeon.is_walkable(nx, ny)
                    and not self.dungeon.get_enemy_at(nx, ny)
                    and (nx, ny) != (self.player.x, self.player.y)):
                ox, oy = enemy.x, enemy.y
                enemy.x, enemy.y = nx, ny
                enemy._slide_from(ox, oy)
            enemy.staggered_ms = max(enemy.staggered_ms, 500)
        self.animator.particles.emit_power_hit(enemy.x, enemy.y)
        self._white_flash_ms = 55            # 임팩트 프레임
        self._hitstop_ms = max(self._hitstop_ms, 90)
        self._start_shake(4, 180)
        self.audio.play('finisher')
        # 강타 시너지: 인접 균열 벽 파괴 (전사 근접 채굴감)
        if self._break_cracked_walls_near(enemy.x, enemy.y, 1):
            self.messages.append((t('bomb_wall_break', 1), 'good'))

    # ── 커맨드: 런지 스러스트 (전방키 + Space) ────────────────────────
    def _cmd_lunge(self):
        if not self._spend_stamina(self._STAMINA_COST['lunge']):
            return False
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        sx, sy = self.player.x, self.player.y
        self._atk_variant = 'lunge'
        self._trigger_atk_anim()
        self._spawn_afterimage(sx, sy)
        # 1타일 전진 (막히면 제자리)
        nx, ny = sx + dx, sy + dy
        if (self.dungeon.is_walkable(nx, ny)
                and not self.dungeon.get_enemy_at(nx, ny)):
            self.player.x, self.player.y = nx, ny
            self._move_anim_offset[0] -= dx * TILE_SIZE
            self._move_anim_offset[1] -= dy * TILE_SIZE
            item = self.dungeon.get_item_at(nx, ny)
            if item:
                self._pickup(item)
        # 전방 2타일 관통 (1.3배)
        hit = 0
        for i in (1, 2):
            e = self.dungeon.get_enemy_at(self.player.x + dx * i,
                                          self.player.y + dy * i)
            if e:
                self._player_attack(e, dmg_mul=1.3)
                hit += 1
        self.animator.add(ThrustSmearAnim(self.player.x, self.player.y,
                                          self._facing))
        self.audio.play('lunge' if hit == 0 else 'crit')
        self._atk_cd_timer = self.player.atk_cooldown_ms * 1.5
        # 런지는 체인 스타터: 바로 2타로 이어진다
        self._chain_step = 1
        self._chain_window_ms = self._CHAIN_WINDOW_MS
        return True

    # ── 커맨드: 백스텝 슬래시 (후방키 + Space) ────────────────────────
    def _cmd_backstep(self):
        if not self._spend_stamina(self._STAMINA_COST['backstep']):
            return False
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        sx, sy = self.player.x, self.player.y
        self._atk_variant = 'backstep'
        self._trigger_atk_anim()
        self.animator.add(SmearAnim(sx, sy, self._facing, 'backstep',
                                    (180, 235, 255)))
        enemy = self.dungeon.get_enemy_at(sx + dx, sy + dy)
        if enemy:
            self._player_attack(enemy, dmg_mul=1.15)
        else:
            self.audio.play('swing')
        # 1타일 후퇴 (히트앤런) + 잔상
        bx, by = sx - dx, sy - dy
        if (self.dungeon.is_walkable(bx, by)
                and not self.dungeon.get_enemy_at(bx, by)):
            self._spawn_afterimage(sx, sy)
            self.player.x, self.player.y = bx, by
            self._move_anim_offset[0] += dx * TILE_SIZE
            self._move_anim_offset[1] += dy * TILE_SIZE
            item = self.dungeon.get_item_at(bx, by)
            if item:
                self._pickup(item)
        self.audio.play('skill_dash')
        self._atk_cd_timer = self.player.atk_cooldown_ms * 1.2
        return True

    def _do_use_inventory_item(self, item):
        """인벤토리 화면에서 선택한 아이템 사용/장착."""
        if item not in self.player.inventory and item.equip_slot is None:
            return
        if item.effect == 'teleport':
            if item in self.player.inventory:
                self.player.inventory.remove(item)
            self._use_teleport()
        elif item.effect == 'town_portal':
            if self._in_town:
                return
            if item in self.player.inventory:
                self.player.inventory.remove(item)
            self._spawn_town_portal()
            self.state = 'playing'             # 인벤 닫고 포탈 확인
        elif item.effect == 'repair':
            if item in self.player.inventory:
                self.player.inventory.remove(item)
            self._use_repair_kit()
        elif item.effect == 'whirlwind':
            if item in self.player.inventory:
                self.player.inventory.remove(item)
            self._skill_whirl(no_cooldown=True)
        elif item.effect == 'seed':
            self._plant_seed(item)
        elif item.equip_slot:
            msg = item.use(self.player)
            self.messages.append((msg, 'good'))
            self._equip_burst(item)
            self.audio.play('use_item')
        else:
            if item in self.player.inventory:
                self.player.inventory.remove(item)
            self.messages.append((item.use(self.player), 'good'))
            self.audio.play('use_item')

    def _plant_seed(self, item):
        """씨앗 아이템 사용 — 서 있는 빈 밭칸에 해당 작물을 심는다."""
        from core.save_load import save_records
        crop = self._SEED_CROP.get(item.key)
        idx = (self._town.farm_plot_at(self.player.x, self.player.y)
               if (self._in_town and self._town) else None)
        if crop is None or idx is None:
            self.messages.append((t('seed_need_plot'), 'warn'))
            self.audio.play('no_gold')
            return
        farm = self._town.farm
        plot = farm[idx]
        if plot.get('crop'):
            self.messages.append((t('seed_plot_taken'), 'warn'))
            self.audio.play('no_gold')
            return
        from core.town import FARM_GROW_MAX
        plot['crop'] = crop; plot['watered'] = False
        plot['stage'] = FARM_GROW_MAX if self._is_test_mode else 0  # 테스트: 즉시 수확
        farm[idx] = plot
        self._records['farm'] = farm
        if item in self.player.inventory:
            self.player.inventory.remove(item)
        if not self._is_test_mode:
            save_records(self._records)
        self.messages.append((t('farm_planted', t('crop_' + crop)), 'good'))
        self.animator.particles.emit_heal(self.player.x, self.player.y)
        self.audio.play('use_item')
        self.state = 'playing'                 # 인벤 닫고 밭 확인

    def _player_attack(self, enemy, dmg_mul=1.0):
        # 두려움: 명중률 40%
        if getattr(self.player, 'feared_ms', 0) > 0 and random.random() > 0.4:
            self.messages.append((t('fear_miss'), 'bad'))
            return
        crit = random.random() < 0.1
        # 체인 단계/커맨드 배율 + 드라이브 캔슬 보너스(+15%)
        if self._cancel_bonus_ms > 0:
            dmg_mul *= 1.15
        dmg = max(1, int(roll_damage(self.player.total_attack, enemy.defense)
                         * dmg_mul))
        # 타격 시 드라이브 소폭 회복
        self.player.drive = min(self.player.drive_max, self.player.drive + 0.15)
        # 무기 내구도: 적중할 때마다 -1 (헛스윙은 안 닳음)
        wpn = self.player.equipment.get('weapon')
        if wpn and wpn.max_durability > 0 and wpn.durability > 0:
            wpn.durability -= 1
            if wpn.durability <= 0:
                self.player.just_broken.append(wpn)
        if crit:
            dmg *= 2
            self.messages.append((t('crit_hit', enemy.name, dmg), 'warn'))
        else:
            self.messages.append((t('normal_hit', enemy.name, dmg), 'warn'))
        enemy.take_damage(dmg)
        enemy.on_hurt(self.player.x, self.player.y)
        self._apply_lifesteal(dmg)
        if crit:
            self.juice.crit()
        else:
            self.juice.hit()
        self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (255, 80, 80), crit=crit))
        self.animator.particles.emit_basic_hit(enemy.x, enemy.y)
        self.audio.play('crit' if crit else 'attack')
        if not enemy.is_alive():
            self._on_enemy_killed(enemy)

    # ── 도전과제 헬퍼 (테스트 모드에서는 잠금) ─────────────────────────
    def _on_achievement_unlocked(self, api_name):
        self.messages.append((t('ach_unlock', t('ach_' + api_name)), 'good'))
        self.audio.play('levelup')

    def _ach_unlock(self, api_name):
        if not self._is_test_mode:
            self.achievements.unlock(api_name)

    def _ach_stat(self, stat, amount=1):
        if not self._is_test_mode:
            self.achievements.add_stat(stat, amount)

    def _on_enemy_killed(self, enemy):
        # 프롭(항아리/나무상자): 파괴 연출 + 콤보 유지 + 소소한 보상 후 종료
        if enemy.is_prop:
            self.animator.add(DeathAnim(enemy.x, enemy.y,
                                        self._enemy_sprite_fn(enemy.key),
                                        enemy.color, False))
            self.animator.particles.emit_death(enemy.x, enemy.y, enemy.color)
            self.juice.kill()
            self._bump_kill_combo()
            self._on_prop_broken(enemy)
            return
        gold = int(enemy.gold_drop * self._gold_mult)   # NG+ 영구 골드 배율
        self._run_kills += 1
        # 펫 강화석 드롭 (해금 후): 일반 3% · 보스/엘리트 30%
        if self.player.is_pet_unlocked:
            drop_p = 0.30 if (enemy.is_boss or enemy.elite) else 0.03
            if random.random() < drop_p:
                self.player.pet_stones += 1
                self.animator.add(CalloutAnim(enemy.x, enemy.y, '+STONE', (185, 150, 255)))
                self.messages.append((t('pet_stone_drop', self.player.pet_stones), 'good'))
        # 처치 SP 회복: 일반 15% / 엘리트 30% / 보스 전량 — 전투를 이어가는 연료
        pct = 1.0 if enemy.is_boss else (0.30 if enemy.elite else 0.15)
        self.player.stamina = min(self.player.stamina_max,
                                  self.player.stamina + self.player.stamina_max * pct)
        # 사망 연출: 시체 잔상 + 적 색 파편 버스트 + 히트스톱 + 흔들림
        self.animator.add(DeathAnim(enemy.x, enemy.y,
                                    self._enemy_sprite_fn(enemy.key),
                                    enemy.color, enemy.is_boss))
        self.animator.particles.emit_death(enemy.x, enemy.y, enemy.color)
        self.juice.kill(boss=enemy.is_boss)
        # 폭발 엘리트: 사망 시 1칸 폭발 — 인접 처치의 리스크
        if enemy.elite == 'volatile':
            self.animator.particles.emit_fireball_hit(enemy.x, enemy.y)
            self._start_shake(5, 220)
            if abs(self.player.x - enemy.x) + abs(self.player.y - enemy.y) <= 1:
                dmg = roll_damage(enemy.attack, self.player.total_defense, 1.2)
                self.player.take_damage(dmg)
                self._hurt_flash_ms = 260
                self.animator.add(HitFlashAnim(self.player.x, self.player.y, dmg, (255,120,40)))
                self.messages.append((t('volatile_boom', enemy.name, dmg), 'bad'))
            else:
                self.messages.append((t('volatile_boom_safe', enemy.name), 'warn'))
        # 처치 연쇄 + 티어 승급 (프롭 파괴와 공유)
        self._bump_kill_combo()
        # 오버킬: 초과 피해가 최대 HP의 1.5배 이상 (4초 쿨다운, 보스 제외)
        now = pygame.time.get_ticks()
        if (not enemy.is_boss
                and getattr(enemy, 'last_overkill', 0) >= enemy.max_hp * 1.5
                and now - self._last_overkill_t > 4000):
            self._last_overkill_t = now
            self.animator.add(BannerAnim('OVERKILL!', (255, 95, 40),
                                         y=140, size=26, duration_ms=900))
            self.animator.particles.emit_power_hit(enemy.x, enemy.y)
            self.audio.play('crit')
            self.juice.overkill()
        # 퀘스트 진행 (kill_any / kill_key)
        self._quest_on_kill(enemy)
        # 도전과제
        self._ach_stat('kills')
        if enemy.elite:
            self._ach_stat('elite_kills')
        if enemy.is_boss:
            self._ach_stat('boss_kills')
            self._ach_unlock('ACH_FIRST_BOSS')
        if self._combo_count >= 15:
            self._ach_unlock('ACH_COMBO_15')
        if self.player.gold + (gold or 0) >= 2000:
            self._ach_unlock('ACH_RICH')
        if gold:
            self.player.gold += gold                      # 상태: 즉시 지급
            self.vfx_loot.spawn_gold(enemy.x, enemy.y, gold)  # 연출: 코인 산탄→흡입
            self.animator.add(GoldPopAnim(enemy.x, enemy.y, gold))
            self.messages.append((t('kill_gold', enemy.name, enemy.xp_value, gold), 'good'))
        else:
            self.messages.append((t('kill', enemy.name, enemy.xp_value), 'good'))
        if self.player.gain_xp(enemy.xp_value):
            self._skill_points += 3
            if self.player.level >= 20:
                self._ach_unlock('ACH_LEVEL_20')
            self.messages.append((t('levelup', self.player.level), 'good'))
            self.messages.append((t('sp_gained', self._skill_points), 'info'))
            # 레벨업 셀레브레이션 — 배너 + 황금 분수 + 골든 플래시 + 히트스톱
            self.animator.add(BannerAnim(f"LEVEL UP!  Lv.{self.player.level}",
                                         (255, 226, 110), y=104, size=30))
            self.animator.particles.emit_levelup(self.player.x, self.player.y)
            self.juice.levelup()
            self.audio.play('levelup_big')
            for cid, cdef in COMBO_SKILL_DEFS.items():
                slv_req = cdef.get('skill_level_req', 1)
                if (cid in self._skill_books and
                        cid not in self._unlocked_combos and
                        self.player.level >= cdef['level_req'] and
                        all(self._skill_levels.get(self._equipped_skills.get(k, ''), 1) >= slv_req for k in cid)):
                    self._unlocked_combos.add(cid)
                    _nm = combo_def(cid, self.player.char_class)['name']
                    self.messages.append((t('combo_unlock', _nm), 'good'))
        self.dungeon.enemies.remove(enemy)
        # 드라마틱 마무리 슬로모션: 보스 막타 / 층의 마지막 몬스터
        if enemy.is_boss:
            self.juice.slowmo(500, 0.2)
        elif (not self._burning_active
              and not any(e.is_alive() and not e.is_prop and not e.flee
                          for e in self.dungeon.enemies)):
            self.juice.slowmo(350, 0.3)
        self._check_boss_cleared()
        # ── 아이템 드랍 ───────────────────────────────────────────
        if enemy.key == 'treasure_goblin':
            # 잭팟! — 골드 2연타 + 확정 드랍 3개 + 슬로모
            self.animator.add(BannerAnim('JACKPOT!', (255, 215, 70), size=36))
            self.vfx_loot.spawn_gold(enemy.x, enemy.y, 60)   # 추가 코인 비주얼
            self.audio.play('loot_r3')
            self.juice.slowmo(400, 0.25)
            for _ in range(3):
                self._try_enemy_drop(enemy, force=True)
        else:
            self._try_enemy_drop(enemy)

    # ── 처치 연쇄 (몬스터·프롭 공용): 카운트 + 피치 래더 + 티어 배너 ──
    def _bump_kill_combo(self):
        prev_tier = self._combo_tier(self._combo_count)
        self._combo_count += 1
        self._combo_ms = 4000
        self.audio.play_combo(self._combo_count)   # 킬마다 한 음씩 상승
        if self._combo_count >= 2:
            # 연쇄 보너스: 스태미나 SP 추가 회복 (콤보가 공격 지속력을 만든다)
            bonus = min(self._combo_count, 8)
            self.player.stamina = min(self.player.stamina_max,
                                      self.player.stamina + bonus)
            if self._combo_count % 5 == 0:
                self.messages.append((t('combo_kill', self._combo_count, bonus), 'good'))
        new_tier = self._combo_tier(self._combo_count)
        if new_tier and new_tier != prev_tier:
            _, tier_name, tier_color = new_tier
            self.animator.add(BannerAnim(tier_name, tier_color))
            self.animator.particles.emit_combo_tier(
                self.player.x, self.player.y, tier_color)
            self.audio.play('tier_up')
            self.juice.tier_up()

    # ── 프롭 파괴 (항아리/나무상자): 소소하지만 즉각적인 보상 ─────────
    def _on_prop_broken(self, prop):
        self.player.stamina = min(self.player.stamina_max,
                                  self.player.stamina + 5)   # 소량 SP 회복
        gold = int(prop.gold_drop * self._gold_mult)     # NG+ 영구 골드 배율
        if gold:
            self.player.gold += gold                          # 상태: 즉시 지급
            self.vfx_loot.spawn_gold(prop.x, prop.y, gold)    # 연출: 코인 산탄
            self.messages.append((t('prop_break_gold', prop.name, gold), 'good'))
        else:
            self.messages.append((t('prop_break', prop.name), 'info'))
        # 18% 확률 물약 서프라이즈 (등급 reveal 연출 포함)
        if random.random() < 0.18:
            from entities.item import Item
            key = 'large_health_potion' if random.random() < 0.25 else 'health_potion'
            d = dict(self._item_data[key]); d['key'] = key
            it = Item(prop.x, prop.y, d)
            self.dungeon.items.append(it)
            self.vfx_loot.spawn_drop(it)
        self.dungeon.enemies.remove(prop)

    def _pickup(self, item):
        if item.effect == 'vault_key':
            self._keys += 1
            self.dungeon.remove_item(item)
            self.messages.append((t('key_pickup'), 'good'))
            self.animator.add(CalloutAnim(self.player.x, self.player.y,
                                          t('key_get'), (245, 210, 80)))
            self.animator.particles.emit_levelup(self.player.x, self.player.y)
            self.audio.play('pickup')
            return
        if item.effect == 'enhance_stone':
            self.player.enhance_stones += 1
            self.dungeon.remove_item(item)
            self.messages.append((t('enhance_stone_pickup', self.player.enhance_stones), 'good'))
            self.audio.play('pickup')
            return
        if item.effect == 'unlock_combo':
            combo_id = str(item.value)
            cdef = combo_def(combo_id, self.player.char_class)
            self.dungeon.remove_item(item)
            self.audio.play('pickup')
            if cdef:
                self._skill_books.add(combo_id)
                slv_req = cdef.get('skill_level_req', 1)
                level_ok = self.player.level >= cdef['level_req']
                skill_ok = all(self._skill_levels.get(self._equipped_skills.get(k, ''), 1) >= slv_req for k in combo_id)
                if level_ok and skill_ok:
                    self._unlocked_combos.add(combo_id)
                    self.messages.append((t('combo_unlock', cdef['name']), 'good'))
                elif not level_ok:
                    self.messages.append((t('combo_need_level', item.name, cdef['level_req']), 'warn'))
                else:
                    self.messages.append((t('combo_need_skill_level', item.name, slv_req), 'warn'))
            return
        if len(self.player.inventory) < self.player.max_inventory:
            self.player.inventory.append(item)
            self.dungeon.remove_item(item)
            self.messages.append((t('pickup', item.name), 'good'))
            self.audio.play('pickup')
        else:
            self.messages.append((t('inv_full'), 'warn'))

    def _use_item(self, slot):
        if slot >= len(self.player.inventory):
            return False
        item = self.player.inventory[slot]
        if item.equip_slot:
            # 장비 아이템: equip이 인벤토리 이동을 직접 처리
            msg = item.use(self.player)
            self.messages.append((msg, 'good'))
            self._equip_burst(item)
            self.audio.play('use_item')
        elif item.effect == 'teleport':
            self.player.inventory.pop(slot)
            self._use_teleport()
        elif item.effect == 'town_portal':
            if self._in_town:
                return False                   # 마을에서는 사용 불가
            self.player.inventory.pop(slot)
            self._spawn_town_portal()
        elif item.effect == 'repair':
            self.player.inventory.pop(slot)
            self._use_repair_kit()
        elif item.effect == 'whirlwind':
            self.player.inventory.pop(slot)
            self._skill_whirl(no_cooldown=True)
        elif item.effect == 'bomb':
            if self._in_town:
                return False               # 마을에선 사용 불가
            self.player.inventory.pop(slot)
            self._throw_bomb()
        else:
            self.player.inventory.pop(slot)
            self.messages.append((item.use(self.player), 'good'))
            self.audio.play('use_item')
        return True

    # ═════════════════ 마을 시스템 ═══════════════════════════════════
    def _spawn_town_portal(self, x=None, y=None):
        """귀환 포탈 생성 — 주문서 사용 또는 보스 클리어 시."""
        if self._in_town:
            return
        px = x if x is not None else self.player.x
        py = y if y is not None else self.player.y
        self.dungeon.town_portal_pos = (px, py)
        # 연출: 포탈 개방 버스트 (자리: 여기에 히트스톱/사운드 추가 가능)
        self.animator.particles.emit_combo_tier(px, py, (170, 110, 255))
        self.audio.play('teleport')
        self.messages.append((t('portal_open'), 'good'))

    def _enter_town(self):
        """포탈 진입: 던전 세션(맵·적·좌표) 임시 저장 → 마을 전환.

        인벤토리 세션 분리 규칙: 소지품(dungeon_inventory)은 마을에
        무사히 도착하는 순간 영구 창고(permanent)로 이전 — 이후 사망해도
        창고(storage.json)는 유지된다.
        """
        from core.town import TownScene, TOWN_THEME, TOWN_W, TOWN_H
        from core.camera import Camera
        if self._town is None:
            self._town = TownScene()
        self._town.home_style = int(self._records.get('home_style', 0))   # 내 집 인테리어
        self._town.trophies = int(self._records.get('max_boss_floor', 0)) // 5  # 보스 전리품(보스층 수)
        # 농장: 재방문할 때마다 심은 작물이 한 단계 성장
        from core.town import FARM_GROW_MAX as _FGM
        farm = self._farm_state()
        for plot in farm:                       # 물 준 작물만 한 단계 성장(물 소모)
            if plot.get('crop') and plot.get('stage', 0) < _FGM and plot.get('watered'):
                plot['stage'] = plot.get('stage', 0) + 1
                plot['watered'] = False
        self._records['farm'] = farm
        self._town.farm = farm
        # 목장: 재방문할 때마다 먹이 준 가축이 한 단계 성장(먹이 소모)
        from core.town import RANCH_FEED_MAX as _RFM
        ranch = self._ranch_state()
        for pen in ranch:
            if pen.get('animal') and pen.get('stage', 0) < _RFM and pen.get('fed'):
                pen['stage'] = pen.get('stage', 0) + 1
                pen['fed'] = False
        self._records['ranch'] = ranch
        self._town.ranch = ranch
        # ① 던전 세션 저장 (객체 참조 보존 — 적 위치/맵/층 무손실)
        self._dungeon_session = {
            'dungeon': self.dungeon,
            'floor': self.floor,
            'px': self.player.x, 'py': self.player.y,
            'theme': self._theme,
            'respawn_max': self._respawn_max,
        }
        # ② 소지품 → 영구 창고 이전 (Transfer)
        moved = self._deposit_all_to_storage()
        # ③ 씬 전환
        self._in_town = True
        self.vfx_loot.clear()
        self.dungeon = self._town.dungeon
        self._theme = TOWN_THEME
        self.player.x, self.player.y = self._town.spawn_pos
        # 넓어진 마을 크기에 맞춘 카메라 (기존 것은 복귀 시 복원)
        self._saved_camera = self.camera
        self.camera = Camera(TOWN_W, TOWN_H)
        self.camera.center_on(self.player.x, self.player.y)
        self._apply_map_fx()        # 마을은 정적 (지진/왜곡 없음)
        self.messages.append((t('town_enter'), 'good'))
        if moved:
            self.messages.append((t('town_deposit', moved), 'info'))
        self.audio.play('stairs')
        # 방 입장 시 자기 프로필 브로드캐스트 (스텁 · 미래 멀티플레이 결합점)
        self._broadcast_user_profile()

    # ── 층 클리어 보상: 던전 증표 + 직업 장비 보급 ──────────────────────
    _TOKEN_CYCLE = ('guard', 'atk', 'haste')   # floor % 3 → 증표 종류
    _CLASS_GEAR = {
        'warrior': ['broad_sword', 'great_sword', 'chain_mail', 'plate_armor',
                    'mythril_armor', 'iron_shield', 'tower_shield', 'knight_helm',
                    'war_pendant'],
        'archer':  ['sword', 'broad_sword', 'swift_boots', 'shadow_boots',
                    'leather_armor', 'mythril_armor', 'iron_helm', 'magic_stone',
                    'silver_ring'],
        'mage':    ['apprentice_staff', 'arcane_staff', 'leather_armor',
                    'mythril_armor', 'leather_boots', 'magic_stone', 'silver_ring',
                    'war_pendant', 'leather_helm'],
        'axeman':  ['battle_axe', 'great_axe', 'chain_mail', 'plate_armor',
                    'mythril_armor', 'iron_helm', 'knight_helm', 'war_pendant',
                    'iron_boots'],
    }

    def _grant_floor_clear_reward(self, cleared_floor):
        """한 층을 클리어(다음 층 문 통과)할 때마다 보상.

        · 던전 증표 +1 (종류는 층에 따라 순환) — 소지 시 패시브 스탯 상승
        · 10층마다 직업별 장비 보급
        """
        p = self.player
        if p is None:
            return
        if not hasattr(p, 'tokens') or p.tokens is None:
            p.tokens = {'atk': 0, 'haste': 0, 'guard': 0}
        kind = self._TOKEN_CYCLE[cleared_floor % 3]
        p.tokens[kind] = p.tokens.get(kind, 0) + 1
        # 알림 스팸 방지: 5층마다 현재 증표 보너스 요약만 표시
        if cleared_floor % 5 == 0:
            self.messages.append((t('token_gain_sum', p.token_atk, p.token_def,
                                     int(p.token_aspd * 100)), 'info'))
            # 보스층 클리어 → 내 집 전리품 진열 (최고 보스층 갱신)
            if cleared_floor > int(self._records.get('max_boss_floor', 0)):
                self._records['max_boss_floor'] = cleared_floor
                if not self._is_test_mode:
                    from core.save_load import save_records
                    save_records(self._records)
        # 직업별 장비 보급 (10층마다)
        if cleared_floor % 10 == 0:
            self._grant_class_gear(cleared_floor)
        # 상급 직업(궁수·마법사) 해금: 전사 Lv20 · 20층 클리어
        self._check_class_unlock(cleared_floor)

    def _check_class_unlock(self, cleared_floor):
        """직업 해금: 전사 Lv20·20층 → 궁수·마법사 / (직업무관) Lv30·40층 → 도끼맨."""
        from core.save_load import (UNLOCK_LEVEL, UNLOCK_FLOOR, save_records)
        if self._is_test_mode:
            return
        rec = self._records
        if (not rec.get('classes_unlocked')
                and self.player.char_class == 'warrior'
                and self.player.level >= UNLOCK_LEVEL
                and cleared_floor >= UNLOCK_FLOOR):
            rec['classes_unlocked'] = True
            save_records(rec)
            self.messages.append((t('classes_unlocked_msg'), 'good'))
            self.animator.add(BannerAnim(t('classes_unlocked_banner'),
                                         (170, 130, 245), size=28))
            self.audio.play('levelup_big')
        # 도끼맨(4번째 클래스): 직업 무관 Lv30 + 40층 클리어 시 해금
        from core.save_load import AXEMAN_UNLOCK_LEVEL, AXEMAN_UNLOCK_FLOOR
        if (not rec.get('axeman_unlocked')
                and self.player.level >= AXEMAN_UNLOCK_LEVEL
                and cleared_floor >= AXEMAN_UNLOCK_FLOOR):
            rec['axeman_unlocked'] = True
            save_records(rec)
            self.messages.append((t('axeman_unlocked_msg'), 'good'))
            self.animator.add(BannerAnim(t('axeman_unlocked_banner'),
                                         (220, 120, 60), size=28))
            self.audio.play('levelup_big')

    def _grant_class_gear(self, floor):
        """직업에 맞는 무기/방어구 1개를 깊이에 맞춰 강화된 상태로 지급."""
        from entities.item import Item
        p = self.player
        cls = getattr(p, 'char_class', 'warrior')
        pool = [k for k in self._CLASS_GEAR.get(cls, self._CLASS_GEAR['warrior'])
                if k in self._item_data]
        if not pool:
            return
        key = random.choice(pool)
        d = dict(self._item_data[key])
        d['key'] = key
        d['enhance_level'] = min(18, floor // 50)
        it = Item(0, 0, d)
        if len(p.inventory) < p.max_inventory:
            p.inventory.append(it)
            self.messages.append((t('class_gear_grant', it.name), 'good'))
        else:
            # 인벤 가득 → 강화석 +2로 보상 전환 (바닥 드롭은 층 전환으로 소실되므로)
            p.enhance_stones += 2
            self.messages.append((t('class_gear_full', it.name), 'good'))

    # ── 정복 일지 / 마스터 정산 ─────────────────────────────────────────
    def _record_theme_clear_for(self, floor):
        """해당 층이 속한 테마 구간을 1회 완수 처리 (기록 누적).

        테스트 모드에서는 격리된 *_test.json 에 기록된다(use_test_data).
        """
        idx = theme_index(floor)
        self._records = record_theme_clear(idx, self._records)

    def _check_game_complete(self):
        """999층 최종 클리어 감지 → 영구 보상 지급 (최초 1회 강제)."""
        first_time = not self._records.get('game_cleared', False)
        # 칭호 해금 + NG+ 회차 증가 (반복 클리어도 NG+는 누적)
        self._records = grant_master_completion(self._records)
        self._grant_endgame_weapon()
        self._gold_mult = ng_plus_gold_mult(self._records)   # 즉시 반영
        self._title_badge = True
        self._broadcast_user_profile()
        self.messages.append((t('master_complete'), 'good'))
        self.messages.append((t('title_unlock', t('title_abyss_sovereign')), 'good'))
        self.messages.append((t('ngplus_on', int(self._gold_mult * 100)), 'good'))
        if first_time:
            self.animator.particles.emit_levelup(self.player.x, self.player.y)
        self.audio.play('levelup_big')

    def _grant_endgame_weapon(self):
        """종결 무기 [심연의 파쇄곤]을 영구 창고에 지급 (중복 방지)."""
        if any(e.get('key') == 'abyss_maul' for e in self._storage):
            return
        if len(self._storage) >= self._storage_cap:
            self._storage_cap += 1        # 보상은 용량 초과해도 반드시 지급
        self._storage.append({'key': 'abyss_maul',
                              'enhance_level': 0, 'durability': 999999})
        save_storage(self._storage, self._storage_cap)
        self.messages.append((t('endgame_weapon_grant'), 'good'))

    def _broadcast_user_profile(self):
        """USER_PROFILE 패킷 구성 후 네트워크 스텁으로 브로드캐스트."""
        name = getattr(self, '_char_name', None) or getattr(self.player, 'char_name', 'Hero')
        prof = build_user_profile(name, self._records)
        self._net.broadcast_profile(prof)

    # ── 엔딩 크레딧 / 엔들리스 심연 ──────────────────────────────────
    def _update_credits(self, dt):
        self._credits_scroll += dt * 0.05          # px/ms
        if self._credits_scroll > self.hud.credits_height():
            self._finish_credits()

    def _finish_credits(self):
        """크레딧 종료 → 마을로 (엔들리스 심연 재도전 거점)."""
        self.messages.append((t('credits_done'), 'good'))
        self.state = 'playing'
        self._enter_town()

    def _abyss_reward(self):
        """엔들리스 심연 각 층 진입 보상 — 강화석·펫석·골드."""
        self.player.enhance_stones += 2
        if getattr(self.player, 'is_pet_unlocked', False):
            self.player.pet_stones += 1
        self.player.gold += int(400 * self._gold_mult)
        self.messages.append((t('abyss_descend', self.floor), 'good'))
        self.animator.add(BannerAnim(t('abyss_banner', self.floor),
                                     (180, 90, 240), size=30))

    def _open_journal(self):
        self._journal_return_state = self.state
        self.state = 'journal'
        self.audio.play('menu_select')

    def _close_journal(self):
        self.state = getattr(self, '_journal_return_state', 'playing')

    # ── 펫 시스템 ────────────────────────────────────────────────────────
    def _attach_pet(self):
        """플레이어 데이터로 활성 Pet 객체 (재)생성. 미해금이면 None."""
        p = self.player
        if p and getattr(p, 'is_pet_unlocked', False):
            self._pet = Pet(p.pet_type, p.pet_level)
            self._pet.snap_to(p.x, p.y)
            self._pet_trail = [(p.x, p.y)]      # 경로 초기화
            p.active_pet = self._pet
        else:
            self._pet = None
            self._pet_trail = []
            if p:
                p.active_pet = None

    def _toggle_pet(self):
        """펫 소환/해제 토글 (V키). 미해금이면 안내만."""
        p = self.player
        if not (p and p.is_pet_unlocked):
            self.messages.append((t('pet_locked'), 'info'))
            self.audio.play('player_hit')
            return
        if self._pet is None:
            self._attach_pet()
            self.messages.append((t('pet_summoned', t(PET_META[p.pet_type]['name_key'])), 'good'))
            self.animator.particles.emit_levelup(p.x, p.y)
            self.audio.play('levelup')
        else:
            self._pet = None
            self._pet_trail = []
            p.active_pet = None
            self.messages.append((t('pet_dismissed'), 'info'))
            self.audio.play('menu_select')

    def _update_pet_trail(self):
        """플레이어가 새 타일로 이동할 때마다 경로에 기록.

        인접 1칸 이동은 경로에 추가(펫이 그 길을 밟음), 대시/텔레포트 등
        비인접 점프는 경로를 리셋하고 펫을 순간이동시켜 벽 통과를 막는다.
        """
        p = self.player
        trail = self._pet_trail
        cur = (p.x, p.y)
        if not trail:
            trail.append(cur); return
        if trail[-1] == cur:
            return
        if abs(cur[0] - trail[-1][0]) + abs(cur[1] - trail[-1][1]) == 1:
            trail.append(cur)
            if len(trail) > 48:
                trail.pop(0)
                if self._pet:
                    self._pet._ti = max(0, self._pet._ti - 1)
        else:                                    # 대시/전이 — 경로 리셋
            trail.clear(); trail.append(cur)
            if self._pet:
                self._pet.snap_to(p.x, p.y)

    def unlock_pet(self, pet_type='attack'):
        """펫 해금 트리거 — 기본 펫 지급 (20층 퀘스트 완료 시 호출)."""
        p = self.player
        if not p or p.is_pet_unlocked:
            return False
        p.is_pet_unlocked = True
        p.pet_type = pet_type if pet_type in PET_TYPES else 'attack'
        p.pet_level = 1
        self._attach_pet()
        self.messages.append((t('pet_unlocked', t(PET_META[p.pet_type]['name_key'])), 'good'))
        self.animator.particles.emit_levelup(p.x, p.y)
        self.audio.play('levelup')
        return True

    # 능력 콜백 (Pet._activate 에서 호출) ─────────────────────────────────
    def _pet_buff(self, pct, dur_ms):
        p = self.player
        p.atk_bonus_pct = max(getattr(p, 'atk_bonus_pct', 0.0), pct)
        p.atk_bonus_ms  = max(getattr(p, 'atk_bonus_ms', 0), dur_ms)
        self.animator.particles.emit_combo_tier(p.x, p.y, (255, 225, 120))

    def _pet_debuff(self, enemy, slow_pct, dur_ms):
        enemy.slowed_ms = max(getattr(enemy, 'slowed_ms', 0), dur_ms)
        enemy.slow_pct  = max(getattr(enemy, 'slow_pct', 0.0), slow_pct)
        self.animator.add(HitFlashAnim(enemy.x, enemy.y, 0, (170, 140, 255)))
        self.animator.particles.emit_combo_tier(enemy.x, enemy.y, (170, 140, 255))

    def _pet_attack(self, pet, enemy):
        dmg = max(1, int(self._skill_atk * pet.atk_coeff))
        self.animator.add(BoltAnim(pet.x, pet.y, enemy.x, enemy.y, (255, 150, 120)))
        self.audio.play('skill_dash')
        enemy.take_damage(dmg)
        self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (255, 150, 120)))
        self.animator.particles.emit_basic_hit(enemy.x, enemy.y)
        if not enemy.is_alive():
            self._on_enemy_killed(enemy)

    # 펫 상태창 / 강화 ────────────────────────────────────────────────────
    def _open_pet_status(self):
        if not (self.player and self.player.is_pet_unlocked):
            self.messages.append((t('pet_locked'), 'info'))
            return
        self._pet_return_state = self.state
        self.state = 'pet'
        self.audio.play('menu_select')

    def _close_pet_status(self):
        self.state = getattr(self, '_pet_return_state', 'playing')

    def _cycle_pet_type(self, delta):
        """펫 타입 전환 (상태창에서 ←→). 레벨/강화석은 유지."""
        p = self.player
        if not (p and p.is_pet_unlocked):
            return
        i = (PET_TYPES.index(p.pet_type) + delta) % len(PET_TYPES)
        p.pet_type = PET_TYPES[i]
        self._attach_pet()
        self.audio.play('menu_select')

    def upgrade_pet(self):
        """골드+강화석 소모 → 성공 확률에 따라 펫 레벨/계수 상승."""
        p = self.player
        if not (p and p.is_pet_unlocked and self._pet):
            return False
        gold_cost, stone_cost = self._pet.next_cost()
        if p.pet_stones < stone_cost:
            self.messages.append((t('pet_need_stones', stone_cost), 'warn')); return False
        if p.gold < gold_cost:
            self.messages.append((t('pet_need_gold', gold_cost), 'warn')); return False
        p.pet_stones -= stone_cost
        p.gold       -= gold_cost
        if random.random() < self._pet.success_chance():
            p.pet_level += 1
            self._attach_pet()
            self.messages.append((t('pet_upgrade_ok', p.pet_level), 'good'))
            self.animator.particles.emit_levelup(p.x, p.y)
            self.audio.play('enhance_success' if False else 'levelup')
        else:
            self.messages.append((t('pet_upgrade_fail'), 'warn'))
            self.audio.play('menu_select')
        return True

    def _handle_pet_key(self, key):
        """펫 상태창 입력 (ESC는 액션 파이프라인이 처리)."""
        import pygame as _pg
        if key == _pg.K_b:
            self._close_pet_status()
        elif key in (_pg.K_LEFT, _pg.K_a):
            self._cycle_pet_type(-1)
        elif key in (_pg.K_RIGHT, _pg.K_d):
            self._cycle_pet_type(1)
        elif key in (_pg.K_u, _pg.K_RETURN):
            self.upgrade_pet()

    def _return_from_town(self):
        """마을 포탈 재진입: 저장해 둔 던전 세션 복원 (사냥터 그 자리)."""
        s = self._dungeon_session
        self._in_town = False
        # 마을 진입 시 저장한 던전 카메라 복원
        if getattr(self, '_saved_camera', None) is not None:
            self.camera = self._saved_camera
            self._saved_camera = None
        if s:
            self.dungeon = s['dungeon']
            self.floor   = s['floor']
            self._theme  = s['theme']
            self._respawn_max = s['respawn_max']
            self.player.x, self.player.y = s['px'], s['py']
            self._dungeon_session = None
            if not self._is_test_mode:
                self.dungeon.update_visibility(self.player.x, self.player.y)
            self.camera.center_on(self.player.x, self.player.y)
            self._apply_map_fx()        # 복귀한 층의 지진/왜곡 재적용
            self.messages.append((t('town_return', self.floor), 'good'))
            self.audio.play('teleport')
        else:
            # 세션 없음 (마을에서 시작한 경우) → 현재 층 새로 생성
            self._load_floor()

    # 스택 가능(개수 누적) 아이템 타입 — 소모품·스킬북·강화석 등 동일 아이템
    _STACK_TYPES = {'consumable', 'skillbook', 'enhance_stone'}

    def _storage_add(self, key, enhance_level=0, durability=None) -> bool:
        """창고에 아이템 1개 추가 — 스택 가능 아이템은 같은 칸에 개수로 누적.
        반환: True(추가/누적) / False(칸 가득)."""
        stackable = (self._item_data.get(key, {}).get('type') in self._STACK_TYPES
                     and not enhance_level)
        if stackable:
            for e in self._storage:
                if (e.get('key') == key and not e.get('enhance_level')
                        and 'durability' not in e):
                    e['count'] = e.get('count', 1) + 1
                    return True
            if len(self._storage) >= self._storage_cap:
                return False
            self._storage.append({'key': key, 'enhance_level': 0, 'count': 1})
            return True
        if len(self._storage) >= self._storage_cap:
            return False
        e = {'key': key, 'enhance_level': enhance_level}
        if durability is not None:
            e['durability'] = durability
        self._storage.append(e)
        return True

    def _inv_group_view(self):
        """소지품을 스택 가능 아이템끼리 묶은 뷰 (창고 UI 표시/이동 공용).
        각 원소: {'item': 대표 Item, 'count': 개수, 'indices': [인벤 인덱스…]}."""
        groups = []
        sig_to_idx = {}
        for idx, it in enumerate(self.player.inventory):
            stackable = (self._item_data.get(it.key, {}).get('type') in self._STACK_TYPES
                         and not it.enhance_level)
            if stackable and it.key in sig_to_idx:
                g = groups[sig_to_idx[it.key]]
                g['count'] += 1
                g['indices'].append(idx)
            else:
                if stackable:
                    sig_to_idx[it.key] = len(groups)
                groups.append({'item': it, 'count': 1, 'indices': [idx]})
        return groups

    def _deposit_all_to_storage(self) -> int:
        """소지품 전량을 영구 창고로 이전하고 저장. 이전 개수 반환."""
        from core.save_load import save_storage
        moved = 0
        for it in list(self.player.inventory):
            if not self._storage_add(it.key, it.enhance_level, it.durability):
                self.messages.append((t('storage_cap_full'), 'warn'))
                break
            self.player.inventory.remove(it)
            moved += 1
        if moved:
            save_storage(self._storage, self._storage_cap)
        return moved

    def _storage_transfer(self):
        """창고 UI: 선택 항목을 반대편으로 이동 (즉시 디스크 저장)."""
        from core.save_load import save_storage
        from entities.item import Item
        if self._storage_pane == 0:                       # 소지품 → 창고 (묶음에서 1개)
            groups = self._inv_group_view()
            if not groups:
                return
            gi = min(self._storage_cursor, len(groups) - 1)
            g = groups[gi]
            it = g['item']
            if not self._storage_add(it.key, it.enhance_level, it.durability):
                self.messages.append((t('storage_cap_full'), 'warn'))
                return
            self.player.inventory.pop(g['indices'][0])     # 묶음에서 한 개 이동
            self.audio.play('pickup')
        else:                                             # 창고 → 소지품 (스택에서 1개)
            if not self._storage:
                return
            if len(self.player.inventory) >= self.player.max_inventory:
                self.messages.append((t('inv_full'), 'warn'))
                return
            i = min(self._storage_cursor, len(self._storage) - 1)
            entry = self._storage[i]
            key = entry.get('key', '')
            if key in self._item_data:
                d = dict(self._item_data[key])
                d['key'] = key
                d['enhance_level'] = entry.get('enhance_level', 0)
                if 'durability' in entry:
                    d['durability'] = entry['durability']
                self.player.inventory.append(Item(0, 0, d))
            cnt = entry.get('count', 1)                    # 스택은 1개씩 인출
            if cnt > 1:
                entry['count'] = cnt - 1
            else:
                self._storage.pop(i)
            self.audio.play('pickup')
        save_storage(self._storage, self._storage_cap)    # 영구 반영
        self._storage_cursor = max(0, self._storage_cursor - 0)

    def _handle_storage_action(self, action):
        ty = action['type']
        # 소지품 패널은 묶음(그룹) 기준으로 커서 이동
        cur_len = (len(self._inv_group_view()) if self._storage_pane == 0
                   else len(self._storage))
        if ty == 'move':
            if action.get('dx'):
                self._storage_pane ^= 1
                self._storage_cursor = 0
            elif action.get('dy'):
                if cur_len:
                    self._storage_cursor = ((self._storage_cursor + action['dy'])
                                            % cur_len)
        elif ty in ('confirm', 'attack'):                 # Enter/Space 이동
            self._storage_transfer()

    def _town_interact(self):
        """마을에서 E: 인접 NPC 상호작용."""
        npc = self._town.npc_near(self.player.x, self.player.y) if self._town else None
        _INTERACT_IDS = ('chest', 'inn', 'merchant', 'smith', 'home_board',
                         'home_chest', 'altar', 'angler')
        interactive = npc and (npc['id'] in _INTERACT_IDS or 'quest' in npc)
        if not interactive:
            # 상호작용 NPC가 없으면 밭칸 위에서 E → 농사 팝업 / 강둑에서 E → 낚시
            if self._town:
                idx = self._town.farm_plot_at(self.player.x, self.player.y)
                pen = self._town.pen_at(self.player.x, self.player.y)
                if idx is not None:
                    self._farm_menu_plot = idx
                    self._farm_menu_idx = 0
                    self.state = 'farm_menu'
                    self.audio.play('menu_select')
                elif pen is not None:
                    self._open_ranch_menu(pen)
                elif self._town.water_adjacent(self.player.x, self.player.y):
                    self._open_fishing()
            return
        if npc['id'] == 'chest':
            self._storage_cursor = 0
            self._storage_pane = 0
            self.state = 'storage'
            self.audio.play('shop_open')
        elif npc['id'] == 'inn':
            self.state = 'inn'
            self.audio.play('shop_open')
        elif npc['id'] == 'merchant':
            self.dungeon.shop_items = self._make_town_stock()
            self.state = 'shop'
            self.audio.play('shop_open')
        elif npc['id'] == 'smith':
            # 대장장이: 골드 소모 강화 (기존 강화 패널 재사용)
            self._enhance_mode = 'gold'
            self._enhance_open = True
            self._enhance_cursor = 0
            self.audio.play('shop_open')
        elif npc['id'] == 'home_board':
            self._cycle_home_style()
        elif npc['id'] == 'home_chest':
            # 내 집 보관함 — 창고 시스템 공유 (같은 스태시, 최대 100)
            self._storage_cursor = 0
            self._storage_pane = 0
            self.state = 'storage'
            self.audio.play('shop_open')
        elif npc['id'] == 'altar':
            self._open_altar()
        elif npc['id'] == 'angler':
            self._open_angler()
        elif 'quest' in npc:
            self._open_quest_dialog(npc['id'])

    def _farm_state(self):
        """records의 밭 상태 리스트를 정규화해 반환 (길이/형식 보정)."""
        from core.town import FARM_PLOTS
        farm = self._records.get('farm')
        if not isinstance(farm, list) or len(farm) != len(FARM_PLOTS):
            farm = [{'crop': None, 'stage': 0} for _ in FARM_PLOTS]
        for i in range(len(farm)):
            if not isinstance(farm[i], dict):
                farm[i] = {'crop': None, 'stage': 0}
        return farm

    # ── 목장 팝업 메뉴 (가축 구입 / 먹이주기 / 수확 / 처분) ────────────────
    def _ranch_state(self):
        """records의 목장 상태 리스트를 정규화해 반환."""
        from core.town import RANCH_PENS
        ranch = self._records.get('ranch')
        if not isinstance(ranch, list) or len(ranch) != len(RANCH_PENS):
            ranch = [{'animal': None, 'fed': False, 'stage': 0} for _ in RANCH_PENS]
        for i in range(len(ranch)):
            if not isinstance(ranch[i], dict):
                ranch[i] = {'animal': None, 'fed': False, 'stage': 0}
        return ranch

    def _pen_ready(self, pen):
        """생산물 수확 가능 여부 — 테스트 모드면 가축만 있으면 즉시."""
        from core.town import RANCH_FEED_MAX
        if not pen.get('animal'):
            return False
        return self._is_test_mode or pen.get('stage', 0) >= RANCH_FEED_MAX

    def _open_ranch_menu(self, pen_idx):
        self._ranch_menu_pen = pen_idx
        self._ranch_menu_idx = 0
        self.state = 'ranch_menu'
        self.audio.play('menu_select')

    def _ranch_options(self, pen):
        """빈 우리 → 가축 구입 목록 / 가축 있음 → 먹이·수확·처분."""
        if not pen.get('animal'):
            return [{'act': 'buy', 'animal': k, 'cost': c, 'prod': p, 'gold': g}
                    for (k, c, p, g) in self.LIVESTOCK]
        return [{'act': a} for a in self.RANCH_ACTIONS]

    def _ranch_action_enabled(self, pen, opt):
        act = opt['act']
        if act == 'buy':
            return self.player.gold >= opt['cost']
        if act == 'feed':
            return (bool(pen.get('animal')) and not self._pen_ready(pen)
                    and not pen.get('fed'))
        if act == 'collect':
            return self._pen_ready(pen)
        if act == 'sell':
            return bool(pen.get('animal'))
        return False

    def _handle_ranch_menu_action(self, action):
        ty = action['type']
        pen = self._town.ranch[self._ranch_menu_pen]
        opts = self._ranch_options(pen)
        if ty == 'move':
            d = action.get('dy') or action.get('dx')
            if d:
                self._ranch_menu_idx = (self._ranch_menu_idx + d) % len(opts)
                self.audio.play('menu_select')
        elif ty in ('confirm', 'attack', 'interact'):
            self._ranch_do(opts[self._ranch_menu_idx % len(opts)])

    def _ranch_do(self, opt):
        from core.town import RANCH_FEED_MAX
        from core.save_load import save_records
        ranch = self._town.ranch
        pen = ranch[self._ranch_menu_pen]
        if not self._ranch_action_enabled(pen, opt):
            self.messages.append((t('ranch_cant'), 'warn'))
            self.audio.play('no_gold')
            return
        act = opt['act']
        if act == 'buy':
            self.player.gold -= opt['cost']
            self._gold_flash_ms = 220
            pen['animal'] = opt['animal']
            pen['fed'] = False
            pen['stage'] = RANCH_FEED_MAX if self._is_test_mode else 0
            self.messages.append((t('ranch_bought', t('animal_' + opt['animal']),
                                    opt['cost']), 'good'))
            self.animator.particles.emit_heal(self.player.x, self.player.y)
            self.audio.play('buy')
        elif act == 'feed':
            pen['fed'] = True
            if self._is_test_mode:
                pen['stage'] = RANCH_FEED_MAX
            self.messages.append((t('ranch_fed', t('animal_' + pen['animal'])), 'good'))
            self.animator.particles.emit_heal(self.player.x, self.player.y)
            self.audio.play('use_item')
        elif act == 'collect':
            self._ranch_collect(pen)
        elif act == 'sell':
            refund = self._livestock_cost(pen['animal']) // 2
            self.player.gold += refund
            self._gold_flash_ms = 220
            self.messages.append((t('ranch_sold', t('animal_' + pen['animal']),
                                    refund), 'info'))
            pen['animal'] = None; pen['fed'] = False; pen['stage'] = 0
            self.audio.play('pickup')
        ranch[self._ranch_menu_pen] = pen
        self._records['ranch'] = ranch
        if not self._is_test_mode:
            save_records(self._records)
        # 멀티플레이: 목장 변경 동기화 (호스트=브로드캐스트, 클라=인텐트)
        if self.net is not None and self._in_town:
            if self.net.is_host:
                self.net.push_world()
            else:
                self.net.send_world_action({
                    'kind': 'ranch', 'act': act,
                    'pen': self._ranch_menu_pen,
                    'animal': pen.get('animal'),
                })
        self.state = 'playing'

    def _livestock_cost(self, animal):
        return next((c for (k, c, p, g) in self.LIVESTOCK if k == animal), 60)

    def _ranch_collect(self, pen):
        """생산물 수확 — 아이템(채집품) + 골드, 가축은 남아 재생산(먹이 필요)."""
        animal = pen['animal']
        spec = next((s for s in self.LIVESTOCK if s[0] == animal), None)
        if not spec:
            return
        _k, _c, pkey, pgold = spec
        gold = int(pgold * getattr(self, '_gold_mult', 1.0))
        self.player.gold += gold
        self._gold_flash_ms = 220
        added = self._give_inventory_item(pkey)
        pen['fed'] = False; pen['stage'] = 0          # 재생산 위해 다시 먹이 필요
        if added:
            self.messages.append((t('ranch_collect_item', added, gold), 'good'))
        else:
            self.messages.append((t('ranch_collect', t('animal_' + animal), gold), 'good'))
        self.animator.add(BannerAnim(t('ranch_collect_banner'), (230, 210, 120), size=22))
        self.animator.particles.emit_levelup(self.player.x, self.player.y)
        self.audio.play('buy')

    def _render_ranch_menu(self):
        if self._ranch_menu_pen is None or not self._town:
            return
        pen = self._town.ranch[self._ranch_menu_pen]
        opts = self._ranch_options(pen)
        s = self.screen
        empty = not pen.get('animal')
        bw = 236
        bh = 52 + len(opts) * 26 + 22
        bx = GAME_X + (GAME_W - bw) // 2
        by = GAME_Y + (GAME_H - bh) // 2
        pygame.draw.rect(s, (26, 20, 12), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(s, (206, 168, 96), (bx, by, bw, bh), 2, border_radius=6)
        # 상태 헤더
        if empty:
            status = t('ranch_status_empty')
        else:
            ready = self._pen_ready(pen)
            sk = ('ranch_status_ready' if ready else
                  ('ranch_status_grow' if pen.get('fed') else 'ranch_status_hungry'))
            status = t('animal_' + pen['animal']) + ' — ' + t(sk)
        title = self.hud.font_sm.render(status, True, (238, 216, 160))
        s.blit(title, (bx + (bw - title.get_width()) // 2, by + 9))
        pygame.draw.line(s, (96, 74, 44), (bx + 12, by + 28), (bx + bw - 12, by + 28), 1)
        y = by + 36
        for i, opt in enumerate(opts):
            enabled = self._ranch_action_enabled(pen, opt)
            sel = (i == self._ranch_menu_idx)
            if sel:
                pygame.draw.rect(s, (60, 46, 26), (bx + 10, y, bw - 20, 23), border_radius=4)
                pygame.draw.rect(s, (220, 184, 110), (bx + 10, y, bw - 20, 23), 1, border_radius=4)
                pygame.draw.polygon(s, (220, 184, 110),
                                    [(bx + 16, y + 6), (bx + 16, y + 16), (bx + 22, y + 11)])
            if opt['act'] == 'buy':
                label = t('animal_' + opt['animal']) + f"  {opt['cost']}G"
            else:
                label = t('ranch_btn_' + opt['act'])
            col = (240, 232, 210) if enabled else (110, 100, 84)
            lbl = self.hud.font_sm.render(label, True, col)
            s.blit(lbl, (bx + 28, y + 4))
            y += 26
        hint = self.hud.font_sm.render(t('ranch_menu_hint'), True, (140, 122, 92))
        s.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 17))

    # ── 농사 팝업 메뉴 (씨앗뿌리기/물주기/수확하기/뽑고버리기) ──────────
    FARM_ACTIONS = ('plant', 'water', 'harvest', 'uproot')
    _CROP_PRODUCE = {'wheat': 'food_bread', 'tomato': 'food_soup',
                     'pumpkin': 'food_pie', 'carrot': 'food_stew'}
    _CROP_SEED = {'wheat': 'seed_wheat', 'tomato': 'seed_tomato',
                  'pumpkin': 'seed_pumpkin', 'carrot': 'seed_carrot'}
    _SEED_CROP = {v: k for k, v in _CROP_SEED.items()}

    # ── 목장(가축 사육) ─────────────────────────────────────────────────────
    # (key, 구입가, 생산물 아이템, 생산 골드) — 가축 그림은 town._draw_animal 재사용
    LIVESTOCK = (('chicken', 60,  'egg',        18),
                 ('sheep',   130, 'mutton',     34),
                 ('pig',     170, 'pork_belly', 42),
                 ('cow',     240, 'milk',       55))
    _LIVESTOCK_COL = {'chicken': (238, 232, 214), 'sheep': (226, 226, 230),
                      'pig': (232, 176, 180), 'cow': (86, 74, 66)}
    RANCH_ACTIONS = ('feed', 'collect', 'sell')

    # ── 희귀식물(고대 제단) ────────────────────────────────────────────────
    # 수확 시 낮은 확률로 등장 → 영구 스탯 강화 재료 & 고대 무기 교환 재료.
    RARE_PLANTS = ('sunbloom', 'ironvine', 'galeleaf')   # 공격/방어/회피 계열
    _RARE_STAT  = {'sunbloom': 'atk', 'ironvine': 'def', 'galeleaf': 'eva'}
    _RELIC_CAP  = {'atk': 15, 'def': 12, 'eva': 12}       # 영구 강화 상한
    _RARE_BASE_CHANCE = 0.12                              # 기본 희귀 드랍 확률
    # 고대 무기 교환: 3단계, 각 (희귀식물 총량 요구, 지급 무기 key)
    ALTAR_WEAPONS = (('ancient_dagger', 12), ('ancient_glaive', 24),
                     ('ancient_ragnarok', 40))

    def _apply_relic_bonus(self):
        """기록의 영구 희귀식물 보너스를 현재 플레이어에 반영."""
        rb = (self._records or {}).get('relic_bonus') or {}
        if getattr(self, 'player', None):
            self.player.relic_atk = int(rb.get('atk', 0))
            self.player.relic_def = int(rb.get('def', 0))
            self.player.relic_eva = int(rb.get('eva', 0))

    def _rare_counts(self) -> dict:
        rp = self._records.get('rare_plants')
        if not isinstance(rp, dict):
            rp = {}
        counts = {k: int(rp.get(k, 0)) for k in self.RARE_PLANTS}
        self._records['rare_plants'] = counts
        return counts

    def _relic_bonus(self) -> dict:
        rb = self._records.get('relic_bonus')
        if not isinstance(rb, dict):
            rb = {}
        bonus = {k: int(rb.get(k, 0)) for k in ('atk', 'def', 'eva')}
        self._records['relic_bonus'] = bonus
        return bonus

    def _relic_cost(self, stat) -> int:
        """다음 +1에 필요한 희귀식물 개수 — 누적(현재 레벨 + 2)."""
        return self._relic_bonus()[stat] + 2

    def _plot_ready(self, plot):
        """수확 가능 여부 — 테스트 모드에선 심자마자 즉시 수확 가능."""
        from core.town import FARM_GROW_MAX
        if not plot.get('crop'):
            return False
        return self._is_test_mode or plot.get('stage', 0) >= FARM_GROW_MAX

    def _farm_action_enabled(self, plot, act):
        crop = plot.get('crop')
        ready = self._plot_ready(plot)
        if act == 'plant':   return not crop
        if act == 'water':   return bool(crop) and not ready and not plot.get('watered')
        if act == 'harvest': return ready
        if act == 'uproot':  return bool(crop)
        return False

    def _handle_farm_menu_action(self, action):
        ty = action['type']
        if ty == 'move':
            d = action.get('dy') or action.get('dx')
            if d:
                self._farm_menu_idx = (self._farm_menu_idx + d) % len(self.FARM_ACTIONS)
                self.audio.play('menu_select')
        elif ty in ('confirm', 'attack', 'interact'):
            self._farm_do(self.FARM_ACTIONS[self._farm_menu_idx])

    def _farm_do(self, act):
        from core.town import CROPS
        from core.save_load import save_records
        import random
        farm = self._town.farm
        plot = farm[self._farm_menu_plot]
        if not self._farm_action_enabled(plot, act):
            self.messages.append((t('farm_cant'), 'warn'))
            self.audio.play('no_gold')
            return                                          # 불가 → 메뉴 유지
        crop = plot.get('crop')
        if act == 'plant':
            from core.town import FARM_GROW_MAX
            cid, _c, _v = random.choice(CROPS)
            plot['crop'] = cid; plot['watered'] = False
            plot['stage'] = FARM_GROW_MAX if self._is_test_mode else 0  # 테스트: 즉시 수확
            self.messages.append((t('farm_planted', t('crop_' + cid)), 'good'))
            self.animator.particles.emit_heal(self.player.x, self.player.y)
            self.audio.play('use_item')
        elif act == 'water':
            plot['watered'] = True
            self.messages.append((t('farm_watered', t('crop_' + crop)), 'good'))
            self.animator.particles.emit_heal(self.player.x, self.player.y)
            self.audio.play('use_item')
        elif act == 'harvest':
            self._farm_harvest(plot, crop)
        elif act == 'uproot':
            plot['crop'] = None; plot['stage'] = 0; plot['watered'] = False
            self.messages.append((t('farm_uprooted'), 'info'))
            self.audio.play('pickup')
        farm[self._farm_menu_plot] = plot
        self._records['farm'] = farm
        if not self._is_test_mode:
            save_records(self._records)
        # 멀티플레이: 밭 변경을 동기화 (호스트=즉시 브로드캐스트, 클라=인텐트 전송)
        if self.net is not None and self._in_town:
            if self.net.is_host:
                self.net.push_world()
            else:
                self.net.send_world_action({
                    'kind': 'farm', 'act': act,
                    'plot': self._farm_menu_plot,
                    'crop': plot.get('crop'),
                })
        self.state = 'playing'                              # 액션 후 메뉴 닫기

    def _farm_harvest(self, plot, crop):
        """수확 — 치유 아이템(수확물) 인벤 지급 + 소액 골드 + 농사 진척(퀘스트형)."""
        from core.town import CROPS
        from entities.item import Item
        val = next((v for (cid, c, v) in CROPS if cid == crop), 30)
        gold = int(val * getattr(self, '_gold_mult', 1.0) * 0.5)
        self.player.gold += gold
        self._gold_flash_ms = 220
        pkey = self._CROP_PRODUCE.get(crop)
        added = None
        if pkey and pkey in self._item_data and len(self.player.inventory) < self.player.max_inventory:
            d = dict(self._item_data[pkey]); d['key'] = pkey
            it = Item(0, 0, d)
            self.player.inventory.append(it)
            added = it.name
        plot['crop'] = None; plot['stage'] = 0; plot['watered'] = False
        if added:
            self.messages.append((t('farm_harvest_item', added, gold), 'good'))
        else:
            self.messages.append((t('farm_harvest', t('crop_' + crop), gold), 'good'))
        # 채집품: 씨앗을 인벤토리에 지급 (밭에서 다시 심을 수 있음)
        seed = self._give_inventory_item(self._CROP_SEED.get(crop))
        if seed:
            self.messages.append((t('farm_seed_get', seed), 'info'))
        self.animator.particles.emit_levelup(self.player.x, self.player.y)
        self.audio.play('buy')
        self._farm_quest_progress()
        self._roll_rare_plant(crop, val)

    def _roll_rare_plant(self, crop, val):
        """수확 시 낮은 확률로 희귀식물 획득 — 작물 가치가 높을수록 확률↑."""
        import random
        chance = self._RARE_BASE_CHANCE + max(0, val - 30) * 0.004   # 최대 ~+12%p
        if random.random() >= chance:
            return
        rp = random.choice(self.RARE_PLANTS)
        counts = self._rare_counts()
        counts[rp] += 1
        self.messages.append((t('rare_found', t('rare_' + rp)), 'good'))
        self.animator.add(BannerAnim(t('rare_banner'), (210, 150, 235), size=22))
        self.animator.particles.emit_heal(self.player.x, self.player.y)
        self.audio.play('levelup')

    def _farm_quest_progress(self):
        """수확 누적(퀘스트형) — 5회마다 농부의 인정 보너스."""
        n = int(self._records.get('harvest_total', 0)) + 1
        self._records['harvest_total'] = n
        if n % 5 == 0:
            bonus = 100 * (n // 5)
            self.player.gold += bonus
            self.messages.append((t('farm_quest_milestone', n, bonus), 'good'))
            self.animator.add(BannerAnim(t('farm_quest_banner'), (120, 210, 90), size=24))
            self.audio.play('levelup')

    def _render_farm_menu(self):
        if self._farm_menu_plot is None or not self._town:
            return
        plot = self._town.farm[self._farm_menu_plot]
        s = self.screen
        bw, bh = 214, 160
        bx = GAME_X + (GAME_W - bw) // 2
        by = GAME_Y + (GAME_H - bh) // 2
        pygame.draw.rect(s, (16, 22, 12), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(s, (120, 185, 90), (bx, by, bw, bh), 2, border_radius=6)
        crop = plot.get('crop')
        if crop:
            ready = self._plot_ready(plot)
            sk = ('farm_status_ready' if ready else
                  ('farm_status_grow' if plot.get('watered') else 'farm_status_dry'))
            status = t('crop_' + crop) + ' — ' + t(sk)
        else:
            status = t('farm_status_empty')
        title = self.hud.font_sm.render(status, True, (200, 235, 170))
        s.blit(title, (bx + (bw - title.get_width()) // 2, by + 9))
        pygame.draw.line(s, (60, 90, 44), (bx + 12, by + 28), (bx + bw - 12, by + 28), 1)
        labels = {'plant': t('farm_btn_plant'), 'water': t('farm_btn_water'),
                  'harvest': t('farm_btn_harvest'), 'uproot': t('farm_btn_uproot')}
        y = by + 36
        for i, act in enumerate(self.FARM_ACTIONS):
            enabled = self._farm_action_enabled(plot, act)
            sel = (i == self._farm_menu_idx)
            if sel:
                pygame.draw.rect(s, (40, 62, 30), (bx + 10, y, bw - 20, 25), border_radius=4)
                pygame.draw.rect(s, (150, 220, 110), (bx + 10, y, bw - 20, 25), 1, border_radius=4)
                pygame.draw.polygon(s, (150, 220, 110),
                                    [(bx + 16, y + 7), (bx + 16, y + 18), (bx + 22, y + 12)])
            col = (238, 246, 214) if enabled else (92, 98, 86)
            lbl = self.hud.font_sm.render(labels[act], True, col)
            s.blit(lbl, (bx + 28, y + 6))
            y += 28
        hint = self.hud.font_sm.render(t('farm_menu_hint'), True, (110, 130, 100))
        s.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 17))

    # ── 고대 제단 — 희귀식물 영구강화 & 고대 무기 교환 ────────────────────
    def _open_altar(self):
        self._altar_idx = 0
        self.state = 'altar'
        self.audio.play('shop_open')

    def _altar_options(self):
        """제단 메뉴 항목 — 스탯강화 3종 + 다음 미획득 고대 무기 1종."""
        counts = self._rare_counts()
        bonus = self._relic_bonus()
        opts = []
        for plant in self.RARE_PLANTS:
            stat = self._RARE_STAT[plant]
            cap = self._RELIC_CAP[stat]
            cur = bonus[stat]
            cost = self._relic_cost(stat)
            maxed = cur >= cap
            opts.append({'kind': 'stat', 'stat': stat, 'plant': plant,
                         'cost': cost, 'cur': cur, 'cap': cap, 'maxed': maxed,
                         'have': counts[plant],
                         'can': (not maxed) and counts[plant] >= cost})
        claimed = self._records.get('altar_claimed') or []
        total = sum(counts.values())
        for (wkey, need) in self.ALTAR_WEAPONS:
            if wkey in claimed:
                continue
            opts.append({'kind': 'weapon', 'wkey': wkey, 'need': need,
                         'total': total, 'can': total >= need})
            break
        return opts

    def _handle_altar_action(self, action):
        ty = action['type']
        opts = self._altar_options()
        if not opts:
            return
        if ty == 'move':
            d = action.get('dy') or action.get('dx')
            if d:
                self._altar_idx = (self._altar_idx + d) % len(opts)
                self.audio.play('menu_select')
        elif ty in ('confirm', 'attack', 'interact'):
            self._altar_do(opts[self._altar_idx % len(opts)])

    def _altar_do(self, opt):
        from core.save_load import save_records
        if not opt.get('can'):
            self.messages.append((t('altar_cant'), 'warn'))
            self.audio.play('no_gold')
            return
        counts = self._rare_counts()
        if opt['kind'] == 'stat':
            counts[opt['plant']] -= opt['cost']
            bonus = self._relic_bonus()
            bonus[opt['stat']] += 1
            self._apply_relic_bonus()
            self.messages.append((t('altar_stat_up',
                                    t('relic_stat_' + opt['stat']), bonus[opt['stat']]), 'good'))
            self.animator.add(BannerAnim(t('altar_stat_banner'), (235, 200, 90), size=24))
            self.animator.particles.emit_levelup(self.player.x, self.player.y)
            self.audio.play('levelup')
        else:
            self._consume_rare(opt['need'])
            self._grant_ancient_weapon(opt['wkey'])
            claimed = self._records.setdefault('altar_claimed', [])
            if opt['wkey'] not in claimed:
                claimed.append(opt['wkey'])
        if not self._is_test_mode:
            save_records(self._records)
        opts = self._altar_options()
        self._altar_idx = min(self._altar_idx, max(0, len(opts) - 1))

    def _consume_rare(self, n):
        """희귀식물 총 n개를 균등(보유 많은 순)으로 차감."""
        counts = self._rare_counts()
        for _ in range(n):
            k = max(self.RARE_PLANTS, key=lambda p: counts[p])
            if counts[k] <= 0:
                break
            counts[k] -= 1

    def _grant_ancient_weapon(self, wkey, get_key='altar_weapon_get',
                              banner_key='altar_weapon_banner'):
        """고대 무기/유물을 영구 창고에 지급 (없는 키면 무시)."""
        from core.save_load import save_storage
        if wkey not in self._item_data:
            return
        name = self._item_data[wkey].get('name', wkey)
        if self._storage_add(wkey):
            save_storage(self._storage, self._storage_cap)
            self.messages.append((t(get_key, name), 'good'))
            self.animator.add(BannerAnim(t(banner_key), (240, 190, 110), size=26))
            self.audio.play('levelup')
        else:
            self.messages.append((t('storage_cap_full'), 'warn'))

    # ── 낚시 미니게임 (입질 타이밍) & 낚시 노인(고대 유물 교환) ────────────
    # (key, grade, gold, weight)   grade: 0 일반 · 1 희귀 · 2 정예 · 3 전설
    FISH_SPECIES = (('minnow', 0, 12, 42), ('carp', 0, 18, 34),
                    ('trout', 1, 42, 16), ('koi', 1, 60, 8),
                    ('golden_koi', 2, 130, 4), ('ancient_fish', 3, 320, 1))
    FISH_GRADE_COL = {0: (176, 200, 214), 1: (120, 206, 150),
                      2: (242, 200, 108), 3: (212, 150, 236)}
    _FISH_POINTS = {0: 1, 1: 3, 2: 8, 3: 20}      # 등급별 교환 포인트
    _BITE_WINDOW_MS = 750                          # 입질 후 챔질 허용시간
    # 고대 유물(장신구) 교환 3단계 — (아이템 key, 요구 물고기 포인트)
    ANGLER_RELICS = (('relic_charm', 20), ('relic_pendant', 48), ('relic_crown', 95))

    def _give_inventory_item(self, key):
        """아이템 1개를 인벤토리에 지급. 성공 시 이름, 실패(꽉참/없음) 시 None."""
        from entities.item import Item
        if key not in self._item_data:
            return None
        if len(self.player.inventory) >= self.player.max_inventory:
            return None
        d = dict(self._item_data[key]); d['key'] = key
        it = Item(0, 0, d)
        self.player.inventory.append(it)
        return it.name

    def _open_fishing(self):
        import random
        self._fish = {'phase': 'cast', 't': 0.0,
                      'wait': random.uniform(1000, 2600),
                      'result': None, 'grade': None, 'gold': 0}
        self.state = 'fishing'
        self.audio.play('menu_select')

    # 릴 감기: 어종 등급 → (목표 밴드 반폭, 커서 속도 fraction/ms)
    _REEL_DIFF = {0: (0.20, 0.0011), 1: (0.15, 0.0014),
                  2: (0.11, 0.0018), 3: (0.085, 0.0024)}
    _REEL_LIMIT_MS = 4200

    def _update_fishing(self, dt):
        f = self._fish
        if not f:
            return
        f['t'] += dt
        ph = f['phase']
        if ph == 'cast' and f['t'] >= 350:
            f['phase'] = 'wait'; f['t'] = 0.0
        elif ph == 'wait' and f['t'] >= f['wait']:
            f['phase'] = 'bite'; f['t'] = 0.0
            self.audio.play('button')                    # 입질 신호
        elif ph == 'bite' and f['t'] >= self._BITE_WINDOW_MS:
            f['phase'] = 'result'; f['result'] = 'miss'; f['t'] = 0.0
            self.audio.play('no_gold')
        elif ph == 'reel':
            f['cursor'] += f['dir'] * f['speed'] * dt
            if f['cursor'] <= 0.0:
                f['cursor'] = 0.0; f['dir'] = 1
            elif f['cursor'] >= 1.0:
                f['cursor'] = 1.0; f['dir'] = -1
            if f['t'] >= self._REEL_LIMIT_MS:            # 너무 오래 끌면 도망
                f['phase'] = 'result'; f['result'] = 'escape'; f['t'] = 0.0
                self.audio.play('no_gold')

    def _handle_fishing_action(self, action):
        f = self._fish
        if not f:
            return
        ty = action['type']
        confirm = ty in ('confirm', 'attack', 'interact')
        if f['phase'] == 'result':
            if confirm:
                self._open_fishing()                     # 다시 던지기
            return
        if not confirm:
            return
        if f['phase'] in ('cast', 'wait'):
            f['phase'] = 'result'; f['result'] = 'early'  # 너무 일찍 챔
            self.audio.play('no_gold')
        elif f['phase'] == 'bite':
            self._fish_hook()                            # 챔질 성공 → 릴 감기 단계
        elif f['phase'] == 'reel':
            if abs(f['cursor'] - f['band_c']) <= f['band_w']:
                self._fish_land(*f['pending'])           # 타이밍 명중 → 낚음!
            else:
                f['phase'] = 'result'; f['result'] = 'escape'
                self.audio.play('no_gold')

    def _fish_hook(self):
        """챔질 성공 — 어종을 뽑고 등급별 난이도로 릴 감기 미니게임 시작."""
        import random
        keys = [s[0] for s in self.FISH_SPECIES]
        weights = [s[3] for s in self.FISH_SPECIES]
        key = random.choices(keys, weights=weights, k=1)[0]
        spec = next(s for s in self.FISH_SPECIES if s[0] == key)
        grade = spec[1]
        gold = int(spec[2] * getattr(self, '_gold_mult', 1.0))
        band_w, spd = self._REEL_DIFF[grade]
        f = self._fish
        f.update({'phase': 'reel', 't': 0.0,
                  'cursor': random.uniform(0.1, 0.9),
                  'dir': random.choice((-1, 1)), 'speed': spd,
                  'band_c': random.uniform(0.24, 0.76), 'band_w': band_w,
                  'pending': (key, grade, gold), 'grade': grade})
        self.audio.play('button')

    def _fish_land(self, key, grade, gold):
        """릴 감기 성공 — 보상 지급(골드/카운터/구운 생선) + 결과 화면."""
        from core.save_load import save_records
        f = self._fish
        self.player.gold += gold
        self._gold_flash_ms = 220
        counts = self._fish_counts()
        counts[key] += 1
        self._records['fish_total'] = int(self._records.get('fish_total', 0)) + 1
        # 채집품: 구운 생선을 인벤토리에 지급(고급 어종은 특상 생선구이)
        f['food'] = self._give_inventory_item('deluxe_fish' if grade >= 2 else 'grilled_fish')
        if f['food']:
            self.messages.append((t('fish_food_get', f['food']), 'info'))
        f['phase'] = 'result'; f['result'] = key; f['grade'] = grade; f['gold'] = gold
        if grade >= 2:
            self.animator.add(BannerAnim(t('fish_grade_' + str(grade)),
                                         self.FISH_GRADE_COL[grade], size=24))
            self.audio.play('levelup')
        else:
            self.audio.play('buy')
        self.animator.particles.emit_heal(self.player.x, self.player.y)
        if not self._is_test_mode:
            save_records(self._records)

    def _fish_counts(self) -> dict:
        c = self._records.get('fish_caught')
        if not isinstance(c, dict):
            c = {}
        counts = {s[0]: int(c.get(s[0], 0)) for s in self.FISH_SPECIES}
        self._records['fish_caught'] = counts
        return counts

    def _fish_points(self) -> int:
        counts = self._fish_counts()
        grade = {s[0]: s[1] for s in self.FISH_SPECIES}
        return sum(counts[k] * self._FISH_POINTS[grade[k]] for k in counts)

    def _consume_fish_points(self, need):
        """낮은 등급 물고기부터 소비해 need 포인트 충당(고급 어종 보존)."""
        counts = self._fish_counts()
        grade = {s[0]: s[1] for s in self.FISH_SPECIES}
        remain = need
        for k in sorted(counts, key=lambda kk: grade[kk]):
            while counts[k] > 0 and remain > 0:
                counts[k] -= 1
                remain -= self._FISH_POINTS[grade[k]]

    def _open_angler(self):
        self._angler_idx = 0
        self.state = 'angler'
        self.audio.play('shop_open')

    def _angler_options(self):
        """다음 미획득 고대 유물 1종 + 현재 물고기 포인트."""
        pts = self._fish_points()
        claimed = self._records.get('angler_claimed') or []
        opts = []
        for (rkey, need) in self.ANGLER_RELICS:
            if rkey in claimed:
                continue
            opts.append({'rkey': rkey, 'need': need, 'pts': pts, 'can': pts >= need})
            break
        return opts, pts

    def _handle_angler_action(self, action):
        ty = action['type']
        opts, _ = self._angler_options()
        if not opts:
            return
        if ty == 'move':
            d = action.get('dy') or action.get('dx')
            if d:
                self._angler_idx = (self._angler_idx + d) % len(opts)
                self.audio.play('menu_select')
        elif ty in ('confirm', 'attack', 'interact'):
            self._angler_do(opts[self._angler_idx % len(opts)])

    def _angler_do(self, opt):
        from core.save_load import save_records
        if not opt['can']:
            self.messages.append((t('angler_cant'), 'warn'))
            self.audio.play('no_gold')
            return
        self._consume_fish_points(opt['need'])
        self._grant_ancient_weapon(opt['rkey'], 'angler_relic_get', 'angler_relic_banner')
        claimed = self._records.setdefault('angler_claimed', [])
        if opt['rkey'] not in claimed:
            claimed.append(opt['rkey'])
        if not self._is_test_mode:
            save_records(self._records)
        self._angler_idx = 0

    def _render_fishing(self):
        f = self._fish or {}
        s = self.screen
        bw, bh = 260, 180
        bx = GAME_X + (GAME_W - bw) // 2
        by = GAME_Y + (GAME_H - bh) // 2
        pygame.draw.rect(s, (14, 20, 30), (bx, by, bw, bh), border_radius=7)
        pygame.draw.rect(s, (110, 170, 220), (bx, by, bw, bh), 2, border_radius=7)
        # 물 + 찌
        wx, wy, ww, wh = bx + 16, by + 40, bw - 32, 78
        pygame.draw.rect(s, (32, 74, 110), (wx, wy, ww, wh), border_radius=5)
        for i in range(3):
            yy = wy + 16 + i * 22 + int(3 * math.sin(pygame.time.get_ticks() * 0.003 + i))
            pygame.draw.line(s, (60, 108, 150), (wx + 8, yy), (wx + ww - 8, yy), 1)
        ph = f.get('phase')
        cx = wx + ww // 2
        dip = 0
        if ph in ('bite', 'reel'):
            dip = 8 if (pygame.time.get_ticks() // 90) % 2 == 0 else 3
        bob_y = wy + 20 + dip
        pygame.draw.line(s, (220, 220, 230), (cx, wy - 18), (cx, bob_y), 1)
        pygame.draw.circle(s, (232, 96, 84), (cx, bob_y), 4)
        pygame.draw.circle(s, (250, 220, 210), (cx - 1, bob_y - 1), 1)
        # ── 릴 감기 바 (좌우로 움직이는 커서를 초록 밴드에 맞춰 E) ──────
        if ph == 'reel':
            rx, rw = wx + 12, ww - 24
            ry = wy + wh - 22
            pygame.draw.rect(s, (18, 40, 58), (rx, ry, rw, 12), border_radius=6)
            bc = f.get('band_c', 0.5); bwd = f.get('band_w', 0.15)
            band_x = int(rx + (bc - bwd) * rw)
            band_w = max(4, int(2 * bwd * rw))
            in_band = abs(f.get('cursor', 0) - bc) <= bwd
            bandcol = (90, 220, 130) if in_band else (70, 170, 100)
            pygame.draw.rect(s, bandcol, (band_x, ry, band_w, 12), border_radius=6)
            curx = int(rx + f.get('cursor', 0) * rw)
            pygame.draw.rect(s, (255, 244, 180), (curx - 2, ry - 4, 4, 20), border_radius=2)
        # 상단/하단 텍스트
        title = self.hud.font_sm.render(t('fish_title'), True, (200, 224, 246))
        s.blit(title, (bx + (bw - title.get_width()) // 2, by + 9))
        big = self.hud.font_md
        if ph == 'cast':
            msg, col = t('fish_cast'), (180, 210, 230)
        elif ph == 'wait':
            msg, col = t('fish_wait'), (180, 210, 230)
        elif ph == 'bite':
            flash = (pygame.time.get_ticks() // 100) % 2 == 0
            msg = t('fish_bite')
            col = (255, 236, 120) if flash else (255, 170, 60)
        elif ph == 'reel':
            flash = (pygame.time.get_ticks() // 120) % 2 == 0
            msg = t('fish_reel')
            col = (150, 240, 170) if flash else (110, 200, 140)
        else:
            res = f.get('result')
            if res == 'miss':
                msg, col = t('fish_miss'), (200, 150, 150)
            elif res == 'early':
                msg, col = t('fish_early'), (220, 170, 120)
            elif res == 'escape':
                msg, col = t('fish_escape'), (210, 160, 150)
            else:
                grade = f.get('grade', 0)
                col = self.FISH_GRADE_COL.get(grade, (220, 230, 240))
                msg = t('fish_got', t('fish_' + res), f.get('gold', 0))
        mt = big.render(msg, True, col)
        s.blit(mt, (bx + (bw - mt.get_width()) // 2, by + bh - 40))
        hint = self.hud.font_sm.render(t('fish_hint_menu'), True, (120, 150, 170))
        s.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 18))

    def _render_angler(self):
        opts, pts = self._angler_options()
        counts = self._fish_counts()
        s = self.screen
        bw, bh = 320, 200
        bx = GAME_X + (GAME_W - bw) // 2
        by = GAME_Y + (GAME_H - bh) // 2
        pygame.draw.rect(s, (14, 22, 26), (bx, by, bw, bh), border_radius=7)
        pygame.draw.rect(s, (120, 180, 200), (bx, by, bw, bh), 2, border_radius=7)
        title = self.hud.font_sm.render(t('angler_title'), True, (198, 226, 234))
        s.blit(title, (bx + (bw - title.get_width()) // 2, by + 8))
        pts_txt = self.hud.font_sm.render(t('angler_points', pts), True, (150, 210, 230))
        s.blit(pts_txt, (bx + (bw - pts_txt.get_width()) // 2, by + 26))
        pygame.draw.line(s, (54, 74, 84), (bx + 12, by + 44), (bx + bw - 12, by + 44), 1)
        # 어종 보유 요약 (등급색, 2열)
        for i, s0 in enumerate(self.FISH_SPECIES):
            key, grade = s0[0], s0[1]
            col = self.FISH_GRADE_COL[grade]
            ln = self.hud.font_sm.render(f"{t('fish_' + key)} x{counts[key]}", True, col)
            s.blit(ln, (bx + 18 + (i % 2) * 152, by + 50 + (i // 2) * 20))
        yb = by + 122
        if opts:
            opt = opts[0]
            sel = True
            pygame.draw.rect(s, (34, 50, 56), (bx + 12, yb, bw - 24, 34), border_radius=5)
            pygame.draw.rect(s, (150, 210, 226), (bx + 12, yb, bw - 24, 34), 1, border_radius=5)
            name = self._item_data.get(opt['rkey'], {}).get('name', opt['rkey'])
            col = (238, 232, 210) if opt['can'] else (140, 150, 150)
            ln = self.hud.font_sm.render(t('angler_relic_opt', name), True, col)
            s.blit(ln, (bx + 22, yb + 5))
            sub = self.hud.font_sm.render(f"{t('angler_relic_need')} {opt['pts']}/{opt['need']}",
                                          True, (170, 210, 160) if opt['can'] else (140, 130, 130))
            s.blit(sub, (bx + 22, yb + 18))
        else:
            done = self.hud.font_sm.render(t('angler_done'), True, (180, 210, 200))
            s.blit(done, (bx + (bw - done.get_width()) // 2, yb + 8))
        hint = self.hud.font_sm.render(t('angler_hint'), True, (120, 150, 160))
        s.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 17))


    _RELIC_ICON = {'atk': (232, 96, 84), 'def': (110, 168, 236), 'eva': (150, 220, 150)}

    def _render_altar(self):
        opts = self._altar_options()
        counts = self._rare_counts()
        s = self.screen
        bw, bh = 306, 226
        bx = GAME_X + (GAME_W - bw) // 2
        by = GAME_Y + (GAME_H - bh) // 2
        pygame.draw.rect(s, (18, 14, 26), (bx, by, bw, bh), border_radius=7)
        pygame.draw.rect(s, (188, 150, 224), (bx, by, bw, bh), 2, border_radius=7)
        title = self.hud.font_sm.render(t('altar_title'), True, (224, 198, 246))
        s.blit(title, (bx + (bw - title.get_width()) // 2, by + 8))
        # 보유 희귀식물 요약
        summ = '  '.join(f"{t('rare_' + p)} x{counts[p]}" for p in self.RARE_PLANTS)
        ss = self.hud.font_sm.render(summ, True, (200, 180, 150))
        s.blit(ss, (bx + (bw - ss.get_width()) // 2, by + 26))
        pygame.draw.line(s, (70, 54, 92), (bx + 12, by + 44), (bx + bw - 12, by + 44), 1)
        y = by + 52
        for i, opt in enumerate(opts):
            sel = (i == self._altar_idx)
            if sel:
                pygame.draw.rect(s, (44, 34, 60), (bx + 10, y, bw - 20, 30), border_radius=4)
                pygame.draw.rect(s, (198, 160, 234), (bx + 10, y, bw - 20, 30), 1, border_radius=4)
            if opt['kind'] == 'stat':
                ic = self._RELIC_ICON[opt['stat']]
                pygame.draw.circle(s, ic, (bx + 24, y + 15), 6)
                if opt['maxed']:
                    line = f"{t('relic_stat_' + opt['stat'])} MAX ({opt['cur']})"
                    sub = ''
                    col = (150, 140, 120)
                else:
                    line = f"{t('relic_stat_' + opt['stat'])} +1  →  {opt['cur'] + 1}/{opt['cap']}"
                    sub = f"{t('rare_' + opt['plant'])} {opt['have']}/{opt['cost']}"
                    col = (238, 230, 246) if opt['can'] else (120, 110, 130)
            else:
                pygame.draw.polygon(s, (240, 190, 110),
                                    [(bx + 20, y + 21), (bx + 24, y + 9), (bx + 28, y + 21)])
                name = self._item_data.get(opt['wkey'], {}).get('name', opt['wkey'])
                line = f"{t('altar_weapon_opt', name)}"
                sub = f"{t('altar_weapon_need')} {opt['total']}/{opt['need']}"
                col = (244, 214, 160) if opt['can'] else (140, 120, 100)
            ln = self.hud.font_sm.render(line, True, col)
            s.blit(ln, (bx + 38, y + 3))
            if sub:
                sb = self.hud.font_sm.render(sub, True,
                                             (170, 210, 150) if opt['can'] else (120, 104, 120))
                s.blit(sb, (bx + 38, y + 16))
            y += 34
        hint = self.hud.font_sm.render(t('altar_hint'), True, (120, 110, 130))
        s.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 17))

    _HOME_STYLES = ('cozy', 'noble', 'rustic', 'study', 'garden')

    def _cycle_home_style(self):
        """내 집 인테리어 스타일을 다음으로 순환 + 영구 저장."""
        from core.save_load import save_records
        cur = int(self._records.get('home_style', 0))
        nxt = (cur + 1) % len(self._HOME_STYLES)
        self._records['home_style'] = nxt
        save_records(self._records)
        if self._town:
            self._town.home_style = nxt
        self.messages.append((t('home_style_changed',
                                 t('hstyle_' + self._HOME_STYLES[nxt])), 'good'))
        self.animator.particles.emit_heal(self.player.x, self.player.y)
        self.audio.play('menu_select')

    def _smith_cost(self, item) -> int:
        """대장장이 강화 비용 — 강화 단계가 오를수록 비싸진다."""
        return 40 + item.enhance_level * 35

    # ═════════════════ 퀘스트 (시민 의뢰) ═════════════════════════════
    def _town_visible_givers(self) -> set:
        """현재 마을에 등장한 시민 giver 집합 (층 진행·체인 기준)."""
        from core.quests import all_givers, giver_present
        mf = self._max_floor_reached
        return {g for g in all_givers()
                if giver_present(g, self._quests, mf)}

    def _open_quest_dialog(self, giver_id):
        """시민 상호작용 — 체인에서 현재 퀘스트를 골라 상태별 대사 표시."""
        from core.quests import QUESTS, qtext, giver_name, giver_current_quest
        qid = giver_current_quest(giver_id, self._quests, self._max_floor_reached)
        if qid is None:
            # 제공할 퀘스트 없음 (전부 완료 or 다음 퀘 미개방) → 잡담 (랜덤)
            from core.quests import random_chat
            self._dialog = {'qid': None, 'mode': 'info',
                            'npc_name': giver_name(giver_id),
                            'text': random_chat(giver_id) or t('quest_idle_chat'),
                            'start': pygame.time.get_ticks()}
            self.state = 'dialog'
            self.audio.play('menu_select')
            return
        st = self._quests[qid]['state']
        if st == 'done':
            # 목표 달성 후 보고 — 보상 지급 + 화려한 클리어 연출
            self._claim_quest(qid)
            text, mode = qtext(qid, 'done'), 'info'
        else:
            text = qtext(qid, 'offer' if st == 'available' else 'active')
            mode = 'offer' if st == 'available' else 'info'
        self._dialog = {'qid': qid, 'mode': mode,
                        'npc_name': giver_name(QUESTS[qid]['giver']),
                        'text': text, 'start': pygame.time.get_ticks()}
        self.state = 'dialog'
        self.audio.play('menu_select')

    def _dialog_confirm(self):
        """대화창 Enter/Space — 제안이면 수락, 아니면 닫기."""
        if not self._dialog:
            self.state = 'playing'
            return
        if self._dialog['mode'] == 'offer':
            qid = self._dialog['qid']
            self._quests[qid]['state'] = 'active'
            from core.quests import qtext
            self.messages.append((t('quest_accepted', qtext(qid, 'name')), 'good'))
            self.audio.play('menu_confirm')
            # 이미 목표 층까지 내려가 있던 경우 즉시 반영
            cur_floor = (self._dungeon_session['floor']
                         if self._dungeon_session else self.floor)
            self._quest_on_floor(cur_floor)
        self._dialog_close()

    def _dialog_close(self, declined=False):
        if declined and self._dialog and self._dialog['mode'] == 'offer':
            self.audio.play('menu_select')
        self._dialog = None
        self.state = 'playing'

    def _claim_quest(self, qid):
        """보고 → 보상 지급 + 화려한 클리어 연출 (하이라이트 순간)."""
        from core.quests import QUESTS, qtext
        from entities.item import Item
        self._quests[qid]['state'] = 'claimed'
        r = QUESTS[qid]['reward']
        gold = r.get('gold', 0)
        if gold:
            self.player.gold += gold
            self.vfx_loot.spawn_gold(self.player.x, self.player.y, gold)
        stones = r.get('stones', 0)
        if stones:
            self.player.enhance_stones += stones
        # 펫 해금 보상 (예: 사냥꾼의 20층 게이팅 퀘스트)
        pet = r.get('pet')
        if pet:
            self.unlock_pet(pet)
        for key in r.get('items', ()):
            if key in self._item_data and \
                    len(self.player.inventory) < self.player.max_inventory:
                d = dict(self._item_data[key]); d['key'] = key
                self.player.inventory.append(Item(0, 0, d))
        self.messages.append((t('quest_reward', qtext(qid, 'name'), gold), 'good'))
        # ── 화려한 클리어 연출 ──────────────────────────────────────
        self._quest_clear_ms   = 2200
        self._quest_clear_name = qtext(qid, 'name')
        self.animator.add(BannerAnim(t('quest_reward_banner'), (255, 225, 120),
                                     y=96, size=34, duration_ms=1600))
        self.animator.particles.emit_levelup(self.player.x, self.player.y)
        self.animator.particles.emit_combo_tier(self.player.x, self.player.y,
                                                (255, 220, 120))
        self._gold_flash_ms = 520
        self._start_shake(4, 300)
        self.juice.slowmo(360, 0.35)
        self.audio.play('levelup_big')
        self.audio.play('tier_up')

    def _quest_complete_toast(self, qid):
        """목표 달성(보고 전) — 배너 + 안내 (아직 보상 전)."""
        from core.quests import qtext
        self._quests[qid]['state'] = 'done'
        self.messages.append((t('quest_complete', qtext(qid, 'name')), 'good'))
        self.animator.add(BannerAnim(t('quest_complete_banner'),
                                     (140, 255, 170), y=140, size=24,
                                     duration_ms=1100))
        self._start_punch_zoom(0.045, 130)
        self.audio.play('tier_up')

    def _quest_on_kill(self, enemy):
        """킬 추적 — kill_any / kill_key / kill_elite 퀘스트 진행."""
        from core.quests import QUESTS
        is_elite = bool(getattr(enemy, 'elite', None))
        for qid, qs in self._quests.items():
            if qs['state'] != 'active':
                continue
            k = QUESTS[qid]['kind']
            hit = (k == 'kill_any'
                   or (k == 'kill_key' and enemy.key == QUESTS[qid].get('key'))
                   or (k == 'kill_elite' and is_elite))
            if hit:
                qs['progress'] += 1
                if qs['progress'] >= QUESTS[qid]['count']:
                    self._quest_complete_toast(qid)

    def _quest_on_floor(self, floor):
        """층 도달 추적 — 최고 층 갱신 + reach_floor 퀘스트 진행."""
        from core.quests import QUESTS
        self._max_floor_reached = max(self._max_floor_reached, floor)
        for qid, qs in self._quests.items():
            if qs['state'] != 'active':
                continue
            q = QUESTS[qid]
            if q['kind'] == 'reach_floor':
                qs['progress'] = max(qs['progress'], floor)
                if qs['progress'] >= q['floor']:
                    if qid == 'rescue_girl':
                        self.messages.append((t('quest_girl_found'), 'good'))
                    self._quest_complete_toast(qid)

    def _draw_quest_markers(self, cx, cy):
        """등장한 시민 머리 위 퀘스트 마커 — ! 노랑(제안) / ? 초록(보고)."""
        from core.quests import giver_current_quest
        ts = TILE_SIZE
        bob = int(math.sin(pygame.time.get_ticks() * 0.006) * 2)
        for npc in self._town.visible_npcs():
            if 'quest' not in npc:
                continue
            qid = giver_current_quest(npc['id'], self._quests, self._max_floor_reached)
            if qid is None:
                continue
            st = self._quests[qid]['state']
            if st == 'available':
                mark, col = '!', (255, 220, 60)
            elif st == 'done':
                mark, col = '?', (120, 255, 150)
            else:
                continue
            mx = int(npc.get('fx', npc['x'] * ts)) - cx * ts + ts // 2
            my = int(npc.get('fy', npc['y'] * ts)) - cy * ts - 26 + bob
            txt = self.hud.font_md.render(mark, True, col)
            self._game_surf.blit(txt, (mx - txt.get_width() // 2, my))

    def _draw_quest_tracker(self):
        """뷰포트 좌상단 실시간 퀘스트 목표 (active/done만)."""
        from core.quests import qtext, objective_str
        y = 8
        for qid, qs in self._quests.items():
            if qs['state'] not in ('active', 'done'):
                continue
            done = qs['state'] == 'done'
            obj = objective_str(qid, qs['progress'])
            line = f"{'✔' if done else '▸'} {qtext(qid, 'name')}  {obj}"
            txt = self.hud.font_sm.render(
                line, True, (130, 255, 160) if done else (235, 225, 180))
            bg = pygame.Surface((txt.get_width() + 10, 16), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 110))
            self._game_surf.blit(bg, (6, y - 2))
            self._game_surf.blit(txt, (11, y))
            y += 18

    def _draw_quest_clear_overlay(self):
        """퀘스트 보고 완료 순간의 화려한 전면 연출 (골드 방사 + 이름)."""
        k = self._quest_clear_ms / 2200.0          # 1=시작 0=끝
        cx, cy = GAME_W // 2, GAME_H // 2 - 30
        # 확장하는 골드 링 2겹
        for i in range(2):
            r = int((1 - k) * 220) + i * 30
            a = int(90 * k)
            if a > 4 and r > 2:
                ring = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
                pygame.draw.circle(ring, (255, 215, 110, a), (cx, cy), r,
                                   max(2, int(6 * k)))
                self._game_surf.blit(ring, (0, 0))
        # 방사 광선 (회전)
        rays = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
        tk = pygame.time.get_ticks() * 0.001
        for n in range(12):
            a = tk + n * math.pi / 6
            x2 = cx + math.cos(a) * 260
            y2 = cy + math.sin(a) * 260
            pygame.draw.line(rays, (255, 225, 130, int(45 * k)),
                             (cx, cy), (int(x2), int(y2)), 3)
        self._game_surf.blit(rays, (0, 0))
        # "✦ QUEST CLEAR ✦" + 퀘스트 이름 (팝 인 후 유지)
        if self._quest_clear_font is None:
            from core.animator import _load_font
            self._quest_clear_font = _load_font(26)
        alpha = 255 if k > 0.25 else int(255 * k / 0.25)
        title = self._quest_clear_font.render(f"✦ {t('quest_clear')} ✦", True,
                                              (255, 235, 150))
        # per-pixel alpha 안전 페이드 (set_alpha는 일부 SDL에서 직사각형 아티팩트)
        title.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
        self._game_surf.blit(title, (cx - title.get_width() // 2, cy - 24))
        nm = self.hud.font_md.render(self._quest_clear_name, True, (255, 250, 220))
        nm.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
        self._game_surf.blit(nm, (cx - nm.get_width() // 2, cy + 8))

    # ── 잡화점 (마을 상인): 소모품 위주, 던전 상점보다 저렴 ───────────
    def _make_town_stock(self):
        from entities.item import Item
        stock = []
        for key, price in (('health_potion', 12), ('large_health_potion', 28),
                           ('return_scroll', 22), ('repair_kit', 34),
                           ('teleport_scroll', 30), ('whirlwind_potion', 45)):
            if key in self._item_data:
                d = dict(self._item_data[key]); d['key'] = key
                stock.append((Item(0, 0, d), price))
        return stock

    # ── 여관 (주모): 휴식 + 여관밥 ────────────────────────────────────
    def _inn_rest_cost(self) -> int:
        floor = (self._dungeon_session['floor']
                 if self._dungeon_session else self.floor)
        return 15 + floor * 5

    def _handle_inn_action(self, action):
        ty = action['type']
        if ty == 'use_item' and action.get('slot') == 0:      # [1] 휴식
            cost = self._inn_rest_cost()
            if self.player.gold < cost:
                self.messages.append((t('no_gold'), 'warn'))
                self.audio.play('no_gold')
                return
            self.player.gold -= cost
            self.player.hp = self.player.max_hp
            self.player.stamina = float(self.player.stamina_max)
            self.player.drive = float(self.player.drive_max)
            self.messages.append((t('inn_rested', cost), 'good'))
            self.animator.particles.emit_heal(self.player.x, self.player.y)
            self.audio.play('skill_heal')
            self.state = 'playing'
        elif ty == 'use_item' and action.get('slot') == 1:    # [2] 여관밥
            if getattr(self.player, 'well_fed', False):
                self.messages.append((t('inn_food_already'), 'info'))
                return
            if self.player.gold < 30:
                self.messages.append((t('no_gold'), 'warn'))
                self.audio.play('no_gold')
                return
            self.player.gold -= 30
            bonus = max(5, int(self.player.max_hp * 0.10))
            self.player.max_hp += bonus
            self.player.hp = self.player.max_hp
            self.player.well_fed = True
            self.messages.append((t('inn_food_done', bonus), 'good'))
            self.animator.particles.emit_levelup(self.player.x, self.player.y)
            self.audio.play('levelup')
            self.state = 'playing'

    # ── 창고 용량 확장 (U키) ──────────────────────────────────────────
    _STORAGE_UPGRADES = {30: 500, 60: 2000, 90: 4000}   # 현재 용량 → 확장 비용 (최대 100)
    _STORAGE_MAX_CAP  = 100

    def _upgrade_storage(self):
        from core.save_load import save_storage
        cost = self._STORAGE_UPGRADES.get(self._storage_cap)
        if cost is None:
            self.messages.append((t('storage_cap_max'), 'info'))
            return
        if self.player.gold < cost:
            self.messages.append((t('no_gold'), 'warn'))
            self.audio.play('no_gold')
            return
        self.player.gold -= cost
        self._storage_cap = min(self._STORAGE_MAX_CAP, self._storage_cap + 30)
        save_storage(self._storage, self._storage_cap)
        self.messages.append((t('storage_upgraded', self._storage_cap), 'good'))
        self.audio.play('levelup')

    def _use_repair_kit(self):
        """응급 수리 키트 — 장착 방어구 각각 최대치의 50% 회복."""
        fixed = 0
        for it in self.player.equipment.values():
            if it and it.max_durability > 0 and it.durability < it.max_durability:
                it.durability = min(it.max_durability,
                                    it.durability + it.max_durability // 2)
                fixed += 1
        self.messages.append((t('repair_kit_used', fixed), 'good'))
        self.animator.particles.emit_heal(self.player.x, self.player.y)
        self.audio.play('use_item')

    def _equip_burst(self, item):
        """장착 순간 아이템 색 버스트 — 상시 오버레이 대신 '입는 쾌감'으로."""
        self.animator.particles.emit_combo_tier(self.player.x, self.player.y,
                                                item.color)

    def _buy_item(self, slot):
        if slot >= len(self.dungeon.shop_items):
            return
        item, price = self.dungeon.shop_items[slot]
        if self.player.gold < price:
            self.messages.append((t('no_gold'), 'warn')); self.audio.play('no_gold'); return
        if len(self.player.inventory) >= self.player.max_inventory:
            self.messages.append((t('inv_full'), 'warn')); return
        self.player.gold -= price
        self.player.inventory.append(item)
        self.dungeon.shop_items.pop(slot)
        self.messages.append((t('buy_ok', item.name, price), 'good'))
        self.audio.play('buy')

    def _use_teleport(self):
        candidates = [(x, y)
                      for y in range(self.dungeon.height)
                      for x in range(self.dungeon.width)
                      if (self.dungeon.tiles[y][x].explored and
                          not self.dungeon.tiles[y][x].blocked and
                          not self.dungeon.get_enemy_at(x, y) and
                          (x, y) != (self.player.x, self.player.y))]
        if candidates:
            self.player.x, self.player.y = random.choice(candidates)
            self.messages.append((t('teleport'), 'warn'))
            self.audio.play('teleport')
            self._start_shake(3, 150)

    # ─────────────── 스킬 ─────────────────────────────────────────────
    @property
    def _skill_atk(self) -> int:
        """스킬 데미지 기준 공격력 (장신구 강화 + 위력 인챈트 포함)."""
        return int(self.player.total_attack * self.player.skill_damage_mul * self._enchant_dmg_mul)

    # ── 드라이브 캔슬 ────────────────────────────────────────────────
    def _can_drive_cancel(self) -> bool:
        """공격 후딜(쿨다운/스윙) 중 + 드라이브 1칸 이상."""
        return ((self._atk_cd_timer > 0 or self._atk_phase != 0)
                and self.player.drive >= 1.0)

    def _do_drive_cancel(self):
        """후딜 삭제 + 게이지 소모 + CANCEL! 연출. 이어지는 공격도 보너스."""
        self.player.drive -= 1.0
        self._atk_cd_timer = 0.0
        self._atk_phase = 0
        self._atk_timer = 0
        self._cancel_bonus_ms = 1200
        self._spawn_afterimage(self.player.x, self.player.y)
        self.animator.add(CalloutAnim(self.player.x, self.player.y,
                                      'CANCEL!', (120, 230, 255)))
        self._start_punch_zoom(0.035, 90)
        self.audio.play('cancel')

    # W/A/S/D 스킬 쿨다운 시스템 비활성화 — SP(스태미나) 소모 체제로 전환.
    # True로 되돌리면 기존 쿨다운 게이트가 다시 활성화된다.
    _SKILL_COOLDOWNS_ENABLED = False

    # 스킬 카테고리별 SP 소모량
    _SKILL_STAMINA_COST = {'mobility': 15, 'defense': 20, 'attack': 22,
                           'buff': 20, 'blink': 38}

    def _use_skill(self, slot):
        skill_id = self._equipped_skills.get(slot)
        if not skill_id:
            return False
        sdef = ALL_SKILL_DEFS.get(skill_id)
        if not sdef:
            return False
        if self.player.level < sdef['level_req']:
            self.messages.append((t('skill_need_level', sdef['name'], sdef['level_req']), 'warn'))
            return False
        if self._SKILL_COOLDOWNS_ENABLED and not self.skills.ready(slot):
            self.messages.append((t('skill_cd', self.skills.remaining_sec(slot)), 'info'))
            return False
        _exec_map = {
            'flash_dash':  self._exec_flash_dash,
            'steel_whirl': self._exec_steel_whirl,
            'regen_breath': self._exec_regen_breath,
            'judgment':    self._exec_judgment,
            'shadow_step': self._exec_shadow_step,
            'iron_shell':  self._exec_iron_shell,
            'flame_strike': self._exec_flame_strike,
            'life_steal':  self._exec_life_steal,
            'war_cry':     self._exec_war_cry,
            'dark_pulse':  self._exec_dark_pulse,
            'power_shot':  self._exec_power_shot,
            'arrow_rain':  self._exec_arrow_rain,
            'flame_pool':  self._exec_flame_pool,
            'summon_familiar': self._exec_summon_familiar,
            'arcane_blink': self._exec_arcane_blink,
            'axe_throw':   self._exec_axe_throw,
            'berserk':     self._exec_berserk,
            'leap_smash':  self._exec_leap_smash,
        }
        fn = _exec_map.get(skill_id)
        if not fn:
            return False

        # SP 소모 (절약 인챈트가 소모량 절감)
        final = self._get_skill_final_stats(skill_id)
        cost = (self._SKILL_STAMINA_COST.get(sdef.get('category'), 20)
                * final['stamina_mul'])
        if not self._spend_stamina(cost):
            return False

        # 드라이브 캔슬: 공격 후딜 중 스킬 발동 시 후딜 삭제 + 데미지 +15%
        cancel_ok = self._can_drive_cancel()
        self._enchant_dmg_mul = final['dmg_mul'] * (1.15 if cancel_ok else 1.0)
        result = fn(slot)
        self._enchant_dmg_mul = 1.0
        if result and cancel_ok:
            self._do_drive_cancel()

        if result:
            if not self._SKILL_COOLDOWNS_ENABLED:
                self.skills.reset(slot)   # 실행부가 건 쿨다운 즉시 해제
            if final['arcane_eligible']:
                self._arcane_window_ms = 2000
                self._arcane_last_skill = skill_id
        else:
            # 스킬 불발 시 SP 환불 (실제 차감액 = 경감 적용 후)
            self.player.stamina = min(
                self.player.stamina_max,
                self.player.stamina + cost * (1.0 - self.player.total_sp_reduce))

        return result

    # ── 기본 장착 스킬 실행 ──────────────────────────────────────────────

    def _exec_flash_dash(self, slot):
        lvl   = self._skill_levels.get('flash_dash', 1)
        stats = ALL_SKILL_DEFS['flash_dash']['upgrades'][lvl - 1]
        tiles = stats['tiles']
        stagger_ms = stats['stagger_ms']
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0, 1))
        sx, sy = self.player.x, self.player.y
        moved = 0
        hit_enemy = False
        for _ in range(tiles):
            nx, ny = self.player.x + dx, self.player.y + dy
            enemy = self.dungeon.get_enemy_at(nx, ny)
            if enemy:
                self._player_attack(enemy)
                enemy.staggered_ms = stagger_ms
                self.animator.add(HitFlashAnim(nx, ny, 0, (100, 180, 255)))
                hit_enemy = True
                break
            if not self.dungeon.is_walkable(nx, ny): break
            self.player.x, self.player.y = nx, ny; moved += 1
        self.animator.particles.emit_dash_trail((sx, sy), (self.player.x, self.player.y))
        self._trigger_atk_anim()
        self._gain_skill_xp('flash_dash')
        if lvl >= SKILL_MAX_LEVEL and hit_enemy:
            self.skills.reset(slot)
        else:
            self.skills.trigger(slot)
        self.audio.play('skill_dash')
        self.messages.append((t('skill_dash', moved), 'warn'))
        return True

    def _exec_arcane_blink(self, slot):
        """마법사 점멸 — 벽을 무시하고 사거리 내 가장 먼 착지 가능 칸으로 순간이동."""
        lvl   = self._skill_levels.get('arcane_blink', 1)
        stats = ALL_SKILL_DEFS['arcane_blink']['upgrades'][lvl - 1]
        tiles = stats['tiles']
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        sx, sy = self.player.x, self.player.y
        # 먼 칸부터 검사 — 벽은 통과하되 착지는 바닥·적 없는 칸에만
        dest = None
        for i in range(tiles, 0, -1):
            nx, ny = sx + dx * i, sy + dy * i
            if not self.dungeon.in_bounds(nx, ny):
                continue
            if self.dungeon.tiles[ny][nx].blocked:
                continue
            if self.dungeon.get_enemy_at(nx, ny):
                continue
            dest = (nx, ny)
            break
        if dest is None:
            self.messages.append((t('skill_blink_fail'), 'info'))
            return False                       # 착지 불가 → 디스패치가 SP 환불
        # 순간이동 연출: 출발/도착 파티클 + 마법 궤적
        self.animator.particles.emit_death(sx, sy, (150, 110, 245))
        self.animator.add(MagicBoltAnim(sx, sy, dest[0], dest[1], self._facing,
                                        (170, 130, 250)))
        self.player.x, self.player.y = dest
        self.camera.center_on(dest[0], dest[1])
        if not self._is_test_mode:
            self.dungeon.update_visibility(dest[0], dest[1])
        self.animator.particles.emit_heal(dest[0], dest[1])
        self._trigger_atk_anim()
        self._gain_skill_xp('arcane_blink')
        self.skills.trigger(slot)
        self.audio.play('teleport')
        self.messages.append((t('skill_blink', abs(dest[0] - sx) + abs(dest[1] - sy)),
                              'warn'))
        return True

    # ── 도끼맨 전용 스킬 ──────────────────────────────────────────────
    def _apply_lifesteal(self, dmg):
        """광폭화/라그나로크 중이면 가한 피해의 일부를 흡혈로 회복."""
        p = self.player
        if p.lifesteal_ms > 0 and dmg > 0:
            p.hp = min(p.max_hp, p.hp + max(1, int(dmg * p.lifesteal_pct)))

    _AXE_ABANDON_CD = 10000   # 회수 안 하고 재투척 시 쿨타임(ms)

    def _exec_axe_throw(self, slot):
        """도끼 투척 — 직선 강타 후 바닥에 낙하.
        회수하면 즉시 재투척(+SP). 회수 안 하고 던지면 새 도끼를 쓰되 10초 쿨."""
        if self._axe_throw_cd_ms > 0:
            self.messages.append((t('axe_cd', self._axe_throw_cd_ms / 1000.0), 'info'))
            return False
        abandoned = self._thrown_axe is not None   # 회수 안 한 도끼가 있으면 버리고 새로
        lvl = self._skill_levels.get('axe_throw', 1)
        stats = ALL_SKILL_DEFS['axe_throw']['upgrades'][lvl - 1]
        rng, mul = stats['range'], stats['mul']
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        sx, sy = self.player.x, self.player.y
        land = (sx, sy)
        hits = 0
        for i in range(1, rng + 1):
            nx, ny = sx + dx * i, sy + dy * i
            if not self.dungeon.in_bounds(nx, ny) or self.dungeon.tiles[ny][nx].blocked:
                break
            enemy = self.dungeon.get_enemy_at(nx, ny)
            if enemy:
                dmg = roll_damage(self._skill_atk, enemy.defense, mul)
                enemy.take_damage(dmg); enemy.on_hurt(sx, sy)
                self._apply_lifesteal(dmg)
                self.animator.add(HitFlashAnim(nx, ny, dmg, (255, 150, 70)))
                self.animator.particles.emit_power_hit(nx, ny)
                hits += 1
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
            land = (nx, ny)
        self._thrown_axe = {'x': land[0], 'y': land[1]}
        self.animator.add(MagicBoltAnim(sx, sy, land[0], land[1], self._facing, (235, 170, 90)))
        self._trigger_atk_anim()
        self._gain_skill_xp('axe_throw', hits)
        self.skills.trigger(slot)
        self.audio.play('skill_whirl')
        if abandoned:
            self._axe_throw_cd_ms = self._AXE_ABANDON_CD   # 회수 안 함 → 10초 쿨
            self.messages.append((t('axe_abandon_cd'), 'warn'))
        else:
            self.messages.append((t('axe_thrown', hits) if hits else t('axe_thrown_miss'),
                                  'warn' if hits else 'info'))
        return True

    _AXE_RECALL_SP = 30   # 도끼 회수 시 SP 회복량(투척 비용보다 커서 순이득)

    def _retrieve_axe(self):
        """던져진 도끼 회수 — SP 회복 + 쿨 초기화 + 다시 던질 수 있게 됨."""
        self._thrown_axe = None
        self._axe_throw_cd_ms = 0        # 회수하면 쿨 초기화(회수 보상)
        p = self.player
        p.stamina = min(p.stamina_max, p.stamina + self._AXE_RECALL_SP)
        self.animator.add(CalloutAnim(self.player.x, self.player.y,
                                      t('axe_recall_sp', self._AXE_RECALL_SP),
                                      (245, 200, 110)))
        self.animator.particles.emit_heal(self.player.x, self.player.y)
        self.audio.play('pickup')

    def _exec_berserk(self, slot):
        """광폭화 — 공속↑ + 흡혈 + 공격력↑ 자가 버프 (느린 공속 보완)."""
        lvl = self._skill_levels.get('berserk', 1)
        s = ALL_SKILL_DEFS['berserk']['upgrades'][lvl - 1]
        p = self.player
        p.aspd_buff_ms = s['dur_ms'];  p.aspd_buff_pct = s['aspd_pct']
        p.lifesteal_ms = s['dur_ms'];  p.lifesteal_pct = s['lifesteal_pct']
        p.atk_bonus_ms = max(p.atk_bonus_ms, s['dur_ms'])
        p.atk_bonus_pct = max(p.atk_bonus_pct, s['atk_pct'])
        self.animator.add(BannerAnim(t('skill_berserk'), (235, 80, 60), size=24))
        self.animator.particles.emit_power_hit(p.x, p.y)
        self._white_flash_ms = 80
        self._gain_skill_xp('berserk')
        self.skills.trigger(slot)
        self.audio.play('levelup')
        return True

    def _exec_leap_smash(self, slot):
        """도약 강타 — 방향으로 도약 후 착지 지점 광역 강타."""
        lvl = self._skill_levels.get('leap_smash', 1)
        s = ALL_SKILL_DEFS['leap_smash']['upgrades'][lvl - 1]
        tiles, radius, mul = s['tiles'], s['radius'], s['mul']
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        sx, sy = self.player.x, self.player.y
        dest = (sx, sy)
        for i in range(1, tiles + 1):
            nx, ny = sx + dx * i, sy + dy * i
            if not self.dungeon.in_bounds(nx, ny) or self.dungeon.tiles[ny][nx].blocked:
                break
            if self.dungeon.get_enemy_at(nx, ny):
                break
            dest = (nx, ny)
        self.player.x, self.player.y = dest
        self.camera.center_on(*dest)
        if not self._is_test_mode:
            self.dungeon.update_visibility(*dest)
        self.animator.particles.emit_dash_trail((sx, sy), dest)
        hits = 0
        for ddx in range(-radius, radius + 1):
            for ddy in range(-radius, radius + 1):
                if ddx == 0 and ddy == 0:
                    continue
                nx, ny = dest[0] + ddx, dest[1] + ddy
                enemy = self.dungeon.get_enemy_at(nx, ny)
                if not enemy:
                    continue
                dmg = roll_damage(self._skill_atk, enemy.defense, mul)
                enemy.take_damage(dmg); enemy.on_hurt(*dest)
                self._apply_lifesteal(dmg)
                self.animator.add(HitFlashAnim(nx, ny, dmg, (255, 150, 70)))
                self.animator.particles.emit_basic_hit(nx, ny)
                hits += 1
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
        self.animator.add(WhirlAnim(dest[0], dest[1]))
        self.animator.particles.emit_whirl(*dest)
        self._start_shake(6, 220)
        self._trigger_atk_anim()
        self._gain_skill_xp('leap_smash', hits)
        self.skills.trigger(slot)
        self.audio.play('skill_whirl')
        self.messages.append((t('skill_leap', hits), 'warn'))
        return True

    _RAGNAROK_AURA_TICK = 260   # 오라 접촉 데미지 간격(ms)

    def _update_ragnarok_aura(self, dt):
        """라그나로크 중 — 인접(반경1) 적에게 주기적 접촉 데미지(닿기만 해도)."""
        self._ragnarok_aura_t += dt
        if self._ragnarok_aura_t < self._RAGNAROK_AURA_TICK:
            return
        self._ragnarok_aura_t = 0.0
        px, py = self.player.x, self.player.y
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1):
                if ddx == 0 and ddy == 0:
                    continue
                enemy = self.dungeon.get_enemy_at(px + ddx, py + ddy)
                if not enemy or not enemy.is_alive():
                    continue
                dmg = max(1, int(roll_damage(self.player.total_attack, enemy.defense, 0.6)))
                enemy.take_damage(dmg); enemy.on_hurt(px, py)
                self._apply_lifesteal(dmg)
                self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (255, 130, 60)))
                self.animator.particles.emit_basic_hit(enemy.x, enemy.y)
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)

    def _draw_ragnarok_aura(self, cx, cy):
        """라그나로크 중 플레이어 주위 맥동하는 화염 오라."""
        ts = TILE_SIZE
        s = self._game_surf
        px = (self.player.x - cx) * ts + ts // 2
        py = (self.player.y - cy) * ts + ts // 2
        tk = pygame.time.get_ticks()
        for ring in range(3):
            r = int(ts * (1.0 + ring * 0.55) + 4 * math.sin(tk / 130.0 + ring))
            a = int(90 - ring * 26 + 30 * math.sin(tk / 90.0 + ring * 1.7))
            if a <= 0:
                continue
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            col = (255, 120 - ring * 20, 40, max(0, a))
            pygame.draw.circle(glow, col, (r, r), r, 3)
            s.blit(glow, (px - r, py - r), special_flags=pygame.BLEND_ADD)

    def _ragnarok_swing(self):
        """라그나로크 중 기본 휘두르기 — 중거리(반경 2) 광역 강타."""
        if not self._spend_stamina(self._STAMINA_COST['slash']):
            return False
        self._trigger_atk_anim()
        px, py = self.player.x, self.player.y
        self.animator.add(WhirlAnim(px, py))
        self.animator.particles.emit_whirl(px, py)
        hits = 0
        for ddx in range(-2, 3):
            for ddy in range(-2, 3):
                if ddx == 0 and ddy == 0:
                    continue
                enemy = self.dungeon.get_enemy_at(px + ddx, py + ddy)
                if not enemy:
                    continue
                dmg = max(1, int(roll_damage(self.player.total_attack, enemy.defense, 1.4)))
                enemy.take_damage(dmg); enemy.on_hurt(px, py)
                self._apply_lifesteal(dmg)
                self.animator.add(SlashAnim(px, py, px + ddx, py + ddy, (255, 130, 60)))
                self.animator.add(HitFlashAnim(px + ddx, py + ddy, dmg, (255, 90, 60)))
                hits += 1
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
        self._atk_cd_timer = self.player.atk_cooldown_ms
        self.audio.play('skill_whirl')
        return True

    def _skill_ultimate_ragnarok(self):
        """라그나로크(도끼맨 R) — 수 초간 무적 + 이동·공격 강화 + 중거리 광역 휘두르기."""
        dur = 5000
        p = self.player
        p.invincible_ms = max(p.invincible_ms, dur)
        self._ragnarok_ms = dur
        self._ragnarok_aura_t = 0.0            # 접촉 오라 데미지 틱 누적
        p.aspd_buff_ms = max(p.aspd_buff_ms, dur); p.aspd_buff_pct = max(p.aspd_buff_pct, 0.8)
        p.lifesteal_ms = max(p.lifesteal_ms, dur); p.lifesteal_pct = max(p.lifesteal_pct, 0.3)
        p.move_buff_ms = max(p.move_buff_ms, dur); p.move_buff_pct = max(p.move_buff_pct, 0.6)
        self.animator.add(BannerAnim(t('ult_ragnarok'), (255, 90, 50), size=30))
        self.animator.particles.emit_levelup(p.x, p.y)
        self._start_punch_zoom(0.08, 200)
        self._start_shake(7, 400)
        self.skills.trigger('R')
        self.audio.play('levelup_big')
        self.messages.append((t('ult_ragnarok'), 'good'))
        return True

    def _exec_steel_whirl(self, slot, no_cooldown=False):
        lvl    = self._skill_levels.get('steel_whirl', 1)
        stats  = ALL_SKILL_DEFS['steel_whirl']['upgrades'][lvl - 1]
        radius = stats['radius']
        mul    = stats['mul']
        dirs = [(ddx, ddy) for ddx in range(-radius, radius+1)
                for ddy in range(-radius, radius+1)
                if not (ddx == 0 and ddy == 0)]
        hits = 0
        for ddx, ddy in dirs:
            nx, ny = self.player.x+ddx, self.player.y+ddy
            enemy = self.dungeon.get_enemy_at(nx, ny)
            if not enemy: continue
            crit = random.random() < 0.1
            dmg  = roll_damage(self._skill_atk, enemy.defense, mul)
            if crit: dmg *= 2
            enemy.take_damage(dmg)
            self.animator.add(SlashAnim(self.player.x, self.player.y, nx, ny, (255,180,60)))
            self.animator.add(HitFlashAnim(nx, ny, dmg, (255,80,80)))
            self.animator.particles.emit_basic_hit(nx, ny)
            hits += 1
            if not enemy.is_alive():
                self._on_enemy_killed(enemy)
        self.animator.add(WhirlAnim(self.player.x, self.player.y))
        self.animator.particles.emit_whirl(self.player.x, self.player.y)
        if not no_cooldown:
            self._gain_skill_xp('steel_whirl', hits)
            self.skills.trigger(slot)
        self.audio.play('skill_whirl')
        self.messages.append((t('skill_whirl_h', hits) if hits else t('skill_whirl_m'),
                               'warn' if hits else 'info'))
        return True

    def _skill_whirl(self, no_cooldown=False):
        """whirlwind 아이템 사용 시 호환용 — steel_whirl을 A 슬롯으로 직접 발동."""
        return self._exec_steel_whirl('A', no_cooldown=no_cooldown)

    def _exec_regen_breath(self, slot):
        lvl   = self._skill_levels.get('regen_breath', 1)
        stats = ALL_SKILL_DEFS['regen_breath']['upgrades'][lvl - 1]
        amt   = max(1, int(self.player.max_hp * stats['heal_pct']))
        self.player.heal(amt)
        self.player.heal_def_bonus = stats['def_bonus']
        self.player.heal_def_ms   = stats['def_ms']
        self.animator.add(HealAnim(self.player.x, self.player.y))
        self.animator.particles.emit_heal(self.player.x, self.player.y)
        self._gain_skill_xp('regen_breath')
        self.skills.trigger(slot)
        self.audio.play('skill_heal')
        self.messages.append((t('skill_heal', amt), 'good'))
        self.messages.append((t('skill_regen_def', stats['def_bonus'], stats['def_ms']//1000), 'good'))
        return True

    def _exec_judgment(self, slot):
        lvl   = self._skill_levels.get('judgment', 1)
        stats = ALL_SKILL_DEFS['judgment']['upgrades'][lvl - 1]
        mul   = stats['mul']
        crit_chance = stats['crit']
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0, 1))
        tx, ty = self.player.x + dx, self.player.y + dy
        enemy  = self.dungeon.get_enemy_at(tx, ty)
        self._trigger_atk_anim()
        self.animator.add(AttackSwingAnim(self.player.x, self.player.y, self._facing, hit=bool(enemy)))
        if not enemy:
            self.audio.play('swing')
            self.skills.trigger(slot)
            self.messages.append((t('skill_power_miss'), 'info'))
            return True
        crit = random.random() < crit_chance
        dmg  = roll_damage(self._skill_atk, enemy.defense, mul)
        if crit: dmg = int(dmg * 1.5)
        enemy.take_damage(dmg)
        self.animator.add(HitFlashAnim(tx, ty, dmg, (255, 120, 50)))
        self.animator.particles.emit_power_hit(tx, ty)
        if crit:
            self.audio.play('crit')
            self.messages.append((t('crit_hit', enemy.name, dmg), 'bad'))
        else:
            self.audio.play('attack')
            self.messages.append((t('skill_power', enemy.name, dmg), 'warn'))
        if not enemy.is_alive():
            self._on_enemy_killed(enemy)
        self._gain_skill_xp('judgment')
        self.skills.trigger(slot)
        return True

    # ── 추가 스킬 실행 ────────────────────────────────────────────────────

    def _exec_shadow_step(self, slot):
        lvl = self._skill_levels.get('shadow_step', 1)
        stats = ALL_SKILL_DEFS['shadow_step']['upgrades'][lvl - 1]
        tiles = stats['tiles']
        stagger_ms = [500, 800, 1000][lvl - 1]
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0, 1))
        sx, sy = self.player.x, self.player.y
        dest_x, dest_y = sx, sy
        for _ in range(tiles):
            nx, ny = dest_x + dx, dest_y + dy
            if not self.dungeon.is_walkable(nx, ny):
                break
            if self.dungeon.get_enemy_at(nx, ny):
                dest_x, dest_y = nx, ny
                break
            dest_x, dest_y = nx, ny
        enemy = self.dungeon.get_enemy_at(dest_x, dest_y)
        if enemy:
            enemy.staggered_ms = stagger_ms
            self.animator.add(HitFlashAnim(dest_x, dest_y, 0, (180, 100, 255)))
        else:
            self.player.x, self.player.y = dest_x, dest_y
        self.animator.particles.emit_dash_trail((sx, sy), (dest_x, dest_y))
        self._gain_skill_xp('shadow_step')
        self.skills.trigger(slot)
        self.audio.play('skill_dash')
        self.messages.append((t('skill_shadow_step'), 'warn'))
        return True

    def _exec_iron_shell(self, slot):
        lvl = self._skill_levels.get('iron_shell', 1)
        stats = ALL_SKILL_DEFS['iron_shell']['upgrades'][lvl - 1]
        self.player.damage_reduce_pct = stats['reduce']
        self.player.damage_reduce_ms  = stats['duration_ms']
        self.animator.add(HealAnim(self.player.x, self.player.y))
        self.animator.particles.emit_heal(self.player.x, self.player.y)
        self._gain_skill_xp('iron_shell')
        self.skills.trigger(slot)
        self.audio.play('skill_heal')
        self.messages.append((t('skill_iron_shell', int(stats["reduce"]*100), stats["duration_ms"]//1000), 'good'))
        return True

    def _exec_flame_strike(self, slot):
        lvl = self._skill_levels.get('flame_strike', 1)
        stats = ALL_SKILL_DEFS['flame_strike']['upgrades'][lvl - 1]
        range_ = stats['range']
        mul = stats['mul']
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0, 1))
        hits = 0
        for i in range(1, range_ + 1):
            nx, ny = self.player.x + dx*i, self.player.y + dy*i
            if not self.dungeon.in_bounds(nx, ny):
                break
            self.animator.add(BoltAnim(self.player.x, self.player.y, nx, ny, (255, 140, 40)))
            if not self.dungeon.is_walkable(nx, ny) and not self.dungeon.get_enemy_at(nx, ny):
                break
            enemy = self.dungeon.get_enemy_at(nx, ny)
            if enemy:
                dmg = roll_damage(self._skill_atk, enemy.defense, mul)
                enemy.take_damage(dmg)
                self.animator.add(HitFlashAnim(nx, ny, dmg, (255, 140, 40)))
                self.animator.particles.emit_power_hit(nx, ny)
                hits += 1
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
        self._gain_skill_xp('flame_strike', max(1, hits))
        self.skills.trigger(slot)
        self.audio.play('skill_dash')
        self.messages.append((t('skill_flame_hit', hits) if hits else t('skill_flame_miss'),
                               'warn' if hits else 'info'))
        return True

    # ── 궁수 스킬 ──────────────────────────────────────────────────────
    def _exec_power_shot(self, slot):
        lvl = self._skill_levels.get('power_shot', 1)
        stats = ALL_SKILL_DEFS['power_shot']['upgrades'][lvl - 1]
        rng, mul = stats['range'], stats['mul']
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        end = (self.player.x, self.player.y)
        hits = 0
        for i in range(1, rng + 1):
            nx, ny = self.player.x + dx * i, self.player.y + dy * i
            if not self.dungeon.in_bounds(nx, ny) or self.dungeon.tiles[ny][nx].block_sight:
                break
            end = (nx, ny)
            e = self.dungeon.get_enemy_at(nx, ny)
            if e:
                dmg = roll_damage(self._skill_atk, e.defense, mul)
                e.take_damage(dmg)
                self.animator.add(HitFlashAnim(nx, ny, dmg, (255, 170, 60)))
                self.animator.particles.emit_power_hit(nx, ny)
                hits += 1
                if not e.is_alive():
                    self._on_enemy_killed(e)
                # 관통 — 멈추지 않고 계속 진행
        self.animator.add(ArrowAnim(self.player.x, self.player.y,
                                    end[0], end[1], self._facing, (255, 190, 90)))
        self._trigger_atk_anim()
        self._start_shake(2, 130)
        self._gain_skill_xp('power_shot', max(1, hits))
        self.skills.trigger(slot)
        self.audio.play('bow_shoot')
        self.messages.append((t('skill_power_shot', hits) if hits
                              else t('skill_power_shot_miss'),
                              'warn' if hits else 'info'))
        return True

    def _exec_arrow_rain(self, slot):
        import random as _r
        lvl = self._skill_levels.get('arrow_rain', 1)
        stats = ALL_SKILL_DEFS['arrow_rain']['upgrades'][lvl - 1]
        radius, mul = stats['radius'], stats['mul']
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        cx = self.player.x + dx * (radius + 1)     # 전방 지역 중심
        cy = self.player.y + dy * (radius + 1)
        hits = 0
        for ddx in range(-radius, radius + 1):
            for ddy in range(-radius, radius + 1):
                if abs(ddx) + abs(ddy) > radius:
                    continue
                tx, ty = cx + ddx, cy + ddy
                if not self.dungeon.in_bounds(tx, ty):
                    continue
                e = self.dungeon.get_enemy_at(tx, ty)
                if e:
                    dmg = roll_damage(self._skill_atk, e.defense, mul)
                    e.take_damage(dmg)
                    self.animator.add(HitFlashAnim(tx, ty, dmg, (120, 200, 255)))
                    hits += 1
                    if not e.is_alive():
                        self._on_enemy_killed(e)
        for _ in range(12):                        # 화살 낙하 연출
            ox = _r.uniform(-radius, radius)
            oy = _r.uniform(-radius, radius)
            self.animator.add(ArrowAnim(cx + ox, cy - 5, cx + ox, cy + oy,
                                        'down', (150, 210, 255)))
        self.animator.particles.emit_frost_hit(cx, cy)
        self._trigger_atk_anim()
        self._gain_skill_xp('arrow_rain', max(1, hits))
        self.skills.trigger(slot)
        self.audio.play('bow_shoot')
        self.messages.append((t('skill_arrow_rain', hits) if hits
                              else t('skill_arrow_rain_miss'),
                              'warn' if hits else 'info'))
        return True

    # ── 마법사 스킬 ────────────────────────────────────────────────────
    def _exec_flame_pool(self, slot):
        lvl = self._skill_levels.get('flame_pool', 1)
        stats = ALL_SKILL_DEFS['flame_pool']['upgrades'][lvl - 1]
        r, base_dps, zone_ms = stats['radius'], stats['dps'], stats['zone_ms']
        # 스킬 공격력에 비례해 dps 스케일 (후반에도 유효)
        dps = base_dps + max(0, self._skill_atk // 8)
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        zx = self.player.x + dx * (r + 1)
        zy = self.player.y + dy * (r + 1)
        self._spawn_dot_zone(zx, zy, r, dps, zone_ms, col=(255, 120, 40))
        # 즉시 첫 점화 + 연출
        for e in self.dungeon.enemies:
            if e.is_alive() and abs(e.x - zx) <= r and abs(e.y - zy) <= r:
                self._apply_burn(e, dps=dps, ms=zone_ms, col=(255, 120, 40))
        self.animator.add(MagicBoltAnim(self.player.x, self.player.y, zx, zy,
                                        self._facing, (255, 140, 50)))
        self.animator.particles.emit_fireball_hit(zx, zy)
        self._gain_skill_xp('flame_pool', 2)
        self.skills.trigger(slot)
        self.audio.play('skill_dash')
        self.messages.append((t('skill_flame_pool'), 'warn'))
        return True

    def _exec_summon_familiar(self, slot):
        lvl = self._skill_levels.get('summon_familiar', 1)
        stats = ALL_SKILL_DEFS['summon_familiar']['upgrades'][lvl - 1]
        # 소환 상한(과다 방지)
        room = max(0, 4 - len(self._summons))
        n = min(stats['count'], room)
        if n <= 0:
            self.messages.append((t('skill_summon_full'), 'info'))
            return False
        self._spawn_summon(n, stats['summon_ms'], stats['mul'])
        self._gain_skill_xp('summon_familiar', 2)
        self.skills.trigger(slot)
        self.audio.play('skill_heal')
        self.messages.append((t('skill_summon', n), 'good'))
        return True

    def _exec_life_steal(self, slot):
        lvl = self._skill_levels.get('life_steal', 1)
        stats = ALL_SKILL_DEFS['life_steal']['upgrades'][lvl - 1]
        radius = stats['radius']
        steal_pct = stats['steal_pct']
        dirs = [(ddx, ddy) for ddx in range(-radius, radius+1)
                for ddy in range(-radius, radius+1)
                if not (ddx == 0 and ddy == 0)]
        total_dmg = 0
        for ddx, ddy in dirs:
            nx, ny = self.player.x+ddx, self.player.y+ddy
            enemy = self.dungeon.get_enemy_at(nx, ny)
            if not enemy: continue
            dmg = roll_damage(self._skill_atk, enemy.defense)
            enemy.take_damage(dmg)
            total_dmg += dmg
            self.animator.add(SlashAnim(self.player.x, self.player.y, nx, ny, (220, 80, 180)))
            self.animator.add(HitFlashAnim(nx, ny, dmg, (220, 80, 180)))
            if not enemy.is_alive():
                self._on_enemy_killed(enemy)
        heal = max(1, int(total_dmg * steal_pct)) if total_dmg else 0
        if heal:
            self.player.heal(heal)
            self.animator.add(HealAnim(self.player.x, self.player.y))
        self._gain_skill_xp('life_steal', max(1, total_dmg // 5 + 1))
        self.skills.trigger(slot)
        self.audio.play('skill_whirl')
        self.messages.append((t('skill_life_hit', heal) if heal else t('skill_life_miss'),
                               'good' if heal else 'info'))
        return True

    def _exec_war_cry(self, slot):
        lvl = self._skill_levels.get('war_cry', 1)
        stats = ALL_SKILL_DEFS['war_cry']['upgrades'][lvl - 1]
        self.player.atk_bonus_pct = stats['atk_mul']
        self.player.atk_bonus_ms  = stats['duration_ms']
        self.animator.add(HealAnim(self.player.x, self.player.y))
        self.animator.particles.emit_heal(self.player.x, self.player.y)
        self._gain_skill_xp('war_cry')
        self.skills.trigger(slot)
        self.audio.play('skill_heal')
        self.messages.append((t('skill_war_cry', int(stats["atk_mul"]*100), stats["duration_ms"]//1000), 'good'))
        return True

    def _exec_dark_pulse(self, slot):
        lvl = self._skill_levels.get('dark_pulse', 1)
        stats = ALL_SKILL_DEFS['dark_pulse']['upgrades'][lvl - 1]
        radius = stats['radius']
        mul = stats['mul']
        push = stats['push']
        stagger_ms = stats.get('stagger_ms', 0)
        dirs = [(ddx, ddy) for ddx in range(-radius, radius+1)
                for ddy in range(-radius, radius+1)
                if not (ddx == 0 and ddy == 0)]
        hits = 0
        for ddx, ddy in dirs:
            nx, ny = self.player.x+ddx, self.player.y+ddy
            enemy = self.dungeon.get_enemy_at(nx, ny)
            if not enemy: continue
            dmg = roll_damage(self._skill_atk, enemy.defense, mul)
            enemy.take_damage(dmg)
            hits += 1
            if stagger_ms:
                enemy.staggered_ms = stagger_ms
            push_dx = (1 if ddx > 0 else -1) if ddx != 0 else 0
            push_dy = (1 if ddy > 0 else -1) if ddy != 0 else 0
            for _ in range(push):
                px, py = enemy.x + push_dx, enemy.y + push_dy
                if self.dungeon.is_walkable(px, py) and not self.dungeon.get_enemy_at(px, py):
                    enemy.x, enemy.y = px, py
                else:
                    break
            self.animator.add(SlashAnim(self.player.x, self.player.y, nx, ny, (140, 80, 220)))
            self.animator.add(HitFlashAnim(nx, ny, dmg, (140, 80, 220)))
            self.animator.particles.emit_whirl(nx, ny)
            if not enemy.is_alive():
                self._on_enemy_killed(enemy)
        self.animator.add(WhirlAnim(self.player.x, self.player.y))
        self._gain_skill_xp('dark_pulse', max(1, hits))
        self.skills.trigger(slot)
        self.audio.play('skill_whirl')
        self.messages.append((t('skill_dark_hit', hits) if hits else t('skill_dark_miss'),
                               'warn' if hits else 'info'))
        return True

    # ─────────────── 스킬 강화 ───────────────────────────────────────
    def _apply_skill_level_cds(self):
        for slot in ('W', 'A', 'S', 'D'):
            skill_id = self._equipped_skills.get(slot)
            if not skill_id:
                continue
            stats = self._get_skill_final_stats(skill_id)
            self.skills.set_cd_override(slot, stats['cd_ms'])

    def _get_skill_final_stats(self, skill_id: str) -> dict:
        """인챈트 반영 최종 스킬 스탯을 반환."""
        sdef = ALL_SKILL_DEFS.get(skill_id)
        if not sdef:
            return {'dmg_mul': 1.0, 'cd_ms': 0, 'sp_threshold': 100,
                    'stamina_mul': 1.0, 'arcane_eligible': False}
        lvl = self._skill_levels.get(skill_id, 1)
        upgrades = sdef['upgrades']
        udata = upgrades[min(lvl - 1, len(upgrades) - 1)]
        base_cd = udata['cd_ms']
        enc = self._skill_enchants.get(skill_id, {})
        power_lvl = enc.get('power', 0)
        haste_lvl = enc.get('haste', 0)
        effi_lvl  = enc.get('efficiency', 0)
        arcane_lvl = enc.get('arcane', 0)
        dmg_mul      = 1.0 + power_lvl * 0.15
        cd_ms        = max(500, int(base_cd * (1.0 - haste_lvl * 0.10)))
        sp_threshold = max(40, 100 - effi_lvl * 15)   # (구) 오의 임계값 — 미사용
        return {
            'dmg_mul':        dmg_mul,
            'cd_ms':          cd_ms,
            'sp_threshold':   sp_threshold,
            'stamina_mul':    max(0.4, 1.0 - effi_lvl * 0.15),  # 절약: SP 소모 절감
            'arcane_eligible': arcane_lvl >= 1,
        }

    def _gain_skill_xp(self, skill_id: str, amount: int = 1):
        """스킬 적중 → 5회 누적마다 SP +1."""
        self._skill_xp[skill_id] = self._skill_xp.get(skill_id, 0) + amount
        gained = self._skill_xp[skill_id] // 5
        if gained > 0:
            self._skill_xp[skill_id] %= 5
            self._skill_points += gained

    def _do_skill_upgrade(self, skill_id: str):
        """스킬 도감에서 U 시 호출 — SP를 소모해 스킬 레벨업."""
        lvl = self._skill_levels.get(skill_id, 1)
        sname = ALL_SKILL_DEFS.get(skill_id, {}).get('name', skill_id)
        if lvl >= SKILL_MAX_LEVEL:
            self.messages.append((t('skill_upg_maxed', sname), 'warn'))
            return
        cost = SKILL_SP_COST.get(skill_id, [5, 10])[lvl - 1]
        if self._skill_points < cost:
            self.messages.append((t('skill_upg_nosp', cost, self._skill_points), 'warn'))
            return
        self._skill_points -= cost
        self._skill_levels[skill_id] = lvl + 1
        self._apply_skill_level_cds()
        self.messages.append((t('upg_done', sname, self._skill_levels[skill_id]), 'good'))
        self.audio.play('levelup')

    def _do_enchant_upgrade(self, skill_id: str, etype: str):
        """스킬 도감에서 1-4 키 시 호출 — SP를 소모해 인챈트 레벨업."""
        if etype not in ENCHANT_TYPES:
            return
        enc = self._skill_enchants.setdefault(
            skill_id, {'power': 0, 'haste': 0, 'efficiency': 0, 'arcane': 0})
        cur = enc.get(etype, 0)
        if cur >= ENCHANT_MAX_LEVEL:
            self.messages.append((t('enc_max'), 'warn'))
            return
        edef = ENCHANT_DEFS.get(etype, {})
        sp_costs = edef.get('sp_cost', [5, 10, 20])
        cost = sp_costs[cur] if cur < len(sp_costs) else 20
        if self._skill_points < cost:
            self.messages.append((t('enc_no_sp', cost, self._skill_points), 'warn'))
            return
        self._skill_points -= cost
        enc[etype] = cur + 1
        self._apply_skill_level_cds()
        sname = ALL_SKILL_DEFS.get(skill_id, {}).get('name', skill_id)
        ename = t(f'enc_type_{etype}')
        self.messages.append((t('enc_done', sname, ename, cur + 1), 'good'))
        self.audio.play('levelup')

    def _try_arcane_art(self) -> bool:
        """오의 연계 시도 — 오의 인챈트 스킬 직후 2초 창 안에 R.

        (구 오의 SP 임계값 시스템은 스태미나 SP 도입과 함께 제거 —
         이제 스태미나를 크게 소모하는 것으로 대가를 치른다)
        """
        skill_id = self._arcane_last_skill
        if not skill_id:
            self.messages.append((t('arcane_no_skill'), 'warn'))
            return False
        stats = self._get_skill_final_stats(skill_id)
        if not stats['arcane_eligible']:
            self.messages.append((t('arcane_no_enc'), 'warn'))
            return False
        if not self._spend_stamina(50):
            return False
        self._arcane_window_ms = 0
        self._arcane_last_skill = None
        self.messages.append((t('arcane_trigger'), 'warn'))
        return self._skill_ultimate_slash()


    # ─────────────── 조합 스킬 ───────────────────────────────────────
    def _use_combo_skill(self, combo_id):
        cdef = combo_def(combo_id, self.player.char_class)
        if not cdef:
            return False
        if combo_id not in self._unlocked_combos:
            if combo_id in self._skill_books:
                self.messages.append((t('combo_need_level', cdef['name'], cdef['level_req']), 'warn'))
            else:
                self.messages.append((t('combo_no_unlock', cdef['name'], cdef['level_req']), 'warn'))
            return False
        if not self.skills.ready(combo_id):
            self.messages.append((t('skill_cd', self.skills.remaining_sec(combo_id)), 'info'))
            return False
        # 조합 스킬은 스태미나 소모 (쿨다운 통과 후, 드라이브 소모 전)
        if not self._spend_stamina(self._STAMINA_COST['combo_skill']):
            return False
        cancel_ok = self._can_drive_cancel()
        if cancel_ok:
            self._do_drive_cancel()
        axe = self.player.char_class == 'axeman'
        if combo_id == 'WS': return self._skill_fortify()
        if combo_id == 'AD':
            if self.player.char_class == 'archer': return self._skill_auto_volley()
            if axe: return self._skill_axe_storm()
            return self._skill_thunder()
        if combo_id == 'WA':
            return self._skill_earthbreaker() if axe else self._skill_frost()
        if combo_id == 'WD':
            return self._skill_axe_charge() if axe else self._skill_wind()
        return False

    def _skill_fireball(self):
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0, 1))
        px, py = self.player.x, self.player.y
        hit = False
        bolt_end = (px + dx * 5, py + dy * 5)
        for step in range(1, 6):
            tx, ty = px + dx * step, py + dy * step
            if not self.dungeon.is_walkable(tx, ty) and not self.dungeon.get_enemy_at(tx, ty):
                bolt_end = (tx, ty)
                self.animator.add(BoltAnim(px, py, tx, ty, (255, 140, 40)))
                break
            enemy = self.dungeon.get_enemy_at(tx, ty)
            if enemy:
                bolt_end = (tx, ty)
                crit = random.random() < 0.3
                dmg  = roll_damage(self._skill_atk, enemy.defense, 2.2)
                if crit: dmg = int(dmg * 1.5)
                enemy.take_damage(dmg)
                self.animator.add(BoltAnim(px, py, tx, ty, (255, 140, 40)))
                self.animator.add(HitFlashAnim(tx, ty, dmg, (255, 100, 30)))
                self.animator.particles.emit_fireball_hit(tx, ty)
                if crit:
                    self.messages.append((t('crit_hit', enemy.name, dmg), 'bad'))
                else:
                    self.messages.append((t('skill_fireball', enemy.name, dmg), 'warn'))
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
                hit = True
                break
        self.animator.particles.emit_fireball_trail((px, py), bolt_end)
        if not hit:
            self.messages.append((t('skill_fireball_m'), 'info'))
        self.audio.play('skill_dash')
        self.skills.trigger('WS')
        return True

    def _skill_thunder(self):
        targets = [e for e in self.dungeon.enemies
                   if e.is_alive() and self.dungeon.tiles[e.y][e.x].visible]
        random.shuffle(targets)
        targets = targets[:5]
        hits = 0
        for enemy in targets:
            dmg = roll_damage(self._skill_atk, enemy.defense, 1.2)
            enemy.take_damage(dmg)
            self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (200, 160, 255)))
            self.animator.particles.emit_thunder_hit(enemy.x, enemy.y)
            hits += 1
            if not enemy.is_alive():
                self._on_enemy_killed(enemy)
        if hits:
            self._start_shake(4, 350)
            self.messages.append((t('skill_thunder', hits), 'warn'))
        else:
            self.messages.append((t('skill_thunder_m'), 'info'))
        self.audio.play('skill_whirl')
        self.skills.trigger('AD')
        return True

    # ── 궁수 자동 사격 (Auto Volley) ─────────────────────────────────────
    _AUTO_VOLLEY_INTERVAL = 480   # ms, 발사 간격
    _AUTO_VOLLEY_RANGE    = 11    # 타일 (맨해튼)

    def _skill_auto_volley(self):
        """발동 시 일정 시간 자동으로 화살을 발사하는 버프. 강화(D스킬 Lv) 연동."""
        lvl = self._skill_levels.get(self._equipped_skills.get('D', 'power_shot'), 1)
        lvl = max(1, min(3, lvl))
        dur = 10000 * lvl                         # 10 / 20 / 30초
        mul = 1.0 + 0.4 * (lvl - 1)               # Lv1 1.0 · Lv2 1.4 · Lv3 1.8
        p = self.player
        p.auto_volley_ms   = dur
        p.auto_volley_mul  = mul
        p.auto_volley_tick = 0                     # 즉시 첫 발
        # 쿨다운 = 지속시간 + 5초 (짧은 공백)
        self.skills.set_cd_override('AD', dur + 5000)
        self.skills.trigger('AD')
        self.audio.play('bow_shoot')
        self.messages.append((t('skill_auto_volley', dur // 1000), 'good'))
        self.animator.add(CalloutAnim(p.x, p.y, 'AUTO!', (120, 220, 255)))
        return True

    def _update_auto_volley(self, dt):
        p = self.player
        if getattr(p, 'auto_volley_ms', 0) <= 0:
            return
        p.auto_volley_ms = max(0, p.auto_volley_ms - dt)
        p.auto_volley_tick -= dt
        if p.auto_volley_tick > 0:
            return
        p.auto_volley_tick += self._AUTO_VOLLEY_INTERVAL
        # 가장 가까운 시야 내 생존 적
        best, bestd = None, 999
        for e in self.dungeon.enemies:
            if not e.is_alive() or not self.dungeon.tiles[e.y][e.x].visible:
                continue
            d = abs(e.x - p.x) + abs(e.y - p.y)
            if d <= self._AUTO_VOLLEY_RANGE and d < bestd:
                best, bestd = e, d
        if best is None:
            return
        dx, dy = best.x - p.x, best.y - p.y
        face = ('right' if dx > 0 else 'left') if abs(dx) >= abs(dy) \
            else ('down' if dy > 0 else 'up')
        self.animator.add(ArrowAnim(p.x, p.y, best.x, best.y, face, (150, 230, 255)))
        self.audio.play('bow_shoot')
        dmg = roll_damage(self._skill_atk, best.defense, p.auto_volley_mul)
        best.take_damage(dmg)
        self.animator.add(HitFlashAnim(best.x, best.y, dmg, (150, 230, 255)))
        self.animator.particles.emit_basic_hit(best.x, best.y)
        if not best.is_alive():
            self._on_enemy_killed(best)

    def _skill_frost(self):
        px, py = self.player.x, self.player.y
        hits = 0
        for enemy in list(self.dungeon.enemies):
            if not enemy.is_alive():
                continue
            if max(abs(enemy.x - px), abs(enemy.y - py)) <= 3:
                dmg = roll_damage(self._skill_atk, enemy.defense, 1.3)
                enemy.take_damage(dmg)
                self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (100, 220, 255)))
                self.animator.particles.emit_frost_hit(enemy.x, enemy.y)
                hits += 1
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
        self.animator.add(WhirlAnim(px, py))
        if hits:
            self.messages.append((t('skill_frost', hits), 'good'))
        else:
            self.messages.append((t('skill_frost_m'), 'info'))
        self.audio.play('skill_heal')
        self.skills.trigger('WA')
        return True

    def _skill_wind(self):
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0, 1))
        px, py = self.player.x, self.player.y
        hits = 0
        end_x, end_y = px, py
        for step in range(1, 9):
            tx, ty = px + dx * step, py + dy * step
            if not (0 <= tx < self.dungeon.width and 0 <= ty < self.dungeon.height):
                break
            if not self.dungeon.is_walkable(tx, ty) and not self.dungeon.get_enemy_at(tx, ty):
                end_x, end_y = tx, ty
                break
            end_x, end_y = tx, ty
            enemy = self.dungeon.get_enemy_at(tx, ty)
            if enemy and enemy.is_alive():
                dmg = roll_damage(self._skill_atk, enemy.defense, 1.8)
                enemy.take_damage(dmg)
                self.animator.add(SlashAnim(px, py, tx, ty, (160, 255, 160)))
                self.animator.add(HitFlashAnim(tx, ty, dmg, (160, 255, 160)))
                self.animator.particles.emit_wind_hit(tx, ty, dx, dy)
                hits += 1
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
        self.animator.particles.emit_wind_sweep((px, py), (end_x, end_y), dx, dy)
        if hits:
            self.messages.append((t('skill_wind', hits), 'warn'))
        else:
            self.messages.append((t('skill_wind_m'), 'info'))
        self.audio.play('skill_dash')
        self.skills.trigger('WD')
        return True

    # ── 도끼맨 강화 스킬 (물리 도끼 기술) ──────────────────────────────
    def _skill_axe_storm(self):
        """도끼 폭풍(도끼맨 AD) — 반경3을 2연타로 휩쓰는 회전 강타."""
        px, py = self.player.x, self.player.y
        hits = 0
        for _pass in range(2):
            for enemy in list(self.dungeon.enemies):
                if not enemy.is_alive():
                    continue
                if max(abs(enemy.x - px), abs(enemy.y - py)) <= 3:
                    dmg = roll_damage(self._skill_atk, enemy.defense, 1.5)
                    enemy.take_damage(dmg); enemy.on_hurt(px, py)
                    self._apply_lifesteal(dmg)
                    self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (255, 150, 70)))
                    self.animator.particles.emit_basic_hit(enemy.x, enemy.y)
                    hits += 1
                    if not enemy.is_alive():
                        self._on_enemy_killed(enemy)
        self.animator.add(WhirlAnim(px, py))
        self.animator.add(ShockwaveAnim(px, py, color=(220, 190, 150), rmax=3.2, dur=440))
        self.animator.particles.emit_whirl(px, py)
        self.animator.particles.emit_death(px, py, (150, 135, 108))
        self._start_shake(6, 260)
        self.audio.play('skill_whirl')
        self.messages.append((t('skill_axe_storm', hits) if hits else t('skill_axe_storm_m'),
                              'warn' if hits else 'info'))
        self.skills.trigger('AD')
        return True

    def _skill_earthbreaker(self):
        """대지 분쇄(도끼맨 WA) — 전방 직선을 내려찍어 균열 충격파 + 경직."""
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        px, py = self.player.x, self.player.y
        hits = 0
        for step in range(1, 6):
            tx, ty = px + dx * step, py + dy * step
            if not self.dungeon.in_bounds(tx, ty) or self.dungeon.tiles[ty][tx].blocked:
                break
            self.animator.add(ShockwaveAnim(tx, ty, color=(210, 185, 140), rmax=1.25, dur=300))
            self.animator.particles.emit_death(tx, ty, (150, 135, 108))
            for wx, wy in ((tx, ty), (tx + dy, ty + dx), (tx - dy, ty - dx)):  # 폭(직교 1칸)
                enemy = self.dungeon.get_enemy_at(wx, wy)
                if enemy and enemy.is_alive():
                    dmg = roll_damage(self._skill_atk, enemy.defense, 2.2)
                    enemy.take_damage(dmg); enemy.on_hurt(px, py)
                    enemy.staggered_ms = max(getattr(enemy, 'staggered_ms', 0), 800)
                    self._apply_lifesteal(dmg)
                    self.animator.add(HitFlashAnim(wx, wy, dmg, (255, 140, 60)))
                    hits += 1
                    if not enemy.is_alive():
                        self._on_enemy_killed(enemy)
        self._start_shake(7, 300)
        self._white_flash_ms = 60
        self.audio.play('skill_whirl')
        self.messages.append((t('skill_earthbreaker', hits) if hits else t('skill_earthbreaker_m'),
                              'warn' if hits else 'info'))
        self.skills.trigger('WA')
        return True

    def _skill_axe_charge(self):
        """광란의 강습(도끼맨 WD) — 전방으로 돌진하며 경로의 적을 베어넘김."""
        dx, dy = self._DIRS.get(self._facing, (0, 1))
        px, py = self.player.x, self.player.y
        hits = 0
        dest = (px, py)
        for step in range(1, 7):
            tx, ty = px + dx * step, py + dy * step
            if not self.dungeon.in_bounds(tx, ty) or self.dungeon.tiles[ty][tx].blocked:
                break
            enemy = self.dungeon.get_enemy_at(tx, ty)
            if enemy and enemy.is_alive():
                dmg = roll_damage(self._skill_atk, enemy.defense, 2.0)
                enemy.take_damage(dmg); enemy.on_hurt(px, py)
                enemy.staggered_ms = max(getattr(enemy, 'staggered_ms', 0), 500)
                self._apply_lifesteal(dmg)
                self.animator.add(SlashAnim(px, py, tx, ty, (255, 150, 70)))
                self.animator.add(HitFlashAnim(tx, ty, dmg, (255, 120, 50)))
                hits += 1
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
            else:
                dest = (tx, ty)            # 관통은 하되 착지는 빈 칸까지
        self.player.x, self.player.y = dest
        self.camera.center_on(*dest)
        if not self._is_test_mode:
            self.dungeon.update_visibility(*dest)
        self.animator.particles.emit_dash_trail((px, py), dest)
        self.animator.add(ShockwaveAnim(dest[0], dest[1], color=(210, 185, 140), rmax=1.6, dur=320))
        self._start_shake(5, 220)
        self.audio.play('skill_dash')
        self.messages.append((t('skill_axe_charge', hits) if hits else t('skill_axe_charge_m'),
                              'warn' if hits else 'info'))
        self.skills.trigger('WD')
        return True

    # ─────────────── 강화술 ──────────────────────────────────────────
    def _skill_fortify(self):
        cdef = COMBO_SKILL_DEFS['WS']
        dur  = cdef['duration_ms']

        # 이미 활성 상태면 스탯 복원 후 재적용
        self._remove_fortify_buff()

        self._fortify_def_bonus  = cdef['defense_bonus']
        self._fortify_atk_bonus  = cdef['atk_speed_bonus']
        self.player.defense      += self._fortify_def_bonus
        self.player.attack_speed += self._fortify_atk_bonus
        self.input.set_move_speed(self.player.total_move_speed)

        self._fortify_effect = SkillEffect(cdef['color'], dur)

        dur_sec = dur // 1000
        self.messages.append((
            t('skill_fortify',
              f'+{self._fortify_atk_bonus:.1f}',
              f'+{self._fortify_def_bonus}',
              dur_sec),
            'good',
        ))
        self.audio.play('levelup')
        self.skills.trigger('WS')
        return True

    def _update_fortify(self, dt_ms: int):
        if self._fortify_effect is None:
            return
        self._fortify_effect.update(dt_ms)
        if not self._fortify_effect.alive:
            self._remove_fortify_buff()
            self._fortify_effect = None
            self.messages.append((t('skill_fortify_end'), 'info'))

    # ── 장비 강화 ───────────────────────────────────────────────────────────
    _ENHANCE_SLOTS  = ['head', 'body', 'weapon', 'off_hand', 'accessory', 'feet']
    _ENHANCE_MAX    = 18
    _ENHANCE_RATES  = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0,   # +0→+5
                       0.8, 0.8, 0.8,                    # +6→+8
                       0.6, 0.6, 0.6,                    # +9→+11
                       0.4, 0.4, 0.4,                    # +12→+14
                       0.2, 0.2, 0.2]                    # +15→+17

    def _skillbook_avail_skills(self):
        """현재 플레이어 레벨에서 사용 가능한 스킬 id 목록."""
        return [sid for sid, sdef in ALL_SKILL_DEFS.items()
                if self.player.level >= sdef.get('level_req', 1)]

    def _handle_skillbook_key(self, key):
        import pygame
        avail = self._skillbook_avail_skills()
        total = 4 + len(avail)
        SLOTS = ('W', 'A', 'S', 'D')

        def _exit_equip():
            self._skillbook_equip_mode = False
            self._skillbook_target_slot = None
            self._skillbook_equip_skill_id = None

        if self._skillbook_equip_mode:
            if self._skillbook_equip_skill_id is not None:
                # ── pick_slot 모드: 스킬 → 슬롯 선택 ──────────────────
                if key in (pygame.K_UP, pygame.K_w):
                    self._skillbook_equip_cursor = (self._skillbook_equip_cursor - 1) % 4
                elif key in (pygame.K_DOWN, pygame.K_s):
                    self._skillbook_equip_cursor = (self._skillbook_equip_cursor + 1) % 4
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    slot = SLOTS[self._skillbook_equip_cursor]
                    sid  = self._skillbook_equip_skill_id
                    self._equipped_skills[slot] = sid
                    sname = ALL_SKILL_DEFS[sid]['name']
                    self.messages.append((t('skill_equip_slot', slot, sname), 'good'))
                    self._apply_skill_level_cds()
                    _exit_equip()
                elif key == pygame.K_ESCAPE:
                    _exit_equip()
            else:
                # ── pick_skill 모드: 슬롯 → 스킬 선택 ─────────────────
                if key in (pygame.K_UP, pygame.K_w):
                    self._skillbook_equip_cursor = (self._skillbook_equip_cursor - 1) % max(1, len(avail))
                elif key in (pygame.K_DOWN, pygame.K_s):
                    self._skillbook_equip_cursor = (self._skillbook_equip_cursor + 1) % max(1, len(avail))
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    if avail and self._skillbook_equip_cursor < len(avail):
                        chosen = avail[self._skillbook_equip_cursor]
                        target = self._skillbook_target_slot
                        if target:
                            self._equipped_skills[target] = chosen
                            sname = ALL_SKILL_DEFS[chosen]['name']
                            self.messages.append((t('skill_equip_slot', target, sname), 'good'))
                            self._apply_skill_level_cds()
                    _exit_equip()
                elif key == pygame.K_ESCAPE:
                    _exit_equip()
        else:
            # ── 일반 탐색 ───────────────────────────────────────────────
            if key in (pygame.K_UP, pygame.K_w):
                self._skillbook_cursor = (self._skillbook_cursor - 1) % max(1, total)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self._skillbook_cursor = (self._skillbook_cursor + 1) % max(1, total)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                if self._skillbook_cursor < 4:
                    # 슬롯 행 → pick_skill 모드 진입
                    self._skillbook_equip_mode = True
                    self._skillbook_target_slot = SLOTS[self._skillbook_cursor]
                    self._skillbook_equip_skill_id = None
                    self._skillbook_equip_cursor = 0
                else:
                    avail_idx = self._skillbook_cursor - 4
                    if avail_idx < len(avail):
                        # 스킬 행 → pick_slot 모드 진입
                        self._skillbook_equip_mode = True
                        self._skillbook_equip_skill_id = avail[avail_idx]
                        self._skillbook_target_slot = None
                        self._skillbook_equip_cursor = 0
            elif key == pygame.K_u:
                # U 키: SP 소모 스킬 레벨업
                if self._skillbook_cursor < 4:
                    slot = SLOTS[self._skillbook_cursor]
                    sid = self._equipped_skills.get(slot)
                    if sid:
                        self._do_skill_upgrade(sid)
                else:
                    avail_idx = self._skillbook_cursor - 4
                    if avail_idx < len(avail):
                        self._do_skill_upgrade(avail[avail_idx])
            elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                # 1-4 키: 인챈트 업그레이드 (위력/신속/절약/오의)
                etype_idx = key - pygame.K_1
                etype = ENCHANT_TYPES[etype_idx]
                if self._skillbook_cursor < 4:
                    slot = SLOTS[self._skillbook_cursor]
                    sid = self._equipped_skills.get(slot)
                    if sid:
                        self._do_enchant_upgrade(sid, etype)
                else:
                    avail_idx = self._skillbook_cursor - 4
                    if avail_idx < len(avail):
                        self._do_enchant_upgrade(avail[avail_idx], etype)
            elif key in (pygame.K_ESCAPE, pygame.K_k):
                self._skillbook_open = False

    def _handle_enhance_key(self, key):
        import pygame
        slots = self._ENHANCE_SLOTS
        if key in (pygame.K_UP, pygame.K_w):
            self._enhance_cursor = (self._enhance_cursor - 1) % len(slots)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self._enhance_cursor = (self._enhance_cursor + 1) % len(slots)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self._do_enhance(slots[self._enhance_cursor])
        elif key == pygame.K_r and self._enhance_mode == 'gold':
            self._do_repair(slots[self._enhance_cursor])      # 대장장이: 선택 수리
        elif key == pygame.K_t and self._enhance_mode == 'gold':
            self._do_repair_all()                             # 대장장이: 전체 수리
        elif key in (pygame.K_ESCAPE, pygame.K_p):
            self._enhance_open = False

    # ── 대장장이 수리 (내구도) ────────────────────────────────────────
    def _repair_cost(self, item) -> int:
        return (item.max_durability - item.durability) * 2

    def _do_repair(self, slot: str) -> bool:
        item = self.player.equipment.get(slot)
        if not item or item.max_durability <= 0:
            self.messages.append((t('enhance_no_item'), 'warn'))
            return False
        missing = item.max_durability - item.durability
        if missing <= 0:
            self.messages.append((t('repair_full'), 'info'))
            return False
        cost = self._repair_cost(item)
        if self.player.gold < cost:
            self.messages.append((t('no_gold'), 'warn'))
            self.audio.play('no_gold')
            return False
        self.player.gold -= cost
        item.durability = item.max_durability
        self.messages.append((t('repair_done', item.name, cost), 'good'))
        # 수리 연출: 망치질 스파크 (자리: 히트스톱/모루 사운드 확장 가능)
        self.animator.particles.emit_basic_hit(self.player.x, self.player.y)
        self.audio.play('buy')
        return True

    def _do_repair_all(self):
        repaired = 0
        for slot in self._ENHANCE_SLOTS:
            item = self.player.equipment.get(slot)
            if item and item.max_durability > 0 and item.durability < item.max_durability:
                if not self._do_repair(slot):
                    break
                repaired += 1
        if repaired == 0:
            self.messages.append((t('repair_full'), 'info'))

    def _do_enhance(self, slot: str):
        import random
        import pygame as _pg
        item = self.player.equipment.get(slot)
        if not item:
            self.messages.append((t('enhance_no_item'), 'warn'))
            return
        if item.enhance_level >= self._ENHANCE_MAX:
            self.messages.append((t('enhance_max', item.name), 'warn'))
            return
        if self._enhance_mode == 'gold':
            # 대장장이: 골드 소모 (단계 비례 가격)
            cost = self._smith_cost(item)
            if self.player.gold < cost:
                self.messages.append((t('no_gold'), 'warn'))
                self.audio.play('no_gold')
                return
            self.player.gold -= cost
        else:
            if self.player.enhance_stones < 1:
                self.messages.append((t('enhance_no_stone'), 'warn'))
                return
            self.player.enhance_stones -= 1
        rate = self._ENHANCE_RATES[item.enhance_level]
        if random.random() < rate:
            item.enhance_level += 1
            if item.enhance_level >= 10:
                self._ach_unlock('ACH_ENHANCE_10')
            self.messages.append((t('enhance_success', item.name, item.enhance_level), 'good'))
            self.audio.play('levelup')
            self._start_shake(3, 200)
            self.animator.add(HitFlashAnim(self.player.x, self.player.y, 0, (255, 215, 0)))
            self.animator.particles.emit_heal(self.player.x, self.player.y)
            self._enhance_result = ('success', _pg.time.get_ticks(), self._enhance_cursor)
        else:
            self.messages.append((t('enhance_fail', item.name, item.enhance_level), 'warn'))
            self._start_shake(7, 380)
            self.animator.add(HitFlashAnim(self.player.x, self.player.y, 0, (200, 40, 40)))
            self.audio.play('player_hit')
            self._enhance_result = ('fail', _pg.time.get_ticks(), self._enhance_cursor)

    def _do_respawn(self):
        """보스·버닝 스테이지를 제외한 일반 층에서 몬스터 1마리 리스폰."""
        import random as _rnd
        from map.generator import _enemy_pool, _scale_enemy
        from entities.enemy import Enemy

        # 플레이어 시야 밖의 빈 바닥 타일 후보 수집 (거리 5 이상, 시야 밖 우선)
        candidates = []
        fallback   = []
        for y in range(self.dungeon.height):
            for x in range(self.dungeon.width):
                tile = self.dungeon.tiles[y][x]
                if tile.blocked:
                    continue
                if self.dungeon.get_enemy_at(x, y):
                    continue
                dist = abs(x - self.player.x) + abs(y - self.player.y)
                if dist < 5:
                    continue
                if not tile.visible:
                    candidates.append((x, y))
                else:
                    fallback.append((x, y))   # 시야 안이지만 거리는 충분

        spawn_list = candidates if candidates else fallback
        if not spawn_list:
            return

        sx, sy = _rnd.choice(spawn_list)
        pool = _enemy_pool(self.floor, getattr(self.dungeon, 'theme_index', 0))
        if not pool:
            return

        key  = _rnd.choice(pool)
        if key not in self._enemy_data:
            return
        from map.generator import maybe_make_elite
        data = _scale_enemy(self._enemy_data[key], self.floor)
        data['key'] = key
        data = maybe_make_elite(data, self.floor)
        enemy = Enemy(sx, sy, data)
        self.dungeon.enemies.append(enemy)
        if enemy.elite:
            self.messages.append((t('elite_appear', enemy.name), 'warn'))
        else:
            self.messages.append((t('monster_appear'), 'warn'))

    def _remove_fortify_buff(self):
        if self._fortify_def_bonus or self._fortify_atk_bonus:
            self.player.defense      -= self._fortify_def_bonus
            self.player.attack_speed -= self._fortify_atk_bonus
            self.player.attack_speed  = max(0.5, self.player.attack_speed)
            self._fortify_def_bonus   = 0
            self._fortify_atk_bonus   = 0.0

    # ─────────────── 궁극기 ─────────────────────────────────────────────
    def _use_ultimate(self, key: str):
        # 오의 창이 열려 있으면 R키를 오의 발동으로 우선 처리
        if key == 'R' and self._arcane_window_ms > 0:
            return self._try_arcane_art()

        udef = ULTIMATE_SKILL_DEFS.get(key)
        if not udef:
            return False
        if self.player.level < udef['level_req']:
            self.messages.append((
                t('ult_no_level', udef['name'], udef['level_req'], self.player.level), 'warn'))
            return False
        if not self.skills.ready(key):
            self.messages.append((t('skill_cd', self.skills.remaining_sec(key)), 'info'))
            return False
        if key == 'R':
            if self.player.char_class == 'mage':
                result = self._skill_ultimate_inferno()
            elif self.player.char_class == 'axeman':
                result = self._skill_ultimate_ragnarok()
            else:
                result = self._skill_ultimate_breaker()
        elif key == 'Ctrl_R':
            result = self._skill_ultimate_slash()
        else:
            return False
        if result:
            self._ach_unlock('ACH_ULTIMATE')
        return result

    def _skill_ultimate_breaker(self):
        """던전 브레이커: 화면 내 모든 적에게 공격력 3배 일격 + 대규모 이펙트."""
        targets = [e for e in self.dungeon.enemies
                   if e.is_alive() and self.dungeon.tiles[e.y][e.x].visible]
        hits = 0
        for enemy in targets:
            dmg = roll_damage(self._skill_atk, enemy.defense, 3.0)
            enemy.take_damage(dmg)
            self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (255, 80, 80)))
            self.animator.particles.emit_power_hit(enemy.x, enemy.y)
            hits += 1
            if not enemy.is_alive():
                self._on_enemy_killed(enemy)
        # 여러 방향으로 슬래시 이펙트
        px, py = self.player.x, self.player.y
        for facing in ('right', 'left', 'up', 'down'):
            self.animator.add(SlashAnim(px, py, px, py, (255, 120, 60)))
        # 던전 브레이커 — 시야 내 균열 벽도 전부 붕괴 (이름값)
        self._break_cracked_walls_near(px, py, 12)
        self._start_shake(8, 500)
        self.skills.trigger('R')
        self.audio.play('skill_whirl')
        if hits:
            self.messages.append((t('ult_breaker_hit', hits), 'bad'))
        else:
            self.messages.append((t('ult_breaker_miss'), 'info'))
        return True

    def _skill_ultimate_inferno(self):
        """인페르노(마법사 R): 화면 전역에 화염 장판 도배 + 전 적 강점화 + 정령 소환."""
        cx, cy = self.camera.x, self.camera.y
        dps = 20 + max(0, self._skill_atk // 5)
        # 시야 격자 곳곳에 장판
        for gy in range(2, VIEWPORT_TILES_Y - 1, 3):
            for gx in range(2, VIEWPORT_TILES_X - 1, 3):
                wx, wy = cx + gx, cy + gy
                if self.dungeon.in_bounds(wx, wy) and self.dungeon.tiles[wy][wx].visible \
                        and not self.dungeon.tiles[wy][wx].blocked:
                    self._spawn_dot_zone(wx, wy, 1, dps, 6000, col=(255, 110, 35))
        # 화면 내 전 적 즉시 강점화 + 초기 타격
        hits = 0
        for e in self.dungeon.enemies:
            if e.is_alive() and self.dungeon.tiles[e.y][e.x].visible:
                self._hurt_enemy(e, roll_damage(self._skill_atk, e.defense, 1.5),
                                 (255, 120, 40))
                self._apply_burn(e, dps=dps, ms=6000, col=(255, 110, 35))
                hits += 1
        # 정령 지원군 + 시야 내 균열 벽 붕괴
        self._spawn_summon(min(3, max(0, 4 - len(self._summons))), 10000, 0.9)
        self._break_cracked_walls_near(self.player.x, self.player.y, 12)
        self._start_shake(8, 520)
        self._start_punch_zoom(0.06, 160)
        self.skills.trigger('R')
        self.audio.play('skill_whirl')
        self.messages.append((t('skill_inferno'), 'bad'))
        return True

    def _skill_ultimate_slash(self):
        """진(眞) 일도양단: 2초 무적 + 화면 내 모든 적에게 공격력 10배."""
        self.player.invincible_ms = 2000
        targets = [e for e in self.dungeon.enemies
                   if e.is_alive() and self.dungeon.tiles[e.y][e.x].visible]
        hits = 0
        for enemy in targets:
            dmg = roll_damage(self._skill_atk, enemy.defense, 10)
            enemy.take_damage(dmg)
            self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (255, 255, 255)))
            self.animator.particles.emit_thunder_hit(enemy.x, enemy.y)
            hits += 1
            if not enemy.is_alive():
                self._on_enemy_killed(enemy)
        px, py = self.player.x, self.player.y
        self.animator.add(WhirlAnim(px, py))
        self.animator.add(SlashAnim(px, py, px, py, (255, 255, 255)))
        self._start_shake(10, 600)
        self.skills.trigger('Ctrl_R')
        self.audio.play('crit')
        msg = t('ult_slash_hit', hits) if hits else t('ult_slash_miss')
        self.messages.append((msg, 'warn'))
        return True

    # ─────────────── 보스 처치 ────────────────────────────────────────
    def _check_boss_cleared(self):
        if (self.dungeon.is_boss_floor and
                self.dungeon.boss and
                not self.dungeon.boss.is_alive() and
                self.dungeon.stairs_pos is None):
            bx, by = self.dungeon.boss.x, self.dungeon.boss.y
            placed = False
            for ddx, ddy in [(0, -1), (0, 1), (-1, 0), (1, 0),
                             (0, -2), (0, 2), (-2, 0), (2, 0)]:
                wx, wy = bx + ddx, by + ddy
                if (self.dungeon.in_bounds(wx, wy) and
                        self.dungeon.tiles[wy][wx].tile_type == TileType.WALL):
                    self.dungeon.tiles[wy][wx] = Tile.door()
                    self.dungeon.stairs_pos = (wx, wy)
                    placed = True
                    break
            if not placed:
                self.dungeon.tiles[by][bx] = Tile.door()
                self.dungeon.stairs_pos = (bx, by)
            self.messages.append((t('boss_clear'), 'good'))
            self.audio.play('stairs')
            self._start_shake(6, 400)
            # 구역(보스) 클리어 보상: 마을 귀환 포탈 자동 개방
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)):
                px_, py_ = self.player.x + ddx, self.player.y + ddy
                if (self.dungeon.is_walkable(px_, py_)
                        and (px_, py_) != self.dungeon.stairs_pos):
                    self._spawn_town_portal(px_, py_)
                    break

    # ─────────────── 버닝 스테이지 ──────────────────────────────────
    def _enter_burning_stage(self):
        self._burning_floor       = self.floor
        self._burning_active      = True
        self._burning_timer_ms    = BURNING_DURATION_MS
        self._burning_spawn_timer = 500            # 0.5초 후 첫 파도
        self._burning_wave        = 0
        self._burning_warned_10s  = False

        dungeon, start = generate_arena()
        self.dungeon = dungeon
        self._theme  = BURNING_THEME

        self.player.x, self.player.y = start
        self.player.hp = self.player.max_hp        # 체력 완전 회복

        self.camera = Camera(ARENA_WIDTH, ARENA_HEIGHT)
        self.camera.center_on(self.player.x, self.player.y)

        self.messages.clear()
        self.messages.append((t('burning_enter'), 'bad'))
        self.audio.play('boss_appear')
        self._start_shake(6, 500)

    def _update_burning(self, dt_ms: int):
        dt_ms = min(dt_ms, 200)   # 한 프레임이 타이머를 200ms 이상 삭감하지 않도록
        self._burning_timer_ms    -= dt_ms
        self._burning_spawn_timer -= dt_ms

        # 10초 경고
        if (not self._burning_warned_10s and
                self._burning_timer_ms <= 10_000):
            self._burning_warned_10s = True
            self.messages.append((t('burning_10sec'), 'bad'))
            self._start_shake(4, 300)

        # 생존 달성
        if self._burning_timer_ms <= 0:
            self._exit_burning_stage(survived=True)
            return

        # 파도 스폰
        live = sum(1 for e in self.dungeon.enemies if e.is_alive())
        if self._burning_spawn_timer <= 0 and live < MAX_LIVE_ENEMIES:
            self._burning_spawn_timer = SPAWN_INTERVAL_MS
            self._burning_wave       += 1
            new_enemies = spawn_wave(
                self.dungeon, self._enemy_data,
                self._burning_floor, self._burning_wave,
            )
            self.dungeon.enemies.extend(new_enemies)
            self.messages.append((t('burning_wave', self._burning_wave), 'warn'))

        # 오래된 dead 적 정리 (성능)
        if len(self.dungeon.enemies) > MAX_LIVE_ENEMIES * 2:
            self.dungeon.enemies = [e for e in self.dungeon.enemies if e.is_alive()]

    def _exit_burning_stage(self, survived: bool):
        self._burning_active = False
        self._fortify_effect = None      # 이펙트 초기화
        self._remove_fortify_buff()

        if survived:
            self.messages.append((t('burning_survived'), 'good'))
            self.audio.play('levelup')
            self._ach_unlock('ACH_BURNING')
            # 다음 보스 층으로 이동
            boss_floor = ((self._burning_floor // 5) + 1) * 5
            self.floor = max(boss_floor, self._burning_floor + 1)
        else:
            self.messages.append((t('burning_failed'), 'info'))
            self.audio.play('death')
            self.floor = self._burning_floor
            self.player.hp = max(1, self.player.max_hp // 4)  # 25% 잔여 HP

        self._start_fade(self._load_floor)

    # ─────────────── 실시간 적 AI ─────────────────────────────────────
    def _spawn_boss_summon(self, key: str, bx: int, by: int):
        if key not in self._enemy_data:
            return
        from entities.enemy import Enemy
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,1),(1,-1),(-1,-1)]:
            nx, ny = bx + dx, by + dy
            if (self.dungeon.is_walkable(nx, ny) and
                    not self.dungeon.get_enemy_at(nx, ny) and
                    (nx, ny) != (self.player.x, self.player.y)):
                d = dict(self._enemy_data[key]); d['key'] = key
                new_e = Enemy(nx, ny, d)
                self.dungeon.enemies.append(new_e)
                self.animator.add(HitFlashAnim(nx, ny, 0, (120, 200, 160)))
                return

    def _update_enemies(self, dt):
        # co-op 클라: 적 AI는 호스트 권위 → 로컬 시뮬 정지(스냅샷으로 갱신)
        if self._coop_is_client():
            return
        for enemy in list(self.dungeon.enemies):
            if not (enemy.is_alive() and self.player.is_alive()):
                continue
            # 보물 고블린: 수명 만료 시 도주 성공 (연출과 함께 소멸)
            if enemy.lifetime_ms > 0:
                enemy.lifetime_ms -= dt
                if enemy.lifetime_ms <= 0:
                    self.animator.particles.emit_death(enemy.x, enemy.y, enemy.color)
                    self.dungeon.enemies.remove(enemy)
                    self.messages.append((t('goblin_escape'), 'bad'))
                    self.audio.play('teleport')
                    continue
                # 황금 반짝임 잔상 — 시야에 들어오면 눈에 확 띄게
                if (dt > 0 and random.random() < dt / 150.0
                        and self.dungeon.tiles[enemy.y][enemy.x].visible):
                    self._emit_goblin_sparkle(enemy)
            prev_hp = self.player.hp
            result  = enemy.update(dt, self.dungeon, self.player, self.messages)
            if self.player.hp < prev_hp:
                dmg = prev_hp - self.player.hp
                self.animator.add(HitFlashAnim(self.player.x, self.player.y, dmg, (255,50,50)))
                self.audio.play('player_hit')
                # 피해 비중에 비례한 흔들림 + 붉은 비네트
                ratio = dmg / max(1, self.player.max_hp)
                self._start_shake(min(8, 2 + int(ratio * 20)), 200)
                self._hurt_flash_ms = 260
                # 원거리 공격 볼트 연출
                dist = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
                if dist > 1:
                    self.animator.add(BoltAnim(enemy.x, enemy.y,
                                               self.player.x, self.player.y,
                                               (100,180,255) if enemy.key=='wizard' else (255,140,0)))
            # 보스 스킬 시각 효과
            if result:
                skill = result.get('skill')
                ex, ey = result.get('ex', enemy.x), result.get('ey', enemy.y)
                if skill == 'whirlwind':
                    self.animator.add(WhirlAnim(ex, ey))
                    self.animator.particles.emit_whirl(ex, ey)
                    self._start_shake(5, 300)
                elif skill == 'charge':
                    self.animator.particles.emit_power_hit(ex, ey)
                    self._start_shake(6, 280)
                elif skill == 'death_nova':
                    self.animator.add(WhirlAnim(ex, ey))
                    self.animator.particles.emit_thunder_hit(ex, ey)
                    self._start_shake(5, 350)
                elif skill == 'summon_undead':
                    self._spawn_boss_summon(result.get('spawn_key','skeleton'), ex, ey)
                elif skill == 'curse':
                    self.animator.add(HitFlashAnim(self.player.x, self.player.y, 0, (160, 50, 220)))
                elif skill == 'slow':
                    self.animator.add(HitFlashAnim(self.player.x, self.player.y, 0, (80, 130, 255)))
                elif skill == 'fear':
                    self.animator.add(HitFlashAnim(self.player.x, self.player.y, 0, (255, 200, 50)))

        if not self.player.is_alive() and self.state == 'playing':
            if self._burning_active:
                self._exit_burning_stage(survived=False)
            else:
                self._records = update_records(self.floor, self._run_kills, self.player.gold)
                delete_save(self._save_slot)
                self.audio.play('death')
                self._ach_unlock('ACH_DIE')
                self.state = 'dead'

        # ── 몬스터 리스폰 ────────────────────────────────────────────
        if (not self._burning_active and
                not self._in_town and
                not self._coop_dungeon and       # co-op: net_id 안정성 위해 리스폰 정지
                not self.dungeon.is_boss_floor and
                self._respawn_max > 0):
            live_normal = sum(1 for e in self.dungeon.enemies
                              if e.is_alive() and not e.is_boss)
            if live_normal < self._respawn_max:
                self._respawn_timer_ms -= dt
                if self._respawn_timer_ms <= 0:
                    self._do_respawn()
                    self._respawn_timer_ms = self._RESPAWN_INTERVAL
            else:
                self._respawn_timer_ms = self._RESPAWN_INTERVAL

    # ─────────────── 렌더링 ───────────────────────────────────────────
    def _render(self):
        self.screen.fill(BLACK)

        if self.state == 'menu':
            self._menu_buttons = self.hud.render_menu(
                self.screen, self._cards,
                self._menu_sel, pygame.mouse.get_pos(),
                page=self._menu_page,
                settings=self._settings,
                settings_sel=self._menu_settings_sel,
                mp_ip=self._mp_ip,
                mp_status=self._mp_status,
                mp_banner=self._mp_mode_banner,
            )
            pygame.display.flip()
            return

        if self.state == 'char_create':
            self.hud.render_char_create(
                self.screen, self._create_class, self._create_name,
                self._create_sel, pygame.mouse.get_pos(),
                appearance=self._create_appearance(),
                locked=self._class_locked(self._create_class))
            pygame.display.flip()
            return

        if self.state == 'credits':
            self.hud.render_credits(self.screen, self._credits_scroll, self._records)
            pygame.display.flip()
            return

        self._render_dungeon()
        if self.state == 'playing':
            self._draw_map_labels()
        if self._collapse_active:
            self._draw_collapse_exit_arrow()
        if self._keys > 0 and not self._in_town:
            self._draw_key_badge()
        self.hud.render(self.screen, self.player, self.messages, self.floor,
                        self.dungeon, self.skills,
                        unlocked_combos=self._unlocked_combos,
                        skill_books=self._skill_books,
                        skill_levels=self._skill_levels,
                        skill_xp=self._skill_xp,
                        is_test_mode=self._is_test_mode,
                        equipped_skills=self._equipped_skills,
                        minimap_npcs=(self._town.visible_npcs()
                                      if self._in_town and self._town else None))

        # 마을·co-op던전 채팅 오버레이 (최근 피드 + 입력줄)
        if self.net is not None and (self._in_town or self._coop_dungeon):
            self._draw_chat_overlay()

        if self.dungeon.is_boss_floor and self.dungeon.boss and self.dungeon.boss.is_alive():
            self.hud.render_boss_bar(self.screen, self.dungeon.boss)

        # 층 전환 페이드 오버레이
        if self._fade_alpha > 0:
            fade_surf = pygame.Surface((GAME_W, GAME_H))
            fade_surf.fill(BLACK)
            fade_surf.set_alpha(self._fade_alpha)
            self.screen.blit(fade_surf, (GAME_X, GAME_Y))

        if self.state == 'shop':
            self.hud.render_shop(self.screen, self.dungeon.shop_items, self.player.gold)
        elif self.state == 'storage':
            self.hud.render_storage(self.screen, self.player, self._storage,
                                    self._item_data, self._storage_pane,
                                    self._storage_cursor,
                                    capacity=self._storage_cap,
                                    upgrade_cost=self._STORAGE_UPGRADES.get(self._storage_cap),
                                    carried_groups=self._inv_group_view())
        elif self.state == 'farm_menu':
            self._render_farm_menu()
        elif self.state == 'altar':
            self._render_altar()
        elif self.state == 'angler':
            self._render_angler()
        elif self.state == 'fishing':
            self._render_fishing()
        elif self.state == 'ranch_menu':
            self._render_ranch_menu()
        elif self.state == 'inn':
            self.hud.render_inn(self.screen, self.player, self._inn_rest_cost())
        elif self.state == 'dialog' and self._dialog:
            self.hud.render_dialog(self.screen, self._dialog)
        elif self.state == 'questlog':
            self.hud.render_questlog(self.screen, self._quests,
                                     self._max_floor_reached)
        elif self.state == 'journal':
            self.hud.render_journal(self.screen, self._records,
                                    max(self.floor, self._records.get('best_floor', 0)))
        elif self.state == 'pet':
            self.hud.render_pet_status(self.screen, self.player, self._pet)
        elif self.state == 'paused':
            self.hud.render_paused(self.screen, self._settings, self._pause_sel,
                                   mouse_pos=pygame.mouse.get_pos())
        elif self.state == 'dead':
            self.hud.render_game_over(self.screen, self.floor, self._records)
        elif self.state == 'inventory':
            self.hud.render_inventory(self.screen, self.player, self._inv_sel,
                                      mouse_pos=pygame.mouse.get_pos(),
                                      drag_idx=self._inv_drag_idx,
                                      drag_pos=self._inv_drag_pos,
                                      view=self._inv_view(),
                                      cat=self._inv_cat,
                                      cat_counts=self._inv_cat_counts())
            if self._inv_confirm_idx is not None and \
                    self._inv_confirm_idx < len(self.player.inventory):
                item_name = self.player.inventory[self._inv_confirm_idx].name
                _, yes_r, no_r = self._inv_confirm_rects()
                self.hud.render_discard_confirm(self.screen, item_name,
                                                yes_r, no_r,
                                                mouse_pos=pygame.mouse.get_pos())
        elif self.state == 'equipment':
            if self._USE_AVATAR:
                from entities.avatar import avatar_surface
                _pspr = avatar_surface(64, getattr(self.player, 'appearance', None),
                                       self.player.char_class, scale=3)
            else:
                _pspr = self._sprites.get('hero_down')
            self.hud.render_equipment(self.screen, self.player, self._equip_sel,
                                      _pspr,
                                      mouse_pos=pygame.mouse.get_pos())

        if self._skillbook_open and self.state == 'playing':
            self.hud.render_skillbook(
                self.screen,
                skill_levels=self._skill_levels,
                unlocked_combos=self._unlocked_combos,
                skill_books=self._skill_books,
                skill_points=self._skill_points,
                cursor=self._skillbook_cursor,
                player_level=self.player.level,
                equipped_skills=self._equipped_skills,
                equip_mode=self._skillbook_equip_mode,
                equip_target_slot=self._skillbook_target_slot,
                equip_skill_id=self._skillbook_equip_skill_id,
                equip_cursor=self._skillbook_equip_cursor,
                skill_enchants=self._skill_enchants,
                arcane_window=self._arcane_window_ms > 0,
            )
        if self._enhance_open and self.state == 'playing':
            self.hud.render_enhance(self.screen, self.player, self._enhance_cursor,
                                    self._enhance_result,
                                    mode=self._enhance_mode,
                                    cost_fn=self._smith_cost)

        # 버닝 스테이지 타이머 오버레이
        if self._burning_active:
            self._render_burning_hud()

        pygame.display.flip()

    def _render_dungeon(self):
        self._game_surf.fill(self._theme['bg'])
        cx, cy = self.camera.x, self.camera.y

        for ty in range(VIEWPORT_TILES_Y + 1):
            for tx in range(VIEWPORT_TILES_X + 1):
                wx, wy = cx+tx, cy+ty
                if not self.dungeon.in_bounds(wx, wy): continue
                tile = self.dungeon.tiles[wy][wx]
                sx, sy = tx*TILE_SIZE, ty*TILE_SIZE
                if tile.visible:    self._draw_tile(tile, sx, sy, True)
                elif tile.explored: self._draw_tile(tile, sx, sy, False)

        for item in self.dungeon.items:
            if self.dungeon.tiles[item.y][item.x].visible:
                iox, ioy, draw_glyph = self.vfx_loot.item_render_state(item)
                if draw_glyph:
                    self._draw_item(item, (item.x-cx)*TILE_SIZE + int(iox),
                                    (item.y-cy)*TILE_SIZE + int(ioy))

        # 마법사 화염 장판 (바닥 위, 적 아래)
        self._draw_dot_zones(cx, cy)

        # 붕괴 경고 (곧 무너질 타일 균열/붉은 점멸)
        if self._collapse_active:
            self._draw_collapse_warn(cx, cy)

        # 보스 스킬 위험 구역 (예고 중 붉게 점멸)
        for enemy in self.dungeon.enemies:
            if not (enemy.is_alive() and enemy._pending_skill):
                continue
            pulse = 70 + int(45 * math.sin(pygame.time.get_ticks() * 0.018))
            ov = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            ov.fill((255, 55, 35, pulse))
            pygame.draw.rect(ov, (255, 90, 60, min(255, pulse + 70)),
                             (0, 0, TILE_SIZE, TILE_SIZE), 2)
            for wx, wy in enemy.telegraph_tiles(self.dungeon):
                if self.dungeon.in_bounds(wx, wy) and self.dungeon.tiles[wy][wx].visible:
                    self._game_surf.blit(ov, ((wx-cx)*TILE_SIZE, (wy-cy)*TILE_SIZE))

        for enemy in self.dungeon.enemies:
            if enemy.is_alive() and self.dungeon.tiles[enemy.y][enemy.x].visible:
                self._draw_enemy(enemy,
                                 (enemy.x-cx)*TILE_SIZE + int(enemy.anim_ox),
                                 (enemy.y-cy)*TILE_SIZE + int(enemy.anim_oy))

        # ── 마을 NPC / 귀환 포탈 ────────────────────────────────────
        if self._in_town and self._town:
            self._town.visible_givers = self._town_visible_givers()
            self._town.draw(self._game_surf, cx, cy,
                            self.player.x, self.player.y, self.hud.font_sm)
            self._draw_quest_markers(cx, cy)
        else:
            portal = getattr(self.dungeon, 'town_portal_pos', None)
            if portal and self.dungeon.tiles[portal[1]][portal[0]].visible:
                from core.town import TownScene
                TownScene.draw_portal(self._game_surf, portal, cx, cy)

        ox, oy = self.animator.player_offset
        ox += int(self._move_anim_offset[0])
        oy += int(self._move_anim_offset[1])
        px = (self.player.x - cx) * TILE_SIZE + ox
        py = (self.player.y - cy) * TILE_SIZE + oy

        # 강화술 아우라 링 (플레이어 아래)
        if self._fortify_effect and self._fortify_effect.alive:
            self._fortify_effect.draw_below(self._game_surf, px, py)

        self._draw_player_sprite(px, py)

        # 멀티플레이: 원격 플레이어(다른 접속자) — 마을·co-op던전
        if self.net is not None and (self._in_town or self._coop_dungeon):
            for rp in self.net.remote_players.values():
                rp.draw(self._game_surf, cx, cy)
            self._draw_chat_bubbles(cx, cy, px, py)

        # 펫 (플레이어 근처, 카메라 오프셋 적용)
        if self._pet and not self._in_town:
            self._pet.draw(self._game_surf, cx, cy)

        # 마법사 소환수
        for s in self._summons:
            s.draw(self._game_surf, cx, cy)

        # 투척 폭탄 (도화선 깜빡임 — 임박할수록 빠르게)
        for b in self._bombs:
            self._draw_bomb(b, cx, cy)

        # 도끼맨: 바닥에 박힌 도끼(회수 대기)
        if self._thrown_axe is not None:
            ax, ay = self._thrown_axe['x'], self._thrown_axe['y']
            if self.dungeon.in_bounds(ax, ay) and self.dungeon.tiles[ay][ax].visible:
                self._draw_thrown_axe(ax - cx, ay - cy)

        # 라그나로크: 플레이어 주위 화염 오라
        if self._ragnarok_ms > 0:
            self._draw_ragnarok_aura(cx, cy)

        # 강화술 상승 파티클 (플레이어 위)
        if self._fortify_effect and self._fortify_effect.alive:
            self._fortify_effect.draw_above(self._game_surf, px, py)

        self.animator.draw(self._game_surf, cx, cy)
        self.vfx_loot.draw(self._game_surf, cx, cy)   # 코인·등급 오브·이름 팝업

        # 실시간 퀘스트 트래커 (좌상단)
        self._draw_quest_tracker()

        # 퀘스트 클리어 하이라이트 오버레이 (전면 골드 링 + 이름)
        if self._quest_clear_ms > 0:
            self._draw_quest_clear_overlay()

        # 처치 연쇄 카운터 (상단 중앙) — 콤보가 쌓일수록 커지고 티어 색으로 발광
        if self._combo_count >= 2 and self._combo_ms > 0:
            if self._combo_font is None:
                from core.animator import _load_font
                self._combo_font = _load_font(24)
            alpha = min(255, int(255 * self._combo_ms / 1500))
            tier  = self._combo_tier(self._combo_count)
            color = tier[2] if tier else (255, 225, 80)
            txt = self._combo_font.render(f"COMBO x{self._combo_count}", True, color)
            # 콤보 수 비례 확대 + 상시 펄스 + 처치 직후 펀치 팝
            grow  = 1.0 + min(self._combo_count, 20) * 0.02
            pulse = 1.0 + (0.05 * math.sin(pygame.time.get_ticks() * 0.02)
                           if tier else 0.0)
            pop   = 1.3 if self._combo_ms > 3800 else 1.0
            scale = grow * pulse * pop
            w, h = txt.get_size()
            txt = pygame.transform.scale(txt, (int(w * scale), int(h * scale)))
            # 티어 진입 시 뒤에 글로우 잔광 (확대 저알파 사본)
            # NOTE: set_alpha()는 일부 SDL 블리터에서 per-pixel alpha를 무시해
            #       투명 영역(폰트색·alpha 0)이 통째로 채워진 '보라 직사각형'으로
            #       렌더된다. BLEND_RGBA_MULT로 per-pixel alpha에 곱해 확실히 처리.
            if tier:
                glow = pygame.transform.scale(txt, (txt.get_width() + 12,
                                                    txt.get_height() + 12))
                ga = max(0, min(255, alpha // 4))
                glow.fill((255, 255, 255, ga), special_flags=pygame.BLEND_RGBA_MULT)
                self._game_surf.blit(glow, ((GAME_W - glow.get_width()) // 2, 28))
            txt.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            self._game_surf.blit(txt, ((GAME_W - txt.get_width()) // 2, 34))

        # 피격 붉은 비네트 (가장자리 테두리, 잔여 시간에 따라 옅어짐)
        if self._hurt_flash_ms > 0:
            a = max(0, int(110 * self._hurt_flash_ms / 260))
            vig = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
            pygame.draw.rect(vig, (255, 30, 30, a),      (0, 0, GAME_W, GAME_H), 14)
            pygame.draw.rect(vig, (255, 30, 30, a // 2), (14, 14, GAME_W - 28, GAME_H - 28), 12)
            self._game_surf.blit(vig, (0, 0))

        # 저체력 심장박동 비네트 (HP 25% 이하, 위기감 펄스)
        if (self.player and self.player.is_alive()
                and self.player.hp <= self.player.max_hp * 0.25):
            beat = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.007)
            a = int(35 + 55 * beat)
            vig = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
            pygame.draw.rect(vig, (200, 15, 15, a),      (0, 0, GAME_W, GAME_H), 18)
            pygame.draw.rect(vig, (200, 15, 15, a // 2), (18, 18, GAME_W - 36, GAME_H - 36), 14)
            self._game_surf.blit(vig, (0, 0))

        # 피니셔 임팩트 프레임 (한순간 흰 섬광)
        if self._white_flash_ms > 0:
            a = int(120 * self._white_flash_ms / 55)
            flash = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
            flash.fill((255, 255, 255, min(255, a)))
            self._game_surf.blit(flash, (0, 0))

        # 레벨업 골든 플래시 (짧은 전면 섬광)
        if self._gold_flash_ms > 0:
            a = int(80 * self._gold_flash_ms / 420)
            flash = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
            flash.fill((255, 218, 100, a))
            self._game_surf.blit(flash, (0, 0))

        # 사인파 왜곡(수중/마법 층) → 화면 흔들림(+카메라 지진) + 펀치 줌
        src = self._apply_distortion(self._game_surf)
        sox, soy = self._shake_offset
        if self.camera:                          # 동적 지진 오프셋 합산
            sox += int(self.camera.offset_x)
            soy += int(self.camera.offset_y)
        if self._punch_zoom_ms > 0:
            k  = self._punch_zoom_ms / self._punch_zoom_max
            z  = 1.0 + self._punch_zoom_amt * k
            zw, zh = int(GAME_W * z), int(GAME_H * z)
            zoomed = pygame.transform.scale(src, (zw, zh))
            clip = self.screen.get_clip()
            self.screen.set_clip(pygame.Rect(GAME_X, GAME_Y, GAME_W, GAME_H))
            self.screen.blit(zoomed, (GAME_X - (zw - GAME_W) // 2 + sox,
                                      GAME_Y - (zh - GAME_H) // 2 + soy))
            self.screen.set_clip(clip)
        else:
            self.screen.blit(src, (GAME_X + sox, GAME_Y + soy))

    def _draw_tile(self, tile, x, y, lit):
        ts = TILE_SIZE; s = self._game_surf; tt = tile.tile_type
        th = self._theme
        if tt == TileType.WALL:
            col = th['wall_lit'] if lit else th['wall_dim']
            pygame.draw.rect(s, col, (x,y,ts,ts))
            if lit:
                pygame.draw.line(s,th['wall_top'],(x,y),(x+ts-1,y))
                pygame.draw.line(s,th['wall_top'],(x,y),(x,y+ts-1))
                pygame.draw.line(s,th['wall_bot'],(x,y+ts-1),(x+ts-1,y+ts-1))
        elif tt == TileType.CRACKED_WALL:
            self._draw_cracked_wall(s, x, y, lit, th)
        elif tt == TileType.COLLAPSED:
            # 무너진 구덩이 — 검은 심연 + 톱니 가장자리
            pygame.draw.rect(s, (6, 5, 9), (x, y, ts, ts))
            edge = (40, 34, 30) if lit else (22, 19, 17)
            pygame.draw.lines(s, edge, True,
                              [(x + 2, y + 5), (x + 7, y + 2), (x + ts - 6, y + 4),
                               (x + ts - 2, y + 9), (x + ts - 4, y + ts - 4),
                               (x + 6, y + ts - 2), (x + 3, y + ts - 7)], 2)
        elif tt == TileType.ALTAR:
            self._draw_altar(s, x, y, lit, th)
        elif tt == TileType.WATER:
            self._draw_water(s, x, y, lit, th)
        elif tt == TileType.LOCKED_DOOR:
            self._draw_locked_door(s, x, y, lit, th)
        elif tt == TileType.DOOR:
            self._draw_door(s, x, y, lit, th)
        elif tt == TileType.BURNING_DOOR:
            self._draw_burning_door(s, x, y, lit, th)
        elif tt == TileType.SHOP:
            col = (25,55,30) if lit else (12,28,15)
            pygame.draw.rect(s, col, (x,y,ts,ts))
            if lit:
                pygame.draw.rect(s, SHOP_COLOR, (x,y,ts,ts), 1)
                ccx, ccy = x+ts//2, y+ts//2
                pygame.draw.circle(s, SHOP_COLOR, (ccx, ccy), 6, 2)
                _r(s, SHOP_COLOR, ccx, ccy-1, 5, 2)
        elif tt in (TileType.CONVEYOR_LEFT, TileType.CONVEYOR_RIGHT):
            self._draw_conveyor(s, x, y, lit, tt)
        elif tt in (TileType.SPIKE_TRAP, TileType.WEB_TRAP,
                    TileType.CURSE_TRAP, TileType.BUTTON):
            self._draw_trap(s, x, y, lit, tt, tile)
        elif tt == TileType.SHIFT_WALL:
            self._draw_shift_wall(s, x, y, lit, tile)
        else:
            col = th['floor_lit'] if lit else th['floor_dim']
            pygame.draw.rect(s, col, (x,y,ts,ts))
            if lit: pygame.draw.rect(s, th['floor_edge'], (x,y,ts,ts), 1)
            if tt == TileType.STAIRS_DOWN:
                sc = th['stairs_lit'] if lit else th['stairs_dim']
                ccx, ccy = x+ts//2, y+ts//2
                pygame.draw.polygon(s, sc, [(ccx,ccy+7),(ccx-6,ccy-3),(ccx+6,ccy-3)])
                pygame.draw.line(s, sc, (ccx-4,ccy-3),(ccx+4,ccy-3), 2)

    def _draw_conveyor(self, s, x, y, lit, tt):
        """흐르는 바닥 — 방향 화살표(쉐브론)가 흘러가는 애니메이션."""
        ts = TILE_SIZE
        d = CONVEYOR_DIR[tt]
        base = (58, 64, 82) if lit else (32, 36, 48)
        pygame.draw.rect(s, base, (x, y, ts, ts))
        if lit:
            pygame.draw.rect(s, (86, 94, 116), (x, y, ts, ts), 1)
        arr = (150, 165, 205) if lit else (66, 74, 96)
        period = 12
        off = int(pygame.time.get_ticks() * 0.04) % period
        cy = y + ts // 2
        for i in range(-1, ts // period + 2):
            ax = x + i * period + (off if d > 0 else period - off)
            if d > 0:
                pygame.draw.lines(s, arr, False, [(ax, cy-5), (ax+5, cy), (ax, cy+5)], 2)
            else:
                pygame.draw.lines(s, arr, False, [(ax+5, cy-5), (ax, cy), (ax+5, cy+5)], 2)

    def _draw_dot_zones(self, cx, cy):
        """화염 장판 — 반경 타일에 맥동하는 반투명 원소 바닥."""
        ts = TILE_SIZE
        tnow = pygame.time.get_ticks()
        for z in self._dot_zones:
            r = z['r']; col = z['col']
            fade = min(1.0, z['ms'] / 500.0)          # 소멸 직전 페이드아웃
            pulse = 70 + int(45 * math.sin(tnow * 0.012 + z['x'] + z['y']))
            for oy in range(-r, r + 1):
                for ox in range(-r, r + 1):
                    wx, wy = z['x'] + ox, z['y'] + oy
                    if not self.dungeon.in_bounds(wx, wy):
                        continue
                    if not self.dungeon.tiles[wy][wx].visible:
                        continue
                    sx, sy = (wx - cx) * ts, (wy - cy) * ts
                    a = int(pulse * fade)
                    ov = pygame.Surface((ts, ts), pygame.SRCALPHA)
                    ov.fill((*col, a))
                    # 불꽃 코어 몇 점
                    for _ in range(2):
                        fx = sx + random.randint(4, ts - 4)
                        fy = sy + random.randint(4, ts - 4)
                        pygame.draw.circle(ov, (*[min(255, c + 60) for c in col],
                                                min(255, a + 90)),
                                           (fx - sx, fy - sy), 2)
                    self._game_surf.blit(ov, (sx, sy))

    def _draw_cracked_wall(self, s, x, y, lit, th):
        """균열 벽 — 벽 위에 노란 금(균열) 표시로 '부술 수 있음'을 암시."""
        ts = TILE_SIZE
        col = th['wall_lit'] if lit else th['wall_dim']
        pygame.draw.rect(s, col, (x, y, ts, ts))
        if lit:
            pygame.draw.line(s, th['wall_top'], (x, y), (x + ts - 1, y))
            pygame.draw.line(s, th['wall_top'], (x, y), (x, y + ts - 1))
            pygame.draw.line(s, th['wall_bot'], (x, y + ts - 1), (x + ts - 1, y + ts - 1))
        # 균열 (지그재그 금) — 밝을 때 또렷, 어두울 땐 은은
        crack = (210, 180, 90) if lit else (110, 96, 60)
        cx0 = x + ts // 2
        pts = [(cx0 - 5, y + 3), (cx0 + 3, y + 10), (cx0 - 3, y + 17),
               (cx0 + 4, y + 24), (cx0 - 2, y + ts - 3)]
        pygame.draw.lines(s, crack, False, pts, 2)
        pygame.draw.line(s, crack, (cx0 + 3, y + 10), (x + ts - 4, y + 8), 1)
        pygame.draw.line(s, crack, (cx0 - 3, y + 17), (x + 4, y + 20), 1)

    def _draw_altar(self, s, x, y, lit, th):
        """붕괴 제단 — 바닥 위 맥동하는 보물 제단(밟으면 붕괴)."""
        ts = TILE_SIZE
        # 바닥 베이스
        base = th['floor_lit'] if lit else th['floor_dim']
        pygame.draw.rect(s, base, (x, y, ts, ts))
        cx, cy = x + ts // 2, y + ts // 2
        if not lit:
            # 미탐색/어두움 — 제단 실루엣만
            pygame.draw.rect(s, (60, 50, 40), (cx - 6, cy - 4, 12, 10))
            return
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 260.0)
        # 바닥 광휘 (BLEND_ADD)
        gr = int(10 + 8 * pulse)
        glow = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 180, 70, int(70 + 60 * pulse)), (gr, gr), gr)
        s.blit(glow, (cx - gr, cy - gr), special_flags=pygame.BLEND_ADD)
        # 제단 받침
        pygame.draw.rect(s, (70, 58, 44), (cx - 7, cy + 1, 14, 7))
        pygame.draw.rect(s, (110, 92, 66), (cx - 7, cy + 1, 14, 2))
        # 보물(맥동하는 보석)
        gem = (255, int(180 + 60 * pulse), 60)
        pygame.draw.polygon(s, gem, [(cx, cy - 8), (cx + 5, cy - 2),
                                     (cx, cy + 3), (cx - 5, cy - 2)])
        pygame.draw.polygon(s, (255, 245, 200), [(cx, cy - 8), (cx + 2, cy - 4),
                                                  (cx - 2, cy - 4)])

    def _draw_map_labels(self):
        """상호작용 오브젝트/아이템에 작은 이름표(현지화). 적은 제외.

        · 랜덤 상자(제단)·잠긴 금고: 보이면 항상 표시(중요 랜드마크)
        · 금고 열쇠: 항상 표시(찾아야 함)
        · 그 외 아이템: 플레이어 근접(≤4칸) 시만 표시(화면 정리)
        """
        if self._in_town:
            return
        cx, cy = self.camera.x, self.camera.y
        px, py = self.player.x, self.player.y
        font = self.hud.font_sm
        labels = []
        for ty in range(VIEWPORT_TILES_Y + 1):
            for tx in range(VIEWPORT_TILES_X + 1):
                wx, wy = cx + tx, cy + ty
                if not self.dungeon.in_bounds(wx, wy):
                    continue
                tl = self.dungeon.tiles[wy][wx]
                if not tl.visible:
                    continue
                if tl.tile_type == TileType.ALTAR:
                    labels.append((wx, wy, t('label_box'), (255, 205, 90)))
                elif tl.tile_type == TileType.LOCKED_DOOR:
                    labels.append((wx, wy, t('label_vault'), (245, 210, 90)))
                elif tl.tile_type == TileType.SHOP and self.dungeon.has_shop:
                    labels.append((wx, wy, t('label_shop'), (120, 230, 140)))
        for it in self.dungeon.items:
            if not self.dungeon.tiles[it.y][it.x].visible:
                continue
            if it.effect == 'vault_key':
                labels.append((it.x, it.y, it.name, (245, 215, 80)))
            elif max(abs(it.x - px), abs(it.y - py)) <= 4:
                labels.append((it.x, it.y, it.name, (212, 216, 228)))
        for wx, wy, text, col in labels:
            self._label_at(font, text, wx, wy, col)

    def _label_at(self, font, text, wx, wy, col):
        """월드 타일 위에 작은 이름표를 화면에 그린다(가장자리 클램프)."""
        sx = GAME_X + (wx - self.camera.x) * TILE_SIZE + TILE_SIZE // 2
        sy = GAME_Y + (wy - self.camera.y) * TILE_SIZE
        if not (GAME_X <= sx <= GAME_X + GAME_W and GAME_Y <= sy <= GAME_Y + GAME_H):
            return
        lbl = font.render(text, True, col)
        w, h = lbl.get_size()
        lx = max(GAME_X + 1, min(int(sx - w / 2), GAME_X + GAME_W - w - 1))
        ly = max(GAME_Y + 1, int(sy - h - 3))
        bg = pygame.Surface((w + 4, h + 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 165))
        self.screen.blit(bg, (lx - 2, ly - 1))
        self.screen.blit(lbl, (lx, ly))

    def _draw_key_badge(self):
        """열쇠 소지 중 — 게임 화면 좌상단에 금색 열쇠 뱃지."""
        s = self.screen
        bx, by = GAME_X + 8, GAME_Y + 8
        w, h = 60, 22
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((30, 24, 8, 190))
        s.blit(bg, (bx, by))
        pygame.draw.rect(s, (240, 205, 70), (bx, by, w, h), 1)
        # 열쇠 아이콘
        kx, ky = bx + 12, by + h // 2
        pygame.draw.circle(s, (240, 205, 70), (kx, ky), 4, 2)
        pygame.draw.line(s, (240, 205, 70), (kx + 4, ky), (kx + 13, ky), 2)
        pygame.draw.line(s, (240, 205, 70), (kx + 11, ky), (kx + 11, ky + 4), 2)
        lbl = self.hud.font_sm.render('x%d' % self._keys, True, (245, 225, 140))
        s.blit(lbl, (bx + 32, by + 4))

    def _draw_locked_door(self, s, x, y, lit, th):
        """잠긴 금고문 — 철문 + 금색 자물쇠(열쇠 필요 암시)."""
        ts = TILE_SIZE
        body = (78, 66, 40) if lit else (40, 34, 22)
        pygame.draw.rect(s, body, (x, y, ts, ts))
        if lit:
            pygame.draw.rect(s, (120, 100, 60), (x, y, ts, ts), 1)
            # 가로 보강대
            pygame.draw.line(s, (52, 44, 28), (x + 2, y + ts // 3), (x + ts - 3, y + ts // 3), 2)
            pygame.draw.line(s, (52, 44, 28), (x + 2, y + 2 * ts // 3), (x + ts - 3, y + 2 * ts // 3), 2)
        # 자물쇠(금색)
        cx, cy = x + ts // 2, y + ts // 2
        lc = (240, 205, 70) if lit else (150, 128, 55)
        pygame.draw.arc(s, lc, (cx - 4, cy - 7, 8, 8), 3.14, 6.28, 2)   # 고리
        pygame.draw.rect(s, lc, (cx - 5, cy - 2, 10, 8))               # 몸통
        pygame.draw.circle(s, (60, 48, 20), (cx, cy + 1), 1)           # 열쇠구멍

    def _draw_water(self, s, x, y, lit, th):
        """깊은 물 — 테마색 기반 잔물결(통행 불가)."""
        ts = TILE_SIZE
        # 테마 바닥색을 어둡고 푸르게 편향
        fl = th['floor_dim']
        base = (max(0, fl[0] - 6), min(255, fl[1] + 10), min(255, fl[2] + 40))
        if not lit:
            base = (base[0] // 2, base[1] // 2, base[2] // 2)
        pygame.draw.rect(s, base, (x, y, ts, ts))
        if lit:
            hi = (min(255, base[0] + 30), min(255, base[1] + 40), min(255, base[2] + 55))
            ph = pygame.time.get_ticks() / 400.0 + (x * 0.11 + y * 0.07)
            wy = y + ts // 2 + int(2 * math.sin(ph))
            pygame.draw.line(s, hi, (x + 3, wy), (x + ts - 3, wy), 1)
            wy2 = y + ts // 3 + int(2 * math.sin(ph + 1.7))
            pygame.draw.line(s, hi, (x + 5, wy2), (x + ts - 6, wy2), 1)

    def _draw_collapse_exit_arrow(self):
        """붕괴 중 출구 방향 안내 — 게임 화면 가장자리에 계단을 가리키는 화살표."""
        exit_pos = getattr(self.dungeon, 'stairs_pos', None)
        if not exit_pos:
            return
        s = self.screen
        # 뷰포트(게임 영역) 중심 · 출구 화면 좌표
        vx0, vy0, vw, vh = GAME_X, GAME_Y, GAME_W, GAME_H
        ccx, ccy = vx0 + vw // 2, vy0 + vh // 2
        ex = vx0 + (exit_pos[0] - self.camera.x) * TILE_SIZE + TILE_SIZE // 2
        ey = vy0 + (exit_pos[1] - self.camera.y) * TILE_SIZE + TILE_SIZE // 2
        on_screen = (vx0 + 8 <= ex <= vx0 + vw - 8 and vy0 + 8 <= ey <= vy0 + vh - 8)
        col = (255, 235, 90) if (pygame.time.get_ticks() // 250) % 2 == 0 else (255, 150, 40)
        if on_screen:
            # 출구가 화면 안 — 계단 위에 반짝이는 하강 화살표
            pygame.draw.polygon(s, col, [(ex, ey - 14), (ex - 7, ey - 24), (ex + 7, ey - 24)])
            lbl = self.hud.font_sm.render(t('collapse_exit'), True, col)
            s.blit(lbl, (ex - lbl.get_width() // 2, ey - 40))
            return
        # 화면 밖 — 방향 벡터로 가장자리에 화살표 클램프
        dx, dy = ex - ccx, ey - ccy
        import math as _m
        dist = _m.hypot(dx, dy) or 1
        dx, dy = dx / dist, dy / dist
        margin = 26
        # 뷰포트 사각형과의 교점(간단 스케일)
        sx = min((vx0 + vw - margin - ccx) / dx if dx > 0 else 1e9,
                 (vx0 + margin - ccx) / dx if dx < 0 else 1e9)
        sy = min((vy0 + vh - margin - ccy) / dy if dy > 0 else 1e9,
                 (vy0 + margin - ccy) / dy if dy < 0 else 1e9)
        tscale = min(sx, sy)
        ax, ay = int(ccx + dx * tscale), int(ccy + dy * tscale)
        ang = _m.atan2(dy, dx)
        tip = (ax + int(_m.cos(ang) * 14), ay + int(_m.sin(ang) * 14))
        l = (ax + int(_m.cos(ang + 2.4) * 13), ay + int(_m.sin(ang + 2.4) * 13))
        r = (ax + int(_m.cos(ang - 2.4) * 13), ay + int(_m.sin(ang - 2.4) * 13))
        pygame.draw.circle(s, (20, 16, 24), (ax, ay), 17)
        pygame.draw.polygon(s, col, [tip, l, r])
        lbl = self.hud.font_sm.render(t('collapse_exit'), True, col)
        lx = min(max(ax - lbl.get_width() // 2, vx0 + 2), vx0 + vw - lbl.get_width() - 2)
        ly = min(max(ay - 30, vy0 + 2), vy0 + vh - 14)
        s.blit(lbl, (lx, ly))

    def _draw_collapse_warn(self, cx, cy):
        """붕괴 임박 타일 — 붉은 균열 + 흔들림으로 예고."""
        ts = TILE_SIZE
        s = self._game_surf
        t_now = self._collapse_t
        warn = self._COLLAPSE_WARN
        tnow_ticks = pygame.time.get_ticks()
        for (x, y), ct in self._crumble.items():
            left = ct - t_now
            if left <= 0 or left > warn:
                continue
            tile = self.dungeon.tiles[y][x]
            if not tile.visible or tile.blocked:
                continue
            urg = 1.0 - left / warn                    # 0→1 임박도
            sx, sy = (x - cx) * ts, (y - cy) * ts
            jitter = int(urg * 2)
            jx = random.randint(-jitter, jitter) if jitter else 0
            ov = pygame.Surface((ts, ts), pygame.SRCALPHA)
            a = int(40 + 90 * urg)
            if (tnow_ticks // max(80, int(220 * (1 - urg)))) % 2 == 0:
                ov.fill((180, 50, 30, a))
            # 균열 선
            cc = (210, 90, 60)
            pygame.draw.line(ov, cc, (ts // 2, 2), (ts // 2 - 4, ts - 2), 1)
            pygame.draw.line(ov, cc, (4, ts // 2), (ts - 3, ts // 2 + 3), 1)
            s.blit(ov, (sx + jx, sy))

    def _draw_thrown_axe(self, tx, ty):
        """바닥에 박힌 도끼 — 회수 안내(맥동 광휘 + 도끼 글리프)."""
        ts = TILE_SIZE
        s = self._game_surf
        px, py = tx * ts + ts // 2, ty * ts + ts // 2
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 220.0)
        gr = int(9 + 4 * pulse)
        glow = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (240, 170, 80, int(70 + 60 * pulse)), (gr, gr), gr)
        s.blit(glow, (px - gr, py - gr), special_flags=pygame.BLEND_ADD)
        # 자루 + 도끼날
        pygame.draw.line(s, (140, 100, 60), (px - 5, py + 6), (px + 4, py - 6), 2)
        pygame.draw.polygon(s, (210, 215, 225), [(px + 2, py - 8), (px + 8, py - 6),
                                                 (px + 7, py - 1), (px + 1, py - 3)])
        pygame.draw.polygon(s, (245, 248, 252), [(px + 2, py - 8), (px + 5, py - 7),
                                                 (px + 4, py - 4), (px + 1, py - 3)])

    def _draw_bomb(self, b, cx, cy):
        ts = TILE_SIZE
        sx = (b['x'] - cx) * ts + ts // 2
        sy = (b['y'] - cy) * ts + ts // 2
        s = self._game_surf
        # 몸통
        pygame.draw.circle(s, (36, 36, 42), (sx, sy + 2), 8)
        pygame.draw.circle(s, (70, 70, 80), (sx - 2, sy), 3)          # 하이라이트
        # 심지 + 불꽃 (임박할수록 빨리 깜빡)
        pygame.draw.line(s, (150, 120, 70), (sx + 5, sy - 6), (sx + 8, sy - 11), 2)
        blink = max(60, int(b['fuse'] / 3))
        if (pygame.time.get_ticks() // blink) % 2 == 0:
            pygame.draw.circle(s, (255, 210, 90), (sx + 8, sy - 12), 3)
            pygame.draw.circle(s, (255, 120, 40), (sx + 8, sy - 12), 2)
        # 폭발 임박 경고 링
        if b['fuse'] < 260:
            r = b['r'] * ts
            ring = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 80, 40, 70), (r, r), r, 3)
            s.blit(ring, (sx - r, sy - r))

    def _draw_trap(self, s, x, y, lit, tt, tile=None):
        """트랩·압력판 — 바닥 위 위험 표식. 가시는 주기 상태(솟음/경고/숨음) 반영."""
        ts = TILE_SIZE; th = self._theme
        col = th['floor_lit'] if lit else th['floor_dim']
        pygame.draw.rect(s, col, (x, y, ts, ts))
        if lit:
            pygame.draw.rect(s, th['floor_edge'], (x, y, ts, ts), 1)
        cx, cy = x + ts // 2, y + ts // 2
        dim = 0.5 if not lit else 1.0
        pulse = 0.6 + 0.4 * abs(math.sin(pygame.time.get_ticks() * 0.004))
        def C(c): return tuple(min(255, int(v * dim * (pulse if lit else 1))) for v in c)
        if tt == TileType.SPIKE_TRAP:
            # 바닥 판(구멍) — 항상
            pygame.draw.rect(s, (int(60*dim), int(58*dim), int(70*dim)),
                             (x + 3, y + 3, ts - 6, ts - 6))
            hot  = getattr(tile, 'hot', False)
            warn = getattr(tile, 'warn', False)
            if hot:                                   # 솟음 — 위험(밝은 강철 가시)
                for sx in (-6, 0, 6):
                    pygame.draw.polygon(s, C((225, 120, 110)),
                        [(cx + sx - 4, cy + 7), (cx + sx, cy - 8), (cx + sx + 4, cy + 7)])
                    pygame.draw.polygon(s, C((255, 200, 190)),
                        [(cx + sx - 1, cy + 5), (cx + sx, cy - 7), (cx + sx + 1, cy + 5)])
            elif warn and (pygame.time.get_ticks() // 110) % 2 == 0:
                for sx in (-6, 0, 6):                 # 솟기 직전 — 붉은 예고선
                    pygame.draw.line(s, (210, 90, 70), (cx + sx, cy + 4), (cx + sx, cy - 2), 2)
            else:                                     # 숨음 — 안전(작은 홈)
                for sx in (-6, 0, 6):
                    pygame.draw.circle(s, (int(90*dim), int(84*dim), int(96*dim)),
                                       (cx + sx, cy + 3), 2)
        elif tt == TileType.WEB_TRAP:
            wc = C((200, 220, 235))
            for a in range(0, 360, 45):
                r = math.radians(a)
                pygame.draw.line(s, wc, (cx, cy),
                                 (cx + int(math.cos(r) * 8), cy + int(math.sin(r) * 8)), 1)
            pygame.draw.circle(s, wc, (cx, cy), 5, 1)
            pygame.draw.circle(s, wc, (cx, cy), 8, 1)
        elif tt == TileType.CURSE_TRAP:
            mc = C((165, 95, 220))
            pygame.draw.circle(s, mc, (cx, cy), 8, 2)
            pygame.draw.circle(s, C((120, 60, 180)), (cx, cy), 4)
            pygame.draw.line(s, mc, (cx - 4, cy - 4), (cx + 4, cy + 4), 1)
            pygame.draw.line(s, mc, (cx + 4, cy - 4), (cx - 4, cy + 4), 1)
        elif tt == TileType.BUTTON:
            gc = C((255, 205, 90))
            pygame.draw.circle(s, C((90, 70, 30)), (cx, cy), 9)
            pygame.draw.circle(s, gc, (cx, cy), 9, 2)
            pygame.draw.circle(s, gc, (cx, cy), 4)

    def _draw_shift_wall(self, s, x, y, lit, tile):
        """움직이는 벽 — 닫히면 금속 기둥, 열리면 바닥 위 격자. 경고 시 깜빡."""
        ts = TILE_SIZE; th = self._theme
        if tile.blocked:
            col = th['wall_lit'] if lit else th['wall_dim']
            pygame.draw.rect(s, col, (x, y, ts, ts))
            pygame.draw.rect(s, th['wall_top'], (x, y, ts, ts), 2)
            pygame.draw.line(s, th['wall_top'], (x + 4, y + 4), (x + ts - 5, y + 4))
            pygame.draw.line(s, th['wall_bot'], (x + 4, y + ts - 5), (x + ts - 5, y + ts - 5))
        else:
            col = th['floor_lit'] if lit else th['floor_dim']
            pygame.draw.rect(s, col, (x, y, ts, ts))
            grate = (90, 100, 120) if lit else (48, 54, 68)
            # 경고 중이면 붉게 깜빡 (곧 솟아오름)
            if getattr(tile, 'warn', False) and (pygame.time.get_ticks() // 120) % 2 == 0:
                grate = (230, 110, 80)
            for gx in range(x + 3, x + ts - 2, 6):
                pygame.draw.line(s, grate, (gx, y + 3), (gx, y + ts - 3), 1)

    def _draw_door(self, s, x, y, lit, th):
        ts = TILE_SIZE
        # 벽 배경
        wall_col = th['wall_lit'] if lit else th['wall_dim']
        pygame.draw.rect(s, wall_col, (x, y, ts, ts))
        if not lit:
            # 어두운 상태에서도 희미한 빛 힌트
            pygame.draw.rect(s, (30, 20, 50), (x + 7, y + 4, 18, 26))
            return

        T = pygame.time.get_ticks() * 0.001
        cx, cy = x + ts // 2, y + ts // 2

        # 아치 내부 배경 (깊은 어둠)
        pygame.draw.rect(s, (10, 5, 20), (x + 7, y + 6, 18, 26))

        # 내부 글로우 레이어 (안쪽에서 빛이 새어나옴)
        pulse = 1.0 + math.sin(T * 2.2) * 0.18
        glow_colors = [
            (60, 20, 100),
            (90, 40, 150),
            (120, 60, 200),
            (160, 90, 255),
        ]
        for i, gc in enumerate(glow_colors):
            r = round((5 - i) * pulse * 1.5)
            pygame.draw.circle(s, gc, (cx, cy + 4), max(1, r))

        # 아치 프레임 (돌 기둥)
        stone = th.get('wall_lit', (80, 70, 90))
        stone_h = tuple(min(255, c + 30) for c in stone)
        stone_d = tuple(max(0, c - 20) for c in stone)
        # 왼쪽 기둥
        pygame.draw.rect(s, stone_d, (x + 5, y + 8, 4, 22))
        pygame.draw.rect(s, stone_h, (x + 5, y + 8, 2, 22))
        # 오른쪽 기둥
        pygame.draw.rect(s, stone_d, (x + 23, y + 8, 4, 22))
        pygame.draw.rect(s, stone_h, (x + 23, y + 8, 2, 22))
        # 상단 아치 (반원 모양 파티클)
        for i in range(7):
            a = math.pi * i / 6
            ax = round(cx + math.cos(a) * 9)
            ay = round(y + 8 - math.sin(a) * 5)
            pygame.draw.circle(s, stone_d, (ax, ay), 3)
            pygame.draw.circle(s, stone_h, (ax, ay), 1)

        # 내부 파티클: 아래로 빨려들어가는 빛 조각들
        for i in range(6):
            phase = (T * 1.2 + i * 0.28) % 1.0
            px = cx - 5 + i * 2 + math.sin(T * 2 + i * 1.1) * 2.5
            py = y + 6 + phase * 22
            r = max(1, round(2 * (1 - phase * 0.6)))
            col_p = (
                min(255, round(160 + 90 * math.sin(T + i))),
                min(255, round(60 + 40 * math.sin(T * 0.7 + i))),
                255,
            )
            pygame.draw.circle(s, col_p, (round(px), round(py)), r)

        # 아치 상단 윤곽 강조
        pygame.draw.arc(s, stone_h,
                        (x + 6, y + 3, 20, 14), 0, math.pi, 2)

        # 바닥 문지방
        pygame.draw.rect(s, stone_d, (x + 5, y + 28, 22, 3))
        pygame.draw.rect(s, stone_h, (x + 5, y + 28, 22, 1))

        # 벽 상단 하이라이트 복원
        pygame.draw.line(s, th['wall_top'], (x, y), (x + ts - 1, y))

    def _draw_burning_door(self, s, x, y, lit, th):
        ts = TILE_SIZE
        wall_col = th['wall_lit'] if lit else th['wall_dim']
        pygame.draw.rect(s, wall_col, (x, y, ts, ts))
        if not lit:
            pygame.draw.rect(s, (50, 15, 5), (x + 7, y + 4, 18, 26))
            return

        T  = pygame.time.get_ticks() * 0.001
        cx, cy = x + ts // 2, y + ts // 2

        # 아치 내부 — 검은 배경
        pygame.draw.rect(s, (8, 3, 0), (x + 7, y + 6, 18, 26))

        # 화염 코어 글로우 (오렌지-적색)
        for i, (fc, fr) in enumerate([
            ((200, 60, 10), 6),
            ((255, 110, 20), 4),
            ((255, 200, 60), 2),
        ]):
            pulse = 1.0 + math.sin(T * 4.0 + i * 1.1) * 0.2
            pygame.draw.circle(s, fc, (cx, cy + 4), round(fr * pulse))

        # 위로 타오르는 불꽃 파티클
        for i in range(7):
            phase = (T * 1.8 + i * 0.21) % 1.0
            px_ = cx - 5 + i * 2 + math.sin(T * 3 + i * 0.9) * 2
            py_ = y + 30 - phase * 26
            heat = 1.0 - phase
            fc = (
                255,
                round(180 * heat + 30),
                round(20 * heat),
            )
            r = max(1, round(2.5 * heat))
            pygame.draw.circle(s, fc, (round(px_), round(py_)), r)

        # 불씨 스파크 (작은 점들)
        for i in range(5):
            phase = (T * 2.5 + i * 0.4) % 1.0
            if phase < 0.3:
                sp_x = cx - 6 + i * 3 + math.sin(T * 5 + i) * 3
                sp_y = y + 28 - phase * 80
                a_sp = 1 - phase / 0.3
                pygame.draw.circle(s, (round(255 * a_sp), round(220 * a_sp), 0),
                                   (round(sp_x), round(sp_y)), 1)

        # 돌 아치 프레임 (붉은 열기에 물든 석재)
        stone_h = (150, 55, 20)
        stone_d = (70,  20, 8)
        pygame.draw.rect(s, stone_d, (x + 5, y + 8, 4, 22))
        pygame.draw.rect(s, stone_h, (x + 5, y + 8, 2, 22))
        pygame.draw.rect(s, stone_d, (x + 23, y + 8, 4, 22))
        pygame.draw.rect(s, stone_h, (x + 23, y + 8, 2, 22))
        for i in range(7):
            a = math.pi * i / 6
            ax = round(cx + math.cos(a) * 9)
            ay = round(y + 8 - math.sin(a) * 5)
            pygame.draw.circle(s, stone_d, (ax, ay), 3)
            pygame.draw.circle(s, stone_h, (ax, ay), 1)
        pygame.draw.arc(s, stone_h, (x + 6, y + 3, 20, 14), 0, math.pi, 2)
        pygame.draw.rect(s, stone_d, (x + 5, y + 28, 22, 3))
        pygame.draw.rect(s, stone_h, (x + 5, y + 28, 22, 1))
        pygame.draw.line(s, th['wall_top'], (x, y), (x + ts - 1, y))

    def _render_burning_hud(self):
        """버닝 스테이지 타이머 + 파도 오버레이."""
        sec_left  = max(0, self._burning_timer_ms) // 1000
        ms_frac   = (max(0, self._burning_timer_ms) % 1000) // 10
        T         = pygame.time.get_ticks() * 0.001
        live      = sum(1 for e in self.dungeon.enemies if e.is_alive())

        # 상단 타이머 패널 (반투명)
        panel_w, panel_h = 240, 56
        panel_x = GAME_X + (GAME_W - panel_w) // 2
        panel_y = GAME_Y + 8
        panel   = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 170))
        pygame.draw.rect(panel, (200, 60, 10, 200), (0, 0, panel_w, panel_h), 2)
        self.screen.blit(panel, (panel_x, panel_y))

        # 불꽃 깜빡임 색상
        flicker = abs(math.sin(T * 6))
        timer_col = (
            255,
            round(180 + 75 * flicker) if sec_left > 10 else round(60 + 60 * flicker),
            round(30 * flicker)        if sec_left > 10 else 0,
        )

        # 타이머 텍스트
        timer_str = f'{sec_left:02d}.{ms_frac:02d}'
        ts = self._font_burning_big.render(f'* {timer_str}', True, timer_col)
        self.screen.blit(ts, (panel_x + panel_w // 2 - ts.get_width() // 2,
                               panel_y + 6))

        # 파도 / 생존 수
        info_str = f'Wave {self._burning_wave}   Enemies {live}'
        info_s = self._font_burning_small.render(info_str, True, (220, 160, 80))
        self.screen.blit(info_s, (panel_x + panel_w // 2 - info_s.get_width() // 2,
                                   panel_y + 36))

        # 화면 가장자리 화염 테두리 (마지막 10초) — 재사용 Surface로 매 프레임 할당 방지
        if sec_left <= 10:
            edge_a = min(255, round(80 + 80 * abs(math.sin(T * 4))))
            self._edge_surf.fill((0, 0, 0, 0))
            for thickness, alpha in [(8, edge_a), (4, min(255, edge_a + 60))]:
                pygame.draw.rect(self._edge_surf, (255, 80, 20, alpha),
                                 (0, 0, GAME_W, GAME_H), thickness)
            self.screen.blit(self._edge_surf, (GAME_X, GAME_Y))

    # 인게임 캐릭터를 절차적 마인크래프트 아바타로 렌더 (False면 기존 PNG 사용)
    _USE_AVATAR = True

    def _draw_player_sprite(self, x, y):
        facing = self._facing
        phase  = self._atk_phase

        # Squeeze & Stretch 스케일 (강화술 시전 순간)
        scale = 1.0
        if self._fortify_effect and self._fortify_effect.alive:
            scale = self._fortify_effect.squeeze_scale

        if self._USE_AVATAR:
            self._draw_avatar_player(x, y, facing, phase, scale)
            return

        spr = self._pick_hero_png(facing, phase)
        if scale != 1.0:
            tmp = pygame.Surface((TILE_SIZE, TILE_SIZE))
            tmp.fill(_CKEY); tmp.set_colorkey(_CKEY)
            if spr:
                tmp.blit(spr, (0, 0))
            else:
                draw_player(tmp, 0, 0, facing, self._walk_frame)
            w = round(TILE_SIZE * scale)
            h = round(TILE_SIZE * scale)
            scaled = pygame.transform.scale(tmp, (w, h))
            scaled.set_colorkey(_CKEY)
            off = (TILE_SIZE - w) // 2
            self._game_surf.blit(scaled, (x + off, y + off))
        elif spr:
            self._game_surf.blit(spr, (x, y))
        else:
            draw_player(self._game_surf, x, y, facing, self._walk_frame)

        draw_player_layered(
            self._game_surf, x, y,
            facing, self._walk_frame, phase,
            self.player.equipment,
            atk_variant=self._atk_variant,
        )
        # 궁수: 베이스 스프라이트 위에 활 오버레이 (idle/당김/발사 프레임)
        if self.player.char_class == 'archer':
            from entities.player_renderer import draw_archer_bow
            draw_archer_bow(self._game_surf, x, y, facing, phase)
        elif self.player.char_class == 'mage':
            from entities.player_renderer import draw_mage_staff
            draw_mage_staff(self._game_surf, x, y, facing, phase,
                            pygame.time.get_ticks())

    def _draw_avatar_player(self, x, y, facing, phase, scale):
        """절차적 아바타 + (궁수) 활 오버레이. 강화술 스퀴즈 스케일 지원."""
        from entities.avatar import draw_avatar_tile
        from entities.player_renderer import draw_archer_bow, draw_mage_staff
        ap  = getattr(self.player, 'appearance', None)
        cls = self.player.char_class
        tk = pygame.time.get_ticks()

        def _weapon(dst, ox, oy):
            if cls == 'archer':
                draw_archer_bow(dst, ox, oy, facing, phase)
            elif cls == 'mage':
                draw_mage_staff(dst, ox, oy, facing, phase, tk)

        if scale != 1.0:
            tmp = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            draw_avatar_tile(tmp, 0, 0, facing, self._walk_frame, phase, ap, cls)
            _weapon(tmp, 0, 0)
            w = h = round(TILE_SIZE * scale)
            scaled = pygame.transform.scale(tmp, (w, h))
            off = (TILE_SIZE - w) // 2
            self._game_surf.blit(scaled, (x + off, y + off))
        else:
            draw_avatar_tile(self._game_surf, x, y, facing, self._walk_frame,
                             phase, ap, cls)
            _weapon(self._game_surf, x, y)
        # 칭호 뱃지 이펙트 (마을에서 [심연의 지배자] 반짝임)
        if getattr(self, '_title_badge', False) and self._in_town:
            self._draw_title_badge(x, y)

    def _draw_title_badge(self, x, y):
        """플레이어 머리 위 반짝이는 도트 왕관 뱃지."""
        s = self._game_surf
        tk = pygame.time.get_ticks()
        bob = int(2 * math.sin(tk * 0.005))
        cx, cy = x + TILE_SIZE // 2, y - 6 + bob
        glow = (255, 235, 120) if (tk // 250) % 2 == 0 else (235, 185, 60)
        # 작은 왕관 (도트)
        for dx in (-4, 0, 4):
            _r(s, glow, cx + dx - 1, cy - 3, 2, 2)
        _r(s, glow, cx - 5, cy, 11, 3)
        _r(s, (150, 108, 18), cx - 5, cy + 3, 11, 1)
        # 반짝임 스파클
        if (tk // 180) % 3 == 0:
            _r(s, (255, 255, 255), cx + 6, cy - 5, 1, 1)
            _r(s, (255, 255, 255), cx - 7, cy - 1, 1, 1)

    def _pick_hero_png(self, facing, phase):
        """기존 PNG 스프라이트 선택 (레거시 경로)."""
        if facing in ('left', 'right'):
            side = facing
            spr = (self._sprites.get(f'hero_attack_ready_{side}') if phase == 1 else
                   self._sprites.get(f'hero_attack_end_{side}')   if phase == 2 else None)
            return spr or self._sprites.get(f'hero_{side}') or self._sprites.get('hero')
        elif facing == 'up':
            spr = (self._sprites.get('hero_attack_ready_up') if phase == 1 else
                   self._sprites.get('hero_attack_end_up')   if phase == 2 else None)
            return (spr or self._sprites.get('hero_up')
                    or self._sprites.get('hero_back') or self._sprites.get('hero'))
        else:
            spr = (self._sprites.get('hero_attack_ready_down') if phase == 1 else
                   self._sprites.get('hero_attack_end_down')   if phase == 2 else None)
            return spr or self._sprites.get('hero_down') or self._sprites.get('hero')

    # 적/NPC를 마인크래프트 블록 스타일로 렌더 (False면 기존 아트)
    _USE_MC_MOBS = True

    def _enemy_sprite_fn(self, key):
        if self._USE_MC_MOBS:
            return _MC_SPRITE_FN.get(key) or _SPRITE_FN.get(key, mc_generic)
        return _SPRITE_FN.get(key, draw_generic)

    def _draw_enemy(self, enemy, x, y):
        fn = self._enemy_sprite_fn(enemy.key)
        ts = TILE_SIZE
        ticks = pygame.time.get_ticks()
        hurt = enemy.hurt_ms > 0
        telegraphing = enemy.windup_ms > 0 or enemy._pending_skill is not None
        if telegraphing:
            x += random.randint(-1, 1)
            y += random.randint(-1, 1)
        # 엘리트 오라: 발밑에 어픽스 색 링이 맥동
        if enemy.elite:
            aura = ELITE_AFFIXES[enemy.elite]['aura']
            pulse = int(2 * math.sin(ticks * 0.008))
            pygame.draw.ellipse(self._game_surf, aura,
                                (x + 3 - pulse, y + ts - 9 - pulse // 2,
                                 ts - 6 + pulse * 2, 8 + pulse), 2)
        # 스프라이트는 항상 실제 색으로 그린 뒤, 피격 시 흰색을 가산 블렌드해
        # '흰 실루엣' 플래시로 만든다. (col=흰색을 넘기면 checker 무늬가
        #  흰/회 체커보드 네모로 보이는 아티팩트가 있었음)
        if hurt or enemy.is_boss:
            tmp = pygame.Surface((ts, ts), pygame.SRCALPHA)
            fn(tmp, 0, 0, enemy.color, ticks)
            if hurt:
                tmp.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
            if enemy.is_boss:
                big = pygame.transform.scale(tmp, (ts * 2, ts * 2))
                blit_x, blit_y = x - ts // 2, y - ts // 2
                self._game_surf.blit(big, (blit_x, blit_y))
                bw = ts * 2 - 4
                ratio = max(0.0, enemy.hp / enemy.max_hp)
                _r(self._game_surf, (70, 20, 20), blit_x + 2, blit_y + 2, bw, 5)
                if ratio > 0:
                    hc = (200 + int(55*(1-ratio)), int(210*ratio), 40)
                    _r(self._game_surf, hc, blit_x + 2, blit_y + 2, max(1, int(bw*ratio)), 5)
            else:
                self._game_surf.blit(tmp, (x, y))
                if not enemy.is_prop:
                    draw_hp_bar(self._game_surf, x, y, enemy.hp, enemy.max_hp)
        else:
            fn(self._game_surf, x, y, enemy.color, ticks)
            if not enemy.is_prop:            # 프롭은 HP 바 없음
                draw_hp_bar(self._game_surf, x, y, enemy.hp, enemy.max_hp)
        # 공격 전조 '!' 마커 (회피 타이밍 안내)
        if telegraphing:
            mx = x + ts // 2
            my = y - (ts // 2 + 4 if enemy.is_boss else 2)
            _r(self._game_surf, (255, 220, 60), mx - 1, my - 9, 3, 6)
            _r(self._game_surf, (255, 220, 60), mx - 1, my - 1, 3, 2)

    _USE_MC_ITEMS = True

    def _draw_item(self, item, x, y):
        ts=TILE_SIZE; s=self._game_surf
        if self._USE_MC_ITEMS:
            # 살짝 떠오르는 부유 애니
            bob = int(2 * math.sin(pygame.time.get_ticks() * 0.004 + x))
            pygame.draw.ellipse(s, (24, 22, 30),
                                (x + 9, y + ts - 7, ts - 18, 4))   # 발밑 그림자
            from entities.item_icons import draw_mc_item
            draw_mc_item(s, x + 4, y + 2 + bob, ts - 8, item.item_type, item.color,
                         key=getattr(item, 'key', None))
            return
        ccx, ccy = x+ts//2, y+ts//2
        col = item.color
        pygame.draw.polygon(s, col, [(ccx,ccy-7),(ccx+6,ccy),(ccx,ccy+7),(ccx-6,ccy)])
        pygame.draw.polygon(s, WHITE, [(ccx,ccy-7),(ccx+6,ccy),(ccx,ccy+7),(ccx-6,ccy)], 1)
        if item.item_type == 'consumable':
            _r(s,(255,100,100),ccx-1,ccy-3,2,6); _r(s,(255,100,100),ccx-3,ccy-1,6,2)
        elif item.item_type == 'weapon':
            pygame.draw.line(s, WHITE, (ccx-3,ccy+3),(ccx+3,ccy-3), 2)
        elif item.item_type in ('armor', 'body'):
            pygame.draw.rect(s, WHITE, (ccx-2,ccy-2,4,4), 1)
        elif item.item_type == 'head':
            # 반원 (투구 모양)
            pygame.draw.arc(s, WHITE, (ccx-3, ccy-3, 6, 6), 0, 3.14159, 2)
        elif item.item_type == 'off_hand':
            # 방패: 위쪽 사각형 + 아래 삼각형
            pygame.draw.rect(s, WHITE, (ccx-3, ccy-3, 6, 4), 1)
            pygame.draw.line(s, WHITE, (ccx-3, ccy+1), (ccx, ccy+4), 1)
            pygame.draw.line(s, WHITE, (ccx+3, ccy+1), (ccx, ccy+4), 1)
        elif item.item_type == 'accessory':
            pygame.draw.circle(s, WHITE, (ccx, ccy), 3, 1)

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
                            ArrowAnim)
from core.audio import AudioManager
from core.skills import (SkillManager, SKILL_DEFS, COMBO_SKILL_DEFS, SKILL_UPGRADES,
                         SKILL_MAX_LEVEL, SKILL_XP_REQ, ULTIMATE_SKILL_DEFS,
                         SKILL_SP_COST, ALL_SKILL_DEFS, DEFAULT_EQUIPPED,
                         ENCHANT_DEFS, ENCHANT_TYPES, ENCHANT_MAX_LEVEL,
                         default_equipped_for)
from core.save_load import (save_game, load_game, has_save, delete_save,
                             load_settings, save_settings,
                             load_records, update_records,
                             list_cards, migrate_legacy_save, SLOT_COUNT)
from core.lang import t, set_lang
from core.combat import roll_damage
from map.generator import generate_dungeon
from map.tile import Tile, TileType
from map.theme import get_theme, is_new_theme, MAX_FLOOR
from entities.player import Player
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

        # 기록
        self._run_kills = 0
        self._records   = load_records()

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
        self.dungeon = None
        self.camera  = None

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
                if self._in_town and self._town:
                    self._town.update(dt, self.player.x, self.player.y)
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
        self._char_class = char_class if char_class in ('warrior', 'archer') else 'warrior'
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

    # ─────────────── 테스트 모드 ──────────────────────────────────────
    def start_test_mode(self, floor: int = 1, char_class='warrior'):
        """python3 main.py -test [층수] 로 호출 — 최대 스탯으로 지정 층 시작."""
        self._is_test_mode    = True
        self._save_data       = None
        self._char_class      = char_class if char_class in ('warrior', 'archer') else 'warrior'
        self._char_name       = 'TestHero'
        self._char_appearance = {'skin': 0, 'hair': 0, 'haircol': 0}
        self.floor            = max(1, min(floor, MAX_FLOOR))
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
        # 강화 시스템 테스트용 아이템
        from entities.item import Item as _Item
        p.enhance_stones = 100
        _sword_data = dict(self._item_data['sword']); _sword_data['key'] = 'sword'
        p.inventory.append(_Item(0, 0, _sword_data))
        _armor_data = dict(self._item_data['leather_armor']); _armor_data['key'] = 'leather_armor'
        p.inventory.append(_Item(0, 0, _armor_data))
        self.dungeon.reveal_all()
        self.state = 'playing'
        self.messages.append(('[TEST] 테스트 모드 — 저장 없음', 'info'))
        self.messages.append((f'[TEST] B{self.floor}F  최대 스탯 적용', 'good'))

    def start_town_test(self, floor: int = 1, char_class='warrior'):
        """python3 test_main.py town [층] — 던전 세션 생성 후 곧장 마을 진입."""
        self.start_test_mode(floor, char_class=char_class)
        self._enter_town()

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
        self.camera  = Camera(MAP_WIDTH, MAP_HEIGHT)
        self.camera.center_on(self.player.x, self.player.y)
        if not self._is_test_mode:
            self.dungeon.update_visibility(self.player.x, self.player.y)
        self.messages.append((t('floor_cont', self.floor), 'good'))
        self.state = 'playing'

    def _load_floor(self, is_new_game=False):
        self.floor = min(self.floor, MAX_FLOOR)
        self._quest_on_floor(self.floor)   # reach_floor 퀘스트 추적
        self.vfx_loot.clear()          # 이전 층 전리품 연출 정리
        dungeon, start = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, self.floor,
                                          self._enemy_data, self._item_data)
        self.dungeon  = dungeon
        self._theme   = get_theme(self.floor)
        if is_new_game:
            self.player = Player(*start,
                                 char_class=getattr(self, '_char_class', 'warrior'),
                                 char_name=getattr(self, '_char_name', 'Hero'))
            self.player.appearance = dict(getattr(self, '_char_appearance', None)
                                          or {'skin': 0, 'hair': 0, 'haircol': 0})
            self.messages.append((t('welcome'), 'good'))
            self.messages.append((t('wasd_hint'), 'info'))
            self.messages.append((t('archer_hint' if self.player.char_class == 'archer'
                                     else 'combat_hint'), 'info'))
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
            if not self._is_test_mode:
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
        if self._is_test_mode:
            self.dungeon.reveal_all()
        else:
            self.dungeon.update_visibility(self.player.x, self.player.y)

        # 파괴 가능 프롭 + 보물 고블린 (리스폰 카운트 산정 전에 스폰)
        self._spawn_floor_props()

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
                    # 드래그 시작 — 실제 클릭/버리기 처리는 MOUSEBUTTONUP에서
                    self._inv_drag_idx   = self._inv_slot_at(event.pos)
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
                if self._skillbook_open:
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
                elif self.state == 'inventory' and event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    self._start_discard_confirm(self._inv_sel)
                elif self.state == 'char_create':
                    self._handle_char_create_key(event.key, event.unicode)
                elif (self.state == 'menu' and self._menu_page == 'main'
                        and event.key == pygame.K_DELETE):
                    if self._menu_sel < len(self._cards):
                        c = self._cards[self._menu_sel]
                        if c.get('exists'):
                            self._delete_card(c['slot'])

        # 캐릭터 생성 화면은 raw 키 입력 전용 — 액션 처리 건너뜀
        if self.state == 'char_create':
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
                elif self.state in ('storage', 'inn', 'questlog'):
                    self.state = 'playing'
                elif self.state == 'dialog':
                    self._dialog_close(declined=True)
                elif self.state == 'paused':
                    self.state = 'playing'
                elif self.state == 'playing':
                    self._pause_sel = 0
                    self.state = 'paused'
                elif self.state == 'menu':
                    if self._menu_page == 'settings':
                        self._menu_page = 'main'
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
        typ = action['type']
        n = len(self._cards)
        total = n + 2  # + settings + quit
        if typ == 'move':
            dy = action.get('dy', 0)
            if dy != 0:
                self._menu_sel = (self._menu_sel + dy) % total
                self.audio.play('menu_select')
        elif typ in ('wait', 'confirm', 'load'):
            if self._menu_sel < n:
                self._select_card(self._cards[self._menu_sel])
            elif self._menu_sel == n:
                self.audio.play('menu_select')
                self._menu_page = 'settings'
                self._menu_settings_sel = 0
            elif self._menu_sel == n + 1:
                pygame.quit(); sys.exit()

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

    def _do_create_character(self):
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
            self._create_class = 'archer' if self._create_class == 'warrior' else 'warrior'
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

    def _inv_layout(self):
        pw = self._INV_COLS * self._INV_CELL + self._INV_PAD * 2
        ph = 56 + 4 * self._INV_CELL + self._INV_PAD * 2 + 60
        bx = WINDOW_WIDTH  // 2 - pw // 2
        by = WINDOW_HEIGHT // 2 - ph // 2
        return pw, ph, bx, by

    def _inv_slot_at(self, pos):
        _, _, bx, by = self._inv_layout()
        gx = bx + self._INV_PAD; gy = by + 56
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
        i = self._inv_slot_at(pos)
        if i is None:
            return
        inv = self.player.inventory
        if i == self._inv_sel and i < len(inv):
            self._do_use_inventory_item(inv[i])
            self._inv_sel = min(self._inv_sel, max(0, len(inv) - 1))
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
        if t == 'move':
            dx, dy = action.get('dx', 0), action.get('dy', 0)
            self._inv_sel = max(0, min(self.player.max_inventory - 1,
                                       self._inv_sel + dx + dy * cols))
        elif t in ('confirm', 'wait', 'attack'):
            if self._inv_sel < len(inv):
                self._do_use_inventory_item(inv[self._inv_sel])
                self._inv_sel = min(self._inv_sel, max(0, len(inv) - 1))

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
            if not self._is_test_mode and not self._in_town:
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
            return self._chain_attack(dx, dy, enemy)  # 범프도 콤보 체인에 합류
        target_tile = self.dungeon.tiles[ny][nx]

        # 버닝 스테이지 문
        if target_tile.tile_type == TileType.BURNING_DOOR:
            self._enter_burning_stage()
            return True

        # 벽 문: 이동 전에 처리 (blocked=False지만 사실상 벽 안쪽)
        if target_tile.tile_type == TileType.DOOR:
            self.audio.play('stairs')
            if self.floor >= MAX_FLOOR:
                self.messages.append((t('victory'), 'good'))
                self._records = update_records(self.floor, self._run_kills, self.player.gold)
                delete_save(self._save_slot)
                self.state = 'game_over'
            else:
                self.floor += 1
                if not self._is_test_mode:
                    self.achievements.check_floor(self.floor)
                self._start_fade(self._load_floor)
            return True

        if not self.dungeon.is_walkable(nx, ny):
            return False

        # 이동 슬라이딩: 현재 오프셋에 새 방향을 누적 (클램프)
        self._move_anim_offset[0] = max(-TILE_SIZE, min(TILE_SIZE, self._move_anim_offset[0] - dx * TILE_SIZE))
        self._move_anim_offset[1] = max(-TILE_SIZE, min(TILE_SIZE, self._move_anim_offset[1] - dy * TILE_SIZE))

        self.player.x, self.player.y = nx, ny
        item = self.dungeon.get_item_at(nx, ny)
        if item:
            self._pickup(item)

        # ── 포탈 밟기: 마을 ↔ 던전 ──────────────────────────────────
        if self._in_town:
            if self._town and (nx, ny) == self._town.portal_pos:
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
                self.animator.add(CalloutAnim(p.x, p.y, '···',
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

    def _chain_attack(self, dx, dy, enemy=None):
        """3단 콤보 본체 (Space 공격·이동 범프 공격 공용)."""
        step = self._chain_step if self._chain_window_ms > 0 else 0
        cost = self._STAMINA_COST['finisher' if step == 2 else 'slash']
        if not self._spend_stamina(cost):
            return False
        variant = self._CHAIN_VAR[step]
        self._atk_variant = variant
        self._trigger_atk_anim()

        if enemy is None:
            enemy = self.dungeon.get_enemy_at(self.player.x + dx,
                                              self.player.y + dy)
        finisher = (step == 2)
        self.animator.add(SmearAnim(
            self.player.x, self.player.y, self._facing, variant,
            (255, 190, 90) if finisher else (255, 240, 180)))
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
        gold = enemy.gold_drop
        self._run_kills += 1
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
                    self.messages.append((t('combo_unlock', cdef['name']), 'good'))
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
        gold = prop.gold_drop
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
        if item.effect == 'enhance_stone':
            self.player.enhance_stones += 1
            self.dungeon.remove_item(item)
            self.messages.append((t('enhance_stone_pickup', self.player.enhance_stones), 'good'))
            self.audio.play('pickup')
            return
        if item.effect == 'unlock_combo':
            combo_id = str(item.value)
            cdef = COMBO_SKILL_DEFS.get(combo_id)
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
        self.messages.append((t('town_enter'), 'good'))
        if moved:
            self.messages.append((t('town_deposit', moved), 'info'))
        self.audio.play('stairs')

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
            self.messages.append((t('town_return', self.floor), 'good'))
            self.audio.play('teleport')
        else:
            # 세션 없음 (마을에서 시작한 경우) → 현재 층 새로 생성
            self._load_floor()

    def _deposit_all_to_storage(self) -> int:
        """소지품 전량을 영구 창고로 이전하고 저장. 이전 개수 반환."""
        from core.save_load import save_storage
        moved = 0
        for it in list(self.player.inventory):
            if len(self._storage) >= self._storage_cap:
                self.messages.append((t('storage_cap_full'), 'warn'))
                break
            self._storage.append({'key': it.key,
                                  'enhance_level': it.enhance_level,
                                  'durability': it.durability})
            self.player.inventory.remove(it)
            moved += 1
        if moved:
            save_storage(self._storage, self._storage_cap)
        return moved

    def _storage_transfer(self):
        """창고 UI: 선택 항목을 반대편으로 이동 (즉시 디스크 저장)."""
        from core.save_load import save_storage
        from entities.item import Item
        if self._storage_pane == 0:                       # 소지품 → 창고
            inv = self.player.inventory
            if not inv:
                return
            if len(self._storage) >= self._storage_cap:
                self.messages.append((t('storage_cap_full'), 'warn'))
                return
            i = min(self._storage_cursor, len(inv) - 1)
            it = inv.pop(i)
            self._storage.append({'key': it.key,
                                  'enhance_level': it.enhance_level,
                                  'durability': it.durability})
            self.audio.play('pickup')
        else:                                             # 창고 → 소지품
            if not self._storage:
                return
            if len(self.player.inventory) >= self.player.max_inventory:
                self.messages.append((t('inv_full'), 'warn'))
                return
            i = min(self._storage_cursor, len(self._storage) - 1)
            entry = self._storage.pop(i)
            key = entry.get('key', '')
            if key in self._item_data:
                d = dict(self._item_data[key])
                d['key'] = key
                d['enhance_level'] = entry.get('enhance_level', 0)
                if 'durability' in entry:
                    d['durability'] = entry['durability']
                self.player.inventory.append(Item(0, 0, d))
            self.audio.play('pickup')
        save_storage(self._storage, self._storage_cap)    # 영구 반영
        self._storage_cursor = max(0, self._storage_cursor - 0)

    def _handle_storage_action(self, action):
        ty = action['type']
        cur_list = self.player.inventory if self._storage_pane == 0 else self._storage
        if ty == 'move':
            if action.get('dx'):
                self._storage_pane ^= 1
                self._storage_cursor = 0
            elif action.get('dy'):
                if cur_list:
                    self._storage_cursor = ((self._storage_cursor + action['dy'])
                                            % len(cur_list))
        elif ty in ('confirm', 'attack'):                 # Enter/Space 이동
            self._storage_transfer()

    def _town_interact(self):
        """마을에서 E: 인접 NPC 상호작용."""
        npc = self._town.npc_near(self.player.x, self.player.y) if self._town else None
        if not npc:
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
        elif 'quest' in npc:
            self._open_quest_dialog(npc['id'])

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
        title.set_alpha(alpha)
        self._game_surf.blit(title, (cx - title.get_width() // 2, cy - 24))
        nm = self.hud.font_md.render(self._quest_clear_name, True, (255, 250, 220))
        nm.set_alpha(alpha)
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
    _STORAGE_UPGRADES = {30: 500, 60: 2000}   # 현재 용량 → 확장 비용 (+30칸)

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
        self._storage_cap += 30
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
    _SKILL_STAMINA_COST = {'mobility': 15, 'defense': 20, 'attack': 22, 'buff': 20}

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
        cdef = COMBO_SKILL_DEFS.get(combo_id)
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
        if combo_id == 'WS': return self._skill_fortify()
        if combo_id == 'AD': return self._skill_thunder()
        if combo_id == 'WA': return self._skill_frost()
        if combo_id == 'WD': return self._skill_wind()
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
        self._start_shake(8, 500)
        self.skills.trigger('R')
        self.audio.play('skill_whirl')
        if hits:
            self.messages.append((t('ult_breaker_hit', hits), 'bad'))
        else:
            self.messages.append((t('ult_breaker_miss'), 'info'))
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
            )
            pygame.display.flip()
            return

        if self.state == 'char_create':
            self.hud.render_char_create(
                self.screen, self._create_class, self._create_name,
                self._create_sel, pygame.mouse.get_pos(),
                appearance=self._create_appearance())
            pygame.display.flip()
            return

        self._render_dungeon()
        self.hud.render(self.screen, self.player, self.messages, self.floor,
                        self.dungeon, self.skills,
                        unlocked_combos=self._unlocked_combos,
                        skill_books=self._skill_books,
                        skill_levels=self._skill_levels,
                        skill_xp=self._skill_xp,
                        is_test_mode=self._is_test_mode,
                        equipped_skills=self._equipped_skills)

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
                                    upgrade_cost=self._STORAGE_UPGRADES.get(self._storage_cap))
        elif self.state == 'inn':
            self.hud.render_inn(self.screen, self.player, self._inn_rest_cost())
        elif self.state == 'dialog' and self._dialog:
            self.hud.render_dialog(self.screen, self._dialog)
        elif self.state == 'questlog':
            self.hud.render_questlog(self.screen, self._quests,
                                     self._max_floor_reached)
        elif self.state == 'paused':
            self.hud.render_paused(self.screen, self._settings, self._pause_sel,
                                   mouse_pos=pygame.mouse.get_pos())
        elif self.state == 'dead':
            self.hud.render_game_over(self.screen, self.floor, self._records)
        elif self.state == 'inventory':
            self.hud.render_inventory(self.screen, self.player, self._inv_sel,
                                      mouse_pos=pygame.mouse.get_pos(),
                                      drag_idx=self._inv_drag_idx,
                                      drag_pos=self._inv_drag_pos)
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
            if tier:
                glow = pygame.transform.scale(txt, (txt.get_width() + 12,
                                                    txt.get_height() + 12))
                glow.set_alpha(alpha // 4)
                self._game_surf.blit(glow, ((GAME_W - glow.get_width()) // 2, 28))
            txt.set_alpha(alpha)
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

        # 화면 흔들림 + 펀치 줌 적용
        sox, soy = self._shake_offset
        if self._punch_zoom_ms > 0:
            k  = self._punch_zoom_ms / self._punch_zoom_max
            z  = 1.0 + self._punch_zoom_amt * k
            zw, zh = int(GAME_W * z), int(GAME_H * z)
            zoomed = pygame.transform.scale(self._game_surf, (zw, zh))
            clip = self.screen.get_clip()
            self.screen.set_clip(pygame.Rect(GAME_X, GAME_Y, GAME_W, GAME_H))
            self.screen.blit(zoomed, (GAME_X - (zw - GAME_W) // 2 + sox,
                                      GAME_Y - (zh - GAME_H) // 2 + soy))
            self.screen.set_clip(clip)
        else:
            self.screen.blit(self._game_surf, (GAME_X + sox, GAME_Y + soy))

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
        else:
            col = th['floor_lit'] if lit else th['floor_dim']
            pygame.draw.rect(s, col, (x,y,ts,ts))
            if lit: pygame.draw.rect(s, th['floor_edge'], (x,y,ts,ts), 1)
            if tt == TileType.STAIRS_DOWN:
                sc = th['stairs_lit'] if lit else th['stairs_dim']
                ccx, ccy = x+ts//2, y+ts//2
                pygame.draw.polygon(s, sc, [(ccx,ccy+7),(ccx-6,ccy-3),(ccx+6,ccy-3)])
                pygame.draw.line(s, sc, (ccx-4,ccy-3),(ccx+4,ccy-3), 2)

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

    def _draw_avatar_player(self, x, y, facing, phase, scale):
        """절차적 아바타 + (궁수) 활 오버레이. 강화술 스퀴즈 스케일 지원."""
        from entities.avatar import draw_avatar_tile
        from entities.player_renderer import draw_archer_bow
        ap  = getattr(self.player, 'appearance', None)
        cls = self.player.char_class
        if scale != 1.0:
            tmp = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            draw_avatar_tile(tmp, 0, 0, facing, self._walk_frame, phase, ap, cls)
            if cls == 'archer':
                draw_archer_bow(tmp, 0, 0, facing, phase)
            w = h = round(TILE_SIZE * scale)
            scaled = pygame.transform.scale(tmp, (w, h))
            off = (TILE_SIZE - w) // 2
            self._game_surf.blit(scaled, (x + off, y + off))
        else:
            draw_avatar_tile(self._game_surf, x, y, facing, self._walk_frame,
                             phase, ap, cls)
            if cls == 'archer':
                draw_archer_bow(self._game_surf, x, y, facing, phase)

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
        # 피격 순간 흰 플래시 / 공격 전조 중 미세 떨림
        col = (255, 255, 255) if enemy.hurt_ms > 0 else enemy.color
        telegraphing = enemy.windup_ms > 0 or enemy._pending_skill is not None
        if telegraphing:
            x += random.randint(-1, 1)
            y += random.randint(-1, 1)
        # 엘리트 오라: 발밑에 어픽스 색 링이 맥동
        if enemy.elite:
            aura = ELITE_AFFIXES[enemy.elite]['aura']
            pulse = int(2 * math.sin(pygame.time.get_ticks() * 0.008))
            pygame.draw.ellipse(self._game_surf, aura,
                                (x + 3 - pulse, y + ts - 9 - pulse // 2,
                                 ts - 6 + pulse * 2, 8 + pulse), 2)
        if enemy.is_boss:
            tmp = pygame.Surface((ts, ts))
            tmp.fill(_CKEY); tmp.set_colorkey(_CKEY)
            fn(tmp, 0, 0, col, pygame.time.get_ticks())
            big = pygame.transform.scale(tmp, (ts * 2, ts * 2))
            big.set_colorkey(_CKEY)
            blit_x, blit_y = x - ts // 2, y - ts // 2
            self._game_surf.blit(big, (blit_x, blit_y))
            # 보스 HP 바 (2배 너비)
            bw = ts * 2 - 4
            ratio = max(0.0, enemy.hp / enemy.max_hp)
            _r(self._game_surf, (70, 20, 20), blit_x + 2, blit_y + 2, bw, 5)
            if ratio > 0:
                col = (200 + int(55*(1-ratio)), int(210*ratio), 40)
                _r(self._game_surf, col, blit_x + 2, blit_y + 2, max(1, int(bw*ratio)), 5)
        else:
            fn(self._game_surf, x, y, col, pygame.time.get_ticks())
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
            draw_mc_item(s, x + 4, y + 2 + bob, ts - 8, item.item_type, item.color)
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

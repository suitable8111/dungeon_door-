import math
import os
import random
import sys
import pygame

from core.constants import *
from core.camera import Camera
from core.input_handler import InputHandler
from core.animator import (Animator, LungeAnim, SlashAnim, HitFlashAnim, BoltAnim,
                            AttackSwingAnim, DashTrailAnim, WhirlAnim, HealAnim)
from core.audio import AudioManager
from core.skills import (SkillManager, SKILL_DEFS, COMBO_SKILL_DEFS, SKILL_UPGRADES,
                         SKILL_MAX_LEVEL, SKILL_XP_REQ, ULTIMATE_SKILL_DEFS,
                         SKILL_SP_COST, ALL_SKILL_DEFS, DEFAULT_EQUIPPED)
from core.save_load import (save_game, load_game, has_save, delete_save,
                             load_settings, save_settings,
                             load_records, update_records)
from core.lang import t, set_lang
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
        set_lang(self._settings.get('language', 'ko'))
        flags = (pygame.FULLSCREEN | pygame.SCALED) if self._settings.get('fullscreen') else 0
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        pygame.display.set_caption("Dungeon Door")

        self.clock    = pygame.time.Clock()
        self.input    = InputHandler()
        self.hud      = HUD()
        self.animator = Animator()
        self.audio    = AudioManager()
        self.skills   = SkillManager()

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

        # 버닝 HUD 폰트 캐시 (매 프레임 SysFont 생성 방지)
        self._font_burning_big   = pygame.font.SysFont('Arial', 28, bold=True)
        self._font_burning_small = pygame.font.SysFont('Arial', 13)
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

        # 저장파일 확인 후 메뉴로
        self._save_data         = load_game()
        self._menu_sel          = 0
        self._menu_page         = 'main'
        self._menu_settings_sel = 0
        self._menu_buttons      = []
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
        base    = os.path.join(os.path.dirname(__file__), '..', 'assets')
        spr_dir = os.path.join(base, 'sprites')

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
            self._update_fade(dt)
            self._update_shake(dt)
            self._update_move_anim(dt)
            if not self._is_fading:
                self._handle_events(dt)
            self.animator.update(dt)
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
                if self._burning_active:
                    self._update_burning(dt)
            if self.state == 'playing':
                if self.player:
                    self.player.tick_debuffs(dt)
                self._update_enemies(dt)
            self._update_bgm()
            self._render()

    # ─────────────── 화면 흔들림 ──────────────────────────────────────
    def _start_shake(self, intensity=4, duration_ms=250):
        self._shake_intensity = intensity
        self._shake_timer     = duration_ms
        self._shake_max       = duration_ms

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
        factor = 0.982 ** dt
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
        elif self.state in ('playing', 'shop', 'paused', 'dead'):
            if self.dungeon is None:
                return
            if self.dungeon.is_boss_floor:
                self.audio.bgm.play('boss')
            elif self.dungeon.has_shop:
                self.audio.bgm.play('shop')
            else:
                self.audio.bgm.play(f'theme_{self.dungeon.theme_index}')

    # ─────────────── 새 게임 / 불러오기 ──────────────────────────────
    def _new_game(self):
        delete_save()
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
        self._equipped_skills = DEFAULT_EQUIPPED.copy()
        self._load_floor(is_new_game=True)
        self.state = 'playing'

    # ─────────────── 테스트 모드 ──────────────────────────────────────
    def start_test_mode(self, floor: int = 1):
        """python3 main.py -test [층수] 로 호출 — 최대 스탯으로 지정 층 시작."""
        self._is_test_mode    = True
        self._save_data       = None
        self.floor            = max(1, min(floor, MAX_FLOOR))
        self._facing          = 'down'
        self._walk_frame      = 0
        self.messages         = []
        self.skills           = SkillManager()
        self._run_kills       = 0
        # 모든 스킬 최대 레벨, 조합 스킬 전체 해금
        self._skill_levels    = {sid: SKILL_MAX_LEVEL for sid in ALL_SKILL_DEFS}
        self._skill_xp        = {sid: 0 for sid in ALL_SKILL_DEFS}
        self._equipped_skills = DEFAULT_EQUIPPED.copy()
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

    def start_burning_mode(self):
        """python3 test_main.py bunning — 버닝 스테이지 직행."""
        self.start_test_mode(floor=1)
        self._enter_burning_stage()
        self.clock.tick()   # 초기화 누적 시간 소비 — 첫 dt가 타이머를 왜곡하지 않도록

    def _continue_game(self):
        data = self._save_data
        if not data:
            self._new_game(); return
        self.floor       = data['floor']
        self._facing     = 'down'
        self._walk_frame = 0
        self.messages    = []
        self.skills           = SkillManager()
        self.skills.from_dict(data.get('skills', {}))
        self._unlocked_combos = set(data.get('unlocked_combos', []))
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
        self._apply_skill_level_cds()
        self._run_kills       = 0
        dungeon, start = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, self.floor,
                                          self._enemy_data, self._item_data)
        self.dungeon = dungeon
        self._theme  = get_theme(self.floor)
        self.player  = Player.from_save(start[0], start[1], data['player'], self._item_data)
        self.camera  = Camera(MAP_WIDTH, MAP_HEIGHT)
        self.camera.center_on(self.player.x, self.player.y)
        if not self._is_test_mode:
            self.dungeon.update_visibility(self.player.x, self.player.y)
        self.messages.append((t('floor_cont', self.floor), 'good'))
        self.state = 'playing'

    def _load_floor(self, is_new_game=False):
        self.floor = min(self.floor, MAX_FLOOR)
        dungeon, start = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, self.floor,
                                          self._enemy_data, self._item_data)
        self.dungeon  = dungeon
        self._theme   = get_theme(self.floor)
        if is_new_game:
            self.player = Player(*start)
            self.messages.append((t('welcome'), 'good'))
            self.messages.append((t('wasd_hint'), 'info'))
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
                              self._equipped_skills)
                self.messages.append((t('auto_saved'), 'info'))
                self.audio.play('save')
        self.camera = Camera(MAP_WIDTH, MAP_HEIGHT)
        self.camera.center_on(self.player.x, self.player.y)
        if self._is_test_mode:
            self.dungeon.reveal_all()
        else:
            self.dungeon.update_visibility(self.player.x, self.player.y)

        # 리스폰 설정: 보스 제외 초기 몬스터 수를 최대치로 고정
        self._respawn_max      = sum(1 for e in self.dungeon.enemies if not e.is_boss)
        self._respawn_timer_ms = self._RESPAWN_INTERVAL

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
                elif self._inv_confirm_idx is not None:
                    if event.key in (pygame.K_y, pygame.K_RETURN):
                        self._discard_inventory_item(self._inv_confirm_idx)
                        self._inv_confirm_idx = None
                    elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                        self._inv_confirm_idx = None
                elif self.state == 'inventory' and event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    self._start_discard_confirm(self._inv_sel)

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
                    self._enhance_open = True
                    self._enhance_cursor = 0
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
        n_main = 2 if self._save_data else 1
        total  = n_main + 2  # + settings + quit
        if typ == 'move':
            dy = action.get('dy', 0)
            if dy != 0:
                self._menu_sel = (self._menu_sel + dy) % total
                self.audio.play('menu_select')
        elif typ in ('wait', 'confirm'):
            if self._menu_sel == 0:
                self.audio.play('menu_confirm')
                self._new_game()
            elif self._menu_sel == 1 and self._save_data:
                self.audio.play('menu_confirm')
                self._continue_game()
            elif self._menu_sel == n_main:
                self.audio.play('menu_select')
                self._menu_page = 'settings'
                self._menu_settings_sel = 0
            elif self._menu_sel == n_main + 1:
                pygame.quit(); sys.exit()
        elif typ == 'load' and self._save_data:
            self.audio.play('menu_confirm')
            self._continue_game()

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
                if action == 'new':
                    self._new_game()
                elif action == 'continue' and self._save_data:
                    self._continue_game()
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
        self.messages.append((f"[{item.name}] 버림", 'info'))
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
                          self._equipped_skills)
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
            self._save_data      = load_game()
        elif self._pause_sel == 7:
            pygame.quit(); sys.exit()

    def _toggle_language(self):
        cur = self._settings.get('language', 'ko')
        self._settings['language'] = 'en' if cur == 'ko' else 'ko'
        set_lang(self._settings['language'])
        save_settings(self._settings)

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
    def _try_enemy_drop(self, enemy):
        import random
        from map.generator import drop_pool
        from entities.item import Item

        is_boss = getattr(enemy, 'is_boss', False)
        if not is_boss and random.random() >= 0.28:
            return

        pool = drop_pool(self.floor)
        if not pool:
            return
        key = random.choice(pool)
        if key not in self._item_data:
            return

        d = dict(self._item_data[key])
        d['key'] = key
        self.dungeon.items.append(Item(enemy.x, enemy.y, d))

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
            if not self._is_test_mode:
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
            self._trigger_atk_anim()
            self._player_attack(enemy)
            self._atk_cd_timer = self.player.atk_cooldown_ms
            return True
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
                delete_save()
                self.state = 'game_over'
            else:
                self.floor += 1
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

        tile = self.dungeon.tiles[ny][nx]
        if tile.tile_type == TileType.SHOP and self.dungeon.has_shop:
            self.state = 'shop'
            self.audio.play('shop_open')
            return True

        return True

    def _player_basic_attack(self):
        """Space bar: 바라보는 방향 인접 타일 공격. 적 없으면 허공 스윙."""
        if self._atk_cd_timer > 0:
            return False  # 쿨다운 중
        self._trigger_atk_anim()
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0,1))
        tx, ty = self.player.x + dx, self.player.y + dy
        enemy = self.dungeon.get_enemy_at(tx, ty)
        if enemy:
            self._player_attack(enemy)
        else:
            self.audio.play('swing')
        self._atk_cd_timer = self.player.atk_cooldown_ms
        return True

    def _do_use_inventory_item(self, item):
        """인벤토리 화면에서 선택한 아이템 사용/장착."""
        if item not in self.player.inventory and item.equip_slot is None:
            return
        if item.effect == 'teleport':
            if item in self.player.inventory:
                self.player.inventory.remove(item)
            self._use_teleport()
        elif item.effect == 'whirlwind':
            if item in self.player.inventory:
                self.player.inventory.remove(item)
            self._skill_whirl(no_cooldown=True)
        elif item.equip_slot:
            msg = item.use(self.player)
            self.messages.append((msg, 'good'))
            self.audio.play('use_item')
        else:
            if item in self.player.inventory:
                self.player.inventory.remove(item)
            self.messages.append((item.use(self.player), 'good'))
            self.audio.play('use_item')

    def _player_attack(self, enemy):
        # 두려움: 명중률 40%
        if getattr(self.player, 'feared_ms', 0) > 0 and random.random() > 0.4:
            self.messages.append(("두려움에 공격이 빗나갔습니다!", 'bad'))
            return
        crit = random.random() < 0.1
        dmg  = max(1, self.player.total_attack - enemy.defense + random.randint(0, 3))
        if crit:
            dmg *= 2
            self.messages.append((t('crit_hit', enemy.name, dmg), 'warn'))
        else:
            self.messages.append((t('normal_hit', enemy.name, dmg), 'warn'))
        enemy.take_damage(dmg)
        self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (255, 80, 80)))
        self.animator.particles.emit_basic_hit(enemy.x, enemy.y)
        self.audio.play('crit' if crit else 'attack')
        if not enemy.is_alive():
            self._on_enemy_killed(enemy)

    def _on_enemy_killed(self, enemy):
        gold = enemy.gold_drop
        self._run_kills += 1
        if gold:
            self.player.gold += gold
            self.messages.append((t('kill_gold', enemy.name, enemy.xp_value, gold), 'good'))
        else:
            self.messages.append((t('kill', enemy.name, enemy.xp_value), 'good'))
        if self.player.gain_xp(enemy.xp_value):
            self._skill_points += 3
            self.messages.append((t('levelup', self.player.level), 'good'))
            self.messages.append((f'스킬 포인트 +3 (보유: {self._skill_points})', 'info'))
            self.audio.play('levelup')
            for cid, cdef in COMBO_SKILL_DEFS.items():
                slv_req = cdef.get('skill_level_req', 1)
                if (cid in self._skill_books and
                        cid not in self._unlocked_combos and
                        self.player.level >= cdef['level_req'] and
                        all(self._skill_levels.get(self._equipped_skills.get(k, ''), 1) >= slv_req for k in cid)):
                    self._unlocked_combos.add(cid)
                    self.messages.append((t('combo_unlock', cdef['name']), 'good'))
        self.dungeon.enemies.remove(enemy)
        self._check_boss_cleared()
        # ── 아이템 드랍 ───────────────────────────────────────────
        self._try_enemy_drop(enemy)

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
            self.audio.play('use_item')
        elif item.effect == 'teleport':
            self.player.inventory.pop(slot)
            self._use_teleport()
        elif item.effect == 'whirlwind':
            self.player.inventory.pop(slot)
            self._skill_whirl(no_cooldown=True)
        else:
            self.player.inventory.pop(slot)
            self.messages.append((item.use(self.player), 'good'))
            self.audio.play('use_item')
        return True

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
        """스킬 데미지 기준 공격력 (장신구 강화 보너스 포함)."""
        return int(self.player.total_attack * self.player.skill_damage_mul)

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
        if not self.skills.ready(slot):
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
        }
        fn = _exec_map.get(skill_id)
        return fn(slot) if fn else False

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
            dmg  = max(1, int(self._skill_atk * mul) - enemy.defense + random.randint(0,3))
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
        self.messages.append((f"방어력 +{stats['def_bonus']} ({stats['def_ms']//1000}초)", 'good'))
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
        dmg  = max(1, int(self._skill_atk * mul) - enemy.defense)
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
        self.messages.append(('그림자 속으로 사라졌다!', 'warn'))
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
        self.messages.append((f'철갑 방벽! 피해 {int(stats["reduce"]*100)}% 감소 ({stats["duration_ms"]//1000}초)', 'good'))
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
                dmg = max(1, int(self._skill_atk * mul) - enemy.defense)
                enemy.take_damage(dmg)
                self.animator.add(HitFlashAnim(nx, ny, dmg, (255, 140, 40)))
                self.animator.particles.emit_power_hit(nx, ny)
                hits += 1
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
        self._gain_skill_xp('flame_strike', max(1, hits))
        self.skills.trigger(slot)
        self.audio.play('skill_dash')
        self.messages.append((f'화염 강타! {hits}명 적중' if hits else '화염이 허공을 갈랐다!',
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
            dmg = max(1, self._skill_atk - enemy.defense)
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
        self.messages.append((f'생명 흡수! {heal} HP 회복' if heal else '생명 흡수 (미적중)',
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
        self.messages.append((f'전투 함성! 공격력 +{int(stats["atk_mul"]*100)}% ({stats["duration_ms"]//1000}초)', 'good'))
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
            dmg = max(1, int(self._skill_atk * mul) - enemy.defense)
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
        self.messages.append((f'암흑 파동! {hits}명 적중' if hits else '파동이 허공에 사라졌다!',
                               'warn' if hits else 'info'))
        return True

    # ─────────────── 스킬 강화 ───────────────────────────────────────
    def _apply_skill_level_cds(self):
        for slot in ('W', 'A', 'S', 'D'):
            skill_id = self._equipped_skills.get(slot)
            if not skill_id:
                continue
            lvl = self._skill_levels.get(skill_id, 1)
            sdef = ALL_SKILL_DEFS.get(skill_id)
            if not sdef:
                continue
            cd_ms = sdef['upgrades'][min(lvl - 1, len(sdef['upgrades']) - 1)]['cd_ms']
            self.skills.set_cd_override(slot, cd_ms)

    def _gain_skill_xp(self, skill_id: str, amount: int = 1):
        """스킬 적중 → 5회 누적마다 SP +1."""
        self._skill_xp[skill_id] = self._skill_xp.get(skill_id, 0) + amount
        gained = self._skill_xp[skill_id] // 5
        if gained > 0:
            self._skill_xp[skill_id] %= 5
            self._skill_points += gained

    def _do_skill_upgrade(self, skill_id: str):
        """스킬 도감에서 Enter 시 호출 — SP를 소모해 스킬 레벨업."""
        lvl = self._skill_levels.get(skill_id, 1)
        sname = ALL_SKILL_DEFS.get(skill_id, {}).get('name', skill_id)
        if lvl >= SKILL_MAX_LEVEL:
            self.messages.append((f'{sname} 스킬이 이미 최대 레벨입니다.', 'warn'))
            return
        cost = SKILL_SP_COST.get(skill_id, [5, 10])[lvl - 1]
        if self._skill_points < cost:
            self.messages.append((f'SP가 부족합니다. (필요: {cost}, 보유: {self._skill_points})', 'warn'))
            return
        self._skill_points -= cost
        self._skill_levels[skill_id] = lvl + 1
        self._apply_skill_level_cds()
        self.messages.append((t('upg_done', sname, self._skill_levels[skill_id]), 'good'))
        self.audio.play('levelup')


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
                dmg  = max(1, int(self._skill_atk * 2.2) - enemy.defense)
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
            dmg = max(1, int(self._skill_atk * 1.2) - enemy.defense)
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
                dmg = max(1, int(self._skill_atk * 1.3) - enemy.defense)
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
                dmg = max(1, int(self._skill_atk * 1.8) - enemy.defense)
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

    _ENHANCE_STAT = {
        'weapon':    '공격력 +1',
        'body':      '방어력 +1',
        'off_hand':  '방어력 +1',
        'head':      '회피율 +1%',
        'feet':      '이동속도 +0.05',
        'accessory': '스킬 데미지 +5%',
    }

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
                    self.messages.append((f'[{slot}] 슬롯에 [{sname}] 장착!', 'good'))
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
                            self.messages.append((f'[{target}] 슬롯에 [{sname}] 장착!', 'good'))
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
                # U 키: SP 소모 업그레이드
                if self._skillbook_cursor >= 4:
                    avail_idx = self._skillbook_cursor - 4
                    if avail_idx < len(avail):
                        self._do_skill_upgrade(avail[avail_idx])
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
        elif key in (pygame.K_ESCAPE, pygame.K_p):
            self._enhance_open = False

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
        if self.player.enhance_stones < 1:
            self.messages.append((t('enhance_no_stone'), 'warn'))
            return
        self.player.enhance_stones -= 1
        rate = self._ENHANCE_RATES[item.enhance_level]
        if random.random() < rate:
            item.enhance_level += 1
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
        data = _scale_enemy(self._enemy_data[key], self.floor)
        data['key'] = key
        enemy = Enemy(sx, sy, data)
        self.dungeon.enemies.append(enemy)
        self.messages.append(('몬스터가 나타났다!', 'warn'))

    def _remove_fortify_buff(self):
        if self._fortify_def_bonus or self._fortify_atk_bonus:
            self.player.defense      -= self._fortify_def_bonus
            self.player.attack_speed -= self._fortify_atk_bonus
            self.player.attack_speed  = max(0.5, self.player.attack_speed)
            self._fortify_def_bonus   = 0
            self._fortify_atk_bonus   = 0.0

    # ─────────────── 궁극기 ─────────────────────────────────────────────
    def _use_ultimate(self, key: str):
        udef = ULTIMATE_SKILL_DEFS.get(key)
        if not udef:
            return False
        if self.player.level < udef['level_req']:
            self.messages.append((
                f"{udef['name']}: Lv.{udef['level_req']} 필요 (현재 Lv.{self.player.level})", 'warn'))
            return False
        if not self.skills.ready(key):
            self.messages.append((t('skill_cd', self.skills.remaining_sec(key)), 'info'))
            return False
        if key == 'R':
            return self._skill_ultimate_breaker()
        if key == 'Ctrl_R':
            return self._skill_ultimate_slash()
        return False

    def _skill_ultimate_breaker(self):
        """던전 브레이커: 화면 내 모든 적에게 공격력 3배 일격 + 대규모 이펙트."""
        targets = [e for e in self.dungeon.enemies
                   if e.is_alive() and self.dungeon.tiles[e.y][e.x].visible]
        hits = 0
        for enemy in targets:
            dmg = max(1, int(self._skill_atk * 3.0) - enemy.defense + random.randint(0, 5))
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
            self.messages.append((f"⚔ 던전 브레이커! {hits}마리 초토화!", 'bad'))
        else:
            self.messages.append(("⚔ 던전 브레이커! 적 없음", 'info'))
        return True

    def _skill_ultimate_slash(self):
        """진(眞) 일도양단: 2초 무적 + 화면 내 모든 적에게 공격력 10배."""
        self.player.invincible_ms = 2000
        targets = [e for e in self.dungeon.enemies
                   if e.is_alive() and self.dungeon.tiles[e.y][e.x].visible]
        hits = 0
        for enemy in targets:
            dmg = max(1, int(self._skill_atk * 10) - enemy.defense)
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
        msg = f"真 일도양단! 무적 2초 + {hits}마리 섬멸!" if hits else "真 일도양단! (적 없음)"
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
            prev_hp = self.player.hp
            result  = enemy.update(dt, self.dungeon, self.player, self.messages)
            if self.player.hp < prev_hp:
                dmg = prev_hp - self.player.hp
                self.animator.add(HitFlashAnim(self.player.x, self.player.y, dmg, (255,50,50)))
                self.audio.play('player_hit')
                self._start_shake(4 if enemy.is_boss else 2, 200)
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
                delete_save()
                self.audio.play('death')
                self.state = 'dead'

        # ── 몬스터 리스폰 ────────────────────────────────────────────
        if (not self._burning_active and
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
            sf = self._save_data['floor'] if self._save_data else None
            self._menu_buttons = self.hud.render_menu(
                self.screen, bool(self._save_data), sf,
                self._menu_sel, pygame.mouse.get_pos(),
                page=self._menu_page,
                settings=self._settings,
                settings_sel=self._menu_settings_sel,
                test_floor=self._test_floor,
            )
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
            self.hud.render_equipment(self.screen, self.player, self._equip_sel,
                                      self._sprites.get('hero_down'),
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
            )
        if self._enhance_open and self.state == 'playing':
            self.hud.render_enhance(self.screen, self.player, self._enhance_cursor, self._enhance_result)

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
                self._draw_item(item, (item.x-cx)*TILE_SIZE, (item.y-cy)*TILE_SIZE)

        for enemy in self.dungeon.enemies:
            if enemy.is_alive() and self.dungeon.tiles[enemy.y][enemy.x].visible:
                self._draw_enemy(enemy, (enemy.x-cx)*TILE_SIZE, (enemy.y-cy)*TILE_SIZE)

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

        # 화면 흔들림 오프셋 적용
        sox, soy = self._shake_offset
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

    def _draw_player_sprite(self, x, y):
        facing = self._facing
        phase  = self._atk_phase
        spr = None

        if facing in ('left', 'right'):
            side = 'left' if facing == 'left' else 'right'
            if phase == 1:
                spr = self._sprites.get(f'hero_attack_ready_{side}')
            elif phase == 2:
                spr = self._sprites.get(f'hero_attack_end_{side}')
            if spr is None:
                spr = self._sprites.get(f'hero_{side}') or self._sprites.get('hero')

        elif facing == 'up':
            if phase == 1:
                spr = self._sprites.get('hero_attack_ready_up')
            elif phase == 2:
                spr = self._sprites.get('hero_attack_end_up')
            if spr is None:
                spr = (self._sprites.get('hero_up')
                       or self._sprites.get('hero_back')
                       or self._sprites.get('hero'))

        else:  # down
            if phase == 1:
                spr = self._sprites.get('hero_attack_ready_down')
            elif phase == 2:
                spr = self._sprites.get('hero_attack_end_down')
            if spr is None:
                spr = self._sprites.get('hero_down') or self._sprites.get('hero')

        # Squeeze & Stretch 스케일 (강화술 시전 순간)
        scale = 1.0
        if self._fortify_effect and self._fortify_effect.alive:
            scale = self._fortify_effect.squeeze_scale

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
        )

    def _draw_enemy(self, enemy, x, y):
        fn = _SPRITE_FN.get(enemy.key, draw_generic)
        ts = TILE_SIZE
        if enemy.is_boss:
            tmp = pygame.Surface((ts, ts))
            tmp.fill(_CKEY); tmp.set_colorkey(_CKEY)
            fn(tmp, 0, 0, enemy.color, pygame.time.get_ticks())
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
            fn(self._game_surf, x, y, enemy.color, pygame.time.get_ticks())
            draw_hp_bar(self._game_surf, x, y, enemy.hp, enemy.max_hp)

    def _draw_item(self, item, x, y):
        ts=TILE_SIZE; s=self._game_surf
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

import os
import math
import pygame
from core.constants import *
from core.skills import SKILL_DEFS, SKILL_XP_REQ, SKILL_MAX_LEVEL
from core.lang import t
from map.tile import TileType


# ── 메뉴 전용 드로우 헬퍼 ────────────────────────────────────────────────

def _draw_gear(surf, cx, cy, r, col):
    """6-tooth 기어 아이콘."""
    pts = []
    for i in range(12):
        a  = math.pi * 2 * i / 12 - math.pi / 2
        rr = r if i % 2 == 0 else int(r * 0.64)
        pts.append((int(cx + math.cos(a) * rr), int(cy + math.sin(a) * rr)))
    pygame.draw.polygon(surf, col, pts)
    hole = max(2, r // 3 + 1)
    pygame.draw.circle(surf, (0, 0, 0), (cx, cy), hole)
    pygame.draw.circle(surf, col,       (cx, cy), max(1, hole - 2))


def _draw_x_icon(surf, cx, cy, col):
    pygame.draw.line(surf, col, (cx-5, cy-5), (cx+5, cy+5), 2)
    pygame.draw.line(surf, col, (cx+5, cy-5), (cx-5, cy+5), 2)


def _btn_colors(active, hovered, danger=False):
    """(bg, border, text_col) 반환."""
    if danger:
        if active:  return (50, 10, 10), (210, 70, 70),  (240, 110, 110)
        if hovered: return (32, 12, 12), (155, 50, 50),  (200,  80,  80)
        return              (18, 10, 10), ( 80, 30, 30),  (130,  60,  60)
    else:
        if active:  return (42, 36, 10), GOLD_COLOR,     GOLD_COLOR
        if hovered: return (22, 22, 42), (105,100,148),  WHITE
        return              (14, 14, 26), ( 46, 44, 70),  LIGHT_GRAY

_MSG_COLORS = {'info': MSG_INFO, 'warn': MSG_WARN, 'good': MSG_GOOD, 'bad': MSG_BAD}

_DUNGGEU_FONT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'DungGeunMo.ttf'))

_KO_FONT_FALLBACKS = [
    '/System/Library/Fonts/AppleSDGothicNeo.ttc',
    '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
    'C:/Windows/Fonts/malgun.ttf',
    '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
]


def _load_ko_font(size, bold=False):
    # 번들 폰트 우선
    if os.path.exists(_DUNGGEU_FONT):
        try:
            return pygame.font.Font(_DUNGGEU_FONT, size)
        except Exception:
            pass
    # 시스템 폰트 폴백
    for path in _KO_FONT_FALLBACKS:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass
    for name in ('applesdgothicneo', 'applegothic', 'malgunothic', 'nanumgothic'):
        f = pygame.font.SysFont(name, size, bold=bold)
        if f.size('가')[0] > 4:
            return f
    return pygame.font.SysFont('sans-serif', size, bold=bold)


class HUD:
    def __init__(self):
        pygame.font.init()
        self.font_sm = _load_ko_font(13)
        self.font_md = _load_ko_font(15)
        self.font_lg = _load_ko_font(30)
        self.font_xl = _load_ko_font(46)

        # PressStart2P 픽셀 폰트 (ASCII 전용)
        _base = os.path.join(os.path.dirname(__file__), '..', 'assets')
        _pf   = os.path.join(_base, 'fonts', 'PressStart2P-Regular.ttf')
        if os.path.exists(_pf):
            self.font_pixel_title = pygame.font.Font(_pf, 22)
            self.font_pixel_go    = pygame.font.Font(_pf, 18)
        else:
            self.font_pixel_title = None
            self.font_pixel_go    = None

        # 타이틀 배경 이미지 (원본 크기 유지, 가로 초과분은 중앙 크롭)
        _bg = os.path.join(_base, 'ui', 'title_background.png')
        if os.path.exists(_bg):
            try:
                self._title_bg = pygame.image.load(_bg).convert()
            except Exception:
                self._title_bg = None
        else:
            self._title_bg = None

    # ------------------------------------------------------------------ #
    def render(self, screen, player, messages, floor_num,
               dungeon=None, skill_mgr=None,
               unlocked_combos=None, skill_books=None,
               skill_levels=None, skill_xp=None,
               is_test_mode=False):
        self._top_bar(screen, player, floor_num, is_test_mode=is_test_mode)
        self._right_panel(screen, player, dungeon, skill_mgr,
                          unlocked_combos or set(), skill_books or set(),
                          skill_levels or {}, skill_xp or {})
        self._bottom_bar(screen, messages)

    # ------------------------------------------------------------------ #
    def render_game_over(self, screen, floor_num, records=None):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        go_font = self.font_pixel_go or self.font_xl
        title = go_font.render(t('gameover'), True, MSG_BAD)
        screen.blit(title, (_cx(title, WINDOW_WIDTH), WINDOW_HEIGHT // 2 - 80))

        sub = self.font_md.render(t('survived', floor_num), True, LIGHT_GRAY)
        screen.blit(sub, (_cx(sub, WINDOW_WIDTH), WINDOW_HEIGHT // 2 - 10))

        if records:
            rs = self.font_sm.render(
                t('best_rec', records['best_floor'], records['best_kills'], records['best_gold']),
                True, GOLD_COLOR)
            screen.blit(rs, (_cx(rs, WINDOW_WIDTH), WINDOW_HEIGHT // 2 + 26))
            runs = self.font_sm.render(t('total_runs', records['total_runs']), True, GRAY)
            screen.blit(runs, (_cx(runs, WINDOW_WIDTH), WINDOW_HEIGHT // 2 + 46))

        hint = self.font_md.render(t('go_hint'), True, WHITE)
        screen.blit(hint, (_cx(hint, WINDOW_WIDTH), WINDOW_HEIGHT // 2 + 75))

    # ------------------------------------------------------------------ #
    def render_menu(self, screen, has_save_file, save_floor=None,
                    sel=0, mouse_pos=(0, 0),
                    page='main', settings=None, settings_sel=0,
                    test_floor=None):
        """메인 메뉴 렌더링. 버튼 (pygame.Rect, action_str) 목록을 반환."""
        import random
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        cx = W // 2
        settings = settings or {}

        # ── 공통 배경 ────────────────────────────────────────────────
        if self._title_bg:
            # 이미지가 창보다 넓으면 중앙 크롭, 좁으면 그대로
            bw_img = self._title_bg.get_width()
            bh_img = self._title_bg.get_height()
            bx_off = -(bw_img - W) // 2 if bw_img > W else (W - bw_img) // 2
            by_off = -(bh_img - H) // 2 if bh_img > H else (H - bh_img) // 2
            screen.blit(self._title_bg, (bx_off, by_off))
            # 패널 가독성을 위한 반투명 어둠 오버레이
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 120))
            screen.blit(ov, (0, 0))
        else:
            screen.fill((5, 5, 12))
            rng = random.Random(77)
            for _ in range(110):
                sx = rng.randint(0, W); sy = rng.randint(0, H * 3 // 5)
                br = rng.randint(45, 165)
                pygame.draw.rect(screen, (br, br, min(255, br + 22)), (sx, sy, 1, 1))
            floor_y = H * 3 // 5
            for row in range(floor_y, H, 26):
                for col_x in range(0, W, 34):
                    sh = 9 + ((row // 26 + col_x // 34) % 5) * 2
                    pygame.draw.rect(screen, (sh, sh, sh + 3), (col_x, row, 33, 25))
                    pygame.draw.line(screen, (4, 4, 8), (col_x, row), (col_x + 33, row))
                    pygame.draw.line(screen, (4, 4, 8), (col_x, row), (col_x, row + 25))

        # ── 패널 크기 ────────────────────────────────────────────────
        if page == 'main':
            n_main = 2 if has_save_file else 1
            p_w = 450
            p_h = 82 + n_main * 68 + 14 + 2 * 50 + 52
        else:
            p_w = 440
            p_h = 350

        p_x = cx - p_w // 2
        p_y = H  // 2 - p_h // 2 - 18

        # 그림자 + 패널
        sh_s = pygame.Surface((p_w + 8, p_h + 8), pygame.SRCALPHA)
        sh_s.fill((0, 0, 0, 90))
        screen.blit(sh_s, (p_x + 4, p_y + 4))
        bg_s = pygame.Surface((p_w, p_h), pygame.SRCALPHA)
        bg_s.fill((8, 8, 22, 222))
        screen.blit(bg_s, (p_x, p_y))

        buttons = []

        # ════════════════════════════════════════════════════════════
        if page == 'main':
        # ════════════════════════════════════════════════════════════

            # ── 타이틀 ─────────────────────────────────────────────
            pygame.draw.rect(screen, (12, 10, 28), (p_x, p_y, p_w, 74))
            pygame.draw.line(screen, (70, 65, 100),
                             (p_x+20, p_y+74), (p_x+p_w-20, p_y+74))
            title_font = self.font_pixel_title or self.font_xl
            t1 = title_font.render("DUNGEON", True, GOLD_COLOR)
            t2 = title_font.render("DOOR",    True, (255, 235, 120))
            tw = t1.get_width() + 12 + t2.get_width()
            tx = cx - tw // 2
            ty = p_y + (74 - t1.get_height()) // 2
            screen.blit(t1, (tx, ty))
            screen.blit(t2, (tx + t1.get_width() + 12, ty))

            # ── 메인 버튼 (새 게임 / 이어하기) ─────────────────────
            bw = 320; bh = 52
            bx = cx - bw // 2
            by0 = p_y + 90

            main_items = [(t('menu_new'), 'new')]
            if has_save_file:
                lbl = t('menu_cont_f', save_floor) if save_floor else t('menu_cont')
                main_items.append((lbl, 'continue'))

            for i, (label, action) in enumerate(main_items):
                by   = by0 + i * 68
                rect = pygame.Rect(bx, by, bw, bh)
                act  = (i == sel)
                hov  = rect.collidepoint(mouse_pos)
                bg_c, bd_c, tc = _btn_colors(act, hov)
                bd_w = 2 if act else 1
                pygame.draw.rect(screen, bg_c, rect, border_radius=4)
                pygame.draw.rect(screen, bd_c, rect, bd_w, border_radius=4)
                if act:
                    arr = self.font_md.render("▶", True, GOLD_COLOR)
                    screen.blit(arr, (rect.left+14, rect.centery - arr.get_height()//2))
                ts = self.font_lg.render(label, True, tc)
                screen.blit(ts, (rect.centerx - ts.get_width()//2,
                                  rect.centery - ts.get_height()//2))
                buttons.append((rect, action))

            # ── 구분선 ─────────────────────────────────────────────
            sep_y = by0 + n_main * 68 + 6
            pygame.draw.line(screen, (44, 42, 66),
                             (p_x+30, sep_y), (p_x+p_w-30, sep_y))

            # ── 설정 / 종료 버튼 (나란히, 작은 크기) ───────────────
            sm_h = 44
            sm_w = (p_w - 60) // 2
            sm_y = sep_y + 12
            s_idx = n_main;     q_idx = n_main + 1

            for idx, action, lbl_key, danger, sm_x in [
                (s_idx, 'settings', 'menu_settings', False, p_x + 20),
                (q_idx, 'quit',     'menu_quit',     True,  p_x + 20 + sm_w + 20),
            ]:
                rect = pygame.Rect(sm_x, sm_y, sm_w, sm_h)
                act  = (idx == sel)
                hov  = rect.collidepoint(mouse_pos)
                bg_c, bd_c, tc = _btn_colors(act, hov, danger)
                pygame.draw.rect(screen, bg_c, rect, border_radius=4)
                pygame.draw.rect(screen, bd_c, rect, 1, border_radius=4)

                # 아이콘
                ico_cx = rect.left + 20
                ico_cy = rect.centery
                if not danger:
                    _draw_gear(screen, ico_cx, ico_cy, 8, tc)
                else:
                    _draw_x_icon(screen, ico_cx, ico_cy, tc)

                ts = self.font_md.render(t(lbl_key), True, tc)
                screen.blit(ts, (rect.left + 36,
                                  rect.centery - ts.get_height() // 2))
                buttons.append((rect, action))

            # ── 하단 힌트 ──────────────────────────────────────────
            fy = p_y + p_h - 32
            pygame.draw.line(screen, (42, 40, 64),
                             (p_x+20, fy-10), (p_x+p_w-20, fy-10))
            hint = self.font_sm.render(t('menu_hint'), True, (60, 58, 90))
            screen.blit(hint, (cx - hint.get_width()//2, fy))
            # 테두리를 마지막에 그려 내용에 가리지 않게
            pygame.draw.rect(screen, (62, 58, 92), (p_x,   p_y,   p_w,   p_h  ), 2)
            pygame.draw.rect(screen, (38, 34, 62), (p_x+3, p_y+3, p_w-6, p_h-6), 1)

        # ════════════════════════════════════════════════════════════
        else:  # page == 'settings'
        # ════════════════════════════════════════════════════════════

            # ── 설정 타이틀 ────────────────────────────────────────
            pygame.draw.rect(screen, (12, 10, 28), (p_x, p_y, p_w, 54))
            pygame.draw.line(screen, (70, 65, 100),
                             (p_x+20, p_y+54), (p_x+p_w-20, p_y+54))
            gear_cx = p_x + 36
            _draw_gear(screen, gear_cx, p_y + 27, 12, GOLD_COLOR)
            ts = self.font_lg.render(t('settings_title'), True, GOLD_COLOR)
            screen.blit(ts, (p_x + 58, p_y + 27 - ts.get_height()//2))

            # ── 설정 항목 ──────────────────────────────────────────
            lang_val = t('lang_ko') if settings.get('language','ko') == 'ko' else t('lang_en')
            fs_val   = t('pause_fs_on') if settings.get('fullscreen') else t('pause_fs_off')
            SITEMS = [
                (t('pause_bgm'), 'bgm',  settings.get('bgm_vol', 0.5)),
                (t('pause_sfx'), 'sfx',  settings.get('sfx_vol', 0.8)),
                (t('pause_lang'),'lang', lang_val),
                (t('pause_fs'),  'fs',   fs_val),
                (t('settings_back'), 'back', None),
            ]

            item_y0 = p_y + 62
            for i, (label, tag, val) in enumerate(SITEMS):
                iy   = item_y0 + i * 52
                rect = pygame.Rect(p_x+12, iy, p_w-24, 44)
                act  = (i == settings_sel)
                hov  = rect.collidepoint(mouse_pos)
                is_back = (tag == 'back')

                if is_back:
                    bg_c, bd_c, tc = _btn_colors(act, hov, False)
                    bg_c = (14, 28, 14) if act else ((10, 20, 10) if hov else (8, 14, 8))
                    bd_c = (60, 160, 80) if act else ((50, 110, 60) if hov else (30, 60, 35))
                    tc   = (100, 220, 120) if act else ((80, 170, 100) if hov else (55, 100, 65))
                else:
                    bg_c = (32, 28, 52) if act else ((20, 18, 36) if hov else (14, 12, 26))
                    bd_c = GOLD_COLOR   if act else ((85,  80,120) if hov else (42, 40, 65))
                    tc   = GOLD_COLOR   if act else (WHITE         if hov else LIGHT_GRAY)

                pygame.draw.rect(screen, bg_c, rect, border_radius=3)
                pygame.draw.rect(screen, bd_c, rect, 1, border_radius=3)

                # 라벨
                prefix = "← " if is_back else ("▶ " if act else "  ")
                ls = self.font_md.render(prefix + label, True, tc)
                screen.blit(ls, (rect.left + 10, iy + 12))

                # 값 / 바
                if tag in ('bgm', 'sfx') and isinstance(val, float):
                    bx2 = rect.right - 128; by2 = iy + 16; bw2 = 90; bh2 = 8
                    pygame.draw.rect(screen, (25, 25, 45), (bx2, by2, bw2, bh2))
                    fill = max(1, int(bw2 * val))
                    pygame.draw.rect(screen, (bd_c if act else (65, 65, 100)),
                                     (bx2, by2, fill, bh2))
                    pygame.draw.rect(screen, (55, 55, 88), (bx2, by2, bw2, bh2), 1)
                    pct = self.font_sm.render(f"{int(val*100)}%", True, tc)
                    screen.blit(pct, (bx2 + bw2 + 5, by2))
                    if act:
                        hs = self.font_sm.render(t('adj_hint'), True, GRAY)
                        screen.blit(hs, (rect.left + ls.get_width() + 14, iy + 14))
                elif isinstance(val, str):
                    vs = self.font_md.render(val, True, tc)
                    screen.blit(vs, (rect.right - vs.get_width() - 14, iy + 12))
                    if act and tag in ('lang', 'fs'):
                        hs = self.font_sm.render(t('adj_hint'), True, GRAY)
                        screen.blit(hs, (rect.left + ls.get_width() + 14, iy + 14))

                buttons.append((rect, tag))

            # ── 하단 힌트 ──────────────────────────────────────────
            fy = p_y + p_h - 30
            pygame.draw.line(screen, (42, 40, 64),
                             (p_x+20, fy-10), (p_x+p_w-20, fy-10))
            hint = self.font_sm.render(t('settings_hint'), True, (60, 58, 90))
            screen.blit(hint, (cx - hint.get_width()//2, fy))
            # 테두리를 마지막에 그려 내용에 가리지 않게
            pygame.draw.rect(screen, (62, 58, 92), (p_x,   p_y,   p_w,   p_h  ), 2)
            pygame.draw.rect(screen, (38, 34, 62), (p_x+3, p_y+3, p_w-6, p_h-6), 1)

        # ── 우상단 디버그 아이콘 (패널 바깥, test_floor 있을 때만) ──
        if test_floor is not None:
            iw, ih = 110, 32
            ix = W - iw - 10
            iy = 10
            irect = pygame.Rect(ix, iy, iw, ih)
            hov = irect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (160, 60, 0) if hov else (120, 40, 0), irect, border_radius=5)
            pygame.draw.rect(screen, (255, 160, 0), irect, 2, border_radius=5)
            lbl = self.font_sm.render(f"🐛 B{test_floor}F TEST", True, (255, 220, 100))
            screen.blit(lbl, (irect.centerx - lbl.get_width() // 2,
                               irect.centery - lbl.get_height() // 2))
            buttons.append((irect, 'test_mode'))

        return buttons

    # ------------------------------------------------------------------ #
    def render_shop(self, screen, shop_items, player_gold):
        overlay = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (GAME_X, GAME_Y))

        bx = GAME_X + GAME_W // 2 - 165
        by = GAME_Y + 75
        bw, bh = 330, 310

        pygame.draw.rect(screen, (18, 18, 32), (bx, by, bw, bh))
        pygame.draw.rect(screen, GOLD_COLOR, (bx, by, bw, bh), 2)

        title = self.font_lg.render(t('shop_title'), True, GOLD_COLOR)
        screen.blit(title, (bx + (bw - title.get_width()) // 2, by + 10))

        gold_txt = self.font_md.render(t('shop_gold', player_gold), True, GOLD_COLOR)
        screen.blit(gold_txt, (bx + (bw - gold_txt.get_width()) // 2, by + 50))

        pygame.draw.line(screen, UI_BORDER, (bx + 10, by + 75), (bx + bw - 10, by + 75))

        if shop_items:
            for i, (item, price) in enumerate(shop_items):
                iy = by + 88 + i * 38
                can_buy = player_gold >= price
                col = item.color if can_buy else GRAY
                line = self.font_md.render(f"[{i+1}]  {item.name}", True, col)
                screen.blit(line, (bx + 16, iy))
                pc = self.font_md.render(f"{price} G", True, GOLD_COLOR if can_buy else GRAY)
                screen.blit(pc, (bx + bw - pc.get_width() - 16, iy))
        else:
            empty = self.font_md.render(t('shop_empty'), True, GRAY)
            screen.blit(empty, (bx + (bw - empty.get_width()) // 2, by + 150))

        hint = self.font_sm.render(t('shop_hint'), True, LIGHT_GRAY)
        screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 28))

    # ------------------------------------------------------------------ #
    def render_boss_bar(self, screen, boss):
        bx = GAME_X + 10; by = GAME_Y + 8
        bw = GAME_W - 20; bh = 14
        pygame.draw.rect(screen, (50, 10, 10), (bx, by, bw, bh))
        ratio = max(0.0, boss.hp / boss.max_hp)
        if ratio > 0:
            fc = (200, 50, 200) if ratio > 0.5 else (220, 30, 80)
            pygame.draw.rect(screen, fc, (bx, by, int(bw * ratio), bh))
        pygame.draw.rect(screen, BOSS_COLOR, (bx, by, bw, bh), 1)
        label = self.font_sm.render(t('boss_bar', boss.name, boss.hp, boss.max_hp), True, (255, 200, 255))
        screen.blit(label, (bx, by + bh + 3))

    # ------------------------------------------------------------------ #
    def render_paused(self, screen, settings, pause_sel):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        bw = 370; bh = 490
        bx = WINDOW_WIDTH  // 2 - bw // 2
        by = WINDOW_HEIGHT // 2 - bh // 2

        pygame.draw.rect(screen, (12, 12, 26), (bx, by, bw, bh))
        pygame.draw.rect(screen, (90, 90, 130), (bx, by, bw, bh), 2)
        pygame.draw.rect(screen, (30, 30, 55), (bx+2, by+2, bw-4, 38))

        title_s = self.font_lg.render(t('pause_title'), True, WHITE)
        screen.blit(title_s, (bx + (bw - title_s.get_width()) // 2, by + 8))
        pygame.draw.line(screen, (60, 60, 95), (bx+12, by+44), (bx+bw-12, by+44))

        lang_val = t('lang_ko') if settings.get('language', 'ko') == 'ko' else t('lang_en')
        fs_val   = t('pause_fs_on') if settings['fullscreen'] else t('pause_fs_off')

        ITEMS = [
            (t('pause_resume'),                              None),
            (t('pause_save'),                                'save'),
            (f"{t('pause_bgm')}    {int(settings['bgm_vol']*100):3d}%", 'bgm'),
            (f"{t('pause_sfx')}    {int(settings['sfx_vol']*100):3d}%", 'sfx'),
            (f"{t('pause_fs')}    {fs_val}",                'fs'),
            (f"{t('pause_lang')}    {lang_val}",            'lang'),
            (t('pause_title_'),                              'title'),
            (t('pause_quit'),                                'quit'),
        ]

        item_colors = {
            None: WHITE, 'save': (100, 220, 130),
            'bgm': LIGHT_GRAY, 'sfx': LIGHT_GRAY, 'fs': LIGHT_GRAY,
            'lang': (120, 200, 255), 'title': LIGHT_GRAY, 'quit': (200, 80, 80),
        }

        for i, (text, tag) in enumerate(ITEMS):
            is_sel = (i == pause_sel)
            iy = by + 56 + i * 46

            if is_sel:
                pygame.draw.rect(screen, (30, 30, 58), (bx+8, iy-3, bw-16, 32))
                pygame.draw.rect(screen, (70, 70, 110), (bx+8, iy-3, bw-16, 32), 1)

            base_col = GOLD_COLOR if is_sel else item_colors.get(tag, LIGHT_GRAY)
            prefix = "▶ " if is_sel else "   "
            s = self.font_md.render(prefix + text, True, base_col)
            screen.blit(s, (bx + 20, iy + 3))

            if tag in ('bgm', 'sfx') and is_sel:
                h = self.font_sm.render(t('adj_hint'), True, GRAY)
                screen.blit(h, (bx + bw - h.get_width() - 14, iy + 7))
            elif tag == 'save' and is_sel:
                h = self.font_sm.render(t('save_hint'), True, (60, 180, 90))
                screen.blit(h, (bx + bw - h.get_width() - 14, iy + 7))
            elif tag in ('fs', 'lang') and is_sel:
                h = self.font_sm.render(t('adj_hint'), True, GRAY)
                screen.blit(h, (bx + bw - h.get_width() - 14, iy + 7))

        pygame.draw.line(screen, (60, 60, 95), (bx+12, by+bh-36), (bx+bw-12, by+bh-36))
        esc_hint = self.font_sm.render(t('pause_hint'), True, GRAY)
        screen.blit(esc_hint, (bx + (bw - esc_hint.get_width()) // 2, by + bh - 24))

    # ------------------------------------------------------------------ #
    def _top_bar(self, screen, player, floor_num, is_test_mode=False):
        pygame.draw.rect(screen, (10, 10, 20), (0, 0, WINDOW_WIDTH, TOP_BAR_H))
        pygame.draw.line(screen, (50, 50, 80), (0, TOP_BAR_H - 2), (WINDOW_WIDTH, TOP_BAR_H - 2))
        pygame.draw.line(screen, (25, 25, 45), (0, TOP_BAR_H - 1), (WINDOW_WIDTH, TOP_BAR_H - 1))

        cy = TOP_BAR_H // 2  # 세로 중앙

        # ── 층 표시 ──
        fl = self.font_md.render(f"B{floor_num}F", True, (180, 180, 220))
        screen.blit(fl, (12, cy - fl.get_height() // 2))
        x = 12 + fl.get_width() + 10

        pygame.draw.line(screen, (50, 50, 75), (x, 6), (x, TOP_BAR_H - 6))
        x += 10

        # ── 레벨 ──
        lv = self.font_md.render(f"Lv.{player.level}", True, XP_COLOR)
        screen.blit(lv, (x, cy - lv.get_height() // 2))
        x += lv.get_width() + 12

        pygame.draw.line(screen, (50, 50, 75), (x, 6), (x, TOP_BAR_H - 6))
        x += 10

        # ── HP 바 ──
        hp_label = self.font_sm.render("HP", True, HP_COLOR)
        screen.blit(hp_label, (x, cy - hp_label.get_height() // 2))
        x += hp_label.get_width() + 6

        hp_bw = 140; hp_bh = 10
        hp_by = cy - hp_bh // 2
        ratio = max(0.0, player.hp / player.max_hp)
        pygame.draw.rect(screen, (55, 18, 18), (x, hp_by, hp_bw, hp_bh))
        if ratio > 0:
            bar_col = (int(180 + 70 * (1 - ratio)), int(200 * ratio), 30)
            pygame.draw.rect(screen, bar_col, (x, hp_by, max(1, int(hp_bw * ratio)), hp_bh))
        pygame.draw.rect(screen, (90, 35, 35), (x, hp_by, hp_bw, hp_bh), 1)
        hp_txt = self.font_sm.render(f"{player.hp}/{player.max_hp}", True, (210, 210, 210))
        screen.blit(hp_txt, (x + hp_bw + 5, cy - hp_txt.get_height() // 2))
        x += hp_bw + hp_txt.get_width() + 16

        pygame.draw.line(screen, (50, 50, 75), (x, 6), (x, TOP_BAR_H - 6))
        x += 10

        # ── XP 바 ──
        xp_label = self.font_sm.render("XP", True, XP_COLOR)
        screen.blit(xp_label, (x, cy - xp_label.get_height() // 2))
        x += xp_label.get_width() + 6

        xp_bw = 110; xp_bh = 8
        xp_by = cy - xp_bh // 2
        pygame.draw.rect(screen, XP_BG, (x, xp_by, xp_bw, xp_bh))
        if player.xp_next > 0:
            xp_fill = max(0, int(xp_bw * player.xp / player.xp_next))
            if xp_fill:
                pygame.draw.rect(screen, XP_COLOR, (x, xp_by, xp_fill, xp_bh))
        pygame.draw.rect(screen, (40, 60, 100), (x, xp_by, xp_bw, xp_bh), 1)
        xp_txt = self.font_sm.render(f"{player.xp}/{player.xp_next}", True, (100, 160, 220))
        screen.blit(xp_txt, (x + xp_bw + 5, cy - xp_txt.get_height() // 2))
        x += xp_bw + xp_txt.get_width() + 16

        # ── 골드 (오른쪽) ──
        gold_s = self.font_md.render(f"G  {player.gold}", True, GOLD_COLOR)
        gx = WINDOW_WIDTH - gold_s.get_width() - 16
        screen.blit(gold_s, (gx, cy - gold_s.get_height() // 2))

        # ── TEST 모드 배지 ──
        if is_test_mode:
            badge = self.font_md.render("TEST MODE", True, (20, 20, 20))
            bw = badge.get_width() + 14
            bh = TOP_BAR_H - 8
            bx = gx - bw - 14
            by = 4
            pygame.draw.rect(screen, (255, 80, 0), (bx, by, bw, bh))
            pygame.draw.rect(screen, (255, 160, 60), (bx, by, bw, bh), 1)
            screen.blit(badge, (bx + 7, by + bh // 2 - badge.get_height() // 2))

    def _right_panel(self, screen, player, dungeon, skill_mgr,
                     unlocked_combos=None, skill_books=None,
                     skill_levels=None, skill_xp=None):
        rx = GAME_W
        pw = RIGHT_PANEL_W
        bw = pw - 16

        pygame.draw.rect(screen, (10, 10, 20), (rx, 0, pw, WINDOW_HEIGHT))
        pygame.draw.line(screen, (50, 50, 80), (rx, 0), (rx, WINDOW_HEIGHT))
        pygame.draw.line(screen, (25, 25, 45), (rx+1, 0), (rx+1, WINDOW_HEIGHT))

        y = TOP_BAR_H + 2

        # ── 섹션 헤더 유틸 ──────────────────────────────────────────
        def sec_header(key, col):
            nonlocal y
            pygame.draw.rect(screen, (22, 22, 42), (rx, y, pw, 16))
            pygame.draw.line(screen, (55, 55, 85), (rx, y+16), (rx+pw, y+16))
            screen.blit(self.font_sm.render(t(key), True, col), (rx+8, y+1))
            y += 18

        # ── 스탯 ────────────────────────────────────────────────────
        sec_header('sec_stats', LIGHT_GRAY)
        atk_bonus = player.total_attack - player.attack
        def_bonus = player.total_defense - player.defense
        atk_str = str(player.total_attack) + (f" (+{atk_bonus})" if atk_bonus else "")
        def_str = str(player.total_defense) + (f" (+{def_bonus})" if def_bonus else "")
        stats = [
            ('공격력',   atk_str,                         WHITE),
            ('방어력',   def_str,                         (130, 180, 255)),
            ('공격속도', f"{player.attack_speed:.2f}",    (255, 200, 80)),
            ('회피율',   f"{player.evasion}%",            (80, 220, 160)),
            ('이동속도', f"{player.move_speed:.2f}",      (160, 160, 255)),
        ]
        for label, val, col in stats:
            lbl_s = self.font_sm.render(label, True, (100, 100, 130))
            val_s = self.font_sm.render(val, True, col)
            screen.blit(lbl_s, (rx+8, y))
            screen.blit(val_s, (rx + pw - val_s.get_width() - 8, y))
            y += 14
        y += 2

        # ── 장착 장비 ───────────────────────────────────────────────
        sec_header('sec_equip', LIGHT_GRAY)
        _SLOT_LABELS = {'head': '투구', 'body': '갑옷', 'weapon': '무기',
                        'off_hand': '보조', 'accessory': '장신구'}
        for slot, item in player.equipment.items():
            lbl_s = self.font_sm.render(_SLOT_LABELS.get(slot, slot), True, (100, 100, 130))
            if item:
                pygame.draw.rect(screen, (20, 22, 38), (rx+6, y-1, pw-12, 15))
                nm = item.name if len(item.name) <= 8 else item.name[:7] + '…'
                val_s = self.font_sm.render(nm, True, item.color)
            else:
                val_s = self.font_sm.render('--', True, (40, 40, 60))
            screen.blit(lbl_s, (rx+8, y))
            screen.blit(val_s, (rx + pw - val_s.get_width() - 8, y))
            y += 14
        y += 2

        # ── 빠른 아이템 (슬롯 1-5) ──────────────────────────────────
        sec_header('sec_inv', LIGHT_GRAY)
        for i in range(5):
            if i < len(player.inventory):
                item = player.inventory[i]
                nm = item.name if len(item.name) <= 9 else item.name[:8] + '…'
                pygame.draw.rect(screen, (20, 22, 38), (rx+6, y-1, pw-12, 14))
                txt = self.font_sm.render(f"[{i+1}] {nm}", True, item.color)
            else:
                txt = self.font_sm.render(f"[{i+1}] ---", True, (40, 40, 60))
            screen.blit(txt, (rx+8, y)); y += 14
        y += 2

        # ── 단일 스킬 (W/A/S/D) ─────────────────────────────────────
        sec_header('sec_skills', LIGHT_GRAY)
        _SKILL_TRANS = {
            'W': ('skill_w_name', 'skill_w_desc'),
            'A': ('skill_a_name', 'skill_a_desc'),
            'S': ('skill_s_name', 'skill_s_desc'),
            'D': ('skill_d_name', 'skill_d_desc'),
        }
        sl = skill_levels or {}
        sx = skill_xp or {}
        for sdef in SKILL_DEFS:
            sk    = sdef['key']
            ready = skill_mgr.ready(sk) if skill_mgr else True
            frac  = skill_mgr.cooldown_frac(sk) if skill_mgr else 0.0
            rem   = skill_mgr.remaining_sec(sk) if skill_mgr else 0.0
            nc    = sdef['color'] if ready else (60, 60, 80)
            nk, dk = _SKILL_TRANS.get(sk, ('', ''))
            lvl    = sl.get(sk, 1)
            is_max = lvl >= SKILL_MAX_LEVEL
            lv_str = " MAX" if is_max else (f" Lv.{lvl}" if lvl > 1 else "")
            label  = f"[{sk}] {t(nk)}{lv_str}" if nk else f"[{sk}] {sdef['name']}{lv_str}"

            if ready:
                pygame.draw.rect(screen, (20, 28, 50), (rx+6, y-1, pw-12, 24))
            name_s = self.font_sm.render(label, True, nc)
            screen.blit(name_s, (rx+8, y))
            if not ready:
                rem_s = self.font_sm.render(f"{rem:.1f}s", True, (90, 90, 110))
                screen.blit(rem_s, (rx + pw - rem_s.get_width() - 8, y))
            y += 13
            _bar(screen, rx+8, y, bw, 5, int(bw*(1-frac)), bw,
                 sdef['color'] if ready else (40, 40, 65), (18, 18, 35))
            y += 6
            if not is_max:
                xp_cur = sx.get(sk, 0)
                xp_req = SKILL_XP_REQ[sk][lvl - 1]
                _bar(screen, rx+8, y, bw, 3, xp_cur, xp_req, (80, 160, 80), (12, 20, 12))
                y += 4
            y += 2
        y += 3

        # ── 강화 스킬 ────────────────────────────────────────────────
        from core.skills import COMBO_SKILL_DEFS
        sec_header('sec_combo', (130, 110, 200))
        uc = unlocked_combos or set()
        sb = skill_books or set()
        for cid, cdef in COMBO_SKILL_DEFS.items():
            unlocked = cid in uc
            has_book = cid in sb
            ready    = skill_mgr.ready(cid) if (skill_mgr and unlocked) else False
            rem      = skill_mgr.remaining_sec(cid) if (skill_mgr and unlocked) else 0.0

            key_lbl = f"[{cdef['keys']}]"
            if unlocked:
                col = cdef['color'] if ready else (70, 70, 100)
                pygame.draw.rect(screen, (18, 20, 38), (rx+6, y-1, pw-12, 13))
                ks = self.font_sm.render(key_lbl, True, col)
                ns = self.font_sm.render(cdef['name'], True, col)
                screen.blit(ks, (rx+8, y))
                screen.blit(ns, (rx+8 + ks.get_width() + 4, y))
                if not ready:
                    rs = self.font_sm.render(f"{rem:.1f}s", True, (80, 80, 105))
                    screen.blit(rs, (rx + pw - rs.get_width() - 8, y))
            elif has_book:
                col = (70, 70, 90)
                ks  = self.font_sm.render(key_lbl, True, col)
                ns  = self.font_sm.render(f"{cdef['name']} Lv.{cdef['level_req']}", True, col)
                screen.blit(ks, (rx+8, y))
                screen.blit(ns, (rx+8 + ks.get_width() + 4, y))
            else:
                col = (45, 45, 65)
                ks  = self.font_sm.render(key_lbl, True, col)
                ns  = self.font_sm.render(f"??? Lv.{cdef['level_req']}", True, col)
                screen.blit(ks, (rx+8, y))
                screen.blit(ns, (rx+8 + ks.get_width() + 4, y))
            y += 13
        y += 2

        # ── 미니맵 ──────────────────────────────────────────────────
        sec_header('sec_minimap', LIGHT_GRAY)
        if dungeon:
            self._draw_minimap(screen, dungeon, player, rx+8, y)

    def _draw_minimap(self, screen, dungeon, player, ox, oy):
        scale = 2
        pygame.draw.rect(screen, (8, 8, 18), (ox, oy, dungeon.width*scale, dungeon.height*scale))

        for my in range(dungeon.height):
            for mx in range(dungeon.width):
                tile = dungeon.tiles[my][mx]
                if not tile.explored:
                    continue
                tt = tile.tile_type
                if not tile.visible:
                    if tt == TileType.DOOR: col = (80, 40, 120)
                    elif tt == TileType.WALL: col = (30, 30, 42)
                    else: col = (40, 40, 55)
                else:
                    if tt == TileType.WALL:        col = (60,60,80)
                    elif tt == TileType.STAIRS_DOWN: col = STAIRS_LIT
                    elif tt == TileType.SHOP:        col = SHOP_COLOR
                    elif tt == TileType.DOOR:        col = (160, 80, 255)
                    else:                            col = (75,75,100)
                pygame.draw.rect(screen, col, (ox+mx*scale, oy+my*scale, scale, scale))

        for enemy in dungeon.enemies:
            if enemy.is_alive() and dungeon.tiles[enemy.y][enemy.x].visible:
                ec = BOSS_COLOR if enemy.is_boss else (220,60,60)
                pygame.draw.rect(screen, ec, (ox+enemy.x*scale, oy+enemy.y*scale, scale, scale))

        pygame.draw.rect(screen, WHITE, (ox+player.x*scale-1, oy+player.y*scale-1, scale+1, scale+1))
        pygame.draw.rect(screen, UI_BORDER, (ox, oy, dungeon.width*scale, dungeon.height*scale), 1)

    # ------------------------------------------------------------------ #
    def render_skill_upgrade(self, screen, skill_levels, skill_points, sel):
        from core.skills import SKILL_UPGRADES, SKILL_MAX_LEVEL

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        screen.blit(overlay, (0, 0))

        bw = 420; bh = 390
        bx = WINDOW_WIDTH  // 2 - bw // 2
        by = WINDOW_HEIGHT // 2 - bh // 2

        pygame.draw.rect(screen, (12, 12, 26), (bx, by, bw, bh))
        pygame.draw.rect(screen, (90, 90, 130), (bx, by, bw, bh), 2)
        pygame.draw.rect(screen, (30, 30, 55), (bx+2, by+2, bw-4, 40))

        # ── 제목 + SP 표시 ──
        title_s = self.font_lg.render(t('upg_title'), True, WHITE)
        sp_col  = GOLD_COLOR if skill_points > 0 else (80, 80, 100)
        sp_s    = self.font_md.render(t('upg_sp', skill_points), True, sp_col)
        screen.blit(title_s, (bx + 20, by + 8))
        screen.blit(sp_s,    (bx + bw - sp_s.get_width() - 18, by + 11))
        pygame.draw.line(screen, (60, 60, 95), (bx+12, by+46), (bx+bw-12, by+46))

        _KEYS  = ['W', 'A', 'S', 'D']
        _NAMES = {'W': t('skill_w_name'), 'A': t('skill_a_name'),
                  'S': t('skill_s_name'), 'D': t('skill_d_name')}
        _COLS  = {'W': (100,180,255), 'A': (255,180,60),
                  'S': (80,220,130),  'D': (255,100,80)}

        for i, key in enumerate(_KEYS):
            lvl    = skill_levels.get(key, 1)
            is_sel = (i == sel)
            is_max = (lvl >= SKILL_MAX_LEVEL)
            iy     = by + 54 + i * 76

            if is_sel:
                pygame.draw.rect(screen, (28, 28, 58), (bx+8, iy-2, bw-16, 70))
                pygame.draw.rect(screen, (75, 75, 125), (bx+8, iy-2, bw-16, 70), 1)

            # 스킬 이름 + 레벨
            base_col = _COLS[key]
            name_col = base_col if is_sel else tuple(max(0, c - 70) for c in base_col)
            lv_str   = "MAX" if is_max else f"Lv.{lvl}"
            prefix   = "▶ " if is_sel else "  "
            hdr = self.font_md.render(
                f"{prefix}[{key}] {_NAMES[key]}  {lv_str}", True,
                GOLD_COLOR if is_sel else LIGHT_GRAY)
            screen.blit(hdr, (bx+16, iy+3))

            # 현재 스탯
            curr_s = self.font_sm.render(
                _fmt_skill_stats(key, SKILL_UPGRADES[key][lvl - 1]), True, (130, 130, 160))
            screen.blit(curr_s, (bx+28, iy+22))

            if not is_max:
                nxt_col = (90, 200, 120) if (is_sel and skill_points > 0) else (50, 90, 65)
                nxt_s   = self.font_sm.render(
                    "→ " + _fmt_skill_stats(key, SKILL_UPGRADES[key][lvl]), True, nxt_col)
                screen.blit(nxt_s, (bx+28, iy+40))
                if is_sel and skill_points > 0:
                    cf = self.font_sm.render(t('upg_confirm'), True, (100, 220, 130))
                    screen.blit(cf, (bx + bw - cf.get_width() - 18, iy+40))
            else:
                mx = self.font_sm.render(t('upg_max'), True, (180, 155, 50))
                screen.blit(mx, (bx+28, iy+40))

        pygame.draw.line(screen, (60, 60, 95), (bx+12, by+bh-36), (bx+bw-12, by+bh-36))
        hint = self.font_sm.render(t('upg_hint'), True, GRAY)
        screen.blit(hint, (bx + (bw - hint.get_width()) // 2, by + bh - 22))

    def _bottom_bar(self, screen, messages):
        by = GAME_Y + GAME_H
        pygame.draw.rect(screen, UI_BG, (0, by, GAME_W, BOTTOM_BAR_H))
        pygame.draw.line(screen, UI_BORDER, (0, by), (GAME_W, by))

        line_h = self.font_sm.get_linesize() + 2
        max_lines = (BOTTOM_BAR_H - 10) // line_h
        recent = messages[-max_lines:]
        total  = len(recent)

        for i, (text, kind) in enumerate(recent):
            base = _MSG_COLORS.get(kind, MSG_INFO)
            col = base if i == total-1 else tuple(int(c*(0.35+0.55*(i+1)/max(total-1,1))) for c in base)
            screen.blit(self.font_sm.render(text, True, col), (8, by+6+i*line_h))

    def _label(self, screen, text, x, y, color):
        screen.blit(self.font_sm.render(text, True, color), (x, y))

    # ------------------------------------------------------------------ #
    def render_inventory(self, screen, player, sel):
        """인벤토리 화면 오버레이."""
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        screen.blit(ov, (0, 0))

        cols, rows = 5, 4
        cell = 140
        pad  = 6
        pw   = cols * cell + pad * 2
        ph   = 56 + rows * cell + pad * 2 + 60
        bx   = W // 2 - pw // 2
        by   = H // 2 - ph // 2

        pygame.draw.rect(screen, (12, 12, 26), (bx, by, pw, ph), border_radius=6)
        pygame.draw.rect(screen, (80, 80, 120), (bx, by, pw, ph), 2, border_radius=6)

        # 제목
        title = self.font_lg.render(t('inv_title'), True, GOLD_COLOR)
        screen.blit(title, (bx + (pw - title.get_width()) // 2, by + 12))
        pygame.draw.line(screen, (60, 60, 90), (bx+12, by+46), (bx+pw-12, by+46))

        # 슬롯 그리드
        gx = bx + pad
        gy = by + 56
        inv = player.inventory
        for i in range(player.max_inventory):
            col_i = i % cols
            row_i = i // cols
            sx = gx + col_i * cell
            sy = gy + row_i * cell

            is_sel = (i == sel)
            if is_sel:
                pygame.draw.rect(screen, (50, 50, 90), (sx, sy, cell-2, cell-2), border_radius=4)
                pygame.draw.rect(screen, GOLD_COLOR,   (sx, sy, cell-2, cell-2), 2, border_radius=4)
            else:
                pygame.draw.rect(screen, (20, 20, 38), (sx, sy, cell-2, cell-2), border_radius=4)
                pygame.draw.rect(screen, (45, 45, 70), (sx, sy, cell-2, cell-2), 1, border_radius=4)

            if i < len(inv):
                item = inv[i]
                # 아이콘 (색상 사각형)
                ico_size = 28
                ico_x = sx + (cell - 2 - ico_size) // 2
                ico_y = sy + 10
                pygame.draw.rect(screen, item.color, (ico_x, ico_y, ico_size, ico_size), border_radius=3)
                pygame.draw.rect(screen, tuple(max(0, c-60) for c in item.color),
                                 (ico_x, ico_y, ico_size, ico_size), 1, border_radius=3)
                # 이름 (2줄로 줄임)
                name = item.name
                if len(name) > 5:
                    lines = [name[:5], name[5:10]]
                else:
                    lines = [name]
                for li, ln in enumerate(lines):
                    ln_s = self.font_sm.render(ln, True, WHITE if is_sel else LIGHT_GRAY)
                    screen.blit(ln_s, (sx + (cell - 2 - ln_s.get_width()) // 2, ico_y + ico_size + 4 + li * 14))
                # 장착 중 표시
                for eitem in player.equipment.values():
                    if eitem is item:
                        eq_s = self.font_sm.render("E", True, GOLD_COLOR)
                        screen.blit(eq_s, (sx + cell - 2 - eq_s.get_width() - 3, sy + 3))
                        break
            else:
                empty_s = self.font_sm.render(str(i+1), True, (35, 35, 55))
                screen.blit(empty_s, (sx + (cell-2-empty_s.get_width())//2,
                                       sy + (cell-2-empty_s.get_height())//2))

        # 선택된 아이템 정보
        info_y = gy + rows * cell + pad + 4
        pygame.draw.line(screen, (50, 50, 80), (bx+12, info_y), (bx+pw-12, info_y))
        if sel < len(inv):
            item = inv[sel]
            type_map = {'weapon': '무기', 'armor': '갑옷', 'head': '투구',
                        'off_hand': '보조무기', 'accessory': '장신구',
                        'consumable': '소비', 'skillbook': '스킬북'}
            tname = type_map.get(item.item_type, item.item_type)
            info = f"{item.name}  [{tname}]"
            if item.equip_slot:
                if item.effect == 'stat_up_all':
                    info += f"  ATK+{item.value} DEF+{item.value}"
                elif item.effect == 'attack_up':
                    info += f"  ATK +{item.value}"
                elif item.effect == 'defense_up':
                    info += f"  DEF +{item.value}"
            elif item.effect == 'heal':
                info += f"  HP +{item.value}"
            info_s = self.font_sm.render(info, True, item.color)
            screen.blit(info_s, (bx + (pw - info_s.get_width()) // 2, info_y + 6))

        # 힌트
        hint_s = self.font_sm.render(t('inv_hint'), True, (80, 80, 110))
        screen.blit(hint_s, (bx + (pw - hint_s.get_width()) // 2, by + ph - 20))

    # ------------------------------------------------------------------ #
    def render_equipment(self, screen, player, sel, player_spr=None):
        """장비 장착 화면 — 페이퍼돌 레이아웃."""
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        screen.blit(ov, (0, 0))

        pw, ph = 520, 458
        bx = W // 2 - pw // 2
        by = H // 2 - ph // 2

        pygame.draw.rect(screen, (12, 12, 26), (bx, by, pw, ph), border_radius=6)
        pygame.draw.rect(screen, (80, 80, 120), (bx, by, pw, ph), 2, border_radius=6)

        title = self.font_lg.render(t('equip_title'), True, GOLD_COLOR)
        screen.blit(title, (bx + (pw - title.get_width()) // 2, by + 12))
        pygame.draw.line(screen, (60, 60, 90), (bx+12, by+46), (bx+pw-12, by+46))

        # ── 캐릭터 기준점 ───────────────────────────────────────────
        char_cx = bx + pw // 2
        char_cy = by + 218

        # ── 슬롯 정의: (key, label_key, color, (dx, dy)) ────────────
        # dx/dy: top-left of 110×54 slot box relative to char_cx/char_cy
        SW, SH = 110, 54
        SLOT_DEFS = [
            ('head',      'slot_head',      (220, 210, 140), (-SW//2, -128)),
            ('body',      'slot_body',      (130, 160, 200), (-SW//2, +48)),
            ('weapon',    'slot_weapon',    (220, 190, 100), (+76,    -SH//2)),
            ('off_hand',  'slot_off_hand',  (180, 140, 210), (-186,   -SH//2)),
            ('accessory', 'slot_accessory', (140, 210, 165), (-SW//2, +122)),
        ]

        # ── 연결선 ──────────────────────────────────────────────────
        line_col = (50, 50, 75)
        # head ↕ body
        head_bot = (char_cx, char_cy - 128 + SH)
        body_top = (char_cx, char_cy + 48)
        pygame.draw.line(screen, line_col, head_bot, (char_cx, char_cy - 44), 1)
        pygame.draw.line(screen, line_col, (char_cx, char_cy + 22), body_top, 1)
        # body ↕ accessory
        acc_top = (char_cx, char_cy + 122)
        pygame.draw.line(screen, line_col, (char_cx, char_cy + 48 + SH), acc_top, 1)
        # weapon ←→ off_hand (horizontal, through character)
        weap_left  = (char_cx + 76,          char_cy)
        ofhd_right = (char_cx - 186 + SW,    char_cy)
        pygame.draw.line(screen, line_col, ofhd_right, (char_cx - 38, char_cy), 1)
        pygame.draw.line(screen, line_col, (char_cx + 38, char_cy), weap_left,  1)

        # ── 캐릭터 그림 ─────────────────────────────────────────────
        if player_spr:
            spr = pygame.transform.scale(player_spr, (64, 64))
            screen.blit(spr, (char_cx - 32, char_cy - 44))
        else:
            fig_col = (100, 120, 160)
            pygame.draw.circle(screen, fig_col, (char_cx, char_cy - 32), 14)
            pygame.draw.rect(screen, fig_col, (char_cx - 11, char_cy - 18, 22, 32))
            pygame.draw.line(screen, fig_col, (char_cx - 11, char_cy - 10), (char_cx - 28, char_cy + 8), 3)
            pygame.draw.line(screen, fig_col, (char_cx + 11, char_cy - 10), (char_cx + 28, char_cy + 8), 3)
            pygame.draw.line(screen, fig_col, (char_cx - 7,  char_cy + 14), (char_cx - 12, char_cy + 38), 3)
            pygame.draw.line(screen, fig_col, (char_cx + 7,  char_cy + 14), (char_cx + 12, char_cy + 38), 3)

        # ── 슬롯 박스 ───────────────────────────────────────────────
        for i, (slot_key, label_key, slot_col, (dx, dy)) in enumerate(SLOT_DEFS):
            sx = char_cx + dx
            sy = char_cy + dy
            item   = player.equipment.get(slot_key)
            is_sel = (i == sel)

            bg_col = (48, 44, 82) if is_sel else (18, 18, 38)
            bd_col = GOLD_COLOR   if is_sel else slot_col
            bd_w   = 2 if is_sel else 1
            pygame.draw.rect(screen, bg_col, (sx, sy, SW, SH), border_radius=4)
            pygame.draw.rect(screen, bd_col, (sx, sy, SW, SH), bd_w, border_radius=4)

            lbl_col = GOLD_COLOR if is_sel else slot_col
            lbl_s   = self.font_sm.render(t(label_key), True, lbl_col)
            screen.blit(lbl_s, (sx + (SW - lbl_s.get_width()) // 2, sy + 4))

            if item:
                ico = 10
                pygame.draw.rect(screen, item.color, (sx + 5, sy + SH - ico - 5, ico, ico), border_radius=2)
                nm = item.name if len(item.name) <= 8 else item.name[:7] + '…'
                nm_s = self.font_sm.render(f"+{item.value} {nm}", True,
                                           WHITE if is_sel else LIGHT_GRAY)
                screen.blit(nm_s, (sx + 17, sy + SH - nm_s.get_height() - 4))
            else:
                none_s = self.font_sm.render(t('equip_none'), True, (55, 55, 80))
                screen.blit(none_s, (sx + (SW - none_s.get_width()) // 2,
                                     sy + SH - none_s.get_height() - 4))

        # ── 스탯 + 힌트 ─────────────────────────────────────────────
        sep_y = by + ph - 56
        pygame.draw.line(screen, (50, 50, 80), (bx+12, sep_y), (bx+pw-12, sep_y))
        stat_str = (f"ATK {player.total_attack}   DEF {player.total_defense}   "
                    f"SPD {player.attack_speed:.2f}   EVA {player.evasion}%")
        stat_s = self.font_sm.render(stat_str, True, (130, 130, 160))
        screen.blit(stat_s, (bx + (pw - stat_s.get_width()) // 2, sep_y + 6))

        hint_s = self.font_sm.render(t('equip_hint'), True, (80, 80, 110))
        screen.blit(hint_s, (bx + (pw - hint_s.get_width()) // 2, by + ph - 22))


# ---- helpers ----
def _bar(screen, x, y, w, h, cur, maximum, fg, bg):
    pygame.draw.rect(screen, bg, (x, y, w, h))
    if maximum > 0:
        fill = max(0, int(w * cur / maximum))
        if fill:
            pygame.draw.rect(screen, fg, (x, y, fill, h))
    pygame.draw.rect(screen, UI_BORDER, (x, y, w, h), 1)

def _fmt_skill_stats(key, stats):
    cd = stats['cd_ms'] / 1000
    if key == 'W':
        return f"{stats['tiles']}칸 전진  CD {cd:.1f}s"
    if key == 'A':
        return f"반경 {stats['radius']}  공격력 {int(stats['mul']*100)}%  CD {cd:.1f}s"
    if key == 'S':
        return f"HP +{int(stats['heal_pct']*100)}%  CD {cd:.1f}s"
    if key == 'D':
        return f"{stats['mul']:.1f}배 강타  치명 {int(stats['crit']*100)}%  CD {cd:.1f}s"
    return ""

def _cx(surf, container_w):
    return (container_w - surf.get_width()) // 2

def _midy(surf, container_h):
    return (container_h - surf.get_height()) // 2

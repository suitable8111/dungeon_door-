import os
import math
import pygame
from core.constants import *
from core.skills import SKILL_DEFS
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

_KO_FONT_PATHS = [
    '/System/Library/Fonts/AppleSDGothicNeo.ttc',
    '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
    'C:/Windows/Fonts/malgun.ttf',
    '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
]


def _load_ko_font(size, bold=False):
    for path in _KO_FONT_PATHS:
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

    # ------------------------------------------------------------------ #
    def render(self, screen, player, messages, floor_num,
               dungeon=None, skill_mgr=None):
        self._top_bar(screen, player, floor_num)
        self._right_panel(screen, player, dungeon, skill_mgr)
        self._bottom_bar(screen, messages)

    # ------------------------------------------------------------------ #
    def render_game_over(self, screen, floor_num, records=None):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        title = self.font_xl.render(t('gameover'), True, MSG_BAD)
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
                    page='main', settings=None, settings_sel=0):
        """메인 메뉴 렌더링. 버튼 (pygame.Rect, action_str) 목록을 반환."""
        import random
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        cx = W // 2
        settings = settings or {}

        # ── 공통 배경 ────────────────────────────────────────────────
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
        pygame.draw.rect(screen, (62, 58, 92), (p_x,   p_y,   p_w,   p_h  ), 2)
        pygame.draw.rect(screen, (28, 26, 48), (p_x+3, p_y+3, p_w-6, p_h-6), 1)

        buttons = []

        # ════════════════════════════════════════════════════════════
        if page == 'main':
        # ════════════════════════════════════════════════════════════

            # ── 타이틀 ─────────────────────────────────────────────
            pygame.draw.rect(screen, (12, 10, 28), (p_x, p_y, p_w, 74))
            pygame.draw.line(screen, (70, 65, 100),
                             (p_x+20, p_y+74), (p_x+p_w-20, p_y+74))
            t1 = self.font_xl.render("DUNGEON", True, GOLD_COLOR)
            t2 = self.font_xl.render("DOOR",    True, (255, 235, 120))
            tw = t1.get_width() + 14 + t2.get_width()
            tx = cx - tw // 2
            screen.blit(t1, (tx, p_y + 14))
            screen.blit(t2, (tx + t1.get_width() + 14, p_y + 14))

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
    def _top_bar(self, screen, player, floor_num):
        pygame.draw.rect(screen, (10, 10, 20), (0, 0, WINDOW_WIDTH, TOP_BAR_H))
        # 하단 경계선 두 줄 (입체감)
        pygame.draw.line(screen, (50, 50, 80), (0, TOP_BAR_H - 2), (WINDOW_WIDTH, TOP_BAR_H - 2))
        pygame.draw.line(screen, (25, 25, 45), (0, TOP_BAR_H - 1), (WINDOW_WIDTH, TOP_BAR_H - 1))

        # ── 왼쪽: 층 표시 ──
        fl = self.font_md.render(f"B{floor_num}F", True, (180, 180, 220))
        screen.blit(fl, (12, _midy(fl, TOP_BAR_H)))

        sep_x = 12 + fl.get_width() + 8
        pygame.draw.line(screen, (50, 50, 75), (sep_x, 6), (sep_x, TOP_BAR_H - 6))

        # ── 중앙: 골드 + HP 인디케이터 ──
        gx = sep_x + 12
        gold_label = self.font_sm.render("G", True, GOLD_COLOR)
        gold_val   = self.font_md.render(str(player.gold), True, GOLD_COLOR)
        screen.blit(gold_label, (gx, _midy(gold_label, TOP_BAR_H) + 1))
        screen.blit(gold_val,   (gx + gold_label.get_width() + 3, _midy(gold_val, TOP_BAR_H)))

        # HP 미니바 (중앙 근처)
        hp_bx = gx + gold_label.get_width() + gold_val.get_width() + 20
        hp_bw = 120; hp_bh = 8
        hp_by = (TOP_BAR_H - hp_bh) // 2
        ratio = max(0.0, player.hp / player.max_hp)
        pygame.draw.rect(screen, (55, 18, 18), (hp_bx, hp_by, hp_bw, hp_bh))
        if ratio > 0:
            bar_col = (int(200 + 55*(1-ratio)), int(210*ratio), 40)
            pygame.draw.rect(screen, bar_col, (hp_bx, hp_by, max(1, int(hp_bw*ratio)), hp_bh))
        pygame.draw.rect(screen, (80, 30, 30), (hp_bx, hp_by, hp_bw, hp_bh), 1)
        hp_txt = self.font_sm.render(f"{player.hp}/{player.max_hp}", True, LIGHT_GRAY)
        screen.blit(hp_txt, (hp_bx + hp_bw + 6, _midy(hp_txt, TOP_BAR_H) + 1))

        # ── 오른쪽: 레벨 ──
        lv = self.font_md.render(f"Lv.{player.level}", True, XP_COLOR)
        screen.blit(lv, (GAME_W + (RIGHT_PANEL_W - lv.get_width()) // 2, _midy(lv, TOP_BAR_H)))

    def _right_panel(self, screen, player, dungeon, skill_mgr):
        rx = GAME_W
        pw = RIGHT_PANEL_W
        bw = pw - 16

        pygame.draw.rect(screen, (10, 10, 20), (rx, 0, pw, WINDOW_HEIGHT))
        pygame.draw.line(screen, (50, 50, 80), (rx, 0), (rx, WINDOW_HEIGHT))
        pygame.draw.line(screen, (25, 25, 45), (rx+1, 0), (rx+1, WINDOW_HEIGHT))

        y = TOP_BAR_H + 8

        # ── 섹션 헤더 유틸 ──────────────────────────────────────────
        def sec_header(key, col):
            nonlocal y
            pygame.draw.rect(screen, (22, 22, 42), (rx, y, pw, 20))
            pygame.draw.line(screen, (55, 55, 85), (rx, y+20), (rx+pw, y+20))
            screen.blit(self.font_sm.render(t(key), True, col), (rx+8, y+3))
            y += 24

        # ── HP ──────────────────────────────────────────────────────
        sec_header('sec_hp', HP_COLOR)
        _bar(screen, rx+8, y, bw, 13, player.hp, player.max_hp, HP_COLOR, HP_BG)
        hp_txt = self.font_sm.render(f"{player.hp} / {player.max_hp}", True, (200, 200, 200))
        screen.blit(hp_txt, (rx + pw - hp_txt.get_width() - 8, y + 1))
        y += 18

        # XP
        _bar(screen, rx+8, y, bw, 6, player.xp, player.xp_next, XP_COLOR, XP_BG)
        xp_txt = self.font_sm.render(f"XP {player.xp}/{player.xp_next}", True, (80, 140, 200))
        screen.blit(xp_txt, (rx+8, y+8)); y += 20

        # ── 스탯 ────────────────────────────────────────────────────
        sec_header('sec_stats', LIGHT_GRAY)
        stats = [('ATK', str(player.attack), WHITE),
                 ('DEF', str(player.defense), (130, 180, 255)),
                 ('GOLD', f"{player.gold} G", GOLD_COLOR)]
        for label, val, col in stats:
            lbl_s = self.font_sm.render(label, True, (100, 100, 130))
            val_s = self.font_sm.render(val, True, col)
            screen.blit(lbl_s, (rx+8, y))
            screen.blit(val_s, (rx + pw - val_s.get_width() - 8, y))
            y += 18
        y += 4

        # ── 인벤토리 ─────────────────────────────────────────────────
        sec_header('sec_inv', LIGHT_GRAY)
        for i in range(player.max_inventory):
            if i < len(player.inventory):
                item = player.inventory[i]
                nm = item.name if len(item.name) <= 9 else item.name[:8] + '…'
                slot_col = item.color
                # 슬롯 배경 (소지 중)
                pygame.draw.rect(screen, (20, 22, 38), (rx+6, y-1, pw-12, 18))
                txt = self.font_sm.render(f"[{i+1}] {nm}", True, slot_col)
            else:
                txt = self.font_sm.render(f"[{i+1}] ---", True, (40, 40, 60))
            screen.blit(txt, (rx+8, y)); y += 19
        y += 4

        # ── 스킬 ────────────────────────────────────────────────────
        sec_header('sec_skills', LIGHT_GRAY)
        _SKILL_TRANS = {
            'Q': ('skill_q_name', 'skill_q_desc'),
            'E': ('skill_e_name', 'skill_e_desc'),
            'F': ('skill_f_name', 'skill_f_desc'),
        }
        for sdef in SKILL_DEFS:
            sk    = sdef['key']
            ready = skill_mgr.ready(sk) if skill_mgr else True
            frac  = skill_mgr.cooldown_frac(sk) if skill_mgr else 0.0
            rem   = skill_mgr.remaining_sec(sk) if skill_mgr else 0.0
            nc    = sdef['color'] if ready else (60, 60, 80)
            nk, dk = _SKILL_TRANS.get(sk, ('', ''))
            label = f"[{sk}] {t(nk)}" if nk else f"[{sk}] {sdef['name']}"

            if ready:
                pygame.draw.rect(screen, (20, 28, 50), (rx+6, y-1, pw-12, 28))
            name_s = self.font_sm.render(label, True, nc)
            screen.blit(name_s, (rx+8, y))
            if not ready:
                rem_s = self.font_sm.render(f"{rem:.1f}s", True, (90, 90, 110))
                screen.blit(rem_s, (rx + pw - rem_s.get_width() - 8, y))
            y += 15
            _bar(screen, rx+8, y, bw, 6, int(bw*(1-frac)), bw,
                 sdef['color'] if ready else (40, 40, 65), (18, 18, 35))
            y += 10
        y += 4

        # ── 조작법 ──────────────────────────────────────────────────
        sec_header('sec_controls', (70, 70, 100))
        hints = [
            (t('ctrl_move'),  t('ctrl_move_d')),
            (t('ctrl_atk'),   t('ctrl_atk_d')),
            (t('ctrl_skill'), t('ctrl_skill_d')),
            (t('ctrl_item'),  t('ctrl_item_d')),
            (t('ctrl_esc'),   t('ctrl_esc_d')),
        ]
        for key, desc in hints:
            k_s = self.font_sm.render(key, True, (120, 140, 180))
            d_s = self.font_sm.render(desc, True, (70, 70, 95))
            screen.blit(k_s, (rx+8, y))
            screen.blit(d_s, (rx + pw - d_s.get_width() - 8, y))
            y += 16
        y += 4

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
                    col = (30,30,42) if tt == TileType.WALL else (40,40,55)
                else:
                    if tt == TileType.WALL:        col = (60,60,80)
                    elif tt == TileType.STAIRS_DOWN: col = STAIRS_LIT
                    elif tt == TileType.SHOP:        col = SHOP_COLOR
                    else:                            col = (75,75,100)
                pygame.draw.rect(screen, col, (ox+mx*scale, oy+my*scale, scale, scale))

        for enemy in dungeon.enemies:
            if enemy.is_alive() and dungeon.tiles[enemy.y][enemy.x].visible:
                ec = BOSS_COLOR if enemy.is_boss else (220,60,60)
                pygame.draw.rect(screen, ec, (ox+enemy.x*scale, oy+enemy.y*scale, scale, scale))

        pygame.draw.rect(screen, WHITE, (ox+player.x*scale-1, oy+player.y*scale-1, scale+1, scale+1))
        pygame.draw.rect(screen, UI_BORDER, (ox, oy, dungeon.width*scale, dungeon.height*scale), 1)

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


# ---- helpers ----
def _bar(screen, x, y, w, h, cur, maximum, fg, bg):
    pygame.draw.rect(screen, bg, (x, y, w, h))
    if maximum > 0:
        fill = max(0, int(w * cur / maximum))
        if fill:
            pygame.draw.rect(screen, fg, (x, y, fill, h))
    pygame.draw.rect(screen, UI_BORDER, (x, y, w, h), 1)

def _cx(surf, container_w):
    return (container_w - surf.get_width()) // 2

def _midy(surf, container_h):
    return (container_h - surf.get_height()) // 2

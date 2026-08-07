import os
import sys
import math
import pygame
from core.constants import *
from core.skills import (SKILL_DEFS, SKILL_XP_REQ, SKILL_MAX_LEVEL,
                         COMBO_SKILL_DEFS, ULTIMATE_SKILL_DEFS, SKILL_UPGRADES)
try:
    from core.skills import ALL_SKILL_DEFS, DEFAULT_EQUIPPED
except ImportError:
    ALL_SKILL_DEFS = {}
    DEFAULT_EQUIPPED = {'W': 'flash_dash', 'A': 'steel_whirl', 'S': 'regen_breath', 'D': 'judgment'}
from core.lang import t, LANG_NAMES
from map.tile import TileType
from entities.avatar import (avatar_surface, SKIN_TONES, HAIR_STYLES,
                             HAIR_COLORS, cycle as _appearance_cycle)
from entities.item_icons import draw_mc_item

# 아이템 아이콘을 마인크래프트 블록 스타일로 (False면 단색 스와치)
USE_MC_ITEMS = True

# 픽셀 폰트가 못 그리는 글리프(이모지 등 → ≡ 두부)를 제거한다.
# 폰트는 미지원 글자를 .notdef(두부)로 그리므로 metrics로는 판별 불가 →
# 각 글자 비트맵을 '확실히 미지원인 글자'의 비트맵과 비교해 두부면 제거.
_RENDERABLE_CACHE: dict = {}
_TOFU_REF: dict = {}


def _tofu_bytes(font):
    fid = id(font)
    if fid not in _TOFU_REF:
        ref = font.render('\U000F0000', True, (255, 255, 255))   # PUA — 미지원
        _TOFU_REF[fid] = (ref.get_size(), pygame.image.tobytes(ref, 'RGBA'))
    return _TOFU_REF[fid]


def _renderable(font, text):
    key = (id(font), text)
    cached = _RENDERABLE_CACHE.get(key)
    if cached is not None:
        return cached
    tsz, tbytes = _tofu_bytes(font)
    out = []
    for ch in text:
        if ch in ' \t' or ch.isalnum() or ord(ch) < 0x2000:
            out.append(ch); continue          # 일반 문자/한글은 그대로
        try:
            g = font.render(ch, True, (255, 255, 255))
            is_tofu = (g.get_size() == tsz and
                       pygame.image.tobytes(g, 'RGBA') == tbytes)
        except Exception:
            is_tofu = False
        if not is_tofu:
            out.append(ch)
    res = ''.join(out).lstrip()
    if len(_RENDERABLE_CACHE) > 512:
        _RENDERABLE_CACHE.clear()
    _RENDERABLE_CACHE[key] = res
    return res


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


def _draw_network_icon(surf, cx, cy, col):
    """두 노드를 잇는 링크 — 멀티플레이(P2P) 아이콘."""
    # 좌하·우상 두 피어 + 연결선
    a = (cx - 6, cy + 5)
    b = (cx + 6, cy - 5)
    pygame.draw.line(surf, col, a, b, 2)
    pygame.draw.circle(surf, col, a, 4)
    pygame.draw.circle(surf, col, b, 4)
    pygame.draw.circle(surf, (0, 0, 0), a, 2)
    pygame.draw.circle(surf, (0, 0, 0), b, 2)


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

def _assets_root():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

from core.fonts import load_font as _load_ui_font

# 하위 호환 별칭 — 언어별 폰트는 core/fonts.py에서 처리
def _load_ko_font(size, bold=False):
    return _load_ui_font(size, bold)


class HUD:
    def __init__(self):
        pygame.font.init()
        self.reload_fonts()

        # PressStart2P 픽셀 폰트 (ASCII 전용)
        _base = os.path.join(_assets_root(), 'assets')
        self._init_static_assets(_base)

    def reload_fonts(self):
        """언어 변경 후 호출 — 현재 언어에 맞는 폰트로 재생성."""
        self.font_sm = _load_ui_font(13)
        self.font_md = _load_ui_font(15)
        self.font_lg = _load_ui_font(30)
        self.font_xl = _load_ui_font(46)

    def _init_static_assets(self, _base):
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
               is_test_mode=False,
               equipped_skills=None, minimap_npcs=None):
        self._mm_npcs = minimap_npcs        # 미니맵 NPC 표시(마을)
        self._top_bar(screen, player, floor_num, is_test_mode=is_test_mode)
        self._right_panel(screen, player, dungeon, skill_mgr,
                          unlocked_combos or set(), skill_books or set(),
                          skill_levels or {}, skill_xp or {},
                          equipped_skills=equipped_skills)
        self._bottom_bar(screen, messages)

    # ------------------------------------------------------------------ #
    def _credits_lines(self):
        """엔딩 크레딧 라인 — (text, font, color, 위쪽 여백)."""
        big = self.font_pixel_title or self.font_lg
        return [
            ('DUNGEON DOOR', big, GOLD_COLOR, 60),
            (t('credits_end'), self.font_lg, (235, 235, 245), 26),
            ('', None, None, 60),
            (t('credits_to_conqueror'), self.font_md, (180, 210, 255), 0),
            ('★ ' + t('title_abyss_sovereign') + ' ★', self.font_lg, (255, 222, 105), 14),
            ('', None, None, 70),
            (t('credits_staff'), self.font_md, (150, 150, 195), 0),
            (t('credits_role'), self.font_sm, (215, 215, 228), 8),
            ('', None, None, 70),
            (t('credits_thanks'), self.font_md, (255, 220, 150), 0),
            ('', None, None, 50),
            (t('credits_abyss_open'), self.font_md, (195, 120, 245), 0),
            (t('credits_return_town'), self.font_sm, (170, 170, 195), 8),
            ('', None, None, 90),
            (t('credits_skip'), self.font_sm, (95, 92, 125), 0),
        ]

    def credits_height(self):
        return getattr(self, '_credits_total_h', 2200)

    def render_credits(self, screen, scroll, records=None):
        """엔딩 스태프롤 — 아래에서 위로 스크롤."""
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        screen.fill((5, 4, 12))
        import random as _rnd
        rng = _rnd.Random(3)
        for _ in range(120):
            sx, sy = rng.randint(0, W), rng.randint(0, H)
            b = rng.randint(35, 120)
            screen.set_at((sx, sy), (b, b, min(255, b + 25)))
        y = H - int(scroll)
        total = 0
        for text, font, col, gap in self._credits_lines():
            y += gap; total += gap
            if text and font:
                surf = font.render(text, True, col)
                if -40 < y < H + 40:
                    screen.blit(surf, (W // 2 - surf.get_width() // 2, y))
                lh = surf.get_height() + 14
            else:
                lh = 18
            y += lh; total += lh
        self._credits_total_h = total + H

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
    def render_menu(self, screen, cards, sel=0, mouse_pos=(0, 0),
                    page='main', settings=None, settings_sel=0,
                    mp_ip=None, mp_status=None, mp_banner=None, mp_code=None,
                    mp_upnp=None):
        """메인 메뉴 — 세이브 카드(캐릭터) 목록. 버튼 (rect, action) 반환."""
        import random
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        cx = W // 2
        settings = settings or {}
        cards = cards or []

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
            p_w = 470
            p_h = 82 + len(cards) * 62 + 16 + 54 + 50 + 52
            if mp_banner == 'host' and mp_code:
                p_h += 52    # 초대 코드 2줄 + UPnP 상태 표시 공간
        elif page == 'multiplayer':
            p_w = 440
            p_h = 336
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

            # ── 세이브 카드 (슬롯별 캐릭터) ───────────────────────
            _CLASS_COL = {'warrior': (235, 185, 60), 'archer': (120, 205, 150), 'mage': (170, 130, 245), 'axeman': (222, 120, 58)}
            bw = p_w - 44; bh = 54
            bx = p_x + 22
            by0 = p_y + 88
            for i, card in enumerate(cards):
                by   = by0 + i * 62
                rect = pygame.Rect(bx, by, bw, bh)
                act  = (i == sel)
                hov  = rect.collidepoint(mouse_pos)
                bg_c, bd_c, tc = _btn_colors(act, hov)
                pygame.draw.rect(screen, bg_c, rect, border_radius=5)
                pygame.draw.rect(screen, bd_c, rect, 2 if act else 1, border_radius=5)
                if act:
                    arr = self.font_md.render("▶", True, GOLD_COLOR)
                    screen.blit(arr, (rect.left+8, rect.centery - arr.get_height()//2))
                if card.get('exists'):
                    ccol = _CLASS_COL.get(card['char_class'], (200, 200, 210))
                    # 캐릭터 미니 아바타 (피부/헤어 반영)
                    av = avatar_surface(bh - 6, card.get('appearance'),
                                        card['char_class'], scale=2)
                    screen.blit(av, (rect.left + 26, rect.centery - (bh - 6) // 2))
                    nm = self.font_lg.render(card['name'][:12], True, tc)
                    screen.blit(nm, (rect.left + 70, rect.top + 6))
                    sub = self.font_sm.render(
                        f"{t('class_'+card['char_class'])}  ·  "
                        f"{t('card_floor_lv', card['floor'], card['level'])}",
                        True, ccol)
                    screen.blit(sub, (rect.left + 70, rect.top + 30))
                    buttons.append((rect, f"slot:{card['slot']}"))
                    # 삭제 버튼 (우측 X)
                    dr = pygame.Rect(rect.right - 30, rect.centery - 10, 20, 20)
                    _draw_x_icon(screen, dr.centerx, dr.centery, (150, 70, 70))
                    buttons.append((dr, f"del:{card['slot']}"))
                else:
                    ns = self.font_lg.render(t('card_new'), True,
                                             (120, 200, 130) if act or hov else (90, 130, 95))
                    screen.blit(ns, (rect.centerx - ns.get_width()//2,
                                     rect.centery - ns.get_height()//2))
                    buttons.append((rect, f"slot:{card['slot']}"))

            # ── 구분선 ─────────────────────────────────────────────
            sep_y = by0 + len(cards) * 62 + 2
            pygame.draw.line(screen, (44, 42, 66),
                             (p_x+30, sep_y), (p_x+p_w-30, sep_y))

            # ── 멀티플레이 (beta) 버튼 (전체 폭) ───────────────────
            mp_idx = len(cards)
            mp_h = 46
            mp_rect = pygame.Rect(p_x + 20, sep_y + 12, p_w - 40, mp_h)
            mp_act  = (mp_idx == sel)
            mp_hov  = mp_rect.collidepoint(mouse_pos)
            # 베타 강조: 파란빛 액센트 + 부드러운 발광 테두리
            mp_bg = (26, 34, 58) if (mp_act or mp_hov) else (18, 24, 42)
            mp_bd = (90, 150, 235) if (mp_act or mp_hov) else (58, 92, 150)
            mp_tc = (200, 224, 255) if (mp_act or mp_hov) else (150, 180, 224)
            pygame.draw.rect(screen, mp_bg, mp_rect, border_radius=5)
            pygame.draw.rect(screen, mp_bd, mp_rect, 2 if mp_act else 1, border_radius=5)
            _draw_network_icon(screen, mp_rect.left + 22, mp_rect.centery, mp_tc)
            mlbl = self.font_md.render(t('menu_multiplayer'), True, mp_tc)
            screen.blit(mlbl, (mp_rect.left + 42,
                               mp_rect.centery - mlbl.get_height() // 2))
            buttons.append((mp_rect, 'multiplayer'))

            # ── 설정 / 종료 버튼 (나란히, 작은 크기) ───────────────
            sm_h = 44
            sm_w = (p_w - 60) // 2
            sm_y = mp_rect.bottom + 12
            s_idx = len(cards) + 1;     q_idx = len(cards) + 2

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
            if mp_banner == 'host' and mp_code:
                # 호스트: 초대 코드를 크게 보여줘 친구에게 공유하게 한다
                lbl = self.font_sm.render(t('menu_mp_your_code'), True, (150, 200, 250))
                screen.blit(lbl, (cx - lbl.get_width()//2, fy - 10))
                cf = self.font_pixel_go or self.font_md
                cv = cf.render(mp_code, True, (255, 226, 120))
                screen.blit(cv, (cx - cv.get_width()//2, fy + 6))
                # UPnP 상태 (인터넷 개방 여부)
                _uk = {'wait': ('menu_mp_upnp_wait', (170, 170, 120)),
                       'ok':   ('menu_mp_upnp_ok',   (130, 220, 150)),
                       'lan':  ('menu_mp_upnp_lan',  (200, 160, 120))}.get(mp_upnp)
                if _uk:
                    us = self.font_sm.render(t(_uk[0]), True, _uk[1])
                    screen.blit(us, (cx - us.get_width()//2, fy + 26))
            elif mp_banner:
                hint = self.font_sm.render(t('menu_mp_pick'), True, (150, 200, 250))
                screen.blit(hint, (cx - hint.get_width()//2, fy))
            else:
                hint = self.font_sm.render(t('menu_hint'), True, (60, 58, 90))
                screen.blit(hint, (cx - hint.get_width()//2, fy))
            # 테두리를 마지막에 그려 내용에 가리지 않게
            pygame.draw.rect(screen, (62, 58, 92), (p_x,   p_y,   p_w,   p_h  ), 2)
            pygame.draw.rect(screen, (38, 34, 62), (p_x+3, p_y+3, p_w-6, p_h-6), 1)

        # ════════════════════════════════════════════════════════════
        elif page == 'multiplayer':
        # ════════════════════════════════════════════════════════════

            # ── 타이틀 ─────────────────────────────────────────────
            pygame.draw.rect(screen, (12, 14, 30), (p_x, p_y, p_w, 54))
            pygame.draw.line(screen, (70, 110, 160),
                             (p_x+20, p_y+54), (p_x+p_w-20, p_y+54))
            _draw_network_icon(screen, p_x + 34, p_y + 27, (150, 190, 245))
            ts = self.font_lg.render(t('menu_multiplayer'), True, (190, 218, 255))
            screen.blit(ts, (p_x + 54, p_y + 27 - ts.get_height()//2))

            # ── 안내 문구 ──────────────────────────────────────────
            notice = self.font_sm.render(t('menu_mp_notice'), True, (150, 165, 200))
            screen.blit(notice, (cx - notice.get_width()//2, p_y + 64))

            mb_w = p_w - 40
            mb_x = p_x + 20

            # ── 호스트 IP 입력 필드 (참가용) ───────────────────────
            ip_lbl = self.font_sm.render(t('menu_mp_ip'), True, (150, 170, 205))
            screen.blit(ip_lbl, (mb_x, p_y + 90))
            ip_box = pygame.Rect(mb_x + 90, p_y + 86, mb_w - 90, 28)
            pygame.draw.rect(screen, (10, 14, 26), ip_box, border_radius=4)
            pygame.draw.rect(screen, (70, 104, 160), ip_box, 1, border_radius=4)
            ipv = self.font_sm.render((mp_ip or ''), True, (215, 230, 250))
            screen.blit(ipv, (ip_box.left + 8, ip_box.centery - ipv.get_height()//2))
            iphint = self.font_sm.render(t('menu_mp_ip_hint'), True, (92, 108, 140))
            screen.blit(iphint, (mb_x, p_y + 118))

            # ── 방 만들기 / 친구 참가 ──────────────────────────────
            mb_h = 46
            for i, (act_tag, lbl_key) in enumerate([
                ('mp_host', 'menu_mp_host'),
                ('mp_join', 'menu_mp_join'),
            ]):
                by   = p_y + 140 + i * 52
                rect = pygame.Rect(mb_x, by, mb_w, mb_h)
                act  = (i == settings_sel)
                hov  = rect.collidepoint(mouse_pos)
                bg_c = (24, 32, 54) if (act or hov) else (16, 22, 38)
                bd_c = (88, 148, 230) if (act or hov) else (54, 86, 140)
                tc   = (200, 224, 255) if (act or hov) else (140, 170, 214)
                pygame.draw.rect(screen, bg_c, rect, border_radius=5)
                pygame.draw.rect(screen, bd_c, rect, 2 if act else 1, border_radius=5)
                lbl = self.font_md.render(t(lbl_key), True, tc)
                screen.blit(lbl, (rect.left + 20,
                                  rect.centery - lbl.get_height()//2))
                buttons.append((rect, act_tag))

            # ── 상태 문구 (연결 중 / 실패) ─────────────────────────
            if mp_status:
                stc = (255, 150, 120) if ('실패' in mp_status or 'fail' in mp_status.lower()
                                          or 'сбой' in mp_status.lower()) else (150, 210, 160)
                st = self.font_sm.render(mp_status, True, stc)
                screen.blit(st, (cx - st.get_width()//2, p_y + 246))

            # ── 뒤로 ───────────────────────────────────────────────
            back_rect = pygame.Rect(mb_x, p_y + 270, mb_w, 40)
            act  = (settings_sel == 2)
            hov  = back_rect.collidepoint(mouse_pos)
            bg_c, bd_c, tc = _btn_colors(act, hov)
            pygame.draw.rect(screen, bg_c, back_rect, border_radius=4)
            pygame.draw.rect(screen, bd_c, back_rect, 1, border_radius=4)
            bl = self.font_md.render(t('menu_back'), True, tc)
            screen.blit(bl, (back_rect.centerx - bl.get_width()//2,
                             back_rect.centery - bl.get_height()//2))
            buttons.append((back_rect, 'mp_back'))

            pygame.draw.rect(screen, (62, 78, 112), (p_x,   p_y,   p_w,   p_h  ), 2)
            pygame.draw.rect(screen, (38, 48, 72), (p_x+3, p_y+3, p_w-6, p_h-6), 1)

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
            lang_val = LANG_NAMES.get(settings.get('language', 'en'), 'English')
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

        return buttons

    # ------------------------------------------------------------------ #
    def _draw_class_icon(self, screen, cx, cy, char_class, col):
        """직업 미니 아이콘 — 전사=검, 궁수=활, 마법사=지팡이+오브."""
        if char_class == 'archer':
            pygame.draw.arc(screen, col, (cx - 6, cy - 9, 10, 18), -1.2, 1.2, 2)
            pygame.draw.line(screen, (220, 220, 225), (cx - 5, cy - 8), (cx - 5, cy + 8), 1)
            pygame.draw.line(screen, (200, 180, 130), (cx - 5, cy), (cx + 8, cy), 2)
        elif char_class == 'mage':
            # 지팡이(대각) + 빛나는 오브
            pygame.draw.line(screen, (150, 120, 80), (cx - 7, cy + 8), (cx + 4, cy - 6), 2)
            pygame.draw.circle(screen, col, (cx + 5, cy - 7), 4)
            pygame.draw.circle(screen, (235, 220, 255), (cx + 5, cy - 7), 2)
        elif char_class == 'axeman':
            # 양손도끼 — 긴 자루 + 넓은 도끼날
            pygame.draw.line(screen, (150, 110, 70), (cx - 6, cy + 9), (cx + 5, cy - 8), 2)
            pygame.draw.polygon(screen, col, [(cx + 3, cy - 9), (cx + 9, cy - 7),
                                              (cx + 8, cy - 1), (cx + 2, cy - 3)])
            pygame.draw.polygon(screen, (235, 235, 240), [(cx + 3, cy - 9), (cx + 6, cy - 8),
                                                          (cx + 5, cy - 4), (cx + 2, cy - 3)])
        else:
            pygame.draw.line(screen, (200, 205, 220), (cx - 6, cy + 6), (cx + 5, cy - 6), 3)
            pygame.draw.line(screen, col, (cx - 8, cy - 5), (cx - 3, cy - 8), 2)  # 가드

    def _draw_selector_row(self, screen, x, y, w, label, value_surf, sel,
                           row_idx, mouse_pos, buttons, swatch=None):
        """라벨 + [◀ 값 ▶] 셀렉터 한 줄. prev/next 클릭 rect를 buttons에 추가."""
        act = (sel == row_idx)
        lbl = self.font_sm.render(label, True, (150, 150, 170))
        screen.blit(lbl, (x, y - 15))
        box = pygame.Rect(x, y, w, 38)
        bg = (30, 28, 52) if act else (18, 16, 32)
        bd = GOLD_COLOR if act else (66, 62, 96)
        pygame.draw.rect(screen, bg, box, border_radius=5)
        pygame.draw.rect(screen, bd, box, 2 if act else 1, border_radius=5)
        # 화살표(삼각형 직접 그리기 — 픽셀 폰트에 ◀▶ 글리프 없음)
        acol = GOLD_COLOR if act else (150, 150, 175)
        cyv = box.centery
        pygame.draw.polygon(screen, acol, [(box.left + 18, cyv - 7),
                                           (box.left + 18, cyv + 7),
                                           (box.left + 9,  cyv)])
        pygame.draw.polygon(screen, acol, [(box.right - 18, cyv - 7),
                                           (box.right - 18, cyv + 7),
                                           (box.right - 9,  cyv)])
        # 값: 색 스와치 또는 텍스트
        if swatch is not None:
            sw = pygame.Rect(box.centerx - 30, box.centery - 9, 60, 18)
            pygame.draw.rect(screen, swatch, sw, border_radius=3)
            pygame.draw.rect(screen, (10, 10, 20), sw, 1, border_radius=3)
        if value_surf is not None:
            screen.blit(value_surf, (box.centerx - value_surf.get_width() // 2,
                                     box.centery - value_surf.get_height() // 2))
        buttons.append((pygame.Rect(box.left, box.top, 34, 38), f'row_prev:{row_idx}'))
        buttons.append((pygame.Rect(box.right - 34, box.top, 34, 38), f'row_next:{row_idx}'))

    def render_char_create(self, screen, char_class, name, sel, mouse_pos=(0, 0),
                           appearance=None, locked=False):
        """캐릭터 생성 화면 — 좌: 아바타 프리뷰 / 우: 직업·외형·이름 셀렉터.

        locked=True 면 선택된 직업이 미해금 상태 → 자물쇠·요구조건 표시 + 생성 차단.
        """
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        cx = W // 2
        screen.fill((7, 7, 16))
        pw, ph = 620, 496
        px, py = cx - pw // 2, H // 2 - ph // 2
        pygame.draw.rect(screen, (10, 10, 26), (px, py, pw, ph), border_radius=8)
        pygame.draw.rect(screen, (70, 66, 105), (px, py, pw, ph), 2, border_radius=8)
        title = self.font_lg.render(t('char_create_title'), True, GOLD_COLOR)
        screen.blit(title, (cx - title.get_width() // 2, py + 20))
        pygame.draw.line(screen, (50, 48, 78),
                         (px + 24, py + 56), (px + pw - 24, py + 56))

        buttons = []
        _CC = {'warrior': (235, 185, 60), 'archer': (120, 205, 150),
               'mage': (170, 130, 245), 'axeman': (222, 120, 58)}
        ccol = (108, 108, 128) if locked else _CC.get(char_class, (235, 185, 60))

        # ── 좌측: 아바타 프리뷰 박스 ──────────────────────────────────
        prev_w, prev_h = 236, 320
        prev_x, prev_y = px + 26, py + 78
        pygame.draw.rect(screen, (16, 16, 30), (prev_x, prev_y, prev_w, prev_h),
                         border_radius=6)
        pygame.draw.rect(screen, ccol, (prev_x, prev_y, prev_w, prev_h), 2,
                         border_radius=6)
        # 바닥 원형 그림자
        pygame.draw.ellipse(screen, (6, 6, 14),
                            (prev_x + 58, prev_y + prev_h - 54, 120, 26))
        av = avatar_surface(230, appearance, char_class, scale=11)
        screen.blit(av, (prev_x + prev_w // 2 - 115, prev_y + 20))
        cls_name = self.font_lg.render(t('class_' + char_class), True, ccol)
        screen.blit(cls_name, (prev_x + prev_w // 2 - cls_name.get_width() // 2,
                               prev_y + prev_h - 34))

        # 미해금 직업: 자물쇠 + 요구조건 오버레이
        if locked:
            ov = pygame.Surface((prev_w, prev_h), pygame.SRCALPHA)
            ov.fill((6, 6, 14, 175))
            screen.blit(ov, (prev_x, prev_y))
            lx, ly = prev_x + prev_w // 2, prev_y + prev_h // 2 - 26
            pygame.draw.rect(screen, (210, 210, 225), (lx - 14, ly, 28, 22), border_radius=3)
            pygame.draw.arc(screen, (210, 210, 225), (lx - 10, ly - 17, 20, 28),
                            3.14, 6.28, 3)
            pygame.draw.rect(screen, (55, 55, 75), (lx - 3, ly + 7, 6, 9))
            req_key = 'class_axeman_locked_req' if char_class == 'axeman' else 'class_locked_req'
            req = self._fit_text(self.font_sm, t(req_key), prev_w - 18,
                                 (255, 210, 120))
            screen.blit(req, (prev_x + prev_w // 2 - req.get_width() // 2, ly + 40))

        # ── 우측: 셀렉터 열 ───────────────────────────────────────────
        rx = px + 300
        rw = pw - (rx - px) - 34
        y = py + 94
        gap = 60

        # row 0: 직업
        cv = self.font_md.render(t('class_' + char_class), True, ccol)
        self._draw_selector_row(screen, rx, y, rw, t('char_class_label'),
                                cv, sel, 0, mouse_pos, buttons)
        y += gap
        # row 1: 피부색
        skin_col = SKIN_TONES[(appearance or {}).get('skin', 0) % len(SKIN_TONES)]
        self._draw_selector_row(screen, rx, y, rw, t('char_skin_label'),
                                None, sel, 1, mouse_pos, buttons, swatch=skin_col)
        y += gap
        # row 2: 헤어스타일
        hi = (appearance or {}).get('hair', 0) % len(HAIR_STYLES)
        hv = self.font_md.render(t('hair_' + HAIR_STYLES[hi]), True, (220, 220, 230))
        self._draw_selector_row(screen, rx, y, rw, t('char_hair_label'),
                                hv, sel, 2, mouse_pos, buttons)
        y += gap
        # row 3: 머리색
        hair_col = HAIR_COLORS[(appearance or {}).get('haircol', 0) % len(HAIR_COLORS)]
        self._draw_selector_row(screen, rx, y, rw, t('char_haircol_label'),
                                None, sel, 3, mouse_pos, buttons, swatch=hair_col)
        y += gap
        # row 4: 이름 입력
        nlbl = self.font_sm.render(t('char_name_label'), True, (150, 150, 170))
        screen.blit(nlbl, (rx, y - 15))
        field = pygame.Rect(rx, y, rw, 38)
        act = (sel == 4)
        pygame.draw.rect(screen, (20, 20, 38), field, border_radius=5)
        pygame.draw.rect(screen, GOLD_COLOR if act else (66, 62, 96),
                         field, 2 if act else 1, border_radius=5)
        shown = name or 'Hero'
        caret = '_' if (act and (pygame.time.get_ticks() // 500) % 2 == 0) else ''
        ns = self.font_md.render(shown + caret, True,
                                 (255, 255, 255) if name else (110, 110, 130))
        screen.blit(ns, (field.left + 12, field.centery - ns.get_height() // 2))
        buttons.append((field, 'name_field'))

        # ── 생성 버튼 (하단 전체 폭) ──────────────────────────────────
        cbtn = pygame.Rect(px + 26, py + ph - 66, pw - 52, 46)
        cact = (sel == 5)
        bg_c, bd_c, tc = _btn_colors(cact, cbtn.collidepoint(mouse_pos))
        if locked:
            bg_c, bd_c, tc = (24, 22, 34), (70, 66, 90), (120, 120, 140)
        pygame.draw.rect(screen, bg_c, cbtn, border_radius=6)
        pygame.draw.rect(screen, bd_c, cbtn, 2 if cact else 1, border_radius=6)
        cs = self.font_lg.render(t('class_locked_btn') if locked else t('char_create_btn'),
                                 True, tc)
        screen.blit(cs, (cbtn.centerx - cs.get_width() // 2,
                         cbtn.centery - cs.get_height() // 2))
        buttons.append((cbtn, 'create'))

        hint = self.font_sm.render(t('char_create_hint'), True, (90, 88, 120))
        screen.blit(hint, (cx - hint.get_width() // 2, py + ph - 92))
        self._char_create_buttons = buttons
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
    def render_paused(self, screen, settings, pause_sel, mouse_pos=(0, 0),
                      tags=None, mp_code=None):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        bw = 370
        _tags = tags or ['resume', 'save', 'bgm', 'sfx', 'fs', 'lang', 'title', 'quit']
        bh = 90 + len(_tags) * 46 + 30
        bx = WINDOW_WIDTH  // 2 - bw // 2
        by = WINDOW_HEIGHT // 2 - bh // 2

        pygame.draw.rect(screen, (12, 12, 26), (bx, by, bw, bh))
        pygame.draw.rect(screen, (90, 90, 130), (bx, by, bw, bh), 2)
        pygame.draw.rect(screen, (30, 30, 55), (bx+2, by+2, bw-4, 38))

        title_s = self.font_lg.render(t('pause_title'), True, WHITE)
        screen.blit(title_s, (bx + (bw - title_s.get_width()) // 2, by + 8))
        pygame.draw.line(screen, (60, 60, 95), (bx+12, by+44), (bx+bw-12, by+44))

        lang_val = LANG_NAMES.get(settings.get('language', 'en'), 'English')
        fs_val   = t('pause_fs_on') if settings['fullscreen'] else t('pause_fs_off')

        def _label(tag):
            return {
                'resume': t('pause_resume'),
                'save':   t('pause_save'),
                'mp_copy': f"{t('pause_mp_copy')}  {mp_code or ''}",
                'mp_join': t('pause_mp_join'),
                'bgm':  f"{t('pause_bgm')}    {int(settings['bgm_vol']*100):3d}%",
                'sfx':  f"{t('pause_sfx')}    {int(settings['sfx_vol']*100):3d}%",
                'fs':   f"{t('pause_fs')}    {fs_val}",
                'lang': f"{t('pause_lang')}    {lang_val}",
                'title': t('pause_title_'),
                'quit': t('pause_quit'),
            }.get(tag, tag)

        ITEMS = [(_label(tg), (None if tg == 'resume' else tg)) for tg in _tags]

        item_colors = {
            None: WHITE, 'save': (100, 220, 130),
            'mp_copy': (255, 226, 120), 'mp_join': (140, 200, 255),
            'bgm': LIGHT_GRAY, 'sfx': LIGHT_GRAY, 'fs': LIGHT_GRAY,
            'lang': (120, 200, 255), 'title': LIGHT_GRAY, 'quit': (200, 80, 80),
        }

        for i, (text, tag) in enumerate(ITEMS):
            is_sel = (i == pause_sel)
            iy = by + 56 + i * 46
            is_hov = pygame.Rect(bx+8, iy-3, bw-16, 32).collidepoint(mouse_pos)

            if is_sel:
                pygame.draw.rect(screen, (30, 30, 58), (bx+8, iy-3, bw-16, 32))
                pygame.draw.rect(screen, (70, 70, 110), (bx+8, iy-3, bw-16, 32), 1)
            elif is_hov:
                pygame.draw.rect(screen, (22, 22, 42), (bx+8, iy-3, bw-16, 32))
                pygame.draw.rect(screen, (55, 55, 88), (bx+8, iy-3, bw-16, 32), 1)

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

        # ── SP (스태미나) 바 — 공격 자원, 낮으면 붉게 펄스 ──
        st = getattr(player, 'stamina', 100.0)
        st_max = getattr(player, 'stamina_max', 100)
        sp_ratio = max(0.0, min(1.0, st / st_max))
        low = sp_ratio < 0.25
        if low:
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.012)
            sp_label_col = (255, int(120 + 80 * pulse), 60)
        else:
            sp_label_col = (170, 220, 80)
        sp_label = self.font_sm.render("SP", True, sp_label_col)
        screen.blit(sp_label, (x, cy - sp_label.get_height() // 2))
        x += sp_label.get_width() + 6

        sp_bw = 90; sp_bh = 10
        sp_by = cy - sp_bh // 2
        pygame.draw.rect(screen, (35, 45, 18), (x, sp_by, sp_bw, sp_bh))
        if sp_ratio > 0:
            if low:
                bar_col = (230, 90, 50)
            else:
                bar_col = (int(120 + 90 * (1 - sp_ratio)), 210, 60)
            pygame.draw.rect(screen, bar_col,
                             (x, sp_by, max(1, int(sp_bw * sp_ratio)), sp_bh))
        pygame.draw.rect(screen, (70, 90, 40), (x, sp_by, sp_bw, sp_bh), 1)
        x += sp_bw + 14

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

        pygame.draw.line(screen, (50, 50, 75), (x, 6), (x, TOP_BAR_H - 6))
        x += 10

        # ── 골드 (표시값 롤업 — 실제 player.gold는 항상 정확, 연출만 지연) ──
        shown = getattr(self, '_gold_shown', None)
        if shown is None or abs(shown - player.gold) > 500:
            shown = float(player.gold)          # 첫 렌더/큰 점프는 즉시 동기화
        shown += (player.gold - shown) * 0.12
        if abs(shown - player.gold) < 0.6:
            shown = float(player.gold)
        self._gold_shown = shown
        rolling = int(shown) != player.gold
        g_col = (255, 235, 130) if rolling else GOLD_COLOR   # 롤업 중 반짝
        gold_label = self.font_sm.render("G", True, g_col)
        screen.blit(gold_label, (x, cy - gold_label.get_height() // 2))
        x += gold_label.get_width() + 5
        gold_val = self.font_md.render(str(int(shown)), True, g_col)
        screen.blit(gold_val, (x, cy - gold_val.get_height() // 2))
        x += gold_val.get_width() + 16

        # ── 드라이브 게이지 (캔슬 자원 3칸 — ◆) ──
        drive = getattr(player, 'drive', 0.0)
        drive_max = getattr(player, 'drive_max', 3)
        pygame.draw.line(screen, (50, 50, 75), (x, 6), (x, TOP_BAR_H - 6))
        x += 10
        for i in range(drive_max):
            fill = max(0.0, min(1.0, drive - i))
            pts = [(x + 5, cy - 6), (x + 10, cy), (x + 5, cy + 6), (x, cy)]
            if fill >= 1.0:
                pygame.draw.polygon(screen, (90, 220, 255), pts)      # 가득
            elif fill > 0:
                pygame.draw.polygon(screen, (40, 95, 120), pts)       # 회복 중
                pygame.draw.polygon(screen, (90, 220, 255), pts, 1)
            else:
                pygame.draw.polygon(screen, (45, 55, 80), pts, 1)     # 빈 칸
            x += 14
        x += 8

        # ── 상태이상 배지 ──
        _debuffs = [
            ('cursed_ms',  t('debuff_curse'), (220, 100, 255), (45,  10,  60), (160,  50, 220)),
            ('slowed_ms',  t('debuff_slow'),  ( 90, 170, 255), (10,  20,  55), ( 60, 120, 220)),
            ('feared_ms',  t('debuff_fear'),  (255, 215,  60), (50,  40,   5), (200, 160,  20)),
        ]
        ch = TOP_BAR_H - 8; cy2 = 4
        for attr, label, txt_col, bg_col, border_col in _debuffs:
            ms = getattr(player, attr, 0)
            if ms > 0:
                sec_left = math.ceil(ms / 1000)
                badge_s = self.font_sm.render(f"{label} {sec_left}s", True, txt_col)
                cw = badge_s.get_width() + 10
                pygame.draw.rect(screen, bg_col, (x, cy2, cw, ch))
                pygame.draw.rect(screen, border_col, (x, cy2, cw, ch), 1)
                screen.blit(badge_s, (x + 5, cy2 + ch // 2 - badge_s.get_height() // 2))
                x += cw + 6

        # ── TEST 모드 배지 ──
        if is_test_mode:
            badge = self.font_md.render("TEST MODE", True, (20, 20, 20))
            bw = badge.get_width() + 14
            bh = TOP_BAR_H - 8
            bx = WINDOW_WIDTH - bw - 14
            by = 4
            pygame.draw.rect(screen, (255, 80, 0), (bx, by, bw, bh))
            pygame.draw.rect(screen, (255, 160, 60), (bx, by, bw, bh), 1)
            screen.blit(badge, (bx + 7, by + bh // 2 - badge.get_height() // 2))

    def _right_panel(self, screen, player, dungeon, skill_mgr,
                     unlocked_combos=None, skill_books=None,
                     skill_levels=None, skill_xp=None,
                     equipped_skills=None):
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
        aspd_total = getattr(player, 'total_attack_speed', player.attack_speed)
        aspd_str = f"{aspd_total:.2f}" + (
            f" (+{player.token_aspd:.2f})" if getattr(player, 'token_aspd', 0) else "")
        stats = [
            (t('stat_atk'),  atk_str,                         WHITE),
            (t('stat_def'),  def_str,                         (130, 180, 255)),
            (t('stat_aspd'), aspd_str,                        (255, 200, 80)),
            (t('stat_eva'),  f"{player.evasion}%",            (80, 220, 160)),
            (t('stat_mspd'), f"{player.move_speed:.2f}",      (160, 160, 255)),
            (t('stat_spred'), f"-{getattr(player, 'total_sp_reduce', 0.0) * 100:.0f}%",
             (170, 220, 80)),
        ]
        # 던전 증표 보유 시 요약 표시 (⚔공격 · ⚡신속 · 🛡수호)
        _tok = getattr(player, 'tokens', None)
        if _tok and sum(_tok.values()) > 0:
            stats.append((t('stat_tokens'),
                          f"{_tok.get('atk',0)}/{_tok.get('haste',0)}/{_tok.get('guard',0)}",
                          (235, 200, 90)))
        for label, val, col in stats:
            lbl_s = self.font_sm.render(label, True, (100, 100, 130))
            val_s = self.font_sm.render(val, True, col)
            screen.blit(lbl_s, (rx+8, y))
            screen.blit(val_s, (rx + pw - val_s.get_width() - 8, y))
            y += 14
        y += 2

        # ── 장착 장비 ───────────────────────────────────────────────
        sec_header('sec_equip', LIGHT_GRAY)
        _SLOT_LABELS = {'head': t('slot_head_s'), 'body': t('slot_body_s'), 'weapon': t('slot_wpn_s'),
                        'off_hand': t('slot_off_hud'), 'accessory': t('slot_acc_s'), 'feet': t('slot_feet_s')}
        for slot, item in player.equipment.items():
            lbl_s = self.font_sm.render(_SLOT_LABELS.get(slot, slot), True, (100, 100, 130))
            if item:
                pygame.draw.rect(screen, (20, 22, 38), (rx+6, y-1, pw-12, 15))
                nm = item.name if len(item.name) <= 8 else item.name[:7] + '…'
                broken = getattr(item, 'broken', False)
                val_s = self.font_sm.render(nm, True,
                                            (255, 80, 60) if broken else item.color)
            else:
                val_s = self.font_sm.render('--', True, (40, 40, 60))
            screen.blit(lbl_s, (rx+8, y))
            screen.blit(val_s, (rx + pw - val_s.get_width() - 8, y))
            y += 14
            # 내구도 미니 바 (방어구) — 파손 시 붉은 점멸
            if item and getattr(item, 'max_durability', 0) > 0:
                frac = item.durability / item.max_durability
                bw2 = pw - 16
                pygame.draw.rect(screen, (30, 26, 26), (rx+8, y-2, bw2, 3))
                if frac > 0:
                    d_col = ((90, 200, 90) if frac > 0.5 else
                             (230, 180, 60) if frac > 0.25 else (230, 80, 60))
                    pygame.draw.rect(screen, d_col,
                                     (rx+8, y-2, max(1, int(bw2 * frac)), 3))
                elif (pygame.time.get_ticks() // 400) % 2 == 0:
                    pygame.draw.rect(screen, (255, 70, 50), (rx+8, y-2, bw2, 3))
                y += 4
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
        sl = skill_levels or {}
        _eq = equipped_skills or DEFAULT_EQUIPPED
        for slot in ('W', 'A', 'S', 'D'):
            skill_id = _eq.get(slot)
            if not skill_id:
                continue
            # try ALL_SKILL_DEFS first, fall back to legacy SKILL_DEFS
            sdef = ALL_SKILL_DEFS.get(skill_id)
            if sdef is None:
                # legacy fallback: find by key
                sdef = next((s for s in SKILL_DEFS if s['key'] == slot), None)
            if sdef is None:
                continue
            ready = skill_mgr.ready(slot) if skill_mgr else True
            frac  = skill_mgr.cooldown_frac(slot) if skill_mgr else 0.0
            rem   = skill_mgr.remaining_sec(slot) if skill_mgr else 0.0
            nc    = sdef['color'] if ready else (60, 60, 80)
            lvl    = sl.get(skill_id, 1)
            is_max = lvl >= SKILL_MAX_LEVEL
            lv_str = " MAX" if is_max else (f" Lv.{lvl}" if lvl > 1 else "")
            label  = f"[{slot}] {sdef['name']}{lv_str}"

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
            y += 2
        y += 3

        # ── 강화 스킬 ────────────────────────────────────────────────
        from core.skills import COMBO_SKILL_DEFS, combo_def
        sec_header('sec_combo', (130, 110, 200))
        uc = unlocked_combos or set()
        sb = skill_books or set()
        _cc = getattr(player, 'char_class', 'warrior')
        for cid, _base in COMBO_SKILL_DEFS.items():
            cdef = combo_def(cid, _cc)
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

        # (오의 SP 바 제거 — 스태미나 SP 체제로 통합)

        # ── 궁극기 ──────────────────────────────────────────────────
        from core.skills import ULTIMATE_SKILL_DEFS, ultimate_def_for
        sec_header('sec_ultimate', (255, 120, 50))
        _cc = getattr(player, 'char_class', 'warrior') if player else 'warrior'
        for uid, _base in ULTIMATE_SKILL_DEFS.items():
            udef = ultimate_def_for(uid, _cc)
            unlocked_ult = player and player.level >= udef['level_req']
            ready_ult    = skill_mgr.ready(uid) if (skill_mgr and unlocked_ult) else False
            rem_ult      = skill_mgr.remaining_sec(uid) if (skill_mgr and unlocked_ult) else 0.0
            frac_ult     = skill_mgr.cooldown_frac(uid) if (skill_mgr and unlocked_ult) else 0.0
            col = udef['color'] if (unlocked_ult and ready_ult) else (70, 60, 60)
            if unlocked_ult:
                pygame.draw.rect(screen, (30, 14, 14), (rx+6, y-1, pw-12, 24))
            ks = self.font_sm.render(f"[{udef['keys']}]", True, col)
            ns = self.font_sm.render(udef['name'], True, col)
            screen.blit(ks, (rx+8, y))
            screen.blit(ns, (rx+8 + ks.get_width() + 4, y))
            if unlocked_ult and not ready_ult:
                rs = self.font_sm.render(f"{rem_ult:.0f}s", True, (120, 80, 80))
                screen.blit(rs, (rx + pw - rs.get_width() - 8, y))
            elif not unlocked_ult:
                ls = self.font_sm.render(f"Lv.{udef['level_req']}", True, (55, 45, 45))
                screen.blit(ls, (rx + pw - ls.get_width() - 8, y))
            y += 13
            if unlocked_ult:
                _bar(screen, rx+8, y, bw, 5,
                     int(bw * (1 - frac_ult)), bw,
                     udef['color'] if ready_ult else (60, 30, 30), (18, 10, 10))
                y += 6
            y += 2
        y += 2

        # ── 미니맵 ──────────────────────────────────────────────────
        sec_header('sec_minimap', LIGHT_GRAY)
        if dungeon:
            self._draw_minimap(screen, dungeon, player, rx+8, y)

    def _draw_minimap(self, screen, dungeon, player, ox, oy):
        # 패널에 맞춰 스케일 자동 조정 (큰 마을은 축소) — 던전은 2 유지
        _MM_MAX_W, _MM_MAX_H = 204, 92
        scale = max(1, min(_MM_MAX_W // dungeon.width, _MM_MAX_H // dungeon.height))
        pygame.draw.rect(screen, (8, 8, 18), (ox, oy, dungeon.width*scale, dungeon.height*scale))

        collapsing = False
        for my in range(dungeon.height):
            for mx in range(dungeon.width):
                tile = dungeon.tiles[my][mx]
                if not tile.explored:
                    continue
                tt = tile.tile_type
                if tt == TileType.COLLAPSED:
                    collapsing = True
                    col = (14, 8, 6)                 # 무너진 구덩이 — 미니맵에도 검게
                elif not tile.visible:
                    if tt == TileType.DOOR:         col = (80, 40, 120)
                    elif tt == TileType.BURNING_DOOR: col = (120, 40, 10)
                    elif tt == TileType.WALL: col = (30, 30, 42)
                    else: col = (40, 40, 55)
                else:
                    if tt == TileType.WALL:          col = (60,60,80)
                    elif tt == TileType.STAIRS_DOWN:  col = STAIRS_LIT
                    elif tt == TileType.SHOP:         col = SHOP_COLOR
                    elif tt == TileType.DOOR:         col = (160, 80, 255)
                    elif tt == TileType.BURNING_DOOR: col = (255, 80, 20)
                    elif tt == TileType.WATER:        col = (44, 92, 150)
                    else:                             col = (75,75,100)
                pygame.draw.rect(screen, col, (ox+mx*scale, oy+my*scale, scale, scale))

        # 붕괴 중이면 출구(문/계단)를 미니맵에 크게 점멸 표시
        if collapsing:
            exit_pos = getattr(dungeon, 'stairs_pos', None)
            if exit_pos:
                blink = (255, 235, 90) if (pygame.time.get_ticks() // 250) % 2 == 0 else (255, 140, 40)
                ex = ox + exit_pos[0] * scale
                ey = oy + exit_pos[1] * scale
                pygame.draw.rect(screen, blink, (ex - 2, ey - 2, scale + 4, scale + 4), 1)

        for enemy in dungeon.enemies:
            if not (enemy.is_alive() and dungeon.tiles[enemy.y][enemy.x].visible):
                continue
            ex = ox + enemy.x * scale
            ey = oy + enemy.y * scale
            if enemy.is_boss:
                # 4×4 (scale*2) 크기, 중앙 정렬
                pygame.draw.rect(screen, BOSS_COLOR,
                                 (ex - scale // 2, ey - scale // 2, scale * 2, scale * 2))
                # 밝은 테두리
                pygame.draw.rect(screen, (255, 180, 255),
                                 (ex - scale // 2, ey - scale // 2, scale * 2, scale * 2), 1)
            else:
                pygame.draw.rect(screen, (220, 60, 60), (ex, ey, scale, scale))

        # NPC 마커 (마을) — 시설·퀘스트=금색, 배회 시민=하늘색
        m = max(2, scale)
        for npc in getattr(self, '_mm_npcs', None) or []:
            nx = ox + npc['x'] * scale
            ny = oy + npc['y'] * scale
            ncol = (90, 210, 255) if npc.get('ambient') else (255, 220, 90)
            pygame.draw.rect(screen, ncol, (nx, ny, m, m))

        pygame.draw.rect(screen, WHITE, (ox+player.x*scale-1, oy+player.y*scale-1, scale+2, scale+2))
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
            clean = _renderable(self.font_sm, text)      # 이모지(≡ 두부) 제거
            screen.blit(self.font_sm.render(clean, True, col), (8, by+6+i*line_h))

    def _label(self, screen, text, x, y, color):
        screen.blit(self.font_sm.render(text, True, color), (x, y))

    # ------------------------------------------------------------------ #
    _INV_CAT_COL = {'equip': (108, 152, 232), 'consume': (108, 200, 140),
                    'gather': (232, 182, 92)}
    _INV_CAT_KEYS = ('all', 'equip', 'consume', 'gather')
    _INV_EQUIP_TYPES = ('weapon', 'armor', 'head', 'off_hand', 'accessory',
                        'boots', 'feet')

    _INV_GATHER_PREFIXES = ('food_', 'seed_', 'grilled', 'deluxe')

    def _inv_cat_of(self, item):
        """아이템 → 카테고리(슬롯 색 강조용). game._item_category와 동일 규칙."""
        if item is None:
            return 'consume'
        if item.item_type in self._INV_EQUIP_TYPES:
            return 'equip'
        key = getattr(item, 'key', '') or ''
        if key.startswith(self._INV_GATHER_PREFIXES):
            return 'gather'
        return 'consume'

    def render_inventory(self, screen, player, sel, mouse_pos=(0, 0),
                         drag_idx=None, drag_pos=(0, 0),
                         view=None, cat=0, cat_counts=None):
        """인벤토리 화면 오버레이 (카테고리 탭 + 필터 뷰)."""
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        screen.blit(ov, (0, 0))

        inv = player.inventory
        if view is None:
            view = list(range(len(inv)))
        cat_counts = cat_counts or {}

        cols, rows = 5, 4
        cell = 140
        pad  = 6
        grid_dy = 76
        pw   = cols * cell + pad * 2
        ph   = grid_dy + rows * cell + pad * 2 + 60
        bx   = W // 2 - pw // 2
        by   = H // 2 - ph // 2

        pygame.draw.rect(screen, (12, 12, 26), (bx, by, pw, ph), border_radius=6)
        pygame.draw.rect(screen, (80, 80, 120), (bx, by, pw, ph), 2, border_radius=6)

        # 제목
        title = self.font_lg.render(t('inv_title'), True, GOLD_COLOR)
        screen.blit(title, (bx + (pw - title.get_width()) // 2, by + 6))

        # ── 카테고리 탭 (전체/장비/소모품/채집품) ──────────────────────
        tw = (pw - pad * 2) // 4
        ty, th = by + 42, 26
        _tab_lbl = {'all': t('inv_cat_all'), 'equip': t('inv_cat_equip'),
                    'consume': t('inv_cat_consume'), 'gather': t('inv_cat_gather')}
        for ci, ckey in enumerate(self._INV_CAT_KEYS):
            tr = pygame.Rect(bx + pad + ci * tw, ty, tw - 4, th)
            active = (ci == cat)
            accent = self._INV_CAT_COL.get(ckey, (150, 150, 170))
            if active:
                pygame.draw.rect(screen, (44, 44, 74), tr, border_radius=4)
                pygame.draw.rect(screen, accent, tr, 2, border_radius=4)
            elif tr.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (26, 26, 46), tr, border_radius=4)
                pygame.draw.rect(screen, (70, 70, 100), tr, 1, border_radius=4)
            else:
                pygame.draw.rect(screen, (18, 18, 34), tr, border_radius=4)
                pygame.draw.rect(screen, (48, 48, 74), tr, 1, border_radius=4)
            lbl = _tab_lbl[ckey]
            if ckey != 'all':
                lbl += f" {cat_counts.get(ckey, 0)}"
            col = (255, 255, 255) if active else (150, 150, 175)
            ls = self.font_sm.render(lbl, True, col)
            screen.blit(ls, (tr.centerx - ls.get_width() // 2,
                             tr.centery - ls.get_height() // 2))

        # 슬롯 그리드 — view 순서대로 표시
        gx = bx + pad
        gy = by + grid_dy
        for i in range(player.max_inventory):
            col_i = i % cols
            row_i = i // cols
            sx = gx + col_i * cell
            sy = gy + row_i * cell

            item = inv[view[i]] if i < len(view) else None
            is_sel = (i == sel)
            is_hov = pygame.Rect(sx, sy, cell-2, cell-2).collidepoint(mouse_pos)
            accent = (self._INV_CAT_COL.get(self._inv_cat_of(item), (60, 60, 90))
                      if item else None)
            if is_sel:
                pygame.draw.rect(screen, (50, 50, 90), (sx, sy, cell-2, cell-2), border_radius=4)
                pygame.draw.rect(screen, GOLD_COLOR,   (sx, sy, cell-2, cell-2), 2, border_radius=4)
            elif is_hov:
                pygame.draw.rect(screen, (28, 28, 50), (sx, sy, cell-2, cell-2), border_radius=4)
                pygame.draw.rect(screen, (75, 75, 108), (sx, sy, cell-2, cell-2), 1, border_radius=4)
            else:
                pygame.draw.rect(screen, (20, 20, 38), (sx, sy, cell-2, cell-2), border_radius=4)
                pygame.draw.rect(screen, accent if accent else (45, 45, 70),
                                 (sx, sy, cell-2, cell-2), 1, border_radius=4)
            if item is not None and accent:
                pygame.draw.rect(screen, accent, (sx, sy, 4, cell - 2),
                                 border_top_left_radius=4, border_bottom_left_radius=4)

            if item is not None:
                # 아이콘
                ico_size = 44 if USE_MC_ITEMS else 28
                ico_x = sx + (cell - 2 - ico_size) // 2
                ico_y = sy + 6
                if USE_MC_ITEMS:
                    draw_mc_item(screen, ico_x, ico_y, ico_size,
                                 item.item_type, item.color,
                                 key=getattr(item, 'key', None))
                else:
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
                pygame.draw.circle(screen, (34, 34, 52),
                                   (sx + (cell-2)//2, sy + (cell-2)//2), 3)

        # 선택된 아이템 정보
        info_y = gy + rows * cell + pad + 4
        pygame.draw.line(screen, (50, 50, 80), (bx+12, info_y), (bx+pw-12, info_y))
        if sel < len(view):
            item = inv[view[sel]]
            type_map = {'weapon': t('inv_type_weapon'), 'armor': t('inv_type_armor'),
                        'head': t('inv_type_head'), 'off_hand': t('inv_type_off'),
                        'accessory': t('inv_type_acc'), 'boots': t('inv_type_boots'),
                        'consumable': t('inv_type_cons'), 'skillbook': t('inv_type_book')}
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
            # 내구도 (방어구)
            if getattr(item, 'max_durability', 0) > 0:
                info += ('  ' + t('broken_tag') if item.broken
                         else f'  🛡{item.durability}/{item.max_durability}')
            info_s = self.font_sm.render(info, True,
                                         (255, 80, 60) if getattr(item, 'broken', False)
                                         else item.color)
            screen.blit(info_s, (bx + (pw - info_s.get_width()) // 2, info_y + 6))

        # ── 버리기 존 ────────────────────────────────────────────────
        trash_rect = pygame.Rect(bx + pw - 130, by + ph - 42, 122, 34)
        # 패널 밖 드래그 중일 때도 하이라이트
        drag_outside = (drag_idx is not None and
                        not pygame.Rect(bx, by, pw, ph).collidepoint(drag_pos))
        over_trash = (trash_rect.collidepoint(mouse_pos) or
                      (drag_idx is not None and trash_rect.collidepoint(drag_pos)) or
                      drag_outside)
        has_active = (sel < len(view)) or (drag_idx is not None)
        if over_trash and has_active:
            pygame.draw.rect(screen, (80, 18, 18), trash_rect, border_radius=4)
            pygame.draw.rect(screen, (240, 70, 70), trash_rect, 2, border_radius=4)
            tc = (255, 110, 110)
        elif has_active:
            pygame.draw.rect(screen, (32, 14, 14), trash_rect, border_radius=4)
            pygame.draw.rect(screen, (110, 44, 44), trash_rect, 1, border_radius=4)
            tc = (160, 70, 70)
        else:
            pygame.draw.rect(screen, (18, 12, 12), trash_rect, border_radius=4)
            pygame.draw.rect(screen, (55, 35, 35), trash_rect, 1, border_radius=4)
            tc = (65, 42, 42)
        trash_lbl = self.font_sm.render(t('inv_discard_btn'), True, tc)
        screen.blit(trash_lbl, (trash_rect.centerx - trash_lbl.get_width() // 2,
                                trash_rect.centery - trash_lbl.get_height() // 2))

        # ── 드래그 유령 아이템 ───────────────────────────────────────
        if drag_idx is not None and drag_idx < len(player.inventory):
            ghost_item = player.inventory[drag_idx]
            ghost_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
            ghost_surf.fill((*ghost_item.color, 160))
            pygame.draw.rect(ghost_surf, (*ghost_item.color, 220), (0, 0, 36, 36), 2, border_radius=3)
            screen.blit(ghost_surf, (drag_pos[0] - 18, drag_pos[1] - 18))

        # 힌트
        hint_s = self.font_sm.render(t('inv_hint') + "  " + t('inv_del_hint'), True, (65, 65, 95))
        screen.blit(hint_s, (bx + 10, by + ph - 20))

    # ------------------------------------------------------------------ #
    # ------------------------------------------------------------------ #
    def _wrap_text(self, text, font, max_w):
        words, lines, cur = text.split(' '), [], ''
        for w in words:
            trial = (cur + ' ' + w).strip()
            if font.size(trial)[0] <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def render_dialog(self, screen, dialog):
        """하단 대화창 — NPC 대사 (타자기 효과) + 수락/거절 힌트."""
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        pw, ph = W - 24, 132
        bx, by = 12, H - ph - 8
        pygame.draw.rect(screen, (14, 11, 20), (bx, by, pw, ph), border_radius=8)
        pygame.draw.rect(screen, (190, 160, 90), (bx, by, pw, ph), 2, border_radius=8)

        name_s = self.font_md.render(dialog['npc_name'], True, (255, 215, 130))
        pygame.draw.rect(screen, (40, 30, 16),
                         (bx + 12, by - 10, name_s.get_width() + 16, 22),
                         border_radius=5)
        screen.blit(name_s, (bx + 20, by - 8))

        # 타자기 효과 — 대사가 한 글자씩 흐른다
        elapsed = pygame.time.get_ticks() - dialog.get('start', 0)
        visible = dialog['text'][:max(1, int(elapsed / 16))]
        y = by + 20
        for line in self._wrap_text(visible, self.font_md, pw - 40)[:4]:
            line_s = self.font_md.render(line, True, (230, 225, 210))
            screen.blit(line_s, (bx + 20, y))
            y += 22
        hint_key = 'dialog_offer_hint' if dialog['mode'] == 'offer' else 'dialog_close_hint'
        hint = self.font_sm.render(t(hint_key), True, (170, 150, 110))
        screen.blit(hint, (bx + pw - hint.get_width() - 16, by + ph - 22))

    def _fit_text(self, font, text, max_w, color):
        """max_w 안에 맞게 말줄임(…) 처리한 렌더 서피스."""
        surf = font.render(text, True, color)
        if surf.get_width() <= max_w:
            return surf
        while text and font.size(text + '…')[0] > max_w:
            text = text[:-1]
        return font.render(text + '…', True, color)

    def render_journal(self, screen, records, best_floor=1):
        """J — 정복 일지: 테마별 던전 아트 썸네일 갤러리 + 클리어 횟수 + 칭호.

        각 구간 테마를 팔레트 기반 미니 던전 씬 썸네일로 시각화한다.
        정복(999 클리어) 시 [심연의 지배자] 뱃지 노출. 미해금 테마는 자물쇠.
        """
        from map.theme import (theme_name, theme_floor_range, THEME_COUNT,
                               get_theme_by_index)
        from ui.theme_art import draw_theme_thumb
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 220))
        screen.blit(ov, (0, 0))
        pw, ph = 852, 660
        bx, by = W // 2 - pw // 2, H // 2 - ph // 2
        pygame.draw.rect(screen, (13, 16, 26), (bx, by, pw, ph), border_radius=6)
        pygame.draw.rect(screen, (70, 66, 105), (bx, by, pw, ph), 2, border_radius=6)

        cleared = bool(records.get('game_cleared', False))
        tc = records.get('theme_clears', {}) or {}
        done_cnt = sum(1 for i in range(THEME_COUNT) if int(tc.get(str(i), 0)) > 0)
        tnow = pygame.time.get_ticks()

        # ── 타이틀 + 진행도 ──
        title = self.font_lg.render(t('journal_title'), True, GOLD_COLOR)
        screen.blit(title, (bx + pw // 2 - title.get_width() // 2, by + 14))
        bf = self.font_md.render(t('journal_best_floor', best_floor), True, (170, 210, 255))
        screen.blit(bf, (bx + 26, by + 56))
        prog = self.font_md.render(f"{done_cnt} / {THEME_COUNT}", True, (150, 220, 160))
        screen.blit(prog, (bx + pw - prog.get_width() - 26, by + 56))
        if cleared:
            spark = (255, 235, 120) if (tnow // 300) % 2 == 0 else (235, 185, 60)
            cs = self._fit_text(self.font_md, '★ ' + t('journal_conquered') + ' ★',
                                pw - 220, spark)
            screen.blit(cs, (bx + pw // 2 - cs.get_width() // 2, by + 56))
        pygame.draw.line(screen, (50, 48, 78), (bx + 24, by + 82), (bx + pw - 24, by + 82))

        # ── 테마 썸네일 갤러리 (4열 × 5행) ──
        cols, rows = 4, 5
        mgx, gap = 24, 10
        tw = (pw - mgx * 2 - gap * (cols - 1)) // cols
        top = by + 92
        avail_h = (by + ph - 30) - top
        th = min(96, (avail_h - gap * (rows - 1)) // rows)
        for idx in range(THEME_COUNT):
            c, r = idx % cols, idx // cols
            x = bx + mgx + c * (tw + gap)
            y = top + r * (th + gap)
            cnt = int(tc.get(str(idx), 0))
            done = cnt > 0
            rect = pygame.Rect(x, y, tw, th)
            theme = get_theme_by_index(idx)
            draw_theme_thumb(screen, rect, idx, theme, done, tnow // 90)

            # 이름 스트립 (하단 반투명)
            strip = pygame.Surface((tw, 17), pygame.SRCALPHA)
            strip.fill((0, 0, 0, 165))
            screen.blit(strip, (x, y + th - 17))
            nm = theme_name(idx) if done else '???'
            ncol = (232, 234, 245) if done else (120, 122, 142)
            ns = self._fit_text(self.font_sm, nm, tw - 8, ncol)
            screen.blit(ns, (x + 4, y + th - 16))

            # 층 범위 배지 (좌상단)
            f0, f1 = theme_floor_range(idx)
            fr = self.font_sm.render(f"{f0}-{f1}", True, (210, 214, 230))
            fb = pygame.Surface((fr.get_width() + 6, fr.get_height() + 2), pygame.SRCALPHA)
            fb.fill((0, 0, 0, 150))
            screen.blit(fb, (x + 3, y + 3))
            screen.blit(fr, (x + 6, y + 4))

            # 클리어 횟수 배지 (우상단)
            if done:
                cx = self.font_sm.render('×' + str(cnt), True, (32, 26, 6))
                cb = pygame.Rect(x + tw - cx.get_width() - 9, y + 3,
                                 cx.get_width() + 6, cx.get_height() + 2)
                pygame.draw.rect(screen, GOLD_COLOR, cb, border_radius=3)
                screen.blit(cx, (cb.x + 3, cb.y + 1))

            # 테두리
            bcol = theme['stairs_lit'] if done else (58, 58, 76)
            pygame.draw.rect(screen, bcol, rect, 1, border_radius=3)

        hint = self.font_sm.render(t('journal_hint'), True, (90, 88, 120))
        screen.blit(hint, (bx + pw // 2 - hint.get_width() // 2, by + ph - 22))

    def render_pet_status(self, screen, player, pet):
        """B — 펫 상태창: 이름·타입·레벨·강화석·다음 강화 비용·효과."""
        from entities.pet import PET_META, PET_TYPES
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 0, 214))
        screen.blit(ov, (0, 0))
        pw, ph = 500, 440
        bx, by = W // 2 - pw // 2, H // 2 - ph // 2
        pygame.draw.rect(screen, (13, 16, 26), (bx, by, pw, ph), border_radius=6)
        pygame.draw.rect(screen, (70, 66, 105), (bx, by, pw, ph), 2, border_radius=6)
        cx = bx + pw // 2

        if pet is None:
            msg = self.font_md.render(t('pet_locked'), True, (200, 200, 210))
            screen.blit(msg, (cx - msg.get_width() // 2, by + ph // 2 - 10))
            return

        meta = PET_META[pet.type]; col = meta['color']
        title = self.font_lg.render(t('pet_status_title'), True, GOLD_COLOR)
        screen.blit(title, (cx - title.get_width() // 2, by + 18))
        pygame.draw.line(screen, (50, 48, 78), (bx + 24, by + 56), (bx + pw - 24, by + 56))

        # 펫 아이콘 (블록)
        icx, icy = bx + 70, by + 120
        pygame.draw.circle(screen, (*meta['accent'], 60), (icx, icy), 34)
        def IB(gx, gy, c, w=1, h=1):
            pygame.draw.rect(screen, c, (icx + gx * 6, icy + gy * 6, w * 6, h * 6))
        dark = tuple(max(0, k - 40) for k in col)
        IB(-3, -2, col, 6, 5); IB(-3, -2, meta['accent'], 6, 1); IB(-3, 2, dark, 6, 1)
        IB(-2, 0, (30, 30, 40)); IB(1, 0, (30, 30, 40))

        # 이름 + 타입 (←/→ 전환)
        nm = self.font_lg.render(t(meta['name_key']), True, col)
        screen.blit(nm, (bx + 130, by + 84))
        la = self.font_md.render('◀', True, (170, 170, 195))
        ra = self.font_md.render('▶', True, (170, 170, 195))
        ti = PET_TYPES.index(pet.type)
        screen.blit(la, (bx + 130, by + 120)); screen.blit(ra, (bx + 168, by + 120))
        tstr = self.font_sm.render(f"{ti+1}/{len(PET_TYPES)}", True, (150, 150, 175))
        screen.blit(tstr, (bx + 148, by + 122))

        # 효과 설명
        if pet.type == 'buff':
            eff = t('pet_eff_buff', int(pet.buff_pct * 100))
        elif pet.type == 'debuff':
            eff = t('pet_eff_debuff', int(pet.slow_pct * 100))
        else:
            eff = t('pet_eff_attack', int(pet.atk_coeff * 100))
        es = self.font_sm.render(eff, True, (200, 210, 225))
        screen.blit(es, (bx + 130, by + 150))

        # 스탯 (레벨 / 보유 강화석)
        y = by + 200
        lv = self.font_md.render(f"{t('pet_lvl')}: Lv.{pet.level}", True, (235, 235, 245))
        screen.blit(lv, (bx + 40, y))
        st = self.font_md.render(f"{t('pet_stones_lbl')}: 💠 {player.pet_stones}", True, (200, 170, 255))
        screen.blit(st, (bx + 260, y))

        # 강화 비용 / 성공률 바
        gold_cost, stone_cost = pet.next_cost()
        y2 = by + 250
        cost = self.font_sm.render(t('pet_next_cost', gold_cost, stone_cost), True, (235, 220, 150))
        screen.blit(cost, (bx + 40, y2))
        chance = int(pet.success_chance() * 100)
        sc = self.font_sm.render(t('pet_success', chance), True, (140, 220, 160))
        screen.blit(sc, (bx + 40, y2 + 24))
        # 성공률 바
        bar = pygame.Rect(bx + 40, y2 + 48, pw - 80, 10)
        pygame.draw.rect(screen, (30, 34, 48), bar, border_radius=3)
        pygame.draw.rect(screen, (90, 200, 120),
                         (bar.x, bar.y, int(bar.w * chance / 100), bar.h), border_radius=3)

        # 강화 버튼
        can = player.pet_stones >= stone_cost and player.gold >= gold_cost
        btn = pygame.Rect(cx - 110, by + ph - 78, 220, 40)
        bg = (34, 60, 34) if can else (40, 30, 30)
        bd = (90, 200, 110) if can else (120, 70, 70)
        pygame.draw.rect(screen, bg, btn, border_radius=5)
        pygame.draw.rect(screen, bd, btn, 2, border_radius=5)
        us = self.font_md.render('▲ ' + t('pet_lvl') + ' UP', True,
                                 (150, 240, 170) if can else (170, 120, 120))
        screen.blit(us, (btn.centerx - us.get_width() // 2, btn.centery - us.get_height() // 2))

        hint = self.font_sm.render(t('pet_hint'), True, (90, 88, 120))
        screen.blit(hint, (cx - hint.get_width() // 2, by + ph - 26))

    def render_questlog(self, screen, quests, max_floor=1):
        """Q — 퀘스트 일지: 진행 중 / 수락 가능 / 완료로 분류.

        미개방(층/선행 조건 미충족)은 '???' 티저로 노출해 다음 목표를 암시.
        """
        from core.quests import (QUESTS, qtext, giver_name, objective_str,
                                  quest_target, is_unlocked, unlock_hint)
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        screen.blit(ov, (0, 0))
        pw, ph = 600, 560
        bx, by = W // 2 - pw // 2, H // 2 - ph // 2
        pygame.draw.rect(screen, (13, 16, 26), (bx, by, pw, ph), border_radius=6)
        pygame.draw.rect(screen, (120, 170, 120), (bx, by, pw, ph), 2, border_radius=6)
        title = self.font_lg.render(t('quest_title'), True, (150, 230, 160))
        screen.blit(title, (bx + (pw - title.get_width()) // 2, by + 8))

        # 분류
        active, avail, locked, done = [], [], [], []
        for qid, q in QUESTS.items():
            st = quests.get(qid, {'state': 'available'})['state']
            if st in ('active', 'done'):
                active.append(qid)
            elif st == 'claimed':
                done.append(qid)
            elif is_unlocked(qid, quests, max_floor):
                avail.append(qid)
            else:
                locked.append(qid)

        y = by + 46
        x0 = bx + 16
        cw = pw - 32

        def section(label, color, count):
            nonlocal y
            hdr = self.font_md.render(f'{label}  ({count})', True, color)
            screen.blit(hdr, (x0, y))
            pygame.draw.line(screen, tuple(c // 2 for c in color),
                             (x0, y + 20), (bx + pw - 16, y + 20))
            y += 28

        def full_card(qid):
            nonlocal y
            q = QUESTS[qid]
            qs = quests.get(qid, {'state': 'available', 'progress': 0})
            st = qs['state']
            col = (255, 225, 120) if st == 'active' else (120, 255, 150) if st == 'done' else (200, 205, 215)
            pygame.draw.rect(screen, (24, 28, 42), (x0, y, cw, 66), border_radius=5)
            if st == 'done':
                pygame.draw.rect(screen, (90, 200, 120), (x0, y, cw, 66), 1, border_radius=5)
            screen.blit(self.font_md.render(qtext(qid, 'name'), True, col), (x0 + 10, y + 6))
            st_s = self.font_sm.render(t(f'quest_st_{st}'), True, col)
            screen.blit(st_s, (x0 + cw - st_s.get_width() - 10, y + 8))
            screen.blit(self.font_sm.render(
                f"{giver_name(q['giver'])} · {qtext(qid, 'desc')}", True,
                (170, 170, 185)), (x0 + 10, y + 28))
            if st in ('active', 'done'):
                frac = min(1.0, qs['progress'] / max(1, quest_target(qid)))
                pygame.draw.rect(screen, (30, 36, 30), (x0 + 10, y + 50, 300, 8))
                pygame.draw.rect(screen, col, (x0 + 10, y + 50, max(1, int(300 * frac)), 8))
                screen.blit(self.font_sm.render(objective_str(qid, qs['progress']),
                            True, col), (x0 + 318, y + 47))
            r = q['reward']
            parts = []
            if r.get('gold'):   parts.append(f"{r['gold']}G")
            if r.get('stones'): parts.append(t('quest_rw_stones', r['stones']))
            if r.get('items'):  parts.append(f"+{len(r['items'])}")
            rw = self.font_sm.render('  '.join(parts), True, (215, 185, 110))
            screen.blit(rw, (x0 + cw - rw.get_width() - 10, y + 47))
            y += 72

        def oneline(qid, color, prefix, suffix=''):
            nonlocal y
            label = f"{prefix} {qtext(qid, 'name')}{suffix}"
            screen.blit(self.font_sm.render(label, True, color), (x0 + 12, y))
            y += 20

        if active:
            section(t('quest_sec_active'), (255, 225, 120), len(active))
            for qid in active:
                full_card(qid)
        if avail:
            section(t('quest_sec_avail'), (150, 210, 255), len(avail))
            for qid in avail:
                full_card(qid)
        if locked:
            section(t('quest_sec_locked'), (130, 130, 140), len(locked))
            for qid in locked:
                oneline(qid, (110, 110, 120), '🔒 ???',
                        f"  ({t('quest_unlock_at', unlock_hint(qid))})")
        if done:
            section(t('quest_sec_done'), (110, 200, 130), len(done))
            for qid in done:
                oneline(qid, (110, 160, 120), '✔')

        hint = self.font_sm.render(t('quest_hint'), True, (110, 130, 110))
        screen.blit(hint, (bx + (pw - hint.get_width()) // 2, by + ph - 22))

    # ------------------------------------------------------------------ #
    def render_inn(self, screen, player, rest_cost):
        """여관(주모) — [1] 휴식 / [2] 여관밥."""
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        screen.blit(ov, (0, 0))
        pw, ph = 420, 240
        bx, by = W // 2 - pw // 2, H // 2 - ph // 2
        pygame.draw.rect(screen, (20, 13, 8), (bx, by, pw, ph), border_radius=6)
        pygame.draw.rect(screen, (196, 120, 70), (bx, by, pw, ph), 2, border_radius=6)

        title = self.font_lg.render(t('inn_title'), True, (240, 180, 120))
        screen.blit(title, (bx + (pw - title.get_width()) // 2, by + 12))
        gold_s = self.font_sm.render(t('shop_gold', player.gold), True, GOLD_COLOR)
        screen.blit(gold_s, (bx + pw - gold_s.get_width() - 14, by + 50))

        rows = [
            (t('inn_rest', rest_cost), (150, 230, 150)),
            (t('inn_food_already') if getattr(player, 'well_fed', False)
             else t('inn_food'), (255, 205, 120)),
        ]
        y = by + 84
        for label, col in rows:
            pygame.draw.rect(screen, (34, 24, 14), (bx + 16, y - 4, pw - 32, 30),
                             border_radius=4)
            row_s = self.font_md.render(label, True, col)
            screen.blit(row_s, (bx + 28, y))
            y += 40
        hint = self.font_sm.render(t('inn_hint'), True, (150, 130, 110))
        screen.blit(hint, (bx + (pw - hint.get_width()) // 2, by + ph - 26))

    # ------------------------------------------------------------------ #
    def render_storage(self, screen, player, storage, item_data, pane, cursor,
                       capacity=30, upgrade_cost=None, carried_groups=None):
        """개인 창고(상자) — 좌: 소지품 / 우: 영구 창고 2패널."""
        from core.lang import localized_name
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        screen.blit(ov, (0, 0))

        pw, ph = 720, 440
        bx, by = W // 2 - pw // 2, H // 2 - ph // 2
        pygame.draw.rect(screen, (16, 12, 8), (bx, by, pw, ph), border_radius=6)
        pygame.draw.rect(screen, (150, 110, 60), (bx, by, pw, ph), 2, border_radius=6)

        title = self.font_lg.render(t('storage_title'), True, (235, 190, 120))
        screen.blit(title, (bx + (pw - title.get_width()) // 2, by + 10))
        hint = self.font_sm.render(t('storage_hint'), True, (150, 140, 120))
        screen.blit(hint, (bx + (pw - hint.get_width()) // 2, by + ph - 24))
        if upgrade_cost is not None:
            up_s = self.font_sm.render(t('storage_upgrade_hint', upgrade_cost),
                                       True, (230, 190, 110))
            screen.blit(up_s, (bx + (pw - up_s.get_width()) // 2, by + ph - 42))

        from entities.item import Item as _Item

        def _dur_tag(cur, mx):
            if mx <= 0 or cur >= mx:
                return ''
            return f' 〈{max(0, cur)}/{mx}〉' if cur > 0 else ' ' + t('broken_tag')

        if carried_groups is None:
            carried_groups = [{'item': it, 'count': 1} for it in player.inventory]
        col_w = pw // 2 - 24
        panes = [
            (t('storage_carried', len(player.inventory), player.max_inventory),
             [(g['item'].name + (f'  ×{g["count"]}' if g['count'] > 1 else ''),
               g['item'].enhance_level,
               _dur_tag(g['item'].durability, g['item'].max_durability))
              for g in carried_groups]),
            (t('storage_stored', len(storage), capacity),
             [(localized_name(item_data.get(e.get('key', ''), {'name': e.get('key', '?')}))
               + (f'  ×{e.get("count", 1)}' if e.get('count', 1) > 1 else ''),
               e.get('enhance_level', 0),
               _dur_tag(e.get('durability', 10**9),
                        _Item.calc_max_durability(item_data.get(e.get('key', ''), {}))))
              for e in storage]),
        ]
        for pi, (header, rows) in enumerate(panes):
            px = bx + 16 + pi * (col_w + 16)
            active = (pi == pane)
            hdr_col = (255, 220, 130) if active else (140, 130, 110)
            pygame.draw.rect(screen, (30, 24, 14) if active else (22, 18, 12),
                             (px, by + 44, col_w, ph - 84), border_radius=4)
            if active:
                pygame.draw.rect(screen, (220, 170, 80),
                                 (px, by + 44, col_w, ph - 84), 1, border_radius=4)
            h_s = self.font_md.render(header, True, hdr_col)
            screen.blit(h_s, (px + 8, by + 50))
            # 목록 (커서 주변 스크롤)
            vis = 14
            start = 0
            if active and cursor >= vis:
                start = cursor - vis + 1
            y = by + 74
            for i in range(start, min(len(rows), start + vis)):
                name, enh, dur = rows[i]
                label = (f'{name} [+{enh}]' if enh else name) + dur
                sel = active and i == cursor
                if sel:
                    pygame.draw.rect(screen, (70, 52, 24),
                                     (px + 4, y - 2, col_w - 8, 18), border_radius=3)
                row_s = self.font_sm.render(label, True,
                                            (255, 240, 200) if sel else (190, 180, 160))
                screen.blit(row_s, (px + 10, y))
                y += 19
            if not rows:
                empty = self.font_sm.render(t('inv_empty'), True, (110, 100, 90))
                screen.blit(empty, (px + 10, by + 78))

    def render_enhance(self, screen, player, cursor, flash_result=None,
                       mode='stone', cost_fn=None):
        """장비 강화 오버레이 — P키(강화석) / 대장장이(mode='gold')."""
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        screen.blit(ov, (0, 0))

        pw, ph = 460, 404
        bx = W // 2 - pw // 2
        by = H // 2 - ph // 2

        # 창 테두리 플래시 (성공=금색, 실패=빨강)
        now_ms = pygame.time.get_ticks()
        border_col = (80, 120, 180)
        if flash_result is not None:
            elapsed = now_ms - flash_result[1]
            fade = max(0.0, 1.0 - elapsed / 500)
            if fade > 0:
                if flash_result[0] == 'success':
                    border_col = (int(80 + 175 * fade), int(120 + 95 * fade), int(180 - 130 * fade))
                else:
                    border_col = (int(80 + 175 * fade), int(120 - 100 * fade), int(180 - 150 * fade))

        pygame.draw.rect(screen, (10, 14, 28), (bx, by, pw, ph), border_radius=6)
        pygame.draw.rect(screen, border_col, (bx, by, pw, ph), 2, border_radius=6)

        smith = (mode == 'gold')
        title = self.font_lg.render(t('smith_title') if smith else t('enh_title'),
                                    True, (255, 190, 110) if smith else (160, 210, 255))
        screen.blit(title, (bx + (pw - title.get_width()) // 2, by + 8))

        # 자원 표시는 제목과 겹치지 않게 별도 줄
        if smith:
            res_txt = t('shop_gold', player.gold)
            _slots = ['head', 'body', 'weapon', 'off_hand', 'accessory', 'feet']
            cur_item = player.equipment.get(_slots[cursor]) if cursor < len(_slots) else None
            if cur_item and cost_fn:
                res_txt += f'   ({t("smith_cost", cost_fn(cur_item))})'
            stone_s = self.font_sm.render(res_txt, True, (255, 205, 90))
        else:
            stone_s = self.font_sm.render(t('enh_stones', player.enhance_stones),
                                          True, (160, 210, 255))
        screen.blit(stone_s, (bx + pw - stone_s.get_width() - 14, by + 42))

        pygame.draw.line(screen, (50, 80, 120), (bx+12, by+58), (bx+pw-12, by+58))

        _SLOT_ORDER = ['head', 'body', 'weapon', 'off_hand', 'accessory', 'feet']
        _SLOT_NAMES = {'head': t('slot_head_s'), 'body': t('slot_body_s'), 'weapon': t('slot_wpn_s'),
                       'off_hand': t('slot_off_s'), 'accessory': t('slot_acc_s'), 'feet': t('slot_feet_s')}
        _STAT_LABEL = {'head': t('enh_stat_head'), 'body': t('enh_stat_body'), 'weapon': t('enh_stat_wpn'),
                       'off_hand': t('enh_stat_off'), 'accessory': t('enh_stat_acc'), 'feet': t('enh_stat_feet')}
        _RATES = [100,100,100,100,100,100,80,80,80,60,60,60,40,40,40,20,20,20]

        y = by + 66
        for i, slot in enumerate(_SLOT_ORDER):
            item = player.equipment.get(slot)
            selected = (i == cursor)

            # 행 플래시 계산
            row_flash_type = None
            row_fade = 0.0
            if flash_result is not None and flash_result[2] == i:
                elapsed = now_ms - flash_result[1]
                row_fade = max(0.0, 1.0 - elapsed / 500)
                if row_fade > 0:
                    row_flash_type = flash_result[0]

            if row_flash_type == 'success':
                f = row_fade
                row_bg = (int(18 + 50 * f), int(30 + 80 * f), int(55 - 20 * f))
                edge_col = (int(255 * f), int(215 * f), 0)
            elif row_flash_type == 'fail':
                f = row_fade
                row_bg = (int(10 + 80 * f), int(14 - 5 * f), int(28 - 10 * f))
                edge_col = (int(220 * f), int(30 * f), int(30 * f))
            elif selected:
                row_bg = (18, 30, 55)
                edge_col = (80, 130, 200)
            else:
                row_bg = (10, 14, 28)
                edge_col = None

            pygame.draw.rect(screen, row_bg, (bx+8, y-2, pw-16, 34), border_radius=3)
            if edge_col:
                pygame.draw.rect(screen, edge_col, (bx+8, y-2, pw-16, 34), 1, border_radius=3)

            slot_s = self.font_sm.render(_SLOT_NAMES[slot], True, (100, 130, 170))
            screen.blit(slot_s, (bx+14, y+2))

            if item:
                enh = item.enhance_level
                enh_col = (255, 220, 80) if enh >= 10 else (120, 200, 255) if enh > 0 else (200, 200, 220)
                name_s = self.font_sm.render(f"{item.name}  [+{enh}]", True, enh_col)
                screen.blit(name_s, (bx+80, y+2))
                stat_s = self.font_sm.render(_STAT_LABEL.get(slot, ''), True, (90, 160, 90))
                screen.blit(stat_s, (bx+80, y+16))
                # 내구도 바 + 수치 (방어구) — 파손 시 붉은 태그
                if getattr(item, 'max_durability', 0) > 0:
                    dur_frac = item.durability / item.max_durability
                    dbx = bx + 228
                    pygame.draw.rect(screen, (40, 30, 30), (dbx, y + 19, 64, 5))
                    if dur_frac > 0:
                        d_col = ((90, 200, 90) if dur_frac > 0.5 else
                                 (230, 180, 60) if dur_frac > 0.25 else (230, 80, 60))
                        pygame.draw.rect(screen, d_col,
                                         (dbx, y + 19, max(1, int(64 * dur_frac)), 5))
                        num_s = self.font_sm.render(
                            f'{item.durability}/{item.max_durability}', True, d_col)
                        screen.blit(num_s, (dbx, y + 2))
                    else:
                        broken_s = self.font_sm.render(t('broken_tag'), True, (255, 80, 60))
                        screen.blit(broken_s, (dbx, y + 2))
                if enh < 18:
                    rate = _RATES[enh]
                    rate_col = (80, 220, 80) if rate == 100 else (220, 180, 60) if rate >= 60 else (220, 80, 80)
                    rate_s = self.font_sm.render(t('enh_rate', rate), True, rate_col)
                    screen.blit(rate_s, (bx + pw - rate_s.get_width() - 14, y+2))
                    cost_s = self.font_sm.render(t('enh_cost'), True, (140, 170, 220))
                    screen.blit(cost_s, (bx + pw - cost_s.get_width() - 14, y+16))
                else:
                    max_s = self.font_sm.render("MAX", True, (255, 200, 50))
                    screen.blit(max_s, (bx + pw - max_s.get_width() - 14, y+8))
            else:
                empty_s = self.font_sm.render(t('enh_empty'), True, (50, 55, 75))
                screen.blit(empty_s, (bx+80, y+9))

            y += 38

        if smith:
            rep_s = self.font_sm.render(t('smith_repair_hint'), True, (200, 160, 90))
            screen.blit(rep_s, (bx + (pw - rep_s.get_width()) // 2, by + ph - 40))
        guide_s = self.font_sm.render(t('enh_hint'), True, (70, 90, 130))
        screen.blit(guide_s, (bx + (pw - guide_s.get_width()) // 2, by + ph - 24))

    # ------------------------------------------------------------------ #
    def render_skillbook(self, screen, skill_levels: dict, unlocked_combos: set,
                         skill_books: set, skill_points: int, cursor: int,
                         player_level: int,
                         equipped_skills=None,
                         equip_mode=False, equip_target_slot=None,
                         equip_skill_id=None, equip_cursor=0,
                         skill_enchants=None, arcane_window=False):
        """스킬 도감 오버레이 (K키)."""
        # lazy import to avoid circular imports
        try:
            from core.skills import ALL_SKILL_DEFS as _ALL_SKILL_DEFS, DEFAULT_EQUIPPED as _DEFAULT_EQUIPPED
        except ImportError:
            _ALL_SKILL_DEFS = ALL_SKILL_DEFS
            _DEFAULT_EQUIPPED = DEFAULT_EQUIPPED

        # Try to import SKILL_SP_COST; fall back to default if not yet defined
        try:
            from core.skills import SKILL_SP_COST
        except ImportError:
            SKILL_SP_COST = {'W': [5, 10], 'A': [5, 10], 'S': [5, 10], 'D': [5, 10]}

        try:
            from core.skills import ENCHANT_DEFS as _ENCHANT_DEFS, ENCHANT_TYPES as _ENCHANT_TYPES, ENCHANT_MAX_LEVEL as _ENCHANT_MAX
        except ImportError:
            _ENCHANT_DEFS = {}; _ENCHANT_TYPES = (); _ENCHANT_MAX = 3

        _enc = skill_enchants or {}

        _eq = equipped_skills or _DEFAULT_EQUIPPED

        W, H = WINDOW_WIDTH, WINDOW_HEIGHT

        # ── 반투명 배경 오버레이 ────────────────────────────────────────
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # ── 창 레이아웃 ─────────────────────────────────────────────────
        bw, bh = 720, 520
        bx = W // 2 - bw // 2
        by = H // 2 - bh // 2

        WIN_BG      = (8, 12, 24)
        WIN_BORDER  = (60, 100, 160)
        HDR_COLOR   = (60, 80, 110)
        SEL_BG      = (20, 35, 65)
        SEL_BORDER  = (80, 130, 210)
        LOCKED_COL  = (55, 60, 75)
        DIVIDER_COL = (40, 60, 100)
        GOLD        = (255, 215, 0)
        SP_OK       = (160, 220, 255)
        SP_NO       = (220, 80, 80)

        LEFT_W  = 238   # left panel width
        RIGHT_X = bx + LEFT_W + 8   # right panel start x
        RIGHT_W = bw - LEFT_W - 8

        pygame.draw.rect(screen, WIN_BG, (bx, by, bw, bh))
        pygame.draw.rect(screen, WIN_BORDER, (bx, by, bw, bh), 2)

        # ── 상단 헤더 바 ─────────────────────────────────────────────────
        HEADER_H = 34
        pygame.draw.rect(screen, (12, 18, 36), (bx, by, bw, HEADER_H))
        pygame.draw.line(screen, WIN_BORDER, (bx, by + HEADER_H), (bx + bw, by + HEADER_H))

        title_s = self.font_lg.render(t('sb_title'), True, (180, 220, 255))
        screen.blit(title_s, (bx + 14, by + (HEADER_H - title_s.get_height()) // 2))

        sp_col = SP_OK if skill_points > 0 else (100, 120, 150)
        sp_s = self.font_md.render(t('sb_sp', skill_points), True, sp_col)
        screen.blit(sp_s, (bx + bw - sp_s.get_width() - 14,
                            by + (HEADER_H - sp_s.get_height()) // 2))

        # ── 하단 힌트 바 ─────────────────────────────────────────────────
        FOOTER_H = 26
        footer_y = by + bh - FOOTER_H
        pygame.draw.line(screen, DIVIDER_COL, (bx, footer_y), (bx + bw, footer_y))
        pygame.draw.rect(screen, (10, 15, 28), (bx, footer_y, bw, FOOTER_H))
        if arcane_window:
            _hint_text = t('arcane_ready')
            _hint_col  = (255, 200, 80)
        elif equip_mode:
            _hint_text = t('sb_equip_hint')
            _hint_col  = (200, 140, 50)
        else:
            _hint_text = t('sb_hint')
            _hint_col  = (70, 90, 120)
        hint_s = self.font_sm.render(_hint_text, True, _hint_col)
        screen.blit(hint_s, (bx + (bw - hint_s.get_width()) // 2,
                              footer_y + (FOOTER_H - hint_s.get_height()) // 2))

        # ── 패널 세로 구분선 ─────────────────────────────────────────────
        div_x = bx + LEFT_W
        pygame.draw.line(screen, DIVIDER_COL,
                         (div_x, by + HEADER_H), (div_x, footer_y))

        # ── 커서용 아이템 목록 빌드 ──────────────────────────────────────
        # Section 1: 4 slot rows (W/A/S/D)
        SLOT_ROWS = ['W', 'A', 'S', 'D']
        # Section 2: available skills from ALL_SKILL_DEFS unlocked by player_level
        avail_skills = [
            sid for sid, sdef in _ALL_SKILL_DEFS.items()
            if player_level >= sdef.get('level_req', 1)
        ] if _ALL_SKILL_DEFS else []
        # total items = 4 slots + N avail skills
        total_items = len(SLOT_ROWS) + len(avail_skills)
        cursor = max(0, min(cursor, total_items - 1))
        # pick_slot 모드: equip_cursor는 슬롯 인덱스 (0-3)
        # pick_skill 모드: equip_cursor는 avail_skills 인덱스
        if equip_mode and equip_skill_id is not None:
            equip_cursor = max(0, min(equip_cursor, 3))
        else:
            equip_cursor = max(0, min(equip_cursor, len(avail_skills) - 1)) if avail_skills else 0

        # Determine what is selected for right panel display
        if cursor < len(SLOT_ROWS):
            sel_mode = 'slot'
            sel_slot = SLOT_ROWS[cursor]
            sel_skill_id = _eq.get(sel_slot)
        else:
            sel_mode = 'avail'
            avail_idx = cursor - len(SLOT_ROWS)
            sel_skill_id = avail_skills[avail_idx] if avail_idx < len(avail_skills) else None
            sel_slot = None

        # pick_skill 모드에서만 equip_cursor로 스킬 결정 (pick_slot 모드면 파라미터 그대로 사용)
        if equip_mode and equip_skill_id is None and avail_skills:
            equip_skill_id = avail_skills[equip_cursor] if equip_cursor < len(avail_skills) else None

        # reverse-map: skill_id -> slot it is equipped in
        equipped_in = {v: k for k, v in _eq.items()}

        # ── 왼쪽 패널 스크롤 클립 영역 ───────────────────────────────────
        content_y0 = by + HEADER_H + 4
        content_y1 = footer_y - 2
        LEFT_CLIP = pygame.Rect(bx, content_y0, LEFT_W, content_y1 - content_y0)

        ITEM_H = 26
        GROUP_H = 20

        # ── 왼쪽 패널 그리기 ─────────────────────────────────────────────
        screen.set_clip(LEFT_CLIP)
        lx = bx + 8
        ly = content_y0 + 4

        # equip_mode banner
        if equip_mode:
            if equip_skill_id:
                # pick_slot 모드: 어느 슬롯에 장착?
                _sn = (_ALL_SKILL_DEFS.get(equip_skill_id) or {}).get('name', equip_skill_id)
                banner_s = self.font_sm.render(
                    t('sb_pick_slot_banner', _sn), True, (255, 200, 80))
            elif equip_target_slot:
                # pick_skill 모드: 슬롯에 장착할 스킬 선택
                banner_s = self.font_sm.render(
                    t('sb_pick_skill_banner', equip_target_slot), True, (255, 160, 50))
            else:
                banner_s = None
            if banner_s:
                screen.blit(banner_s, (lx, ly + 2))
                ly += GROUP_H + 2

        # ─ Section 1: 장착 슬롯 ─
        gh_s = self.font_sm.render(t('sb_slot_section'), True, HDR_COLOR)
        screen.blit(gh_s, (lx, ly + (GROUP_H - gh_s.get_height()) // 2))
        ly += GROUP_H

        for slot_idx, slot in enumerate(SLOT_ROWS):
            item_idx = slot_idx
            is_sel       = (not equip_mode) and (item_idx == cursor)
            is_slot_pick = equip_mode and equip_skill_id and (slot_idx == equip_cursor)
            row_rect = pygame.Rect(bx + 2, ly, LEFT_W - 4, ITEM_H)
            sid = _eq.get(slot)
            sdef_slot = _ALL_SKILL_DEFS.get(sid) if sid else None
            locked_slot = sdef_slot and player_level < sdef_slot.get('level_req', 1)

            if is_slot_pick:
                pygame.draw.rect(screen, (40, 35, 10), row_rect)
                pygame.draw.rect(screen, (255, 200, 50), row_rect, 2)
            elif is_sel:
                pygame.draw.rect(screen, SEL_BG, row_rect)
                pygame.draw.rect(screen, SEL_BORDER, row_rect, 1)

            if locked_slot:
                text_col = LOCKED_COL
            elif is_slot_pick:
                text_col = (255, 220, 100)
            elif is_sel:
                text_col = (220, 240, 255)
            else:
                text_col = (160, 180, 210)

            if sdef_slot:
                lvl_s = skill_levels.get(sid, 1)
                lv_str = f' Lv{lvl_s}' if lvl_s > 1 else ''
                row_text = f'[{slot}] {sdef_slot["name"]}{lv_str}'
            elif sid:
                row_text = f'[{slot}] {sid}'
            else:
                row_text = f'[{slot}] ---'

            row_s = self.font_sm.render(row_text, True, text_col)
            screen.blit(row_s, (lx, ly + (ITEM_H - row_s.get_height()) // 2))

            if is_slot_pick:
                # ← 선택 표시
                pick_s = self.font_sm.render(t('sb_slot_here'), True, (255, 200, 50))
                screen.blit(pick_s, (bx + LEFT_W - pick_s.get_width() - 6,
                                     ly + (ITEM_H - pick_s.get_height()) // 2))
            elif is_sel and not equip_mode:
                chg_s = self.font_sm.render(t('sb_slot_change'), True, (100, 200, 255))
                screen.blit(chg_s, (bx + LEFT_W - chg_s.get_width() - 6,
                                    ly + (ITEM_H - chg_s.get_height()) // 2))
            ly += ITEM_H

        ly += 6

        # ─ Section 2: 보유 스킬 ─
        gh2_s = self.font_sm.render(t('sb_avail_section'), True, HDR_COLOR)
        screen.blit(gh2_s, (lx, ly + (GROUP_H - gh2_s.get_height()) // 2))
        ly += GROUP_H

        for avail_idx2, sid2 in enumerate(avail_skills):
            item_idx2 = len(SLOT_ROWS) + avail_idx2
            is_sel2 = (not equip_mode) and (item_idx2 == cursor)
            is_equip_sel = equip_mode and (not equip_skill_id) and (avail_idx2 == equip_cursor)
            row_rect2 = pygame.Rect(bx + 2, ly, LEFT_W - 4, ITEM_H)
            sdef2 = _ALL_SKILL_DEFS.get(sid2, {})

            if is_sel2 or is_equip_sel:
                sel_bg2 = (20, 45, 25) if is_equip_sel else SEL_BG
                sel_bd2 = (80, 200, 80) if is_equip_sel else SEL_BORDER
                pygame.draw.rect(screen, sel_bg2, row_rect2)
                pygame.draw.rect(screen, sel_bd2, row_rect2, 1)

            if is_sel2 or is_equip_sel:
                text_col2 = (200, 255, 200) if is_equip_sel else (220, 240, 255)
            else:
                text_col2 = (160, 180, 210)

            lvl2 = skill_levels.get(sid2, 1)
            lv_str2 = f' Lv{lvl2}' if lvl2 > 1 else ''
            nm2 = sdef2.get('name', sid2)
            row_text2 = f'{nm2}{lv_str2}'

            row_s2 = self.font_sm.render(row_text2, True, text_col2)
            screen.blit(row_s2, (lx, ly + (ITEM_H - row_s2.get_height()) // 2))

            # show [slot] badge if equipped
            if sid2 in equipped_in:
                badge_slot = equipped_in[sid2]
                badge_s = self.font_sm.render(f'[{badge_slot}]', True, (180, 220, 100))
                screen.blit(badge_s, (bx + LEFT_W - badge_s.get_width() - 6,
                                      ly + (ITEM_H - badge_s.get_height()) // 2))
            ly += ITEM_H

        screen.set_clip(None)

        # ── 오른쪽 패널 ──────────────────────────────────────────────────
        rx = RIGHT_X + 6
        ry = content_y0 + 8
        rw = bw - (rx - bx) - 10

        # Helper: render detail for a skill from ALL_SKILL_DEFS
        def _render_all_skill_detail(sid, slot_label=None):
            nonlocal ry
            sdef_r = _ALL_SKILL_DEFS.get(sid)
            if not sdef_r:
                no_s = self.font_sm.render(f'({sid})', True, LOCKED_COL)
                screen.blit(no_s, (rx, ry))
                return
            lvl_r = skill_levels.get(sid, 1)
            sk_col = sdef_r.get('color', WHITE)
            slot_info = f'  [{slot_label}]' if slot_label else ''
            ttl_s = self.font_lg.render(f'{sdef_r["name"]}{slot_info}', True, sk_col)
            screen.blit(ttl_s, (rx, ry))
            ry += ttl_s.get_height() + 4

            usage_text = sdef_r.get('usage', sdef_r.get('desc', ''))
            if usage_text:
                u_s = self.font_sm.render(usage_text, True, (140, 160, 190))
                screen.blit(u_s, (rx, ry))
                ry += u_s.get_height() + 10

            pygame.draw.line(screen, DIVIDER_COL, (rx, ry), (rx + rw - 4, ry))
            ry += 4

            upgrades = sdef_r.get('upgrades', [])
            TABLE_ROW_H = 20
            col_lv_x  = rx
            col_eff_x = rx + 36
            col_cd_x  = rx + rw - 70
            hdr_lv  = self.font_sm.render(t('sb_lv_header'),  True, (100, 120, 150))
            hdr_eff = self.font_sm.render(t('sb_eff_header'), True, (100, 120, 150))
            hdr_cd  = self.font_sm.render(t('sb_cd_header'),  True, (100, 120, 150))
            screen.blit(hdr_lv,  (col_lv_x,  ry))
            screen.blit(hdr_eff, (col_eff_x, ry))
            screen.blit(hdr_cd,  (col_cd_x,  ry))
            ry += hdr_lv.get_height() + 2
            pygame.draw.line(screen, DIVIDER_COL, (rx, ry), (rx + rw - 4, ry))
            ry += 3

            for li, upg in enumerate(upgrades):
                row_lv  = li + 1
                is_curr = (row_lv == lvl_r)
                is_lock = (row_lv > lvl_r)
                eff_text = upg.get('level_desc', f'{upg.get("cd_ms", 0)//1000:.0f}s')
                cd_text  = f'{upg.get("cd_ms", 0) / 1000:.1f}s'
                if is_curr:
                    row_col  = GOLD
                    lv_label = f'{row_lv}★'
                    pygame.draw.rect(screen, (30, 24, 4), (rx - 2, ry - 1, rw, TABLE_ROW_H))
                elif is_lock:
                    row_col  = LOCKED_COL
                    lv_label = str(row_lv)
                else:
                    row_col  = (130, 160, 190)
                    lv_label = str(row_lv)
                lv_s  = self.font_sm.render(lv_label, True, row_col)
                eff_s = self.font_sm.render(eff_text,  True, row_col)
                cd_s  = self.font_sm.render(cd_text,   True, row_col)
                screen.blit(lv_s,  (col_lv_x,  ry + (TABLE_ROW_H - lv_s.get_height())  // 2))
                screen.blit(eff_s, (col_eff_x, ry + (TABLE_ROW_H - eff_s.get_height()) // 2))
                screen.blit(cd_s,  (col_cd_x,  ry + (TABLE_ROW_H - cd_s.get_height())  // 2))
                ry += TABLE_ROW_H

            pygame.draw.line(screen, DIVIDER_COL, (rx, ry + 2), (rx + rw - 4, ry + 2))
            ry += 12

            # upgrade section
            if lvl_r < SKILL_MAX_LEVEL:
                sp_cost_list = sdef_r.get('sp_cost', SKILL_SP_COST.get(sid, [5, 10]))
                if isinstance(sp_cost_list, list):
                    cost_r = sp_cost_list[lvl_r - 1] if lvl_r - 1 < len(sp_cost_list) else 10
                else:
                    cost_r = int(sp_cost_list)
                can_upg = skill_points >= cost_r
                sp_c = SP_OK if can_upg else SP_NO
                upg_s = self.font_md.render(
                    t('sb_upgrade_line', lvl_r, lvl_r + 1, cost_r), True, sp_c)
                screen.blit(upg_s, (rx, ry))
                ry += upg_s.get_height() + 6
                btn_col = (80, 160, 80) if can_upg else (50, 55, 60)
                btn_brd = (120, 220, 120) if can_upg else (70, 75, 80)
                btn_tc  = (180, 255, 180) if can_upg else (80, 85, 90)
                btn_rect = pygame.Rect(rx, ry, 170, 28)
                pygame.draw.rect(screen, btn_col, btn_rect, border_radius=3)
                pygame.draw.rect(screen, btn_brd, btn_rect, 1, border_radius=3)
                btn_s = self.font_sm.render(t('sb_upgrade_btn'), True, btn_tc)
                screen.blit(btn_s, (btn_rect.centerx - btn_s.get_width() // 2,
                                    btn_rect.centery - btn_s.get_height() // 2))
                ry += 34
            else:
                max_s = self.font_md.render(t('sb_max_done'), True, GOLD)
                screen.blit(max_s, (rx, ry))
                ry += max_s.get_height() + 4

        # Helper: render enchant panel for a skill
        def _render_enchants(sid):
            nonlocal ry
            if not _ENCHANT_DEFS or not _ENCHANT_TYPES:
                return
            enc = _enc.get(sid, {})
            pygame.draw.line(screen, DIVIDER_COL, (rx, ry), (rx + rw - 4, ry))
            ry += 4
            hdr_s = self.font_sm.render(t('enc_header'), True, (100, 120, 150))
            screen.blit(hdr_s, (rx, ry)); ry += hdr_s.get_height() + 3

            for ei, etype in enumerate(_ENCHANT_TYPES):
                edef  = _ENCHANT_DEFS.get(etype, {})
                ename = t(f'enc_type_{etype}')
                ecol  = edef.get('color', WHITE)
                cur   = enc.get(etype, 0)
                costs = edef.get('sp_cost', [5, 10, 20])
                if cur < _ENCHANT_MAX:
                    cost  = costs[cur] if cur < len(costs) else 20
                    canup = skill_points >= cost
                    lv_s  = self.font_sm.render(
                        f'[{ei+1}] {ename}  Lv{cur}/{_ENCHANT_MAX}', True,
                        ecol if cur > 0 else (80, 80, 100))
                    cost_s = self.font_sm.render(
                        f'SP {cost}', True,
                        (100, 220, 100) if canup else (160, 80, 80))
                    screen.blit(lv_s,  (rx, ry))
                    screen.blit(cost_s, (rx + rw - cost_s.get_width() - 4, ry))
                else:
                    lv_s = self.font_sm.render(
                        f'[{ei+1}] {ename}  MAX', True, ecol)
                    screen.blit(lv_s, (rx, ry))
                ry += lv_s.get_height() + 2

        # Determine which skill to show in the right panel
        if equip_mode:
            if equip_skill_id:
                # pick_slot 모드: 장착하려는 스킬 상세 표시
                _render_all_skill_detail(equip_skill_id)
                hint_eq = self.font_sm.render(t('sb_equip_slot_hint'), True, (255, 200, 80))
            elif avail_skills and equip_cursor < len(avail_skills):
                # pick_skill 모드: 선택 중인 스킬 상세 표시
                _render_all_skill_detail(avail_skills[equip_cursor])
                hint_eq = self.font_sm.render(t('sb_equip_skill_hint'), True, (255, 180, 50))
            else:
                hint_eq = self.font_sm.render(t('sb_equip_confirm'), True, (255, 180, 50))
            screen.blit(hint_eq, (rx, content_y1 - hint_eq.get_height() - 4))
        elif sel_mode == 'slot':
            # cursor on a slot row: show equipped skill detail
            _e_sid = _eq.get(sel_slot)
            if _e_sid and (_ALL_SKILL_DEFS.get(_e_sid) or True):
                if _ALL_SKILL_DEFS.get(_e_sid):
                    _render_all_skill_detail(_e_sid, slot_label=sel_slot)
                    _render_enchants(_e_sid)
                else:
                    # legacy fallback for basic skills
                    legacy = next((s for s in SKILL_DEFS if s['key'] == sel_slot), None)
                    if legacy:
                        lvl  = skill_levels.get(sel_slot, 1)
                        ttl_s = self.font_lg.render(
                            f'{legacy["name"]}  {t("sb_key_legacy", sel_slot)}', True, legacy['color'])
                        screen.blit(ttl_s, (rx, ry)); ry += ttl_s.get_height() + 4
                        usage_text = legacy.get('usage', legacy.get('desc', ''))
                        if usage_text:
                            u_s = self.font_sm.render(usage_text, True, (140, 160, 190))
                            screen.blit(u_s, (rx, ry)); ry += u_s.get_height() + 10
                        pygame.draw.line(screen, DIVIDER_COL, (rx, ry), (rx+rw-4, ry)); ry += 4
                        TABLE_ROW_H = 20
                        col_lv_x, col_eff_x, col_cd_x = rx, rx+36, rx+rw-70
                        for li in range(SKILL_MAX_LEVEL):
                            row_lv = li + 1
                            upg = SKILL_UPGRADES[sel_slot][li]
                            eff_text = _fmt_skill_stats(sel_slot, upg)
                            cd_text  = f'{upg["cd_ms"]/1000:.1f}s'
                            is_curr = row_lv == lvl; is_lock = row_lv > lvl
                            row_col = GOLD if is_curr else (LOCKED_COL if is_lock else (130,160,190))
                            lv_label = f'{row_lv}★' if is_curr else str(row_lv)
                            if is_curr: pygame.draw.rect(screen, (30,24,4), (rx-2,ry-1,rw,TABLE_ROW_H))
                            lv_s=self.font_sm.render(lv_label,True,row_col)
                            eff_s=self.font_sm.render(eff_text,True,row_col)
                            cd_s=self.font_sm.render(cd_text,True,row_col)
                            screen.blit(lv_s,(col_lv_x,ry+(TABLE_ROW_H-lv_s.get_height())//2))
                            screen.blit(eff_s,(col_eff_x,ry+(TABLE_ROW_H-eff_s.get_height())//2))
                            screen.blit(cd_s,(col_cd_x,ry+(TABLE_ROW_H-cd_s.get_height())//2))
                            ry += TABLE_ROW_H
                        pygame.draw.line(screen, DIVIDER_COL,(rx,ry+2),(rx+rw-4,ry+2)); ry+=12
                        if lvl < SKILL_MAX_LEVEL:
                            cost_list2 = SKILL_SP_COST.get(sel_slot, [5,10])
                            cost2 = cost_list2[lvl-1] if lvl-1<len(cost_list2) else 10
                            can_upg2 = skill_points >= cost2
                            sp_c2 = SP_OK if can_upg2 else SP_NO
                            upg_s2=self.font_md.render(t('sb_upgrade_line',lvl,lvl+1,cost2),True,sp_c2)
                            screen.blit(upg_s2,(rx,ry)); ry+=upg_s2.get_height()+6
                            bc=(80,160,80) if can_upg2 else (50,55,60)
                            bb=(120,220,120) if can_upg2 else (70,75,80)
                            btc=(180,255,180) if can_upg2 else (80,85,90)
                            br2=pygame.Rect(rx,ry,170,28)
                            pygame.draw.rect(screen,bc,br2,border_radius=3)
                            pygame.draw.rect(screen,bb,br2,1,border_radius=3)
                            bs2=self.font_sm.render(t('sb_upgrade_btn'),True,btc)
                            screen.blit(bs2,(br2.centerx-bs2.get_width()//2,br2.centery-bs2.get_height()//2))
                        else:
                            mx_s=self.font_md.render(t('sb_max_done'),True,GOLD)
                            screen.blit(mx_s,(rx,ry))
            else:
                empty_s = self.font_sm.render(t('sb_slot_empty', sel_slot), True, LOCKED_COL)
                screen.blit(empty_s, (rx, ry))
        else:
            # cursor on an available skill
            if sel_skill_id:
                _render_all_skill_detail(sel_skill_id)
                _render_enchants(sel_skill_id)

    # ------------------------------------------------------------------ #
    def render_equipment(self, screen, player, sel, player_spr=None, mouse_pos=(0, 0)):
        """장비 장착 화면 — 페이퍼돌 레이아웃."""
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        screen.blit(ov, (0, 0))

        pw, ph = 520, 516
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
            ('feet',      'slot_feet',      (160, 120, 220), (-SW//2, +190)),
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
        # accessory ↕ feet
        feet_top = (char_cx, char_cy + 190)
        pygame.draw.line(screen, line_col, (char_cx, char_cy + 122 + SH), feet_top, 1)
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
            is_hov = pygame.Rect(sx, sy, SW, SH).collidepoint(mouse_pos) and not is_sel

            bg_col = (48, 44, 82) if is_sel else ((28, 26, 52) if is_hov else (18, 18, 38))
            bd_col = GOLD_COLOR   if is_sel else (WHITE        if is_hov else slot_col)
            bd_w   = 2 if is_sel else 1
            pygame.draw.rect(screen, bg_col, (sx, sy, SW, SH), border_radius=4)
            pygame.draw.rect(screen, bd_col, (sx, sy, SW, SH), bd_w, border_radius=4)

            lbl_col = GOLD_COLOR if is_sel else slot_col
            lbl_s   = self.font_sm.render(t(label_key), True, lbl_col)
            screen.blit(lbl_s, (sx + (SW - lbl_s.get_width()) // 2, sy + 4))

            if item:
                ico = 16 if USE_MC_ITEMS else 10
                if USE_MC_ITEMS:
                    draw_mc_item(screen, sx + 3, sy + SH - ico - 3, ico,
                                 item.item_type, item.color,
                                 key=getattr(item, 'key', None))
                else:
                    pygame.draw.rect(screen, item.color, (sx + 5, sy + SH - ico - 5, ico, ico), border_radius=2)
                nm = item.name if len(item.name) <= 8 else item.name[:7] + '…'
                broken = getattr(item, 'broken', False)
                nm_s = self.font_sm.render(f"+{item.value} {nm}", True,
                                           (255, 80, 60) if broken
                                           else (WHITE if is_sel else LIGHT_GRAY))
                screen.blit(nm_s, (sx + 17, sy + SH - nm_s.get_height() - 4))
                # 내구도 바 + 수치 (방어구) — 라벨 아래 줄
                if getattr(item, 'max_durability', 0) > 0:
                    frac = item.durability / item.max_durability
                    dbw = SW - 46
                    dby = sy + 20
                    pygame.draw.rect(screen, (34, 28, 28), (sx + 6, dby, dbw, 4))
                    if frac > 0:
                        d_col = ((90, 200, 90) if frac > 0.5 else
                                 (230, 180, 60) if frac > 0.25 else (230, 80, 60))
                        pygame.draw.rect(screen, d_col,
                                         (sx + 6, dby, max(1, int(dbw * frac)), 4))
                    dur_txt = (t('broken_tag') if broken
                               else f'{item.durability}/{item.max_durability}')
                    dur_s = self.font_sm.render(
                        dur_txt, True,
                        (255, 80, 60) if broken else (150, 150, 130))
                    screen.blit(dur_s, (sx + 8 + dbw, dby - 5))
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

    # ------------------------------------------------------------------ #
    def render_discard_confirm(self, screen, item_name, yes_rect, no_rect,
                               mouse_pos=(0, 0)):
        """아이템 버리기 확인 대화상자."""
        W, H = WINDOW_WIDTH, WINDOW_HEIGHT
        cw = no_rect.right - yes_rect.left + 20
        ch = yes_rect.bottom - (yes_rect.top - 56) + 8
        cx = W // 2 - cw // 2
        cy = yes_rect.top - 56

        # 배경 패널 (어두운 반투명 오버레이 없이 패널만)
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        screen.blit(ov, (0, 0))

        pygame.draw.rect(screen, (14, 12, 26), (cx, cy, cw, ch), border_radius=6)
        pygame.draw.rect(screen, (180, 80, 80), (cx, cy, cw, ch), 2, border_radius=6)

        # 아이템명
        nm_s = self.font_sm.render(f"[{item_name}]", True, GOLD_COLOR)
        screen.blit(nm_s, (cx + (cw - nm_s.get_width()) // 2, cy + 10))

        # 질문 텍스트
        q_s = self.font_md.render(t('discard_confirm'), True, WHITE)
        screen.blit(q_s, (cx + (cw - q_s.get_width()) // 2, cy + 28))

        # 예 버튼
        yes_hov = yes_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (50, 120, 50) if yes_hov else (30, 70, 30),
                         yes_rect, border_radius=4)
        pygame.draw.rect(screen, (110, 210, 110) if yes_hov else (60, 130, 60),
                         yes_rect, 1, border_radius=4)
        yes_s = self.font_md.render(t('discard_yes'), True,
                                    (160, 255, 160) if yes_hov else (100, 200, 100))
        screen.blit(yes_s, (yes_rect.centerx - yes_s.get_width() // 2,
                            yes_rect.centery - yes_s.get_height() // 2))

        # 아니오 버튼
        no_hov = no_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (120, 40, 40) if no_hov else (70, 24, 24),
                         no_rect, border_radius=4)
        pygame.draw.rect(screen, (230, 80, 80) if no_hov else (140, 54, 54),
                         no_rect, 1, border_radius=4)
        no_s = self.font_md.render(t('discard_no'), True,
                                   (255, 140, 140) if no_hov else (200, 80, 80))
        screen.blit(no_s, (no_rect.centerx - no_s.get_width() // 2,
                           no_rect.centery - no_s.get_height() // 2))


# ---- helpers ----
def _bar(screen, x, y, w, h, cur, maximum, fg, bg):
    pygame.draw.rect(screen, bg, (x, y, w, h))
    if maximum > 0:
        fill = max(0, int(w * cur / maximum))
        if fill:
            pygame.draw.rect(screen, fg, (x, y, fill, h))
    pygame.draw.rect(screen, UI_BORDER, (x, y, w, h), 1)

def _fmt_skill_stats(key, stats):
    from core.lang import t as _t
    cd = stats['cd_ms'] / 1000
    if key == 'W':
        return _t('fmt_tiles', stats['tiles'], f'{cd:.1f}')
    if key == 'A':
        return _t('fmt_radius_atk', stats['radius'], int(stats['mul']*100), f'{cd:.1f}')
    if key == 'S':
        return f"HP +{int(stats['heal_pct']*100)}%  CD {cd:.1f}s"
    if key == 'D':
        return _t('fmt_mul_crit', f"{stats['mul']:.1f}", int(stats['crit']*100), f'{cd:.1f}')
    return ""

def _cx(surf, container_w):
    return (container_w - surf.get_width()) // 2

def _midy(surf, container_h):
    return (container_h - surf.get_height()) // 2

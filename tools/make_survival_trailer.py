"""Dungeon Door — 무한 생존(Endless Survival) 전용 시네마틱 트레일러.

기존 make_trailer.py 의 캡처/합성/인코딩 인프라를 재사용해, 무한 생존 모드를
헤드리스로 오토파일럿 구동하며 캡처한다.

비트: TITLE → THE HORDE → AUGMENTS(증강 드래프트) → GODLIKE(콤보 점수판)
      → SUPPLY(스테이지 보급) → OUTRO(위시리스트)

사용:  python3 tools/make_survival_trailer.py [out.mp4] [ko|en]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("DD_NO_BGM", "1")

import pygame  # noqa: E402
import make_trailer as MT  # noqa: E402  (인프라 재사용 — import 시 pygame.init 등 수행)
from make_trailer import (  # noqa: E402
    Director, render_view, cinematic, vignette, letterbox, chip, caption,
    card, flash, face_nearest, _safe, F_CAP, GOLD, WHITE, OUT_W, OUT_H, FPS, DT,
)
from core.game import Game  # noqa: E402
from core import fonts as _fonts  # noqa: E402

F_SCORE = _fonts.load_font(58, bold=True)
F_COMBO = _fonts.load_font(40, bold=True)

_LANG = "ko"
CAPS = {
    "title_sub": {"ko": "끝없는 파도 · 아수라장", "en": "Endless Waves · Pure Chaos"},
    "horde":     {"ko": "끝없이 몰려오는 군단",     "en": "The horde never stops"},
    "augment":   {"ko": "빌드를 규정하는 증강 1택", "en": "Pick a build-defining Augment"},
    "godlike":   {"ko": "콤보를 쌓아 점수를 폭발시켜라", "en": "Chain combos, erupt the score"},
    "supply":    {"ko": "버틸수록 쏟아지는 보급",   "en": "Survive longer — earn supply drops"},
    "outro_sub": {"ko": "무한 생존 · 최고 점수에 도전하라", "en": "ENDLESS SURVIVAL — Chase the top score"},
}


def L(k):
    return CAPS[k][_LANG]


def set_ui_lang(lang):
    global _LANG
    _LANG = lang if lang in ("ko", "en") else "ko"
    try:
        from core.lang import set_lang
        set_lang(_LANG)
    except Exception:
        pass


# ── 무한 생존 셋업 / 스텝 / 오토파일럿 ─────────────────────────────────────
def new_survival(cls='axeman', level=22, augs=None):
    """무한 생존 런을 헤드리스로 시작(비영속 테스트). augs=강제 시작 증강 목록."""
    g = Game()
    set_ui_lang(_LANG)   # Game()이 설정 언어로 되돌리므로 재적용(인게임 텍스트 로컬라이즈)
    g._is_test_mode = True
    g._records = {}
    g._begin_survival_run(cls, 'HERO', {'skin': 0, 'hair': 1, 'haircol': 2},
                          start_level=level, persist=False)
    # 시작 증강 자동 선택(비주얼용 강한 증강)
    for aid in (augs or ['bullet_storm']):
        if g.state == 'survival_augment':
            g._aug_choices = [aid, aid, aid]
            g._aug_cursor = 0
            g._survival_apply_augment(aid)
    g.state = 'playing'
    return g


def surv_step(g):
    """생존 한 프레임 — 웨이브/점수 갱신 후 기존 step으로 적/애니 갱신."""
    if g.state == 'playing':
        _safe(g._update_survival, DT)
    MT.step(g)
    # 플래시 포화 방지 — 잦은 콤보/마일스톤 플래시가 화면을 뿌옇게 덮지 않게 클램프
    if getattr(g, '_gold_flash_ms', 0) > 110:
        g._gold_flash_ms = 110
    if getattr(g, '_white_flash_ms', 0) > 70:
        g._white_flash_ms = 70


def _combo_mult(g):
    c = getattr(g, '_combo_count', 0)
    return 3.0 if c >= 20 else 2.5 if c >= 15 else 2.0 if c >= 10 else 1.5 if c >= 5 else 1.0


def score_overlay(frame, g):
    """트레일러 전용 점수판(시네마틱 크롭 위에 그려 잘리지 않게).
    큰 점수 + 콤보 배율 칩 — 도파민 강조."""
    score = int(getattr(g, '_survival_score', 0))
    stxt = f"★ {score:,}"
    sh = F_SCORE.render(stxt, True, (60, 30, 0))
    sf = F_SCORE.render(stxt, True, (255, 226, 120))
    x = OUT_W // 2 - sf.get_width() // 2
    y = 62
    frame.blit(sh, (x + 3, y + 3)); frame.blit(sf, (x, y))
    # 콤보 칩
    c = getattr(g, '_combo_count', 0)
    if c >= 2:
        mult = _combo_mult(g)
        tier = g._combo_tier(c) if hasattr(g, '_combo_tier') else None
        col = tier[2] if tier else (255, 190, 90)
        ctxt = f"{c} COMBO  x{mult:.1f}"
        cf = F_COMBO.render(ctxt, True, col)
        cx = OUT_W // 2 - cf.get_width() // 2
        cy = y + sf.get_height() + 4
        csh = F_COMBO.render(ctxt, True, (10, 5, 0))
        frame.blit(csh, (cx + 2, cy + 2)); frame.blit(cf, (cx, cy))


def surv_driver(skills=('W', 'A', 'S', 'D'), pin_combo=False, dense=18):
    """오토파일럿 — 증강 드래프트 자동 확정 + 근접 난전 + 스킬 로테이션 + 밀도 유지."""
    def drv(g, i):
        if g.state == 'survival_augment':      # 드래프트 뜨면 즉시 확정(흐름 유지)
            _safe(g._handle_survival_augment_action, {'type': 'confirm'})
            return
        # 화면을 항상 북적이게 — 플레이어 주위 링 스폰(트레일러 카오스)
        live = sum(1 for e in g.dungeon.enemies if e.is_alive())
        if i % 6 == 0 and live < dense:
            _safe(MT.spawn_ring, g, MT.enemy_keys(g), 4, 12)
        g.player.stamina = g.player.stamina_max
        if pin_combo:                          # GODLIKE 쇼케이스: 콤보 창 고정
            g._combo_ms = 4000
        if i > 3 and i % 10 == 5:
            sk = skills[(i // 10) % len(skills)]
            _safe(g._process, {'type': 'skill', 'skill': sk})
        face_nearest(g)
        if g.dungeon.enemies:
            adj = any(abs(e.x - g.player.x) + abs(e.y - g.player.y) <= 1
                      for e in g.dungeon.enemies)
            if adj and i % 2 == 0:
                _safe(g._process, {'type': 'attack'})
            elif not adj and i % 3 == 0:
                t = min(g.dungeon.enemies,
                        key=lambda e: abs(e.x - g.player.x) + abs(e.y - g.player.y))
                dx = (t.x > g.player.x) - (t.x < g.player.x)
                dy = (t.y > g.player.y) - (t.y < g.player.y)
                _safe(g._process, {'type': 'move', 'dx': dx, 'dy': dy})
        if g.camera:
            g.camera.center_on(g.player.x, g.player.y)
    return drv


def play_survival(d, g, frames, chip_label, chip_col, cap,
                  driver=None, fade_in=False, fade_out=False, show_score=True):
    """생존 씬 캡처 (play_scene 의 생존판 — surv_step + 점수판 오버레이)."""
    for i in range(frames):
        if driver:
            _safe(driver, g, i)
        surv_step(g)
        view = render_view(g)
        frame = cinematic(view)
        vignette(frame)
        letterbox(frame)
        if show_score:
            score_overlay(frame, g)
        if chip_label:
            chip(frame, chip_label, chip_col)
        if cap:
            ca = min(255, i * 24) if i < 12 else 255
            caption(frame, cap, ca)
        MT.fade_pair(frame, fade_in, fade_out, i, frames)
        d.emit(frame)


def show_augment_draft(d, g, frames, cap):
    """증강 드래프트 화면을 그대로 보여준다(선택 커서가 훑고 지나감)."""
    g._aug_choices = ['titan', 'bullet_storm', 'frost_aura']
    g._aug_cursor = 0
    g.state = 'survival_augment'
    for i in range(frames):
        g._aug_cursor = (i // 14) % 3        # 커서가 카드들을 훑는다
        view = render_view(g)
        frame = cinematic(view)
        vignette(frame)
        letterbox(frame)
        chip(frame, "AUGMENT", (180, 150, 245))
        if cap:
            caption(frame, cap, 255)
        MT.fade_pair(frame, i < 6, i >= frames - 6, i, frames)
        d.emit(frame)
    g.state = 'playing'


# ══════════════════════════════════════════════════════════════════════════
def build(out_path, lang="ko"):
    set_ui_lang(lang)
    d = Director(out_path)

    # ── 1. TITLE ───────────────────────────────────────────────────────────
    card(d, 72, "ENDLESS SURVIVAL", L("title_sub"), (255, 120, 90))

    # ── 2. THE HORDE — 도끼맨 난전(폭풍도끼/사이클론) ────────────────────────
    g = new_survival('axeman', level=20, augs=['frost_aura'])
    play_survival(d, g, 170, "SURVIVE", (150, 240, 160), L("horde"),
                  driver=surv_driver(('W', 'A', 'S', 'D')), fade_in=True)
    flash(d, 3)

    # ── 3. AUGMENTS — 드래프트 화면 + 거신 변신 난전 ─────────────────────────
    show_augment_draft(d, g, 78, L("augment"))
    flash(d, 2)
    gt = new_survival('warrior', level=24, augs=['titan', 'overpower'])
    play_survival(d, gt, 130, "TITAN", (220, 170, 90), None,
                  driver=surv_driver(('S', 'A', 'D', 'W')))
    flash(d, 2)

    # ── 4. GODLIKE — 탄막 + 콤보 점수판 폭발 ────────────────────────────────
    gg = new_survival('mage', level=26, augs=['bullet_storm', 'frenzy', 'overpower'])
    gg._combo_count = 22          # 하이라이트: GODLIKE 티어에서 시작
    gg._combo_ms = 4000
    gg._survival_bonus = 4200     # 점수판이 이미 뜨겁게
    play_survival(d, gg, 175, "GODLIKE", (255, 105, 255), L("godlike"),
                  driver=surv_driver(('A', 'D', 'S', 'W'), pin_combo=True, dense=22),
                  fade_out=True)
    flash(d, 3)

    # ── 5. SUPPLY — 스테이지 보급 배너 ──────────────────────────────────────
    gs = new_survival('archer', level=22, augs=['bullet_storm'])
    gs._survival_elapsed = 29200.0    # 곧 스테이지 상승(보급 배너) 트리거
    play_survival(d, gs, 120, "SUPPLY", (255, 210, 90), L("supply"),
                  driver=surv_driver(('A', 'D', 'S', 'W')), fade_in=True, fade_out=True)

    # ── 6. OUTRO ────────────────────────────────────────────────────────────
    card(d, 120, "ENDLESS SURVIVAL", L("outro_sub"), (255, 120, 90), wishlist=True)

    d.close()
    return d.n


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/steam/survival_trailer.mp4"
    lang = sys.argv[2] if len(sys.argv) > 2 else "ko"
    n = build(out, lang)
    print(f"OK  {out}  [{lang}]  ({n} frames, ~{n / FPS:.1f}s)")

"""Dungeon Door — 자동 시네마틱 트레일러 생성기.

게임을 헤드리스로 스크립트 재생하며 게임 뷰포트를 캡처 → 1280x720 시네마틱
프레임으로 합성 → ffmpeg 파이프로 곧장 MP4 인코딩(임시 PNG 없음).

콘셉트: TITLE → HUNT(사냥) → LIVE(생활) → ADVENTURE(모험) → OUTRO

사용:  python3 tools/make_trailer.py [out.mp4]
"""
import os
import sys
import math
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
pygame.init()

from core.constants import GAME_X, GAME_Y, GAME_W, GAME_H  # noqa: E402
from core.game import Game  # noqa: E402
from core import fonts  # noqa: E402

FPS = 30
OUT_W, OUT_H = 1280, 720
DT = 1000.0 / FPS

# ── 폰트 (한글 지원) ──────────────────────────────────────────────────────
F_TITLE = fonts.load_font(96, bold=True)
F_SUB = fonts.load_font(30, bold=True)
F_CHIP = fonts.load_font(34, bold=True)
F_CAP = fonts.load_font(26, bold=True)

GOLD = (255, 212, 96)
WHITE = (240, 244, 252)

# ── 언어별 자막 (UI 언어도 함께 전환) ─────────────────────────────────────
_LANG = "ko"
CAPS = {
    "title_sub":  {"ko": "문 너머, 무엇이든",            "en": "Beyond the Door — Anything"},
    "axe_intro":  {"ko": "신규 클래스 · 도끼맨",          "en": "NEW CLASS — THE AXEMAN"},
    "axe_ult":    {"ko": "궁극기 라그나로크 — 무적의 폭풍", "en": "RAGNAROK — Unstoppable Fury"},
    "warrior":    {"ko": "전사 — 검과 방패의 정면승부",    "en": "Warrior — Blade & Shield"},
    "archer":     {"ko": "궁수 — 쏟아지는 화살",          "en": "Archer — Rain of Arrows"},
    "mage":       {"ko": "마법사 — 원소를 지배하라",       "en": "Mage — Master the Elements"},
    "four":       {"ko": "네 직업, 네 가지 전투",          "en": "Four Classes, Four Playstyles"},
    "feat":       {"ko": "사냥만이 전부가 아니다",         "en": "It's not all about the fight"},
    "farm":       {"ko": "농사로 작물을 길러라",           "en": "Grow crops on your farm"},
    "fish":       {"ko": "손맛 오지는 낚시",              "en": "Cast a line, reel it in"},
    "ranch":      {"ko": "목장에서 가축을 키워라",         "en": "Raise livestock on your ranch"},
    "adv":        {"ko": "문 너머 999층의 심연을 정복하라", "en": "Conquer the 999-floor abyss"},
    "outro_sub":  {"ko": "사냥 · 생활 · 모험",            "en": "HUNT · LIVE · ADVENTURE"},
}


def L(key):
    return CAPS[key][_LANG]


def set_ui_lang(lang):
    """게임 UI 언어 전환 (트레일러 내 화면 텍스트)."""
    global _LANG
    _LANG = lang if lang in ("ko", "en") else "ko"
    try:
        from core.lang import set_lang
        set_lang(_LANG)
    except Exception:
        pass


# 직업별 칩 (이모지 미지원 → 텍스트만). (라벨, 강조색)
CLASS_CHIP = {
    "axeman":  ("AXEMAN",  (255, 150, 60)),
    "warrior": ("WARRIOR", (255, 96, 74)),
    "archer":  ("ARCHER",  (120, 220, 140)),
    "mage":    ("MAGE",    (156, 132, 255)),
}


# ── 프레임 합성 헬퍼 ───────────────────────────────────────────────────────
def cinematic(view):
    """800x608 게임 뷰 → 1280x720 커버 스케일(상하 크롭)."""
    scaled = pygame.transform.smoothscale(view, (1280, 973))
    frame = pygame.Surface((OUT_W, OUT_H))
    frame.blit(scaled, (0, -(973 - OUT_H) // 2))
    return frame


_VIGNETTE = None


def vignette(frame):
    global _VIGNETTE
    if _VIGNETTE is None:
        v = pygame.Surface((OUT_W, OUT_H), pygame.SRCALPHA)
        cx, cy = OUT_W / 2, OUT_H / 2
        maxd = math.hypot(cx, cy)
        for yy in range(0, OUT_H, 4):
            d = abs(yy - cy) / cy
            a = int(120 * max(0, d - 0.35))
            pygame.draw.rect(v, (0, 0, 0, a), (0, yy, OUT_W, 4))
        _VIGNETTE = v
    frame.blit(_VIGNETTE, (0, 0))


def letterbox(frame, h=54):
    pygame.draw.rect(frame, (0, 0, 0), (0, 0, OUT_W, h))
    pygame.draw.rect(frame, (0, 0, 0), (0, OUT_H - h, OUT_W, h))


def _text(frame, font, s, col, cx, y, shadow=True):
    surf = font.render(s, True, col)
    x = cx - surf.get_width() // 2
    if shadow:
        sh = font.render(s, True, (0, 0, 0))
        frame.blit(sh, (x + 2, y + 2))
    frame.blit(surf, (x, y))
    return surf.get_width()


def chip(frame, label, accent):
    """좌상단 섹션 칩 (⚔ HUNT 등)."""
    pad = 16
    surf = F_CHIP.render(label, True, WHITE)
    w = surf.get_width() + pad * 2
    x, y = 46, 64
    box = pygame.Surface((w, 50), pygame.SRCALPHA)
    box.fill((0, 0, 0, 150))
    frame.blit(box, (x, y))
    pygame.draw.rect(frame, accent, (x, y, 5, 50))
    frame.blit(surf, (x + pad, y + 8))


def caption(frame, s, alpha=255):
    if not s:
        return
    surf = F_CAP.render(s, True, WHITE)
    x = OUT_W // 2 - surf.get_width() // 2
    y = OUT_H - 96
    bg = pygame.Surface((surf.get_width() + 40, 44), pygame.SRCALPHA)
    bg.fill((0, 0, 0, min(alpha, 150)))
    frame.blit(bg, (x - 20, y - 8))
    sh = F_CAP.render(s, True, (0, 0, 0))
    surf.set_alpha(alpha); sh.set_alpha(alpha)
    frame.blit(sh, (x + 2, y + 2))
    frame.blit(surf, (x, y))


# ── 한 프레임 게임 업데이트 (run() 핵심만 모사, 안전하게) ──────────────────
def _safe(fn, *a):
    try:
        fn(*a)
    except Exception:
        pass


def step(g, dt=DT):
    if g.state == 'playing' and g.player:
        _safe(g.player.tick_debuffs, dt)
        if getattr(g, '_pet', None):
            _safe(g._update_pet_trail)
            _safe(g._pet.update, dt, g)
        if not g._in_town:
            _safe(g._update_conveyor, dt)
            _safe(g._update_hazards, dt)
            _safe(g._update_enemies, dt)
            _safe(g._update_dots, dt)
            _safe(g._update_summons, dt)
            _safe(g._update_bombs, dt)
            if getattr(g, '_ragnarok_ms', 0) > 0:
                _safe(g._update_ragnarok_aura, dt)
        if g._in_town and g._town:
            _safe(g._town.update, dt, g.player.x, g.player.y)
        for a in ('_axe_throw_cd_ms', '_ragnarok_ms', '_combo_ms', '_gold_flash_ms',
                  '_shake_timer', '_punch_zoom_ms', '_cancel_bonus_ms', '_fade_alpha'):
            if hasattr(g, a):
                setattr(g, a, max(0, getattr(g, a) - dt))
    _safe(g.animator.update, dt)


def render_view(g):
    """게임 렌더 → 뷰포트 서브서피스 복사 반환 (800x608)."""
    g._render()
    return g.screen.subsurface((GAME_X, GAME_Y, GAME_W, GAME_H)).copy()


# ── 디렉터: ffmpeg 파이프 ─────────────────────────────────────────────────
class Director:
    def __init__(self, out_path):
        self.out = out_path
        self.proc = subprocess.Popen(
            ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
             "-preset", "medium", "-movflags", "+faststart", out_path],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        self.n = 0

    def emit(self, frame):
        self.proc.stdin.write(pygame.image.tobytes(frame, "RGB"))
        self.n += 1

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()


def fade_pair(frame, fade_in, fade_out, i, total, flen=6):
    """세그먼트 시작/끝 페이드-투-블랙."""
    a = 0
    if fade_in and i < flen:
        a = int(255 * (1 - i / flen))
    elif fade_out and i >= total - flen:
        a = int(255 * (1 - (total - 1 - i) / flen))
    if a > 0:
        ov = pygame.Surface((OUT_W, OUT_H)); ov.set_alpha(a)
        frame.blit(ov, (0, 0))


# ── 씬: 게임 뷰 기반 (칩/캡션/시네마 처리) ────────────────────────────────
def play_scene(d, g, frames, chip_label=None, chip_col=GOLD, cap=None,
               driver=None, fade_in=False, fade_out=False):
    for i in range(frames):
        if driver:
            _safe(driver, g, i)
        step(g)
        view = render_view(g)
        frame = cinematic(view)
        vignette(frame)
        letterbox(frame)
        if chip_label:
            chip(frame, chip_label, chip_col)
        if cap:
            ca = min(255, i * 24) if i < 12 else 255
            caption(frame, cap, ca)
        fade_pair(frame, fade_in, fade_out, i, frames)
        d.emit(frame)


# ── 타이틀/아웃트로 카드 ──────────────────────────────────────────────────
def card(d, frames, title, sub, accent=GOLD, wishlist=False):
    for i in range(frames):
        frame = pygame.Surface((OUT_W, OUT_H))
        # 배경 그라디언트 + 흐르는 룬 점
        for yy in range(0, OUT_H, 4):
            c = 10 + int(14 * yy / OUT_H)
            pygame.draw.rect(frame, (c, c - 4, c + 8), (0, yy, OUT_W, 4))
        t = i / max(1, frames)
        for k in range(28):
            px = int((k * 137 + i * 3) % OUT_W)
            py = int((k * 53) % OUT_H)
            a = 60 + int(60 * math.sin(i * 0.1 + k))
            pygame.draw.circle(frame, (accent[0], accent[1], accent[2]),
                               (px, py), 1)
        pop = min(1.0, i / 10.0)
        ty = int(OUT_H // 2 - 90 - (1 - pop) * 20)
        _text(frame, F_TITLE, title, WHITE, OUT_W // 2, ty)
        pygame.draw.rect(frame, accent,
                         (OUT_W // 2 - 150, ty + 108, 300, 4))
        if i > 6:
            _text(frame, F_SUB, sub, accent, OUT_W // 2, ty + 128)
        if wishlist:
            blink = (i // 8) % 2 == 0
            col = GOLD if blink else WHITE
            _text(frame, F_SUB, "WISHLIST NOW ON STEAM", col,
                  OUT_W // 2, OUT_H - 150)
        fade_pair(frame, i < 8, i >= frames - 8, i, frames, flen=8)
        d.emit(frame)


# ══════════════════════════════════════════════════════════════════════════
# 씬 셋업
# ══════════════════════════════════════════════════════════════════════════
def spawn_ring(g, keys, radius=3, n=8):
    """플레이어 주위 링으로 적 배치."""
    from entities.enemy import Enemy
    from map.generator import _scale_enemy
    import random
    px, py = g.player.x, g.player.y
    placed = 0
    for a in range(n):
        ang = 2 * math.pi * a / n
        for r in (radius, radius + 1, radius - 1):
            ex = px + int(round(math.cos(ang) * r))
            ey = py + int(round(math.sin(ang) * r))
            if not g.dungeon.is_walkable(ex, ey) or g.dungeon.get_enemy_at(ex, ey):
                continue
            key = random.choice(keys)
            if key not in g._enemy_data:
                continue
            data = _scale_enemy(g._enemy_data[key], g.floor)
            data['key'] = key
            g.dungeon.enemies.append(Enemy(ex, ey, data))
            placed += 1
            break
    return placed


def enemy_keys(g):
    return [k for k in ('rat', 'bat', 'slime', 'centipede', 'skeleton',
                        'goblin', 'zombie', 'spider') if k in g._enemy_data]


def face_nearest(g):
    """가장 가까운 적을 바라보게 (원거리 직업 조준 자연스럽게)."""
    if not g.dungeon.enemies:
        return
    t = min(g.dungeon.enemies,
            key=lambda e: abs(e.x - g.player.x) + abs(e.y - g.player.y))
    dx, dy = t.x - g.player.x, t.y - g.player.y
    g._facing = ('right' if dx > 0 else 'left') if abs(dx) >= abs(dy) \
        else ('down' if dy > 0 else 'up')


def combat_driver(skills=('A', 'S', 'D'), ult_at=None, ranged=False, topup=6):
    """깔끔한 전투 연출: 제자리에서 적을 상대하며 스킬/궁극기 전개.
    (이전 버전의 지그재그 이동 어색함 제거 — 이동 최소화)."""
    def drv(g, i):
        g.player.stamina = g.player.stamina_max
        # 적 보충 — 항상 북적이게 (가까이 붙여서 바로 교전)
        if i % 24 == 0 and len(g.dungeon.enemies) < topup:
            spawn_ring(g, enemy_keys(g), radius=2, n=9)
        if ult_at is not None and i == ult_at:
            _safe(g._process, {'type': 'ultimate', 'key': 'R'})
        # 스킬 로테이션(크게, 간격 있게)
        if i > 4 and i % 16 == 8:
            sk = skills[(i // 16) % len(skills)]
            _safe(g._process, {'type': 'skill', 'skill': sk})
        face_nearest(g)
        if g.dungeon.enemies:
            adj = any(abs(e.x - g.player.x) + abs(e.y - g.player.y) <= 1
                      for e in g.dungeon.enemies)
            if ranged:
                if i % 3 == 0:
                    _safe(g._process, {'type': 'attack'})   # 원거리 연사
            elif adj:
                if i % 2 == 0:
                    _safe(g._process, {'type': 'attack'})   # 제자리 난타
            elif i % 5 == 0:                                 # 멀면 가끔 한 걸음
                t = min(g.dungeon.enemies,
                        key=lambda e: abs(e.x - g.player.x) + abs(e.y - g.player.y))
                dx = (t.x > g.player.x) - (t.x < g.player.x)
                dy = (t.y > g.player.y) - (t.y < g.player.y)
                _safe(g._process, {'type': 'move', 'dx': dx, 'dy': dy})
        g.camera.center_on(g.player.x, g.player.y)
    return drv


def pan_driver(path):
    """카메라를 경유지들(path)로 부드럽게 이동."""
    def drv(g, i):
        segs = len(path) - 1
        if segs <= 0:
            g.camera.center_on(*path[0]); return
        # 전체 프레임을 segs로 나눠 보간 (i는 0..frames-1, frames는 호출측)
        t = i / max(1, drv.total - 1)
        p = min(segs - 1e-6, t * segs)
        a = int(p); f = p - a
        x = path[a][0] * (1 - f) + path[a + 1][0] * f
        y = path[a][1] * (1 - f) + path[a + 1][1] * f
        g.camera.center_on(int(round(x)), int(round(y)))
    drv.total = 1
    return drv


def flash(d, n=2, col=(255, 255, 255)):
    """하드 컷 사이 화이트 플래시 (역동감)."""
    for _ in range(n):
        fr = pygame.Surface((OUT_W, OUT_H))
        fr.fill(col)
        d.emit(fr)


def fishing_scene(d, gt, frames, chip_lbl, chip_col, cap):
    """낚시 릴 미니게임 (fishing 상태는 step()에서 안 도니 직접 갱신)."""
    gt.state = 'playing'
    gt._open_fishing()
    gt._fish.update({'phase': 'reel', 't': 0.0, 'cursor': 0.15, 'dir': 1,
                     'speed': 0.0017, 'band_c': 0.5, 'band_w': 0.13,
                     'pending': ('koi', 1, 60), 'grade': 1})
    for i in range(frames):
        f = gt._fish
        f['cursor'] += f['dir'] * f['speed'] * DT
        if f['cursor'] <= 0:
            f['cursor'] = 0; f['dir'] = 1
        elif f['cursor'] >= 1:
            f['cursor'] = 1; f['dir'] = -1
        gt._render()
        view = gt.screen.subsurface((GAME_X, GAME_Y, GAME_W, GAME_H)).copy()
        frame = cinematic(view); vignette(frame); letterbox(frame)
        chip(frame, chip_lbl, chip_col)
        caption(frame, cap, 255)
        d.emit(frame)
    gt.state = 'playing'


def fill_town_life(g):
    """마을을 풍성하게: 밭 작물 성장 + 목장 가축 + 창고 아이템."""
    from core.town import FARM_PLOTS, FARM_GROW_MAX, RANCH_PENS, RANCH_FEED_MAX
    crops = ['wheat', 'tomato', 'pumpkin', 'carrot']
    farm = []
    for i in range(len(FARM_PLOTS)):
        c = crops[i % 4]
        stg = FARM_GROW_MAX if i % 3 else 1
        farm.append({'crop': c, 'stage': stg, 'watered': True})
    g._records['farm'] = farm
    g._town.farm = farm
    animals = ['cow', 'chicken', 'sheep', 'pig', 'cow', 'chicken']
    ranch = [{'animal': animals[i % len(animals)], 'fed': True,
              'stage': RANCH_FEED_MAX} for i in range(len(RANCH_PENS))]
    g._records['ranch'] = ranch
    g._town.ranch = ranch


# ══════════════════════════════════════════════════════════════════════════
def build(out_path, lang="ko"):
    set_ui_lang(lang)
    d = Director(out_path)

    def combat(cls, floor, frames, cap_key, skills, ult_at=None, ranged=False,
               fade_in=False, fade_out=False):
        g = Game(); g.start_test_mode(floor, char_class=cls)
        g.player.stamina = g.player.stamina_max
        spawn_ring(g, enemy_keys(g), radius=2, n=9)
        g.camera.center_on(g.player.x, g.player.y)
        lbl, col = CLASS_CHIP[cls]
        play_scene(d, g, frames, lbl, col, L(cap_key),
                   driver=combat_driver(skills, ult_at=ult_at, ranged=ranged),
                   fade_in=fade_in, fade_out=fade_out)

    # ── 1. TITLE ──────────────────────────────────────────────────────────
    card(d, 74, "DUNGEON DOOR", L("title_sub"), GOLD)

    # ── 2. HUNT — 도끼맨(신규·메인)을 앞세워 4직업 전부 ────────────────────
    # (a) AXEMAN 등장 — 도끼 스킬 난전
    combat('axeman', 9, 190, "axe_intro", ('W', 'D', 'S'), fade_in=True)
    flash(d, 2)
    # (b) AXEMAN 궁극기 라그나로크 — 하이라이트
    combat('axeman', 12, 180, "axe_ult", ('W', 'D'), ult_at=8)
    flash(d, 3)
    # (c) WARRIOR
    combat('warrior', 7, 135, "warrior", ('A', 'D', 'S'))
    flash(d, 2)
    # (d) MAGE — 원소/궁극기
    combat('mage', 11, 165, "mage", ('A', 'D', 'S'), ult_at=10)
    flash(d, 2)
    # (e) ARCHER — 원거리 연사
    combat('archer', 8, 140, "archer", ('A', 'D', 'S'), ranged=True, fade_out=True)

    # ── 3. 생활 콘텐츠 — 슬로우 팬 대신 빠른 플래시 컷 ─────────────────────
    from core.town import FARM_PLOTS, RANCH_PENS
    gt = Game(); gt.start_town_test(30, char_class='archer')
    fill_town_life(gt)
    fx, fy = FARM_PLOTS[0]
    rx, ry = RANCH_PENS[0]

    # 인트로 한 컷
    gt.camera.center_on(fx + 5, fy + 2)
    play_scene(d, gt, 60, "TOWN", GOLD, L("feat"),
               driver=pan_driver_short([(fx + 3, fy + 2), (fx + 8, fy + 3)], 60),
               fade_in=True)
    flash(d, 2)
    # 농사 팝업
    gt.player.x, gt.player.y = FARM_PLOTS[2]
    gt.camera.center_on(gt.player.x, gt.player.y)
    gt._farm_menu_plot = 2; gt.state = 'farm_menu'
    play_scene(d, gt, 78, "FARM", (150, 220, 120), L("farm"),
               driver=lambda g, i: setattr(g, '_farm_menu_idx', (i // 16) % 4))
    gt.state = 'playing'
    flash(d, 2)
    # 낚시 릴 미니게임
    gt.player.x, gt.player.y = 50, 55
    gt.camera.center_on(50, 55)
    fishing_scene(d, gt, 96, "FISH", (110, 200, 236), L("fish"))
    flash(d, 2)
    # 목장 근접
    gt.camera.center_on(rx, ry)
    play_scene(d, gt, 86, "RANCH", (232, 182, 92), L("ranch"),
               driver=pan_driver_short([(rx - 2, ry), (rx + 4, ry + 1)], 86),
               fade_out=True)

    # ── 4. ADVENTURE ──────────────────────────────────────────────────────
    ga = Game(); ga.start_test_mode(14, char_class='axeman')
    ga.dungeon.reveal_all()
    cx, cy = ga.player.x, ga.player.y
    play_scene(d, ga, 165, "ADVENTURE", (150, 130, 255), L("adv"),
               driver=pan_driver_short([(cx - 8, cy - 4), (cx + 8, cy + 5),
                                        (cx, cy)], 165),
               fade_in=True, fade_out=True)

    # ── 5. OUTRO ──────────────────────────────────────────────────────────
    card(d, 128, "DUNGEON DOOR", L("outro_sub"), GOLD, wishlist=True)

    d.close()
    return d.n


def pan_driver_short(path, total):
    p = pan_driver(path); p.total = total
    return p


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "dungeon_door_trailer.mp4"
    lang = sys.argv[2] if len(sys.argv) > 2 else "ko"
    n = build(out, lang)
    print(f"OK  {out}  [{lang}]  ({n} frames, ~{n / FPS:.1f}s)")

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


def hunt_driver(ranged=False):
    def drv(g, i):
        g.player.stamina = g.player.stamina_max
        # 스킬 로테이션으로 화려하게
        if i % 22 == 6:
            _safe(g._process, {'type': 'skill', 'skill': 'A'})
        if i % 22 == 14:
            _safe(g._process, {'type': 'skill', 'skill': 'D'})
        # 적이 줄면 다시 채워 계속 북적이게
        if i % 30 == 0 and len(g.dungeon.enemies) < 5:
            spawn_ring(g, enemy_keys(g), radius=4, n=8)
        if g.dungeon.enemies:
            tgt = min(g.dungeon.enemies,
                      key=lambda e: abs(e.x - g.player.x) + abs(e.y - g.player.y))
            dx = (tgt.x > g.player.x) - (tgt.x < g.player.x)
            dy = (tgt.y > g.player.y) - (tgt.y < g.player.y)
            adj = abs(tgt.x - g.player.x) + abs(tgt.y - g.player.y) <= 1
            if ranged:
                self_face = dx if dx else dy
                if i % 2 == 0:
                    _safe(g._process, {'type': 'attack'})  # 궁수: 화살
                elif i % 5 == 0:
                    _safe(g._process, {'type': 'move', 'dx': -dx, 'dy': 0})  # 카이팅
            elif adj:
                _safe(g._process, {'type': 'attack'})
            elif i % 2 == 0:
                _safe(g._process, {'type': 'move', 'dx': dx, 'dy': 0})
            else:
                _safe(g._process, {'type': 'move', 'dx': 0, 'dy': dy})
        g.camera.center_on(g.player.x, g.player.y)   # 카메라 추적
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
def build(out_path):
    d = Director(out_path)

    # ── 1. TITLE ──────────────────────────────────────────────────────────
    card(d, 82, "DUNGEON DOOR", "문 너머, 무엇이든", GOLD)

    # ── 2. HUNT ───────────────────────────────────────────────────────────
    # (a) 전사 근접 난전
    g = Game(); g.start_test_mode(7, char_class='warrior')
    g.player.stamina = g.player.stamina_max
    spawn_ring(g, enemy_keys(g), radius=3, n=10)
    g.camera.center_on(g.player.x, g.player.y)
    play_scene(d, g, 230, "⚔  HUNT", (255, 90, 70),
               "지하 999층 — 사냥이 시작된다", driver=hunt_driver(),
               fade_in=True)

    # (b) 도끼맨 궁극기 라그나로크
    gb = Game(); gb.start_test_mode(10, char_class='axeman')
    gb.player.stamina = gb.player.stamina_max
    spawn_ring(gb, enemy_keys(gb), radius=3, n=10)
    gb.camera.center_on(gb.player.x, gb.player.y)

    def boss_drv(g, i):
        g.player.stamina = g.player.stamina_max
        if i == 6:
            _safe(g._process, {'type': 'ultimate', 'key': 'R'})
        if i % 18 == 12:
            _safe(g._process, {'type': 'skill', 'skill': 'D'})
        if i % 34 == 0 and len(g.dungeon.enemies) < 5:
            spawn_ring(g, enemy_keys(g), radius=4, n=8)
        if g.dungeon.enemies and i % 2:
            _safe(g._process, {'type': 'attack'})
        g.camera.center_on(g.player.x, g.player.y)
    play_scene(d, gb, 200, "⚔  HUNT", (255, 90, 70),
               "궁극기 한 방으로 쓸어버려라", driver=boss_drv)

    # (c) 궁수 원거리 카이팅
    ga2 = Game(); ga2.start_test_mode(8, char_class='archer')
    ga2.player.stamina = ga2.player.stamina_max
    spawn_ring(ga2, enemy_keys(ga2), radius=4, n=10)
    ga2.camera.center_on(ga2.player.x, ga2.player.y)
    play_scene(d, ga2, 180, "⚔  HUNT", (255, 90, 70),
               "네 가지 직업, 네 가지 전투", driver=hunt_driver(ranged=True),
               fade_out=True)

    # ── 3. LIVE ───────────────────────────────────────────────────────────
    gt = Game(); gt.start_town_test(30, char_class='archer')
    fill_town_life(gt)
    from core.town import FARM_PLOTS, RANCH_PENS
    fx, fy = FARM_PLOTS[0]
    rx, ry = RANCH_PENS[0]
    pan = pan_driver([(fx + 4, fy + 2), (60, 46), (rx - 6, ry + 2), (rx + 2, ry)])
    pan.total = 240
    play_scene(d, gt, 240, "🌾  LIVE", (120, 210, 120),
               "농사 · 낚시 · 목장 — 마을의 삶", driver=pan, fade_in=True)

    # 농사 팝업 데모
    gt.player.x, gt.player.y = FARM_PLOTS[2]
    gt.camera.center_on(gt.player.x, gt.player.y)
    gt._farm_menu_plot = 2
    gt._farm_menu_idx = 2
    gt.state = 'farm_menu'

    def farm_menu_drv(g, i):
        g._farm_menu_idx = (i // 18) % 4
    play_scene(d, gt, 120, "🌾  LIVE", (120, 210, 120),
               "심고 · 기르고 · 거두고", driver=farm_menu_drv)
    gt.state = 'playing'

    # 낚시 릴 미니게임 데모
    gt.player.x, gt.player.y = 50, 55
    gt.camera.center_on(gt.player.x, gt.player.y)
    gt._open_fishing()
    gt._fish.update({'phase': 'reel', 't': 0.0, 'cursor': 0.2, 'dir': 1,
                     'speed': 0.0016, 'band_c': 0.5, 'band_w': 0.14,
                     'pending': ('koi', 1, 60), 'grade': 1})

    def fish_drv(g, i):
        f = g._fish
        f['cursor'] += f['dir'] * f['speed'] * DT
        if f['cursor'] <= 0:
            f['cursor'] = 0; f['dir'] = 1
        elif f['cursor'] >= 1:
            f['cursor'] = 1; f['dir'] = -1
    # fishing 상태는 step()에서 안 도니 직접 갱신
    for i in range(150):
        fish_drv(gt, i)
        gt._render()
        view = gt.screen.subsurface((GAME_X, GAME_Y, GAME_W, GAME_H)).copy()
        frame = cinematic(view); vignette(frame); letterbox(frame)
        chip(frame, "🌾  LIVE", (120, 210, 120))
        caption(frame, "손맛 오지는 낚시 — 릴을 감아라", 255)
        d.emit(frame)
    gt.state = 'playing'

    # 목장 근접 (가축 어슬렁)
    gt.camera.center_on(rx, ry)
    rpan = pan_driver([(rx - 3, ry), (rx + 4, ry + 1), (rx, ry)]); rpan.total = 150
    play_scene(d, gt, 150, "🌾  LIVE", (120, 210, 120),
               "가축을 길러 우유·달걀·고기를 얻어라",
               driver=rpan, fade_out=True)

    # ── 4. ADVENTURE ──────────────────────────────────────────────────────
    ga = Game(); ga.start_test_mode(14, char_class='mage')
    ga.dungeon.reveal_all()
    ga.camera.center_on(ga.player.x, ga.player.y)
    cx, cy = ga.player.x, ga.player.y
    apan = pan_driver([(cx - 9, cy - 5), (cx + 9, cy + 5), (cx + 2, cy - 3), (cx, cy)])
    apan.total = 260
    play_scene(d, ga, 260, "🚪  ADVENTURE", (150, 130, 255),
               "문 너머의 심연 — 999층을 정복하라", driver=apan,
               fade_in=True, fade_out=True)

    # ── 5. OUTRO ──────────────────────────────────────────────────────────
    card(d, 135, "DUNGEON DOOR", "HUNT · LIVE · ADVENTURE", GOLD, wishlist=True)

    d.close()
    return d.n


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "dungeon_door_trailer_v270.mp4"
    n = build(out)
    print(f"OK  {out}  ({n} frames, ~{n / FPS:.1f}s)")

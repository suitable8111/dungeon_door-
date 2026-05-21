#!/usr/bin/env python3
"""
Steam 예고편 생성
순서: 인트로(2.5s) → 클립1(20s) → 클립2(8.8s) → 클립3(20s) → 아웃트로(3s)
결과: assets/steam/dungeon_door_trailer.mp4
"""
import os, sys, subprocess, tempfile, shutil, math

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

BASE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'steam')
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts')
PX    = os.path.join(FONTS, 'PressStart2P-Regular.ttf')
OUT   = os.path.join(BASE, 'dungeon_door_trailer.mp4')

W, H, FPS = 1920, 1080, 60
GOLD_C = (235, 185,  60)
GOLD_L = (255, 222, 105)
GOLD_D = (150, 108,  18)
GREY_C = (192, 200, 216)


# ── Pygame 타이틀 카드 PNG 생성 ─────────────────────────────────────────

def _glow_text(surf, text, font, col, gcol, cx, cy):
    ts = font.render(text, True, col)
    x, y = cx - ts.get_width() // 2, cy - ts.get_height() // 2
    for d in range(3, 0, -1):
        gs = font.render(text, True, gcol)
        gs.set_alpha(max(1, 50 // d))
        for i in range(8):
            a = math.pi * 2 * i / 8
            surf.blit(gs, (x + round(math.cos(a) * d * 2),
                           y + round(math.sin(a) * d * 2)))
    surf.blit(font.render(text, True, (0, 0, 0)), (x + 3, y + 3))
    surf.blit(ts, (x, y))


def make_card_png(path: str, line1: str, line2: str,
                  sz1=90, sz2=130, col1=GOLD_C, col2=GOLD_L):
    pygame.init()
    pygame.display.set_mode((1, 1))
    surf = pygame.Surface((W, H))
    surf.fill((4, 3, 10))
    f1 = pygame.font.Font(PX, sz1) if os.path.exists(PX) else pygame.font.SysFont('monospace', sz1, bold=True)
    f2 = pygame.font.Font(PX, sz2) if os.path.exists(PX) else pygame.font.SysFont('monospace', sz2, bold=True)
    h1 = f1.get_height()
    h2 = f2.get_height()
    gap = 24
    total_h = h1 + gap + h2
    cy1 = H // 2 - total_h // 2 + h1 // 2
    cy2 = cy1 + h1 // 2 + gap + h2 // 2
    _glow_text(surf, line1, f1, col1, GOLD_D, W // 2, cy1)
    _glow_text(surf, line2, f2, col2, GOLD_D, W // 2, cy2)
    pygame.image.save(surf, path)
    pygame.quit()


# ── ffmpeg 헬퍼 ────────────────────────────────────────────────────────

def run(args: list, label: str):
    print(f'  [{label}] ...', flush=True)
    r = subprocess.run(['ffmpeg', '-y', *args], capture_output=True, text=True)
    if r.returncode != 0:
        print('STDERR:', r.stderr[-3000:])
        raise RuntimeError(f'ffmpeg 실패: {label}')
    print(f'  [{label}] ✓')


def png_to_video(png: str, out: str, duration: float,
                 fade_in=0.0, fade_out=0.0):
    vf_parts = [f'fps={FPS}']
    if fade_in > 0:
        frames_in = round(fade_in * FPS)
        vf_parts.append(f'fade=t=in:st=0:nb_frames={frames_in}')
    if fade_out > 0:
        start_out = duration - fade_out
        frames_out = round(fade_out * FPS)
        vf_parts.append(f'fade=t=out:st={start_out:.3f}:nb_frames={frames_out}')
    run([
        '-loop', '1', '-i', png,
        '-t', str(duration),
        '-vf', ','.join(vf_parts),
        '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p',
        out,
    ], f'PNG→영상: {os.path.basename(out)}')


def main():
    tmpdir = tempfile.mkdtemp(prefix='dd_trailer_')
    parts  = []

    try:
        SCALE = (
            f'scale={W}:{H}:force_original_aspect_ratio=decrease,'
            f'pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,'
            f'fps={FPS}'
        )

        # ── 1. 인트로 PNG → 영상 (2.5초, 페이드인 0.5s) ──────────────
        intro_png = os.path.join(tmpdir, 'intro.png')
        intro_mp4 = os.path.join(tmpdir, '00_intro.mp4')
        print('  [인트로 PNG 생성] ...')
        make_card_png(intro_png, 'DUNGEON', 'DOOR', sz1=90, sz2=130)
        png_to_video(intro_png, intro_mp4, duration=2.5, fade_in=0.5)
        parts.append(intro_mp4)

        # ── 2. 클립 1 (10초 스킵 후 20초) ────────────────────────────
        c1 = os.path.join(tmpdir, '01_clip1.mp4')
        run([
            '-ss', '10',
            '-i', os.path.join(BASE, 'game_trailer_1.mov'),
            '-t', '20',
            '-vf', SCALE,
            '-an', '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p',
            c1,
        ], '클립 1 (10s~30s, 20s)')
        parts.append(c1)

        # ── 3. 클립 2 (전체 ~8.8초) ────────────────────────────────────
        c2 = os.path.join(tmpdir, '02_clip2.mp4')
        run([
            '-i', os.path.join(BASE, 'game_trailer_2.mov'),
            '-vf', SCALE,
            '-an', '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p',
            c2,
        ], '클립 2 (전체)')
        parts.append(c2)

        # ── 4. 클립 3 (처음 20초, 끝 0.6s 페이드아웃) ──────────────────
        c3 = os.path.join(tmpdir, '03_clip3.mp4')
        run([
            '-i', os.path.join(BASE, 'game_trailer_3.mov'),
            '-t', '20',
            '-vf', SCALE + f',fade=t=out:st=19.4:nb_frames={round(0.6*FPS)}',
            '-an', '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p',
            c3,
        ], '클립 3 (20s + 페이드아웃)')
        parts.append(c3)

        # ── 5. 아웃트로 PNG → 영상 (3초, 페이드인 0.5s + 페이드아웃 0.5s)
        outro_png = os.path.join(tmpdir, 'outro.png')
        outro_mp4 = os.path.join(tmpdir, '04_outro.mp4')
        print('  [아웃트로 PNG 생성] ...')
        make_card_png(outro_png, 'DUNGEON DOOR', 'COMING SOON',
                      sz1=74, sz2=38, col1=GOLD_C, col2=GREY_C)
        png_to_video(outro_png, outro_mp4, duration=3.0, fade_in=0.5, fade_out=0.5)
        parts.append(outro_mp4)

        # ── 6. 최종 concat ──────────────────────────────────────────────
        listfile = os.path.join(tmpdir, 'list.txt')
        with open(listfile, 'w') as f:
            for p in parts:
                f.write(f"file '{p}'\n")

        run([
            '-f', 'concat', '-safe', '0', '-i', listfile,
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '20',
            '-pix_fmt', 'yuv420p',
            OUT,
        ], '최종 합성')

        mb = os.path.getsize(OUT) / 1024 / 1024
        print(f'\n✅ 완료: {OUT}  ({mb:.1f} MB)')

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    main()

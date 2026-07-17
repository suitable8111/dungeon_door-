#!/usr/bin/env python3
"""
Steam 예고편 생성 (4개 컨셉 클립 편집본)
  인트로 → 전사 → 궁수 → 버닝 모드 → 마을/퀘스트 → 아웃트로
각 클립: macOS 창 크롬/검은 여백 크롭 + 블러 배경 필러(16:9) + 컨셉 라벨 오버레이 + 오디오.
결과: assets/steam/dungeon_door_trailer.mp4
"""
import os, sys, subprocess, tempfile, shutil, math

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

BASE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'steam')
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts')
PX    = os.path.join(FONTS, 'PressStart2P-Regular.ttf')
KF    = os.path.join(FONTS, 'DungGeunMo.ttf')
OUT   = os.path.join(BASE, 'dungeon_door_trailer.mp4')

W, H, FPS = 1920, 1080, 60
GOLD_C = (235, 185,  60)
GOLD_L = (255, 222, 105)
GOLD_D = (150, 108,  18)
GREY_C = (192, 200, 216)

# 녹화본에서 macOS 타이틀바/검은 여백을 제거하는 크롭 (2272×1816 소스 공통)
CROP = 'crop=2048:1512:112:156'


def _font(path, sz):
    return pygame.font.Font(path, sz) if os.path.exists(path) \
        else pygame.font.SysFont('monospace', sz, bold=True)


# ── 타이틀 카드 (인트로/아웃트로) ────────────────────────────────────────
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


def _starfield(surf, seed=7):
    import random
    rng = random.Random(seed)
    for _ in range(160):
        sx, sy = rng.randint(0, W), rng.randint(0, H)
        b = rng.randint(40, 150)
        surf.set_at((sx, sy), (b, b, min(255, b + 20)))


def make_card_png(path, line1, line2, sub=None,
                  sz1=88, sz2=132, col1=GOLD_C, col2=GOLD_L):
    pygame.init(); pygame.display.set_mode((1, 1))
    surf = pygame.Surface((W, H)); surf.fill((5, 4, 12))
    _starfield(surf)
    f1, f2 = _font(PX, sz1), _font(PX, sz2)
    h1, h2 = f1.get_height(), f2.get_height()
    gap = 26
    total = h1 + gap + h2
    cy1 = H // 2 - total // 2 + h1 // 2 - (18 if sub else 0)
    cy2 = cy1 + h1 // 2 + gap + h2 // 2
    _glow_text(surf, line1, f1, col1, GOLD_D, W // 2, cy1)
    _glow_text(surf, line2, f2, col2, GOLD_D, W // 2, cy2)
    if sub:
        fs = _font(KF, 40)
        ss = fs.render(sub, True, GREY_C)
        surf.blit(ss, (W // 2 - ss.get_width() // 2, cy2 + h2 // 2 + 34))
    pygame.image.save(surf, path)
    pygame.quit()


# ── 컨셉 라벨 오버레이 (투명 PNG, 좌하단 배너) ──────────────────────────
def make_label_png(path, en, kr, tag, accent):
    pygame.init(); pygame.display.set_mode((1, 1))
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    bx, by = 140, 812
    bw, bh = 900, 190
    # 반투명 어두운 패널 + 좌측 강조 바
    panel = pygame.Surface((bw, bh), pygame.SRCALPHA)
    panel.fill((6, 6, 14, 150))
    surf.blit(panel, (bx, by))
    pygame.draw.rect(surf, accent, (bx, by, 12, bh))
    pygame.draw.rect(surf, (*accent, 60), (bx, by, bw, bh), 2)
    # EN (픽셀 폰트 + 글로우)
    fen = _font(PX, 62)
    ex, ey = bx + 42, by + 30
    for i in range(8):
        a = math.pi * 2 * i / 8
        g = fen.render(en, True, accent); g.set_alpha(40)
        surf.blit(g, (ex + round(math.cos(a) * 3), ey + round(math.sin(a) * 3)))
    surf.blit(fen.render(en, True, (0, 0, 0)), (ex + 3, ey + 3))
    surf.blit(fen.render(en, True, GOLD_L), (ex, ey))
    # KR + 태그라인 (한글 폰트)
    fkr = _font(KF, 46); ftag = _font(KF, 32)
    surf.blit(fkr.render(kr, True, (245, 245, 250)), (bx + 44, by + 104))
    surf.blit(ftag.render(tag, True, (185, 190, 205)), (bx + 44, by + 150))
    pygame.image.save(surf, path)
    pygame.quit()


# ── ffmpeg ──────────────────────────────────────────────────────────────
def run(args, label):
    print(f'  [{label}] ...', flush=True)
    r = subprocess.run(['ffmpeg', '-y', *args], capture_output=True, text=True)
    if r.returncode != 0:
        print('STDERR:', r.stderr[-3500:])
        raise RuntimeError(f'ffmpeg 실패: {label}')
    print(f'  [{label}] ✓')


VENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p']
AENC = ['-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2']


def card_to_video(png, out, dur, fade_in=0.0, fade_out=0.0):
    vf = [f'fps={FPS}', 'format=yuv420p']
    if fade_in > 0:
        vf.insert(1, f'fade=t=in:st=0:d={fade_in}')
    if fade_out > 0:
        vf.insert(1, f'fade=t=out:st={dur-fade_out:.3f}:d={fade_out}')
    run(['-loop', '1', '-i', png,
         '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
         '-t', f'{dur}', '-vf', ','.join(vf), *VENC, *AENC, '-shortest', out],
        f'카드→영상 {os.path.basename(out)}')


def clip_to_video(src, label_png, out, ss, dur, accent_hint='', last=False):
    end_fade = f',fade=t=out:st={dur-0.6:.3f}:d=0.6' if last else ''
    fc = (
        f'[0:v]{CROP},fps={FPS},split=2[bg][fg];'
        f'[bg]scale={W}:{H}:force_original_aspect_ratio=increase,'
        f'crop={W}:{H},gblur=sigma=40,eq=brightness=-0.34:saturation=0.55[bgb];'
        f'[fg]scale=-2:{H}[fgs];'
        f'[bgb][fgs]overlay=(W-w)/2:0[base];'
        f'[1:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1,'
        f'fade=t=out:st={dur-0.8:.3f}:d=0.5:alpha=1[lbl];'
        f'[base][lbl]overlay=0:0[ov];'
        f'[ov]fade=t=in:st=0:d=0.35{end_fade}[v];'
        f'[0:a]afade=t=in:st=0:d=0.25,afade=t=out:st={dur-0.35:.3f}:d=0.35,'
        f'aresample=48000[a]'
    )
    run(['-ss', f'{ss}', '-i', src, '-loop', '1', '-i', label_png,
         '-filter_complex', fc, '-map', '[v]', '-map', '[a]',
         '-t', f'{dur}', '-r', str(FPS), *VENC, *AENC, out],
        f'클립 {os.path.basename(out)}')


def main():
    tmp = tempfile.mkdtemp(prefix='dd_trailer_')
    parts = []
    try:
        # 라벨 PNG
        L = {
            'warrior': ('WARRIOR', '전사', '3연타 콤보 · 드라이브 캔슬', (214, 74, 62)),
            'archer':  ('ARCHER', '궁수', '원거리 관통 · 화살비', (110, 200, 140)),
            'burning': ('BURNING MODE', '버닝 모드', '쏟아지는 적 · 폭발적 손맛', (255, 140, 44)),
            'town':    ('TOWN & QUESTS', '마을 · 퀘스트', '정비 · NPC · 의뢰', (176, 136, 236)),
        }
        for key, (en, kr, tag, acc) in L.items():
            make_label_png(os.path.join(tmp, f'lbl_{key}.png'), en, kr, tag, acc)

        # 인트로
        intro = os.path.join(tmp, '00_intro.mp4')
        make_card_png(os.path.join(tmp, 'intro.png'), 'DUNGEON', 'DOOR',
                      sub='로그라이크 던전 액션')
        card_to_video(os.path.join(tmp, 'intro.png'), intro, 2.6, fade_in=0.5)
        parts.append(intro)

        # 클립들 (src, label, ss, dur, last)
        clips = [
            ('game_tralier_1.mov', 'warrior', 4.5, 6.5, False),
            ('game_trailer_2.mov', 'archer',  7.0, 6.5, False),
            ('game_trailer_3.mov', 'burning', 2.0, 7.5, False),
            ('game_trailer4.mov',  'town',    1.5, 6.0, True),
        ]
        for i, (fn, key, ss, dur, last) in enumerate(clips, 1):
            out = os.path.join(tmp, f'{i:02d}_{key}.mp4')
            clip_to_video(os.path.join(BASE, fn), os.path.join(tmp, f'lbl_{key}.png'),
                          out, ss, dur, last=last)
            parts.append(out)

        # 아웃트로
        outro = os.path.join(tmp, '05_outro.mp4')
        make_card_png(os.path.join(tmp, 'outro.png'), 'DUNGEON DOOR', 'WISHLIST NOW',
                      sub='STEAM 위시리스트에 담아주세요', sz1=76, sz2=52,
                      col1=GOLD_C, col2=GOLD_L)
        card_to_video(os.path.join(tmp, 'outro.png'), outro, 3.2,
                      fade_in=0.5, fade_out=0.6)
        parts.append(outro)

        # concat (동일 코덱/파라미터 → 스트림 복사)
        listf = os.path.join(tmp, 'list.txt')
        with open(listf, 'w') as f:
            for p in parts:
                f.write(f"file '{p}'\n")
        run(['-f', 'concat', '-safe', '0', '-i', listf,
             '-c', 'copy', '-movflags', '+faststart', OUT], '최종 concat')

        mb = os.path.getsize(OUT) / 1024 / 1024
        print(f'\n✅ 완료: {OUT}  ({mb:.1f} MB)')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()

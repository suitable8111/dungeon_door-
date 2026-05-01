#!/usr/bin/env python3
"""SVG → PNG 변환 + 폰트 복사. 최초 1회 실행하면 됩니다."""
import os
import shutil
import sys

try:
    import cairosvg
except ImportError:
    print("cairosvg 없음: pip install cairosvg")
    sys.exit(1)

ROOT    = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, 'data', 'assets')
DST_DIR = os.path.join(ROOT, 'assets')

def convert(src, dst, w=None, h=None):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    kw = {}
    if w: kw['output_width']  = w
    if h: kw['output_height'] = h
    cairosvg.svg2png(url=f'file://{src}', write_to=dst, **kw)
    print(f'  ✓ {os.path.relpath(dst, ROOT)}')

SZ = 32  # TILE_SIZE

SPRITES = [
    'hero', 'hero_attack', 'hero_hurt',
    'enemy_rat', 'enemy_goblin', 'enemy_skeleton',
    'enemy_orc', 'enemy_troll',
    'boss_dark_knight', 'boss_lich',
]

print('── 스프라이트 변환 ──────────────────')
for name in SPRITES:
    src = os.path.join(SRC_DIR, 'sprites', f'{name}.svg')
    dst = os.path.join(DST_DIR, 'sprites', f'{name}.png')
    if os.path.exists(src):
        convert(src, dst, SZ, SZ)
    else:
        print(f'  ✗ {name}.svg 없음')

print('\n── 타이틀 배경 변환 ─────────────────')
convert(
    os.path.join(SRC_DIR, 'title_background.svg'),
    os.path.join(DST_DIR, 'ui', 'title_background.png'),
    1024, 768,
)

print('\n── 폰트 복사 ────────────────────────')
font_src = os.path.join(ROOT, 'data', 'fonts', 'PressStart2P-Regular.ttf')
font_dst = os.path.join(DST_DIR, 'fonts', 'PressStart2P-Regular.ttf')
os.makedirs(os.path.dirname(font_dst), exist_ok=True)
shutil.copy2(font_src, font_dst)
print(f'  ✓ assets/fonts/PressStart2P-Regular.ttf')

print('\n완료!')

# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 6.x spec for DungeonDoor
#   Windows → dist/DungeonDoor/game.exe
#   macOS   → dist/DungeonDoor.app

import os
import sys

from PyInstaller.utils.hooks import collect_all

IS_MAC = sys.platform == 'darwin'
_icon = 'assets/steam/icon.icns' if IS_MAC else 'assets/steam/icon.ico'
if not os.path.exists(_icon):
    _icon = None  # 아이콘은 CI에서 생성 — 없으면 기본 아이콘으로 빌드
GAME_VERSION = os.environ.get('GAME_VERSION', '0.0.0').lstrip('v')

# pygame-ce 전체 수집 (DLL 포함)
pg_datas, pg_binaries, pg_hiddenimports = collect_all('pygame')

# SteamworksPy (설치된 경우에만 — 도전과제 스팀 동기화)
try:
    from PyInstaller.utils.hooks import collect_submodules
    import steamworks  # noqa: F401
    sw_hiddenimports = collect_submodules('steamworks')
except Exception:
    sw_hiddenimports = []

added_datas = [
    ('assets/fonts',   'assets/fonts'),
    ('assets/sprites', 'assets/sprites'),
    ('assets/ui',      'assets/ui'),
    ('data',           'data'),
] + pg_datas

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=pg_binaries,
    datas=added_datas,
    hiddenimports=pg_hiddenimports + [
        'pygame',
        'pygame.font',
        'pygame.freetype',
        'pygame.mixer',
        'pygame.image',
        'pygame.transform',
        'core.game',
        'core.skills',
        'core.input_handler',
        'core.lang',
        'core.save_load',
        'entities.player',
        'entities.enemy',
        'entities.item',
        'entities.entity',
        'map.generator',
        'ui.hud',
        'data_loader',
        'core.achievements',
    ] + sw_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[
        'tkinter',
        'make_capsules', 'build_assets', 'test_main',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='game',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DungeonDoor',
)

if IS_MAC:
    app = BUNDLE(
        coll,
        name='DungeonDoor.app',
        icon=_icon,
        bundle_identifier='com.dungeondoor.game',
        info_plist={
            'CFBundleName': 'Dungeon Door',
            'CFBundleDisplayName': 'Dungeon Door',
            'CFBundleShortVersionString': GAME_VERSION,
            'NSHighResolutionCapable': True,
            'LSApplicationCategoryType': 'public.app-category.games',
        },
    )

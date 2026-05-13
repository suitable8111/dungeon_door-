# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for DungeonDoor → game.exe
# Run on Windows: pyinstaller game.spec

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── 포함할 데이터 파일 (src, dest_in_bundle) ─────────────────────────────
added_datas = [
    ('assets/fonts',   'assets/fonts'),
    ('assets/sprites', 'assets/sprites'),
    ('assets/ui',      'assets/ui'),
    ('data',           'data'),
    ('settings.json',  '.'),
]

# pygame-ce 데이터 파일 자동 수집
added_datas += collect_data_files('pygame')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_datas,
    hiddenimports=[
        'pygame',
        'pygame.mixer',
        'pygame.font',
        'pygame.image',
        'pygame.transform',
        'core.game',
        'core.skills',
        'core.input_handler',
        'core.lang',
        'entities.player',
        'entities.enemy',
        'entities.item',
        'entities.entity',
        'map.generator',
        'ui.hud',
        'data_loader',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'email', 'html', 'http',
        'xml', 'pydoc', 'doctest', 'difflib', 'pickle',
        'make_capsules', 'build_assets', 'test_main',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='game',           # → game.exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # 창 없는 GUI 모드 (콘솔 숨김)
    icon='assets/steam/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DungeonDoor',    # 출력 폴더명 → dist/DungeonDoor/
)

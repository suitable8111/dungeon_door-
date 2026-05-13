# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 6.x spec for DungeonDoor → game.exe

from PyInstaller.utils.hooks import collect_all

# pygame-ce 전체 수집 (DLL 포함)
pg_datas, pg_binaries, pg_hiddenimports = collect_all('pygame')

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
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[
        'tkinter', 'unittest', 'email', 'html', 'http',
        'pydoc', 'doctest', 'difflib',
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
    name='DungeonDoor',
)

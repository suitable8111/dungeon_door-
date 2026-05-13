# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 6.x spec for DungeonDoor → game.exe

from PyInstaller.utils.hooks import collect_data_files

added_datas = [
    ('assets/fonts',   'assets/fonts'),
    ('assets/sprites', 'assets/sprites'),
    ('assets/ui',      'assets/ui'),
    ('data',           'data'),
]

try:
    added_datas += collect_data_files('pygame')
except Exception:
    pass

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
        'xml', 'pydoc', 'doctest', 'difflib',
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

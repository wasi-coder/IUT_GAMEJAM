# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

datas = [('crow', 'crow'), ('Dragon', 'Dragon'), ('ghosts', 'ghosts'), ('map1', 'map1'), ('map2', 'map2'), ('map3', 'map3'), ('map4', 'map4'), ('map6', 'map6'), ('map7', 'map7'), ('map8', 'map8'), ('npc1', 'npc1'), ('npc2', 'npc2'), ('npc3', 'npc3'), ('openingvid', 'openingvid'), ('Orge', 'Orge'), ('player', 'player'), ('portal', 'portal'), ('slime', 'slime'), ('toads', 'toads'), ('Green Portal Sprite Sheet.png', '.')]
binaries = []
hiddenimports = []

# Conda keeps Python's native runtime dependencies in Library/bin. Add the
# dependencies used by Python's standard extension modules explicitly so a
# clean build does not depend on the shell's PATH configuration.
conda_runtime_dir = Path(sys.executable).parent / 'Library' / 'bin'
for runtime_dll in (
    'LIBBZ2.dll',
    'ffi.dll',
    'libcrypto-3-x64.dll',
    'libexpat.dll',
    'liblzma.dll',
    'libmpdec-4.dll',
    'libssl-3-x64.dll',
):
    runtime_path = conda_runtime_dir / runtime_dll
    if runtime_path.exists():
        binaries.append((str(runtime_path), '.'))

tmp_ret = collect_all('imageio_ffmpeg')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='The Broken Rite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

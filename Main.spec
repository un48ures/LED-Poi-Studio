# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Studio.py'],
    pathex=['.'],
    binaries=[],
    datas=[('C:/Users/felix/PycharmProjects/LED-Poi-Studio/Studio_GUI.ui', '.'),('C:/Users/felix/PycharmProjects/LED-Poi-Studio/icon_LS_v2_128_128.ico','.')],
    hiddenimports=['numpy'],
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
    name='LED_Poi_Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
	icon='C:/Users/felix/PycharmProjects/LED-Poi-Studio/icon_LS_v2_128_128.ico'
)

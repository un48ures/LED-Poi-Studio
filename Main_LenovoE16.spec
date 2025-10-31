# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Studio.py'],
    pathex=['.'],
    binaries=[],
    datas = [
    ('C:/Users/aac_n/Documents/work/LED-Poi-Studio/GUI_files/Studio_GUI_new_v2.ui', 'GUI_files'),
    ('C:/Users/aac_n/Documents/work/LED-Poi-Studio/Icons/icon_LS_v2_128_128.ico', 'Icons')
	],
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
    name='LED_Poi_Studio_vX.X.X',
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
	icon='C:/Users/aac_n/Documents/work/LED-Poi-Studio/Icons/icon_LS_v2_128_128.ico'
)

# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pos_app\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('pos_app/config', 'pos_app/config'), ('pos_app/utils/config', 'pos_app/utils/config'), ('pos_app/reports', 'pos_app/reports'), ('pos_app/documents', 'pos_app/documents'), ('pos_app/exports', 'pos_app/exports')],
    hiddenimports=[],
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
    name='POS_System_Light',
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

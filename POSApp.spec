# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pos_app\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('pos_app/config', 'pos_app/config'), ('pos_app/ui', 'pos_app/ui'), ('pos_app/reports', 'pos_app/reports'), ('pos_app/documents', 'pos_app/documents'), ('pos_app/network_config.json', 'pos_app')],
    hiddenimports=['psycopg2', 'psycopg2_binary'],
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
    [],
    exclude_binaries=True,
    name='POSApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='POSApp',
)

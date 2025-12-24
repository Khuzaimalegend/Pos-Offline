# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

a = Analysis(
    ['pos_app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('pos_app/config', 'pos_app/config'),
        ('pos_app/ui', 'pos_app/ui'),
        ('pos_app/reports', 'pos_app/reports'),
        ('pos_app/documents', 'pos_app/documents'),
        ('pos_app/network_config.json', 'pos_app')
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtPrintSupport',
        'PySide6.QtGui',
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'sqlalchemy',
        'psycopg2',
        'pos_app.models',
        'pos_app.views',
        'pos_app.controllers',
        'pos_app.utils',
        'pos_app.database',
    ] + collect_submodules('pos_app'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='POSSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

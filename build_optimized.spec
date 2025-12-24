# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

excluded_imports = [
    'matplotlib', 'scipy', 'pytest', 'tensorflow', 'torch', 
    'notebook', 'jupyter', 'ipykernel', 'IPython',
    'django', 'flask', 'boto3', 'botocore', 'pandas',
    'numpy', 'openpyxl', 'reportlab'
]

a = Analysis(
    ['pos_app/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtXml',
        'sqlalchemy',
        'psycopg2',
        'cryptography',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_imports,
    cipher=block_cipher,
    noarchive=True,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='POS_System_Light',
    debug=False,
    bootloader_ignore_signals=True,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    optimize=2,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='POS_System_Light'
)
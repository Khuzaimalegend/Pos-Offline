# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['pos_app/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6',
        'sqlalchemy',
        'psycopg2',
        'psycopg2-binary',
        'sqlalchemy.dialects.postgresql',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy_utils',
        'reportlab',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL._tkinter_finder',
        'pkg_resources.py2_warn',
        'pkg_resources.markers',
        'pandas',
        'numpy',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.worksheet',
        'openpyxl.worksheet.page',
        'openpyxl.worksheet.header_footer',
        'openpyxl.worksheet.pagebreak',
        'openpyxl.worksheet.dimensions',
        'openpyxl.worksheet.views',
        'openpyxl.worksheet.filters',
        'openpyxl.worksheet.datavalidation',
        'openpyxl.worksheet.table',
        'openpyxl.worksheet.cell_range',
        'openpyxl.worksheet.copier',
        'openpyxl.worksheet.pagebreak',
        'openpyxl.worksheet.properties',
        'openpyxl.worksheet.worksheet',
        'openpyxl.worksheet._read_only',
        'openpyxl.worksheet._write_only',
        'openpyxl.worksheet._reader',
        'openpyxl.worksheet._writer',
        'openpyxl.worksheet._read_only',
        'openpyxl.worksheet._write_only',
        'openpyxl.worksheet._reader',
        'openpyxl.worksheet._writer',
        'openpyxl.worksheet._read_only',
        'openpyxl.worksheet._write_only',
        'openpyxl.worksheet._reader',
        'openpyxl.worksheet._writer',
        'openpyxl.worksheet._read_only',
        'openpyxl.worksheet._write_only',
        'openpyxl.worksheet._reader',
        'openpyxl.worksheet._writer',
    ],
    hookspath=[],
    hooksconfig={},
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add any data files
for d in ['config', 'ui', 'data', 'documents']:
    a.datas += Tree(os.path.join('pos_app', d), os.path.join('pos_app', d))

# Add any binary files
# a.binaries += [('path/to/binary', 'binary_name', 'BINARY')]

# Set the application icon if you have one
# icon_path = 'path/to/icon.ico'
# exe = a.analyze()
# exe.icon = icon_path

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='POS_App',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False to hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# Create a single folder distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='POS_App',
)

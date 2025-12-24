"""
Build script to create EXE for POS Application
Uses PyInstaller to bundle the application into a standalone executable
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")

def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")
    
    required_packages = [
        'PyInstaller',
        'PySide6',
        'sqlalchemy',
        'psycopg2-binary',
        'requests'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package.lower() == 'pyinstaller':
                __import__('PyInstaller')
            else:
                __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        for package in missing_packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print("✅ All packages installed successfully")
    else:
        print("\n✅ All dependencies are installed")

def clean_build_dirs():
    """Clean previous build directories"""
    print_header("Cleaning Previous Builds")
    
    # Kill any running POSSystem processes
    try:
        import subprocess
        subprocess.run(['taskkill', '/F', '/IM', 'POSSystem.exe'], 
                      capture_output=True, timeout=5)
        print("[OK] Terminated any running POSSystem processes")
    except Exception as e:
        print(f"[WARN] Could not kill processes: {e}")
    
    import time
    time.sleep(2)
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}...")
            try:
                shutil.rmtree(dir_name)
                print(f"[OK] Removed {dir_name}")
            except PermissionError:
                print(f"[WARN] Could not remove {dir_name} (in use), retrying...")
                time.sleep(2)
                try:
                    shutil.rmtree(dir_name)
                    print(f"[OK] Removed {dir_name} on retry")
                except Exception as e:
                    print(f"[WARN] Skipping {dir_name}: {e}")

def create_spec_file():
    """Create PyInstaller spec file for standalone EXE"""
    print_header("Creating PyInstaller Spec File")
    
    # Prepare datas list, only include existing directories/files
    datas = []
    if os.path.exists('pos_app/config'):
        datas.append(('pos_app/config', 'pos_app/config'))
    if os.path.exists('pos_app/ui'):
        datas.append(('pos_app/ui', 'pos_app/ui'))
    if os.path.exists('pos_app/reports'):
        datas.append(('pos_app/reports', 'pos_app/reports'))
    if os.path.exists('pos_app/documents'):
        datas.append(('pos_app/documents', 'pos_app/documents'))
    if os.path.exists('pos_app/network_config.json'):
        datas.append(('pos_app/network_config.json', 'pos_app'))
    
    datas_str = ',\n        '.join([f"('{src}', '{dst}')" for src, dst in datas])
    
    # Check for icon file
    icon_path = 'pos_app/ui/assets/icon.ico' if os.path.exists('pos_app/ui/assets/icon.ico') else 'None'
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

a = Analysis(
    ['pos_app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        {datas_str}
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
    hooksconfig={{}},
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
    icon={icon_path},
)
'''
    
    with open('POSSystem.spec', 'w') as f:
        f.write(spec_content)
    print("✅ Created POSSystem.spec")

def build_exe():
    """Build the executable using PyInstaller"""
    print_header("Building Executable")
    
    try:
        print("Running PyInstaller...")
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', 'POSSystem.spec', '--distpath', 'dist', '--workpath', 'build'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Executable built successfully")
            return True
        else:
            print(f"❌ Build failed:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error during build: {e}")
        return False

def create_installer_script():
    """Create a simple installer batch script"""
    print_header("Creating Installer Script")
    
    installer_content = '''@echo off
REM POS System Installer
REM This script installs the POS System application

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo   POS SYSTEM INSTALLER
echo ================================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This installer requires administrator privileges.
    echo Please run this script as Administrator.
    pause
    exit /b 1
)

REM Define installation directory
set "INSTALL_DIR=%ProgramFiles%\\POSSystem"

REM Create installation directory
if not exist "!INSTALL_DIR!" (
    mkdir "!INSTALL_DIR!"
    echo Created installation directory: !INSTALL_DIR!
)

REM Copy application files
echo Copying application files...
xcopy /E /I /Y "dist\\POSSystem" "!INSTALL_DIR!" >nul
echo [OK] Files copied successfully

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\\POSSystem.lnk'); $Shortcut.TargetPath = '!INSTALL_DIR!\\POSSystem.exe'; $Shortcut.Save()"
echo [OK] Desktop shortcut created

REM Create Start Menu shortcut
echo Creating Start Menu shortcut...
set "START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('!START_MENU!\\POSSystem.lnk'); $Shortcut.TargetPath = '!INSTALL_DIR!\\POSSystem.exe'; $Shortcut.Save()"
echo [OK] Start Menu shortcut created

echo.
echo ================================================================================
echo   INSTALLATION COMPLETE
echo ================================================================================
echo.
echo The POS System has been installed successfully!
echo You can launch it from:
echo   - Desktop shortcut
echo   - Start Menu
echo   - !INSTALL_DIR!\\POSSystem.exe
echo.
pause
'''
    
    with open('dist/install.bat', 'w', encoding='utf-8') as f:
        f.write(installer_content)
    print("[OK] Created install.bat")

def create_uninstaller_script():
    """Create an uninstaller script"""
    print_header("Creating Uninstaller Script")
    
    uninstaller_content = '''@echo off
REM POS System Uninstaller

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo   POS SYSTEM UNINSTALLER
echo ================================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This uninstaller requires administrator privileges.
    echo Please run this script as Administrator.
    pause
    exit /b 1
)

set "INSTALL_DIR=%ProgramFiles%\\POSSystem"

REM Confirm uninstallation
echo Are you sure you want to uninstall POS System?
set /p confirm="Type 'yes' to confirm: "
if /i not "!confirm!"=="yes" (
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

REM Remove installation directory
if exist "!INSTALL_DIR!" (
    echo Removing application files...
    rmdir /S /Q "!INSTALL_DIR!"
    echo [OK] Application files removed
)

REM Remove desktop shortcut
if exist "%USERPROFILE%\\Desktop\\POSSystem.lnk" (
    del "%USERPROFILE%\\Desktop\\POSSystem.lnk"
    echo [OK] Desktop shortcut removed
)

REM Remove Start Menu shortcut
set "START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"
if exist "!START_MENU!\\POSSystem.lnk" (
    del "!START_MENU!\\POSSystem.lnk"
    echo [OK] Start Menu shortcut removed
)

echo.
echo ================================================================================
echo   UNINSTALLATION COMPLETE
echo ================================================================================
echo.
pause
'''
    
    with open('dist/uninstall.bat', 'w', encoding='utf-8') as f:
        f.write(uninstaller_content)
    print("[OK] Created uninstall.bat")

def create_readme():
    """Create README file"""
    print_header("Creating README")
    
    readme_content = '''# POS SYSTEM - Installation Guide

## System Requirements
- Windows 7 or later
- 4GB RAM minimum
- 500MB disk space
- PostgreSQL 12 or later (for network mode)

## Installation

### Option 1: Automated Installation
1. Run `install.bat` as Administrator
2. Follow the on-screen instructions
3. The application will be installed to `C:\\Program Files\\POSSystem`

### Option 2: Manual Installation
1. Extract the contents of `dist/POSSystem` to your desired location
2. Run `POSSystem.exe`

## First Run

### Database Configuration
On first run, the application will:
1. Attempt to connect to an existing PostgreSQL server on the network
2. If no server is found, it will try to use a local PostgreSQL instance
3. If local PostgreSQL is not available, it will run in OFFLINE MODE

### License
You will be prompted to enter a license key on first run.
Default license key: `yallahmaA1!23`

## Database Migration

If you're upgrading from a previous version:
1. Run `migration_new_pc.py` before starting the application
2. This will update your database schema to match the new application

## Uninstallation

To uninstall the application:
1. Run `uninstall.bat` as Administrator
2. Confirm when prompted
3. All application files and shortcuts will be removed

## Troubleshooting

### Cannot Connect to Database
- Ensure PostgreSQL is running
- Check network connectivity
- Verify database credentials in `pos_app/config/database.json`

### Application Won't Start
- Check that all dependencies are installed
- Run the application from command line to see error messages
- Check the error logs in the application directory

### License Issues
- Ensure you're using the correct license key
- Check that the license file is not corrupted
- Try deleting the license file and re-entering the key

## Support

For issues or questions, please contact support or check the application logs.

## Version
POS System v1.0
'''
    
    with open('dist/README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("[OK] Created README.txt")

def main():
    """Main build function"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "POS SYSTEM - EXE BUILD SCRIPT".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run build steps
    check_dependencies()
    clean_build_dirs()
    create_spec_file()
    
    if build_exe():
        print_header("Build Complete")
        print("[OK] Standalone EXE built successfully!")
        print("\nOutput location: dist/POSSystem/POSSystem.exe")
        print("\nYou can now:")
        print("1. Run the EXE directly: dist/POSSystem/POSSystem.exe")
        print("2. Copy it to any location and run it")
        print("3. Create a shortcut to it on your desktop")
        print("\nNo installation required!")
        print("\n")
    else:
        print_header("Build Failed")
        print("[ERROR] EXE build failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()

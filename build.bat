@echo off
echo Creating POS Application Executable...
echo.

REM Clean up previous build
if exist "build" (
    echo Removing old build directory...
    rmdir /s /q build
)

if exist "dist" (
    echo Removing old dist directory...
    rmdir /s /q dist
)

REM Build the executable
echo.
echo Building the application...
pyinstaller --clean --noconfirm pos_app.spec

if %ERRORLEVEL% NEQ 0 (
    echo Error during build process.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Build completed successfully!
echo The executable is in the 'dist' folder.

REM Open the dist folder in Explorer
start "" "dist"

pause

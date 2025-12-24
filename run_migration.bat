@echo off
REM POS System Database Migration Runner
REM This script runs the database migration to update schema

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo   POS SYSTEM DATABASE MIGRATION
echo ================================================================================
echo.
echo This script will update your database schema to match the new application.
echo All existing data will be preserved.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or later from https://www.python.org/
    pause
    exit /b 1
)

REM Check if migration script exists
if not exist "migration_new_pc.py" (
    echo Error: migration_new_pc.py not found in current directory.
    echo Please ensure you're running this script from the POS application directory.
    pause
    exit /b 1
)

REM Run the migration
echo Starting database migration...
echo.
python migration_new_pc.py

if %errorLevel% neq 0 (
    echo.
    echo Error: Migration failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo   MIGRATION COMPLETED
echo ================================================================================
echo.
echo The database migration has completed successfully.
echo You can now run the POS application.
echo.
pause

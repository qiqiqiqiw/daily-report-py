@echo off
setlocal

set APP_NAME=GitDailyReport
set DIST_DIR=dist
set BUILD_DIR=build

echo === Step 1: Clean previous builds ===
if exist "%BUILD_DIR%\%APP_NAME%" rmdir /s /q "%BUILD_DIR%\%APP_NAME%"
if exist "%DIST_DIR%\%APP_NAME%" rmdir /s /q "%DIST_DIR%\%APP_NAME%"

echo === Step 2: Activate virtual environment ===
if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat

echo === Step 3: Install PyInstaller ===
python -m pip install pyinstaller Pillow --quiet 2>nul

echo === Step 4: Run PyInstaller ===
python -m PyInstaller daily-report-windows.spec --noconfirm --clean

echo === Step 5: Create data directory ===
mkdir "%DIST_DIR%\%APP_NAME%\data" 2>nul

echo.
echo === Build complete ===
echo   Executable: %DIST_DIR%\%APP_NAME%\GitDailyReport.exe
echo.
pause

@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================
echo   Meeting Nameplate Build Tool
echo ========================================
echo.

set "PYTHON=D:\Python\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"

"%PYTHON%" --version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

"%PYTHON%" -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    "%PYTHON%" -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] PyInstaller installation failed.
        pause
        exit /b 1
    )
)

echo [1/3] Cleaning old build files...
if exist build rmdir /s /q build
if exist "dist\会议桌牌打印系统" rmdir /s /q "dist\会议桌牌打印系统"
if not exist dist mkdir dist

echo [2/3] Building EXE...
"%PYTHON%" -m PyInstaller --noconfirm --clean "会议桌牌打印系统.spec"
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

echo [3/3] Removing user configuration files...
if exist "dist\会议桌牌打印系统\config.ini" del /f /q "dist\会议桌牌打印系统\config.ini"
if exist "dist\会议桌牌打印系统\config.json" del /f /q "dist\会议桌牌打印系统\config.json"
if exist "dist\会议桌牌打印系统\settings.ini" del /f /q "dist\会议桌牌打印系统\settings.ini"
if exist "dist\会议桌牌打印系统\settings.json" del /f /q "dist\会议桌牌打印系统\settings.json"
if exist "dist\会议桌牌打印系统\history.json" del /f /q "dist\会议桌牌打印系统\history.json"
if exist "dist\会议桌牌打印系统\history.ini" del /f /q "dist\会议桌牌打印系统\history.ini"
if exist "dist\会议桌牌打印系统\crash.log" del /f /q "dist\会议桌牌打印系统\crash.log"

if exist "dist\会议桌牌打印系统\config.json" (
    echo [ERROR] Personal config file is still present.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build completed
echo ========================================
echo.
echo EXE folder:
echo %CD%\dist\会议桌牌打印系统\
echo.
echo Personal configuration files were excluded.
echo Open Inno Setup 7: 会议桌牌打印系统.iss
echo.
pause
endlocal

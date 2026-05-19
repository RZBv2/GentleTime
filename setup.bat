@echo off
title GentleTime Installer
echo ========================================
echo        GentleTime ✦ Installer
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.7 or higher from python.org
    pause
    exit /b 1
)

:: Display Python version
echo [✓] Python found:
python --version
echo.

:: Install requirements
echo [1/3] Installing dependencies...
pip install pyttsx3
if errorlevel 1 (
    echo [!] TTS installation failed (optional feature)
)

:: Run the application
echo [2/3] Launching GentleTime...
echo.
python gentletime.py

echo.
echo [3/3] Installation complete!
echo.
echo To run again, use: python gentletime.py
pause
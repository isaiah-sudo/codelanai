@echo off
title CodeLan AI Studio - Reinforcement Learning Engine
color 0B

echo =======================================================
echo     CODELAN AI STUDIO - REINFORCEMENT LEARNING
echo =======================================================
echo.

where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [LAUNCHER] Starting via Python...
    python app.py
) else (
    echo [LAUNCHER] Python not found in PATH, launching standalone executable...
    start "" "dist\codelan_ai\codelan_ai.exe"
)

pause

@echo off
REM Setup_Admin.bat - Run the daily automation setup as administrator

echo ========================================
echo  SureBet Daily Automation Setup
echo ========================================
echo.
echo This will create Windows scheduled tasks for:
echo   1. Daily workflow (9:00 AM)
echo   2. Health monitor (every 2 hours)
echo.
echo You need to run this as Administrator.
echo.
pause

REM Check for admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: This script must be run as Administrator!
    echo.
    echo Please:
    echo   1. Right-click this file
    echo   2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo.
echo Running setup with Administrator privileges...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_daily_automation.ps1"

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
pause

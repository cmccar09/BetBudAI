@echo off
REM Quick script to generate picks immediately
REM Use this to test or manually trigger picks generation

echo ================================================================
echo BetBudAI - Generate Picks NOW
echo ================================================================
echo.
echo This will run the full workflow to generate today's picks.
echo Duration: Approximately 5-15 minutes
echo.
echo Press Ctrl+C to cancel, or
pause

cd /d "%~dp0"

echo.
echo [1/4] Starting workflow...
echo.

python run_all_workflows.py

echo.
echo ================================================================
echo Workflow Complete!
echo ================================================================
echo.
echo Next steps:
echo   1. Check for any errors above
echo   2. Verify picks at https://www.betbudai.com
echo   3. Picks should appear within 1-2 minutes
echo.
pause

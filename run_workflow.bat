@echo off
cd /d "C:\Users\charl\OneDrive\futuregenAI\Betting"
REM Set AWS credentials from user profile
set AWS_CONFIG_FILE=%USERPROFILE%\.aws\config
set AWS_SHARED_CREDENTIALS_FILE=%USERPROFILE%\.aws\credentials
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scheduled_workflow.ps1" >> logs\task_output.log 2>&1

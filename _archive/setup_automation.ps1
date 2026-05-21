# Automated Results & Learning System Setup
# Creates scheduled tasks for:
# 1. Hourly results fetching from Betfair
# 2. Daily learning cycle (analyzes all results and improves AI)

$ErrorActionPreference = "Stop"

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "Setting Up Automated Results & Learning System" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

$scriptPath = $PSScriptRoot
$pythonExe = "$scriptPath\.venv\Scripts\python.exe"

# Task 1: Hourly Results Fetcher
Write-Host "Creating Task 1: Hourly Results Fetcher" -ForegroundColor Yellow
Write-Host "  Runs: Every hour" -ForegroundColor Gray
Write-Host "  Purpose: Fetch race results from Betfair and update DynamoDB" -ForegroundColor Gray
Write-Host ""

$action1 = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "$scriptPath\fetch_hourly_results.py" `
    -WorkingDirectory $scriptPath

$trigger1 = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)

$settings1 = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

try {
    Unregister-ScheduledTask -TaskName "BettingResultsFetcher" -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask `
        -TaskName "BettingResultsFetcher" `
        -Action $action1 `
        -Trigger $trigger1 `
        -Settings $settings1 `
        -Description "Fetches betting results from Betfair every hour" `
        -RunLevel Highest
    
    Write-Host "  ✅ Task created: BettingResultsFetcher" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Failed to create task: $_" -ForegroundColor Red
}

Write-Host ""

# Task 2: Daily Learning Cycle
Write-Host "Creating Task 2: Daily Learning Cycle" -ForegroundColor Yellow
Write-Host "  Runs: Daily at 11:00 PM" -ForegroundColor Gray
Write-Host "  Purpose: Analyze all results, generate insights, improve AI" -ForegroundColor Gray
Write-Host ""

$action2 = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "$scriptPath\daily_learning_cycle.py" `
    -WorkingDirectory $scriptPath

$trigger2 = New-ScheduledTaskTrigger -Daily -At "23:00"

$settings2 = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

try {
    Unregister-ScheduledTask -TaskName "BettingLearningCycle" -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask `
        -TaskName "BettingLearningCycle" `
        -Action $action2 `
        -Trigger $trigger2 `
        -Settings $settings2 `
        -Description "Daily learning cycle: analyzes results and generates AI insights" `
        -RunLevel Highest
    
    Write-Host "  ✅ Task created: BettingLearningCycle" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Failed to create task: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "AUTOMATION SETUP COMPLETE" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ Hourly Results Fetcher:" -ForegroundColor Green
Write-Host "   - Checks Betfair every hour for completed races" -ForegroundColor Gray
Write-Host "   - Updates pick outcomes (WON/PLACED/LOST)" -ForegroundColor Gray
Write-Host "   - Calculates profit/loss" -ForegroundColor Gray
Write-Host ""

Write-Host "✅ Daily Learning Cycle (11 PM):" -ForegroundColor Green
Write-Host "   - Analyzes all completed bets from the day" -ForegroundColor Gray
Write-Host "   - Identifies what worked and what didn't" -ForegroundColor Gray
Write-Host "   - Generates insights for AI improvement" -ForegroundColor Gray
Write-Host "   - Uploads learning data to S3" -ForegroundColor Gray
Write-Host ""

Write-Host "View tasks:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName 'Betting*'" -ForegroundColor Cyan
Write-Host ""

Write-Host "Test now:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName 'BettingResultsFetcher'" -ForegroundColor Cyan
Write-Host "  Start-ScheduledTask -TaskName 'BettingLearningCycle'" -ForegroundColor Cyan
Write-Host ""

Write-Host "The system is now fully automated! 🎉" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan

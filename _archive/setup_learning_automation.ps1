# Add Daily Learning Cycle to Automation
# Analyzes results and improves AI based on outcomes

$ErrorActionPreference = "Stop"

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "Adding Daily Learning Cycle to Automation" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

$scriptPath = $PSScriptRoot
$pythonExe = "$scriptPath\.venv\Scripts\python.exe"

Write-Host "Creating: Daily Learning Cycle Task" -ForegroundColor Yellow
Write-Host "  Runs: Daily at 11:00 PM" -ForegroundColor Gray
Write-Host "  Purpose: Analyze results + generate AI insights" -ForegroundColor Gray
Write-Host ""

$action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "$scriptPath\daily_learning_cycle.py" `
    -WorkingDirectory $scriptPath

$trigger = New-ScheduledTaskTrigger -Daily -At "23:00"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

try {
    # Remove old task if exists
    Unregister-ScheduledTask -TaskName "SureBet-Daily-Learning" -Confirm:$false -ErrorAction SilentlyContinue
    
    # Create new task
    Register-ScheduledTask `
        -TaskName "SureBet-Daily-Learning" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Daily learning cycle: analyzes betting results and generates AI insights for continuous improvement"
    
    Write-Host "  ✅ Task created: SureBet-Daily-Learning" -ForegroundColor Green
    Write-Host ""
    
    # Show task details
    $task = Get-ScheduledTask -TaskName "SureBet-Daily-Learning"
    $info = Get-ScheduledTaskInfo $task
    
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $($task.TaskName)" -ForegroundColor Gray
    Write-Host "  State: $($task.State)" -ForegroundColor Gray
    Write-Host "  Next Run: $($info.NextRunTime)" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "  ❌ Failed to create task: $_" -ForegroundColor Red
    exit 1
}

Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "COMPLETE AUTOMATION SYSTEM" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ Hourly Results Fetcher (Already Running):" -ForegroundColor Green
Write-Host "   Task: SureBet-Hourly-ResultsFetcher" -ForegroundColor Gray
Write-Host "   → Fetches Betfair results every hour" -ForegroundColor Gray
Write-Host "   → Updates outcomes in DynamoDB" -ForegroundColor Gray
Write-Host ""

Write-Host "✅ Daily Learning Cycle (NEW - 11 PM):" -ForegroundColor Green
Write-Host "   Task: SureBet-Daily-Learning" -ForegroundColor Gray
Write-Host "   → Analyzes all completed bets" -ForegroundColor Gray
Write-Host "   → Calculates win rates & ROI" -ForegroundColor Gray
Write-Host "   → Identifies patterns in winners/losers" -ForegroundColor Gray
Write-Host "   → Generates insights for AI" -ForegroundColor Gray
Write-Host "   → Uploads to S3 (betting-insights/winner_analysis.json)" -ForegroundColor Gray
Write-Host ""

Write-Host "How it works:" -ForegroundColor Yellow
Write-Host "  1. Every hour: Fetch results from Betfair" -ForegroundColor Cyan
Write-Host "  2. Every night at 11 PM: Analyze ALL results" -ForegroundColor Cyan
Write-Host "  3. Generate insights (what works, what doesn't)" -ForegroundColor Cyan
Write-Host "  4. AI uses insights for tomorrow's picks" -ForegroundColor Cyan
Write-Host "  5. Continuous improvement! 📈" -ForegroundColor Cyan
Write-Host ""

Write-Host "Test the learning cycle now:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName 'SureBet-Daily-Learning'" -ForegroundColor Cyan
Write-Host ""

Write-Host "View all automation tasks:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName 'SureBet-*'" -ForegroundColor Cyan
Write-Host ""

Write-Host "🎉 Self-learning system is now active!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan

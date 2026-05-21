# Setup Daily Learning Task
# This creates a Windows Task Scheduler task to run learning cycle at 8 AM daily

Write-Host "`nSetting up Daily Learning Cycle..." -ForegroundColor Green

$pythonExe = (Get-Command python).Source
$scriptPath = Join-Path $PSScriptRoot "daily_learning_cycle.py"
$logPath = Join-Path $PSScriptRoot "logs"

# Ensure logs directory exists
if (!(Test-Path $logPath)) {
    New-Item -ItemType Directory -Path $logPath | Out-Null
}

# Create task action
$action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "`"$scriptPath`"" `
    -WorkingDirectory $PSScriptRoot

# Create trigger - Daily at 8:00 AM
$trigger = New-ScheduledTaskTrigger -Daily -At "08:00"

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Create principal (run whether user is logged on or not)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType S4U `
    -RunLevel Highest

try {
    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName "BettingDailyLearning" -ErrorAction SilentlyContinue
    
    if ($existingTask) {
        Write-Host "Task already exists, updating..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName "BettingDailyLearning" -Confirm:$false
    }
    
    # Register the task
    Register-ScheduledTask `
        -TaskName "BettingDailyLearning" `
        -Description "Daily learning cycle for betting AI - analyzes performance and updates strategy" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal
    
    Write-Host "`n✓ Daily Learning Task Created Successfully!" -ForegroundColor Green
    Write-Host "`nTask Details:" -ForegroundColor Cyan
    Write-Host "  Name:       BettingDailyLearning"
    Write-Host "  Schedule:   Daily at 8:00 AM"
    Write-Host "  Python:     $pythonExe"
    Write-Host "  Script:     $scriptPath"
    Write-Host "`nWhat it does:" -ForegroundColor Cyan
    Write-Host "  • Loads last 30 days of bet results"
    Write-Host "  • Analyzes performance patterns"
    Write-Host "  • Updates prompt.txt with learnings"
    Write-Host "  • Adjusts current bankroll"
    Write-Host "  • Updates Lambda configuration"
    Write-Host "`nManage task:" -ForegroundColor Yellow
    Write-Host "  View:    Get-ScheduledTask -TaskName 'BettingDailyLearning'"
    Write-Host "  Run now: Start-ScheduledTask -TaskName 'BettingDailyLearning'"
    Write-Host "  Remove:  Unregister-ScheduledTask -TaskName 'BettingDailyLearning'"
    
} catch {
    Write-Host "`n❌ Error creating task: $_" -ForegroundColor Red
    Write-Host "`nYou may need to run as Administrator" -ForegroundColor Yellow
}

Write-Host "`n" -NoNewline

# Setup Windows Task Scheduler to run daily workflow automatically
# Runs at 9:00 AM daily (before racing starts)

$taskName = "BettingDailyWorkflow"
$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\daily_automated_workflow.py"
$pythonPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\.venv\Scripts\python.exe"
$workingDir = "C:\Users\charl\OneDrive\futuregenAI\Betting"

Write-Host "Setting up daily automated workflow..." -ForegroundColor Cyan

# Delete existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create action
$action = New-ScheduledTaskAction -Execute $pythonPath `
    -Argument $scriptPath `
    -WorkingDirectory $workingDir

# Create trigger (daily at 9:00 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00AM"

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register the task
Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Daily automated betting workflow - fetches races, analyzes, generates picks" `
    -Force

Write-Host "`n✓ Daily workflow scheduled successfully!" -ForegroundColor Green
Write-Host "  Task Name: $taskName" -ForegroundColor White
Write-Host "  Schedule: Daily at 9:00 AM" -ForegroundColor White
Write-Host "  Script: $scriptPath" -ForegroundColor White
Write-Host "`nTo view task: taskschd.msc" -ForegroundColor Yellow
Write-Host "To run manually: python daily_automated_workflow.py" -ForegroundColor Yellow

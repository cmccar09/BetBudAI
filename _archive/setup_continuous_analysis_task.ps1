# Setup Continuous Race Analysis Task
# Runs every 30 minutes throughout the day to analyze new races and generate UI picks

$TaskName = "ContinuousRaceAnalysis"
$ScriptPath = "$PSScriptRoot\complete_daily_analysis.py"
$PythonExe = "$PSScriptRoot\.venv\Scripts\python.exe"
$LogFile = "$PSScriptRoot\continuous_analysis_log.txt"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setting up Continuous Race Analysis Task" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Remove existing task if it exists
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "`nRemoving existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create action
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$ScriptPath`" >> `"$LogFile`" 2>&1" `
    -WorkingDirectory $PSScriptRoot

# Create trigger - Every 30 minutes from 7 AM to 11 PM
$Trigger = New-ScheduledTaskTrigger `
    -Once `
    -At "07:00" `
    -RepetitionInterval (New-TimeSpan -Minutes 30) `
    -RepetitionDuration (New-TimeSpan -Hours 16)

# Task settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -MultipleInstances IgnoreNew

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Analyze races every 30 minutes from 7 AM to 11 PM, generate UI picks for high-confidence selections (85+)" `
    -User $env:USERNAME `
    -RunLevel Highest

Write-Host "`n✓ Task created successfully!" -ForegroundColor Green
Write-Host "`nTask Details:" -ForegroundColor Cyan
Write-Host "  Name: $TaskName" -ForegroundColor White
Write-Host "  Script: $ScriptPath" -ForegroundColor White
Write-Host "  Schedule: Every 30 minutes from 7:00 AM to 11:00 PM" -ForegroundColor White
Write-Host "  Log: $LogFile" -ForegroundColor White
Write-Host "`nThe task will:" -ForegroundColor Cyan
Write-Host "  1. Fetch latest races from Betfair" -ForegroundColor White
Write-Host "  2. Analyze all horses with comprehensive scoring" -ForegroundColor White
Write-Host "  3. Generate UI picks for 85+ confidence" -ForegroundColor White
Write-Host "  4. Update database for learning" -ForegroundColor White
Write-Host "`nNext run times:" -ForegroundColor Cyan

# Show next few run times
$nextRun = Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo
Write-Host "  Next run: $($nextRun.NextRunTime)" -ForegroundColor Green

Write-Host "`nTo manually run now:" -ForegroundColor Cyan
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Yellow
Write-Host "`nTo view logs:" -ForegroundColor Cyan
Write-Host "  Get-Content '$LogFile' -Tail 50" -ForegroundColor Yellow
Write-Host "`n========================================" -ForegroundColor Cyan

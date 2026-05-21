# Setup Daily Performance Report Task
# Runs at 7:00 PM every day to show how AI predictions performed

$TaskName = "DailyPerformanceReport"
$ScriptPath = "$PSScriptRoot\daily_performance_report.py"
$PythonExe = "$PSScriptRoot\.venv\Scripts\python.exe"
$LogFile = "$PSScriptRoot\performance_report_log.txt"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setting up Daily Performance Report Task" -ForegroundColor Cyan
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

# Create trigger - Daily at 7:00 PM
$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At "19:00"

# Task settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Generate daily performance report comparing AI tips vs actual race results" `
    -User $env:USERNAME `
    -RunLevel Highest

Write-Host "`n✓ Task created successfully!" -ForegroundColor Green
Write-Host "`nTask Details:" -ForegroundColor Cyan
Write-Host "  Name:     $TaskName"
Write-Host "  Schedule: Daily at 7:00 PM"
Write-Host "  Script:   $ScriptPath"
Write-Host "  Log:      $LogFile"

Write-Host "`nThe task will:" -ForegroundColor Yellow
Write-Host "  1. Compare AI tips vs actual race results"
Write-Host "  2. Calculate win rate and ROI"
Write-Host "  3. Save report to performance_report_YYYY-MM-DD.json"
Write-Host "  4. Output to performance_report_log.txt"

Write-Host "`nManual Commands:" -ForegroundColor Cyan
Write-Host "  Run now:  python daily_performance_report.py"
Write-Host "  View log: Get-Content performance_report_log.txt -Tail 50"
Write-Host "  Disable:  Disable-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Enable:   Enable-ScheduledTask -TaskName '$TaskName'"

Write-Host "`n" -ForegroundColor Green

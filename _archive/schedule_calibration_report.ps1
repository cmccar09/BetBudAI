# Schedule Daily Calibration Report to run daily at 9:00 AM
# This script creates a Windows Task Scheduler task
# Replaces the previous 9am results file email

$TaskName = "SureBet-Calibration-DailyReport"
$ScriptPath = "$PSScriptRoot\send_daily_calibration_report.py"
$PythonPath = "$PSScriptRoot\.venv\Scripts\python.exe"

# Check if Python exists
if (-not (Test-Path $PythonPath)) {
    Write-Host "Error: Python not found at $PythonPath" -ForegroundColor Red
    Write-Host "Please ensure the virtual environment is set up" -ForegroundColor Yellow
    exit 1
}

# Create the task action
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $ScriptPath -WorkingDirectory $PSScriptRoot

# Create the trigger (daily at 9:00 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At "09:00AM"

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register the task
try {
    # Remove existing task if it exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Register new task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Daily v2.3 calibration and comparative learning analysis email" `
        -User $env:USERNAME
    
    Write-Host ""
    Write-Host "✅ Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Schedule: Daily at 9:00 AM"
    Write-Host "  Script: send_daily_calibration_report.py"
    Write-Host "  Recipients: charles.mccarthy@gmail.com, dryanfitness@gmail.com"
    Write-Host ""
    Write-Host "Report Contents:" -ForegroundColor Yellow
    Write-Host "  • Prediction calibration analysis (accuracy by confidence bins)" -ForegroundColor Gray
    Write-Host "  • Brier score (prediction quality metric)" -ForegroundColor Gray
    Write-Host "  • Comparative learning (our picks vs actual winners)" -ForegroundColor Gray
    Write-Host "  • Systematic patterns identified" -ForegroundColor Gray
    Write-Host "  • Actionable recommendations" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Task Commands:" -ForegroundColor Cyan
    Write-Host "  View task:    Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "  Run now:      Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "  Disable:      Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "  Remove:       Unregister-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host ""
    
    # Ask to run now
    $runNow = Read-Host "Would you like to run the task now for testing? (y/n)"
    if ($runNow -eq 'y' -or $runNow -eq 'Y') {
        Write-Host "`nRunning task now..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 2
        Write-Host "✅ Task started. Check email in a few moments." -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ Error creating scheduled task: $_" -ForegroundColor Red
    exit 1
}

# Schedule Top 5 Report to run daily at 10:00 AM
# This script creates a Windows Task Scheduler task

$TaskName = "SureBet-Top5-DailyReport"
$ScriptPath = "$PSScriptRoot\send_yesterday_top5_report.py"
$PythonPath = "$PSScriptRoot\.venv\Scripts\python.exe"

# Check if Python exists
if (-not (Test-Path $PythonPath)) {
    Write-Host "Error: Python not found at $PythonPath" -ForegroundColor Red
    Write-Host "Please ensure the virtual environment is set up" -ForegroundColor Yellow
    exit 1
}

# Create the task action
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $ScriptPath -WorkingDirectory $PSScriptRoot

# Create the trigger (daily at 10:00 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At "10:00AM"

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
        -Description "Daily email report of top 5 moderate ROI betting picks from yesterday" `
        -User $env:USERNAME
    
    Write-Host ""
    Write-Host "✅ Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Schedule: Daily at 10:00 AM"
    Write-Host "  Script: $ScriptPath"
    Write-Host "  Recipients: charles.mccarthy@gmail.com, dryanfitness@gmail.com"
    Write-Host ""
    Write-Host "To view the task: Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host "To run manually now: Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "To disable: Disable-ScheduledTask -TaskName '$TaskName'"
    Write-Host "To remove: Unregister-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    
} catch {
    Write-Host "❌ Error creating scheduled task: $_" -ForegroundColor Red
    exit 1
}

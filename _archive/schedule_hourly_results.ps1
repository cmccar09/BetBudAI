# Schedule Hourly Results Fetcher
# Runs every hour to capture race results while still available in Betfair API

$TaskName = "SureBet-Hourly-ResultsFetcher"
$ScriptPath = "$PSScriptRoot\fetch_hourly_results.py"
$PythonPath = "$PSScriptRoot\.venv\Scripts\python.exe"

# Check if Python exists
if (-not (Test-Path $PythonPath)) {
    Write-Host "Error: Python not found at $PythonPath" -ForegroundColor Red
    Write-Host "Please ensure the virtual environment is set up" -ForegroundColor Yellow
    exit 1
}

# Create the task action
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $ScriptPath -WorkingDirectory $PSScriptRoot

# Create the trigger (every hour)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 1)

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

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
        -Description "Fetches race results hourly from Betfair while markets are still available" `
        -User $env:USERNAME
    
    Write-Host ""
    Write-Host "✅ Hourly results fetcher scheduled successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Schedule: Every hour, 24/7"
    Write-Host "  Script: $ScriptPath"
    Write-Host "  Purpose: Capture race results within 1 hour of completion"
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  Test now:    python fetch_hourly_results.py"
    Write-Host "  Run task:    Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  View task:   Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  View logs:   Get-ScheduledTaskInfo -TaskName '$TaskName'"
    Write-Host "  Disable:     Disable-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Remove:      Unregister-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    
} catch {
    Write-Host "❌ Error creating scheduled task: $_" -ForegroundColor Red
    exit 1
}

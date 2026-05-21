# setup_learning_scheduler.ps1
# Setup Windows Task Scheduler to run learning cycle daily at 6pm and 10pm

$ErrorActionPreference = "Stop"

# Configuration
$taskName = "BettingLearningCycle"
$scriptPath = "$PSScriptRoot\daily_learning_cycle.py"
$logPath = "$PSScriptRoot\logs\learning"
$pythonExe = (Get-Command python).Source

# Ensure log directory exists
New-Item -ItemType Directory -Force -Path $logPath | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Daily Learning Cycle Scheduler Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task '$taskName' already exists" -ForegroundColor Yellow
    $response = Read-Host "Do you want to replace it? (y/n)"
    if ($response -ne 'y') {
        Write-Host "`nSetup cancelled" -ForegroundColor Gray
        exit 0
    }
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed existing task`n" -ForegroundColor Green
}

# Create the action
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$scriptPath`"" -WorkingDirectory $PSScriptRoot

# Create the triggers - Daily at 6:00 PM and 10:00 PM
$trigger1 = New-ScheduledTaskTrigger -Daily -At "18:00"
$trigger2 = New-ScheduledTaskTrigger -Daily -At "22:00"

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Create the principal (run with highest privileges)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest

# Register the task
try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($trigger1, $trigger2) -Settings $settings -Principal $principal -Description "Daily learning cycle - analyzes completed bets and updates AI insights at 6pm and 10pm" -ErrorAction Stop | Out-Null
    
    Write-Host "Created scheduled task: $taskName" -ForegroundColor Green
    Write-Host "`nTask Details:" -ForegroundColor Cyan
    Write-Host "  Schedule: Daily at 6:00 PM and 10:00 PM" -ForegroundColor Gray
    Write-Host "  Script:   $scriptPath" -ForegroundColor Gray
    Write-Host "  Python:   $pythonExe" -ForegroundColor Gray
    Write-Host "  Logs:     $logPath" -ForegroundColor Gray
    
    Write-Host "`nManagement Commands:" -ForegroundColor Cyan
    Write-Host "  View task:" -ForegroundColor Yellow
    Write-Host "    Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host "`n  Disable task:" -ForegroundColor Yellow
    Write-Host "    Disable-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host "`n  Enable task:" -ForegroundColor Yellow
    Write-Host "    Enable-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host "`n  Remove task:" -ForegroundColor Yellow
    Write-Host "    Unregister-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host "`n  Run manually:" -ForegroundColor Yellow
    Write-Host "    python daily_learning_cycle.py" -ForegroundColor Gray
    Write-Host "`n  Test run now:" -ForegroundColor Yellow
    Write-Host "    Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    
    Write-Host "`nLearning cycle will run daily at 6:00 PM and 10:00 PM" -ForegroundColor Green
    Write-Host "System will analyze results and update AI insights automatically`n" -ForegroundColor Green
} catch {
    Write-Host "`nFailed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}

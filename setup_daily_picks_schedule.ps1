# BetBudAI Daily Picks - Windows Task Scheduler Setup
# This creates a scheduled task to run picks generation at 11:00 AM BST daily
# Ensures picks are ready by 1:00 PM BST

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "BetBudAI - Daily Picks Scheduler Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator', then run this script again." -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# Configuration
$taskName = "BetBudAI-DailyPicks"
$workingDir = "c:\Users\charl\OneDrive\futuregenAI\BetBudAI"
$scriptPath = Join-Path $workingDir "run_all_workflows.py"
$pythonPath = "python"  # Assumes python is in PATH
$scheduleTime = "11:00AM"  # 11:00 AM BST

Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "   Python found: $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Host "   [ERROR] Python not found in PATH" -ForegroundColor Red
    Write-Host "   Please ensure Python is installed and added to PATH" -ForegroundColor Yellow
    pause
    exit 1
}

# Check if workflow script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "   [ERROR] Workflow script not found: $scriptPath" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "   Workflow script found" -ForegroundColor Gray
Write-Host ""

Write-Host "[2/5] Removing existing task (if any)..." -ForegroundColor Green
try {
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "   Removed existing task" -ForegroundColor Gray
    } else {
        Write-Host "   No existing task found" -ForegroundColor Gray
    }
} catch {
    Write-Host "   No existing task to remove" -ForegroundColor Gray
}
Write-Host ""

Write-Host "[3/5] Creating scheduled task..." -ForegroundColor Green

# Create action - run Python with the workflow script
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "`"$scriptPath`"" `
    -WorkingDirectory $workingDir

# Create trigger - daily at 11:00 AM
$trigger = New-ScheduledTaskTrigger -Daily -At $scheduleTime

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Create principal (run as current user)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# Register the task
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Generate daily betting picks for BetBudAI. Runs at 11:00 AM BST to ensure picks are ready by 1:00 PM." `
        -ErrorAction Stop | Out-Null

    Write-Host "   Task created successfully" -ForegroundColor Gray
} catch {
    Write-Host "   [ERROR] Failed to create task: $_" -ForegroundColor Red
    pause
    exit 1
}
Write-Host ""

Write-Host "[4/5] Verifying task..." -ForegroundColor Green
$task = Get-ScheduledTask -TaskName $taskName
$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName

Write-Host "   Task Name: $($task.TaskName)" -ForegroundColor Gray
Write-Host "   State: $($task.State)" -ForegroundColor Gray
Write-Host "   Next Run: $($taskInfo.NextRunTime)" -ForegroundColor Gray
Write-Host "   Last Run: $($taskInfo.LastRunTime)" -ForegroundColor Gray
Write-Host ""

Write-Host "[5/5] Testing task (optional)..." -ForegroundColor Green
Write-Host "   Do you want to run the task now to test it? (Y/N)" -ForegroundColor Yellow
$response = Read-Host

if ($response -eq 'Y' -or $response -eq 'y') {
    Write-Host "   Starting task..." -ForegroundColor Gray
    Start-ScheduledTask -TaskName $taskName
    Write-Host "   Task started! Check Task Scheduler for results." -ForegroundColor Gray
    Write-Host "   The workflow typically takes 5-15 minutes to complete." -ForegroundColor Gray
} else {
    Write-Host "   Skipped test run" -ForegroundColor Gray
}
Write-Host ""

Write-Host "================================================" -ForegroundColor Green
Write-Host "SUCCESS! Daily picks schedule configured" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Schedule Details:" -ForegroundColor Cyan
Write-Host "  - Runs daily at: 11:00 AM BST" -ForegroundColor White
Write-Host "  - Script: run_all_workflows.py" -ForegroundColor White
Write-Host "  - Duration: ~5-15 minutes" -ForegroundColor White
Write-Host "  - Picks ready by: 1:00 PM BST" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT NOTES:" -ForegroundColor Yellow
Write-Host "  1. Your computer must be ON at 11:00 AM" -ForegroundColor White
Write-Host "  2. Computer must have internet connection" -ForegroundColor White
Write-Host "  3. Task runs under your user account ($env:USERNAME)" -ForegroundColor White
Write-Host ""
Write-Host "To view/modify the task:" -ForegroundColor Cyan
Write-Host "  1. Open Task Scheduler (taskschd.msc)" -ForegroundColor White
Write-Host "  2. Look for 'BetBudAI-DailyPicks' in Task Scheduler Library" -ForegroundColor White
Write-Host ""
Write-Host "To manually run picks now:" -ForegroundColor Cyan
Write-Host "  cd $workingDir" -ForegroundColor White
Write-Host "  python run_all_workflows.py" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
pause

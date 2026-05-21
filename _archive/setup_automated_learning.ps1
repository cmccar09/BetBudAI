# Setup Automated Daily Learning Workflow
# This script creates/updates the Windows Task Scheduler to run the workflow daily

$TaskName = "BettingWorkflow_AutoLearning"
$ScriptPath = "$PSScriptRoot\daily_automated_workflow.py"
$PythonPath = "$PSScriptRoot\.venv\Scripts\python.exe"
$LogPath = "$PSScriptRoot\logs\daily_workflow.log"

Write-Host "Setting up automated daily learning workflow..." -ForegroundColor Cyan
Write-Host ""

# Create logs directory if it doesn't exist
if (!(Test-Path "$PSScriptRoot\logs")) {
    New-Item -ItemType Directory -Path "$PSScriptRoot\logs" -Force | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed existing task" -ForegroundColor Yellow
}

# Create the scheduled task
$Action = New-ScheduledTaskAction -Execute $PythonPath `
    -Argument "$ScriptPath" `
    -WorkingDirectory $PSScriptRoot

# Trigger: Every day at 8:00 AM (after races finish around 10 PM, before today's races start)
$Trigger = New-ScheduledTaskTrigger -Daily -At "08:00AM"

# Settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Daily automated learning workflow: Fetches results, adjusts weights, generates picks" `
    -User $env:USERNAME

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "AUTOMATED WORKFLOW CONFIGURED" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Task Name: $TaskName" -ForegroundColor Yellow
Write-Host "Schedule: Daily at 8:00 AM" -ForegroundColor Yellow
Write-Host "Script: $ScriptPath" -ForegroundColor Yellow
Write-Host "Logs: $LogPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "WORKFLOW STEPS:" -ForegroundColor Cyan
Write-Host "  1. Fetch yesterday's race results" -ForegroundColor White
Write-Host "  2. Auto-adjust scoring weights (learns from performance)" -ForegroundColor White
Write-Host "  3. Fetch today's races" -ForegroundColor White
Write-Host "  4. Analyze races with updated weights" -ForegroundColor White
Write-Host "  5. Save picks to DynamoDB" -ForegroundColor White
Write-Host ""
Write-Host "MANUAL TESTING:" -ForegroundColor Cyan
Write-Host "  Run now: " -NoNewline -ForegroundColor White
Write-Host "python daily_automated_workflow.py" -ForegroundColor Green
Write-Host "  Check task: " -NoNewline -ForegroundColor White
Write-Host "Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Green
Write-Host "  View logs: " -NoNewline -ForegroundColor White
Write-Host "Get-Content $LogPath -Tail 50" -ForegroundColor Green
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✓ Automated learning is now active!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan

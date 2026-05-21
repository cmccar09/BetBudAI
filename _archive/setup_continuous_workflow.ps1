# Setup Continuous Betting Workflow - Runs every 10 minutes from 06:00-20:00 (8 PM)
# This replaces all the individual BettingWorkflow_* tasks with a single repeating task

$ErrorActionPreference = "Continue"

Write-Host "`n=== Betting Workflow Task Setup ===" -ForegroundColor Cyan
Write-Host "This will create a single task that runs every 10 minutes from 06:00-20:00 (8 PM)`n" -ForegroundColor Yellow
Write-Host "NOTE: Removing old tasks requires administrator privileges" -ForegroundColor Yellow

# Task configuration
$taskName = "BettingWorkflow_Continuous"
$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\scheduled_workflow.ps1"
$workingDir = "C:\Users\charl\OneDrive\futuregenAI\Betting"

# Step 1: Remove old individual tasks
Write-Host "Step 1: Removing old individual BettingWorkflow_* tasks..." -ForegroundColor Cyan
$oldTasks = Get-ScheduledTask -TaskName "BettingWorkflow_*" -ErrorAction SilentlyContinue
if ($oldTasks) {
    foreach ($task in $oldTasks) {
        try {
            Write-Host "  Removing: $($task.TaskName)" -ForegroundColor Gray
            Unregister-ScheduledTask -TaskName $task.TaskName -Confirm:$false -ErrorAction Stop
        } catch {
            Write-Host "    Warning: Could not remove $($task.TaskName) - may need admin rights" -ForegroundColor Yellow
        }
    }
    Write-Host "  Processed $($oldTasks.Count) old tasks" -ForegroundColor Green
} else {
    Write-Host "  No old tasks found" -ForegroundColor Gray
}

# Step 2: Remove the new task if it already exists
Write-Host "`nStep 2: Checking for existing continuous task..." -ForegroundColor Cyan
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "  Removing existing task: $taskName" -ForegroundColor Gray
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Step 3: Create the new continuous task
Write-Host "`nStep 3: Creating continuous task..." -ForegroundColor Cyan

# Action: Run PowerShell script
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
    -WorkingDirectory $workingDir

# Trigger: Daily at 06:00 AM, repeat every 10 minutes for 14 hours
$trigger = New-ScheduledTaskTrigger -Daily -At 06:00AM
$repetitionPattern = New-ScheduledTaskTrigger -Once -At 06:00AM -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Hours 14)
$trigger.Repetition = $repetitionPattern.Repetition

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

# Principal: Run with highest privileges
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# Register the task
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Continuous horse racing betting workflow - Runs every 10 minutes from 06:00 AM to 8:00 PM daily" | Out-Null

Write-Host "  Task created successfully!" -ForegroundColor Green

# Step 4: Verify the task
Write-Host "`nStep 4: Verifying task configuration..." -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $taskName
$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName

Write-Host "`nTask Details:" -ForegroundColor Yellow
Write-Host "  Name: $($task.TaskName)"
Write-Host "  State: $($task.State)"
Write-Host "  Next Run: $($taskInfo.NextRunTime)"
Write-Host "  Trigger: Daily at 12:00 PM"
Write-Host "  Repetition: Every 30 minutes for 8 hours (12:00-20:00)"
Write-Host "  Script: $scriptPath"

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host "The workflow will now run automatically every 30 minutes from 12:00-20:00 daily" -ForegroundColor Green
Write-Host "Next scheduled run: $($taskInfo.NextRunTime)`n" -ForegroundColor Cyan

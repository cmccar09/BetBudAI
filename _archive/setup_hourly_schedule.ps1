#!/usr/bin/env pwsh
# Create a single scheduled task that repeats every hour from 12pm-6pm
# Run as Administrator

$taskName = "BettingWorkflow_Hourly"
$scriptPath = "$PSScriptRoot\scheduled_workflow.ps1"

Write-Host "Creating hourly betting workflow task..." -ForegroundColor Cyan

# Remove old task if exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Create action
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
    -WorkingDirectory $PSScriptRoot

# Create trigger - start at 12pm, repeat every 1 hour for 6 hours
$trigger = New-ScheduledTaskTrigger -Daily -At "12:00"
$trigger.Repetition = New-ScheduledTaskTrigger -Once -At "12:00" -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Hours 6) | Select-Object -ExpandProperty Repetition

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Principal - run whether logged in or not
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# Register task
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Automated betting workflow - runs every hour from 12pm-6pm" `
    -Force

Write-Host "Task created successfully!" -ForegroundColor Green
Write-Host "Schedule: Every hour from 12:00 PM to 6:00 PM daily" -ForegroundColor Cyan

# Show task details
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State, @{Name='NextRun';Expression={(Get-ScheduledTaskInfo $_).NextRunTime}}

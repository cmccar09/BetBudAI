#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup greyhound picks generation - Ireland only, 4pm-10pm every 10 minutes
.DESCRIPTION
    Creates a single scheduled task that repeats every 10 minutes from 4pm-10pm daily
    Only fetches races in Ireland (IE)
#>

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges." -ForegroundColor Yellow
    Write-Host "Relaunching with administrator privileges..." -ForegroundColor Cyan
    
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    Start-Process PowerShell.exe -Verb RunAs -ArgumentList $arguments
    exit
}

$taskName = "SureBet-Greyhound-IrelandOnly"
$scriptPath = "$PSScriptRoot\scheduled_greyhound_workflow.ps1"

Write-Host ""
Write-Host "="*70 -ForegroundColor Cyan
Write-Host "SETUP GREYHOUND PICKS SCHEDULER" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Schedule: 4:00 PM - 10:00 PM daily" -ForegroundColor Gray
Write-Host "  Frequency: Every 30 minutes" -ForegroundColor Gray
Write-Host "  Region: UK & Ireland" -ForegroundColor Gray
Write-Host "  Self-Learning: Enabled" -ForegroundColor Gray
Write-Host ""

# Remove old task if exists
Write-Host "Removing any existing greyhound tasks..." -ForegroundColor Yellow
Get-ScheduledTask -TaskName "*Greyhound*" -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false

# Create action
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
    -WorkingDirectory $PSScriptRoot

# Create trigger - start at 4pm, repeat every 30 minutes for 6 hours (until 10pm)
$trigger = New-ScheduledTaskTrigger -Daily -At "16:00"
$trigger.Repetition = (New-ScheduledTaskTrigger -Once -At "16:00" -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Hours 6)).Repetition

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 8) `
    -MultipleInstances IgnoreNew

# Principal - run whether logged in or not
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# Register task
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Greyhound picks (UK & Ireland) - runs every 30 minutes from 4pm-10pm with self-learning" `
        -Force | Out-Null
    
    Write-Host "Task created successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Show task details
    $task = Get-ScheduledTask -TaskName $taskName
    $info = Get-ScheduledTaskInfo $task
    
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $($task.TaskName)" -ForegroundColor White
    Write-Host "  State: $($task.State)" -ForegroundColor White
    Write-Host "  Next Run: $($info.NextRunTime)" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "ERROR: Failed to create task" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    exit 1
}

Write-Host "="*70 -ForegroundColor Cyan
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Greyhound picks will now generate:" -ForegroundColor Cyan
Write-Host "  - Every 30 minutes from 4:00 PM to 10:00 PM" -ForegroundColor White
Write-Host "  - UK & Ireland races" -ForegroundColor White
Write-Host "  - Self-learning enabled" -ForegroundColor White
Write-Host ""
Write-Host "Horse racing schedules remain UNCHANGED" -ForegroundColor Green
Write-Host ""
Write-Host "Test the greyhound workflow now:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "View all SureBet tasks:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName 'SureBet-*'" -ForegroundColor Gray
Write-Host ""

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

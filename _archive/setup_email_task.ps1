#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup Windows Task Scheduler to send daily email at 9am
.DESCRIPTION
    Creates a scheduled task that sends betting picks email at 09:00 (9am) daily
#>

param(
    [switch]$Remove  # Remove existing task instead of creating it
)

$taskName = "BettingDailyEmail"
$scriptPath = "$PSScriptRoot\send_daily_email.ps1"
$runTime = "09:00"  # 9am

Write-Host "="*60 -ForegroundColor Cyan
if ($Remove) {
    Write-Host "REMOVING Daily Email Task" -ForegroundColor Yellow
} else {
    Write-Host "SETTING UP Daily Email Task" -ForegroundColor Cyan
}
Write-Host "="*60 -ForegroundColor Cyan

if ($Remove) {
    Write-Host "`nRemoving task: $taskName" -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "  Removed" -ForegroundColor Green
    } catch {
        Write-Host "  Not found or error: $_" -ForegroundColor Gray
    }
} else {
    Write-Host "`nCreating task: $taskName (runs at $runTime daily)" -ForegroundColor Cyan
    
    # Define the action
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
        -WorkingDirectory $PSScriptRoot
    
    # Define the trigger (daily at 9am)
    $trigger = New-ScheduledTaskTrigger -Daily -At $runTime
    
    # Define settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
    
    # Define principal - run whether user is logged in or not
    $principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType S4U `
        -RunLevel Highest
    
    # Register the task
    try {
        Register-ScheduledTask `
            -TaskName $taskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "Send daily betting picks email to charles.mccarthy@gmail.com at 2pm" `
            -Force | Out-Null
        
        Write-Host "  Created successfully" -ForegroundColor Green
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n"
Write-Host "="*60 -ForegroundColor Cyan
if ($Remove) {
    Write-Host "TASK REMOVED" -ForegroundColor Yellow
} else {
    Write-Host "SETUP COMPLETE!" -ForegroundColor Green
    Write-Host "`nDaily email will be sent at: $runTime (2pm)" -ForegroundColor Cyan
    Write-Host "To: charles.mccarthy@gmail.com" -ForegroundColor White
    
    Write-Host "`nTo view task:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    
    Write-Host "`nTo test manually:" -ForegroundColor Yellow
    Write-Host "  .\send_daily_email.ps1" -ForegroundColor Gray
    
    Write-Host "`nTo remove task:" -ForegroundColor Yellow
    Write-Host "  .\setup_email_task.ps1 -Remove" -ForegroundColor Gray
    
    Write-Host "`nNote: Ensure AWS SES is configured or set SMTP_USER/SMTP_PASSWORD" -ForegroundColor Yellow
}
Write-Host "="*60 -ForegroundColor Cyan

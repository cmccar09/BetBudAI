#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Fix scheduled tasks to run whether user is logged in or not
.DESCRIPTION
    This script MUST be run as Administrator to modify scheduled task principals
#>

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "`n❌ ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "`nTo run as Admin:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor Cyan
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor Cyan
    Write-Host "  3. Navigate to: $PSScriptRoot" -ForegroundColor Cyan
    Write-Host "  4. Run: .\fix_tasks_run_always.ps1`n" -ForegroundColor Cyan
    exit 1
}

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "FIXING SCHEDULED TASKS - Run Whether Logged In Or Not" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

# Get all betting-related tasks
$taskNames = @(
    "BettingWorkflow_1000",
    "BettingWorkflow_1200",
    "BettingWorkflow_1400",
    "BettingWorkflow_1600",
    "BettingWorkflow_1800",
    "BettingWorkflow_2200",
    "BettingDailyLearning",
    "BettingDailyEmail"
)

foreach ($taskName in $taskNames) {
    Write-Host "`nProcessing: $taskName" -ForegroundColor Cyan
    
    try {
        # Get the existing task
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        
        if (-not $task) {
            Write-Host "  ⚠ Task not found - skipping" -ForegroundColor Yellow
            continue
        }
        
        # Create new principal - run whether logged in or not
        $principal = New-ScheduledTaskPrincipal `
            -UserId "$env:USERDOMAIN\$env:USERNAME" `
            -LogonType S4U `
            -RunLevel Highest
        
        # Update the task with new principal
        Set-ScheduledTask `
            -TaskName $taskName `
            -Principal $principal `
            -ErrorAction Stop | Out-Null
        
        Write-Host "  ✓ Updated successfully - will now run whether logged in or not" -ForegroundColor Green
        
    } catch {
        Write-Host "  ❌ ERROR: $_" -ForegroundColor Red
    }
}

Write-Host "`n"
Write-Host "="*60 -ForegroundColor Green
Write-Host "FIX COMPLETE!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green
Write-Host "`nAll tasks are now configured to run whether you're logged in or not." -ForegroundColor Cyan
Write-Host "`nTo verify, open Task Scheduler and check each task:" -ForegroundColor Yellow
Write-Host "  taskschd.msc" -ForegroundColor Cyan
Write-Host "`nLook for: 'Run whether user is logged on or not'" -ForegroundColor Yellow
Write-Host ""

#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Remove all greyhound-related scheduled tasks
.DESCRIPTION
    This script removes all Windows Task Scheduler tasks related to greyhound picks
    Run this after disabling greyhound schedules to clean up the system
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

Write-Host ""
Write-Host "="*70 -ForegroundColor Cyan
Write-Host "REMOVE GREYHOUND SCHEDULED TASKS" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""

# Find all greyhound-related tasks
Write-Host "Searching for greyhound-related scheduled tasks..." -ForegroundColor Yellow
$greyhoundTasks = @()

# Check for tasks with "Greyhound" in the name
try {
    $allTasks = Get-ScheduledTask -ErrorAction SilentlyContinue
    $greyhoundTasks = $allTasks | Where-Object { $_.TaskName -like "*Greyhound*" }
} catch {
    Write-Host "Error retrieving scheduled tasks: $_" -ForegroundColor Red
}

if ($greyhoundTasks.Count -eq 0) {
    Write-Host ""
    Write-Host "No greyhound scheduled tasks found." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Found $($greyhoundTasks.Count) greyhound task(s):" -ForegroundColor Cyan
    foreach ($task in $greyhoundTasks) {
        Write-Host "  - $($task.TaskName)" -ForegroundColor White
    }
    Write-Host ""
    
    # Confirm removal
    $confirm = Read-Host "Remove all these tasks? (Y/N)"
    
    if ($confirm -eq 'Y' -or $confirm -eq 'y') {
        Write-Host ""
        Write-Host "Removing tasks..." -ForegroundColor Yellow
        
        foreach ($task in $greyhoundTasks) {
            try {
                Unregister-ScheduledTask -TaskName $task.TaskName -Confirm:$false
                Write-Host "  Removed: $($task.TaskName)" -ForegroundColor Green
            } catch {
                Write-Host "  Failed to remove: $($task.TaskName)" -ForegroundColor Red
                Write-Host "    Error: $_" -ForegroundColor Red
            }
        }
        
        Write-Host ""
        Write-Host "All greyhound tasks removed!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Cancelled - no tasks removed." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "="*70 -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Greyhound schedules are now disabled." -ForegroundColor Green
Write-Host ""
Write-Host "The following systems remain ACTIVE:" -ForegroundColor Cyan
Write-Host "  Horse racing picks generation" -ForegroundColor Green
Write-Host "  Daily learning from horse racing results" -ForegroundColor Green
Write-Host "  Self-learning performance tracking" -ForegroundColor Green
Write-Host "  Surebet analysis and ROI calculations" -ForegroundColor Green
Write-Host ""
Write-Host "To view active scheduled tasks:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask | Where-Object { `$_.TaskName -like '*Betting*' }" -ForegroundColor Gray
Write-Host ""

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

# Schedule Greyhound Picks Generation
# Runs every 30 minutes from 12:00 PM to 5:30 PM

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges to create scheduled tasks." -ForegroundColor Yellow
    Write-Host "Relaunching with administrator privileges..." -ForegroundColor Cyan
    
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    Start-Process PowerShell.exe -Verb RunAs -ArgumentList $arguments
    exit
}

$taskName = "SureBet-Greyhound-Picks"
$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\generate_todays_picks.ps1"

Write-Host "Creating scheduled tasks for greyhound picks..." -ForegroundColor Cyan

# Create tasks for each 30-minute interval from 12:00 PM to 5:30 PM
$times = @("12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30")

foreach ($time in $times) {
    $taskNameWithTime = "$taskName-$($time.Replace(':', ''))"
    
    # Delete if exists
    schtasks /query /tn $taskNameWithTime 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        schtasks /delete /tn $taskNameWithTime /f | Out-Null
    }
    
    # Create the task (single line to avoid backtick issues)
    $command = "PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Sport greyhounds"
    schtasks /create /tn $taskNameWithTime /tr $command /sc daily /st $time /rl HIGHEST /f | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Created task for $time" -ForegroundColor Green
    } else {
        Write-Host "  Failed to create task for $time" -ForegroundColor Red
    }
}

Write-Host "`nAll tasks created!" -ForegroundColor Green
Write-Host "Schedule: Every 30 minutes from 12:00 PM to 5:30 PM" -ForegroundColor Cyan
Write-Host "`nTo view tasks: schtasks /query | findstr Greyhound" -ForegroundColor Yellow

Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

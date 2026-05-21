# schedule_handicap_scan.ps1
# ─────────────────────────────────────────────────────────────────────────────
# Registers (or updates) a Windows Task Scheduler task that runs
# handicap_festival_scanner.py once per morning during the Cheltenham Festival.
#
# Festival dates 2026: 10-13 March
# Run time: 08:00 each morning (local time)
#
# Run this script ONCE to register the task:
#   .\schedule_handicap_scan.ps1
#
# To also enable the Racing Post scrape (slower but richer):
#   .\schedule_handicap_scan.ps1 -EnableRPScrape
#
# To remove the task afterwards:
#   Unregister-ScheduledTask -TaskName "CheltenhamHandicapScan" -Confirm:$false
# ─────────────────────────────────────────────────────────────────────────────

param(
    [switch]$EnableRPScrape,
    [switch]$DryRun,
    [string]$TaskName = "CheltenhamHandicapScan"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Paths ─────────────────────────────────────────────────────────────────────
$workspace  = "C:\Users\charl\OneDrive\futuregenAI\Betting"
$venvPython = Join-Path $workspace ".venv\Scripts\python.exe"
$script     = Join-Path $workspace "handicap_festival_scanner.py"

if (-not (Test-Path $venvPython)) {
    Write-Error "Python venv not found: $venvPython. Run: python -m venv .venv && .venv\Scripts\pip install -r requirements.txt"
    exit 1
}
if (-not (Test-Path $script)) {
    Write-Error "Scanner script not found: $script"
    exit 1
}

# ── Build argument string ─────────────────────────────────────────────────────
$scanArgs = "`"$script`""
if ($EnableRPScrape) { $scanArgs += " --rp" }
if ($DryRun)         { $scanArgs += " --no-save" }

Write-Host "╔═══════════════════════════════════════════════════════════════╗"
Write-Host "║   Cheltenham Handicap Festival Scanner — Task Scheduler Setup ║"
Write-Host "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""
Write-Host "  Python  : $venvPython"
Write-Host "  Script  : $script"
Write-Host "  Args    : $scanArgs"
Write-Host ""

# ── Festival run dates: 10-13 March 2026, 08:00 ──────────────────────────────
$festivalDates = @(
    [datetime]"2026-03-10 08:00:00",
    [datetime]"2026-03-11 08:00:00",
    [datetime]"2026-03-12 08:00:00",
    [datetime]"2026-03-13 08:00:00"
)

# ── Remove existing task if present ───────────────────────────────────────────
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "  Removing existing task '$TaskName'..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# ── Build the task action ─────────────────────────────────────────────────────
$action = New-ScheduledTaskAction `
    -Execute  $venvPython `
    -Argument $scanArgs `
    -WorkingDirectory $workspace

# ── Build triggers — one per festival day ────────────────────────────────────
$triggers = foreach ($dt in $festivalDates) {
    New-ScheduledTaskTrigger -Once -At $dt
}

# ── Settings: allow to run on battery, stop after 30 min ─────────────────────
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -StartWhenAvailable

# ── Register the task ─────────────────────────────────────────────────────────
Register-ScheduledTask `
    -TaskName   $TaskName `
    -Action     $action `
    -Trigger    $triggers `
    -Settings   $settings `
    -Description "Runs handicap_festival_scanner.py each morning of the Cheltenham Festival 2026 (10-13 March)" `
    -RunLevel   Highest `
    -Force | Out-Null

Write-Host "  ✅ Task '$TaskName' registered successfully."
Write-Host ""
Write-Host "  Scheduled runs:"
foreach ($dt in $festivalDates) {
    Write-Host ("    {0}" -f $dt.ToString("ddd dd MMM yyyy HH:mm"))
}
Write-Host ""
Write-Host "  To run immediately for testing:"
Write-Host "    Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "  To view task details:"
Write-Host "    Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo"
Write-Host ""
Write-Host "  To remove the task after the festival:"
Write-Host "    Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
Write-Host ""

# ── Optionally run now for a quick test ───────────────────────────────────────
$runNow = Read-Host "Run the scanner right now for a test? (y/N)"
if ($runNow -ieq "y") {
    Write-Host ""
    Write-Host "  Running: $venvPython $scanArgs"
    Write-Host "  (--no-save mode to avoid test data in DynamoDB)"
    & $venvPython $script --no-save
}

# setup_cheltenham_scheduler.ps1
# ============================================================
# Creates two Windows Scheduled Tasks for Cheltenham 2026:
#
#   Task 1: CheltenhamDaily_2026
#       Daily at 10:00am, Mar 7 – Mar 13 2026
#       Runs: cheltenham_daily_update.py  (no --race-day flag)
#
#   Task 2: CheltenhamRaceDay_2026
#       Every 30 minutes, 09:00 – 18:00 on Mar 10–13 2026
#       Runs: cheltenham_daily_update.py --race-day
#
# Run once as Administrator to register the tasks.
# To remove: Unregister-ScheduledTask -TaskName "CheltenhamDaily_2026" -Confirm:$false
# ============================================================

$ErrorActionPreference = "Stop"

# ── Config ──────────────────────────────────────────────────────────────────
$WorkDir   = "C:\Users\charl\OneDrive\futuregenAI\Betting"
$Python    = Join-Path $WorkDir ".venv\Scripts\python.exe"
$Script    = Join-Path $WorkDir "cheltenham_daily_update.py"
$LogDir    = $WorkDir

if (-not (Test-Path $Python)) {
    Write-Warning "Python not found at $Python — update the path in this script."
    exit 1
}
if (-not (Test-Path $Script)) {
    Write-Warning "Script not found at $Script"
    exit 1
}

Write-Host "`n=== Cheltenham 2026 Task Scheduler Setup ===" -ForegroundColor Cyan

# ── Task 1: Daily 10am (Mar 7 – Mar 13) ─────────────────────────────────────
$task1Name = "CheltenhamDaily_2026"

$action1 = New-ScheduledTaskAction `
    -Execute  $Python `
    -Argument "`"$Script`"" `
    -WorkingDirectory $WorkDir

# Daily at 10:00am, starting Mar 7, ending after Mar 13
$trigger1 = New-ScheduledTaskTrigger `
    -Daily `
    -At "10:00AM"

$trigger1.StartBoundary = "2026-03-07T10:00:00"
$trigger1.EndBoundary   = "2026-03-14T00:00:00"  # stop after Mar 13

$settings1 = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

if (Get-ScheduledTask -TaskName $task1Name -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $task1Name -Confirm:$false
    Write-Host "  Removed existing task: $task1Name" -ForegroundColor Yellow
}

Register-ScheduledTask `
    -TaskName    $task1Name `
    -Action      $action1 `
    -Trigger     $trigger1 `
    -Settings    $settings1 `
    -RunLevel    Highest `
    -Description "Cheltenham 2026: daily picks refresh at 10am (7–13 Mar)" `
    | Out-Null

Write-Host "  [OK] $task1Name — daily 10:00am  (7 Mar -> 13 Mar 2026)" -ForegroundColor Green

# ── Task 2: Every 30 mins on race days (Mar 10–13, 09:00–18:00) ───────────
$task2Name = "CheltenhamRaceDay_2026"

$action2 = New-ScheduledTaskAction `
    -Execute  $Python `
    -Argument "`"$Script`" --race-day" `
    -WorkingDirectory $WorkDir

$settings2 = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 25)

if (Get-ScheduledTask -TaskName $task2Name -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $task2Name -Confirm:$false
    Write-Host "  Removed existing task: $task2Name" -ForegroundColor Yellow
}

# Race days: 4 separate days, each with a repeating trigger 9am–6pm every 30min
$raceDays = @(
    [datetime]"2026-03-10T09:00:00",
    [datetime]"2026-03-11T09:00:00",
    [datetime]"2026-03-12T09:00:00",
    [datetime]"2026-03-13T09:00:00"
)

$triggers2 = foreach ($day in $raceDays) {
    $t = New-ScheduledTaskTrigger -Once -At $day
    $t.StartBoundary = $day.ToString("yyyy-MM-ddTHH:mm:ss")
    $t.EndBoundary   = $day.AddHours(9).ToString("yyyy-MM-ddTHH:mm:ss")  # ends at 18:00
    # Set RepetitionInterval = 30 min, RepetitionDuration = 9 hours
    $t.Repetition = (New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 30) `
                                              -RepetitionDuration  (New-TimeSpan -Hours 9) `
                                              -Once -At $day).Repetition
    $t
}

Register-ScheduledTask `
    -TaskName    $task2Name `
    -Action      $action2 `
    -Trigger     $triggers2 `
    -Settings    $settings2 `
    -RunLevel    Highest `
    -Description "Cheltenham 2026: race-day picks refresh every 30min 09:00–18:00 (10–13 Mar)" `
    | Out-Null

Write-Host "  [OK] $task2Name — every 30min 09:00–18:00 on race days (10–13 Mar 2026)" -ForegroundColor Green

Write-Host "`nTasks registered. Verify in Task Scheduler (taskschd.msc)" -ForegroundColor Cyan
Write-Host ""
Write-Host "To test immediately:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName '$task1Name'" -ForegroundColor White
Write-Host "  Get-ScheduledTaskInfo -TaskName '$task1Name' | Select LastRunTime,LastTaskResult" -ForegroundColor White

# ── Show summary ─────────────────────────────────────────────────────────────
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "  Task 1: $task1Name"  -ForegroundColor White
Write-Host "    Schedule : Daily 10:00am, 7 Mar – 13 Mar 2026"
Write-Host "    Action   : python cheltenham_daily_update.py"
Write-Host ""
Write-Host "  Task 2: $task2Name" -ForegroundColor White
Write-Host "    Schedule : Every 30min (09:00–18:00) on 10,11,12,13 March 2026"
Write-Host "    Action   : python cheltenham_daily_update.py --race-day"
Write-Host ""

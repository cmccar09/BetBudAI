$ROOT   = "C:\Users\charl\OneDrive\futuregenAI\Betting"
$PYTHON = "$ROOT\.venv\Scripts\python.exe"

$taskName = "BetfairOddsRefresh"
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Creating task: $taskName"

$action = New-ScheduledTaskAction -Execute $PYTHON -Argument "`"$ROOT\auto_refresh_betfair.py`"" -WorkingDirectory $ROOT

$t1 = New-ScheduledTaskTrigger -Daily -At "12:00"
$t2 = New-ScheduledTaskTrigger -Daily -At "14:00"
$t3 = New-ScheduledTaskTrigger -Daily -At "16:00"

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($t1,$t2,$t3) -Settings $settings -RunLevel Highest -Force | Out-Null
Write-Host "  OK: $taskName registered (12:00, 14:00, 16:00 daily)"

foreach ($stale in @("CheltenhamAutoRefresh","CheltenhamDailyUpdate","CheltenhamPicksSave")) {
    if (Get-ScheduledTask -TaskName $stale -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $stale -Confirm:$false
        Write-Host "  Removed stale task: $stale"
    }
}

Write-Host ""
Write-Host "Active scheduled tasks:"
Get-ScheduledTask | Where-Object { $_.TaskName -match "Betfair|Racing|Learning" } | Select-Object TaskName,State | Format-Table -AutoSize

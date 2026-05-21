# Run this as Administrator to recreate the continuous workflow task
# Runs every 30 minutes from 12:00 PM to 8:00 PM (8 hours)

$taskName = "BettingWorkflow_Continuous"
$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\scheduled_workflow.ps1"
$workingDir = "C:\Users\charl\OneDrive\futuregenAI\Betting"

# Remove old task if exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create action
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
    -WorkingDirectory $workingDir

# Create trigger: Daily at 12:00 PM, repeat every 30 minutes for 8 hours
$trigger = New-ScheduledTaskTrigger -Daily -At 12:00PM
$repetition = New-ScheduledTaskTrigger -Once -At 12:00PM `
    -RepetitionInterval (New-TimeSpan -Minutes 30) `
    -RepetitionDuration (New-TimeSpan -Hours 8)
$trigger.Repetition = $repetition.Repetition

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

# Principal: Run with current user, highest privileges
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
    -Description "Runs betting workflow every 30 minutes from 12:00 PM to 8:00 PM daily" | Out-Null

Write-Host "`n[SUCCESS] Task created!" -ForegroundColor Green
Write-Host "`nSchedule: Every 30 minutes from 12:00 PM to 8:00 PM" -ForegroundColor Cyan
Write-Host "Next run times:" -ForegroundColor Yellow
Write-Host "  12:00 PM, 12:30 PM, 1:00 PM, 1:30 PM, 2:00 PM, 2:30 PM, 3:00 PM, 3:30 PM," -ForegroundColor Gray
Write-Host "  4:00 PM, 4:30 PM, 5:00 PM, 5:30 PM, 6:00 PM, 6:30 PM, 7:00 PM, 7:30 PM, 8:00 PM" -ForegroundColor Gray

$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
Write-Host "`nNext scheduled run: $($taskInfo.NextRunTime)" -ForegroundColor Cyan

Write-Host "`nPress Enter to close..."
Read-Host

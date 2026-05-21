# Fix scheduled task to run at :00 and :30 from 10:00-20:00
Write-Host "Configuring BettingWorkflow_Continuous to run at :00 and :30 from 10:00-20:00..." -ForegroundColor Cyan

$taskName = "BettingWorkflow_Continuous"
$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\scheduled_workflow.ps1"
$workingDir = "C:\Users\charl\OneDrive\futuregenAI\Betting"

# Unregister existing task
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Create triggers for :00 and :30 from 10:00-20:00
$triggers = @()
for ($hour = 10; $hour -le 19; $hour++) {
    # Add :00 trigger
    $time00 = "{0:D2}:00" -f $hour
    $triggers += New-ScheduledTaskTrigger -Daily -At $time00
    Write-Host "  Added trigger: $time00" -ForegroundColor Gray
    
    # Add :30 trigger
    $time30 = "{0:D2}:30" -f $hour
    $triggers += New-ScheduledTaskTrigger -Daily -At $time30
    Write-Host "  Added trigger: $time30" -ForegroundColor Gray
}

Write-Host "  Total: $($triggers.Count) triggers (10:00-19:30)" -ForegroundColor Green

# Create action
$batchPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\run_workflow.bat"
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c ""$batchPath""" -WorkingDirectory $workingDir

# Create principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Register task
Register-ScheduledTask -TaskName $taskName -Trigger $triggers -Action $action -Principal $principal -Settings $settings -Description "Runs betting workflow at :00 and :30 from 10:00-19:30 daily"

Write-Host ""
Write-Host "Task configured successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Schedule: Runs at :00 and :30 every hour from 10:00-19:30" -ForegroundColor Yellow
Write-Host "Times: 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 13:00, 13:30..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Task Details:" -ForegroundColor Cyan
Get-ScheduledTask $taskName | Get-ScheduledTaskInfo | Format-List LastRunTime, NextRunTime

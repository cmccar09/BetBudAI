# Fix Scheduled Task - Add error logging
# Run this script as Administrator

$ErrorActionPreference = "Stop"

Write-Host "`n=== Fixing Scheduled Task ===" -ForegroundColor Cyan

$taskName = "BettingWorkflow_Continuous"
$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\scheduled_workflow.ps1"
$workingDir = "C:\Users\charl\OneDrive\futuregenAI\Betting"
$errorLog = "C:\Users\charl\OneDrive\futuregenAI\Betting\logs\task_error.log"

# Remove existing task
Write-Host "Removing existing task..." -ForegroundColor Cyan
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "  Removed existing task" -ForegroundColor Green
}

# Create action with error redirection
Write-Host "`nCreating task action with error logging..." -ForegroundColor Cyan
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"Set-Location '$workingDir'; & '$scriptPath' 2>&1 | Out-File -FilePath '$errorLog' -Append`"" `
    -WorkingDirectory $workingDir

# Create triggers for :15 and :45 past every hour from 11am to 7pm
Write-Host "Creating triggers..." -ForegroundColor Cyan
$times = @('11:15', '11:45', '12:15', '12:45', '13:15', '13:45', '14:15', '14:45', 
           '15:15', '15:45', '16:15', '16:45', '17:15', '17:45', '18:15', '18:45',
           '19:15', '19:45')
$triggers = @()
foreach ($time in $times) {
    $triggers += New-ScheduledTaskTrigger -Daily -At $time
}
Write-Host "  Created 18 triggers" -ForegroundColor Gray

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Create principal
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# Register the task
Write-Host "`nRegistering task..." -ForegroundColor Cyan
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Principal $principal `
    -Description "Horse racing workflow - Runs at :15 and :45 past every hour (11am-7pm) daily" | Out-Null

Write-Host "  Task registered successfully!" -ForegroundColor Green

# Verify
Write-Host "`nVerifying task..." -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $taskName
$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName

Write-Host "`n=== Task Details ===" -ForegroundColor Yellow
Write-Host "Name: $($task.TaskName)"
Write-Host "State: $($task.State)"
Write-Host "Next Run: $($taskInfo.NextRunTime)"
Write-Host "Error Log: $errorLog"

Write-Host "`n=== Fix Complete ===" -ForegroundColor Green
Write-Host "Task will now log errors to: $errorLog" -ForegroundColor Cyan

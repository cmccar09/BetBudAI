# Fix Scheduled Task - Use Batch Wrapper
# Run this script as Administrator

$ErrorActionPreference = "Stop"

Write-Host "`n=== Fixing Scheduled Task with Batch Wrapper ===" -ForegroundColor Cyan

$taskName = "BettingWorkflow_Continuous"
$batchPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\run_workflow.bat"
$workingDir = "C:\Users\charl\OneDrive\futuregenAI\Betting"

# Remove existing task
Write-Host "Removing existing task..." -ForegroundColor Cyan
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "  Removed existing task" -ForegroundColor Green
}

# Create action using batch file
Write-Host "`nCreating task action with batch wrapper..." -ForegroundColor Cyan
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$batchPath`"" `
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

# Create principal - Run whether user is logged on or not
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Password `
    -RunLevel Highest

# Register the task
Write-Host "`nRegistering task..." -ForegroundColor Cyan
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $triggers `
        -Settings $settings `
        -Principal $principal `
        -Description "Horse racing workflow - Runs at :15 and :45 past every hour (11am-7pm) daily" | Out-Null
    Write-Host "  Task registered successfully!" -ForegroundColor Green
} catch {
    Write-Host "  Failed to register with Password logon type, trying S4U..." -ForegroundColor Yellow
    $principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType S4U `
        -RunLevel Highest
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $triggers `
        -Settings $settings `
        -Principal $principal `
        -Description "Horse racing workflow - Runs at :15 and :45 past every hour (11am-7pm) daily" | Out-Null
    Write-Host "  Task registered successfully with S4U!" -ForegroundColor Green
}

# Verify
Write-Host "`nVerifying task..." -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $taskName
$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName

Write-Host "`n=== Task Details ===" -ForegroundColor Yellow
Write-Host "Name: $($task.TaskName)"
Write-Host "State: $($task.State)"
Write-Host "Next Run: $($taskInfo.NextRunTime)"
Write-Host "Output Log: logs\task_output.log"

Write-Host "`n=== Fix Complete ===" -ForegroundColor Green
Write-Host "Task will now use batch wrapper and log to: logs\task_output.log" -ForegroundColor Cyan

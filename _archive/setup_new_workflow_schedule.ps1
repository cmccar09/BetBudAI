# Setup Horse Racing Workflow - Runs at :15 and :45 past even hours (12pm-6pm)
# Run this script as Administrator

$ErrorActionPreference = "Stop"

Write-Host "`n=== Horse Racing Workflow Schedule Setup ===" -ForegroundColor Cyan
Write-Host "Schedule: :15 and :45 past even hours (12pm, 2pm, 4pm, 6pm)" -ForegroundColor Yellow
Write-Host "Times: 12:15, 12:45, 2:15, 2:45, 4:15, 4:45, 6:15, 6:45`n" -ForegroundColor Yellow

$taskName = "BettingWorkflow_Continuous"
$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\scheduled_workflow.ps1"
$workingDir = "C:\Users\charl\OneDrive\futuregenAI\Betting"

# Remove existing task if present
Write-Host "Removing existing task (if any)..." -ForegroundColor Cyan
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "  Removed existing task" -ForegroundColor Green
} else {
    Write-Host "  No existing task found" -ForegroundColor Gray
}

# Create action
Write-Host "`nCreating task action..." -ForegroundColor Cyan
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
    -WorkingDirectory $workingDir

# Create triggers for each time
Write-Host "Creating triggers..." -ForegroundColor Cyan
$times = @('12:15', '12:45', '14:15', '14:45', '16:15', '16:45', '18:15', '18:45')
$triggers = @()
foreach ($time in $times) {
    $triggers += New-ScheduledTaskTrigger -Daily -At $time
    Write-Host "  Added trigger: $time" -ForegroundColor Gray
}

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
    -Description "Horse racing workflow - Runs at :15 and :45 past even hours (12pm, 2pm, 4pm, 6pm) daily" | Out-Null

Write-Host "  Task registered successfully!" -ForegroundColor Green

# Verify
Write-Host "`nVerifying task..." -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $taskName
$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName

Write-Host "`n=== Task Details ===" -ForegroundColor Yellow
Write-Host "Name: $($task.TaskName)"
Write-Host "State: $($task.State)"
Write-Host "Next Run: $($taskInfo.NextRunTime)"
Write-Host "Triggers: 8 daily triggers at :15 and :45 (even hours)"

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host "Workflow will run 8 times daily:" -ForegroundColor Green
Write-Host "  12:15 PM, 12:45 PM" -ForegroundColor Cyan
Write-Host "  2:15 PM, 2:45 PM" -ForegroundColor Cyan
Write-Host "  4:15 PM, 4:45 PM" -ForegroundColor Cyan
Write-Host "  6:15 PM, 6:45 PM" -ForegroundColor Cyan
Write-Host "`nNext run: $($taskInfo.NextRunTime)`n" -ForegroundColor Yellow

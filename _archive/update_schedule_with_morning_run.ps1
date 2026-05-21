# Update Workflow Schedule - Add 10:30am full analysis + existing 30-min schedule
# Run this script as Administrator

$ErrorActionPreference = "Stop"

Write-Host "`n=== Updating Workflow Schedule ===" -ForegroundColor Cyan
Write-Host "New Schedule:" -ForegroundColor Yellow
Write-Host "  - 10:30 AM: Full 4-hour analysis" -ForegroundColor Green
Write-Host "  - Then every 30 mins: 1-hour analysis (11:15, 11:45, 12:15...)" -ForegroundColor Green
Write-Host ""

$taskName = "BettingWorkflow_Continuous"
$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\scheduled_workflow.ps1"
$workingDir = "C:\Users\charl\OneDrive\futuregenAI\Betting"

# Remove existing task
Write-Host "Removing existing task..." -ForegroundColor Cyan
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "  Removed existing task" -ForegroundColor Green
}

# Create action using batch wrapper
Write-Host "`nCreating task action..." -ForegroundColor Cyan
$batchPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\run_workflow.bat"
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$batchPath`"" `
    -WorkingDirectory $workingDir

# Create triggers
Write-Host "Creating triggers..." -ForegroundColor Cyan

# 1. Daily 10:30am trigger for full 4-hour analysis
$triggers = @()
$triggers += New-ScheduledTaskTrigger -Daily -At "10:30"
Write-Host "  Added trigger: 10:30 (FULL 4-hour analysis)" -ForegroundColor Cyan

# 2. Every 30 minutes from 11am-7pm for 1-hour analysis
$times = @('11:15', '11:45', '12:15', '12:45', '13:15', '13:45', '14:15', '14:45', 
           '15:15', '15:45', '16:15', '16:45', '17:15', '17:45', '18:15', '18:45',
           '19:15', '19:45')
foreach ($time in $times) {
    $triggers += New-ScheduledTaskTrigger -Daily -At $time
    Write-Host "  Added trigger: $time" -ForegroundColor Gray
}

Write-Host "  Total: 19 triggers (1 full analysis + 18 quick scans)" -ForegroundColor Green

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
    -Description "Horse racing workflow - 10:30am full analysis (4hr), then every 30min quick scans (1hr)" | Out-Null

Write-Host "  Task registered successfully!" -ForegroundColor Green

# Verify
Write-Host "`nVerifying task..." -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $taskName
$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName

Write-Host "`n=== Task Details ===" -ForegroundColor Yellow
Write-Host "Name: $($task.TaskName)"
Write-Host "State: $($task.State)"
Write-Host "Next Run: $($taskInfo.NextRunTime)"
Write-Host "Triggers: 19 total"
Write-Host "  - 10:30 AM: Full 4-hour analysis"
Write-Host "  - 11:15-19:45: Every 30 mins (1-hour analysis)"

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green

# Fix scheduled task to run every 30 minutes
Write-Host "Configuring BettingWorkflow_Continuous to run every 30 minutes..." -ForegroundColor Cyan

# Unregister existing task
Unregister-ScheduledTask -TaskName "BettingWorkflow_Continuous" -Confirm:$false -ErrorAction SilentlyContinue

# Create new trigger that repeats every 30 minutes
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration ([TimeSpan]::MaxValue)

# Create action
$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\scheduled_workflow.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`""

# Create principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Register task
Register-ScheduledTask `
    -TaskName "BettingWorkflow_Continuous" `
    -Trigger $trigger `
    -Action $action `
    -Principal $principal `
    -Settings $settings `
    -Description "Runs betting workflow every 30 minutes to generate fresh picks"

Write-Host "✓ Task configured successfully" -ForegroundColor Green
Write-Host "`nTask Details:" -ForegroundColor Cyan
Get-ScheduledTask "BettingWorkflow_Continuous" | Get-ScheduledTaskInfo | Format-List LastRunTime, NextRunTime

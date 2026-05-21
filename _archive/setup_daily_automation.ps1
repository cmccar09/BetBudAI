# setup_daily_automation.ps1
# Setup automated daily workflow + health monitoring with self-healing

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SureBet Daily Automation Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Configuration
$workflowTaskName = "SureBet_DailyWorkflow"
$monitorTaskName = "SureBet_HealthMonitor"
$scriptRoot = $PSScriptRoot

# Task 1: Daily workflow (picks generation)
Write-Host "[1/2] Setting up daily workflow task..." -ForegroundColor Yellow

$existingWorkflow = Get-ScheduledTask -TaskName $workflowTaskName -ErrorAction SilentlyContinue
if ($existingWorkflow) {
    Write-Host "  Removing existing workflow task..." -ForegroundColor Gray
    Unregister-ScheduledTask -TaskName $workflowTaskName -Confirm:$false
}

# Run workflow at 9:00 AM daily (before racing starts)
$workflowAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptRoot\scheduled_workflow.ps1`"" `
    -WorkingDirectory $scriptRoot

$workflowTrigger = New-ScheduledTaskTrigger -Daily -At "09:00"

$workflowSettings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 10)

$workflowPrincipal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType S4U `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $workflowTaskName `
    -Action $workflowAction `
    -Trigger $workflowTrigger `
    -Settings $workflowSettings `
    -Principal $workflowPrincipal `
    -Description "Daily SureBet workflow - generates picks, runs analysis, performs health check" `
    -ErrorAction Stop | Out-Null

Write-Host "  ✓ Created: $workflowTaskName" -ForegroundColor Green
Write-Host "    Schedule: Daily at 9:00 AM" -ForegroundColor Gray
Write-Host "    Script:   scheduled_workflow.ps1" -ForegroundColor Gray

# Task 2: Continuous health monitoring with self-healing
Write-Host "`n[2/2] Setting up continuous health monitor..." -ForegroundColor Yellow

$existingMonitor = Get-ScheduledTask -TaskName $monitorTaskName -ErrorAction SilentlyContinue
if ($existingMonitor) {
    Write-Host "  Removing existing monitor task..." -ForegroundColor Gray
    Unregister-ScheduledTask -TaskName $monitorTaskName -Confirm:$false
}

# Run health monitor every 2 hours
$monitorAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptRoot\self_healing_monitor.ps1`" -RunOnce" `
    -WorkingDirectory $scriptRoot

$monitorTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 2) -RepetitionDuration ([TimeSpan]::MaxValue)

$monitorSettings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5)

$monitorPrincipal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType S4U `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $monitorTaskName `
    -Action $monitorAction `
    -Trigger $monitorTrigger `
    -Settings $monitorSettings `
    -Principal $monitorPrincipal `
    -Description "SureBet health monitor with self-healing - runs every 2 hours" `
    -ErrorAction Stop | Out-Null

Write-Host "  ✓ Created: $monitorTaskName" -ForegroundColor Green
Write-Host "    Schedule: Every 2 hours" -ForegroundColor Gray
Write-Host "    Script:   self_healing_monitor.ps1" -ForegroundColor Gray

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Automation Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "✓ Daily Workflow Task:" -ForegroundColor Green
Write-Host "  - Runs at 9:00 AM daily" -ForegroundColor Gray
Write-Host "  - Generates betting picks" -ForegroundColor Gray
Write-Host "  - Enriches with Racing Post + odds movement data" -ForegroundColor Gray
Write-Host "  - Runs AI analysis via AWS Bedrock" -ForegroundColor Gray
Write-Host "  - Posts picks to DynamoDB" -ForegroundColor Gray
Write-Host "  - Executes health check after completion" -ForegroundColor Gray

Write-Host "`n✓ Health Monitor Task:" -ForegroundColor Green
Write-Host "  - Runs every 2 hours (24/7)" -ForegroundColor Gray
Write-Host "  - Checks system health (6 checks)" -ForegroundColor Gray
Write-Host "  - Auto-refreshes Betfair token if needed" -ForegroundColor Gray
Write-Host "  - Validates Lambda deployment" -ForegroundColor Gray
Write-Host "  - Runs emergency workflow if picks missing" -ForegroundColor Gray
Write-Host "  - Logs all issues to monitor.log" -ForegroundColor Gray

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Management Commands" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "View tasks:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName 'SureBet_*'" -ForegroundColor Gray

Write-Host "`nDisable tasks:" -ForegroundColor Yellow
Write-Host "  Disable-ScheduledTask -TaskName '$workflowTaskName'" -ForegroundColor Gray
Write-Host "  Disable-ScheduledTask -TaskName '$monitorTaskName'" -ForegroundColor Gray

Write-Host "`nEnable tasks:" -ForegroundColor Yellow
Write-Host "  Enable-ScheduledTask -TaskName '$workflowTaskName'" -ForegroundColor Gray
Write-Host "  Enable-ScheduledTask -TaskName '$monitorTaskName'" -ForegroundColor Gray

Write-Host "`nRun manually:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName '$workflowTaskName'  # Run workflow now" -ForegroundColor Gray
Write-Host "  Start-ScheduledTask -TaskName '$monitorTaskName'   # Run health check now" -ForegroundColor Gray

Write-Host "`nRemove tasks:" -ForegroundColor Yellow
Write-Host "  Unregister-ScheduledTask -TaskName '$workflowTaskName'" -ForegroundColor Gray
Write-Host "  Unregister-ScheduledTask -TaskName '$monitorTaskName'" -ForegroundColor Gray

Write-Host "`nView logs:" -ForegroundColor Yellow
Write-Host "  Get-Content workflow_execution.log  # Workflow runs" -ForegroundColor Gray
Write-Host "  Get-Content monitor.log             # Health checks" -ForegroundColor Gray
Write-Host "  Get-Content health_check_alerts.log # Issues found" -ForegroundColor Gray

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  Automation is now active!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "Next workflow run: Tomorrow at 9:00 AM" -ForegroundColor Cyan
Write-Host "Next health check:  Every 2 hours starting now`n" -ForegroundColor Cyan

# Test the monitor immediately
Write-Host "Running initial health check..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName $monitorTaskName
Start-Sleep -Seconds 3
Write-Host "✓ Health monitor started`n" -ForegroundColor Green

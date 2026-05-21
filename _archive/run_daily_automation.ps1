# run_daily_automation.ps1
# Wrapper script to run daily workflow + health monitoring
# This can be added to Windows Task Scheduler manually or run via script

param(
    [switch]$WorkflowOnly,
    [switch]$MonitorOnly
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host "`n[$timestamp] SureBet Daily Automation Starting..." -ForegroundColor Cyan

if (-not $MonitorOnly) {
    # Run the daily workflow
    Write-Host "`n[WORKFLOW] Executing daily betting workflow..." -ForegroundColor Yellow
    try {
        & "$PSScriptRoot\scheduled_workflow.ps1"
        Write-Host "[WORKFLOW] ✓ Completed successfully" -ForegroundColor Green
    } catch {
        Write-Host "[WORKFLOW] ✗ Failed: $_" -ForegroundColor Red
        # Log the error
        "$timestamp - Workflow failed: $_" | Out-File -Append -FilePath "$PSScriptRoot\automation_errors.log"
    }
}

if (-not $WorkflowOnly) {
    # Run the self-healing health monitor
    Write-Host "`n[MONITOR] Running health check with self-healing..." -ForegroundColor Yellow
    try {
        & "$PSScriptRoot\self_healing_monitor.ps1" -RunOnce
        Write-Host "[MONITOR] ✓ Health check completed" -ForegroundColor Green
    } catch {
        Write-Host "[MONITOR] ✗ Failed: $_" -ForegroundColor Red
        # Log the error
        "$timestamp - Monitor failed: $_" | Out-File -Append -FilePath "$PSScriptRoot\automation_errors.log"
    }
}

$endTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "`n[$endTime] SureBet Daily Automation Completed`n" -ForegroundColor Cyan

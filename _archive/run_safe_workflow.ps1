# SAFE WORKFLOW RUNNER
# Runs health check, recovery, then workflow
# Use this in scheduled tasks to prevent failures

$ErrorActionPreference = "Continue"

Write-Host "`n=== SAFE WORKFLOW RUNNER ===" -ForegroundColor Cyan
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

# Step 1: Health Check
Write-Host "`nStep 1: Health Check..." -ForegroundColor Yellow
python daily_health_check.py
$healthOk = $LASTEXITCODE -eq 0

if (-not $healthOk) {
    Write-Host "  Health check failed - attempting recovery..." -ForegroundColor Red
    
    # Step 2: Auto Recovery
    Write-Host "`nStep 2: Auto Recovery..." -ForegroundColor Yellow
    python auto_recovery.py
    $recoveryOk = $LASTEXITCODE -eq 0
    
    if (-not $recoveryOk) {
        Write-Host "`n✗ Recovery failed - workflow aborted" -ForegroundColor Red
        Write-Host "  Manual intervention required!" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "  Recovery succeeded!" -ForegroundColor Green
}

# Step 3: Run Main Workflow
Write-Host "`nStep 3: Running Comprehensive Workflow..." -ForegroundColor Yellow
python comprehensive_workflow.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Workflow completed successfully!" -ForegroundColor Green
    
    # Step 4: Verify picks were created
    Write-Host "`nStep 4: Verifying picks..." -ForegroundColor Yellow
    python learning_summary.py | Select-String "UI picks"
    
    Write-Host "`n=== WORKFLOW COMPLETE ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Workflow failed!" -ForegroundColor Red
    exit 1
}

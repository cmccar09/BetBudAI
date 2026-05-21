# Deploy Phase 1 Signals to Lambda Functions
# ==========================================

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*69) -ForegroundColor Cyan
Write-Host "DEPLOYING PHASE 1 SIGNALS TO LAMBDA" -ForegroundColor Cyan
Write-Host ("="*70) -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# 1. Package scoring module with signals
Write-Host "[1/3] Packaging scoring + signals module..." -ForegroundColor Yellow
Set-Location backend\core
Remove-Item -Path scoring_deploy.zip -ErrorAction SilentlyContinue
Compress-Archive -Path scoring\*.py,signals\*.py -DestinationPath scoring_deploy.zip -Force
Write-Host "  [SUCCESS] scoring_deploy.zip created" -ForegroundColor Green

# 2. Deploy to Analysis Lambda
Write-Host "`n[2/3] Deploying to betbudai-analysis Lambda..." -ForegroundColor Yellow
aws lambda update-function-code `
  --function-name betbudai-analysis `
  --zip-file fileb://scoring_deploy.zip `
  --region eu-west-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [SUCCESS] betbudai-analysis updated" -ForegroundColor Green
} else {
    Write-Host "  [FAILED] betbudai-analysis deployment failed" -ForegroundColor Red
    exit 1
}

# 3. Deploy to Morning Pipeline Lambda
Write-Host "`n[3/3] Deploying to betbudai-morning Lambda..." -ForegroundColor Yellow
Set-Location ..\pipeline\morning
Remove-Item -Path morning_deploy.zip -ErrorAction SilentlyContinue
Compress-Archive -Path handler.py -DestinationPath morning_deploy.zip -Force

aws lambda update-function-code `
  --function-name betbudai-morning `
  --zip-file fileb://morning_deploy.zip `
  --region eu-west-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [SUCCESS] betbudai-morning updated" -ForegroundColor Green
} else {
    Write-Host "  [FAILED] betbudai-morning deployment failed" -ForegroundColor Red
    exit 1
}

# Cleanup
Set-Location ..\..\..\
Remove-Item backend\core\scoring_deploy.zip -ErrorAction SilentlyContinue
Remove-Item backend\pipeline\morning\morning_deploy.zip -ErrorAction SilentlyContinue

Write-Host "`n" -NoNewline
Write-Host ("="*70) -ForegroundColor Cyan
Write-Host "[SUCCESS] PHASE 1 DEPLOYED TO LAMBDA" -ForegroundColor Green
Write-Host ("="*70) -ForegroundColor Cyan

Write-Host "`nDeployed Functions:" -ForegroundColor White
Write-Host "  - betbudai-analysis (scoring with Phase 1 signals)" -ForegroundColor White
Write-Host "  - betbudai-morning (pipeline integration)" -ForegroundColor White

Write-Host "`nPhase 1 Signals Active:" -ForegroundColor White
Write-Host "  [ACTIVE] Run Style + Pace Matching (+12pts)" -ForegroundColor Green
Write-Host "  [ACTIVE] Jockey Upgrade Detection (+10pts)" -ForegroundColor Green
Write-Host "  [PENDING] Equipment (needs HTML extraction)" -ForegroundColor Yellow
Write-Host "  [PENDING] Liquidity (needs Betfair volume)" -ForegroundColor Yellow

Write-Host "`nNext Step:" -ForegroundColor Cyan
Write-Host "  Run: python scripts\rerun_todays_analysis.py" -ForegroundColor White
Write-Host "  This will regenerate today's picks with Phase 1 signals active" -ForegroundColor White

Write-Host ""

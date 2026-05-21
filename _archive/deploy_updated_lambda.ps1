#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy updated Lambda with results checking feature
.DESCRIPTION
    Packages lambda_api_picks.py with requests library and deploys to AWS
#>

$ErrorActionPreference = "Stop"

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Deploying Updated Lambda with Results Feature" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

# Clean up old package
if (Test-Path "lambda-results.zip") {
    Remove-Item "lambda-results.zip" -Force
}

if (Test-Path "lambda-package-results") {
    Remove-Item "lambda-package-results" -Recurse -Force
}

# Create package directory
New-Item -ItemType Directory -Path "lambda-package-results" | Out-Null

Write-Host "`n1. Installing dependencies..." -ForegroundColor Yellow
pip install --target lambda-package-results requests boto3 -q

Write-Host "2. Copying Lambda function..." -ForegroundColor Yellow
Copy-Item "lambda_api_picks.py" "lambda-package-results/lambda_function.py"

Write-Host "3. Creating deployment package..." -ForegroundColor Yellow
Push-Location "lambda-package-results"
Compress-Archive -Path * -DestinationPath "../lambda-results.zip" -Force
Pop-Location

Write-Host "4. Deploying to AWS Lambda..." -ForegroundColor Yellow
aws lambda update-function-code `
    --function-name BettingPicksAPI `
    --zip-file fileb://lambda-results.zip `
    --region eu-west-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Lambda deployed successfully!" -ForegroundColor Green
    Write-Host "`nNew endpoint available:" -ForegroundColor Cyan
    Write-Host "  GET /api/results/today - Check today's results" -ForegroundColor White
    
    Write-Host "`nNext: Configure environment variables in Lambda:" -ForegroundColor Yellow
    Write-Host "  BETFAIR_SESSION_TOKEN" -ForegroundColor Cyan
    Write-Host "  BETFAIR_APP_KEY" -ForegroundColor Cyan
    Write-Host "`nOr run: .\configure_lambda_betfair_creds.ps1" -ForegroundColor White
} else {
    Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`nCleaning up..." -ForegroundColor Gray
Remove-Item "lambda-package-results" -Recurse -Force

Write-Host "`n✓ Complete!" -ForegroundColor Green

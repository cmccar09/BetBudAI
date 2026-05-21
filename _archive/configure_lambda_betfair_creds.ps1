#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Configure Betfair credentials as Lambda environment variables
.DESCRIPTION
    Loads betfair-creds.json and sets as Lambda env vars
#>

$ErrorActionPreference = "Stop"

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Configure Lambda Betfair Credentials" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

# Load betfair creds
if (-not (Test-Path "betfair-creds.json")) {
    Write-Host "`n❌ ERROR: betfair-creds.json not found!" -ForegroundColor Red
    exit 1
}

$creds = Get-Content "betfair-creds.json" | ConvertFrom-Json

$sessionToken = $creds.session_token
$appKey = $creds.app_key

if (-not $sessionToken -or -not $appKey) {
    Write-Host "`n❌ ERROR: Missing session_token or app_key in betfair-creds.json" -ForegroundColor Red
    exit 1
}

Write-Host "`nSetting Lambda environment variables..." -ForegroundColor Yellow

aws lambda update-function-configuration `
    --function-name betting `
    --environment "Variables={BETFAIR_SESSION_TOKEN=$sessionToken,BETFAIR_APP_KEY=$appKey}" `
    --region eu-west-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Credentials configured successfully!" -ForegroundColor Green
    Write-Host "`nLambda can now fetch results from Betfair API" -ForegroundColor Cyan
    
    Write-Host "`n⚠️  Note: Session tokens expire!" -ForegroundColor Yellow
    Write-Host "  Re-run this script if you refresh your Betfair session" -ForegroundColor White
} else {
    Write-Host "`n❌ Configuration failed!" -ForegroundColor Red
    exit 1
}

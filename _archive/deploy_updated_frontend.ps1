#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build and deploy updated frontend with results feature
.DESCRIPTION
    Rebuilds React app and deploys to Amplify
#>

$ErrorActionPreference = "Stop"

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Building & Deploying Frontend with Results Feature" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

Push-Location "frontend"

Write-Host "`n1. Installing dependencies..." -ForegroundColor Yellow
npm install

Write-Host "`n2. Building production bundle..." -ForegroundColor Yellow
# Use API Gateway URL (default in App.js)
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Build failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "`n✓ Build complete!" -ForegroundColor Green

Write-Host "`n3. Deployment options:" -ForegroundColor Cyan
Write-Host "`nOption A - Git Push (Amplify auto-deploys):" -ForegroundColor Yellow
Write-Host "  cd .." -ForegroundColor White
Write-Host "  git add frontend/" -ForegroundColor White
Write-Host "  git commit -m 'Add results checking feature'" -ForegroundColor White
Write-Host "  git push" -ForegroundColor White

Write-Host "`nOption B - Manual Deploy to S3/Amplify:" -ForegroundColor Yellow
Write-Host "  Use Amplify Console to trigger manual deployment" -ForegroundColor White

Write-Host "`nOption C - Local test first:" -ForegroundColor Yellow
Write-Host "  npm start" -ForegroundColor White
Write-Host "  (Opens http://localhost:3000)" -ForegroundColor White

Pop-Location

Write-Host "`n✓ Frontend build ready!" -ForegroundColor Green

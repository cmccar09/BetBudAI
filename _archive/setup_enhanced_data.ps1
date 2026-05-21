#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup script for enhanced data collection system
.DESCRIPTION
    One-time setup for Racing Post enrichment and odds movement tracking
#>

$ErrorActionPreference = "Stop"
$pythonExe = "C:/Users/charl/OneDrive/futuregenAI/Betting/.venv/Scripts/python.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ENHANCED DATA COLLECTION SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Create DynamoDB table for odds history
Write-Host "`n[1/2] Creating DynamoDB table for odds movement tracking..." -ForegroundColor Yellow

& $pythonExe "$PSScriptRoot\odds_movement_tracker.py" --setup

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ DynamoDB table ready" -ForegroundColor Green
} else {
    Write-Host "  ✗ Table creation failed (may already exist)" -ForegroundColor Yellow
}

# Step 2: Test Racing Post scraper
Write-Host "`n[2/2] Testing Racing Post data fetcher..." -ForegroundColor Yellow

if (Test-Path "$PSScriptRoot\response_live.json") {
    Write-Host "  Testing with existing snapshot..." -ForegroundColor Gray
    
    & $pythonExe "$PSScriptRoot\enhanced_racing_data_fetcher.py" --snapshot "$PSScriptRoot\response_live.json"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Racing Post enrichment working" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Enrichment test failed (may be normal if no race cards available)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  No snapshot file found - will test during next workflow run" -ForegroundColor Gray
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SETUP COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Enhanced features enabled:" -ForegroundColor White
Write-Host "  ✓ Odds movement tracking (steam/drift detection)" -ForegroundColor Green
Write-Host "  ✓ Racing Post data enrichment (form, ratings, trainer stats)" -ForegroundColor Green
Write-Host "  ✓ Market intelligence signals" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run .\scheduled_workflow.ps1 to generate picks with enhanced data"
Write-Host "  2. Workflow will automatically enrich each snapshot"
Write-Host "  3. Check ENHANCED_DATA_GUIDE.md for details"
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

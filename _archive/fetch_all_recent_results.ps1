#!/usr/bin/env pwsh
<#
.SYNOPSIS
    One-time script to fetch all available results from recent selections
.DESCRIPTION
    Attempts to fetch results for all selection files in history/
    Only works for races within last 24-48 hours (Betfair API limitation)
#>

$ErrorActionPreference = "Continue"
$pythonExe = "C:/Users/charl/OneDrive/futuregenAI/Betting/.venv/Scripts/python.exe"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "FETCH ALL RECENT RESULTS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Find all selection files
$selectionFiles = Get-ChildItem -Path ".\history" -Filter "selections_*.csv" | Sort-Object Name

Write-Host "Found $($selectionFiles.Count) selection files" -ForegroundColor Yellow

foreach ($file in $selectionFiles) {
    # Extract date from filename: selections_YYYYMMDD_HHMMSS.csv
    if ($file.Name -match "selections_(\d{8})") {
        $dateSlug = $Matches[1]
        $year = $dateSlug.Substring(0, 4)
        $month = $dateSlug.Substring(4, 2)
        $day = $dateSlug.Substring(6, 2)
        $dateStr = "$year-$month-$day"
        
        $resultsFile = ".\history\results_$dateSlug.json"
        
        # Skip if results already exist
        if (Test-Path $resultsFile) {
            Write-Host "`n✓ $dateStr - Results already fetched" -ForegroundColor Gray
            continue
        }
        
        # Check how old
        $raceDate = [datetime]::ParseExact($dateSlug, "yyyyMMdd", $null)
        $hoursOld = ((Get-Date) - $raceDate).TotalHours
        
        if ($hoursOld -gt 48) {
            Write-Host "`n⏭️  $dateStr - Too old ($([int]$hoursOld/24) days), skipping" -ForegroundColor DarkGray
            continue
        }
        
        Write-Host "`n⏳ $dateStr - Fetching results ($([int]$hoursOld) hours old)..." -ForegroundColor Yellow
        & $pythonExe ".\fetch_race_results.py" --date $dateStr --selections $file.FullName --out $resultsFile
        
        if ($LASTEXITCODE -eq 0 -and (Test-Path $resultsFile)) {
            $resultData = Get-Content $resultsFile | ConvertFrom-Json
            $resultCount = $resultData.Count
            
            if ($resultCount -gt 0) {
                Write-Host "  ✓ Saved $resultCount runner results" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  No results returned (markets may be expired)" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RESULTS FETCH COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Run evaluate_performance.py on fetched results" -ForegroundColor White
Write-Host "  2. System will auto-fetch results at 10pm daily going forward" -ForegroundColor White
Write-Host "========================================`n" -ForegroundColor Cyan

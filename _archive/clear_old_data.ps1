#!/usr/bin/env pwsh
# WARNING: THIS SCRIPT DELETES HISTORICAL DATA - DISABLED!
# Historical data is needed for AI learning and performance analysis.
# The UI already filters past races using race_time in the API.

Write-Host "`n" -NoNewline
Write-Host "="*80 -ForegroundColor Red
Write-Host "ERROR: This cleanup script is DISABLED" -ForegroundColor Red
Write-Host "="*80 -ForegroundColor Red
Write-Host "Historical betting data must be preserved for AI learning." -ForegroundColor Yellow
Write-Host "The UI automatically hides past races using race_time filtering." -ForegroundColor Yellow
Write-Host "If you need to clean up, contact the developer." -ForegroundColor Yellow
Write-Host "="*80 -ForegroundColor Red
Write-Host "`n" -NoNewline
exit 1

Write-Host "Clearing old test data from DynamoDB..." -ForegroundColor Yellow
Write-Host ""

$today = Get-Date -Format "yyyy-MM-dd"
Write-Host "Today's date: $today" -ForegroundColor Cyan

# Get all items
$allItems = aws dynamodb scan --table-name SureBetBets --region eu-west-1 | ConvertFrom-Json

$deleteCount = 0
$keepCount = 0

foreach ($item in $allItems.Items) {
    $betId = $item.bet_id.S
    $date = $item.date.S
    $horse = $item.horse.S
    
    # Delete if:
    # 1. Date is before today
    # 2. Or it's a test horse (Golden Spirit, Silver Thunder, Royal Command)
    $isTestData = $horse -in @("Golden Spirit", "Silver Thunder", "Royal Command", "Lucky Strike", "Speed Demon", "Thunder Bolt", "Golden Arrow", "Royal Flash", "Noble Demon", "Mighty Bolt", "Thunder King", "Silver Flash", "Lucky Spirit")
    
    if ($date -lt $today -or $isTestData) {
        Write-Host "  Deleting: $horse ($betId) - Date: $date" -ForegroundColor Red
        aws dynamodb delete-item --table-name SureBetBets --region eu-west-1 --key "{`"bet_id`": {`"S`": `"$betId`"}}" | Out-Null
        $deleteCount++
    } else {
        Write-Host "  Keeping: $horse ($betId) - Date: $date" -ForegroundColor Green
        $keepCount++
    }
}

Write-Host ""
Write-Host "="*60
Write-Host "Cleanup Complete" -ForegroundColor Cyan
Write-Host "  Deleted: $deleteCount items" -ForegroundColor Red
Write-Host "  Kept: $keepCount items" -ForegroundColor Green
Write-Host "="*60

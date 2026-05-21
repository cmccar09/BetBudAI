# Test Betfair Authentication
Write-Host "=== TESTING BETFAIR AUTHENTICATION ===" -ForegroundColor Cyan

Write-Host "`nInvoking Lambda..." -ForegroundColor Yellow
aws lambda invoke --function-name BettingWorkflowScheduled final-test.json | Out-Null

Write-Host "Waiting for execution (20 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

Write-Host "`nResult:" -ForegroundColor Cyan
$result = Get-Content final-test.json -Raw | ConvertFrom-Json

if ($result.statusCode -eq 200) {
    $body = $result.body | ConvertFrom-Json
    if ($body.success) {
        Write-Host "`n✅ SUCCESS!" -ForegroundColor Green
        Write-Host "   Picks: $($body.picks_count)" -ForegroundColor White
        Write-Host "`n🎉 System is working! Refresh your UI:" -ForegroundColor Cyan
        Write-Host "   https://main.dazy5igjmo5m6.amplifyapp.com/" -ForegroundColor White
    } else {
        Write-Host "`n❌ Authentication failed: $($body.error)" -ForegroundColor Red
        Write-Host "`nThis might mean:" -ForegroundColor Yellow
        Write-Host "  • Betfair certificate needs more time to activate (wait 5-10 min)" -ForegroundColor White
        Write-Host "  • Certificate wasn't uploaded correctly" -ForegroundColor White
    }
} else {
    Write-Host "`n❌ Lambda error (Status: $($result.statusCode))" -ForegroundColor Red
}

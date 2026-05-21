# Fix Betfair Certificate Authentication
Write-Host "=== BETFAIR CERTIFICATE FIX ===" -ForegroundColor Cyan

# The certificate that's currently on Betfair website should match what's in AWS
# Make sure we use the NEW certificate (with charles.mccarthy@gmail.com)

Write-Host "`n1. Uploading NEW certificate to AWS..." -ForegroundColor Yellow
$cert = Get-Content "betfair-client.crt" -Raw
$key = Get-Content "betfair-client.key" -Raw

$secret = @{
    certificate = $cert
    private_key = $key
} | ConvertTo-Json

$secret | Out-File "fix-cert.json" -Encoding UTF8

aws secretsmanager put-secret-value --secret-id betfair-ssl-certificate --secret-string file://fix-cert.json
Remove-Item "fix-cert.json"

Write-Host "✓ Certificate uploaded to AWS" -ForegroundColor Green

Write-Host "`n2. Verifying Betfair website has matching certificate..." -ForegroundColor Yellow
Write-Host "   Check Betfair shows: CN=Charles McCarthy, E=charles.mccarthy@gmail.com" -ForegroundColor White

Write-Host "`n3. Testing Lambda..." -ForegroundColor Yellow
aws lambda invoke --function-name BettingWorkflowScheduled test-fix.json | Out-Null
Start-Sleep -Seconds 20

$result = Get-Content test-fix.json -Raw | ConvertFrom-Json

if ($result.statusCode -eq 200) {
    $body = $result.body | ConvertFrom-Json
    if ($body.success) {
        Write-Host "`n✅ SUCCESS! Authentication working!" -ForegroundColor Green
        Write-Host "Picks: $($body.picks_count)" -ForegroundColor White
    } else {
        Write-Host "`n❌ Failed: $($body.error)" -ForegroundColor Red
        Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
        Write-Host "• Verify certificate on Betfair matches the one we just uploaded" -ForegroundColor White
        Write-Host "• Certificate might need 15-30 min to activate on Betfair's side" -ForegroundColor White
        Write-Host "• Check if Betfair username is correct: cmccar02" -ForegroundColor White
    }
} else {
    Write-Host "`n❌ Lambda error" -ForegroundColor Red
}

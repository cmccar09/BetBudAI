# Upload Betfair Certificates to AWS
$cert = Get-Content "betfair-client.crt" -Raw
$key = Get-Content "betfair-client.key" -Raw

$secret = @{
    certificate = $cert
    private_key = $key
}

$jsonSecret = $secret | ConvertTo-Json

# Save to temp file
$jsonSecret | Out-File -FilePath "temp-secret.json" -Encoding UTF8 -NoNewline

# Delete old secret (ignore error if doesn't exist)
aws secretsmanager delete-secret --secret-id betfair-ssl-certificate --force-delete-without-recovery 2>$null

# Wait for deletion
Start-Sleep -Seconds 5

# Create new secret from file
aws secretsmanager create-secret `
    --name betfair-ssl-certificate `
    --description "Betfair SSL Certificate - charles.mccarthy@gmail.com" `
    --secret-string file://temp-secret.json

# Clean up
Remove-Item temp-secret.json

Write-Host "`n✅ Certificate uploaded to AWS Secrets Manager" -ForegroundColor Green
Write-Host "`nEmail on certificate: charles.mccarthy@gmail.com" -ForegroundColor White
Write-Host "`nNOW: Upload betfair-client.crt to Betfair website" -ForegroundColor Yellow
Write-Host "(Delete old certificates first)" -ForegroundColor Red

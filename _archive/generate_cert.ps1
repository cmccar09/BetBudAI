# Generate Betfair SSL Certificate with CN=cmccar02

Write-Host "Generating certificate..." -ForegroundColor Cyan

# Create certificate
$cert = New-SelfSignedCertificate `
    -Subject "CN=cmccar02" `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -KeyExportPolicy Exportable `
    -NotAfter (Get-Date).AddYears(3)

Write-Host "Certificate created: $($cert.Subject)" -ForegroundColor Green

# Export to PFX
$pfxPath = "temp.pfx"
$password = ConvertTo-SecureString -String "temppass123" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $password | Out-Null

# Load PFX
$pfxCert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2(
    $pfxPath, 
    "temppass123", 
    [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable
)

# Export certificate as PEM
$certBytes = $pfxCert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
$certPem = "-----BEGIN CERTIFICATE-----`r`n"
$certPem += [Convert]::ToBase64String($certBytes, [Base64FormattingOptions]::InsertLineBreaks)
$certPem += "`r`n-----END CERTIFICATE-----"
[System.IO.File]::WriteAllText("betfair-final.crt", $certPem)

Write-Host "Certificate saved to betfair-final.crt" -ForegroundColor Green

# Export private key as PEM
$rsa = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($pfxCert)
$keyBytes = $rsa.ExportPkcs8PrivateKey()
$keyPem = "-----BEGIN PRIVATE KEY-----`r`n"
$keyPem += [Convert]::ToBase64String($keyBytes, [Base64FormattingOptions]::InsertLineBreaks)
$keyPem += "`r`n-----END PRIVATE KEY-----"
[System.IO.File]::WriteAllText("betfair-final.key", $keyPem)

Write-Host "Private key saved to betfair-final.key" -ForegroundColor Green

# Cleanup
Remove-Item $pfxPath -Force
Remove-Item "Cert:\CurrentUser\My\$($cert.Thumbprint)" -Force

Write-Host "`nFiles created:" -ForegroundColor Cyan
Get-Item betfair-final.crt, betfair-final.key | Format-Table Name, Length -AutoSize

Write-Host "`n=== NEXT STEP ===" -ForegroundColor Yellow
Write-Host "Upload betfair-final.crt to Betfair at:" -ForegroundColor White
Write-Host "https://myaccount.betfair.com/accountdetails/mysecurity?showAPI=1" -ForegroundColor Cyan

# Generate Betfair SSL Certificate
# This creates a self-signed certificate for Betfair API authentication

Write-Host "Generating Betfair SSL Certificate..." -ForegroundColor Cyan

# Certificate details from Betfair
$certDetails = @{
    Subject = "CN=Charles McCarthy, O=Betting Bot, L=Dublin, ST=Dublin, C=IE"
    FriendlyName = "Betfair API Certificate"
    NotAfter = (Get-Date).AddYears(3)
    CertStoreLocation = "Cert:\CurrentUser\My"
    KeyExportPolicy = "Exportable"
    KeySpec = "Signature"
    KeyLength = 2048
    KeyAlgorithm = "RSA"
    HashAlgorithm = "SHA256"
}

# Generate the certificate
Write-Host "Creating certificate in Windows certificate store..." -ForegroundColor Yellow
$cert = New-SelfSignedCertificate @certDetails

Write-Host "✓ Certificate created with thumbprint: $($cert.Thumbprint)" -ForegroundColor Green

# Export the certificate (.crt file)
$certPath = "betfair-client.crt"
$keyPath = "betfair-client.key"
$pfxPath = "betfair-client.pfx"

# Export as PFX first (with private key)
Write-Host "`nExporting certificate to PFX..." -ForegroundColor Yellow
$password = ConvertTo-SecureString -String "betfair123" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $password | Out-Null
Write-Host "✓ Exported: $pfxPath" -ForegroundColor Green

# Convert PFX to PEM format for Betfair
Write-Host "`nConverting to PEM format for Betfair..." -ForegroundColor Yellow

# Export certificate (public key) to CRT
$certBytes = $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
[System.IO.File]::WriteAllBytes((Join-Path $PWD $certPath), $certBytes)
Write-Host "✓ Exported: $certPath" -ForegroundColor Green

# Export private key
Write-Host "`nExporting private key..." -ForegroundColor Yellow
Write-Host "Note: You'll need OpenSSL to convert PFX to KEY format" -ForegroundColor Yellow

# Try using OpenSSL if available
$opensslPath = Get-Command openssl -ErrorAction SilentlyContinue

if ($opensslPath) {
    Write-Host "Found OpenSSL, converting to KEY format..." -ForegroundColor Cyan
    
    # Extract private key
    & openssl pkcs12 -in $pfxPath -nocerts -nodes -out $keyPath -passin pass:betfair123
    
    # Extract certificate in PEM format
    & openssl pkcs12 -in $pfxPath -clcerts -nokeys -out "${certPath}.pem" -passin pass:betfair123
    
    # Convert to proper format
    & openssl rsa -in $keyPath -out $keyPath
    & openssl x509 -in "${certPath}.pem" -out $certPath
    
    Remove-Item "${certPath}.pem" -ErrorAction SilentlyContinue
    
    Write-Host "✓ Exported: $keyPath" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ OpenSSL not found. Installing OpenSSL..." -ForegroundColor Yellow
    Write-Host "You can install it with: winget install OpenSSL.OpenSSL" -ForegroundColor Yellow
    
    # Try chocolatey
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "Installing via Chocolatey..." -ForegroundColor Cyan
        choco install openssl -y
        
        # Reload PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        # Try again
        if (Get-Command openssl -ErrorAction SilentlyContinue) {
            & openssl pkcs12 -in $pfxPath -nocerts -nodes -out $keyPath -passin pass:betfair123
            & openssl rsa -in $keyPath -out $keyPath
            Write-Host "✓ Exported: $keyPath" -ForegroundColor Green
        }
    } else {
        Write-Host "`nManual conversion needed:" -ForegroundColor Yellow
        Write-Host "1. Install OpenSSL from: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor White
        Write-Host "2. Run: openssl pkcs12 -in $pfxPath -nocerts -nodes -out $keyPath -passin pass:betfair123" -ForegroundColor White
        Write-Host "3. Run: openssl rsa -in $keyPath -out $keyPath" -ForegroundColor White
    }
}

Write-Host "`n=== NEXT STEPS ===" -ForegroundColor Cyan
Write-Host "1. Upload $certPath to Betfair (My Account → API → Certificate Management)" -ForegroundColor White
Write-Host "2. After uploading to Betfair, run: .\upload_betfair_certs_to_aws.ps1" -ForegroundColor White
Write-Host "3. The Lambda function will then be able to authenticate with Betfair" -ForegroundColor White

Write-Host "`n✓ Certificate generation complete!" -ForegroundColor Green

# Generate CSR for Betfair
Write-Host "Generating Certificate Signing Request for Betfair..." -ForegroundColor Cyan

# Create a new certificate request
$subject = "E=charles.mccarthy@gmail.com, CN=Charles McCarthy, O=Betting Bot, L=Dublin, ST=Dublin, C=IE"

# Generate private key and CSR using certreq
$infFile = @"
[NewRequest]
Subject = "$subject"
KeySpec = 1
KeyLength = 2048
Exportable = TRUE
MachineKeySet = FALSE
SMIME = FALSE
PrivateKeyArchive = FALSE
UserProtected = FALSE
UseExistingKeySet = FALSE
ProviderName = "Microsoft RSA SChannel Cryptographic Provider"
ProviderType = 12
RequestType = PKCS10
KeyUsage = 0xa0

[EnhancedKeyUsageExtension]
OID=1.3.6.1.5.5.7.3.2
"@

$infFile | Out-File -FilePath "betfair.inf" -Encoding ASCII

Write-Host "Creating CSR..." -ForegroundColor Yellow
certreq -new betfair.inf betfair.csr

if (Test-Path betfair.csr) {
    Write-Host "`n✅ CSR created: betfair.csr" -ForegroundColor Green
    Write-Host "`nBUT WAIT - Betfair doesn't use CSR!" -ForegroundColor Red
    Write-Host "`nBetfair uses self-signed certificates. The issue might be:" -ForegroundColor Yellow
    Write-Host "1. Certificate needs more time to activate on Betfair's side" -ForegroundColor White
    Write-Host "2. OR we need to generate using openssl instead of Windows" -ForegroundColor White
    
    Remove-Item betfair.inf, betfair.csr -ErrorAction SilentlyContinue
}

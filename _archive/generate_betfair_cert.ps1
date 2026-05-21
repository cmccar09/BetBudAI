#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Generate self-signed SSL certificate for Betfair API
.DESCRIPTION
    Creates a certificate signing request (CSR) and private key for Betfair automated betting
#>

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Generate Betfair SSL Certificate" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""

# Check for OpenSSL
$openssl = Get-Command openssl -ErrorAction SilentlyContinue

if (-not $openssl) {
    Write-Host "❌ OpenSSL not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Installing OpenSSL..." -ForegroundColor Yellow
    
    # Try to install via winget
    try {
        winget install --id ShiningLight.OpenSSL -e --silent
        Write-Host "✓ OpenSSL installed" -ForegroundColor Green
        Write-Host "⚠ Please restart PowerShell and run this script again" -ForegroundColor Yellow
        exit 0
    } catch {
        Write-Host "❌ Auto-install failed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please install OpenSSL manually:" -ForegroundColor Yellow
        Write-Host "1. Download from: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor White
        Write-Host "2. Install 'Win64 OpenSSL' (Light version is fine)" -ForegroundColor White
        Write-Host "3. Add to PATH or use full path" -ForegroundColor White
        exit 1
    }
}

Write-Host "✓ OpenSSL found: $($openssl.Source)" -ForegroundColor Green
Write-Host ""

# Certificate details
Write-Host "Certificate Information:" -ForegroundColor Cyan
Write-Host "(Press Enter to use defaults)" -ForegroundColor Gray
Write-Host ""

$country = Read-Host "Country Code [IE]"
if ([string]::IsNullOrWhiteSpace($country)) { $country = "IE" }

$state = Read-Host "State/Province [Dublin]"
if ([string]::IsNullOrWhiteSpace($state)) { $state = "Dublin" }

$city = Read-Host "City [Dublin]"
if ([string]::IsNullOrWhiteSpace($city)) { $city = "Dublin" }

$org = Read-Host "Organization [Betting Bot]"
if ([string]::IsNullOrWhiteSpace($org)) { $org = "Betting Bot" }

$commonName = Read-Host "Common Name [Your Name]"
if ([string]::IsNullOrWhiteSpace($commonName)) { $commonName = "Betfair Client" }

$email = Read-Host "Email [your@email.com]"

Write-Host ""
Write-Host "Generating certificate..." -ForegroundColor Yellow

# Generate private key (2048-bit RSA)
$keyFile = ".\betfair-client.key"
$csrFile = ".\betfair-client.csr"
$certFile = ".\betfair-client.crt"

# Step 1: Generate private key
Write-Host "  1. Generating private key..." -ForegroundColor Gray
& openssl genrsa -out $keyFile 2048 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to generate private key" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Private key created: $keyFile" -ForegroundColor Green

# Step 2: Generate CSR (Certificate Signing Request)
Write-Host "  2. Generating certificate signing request..." -ForegroundColor Gray

$subject = "/C=$country/ST=$state/L=$city/O=$org/CN=$commonName"
if ($email) { $subject += "/emailAddress=$email" }

& openssl req -new -key $keyFile -out $csrFile -subj $subject 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to generate CSR" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ CSR created: $csrFile" -ForegroundColor Green

# Step 3: Generate self-signed certificate
Write-Host "  3. Generating self-signed certificate..." -ForegroundColor Gray
& openssl x509 -req -days 1095 -in $csrFile -signkey $keyFile -out $certFile 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to generate certificate" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Certificate created: $certFile" -ForegroundColor Green

Write-Host ""
Write-Host "="*60 -ForegroundColor Green
Write-Host "✓ Certificate Generation Complete!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green
Write-Host ""

Write-Host "Files created:" -ForegroundColor Cyan
Write-Host "  • $keyFile (Private Key - Keep Secure!)" -ForegroundColor White
Write-Host "  • $csrFile (Certificate Signing Request)" -ForegroundColor White
Write-Host "  • $certFile (Self-Signed Certificate)" -ForegroundColor White
Write-Host ""

Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Upload Certificate to Betfair:" -ForegroundColor Cyan
Write-Host "   a. Go to: https://developer.betfair.com/" -ForegroundColor White
Write-Host "   b. Login with your account" -ForegroundColor White
Write-Host "   c. Navigate to: My Account → Bot Access" -ForegroundColor White
Write-Host "   d. Click 'Upload Certificate'" -ForegroundColor White
Write-Host "   e. Select file: $certFile" -ForegroundColor Yellow
Write-Host "   f. Click 'Upload'" -ForegroundColor White
Write-Host ""

Write-Host "2. Update Configuration:" -ForegroundColor Cyan
Write-Host "   Run: .\update_betfair_config.ps1" -ForegroundColor White
Write-Host ""

Write-Host "⚠  IMPORTANT: Keep $keyFile secure and private!" -ForegroundColor Red
Write-Host ""

# Update betfair-creds.json
if (Test-Path ".\betfair-creds.json") {
    $update = Read-Host "Update betfair-creds.json with certificate paths? (y/n)"
    if ($update -eq 'y' -or $update -eq 'Y') {
        $creds = Get-Content ".\betfair-creds.json" | ConvertFrom-Json
        $creds | Add-Member -NotePropertyName "cert_file" -NotePropertyValue $certFile -Force
        $creds | Add-Member -NotePropertyName "key_file" -NotePropertyValue $keyFile -Force
        $creds | ConvertTo-Json -Depth 10 | Set-Content ".\betfair-creds.json"
        Write-Host "✓ Updated betfair-creds.json" -ForegroundColor Green
        Write-Host ""
    }
}

Write-Host "Open Betfair developer portal now? (y/n): " -NoNewline -ForegroundColor Yellow
$open = Read-Host

if ($open -eq 'y' -or $open -eq 'Y') {
    Start-Process "https://developer.betfair.com/"
    Write-Host ""
    Write-Host "✓ Opening Betfair developer portal..." -ForegroundColor Green
    Write-Host "  Upload the certificate file: $certFile" -ForegroundColor Cyan
}

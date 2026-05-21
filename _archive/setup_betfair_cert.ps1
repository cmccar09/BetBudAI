#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup Betfair SSL certificate authentication
.DESCRIPTION
    Guides through downloading and configuring SSL certificates from Betfair
#>

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Betfair SSL Certificate Setup" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""

# Check if certificates already exist
$certFile = ".\betfair-client.crt"
$keyFile = ".\betfair-client.key"

if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
    Write-Host "✓ Certificate files found:" -ForegroundColor Green
    Write-Host "  - $certFile"
    Write-Host "  - $keyFile"
    Write-Host ""
    
    # Test the certificates
    Write-Host "Testing certificate authentication..." -ForegroundColor Yellow
    & .\.venv\Scripts\python.exe refresh_token_cert.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "="*60 -ForegroundColor Green
        Write-Host "✓ Certificate authentication working!" -ForegroundColor Green
        Write-Host "="*60 -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Update AWS Secrets Manager with certificate data:"
        Write-Host "   .\update_aws_secrets_with_cert.ps1"
        Write-Host ""
        Write-Host "2. Test Betfair API:"
        Write-Host "   .\.venv\Scripts\python.exe betfair_delayed_snapshots.py --out test.json --max_races 5"
    } else {
        Write-Host ""
        Write-Host "❌ Certificate authentication failed" -ForegroundColor Red
        Write-Host "Check the error above and verify certificates are valid" -ForegroundColor Yellow
    }
    
    exit $LASTEXITCODE
}

Write-Host "Certificate files not found. You need to:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Step 1: Get SSL Certificate from Betfair" -ForegroundColor Cyan
Write-Host "  1. Go to: https://developer.betfair.com/" -ForegroundColor White
Write-Host "  2. Login with your Betfair account" -ForegroundColor White
Write-Host "  3. Navigate to: My Account → API Certificates" -ForegroundColor White
Write-Host "  4. Click 'Create a new certificate'" -ForegroundColor White
Write-Host "  5. Download both files:" -ForegroundColor White
Write-Host "     - client-2048.crt" -ForegroundColor White
Write-Host "     - client-2048.key" -ForegroundColor White
Write-Host ""

Write-Host "Step 2: Save Certificate Files" -ForegroundColor Cyan
Write-Host "  Place downloaded files in this directory as:" -ForegroundColor White
Write-Host "     $certFile" -ForegroundColor White
Write-Host "     $keyFile" -ForegroundColor White
Write-Host ""

$answer = Read-Host "Have you downloaded the certificate files? (y/n)"

if ($answer -eq 'y' -or $answer -eq 'Y') {
    Write-Host ""
    Write-Host "Looking for downloaded certificate files..." -ForegroundColor Yellow
    
    # Check common download locations
    $downloadsPath = [Environment]::GetFolderPath("UserProfile") + "\Downloads"
    $certDownload = Get-ChildItem -Path $downloadsPath -Filter "client-2048.crt" -ErrorAction SilentlyContinue | Select-Object -First 1
    $keyDownload = Get-ChildItem -Path $downloadsPath -Filter "client-2048.key" -ErrorAction SilentlyContinue | Select-Object -First 1
    
    if ($certDownload -and $keyDownload) {
        Write-Host "✓ Found certificate files in Downloads" -ForegroundColor Green
        Write-Host ""
        
        $move = Read-Host "Copy files to project directory? (y/n)"
        if ($move -eq 'y' -or $move -eq 'Y') {
            Copy-Item $certDownload.FullName -Destination $certFile
            Copy-Item $keyDownload.FullName -Destination $keyFile
            Write-Host "✓ Certificate files copied successfully" -ForegroundColor Green
            
            # Update betfair-creds.json
            Write-Host ""
            Write-Host "Updating betfair-creds.json..." -ForegroundColor Yellow
            $creds = Get-Content ".\betfair-creds.json" | ConvertFrom-Json
            $creds | Add-Member -NotePropertyName "cert_file" -NotePropertyValue $certFile -Force
            $creds | Add-Member -NotePropertyName "key_file" -NotePropertyValue $keyFile -Force
            $creds | ConvertTo-Json -Depth 10 | Set-Content ".\betfair-creds.json"
            Write-Host "✓ Updated betfair-creds.json" -ForegroundColor Green
            
            # Test authentication
            Write-Host ""
            Write-Host "Testing certificate authentication..." -ForegroundColor Yellow
            & .\.venv\Scripts\python.exe refresh_token_cert.py
            
        } else {
            Write-Host ""
            Write-Host "Please manually copy files:" -ForegroundColor Yellow
            Write-Host "  Copy-Item '$($certDownload.FullName)' -Destination '$certFile'"
            Write-Host "  Copy-Item '$($keyDownload.FullName)' -Destination '$keyFile'"
        }
    } else {
        Write-Host "❌ Certificate files not found in Downloads" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please:" -ForegroundColor Yellow
        Write-Host "1. Download certificates from Betfair developer portal"
        Write-Host "2. Save as $certFile and $keyFile in this directory"
        Write-Host "3. Run this script again"
    }
} else {
    Write-Host ""
    Write-Host "Please download certificates from Betfair, then run this script again" -ForegroundColor Yellow
    Write-Host "See BETFAIR_CERT_SETUP.md for detailed instructions" -ForegroundColor Cyan
}

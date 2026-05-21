# Betfair Certificate Generation Guide

After changing your Betfair password, you need to generate a new SSL certificate.

## Steps:

### 1. Generate New Certificate

Run this PowerShell command to generate a new certificate:

```powershell
# Generate new certificate request
openssl req -x509 -newkey rsa:2048 -keyout betfair-client.key -out betfair-client.crt -days 365 -nodes -subj "/CN=cmccar02"
```

If you don't have OpenSSL installed:
1. Download from: https://slproweb.com/products/Win32OpenSSL.html
2. Install "Win64 OpenSSL v3.x.x Light"
3. Add to PATH: `C:\Program Files\OpenSSL-Win64\bin`

### 2. Upload Certificate to Betfair

1. Go to: https://myaccount.betfair.com/accountdetails/mysecurity?showAPI=1
2. Click "Edit" next to API Certificates
3. Upload the `betfair-client.crt` file
4. Save changes

### 3. Upload to AWS Secrets Manager

Run this command (from the directory containing the certificate files):

```powershell
# Read certificate files
$cert = Get-Content "betfair-client.crt" -Raw
$key = Get-Content "betfair-client.key" -Raw

# Create secret JSON
$secret = @{
    certificate = $cert
    private_key = $key
} | ConvertTo-Json

# Update Secrets Manager
aws secretsmanager update-secret `
    --secret-id betfair-ssl-certificate `
    --region eu-west-1 `
    --secret-string $secret
```

### 4. Test Results Fetcher

```powershell
aws lambda invoke `
    --function-name BettingResultsFetcher `
    --region eu-west-1 `
    test-output.json

Get-Content test-output.json | ConvertFrom-Json
```

## Alternative: Use Password-Only Authentication

If certificate setup is problematic, I can update the code to use password-only auth (if Betfair allows it for your account tier).

# Betfair Certificate Authentication Setup

## Step 1: Generate SSL Certificate

1. **Log into Betfair Developer Portal**
   - Go to: https://developer.betfair.com/
   - Navigate to "My Account" → "API Certificates"

2. **Create New Certificate**
   - Click "Create a new certificate"
   - Download both files:
     - `client-2048.crt` (Certificate)
     - `client-2048.key` (Private Key)

3. **Save to Project Directory**
   ```powershell
   # Move downloaded files to project root
   Move-Item ~/Downloads/client-2048.crt ./betfair-client.crt
   Move-Item ~/Downloads/client-2048.key ./betfair-client.key
   ```

## Step 2: Convert to PEM Format (Optional)

If needed, convert to PEM:
```powershell
# Install OpenSSL if not already installed
winget install OpenSSL.OpenSSL

# Convert (usually not needed - .crt/.key work directly)
openssl x509 -in betfair-client.crt -out betfair-client.pem
```

## Step 3: Update Credentials File

Add certificate paths to `betfair-creds.json`:
```json
{
  "username": "your_username",
  "password": "your_password",
  "app_key": "your_app_key",
  "session_token": "current_token",
  "cert_file": "./betfair-client.crt",
  "key_file": "./betfair-client.key"
}
```

## Step 4: Test Authentication

```powershell
# Refresh session token with certificates
.\.venv\Scripts\python.exe refresh_token_cert.py
```

## Step 5: Update AWS Secrets Manager

Once working locally, update AWS:
```powershell
aws secretsmanager update-secret `
  --secret-id betfair-credentials `
  --region eu-west-1 `
  --secret-string (Get-Content betfair-creds.json | Out-String)
```

## Troubleshooting

**"CERT_AUTH_REQUIRED" Error**
- Ensure certificates are downloaded from Betfair portal
- Check certificate files exist and are readable
- Verify certificate hasn't expired

**"SSL Error"**
- Check certificate format (.crt and .key are correct)
- Ensure files aren't corrupted during download

**"Invalid Certificate"**
- Generate new certificate from Betfair portal
- Make sure you're using production certificates (not test/demo)

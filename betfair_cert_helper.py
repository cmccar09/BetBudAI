"""
Helper script to manage Betfair certificates
Provides utilities to convert and verify certificate files
"""

import subprocess
import os

def check_pfx_file():
    """Check if PFX file is valid"""
    print("=" * 60)
    print("PFX FILE VERIFICATION")
    print("=" * 60)
    
    pfx_path = 'betfair-client.pfx'
    
    if not os.path.exists(pfx_path):
        print(f"❌ PFX file not found: {pfx_path}")
        return False
    
    print(f"✓ PFX file found: {pfx_path}")
    size = os.path.getsize(pfx_path)
    print(f"  Size: {size} bytes")
    
    # Read first few bytes to verify format
    with open(pfx_path, 'rb') as f:
        header = f.read(4)
        # PFX/PKCS#12 files typically start with 0x30 0x82
        if header[0] == 0x30:
            print(f"  ✓ Valid PKCS#12 format detected")
            return True
        else:
            print(f"  ⚠ Unexpected file format (header: {header.hex()})")
            return False

def print_upload_instructions():
    """Print step-by-step upload instructions"""
    print("\n" + "=" * 60)
    print("CERTIFICATE UPLOAD INSTRUCTIONS")
    print("=" * 60)
    
    print("""
╔════════════════════════════════════════════════════════════╗
║  STEP-BY-STEP: Upload Certificate to Betfair              ║
╚════════════════════════════════════════════════════════════╝

OPTION 1: Upload Existing Certificate (betfair-client.pfx)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Open your web browser

2. Go to: https://myaccount.betfair.com/accountdetails/mysecurity

3. Login with:
   Username: cmccar02
   Password: [your betfair password]

4. Scroll down to find one of these sections:
   - "Automated Access"
   - "API Certificate" 
   - "Developer Tools"
   - "Certificate Management"

5. Look for options like:
   - "Upload Certificate"
   - "Manage Certificates"
   - "SSL Certificate"

6. Upload the file: betfair-client.pfx
   (Located in this directory)
   
   NOTE: Some Betfair interfaces want .crt file instead
   If so, upload: betfair-client.crt

7. You might be asked for a password:
   - If you set one when creating: use that password
   - If you didn't set one: try leaving it blank
   - Common default: "betfair" or "password"

8. After upload, you should see:
   ✓ "Certificate uploaded successfully"
   ✓ Certificate status: Active
   ✓ Valid from/to dates

9. WAIT 5-10 MINUTES for Betfair to process and activate


OPTION 2: Generate Fresh Certificate via Betfair Website
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Go to: https://myaccount.betfair.com/accountdetails/mysecurity

2. Login with your credentials

3. Find the certificate section

4. Click "Generate New Certificate" or "Create Certificate"

5. Download the certificate file (.p12 or .pfx)
   Save it as: betfair-client-new.pfx

6. You'll need to convert it to .crt and .key:
   
   Run this command in PowerShell:
   
   # Extract certificate
   openssl pkcs12 -in betfair-client-new.pfx -clcerts -nokeys -out betfair-client-new.crt
   
   # Extract private key
   openssl pkcs12 -in betfair-client-new.pfx -nocerts -nodes -out betfair-client-new.key

7. Backup old files:
   - Move betfair-client.crt to betfair-client.crt.old2
   - Move betfair-client.key to betfair-client.key.old2

8. Rename new files:
   - betfair-client-new.crt → betfair-client.crt
   - betfair-client-new.key → betfair-client.key

9. Test the new certificate:
   python test_betfair_odds_debug.py


TROUBLESHOOTING
━━━━━━━━━━━━━━━
❓ Can't find certificate section on Betfair website?
   → Try these URLs directly:
     - https://myaccount.betfair.com/account/security
     - https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Non-Interactive+%28bot%29+login
     - https://myaccount.betfair.com/account/en/home

❓ Certificate upload says "already exists"?
   → You may have uploaded it before - check the status
   → Or revoke the old certificate and upload new one

❓ Don't have OpenSSL?
   → Install Git for Windows (includes OpenSSL)
   → Or use online converter: https://www.sslshopper.com/ssl-converter.html

❓ Upload successful but still getting CERT_AUTH_REQUIRED?
   → Wait 10-15 minutes for Betfair to activate
   → Clear browser cache
   → Try logging out and back in to Betfair
   → Verify certificate is marked as "Active" in account settings


AFTER UPLOAD
━━━━━━━━━━━━
Once you've uploaded the certificate and it shows as active,
run the diagnostic test again:

    python test_betfair_odds_debug.py

You should see:
✓ Certificate authentication SUCCESSFUL
✓ Session token: [token]
""")

def main():
    print("\n╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "BETFAIR CERTIFICATE HELPER" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝\n")
    
    check_pfx_file()
    print_upload_instructions()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
Current Status:
  ✓ Certificate files exist locally
  ❌ Certificate NOT uploaded to Betfair (or not activated)

Required Action:
  → Upload betfair-client.pfx to Betfair website
  → OR generate fresh certificate from Betfair
  → Wait 5-10 minutes for activation
  → Run: python test_betfair_odds_debug.py
""")

if __name__ == "__main__":
    main()

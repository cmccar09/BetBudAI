"""
Check Betfair Certificate Status
Helps diagnose certificate authentication issues
"""

import os
import json

def check_cert_files():
    """Check if certificate files exist and are readable"""
    print("=" * 60)
    print("CERTIFICATE FILE CHECK")
    print("=" * 60)
    
    cert_path = 'betfair-client.crt'
    key_path = 'betfair-client.key'
    pfx_path = 'betfair-client.pfx'
    
    files_status = {}
    
    for path in [cert_path, key_path, pfx_path]:
        if os.path.exists(path):
            size = os.path.getsize(path)
            modified = os.path.getmtime(path)
            from datetime import datetime
            mod_date = datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"✓ {path}")
            print(f"  Size: {size} bytes")
            print(f"  Modified: {mod_date}")
            
            # Try to read first few bytes
            try:
                with open(path, 'rb') as f:
                    first_bytes = f.read(50)
                    if path.endswith('.crt'):
                        if b'BEGIN CERTIFICATE' in first_bytes or b'BEGIN CERT' in first_bytes:
                            print(f"  Format: PEM (text format) ✓")
                        else:
                            print(f"  Format: Unknown (might be DER/binary)")
                    elif path.endswith('.key'):
                        if b'BEGIN' in first_bytes:
                            print(f"  Format: PEM (text format) ✓")
                        else:
                            print(f"  Format: Unknown or encrypted")
                    elif path.endswith('.pfx'):
                        print(f"  Format: PFX/PKCS12 (binary) ✓")
                
                files_status[path] = 'exists'
            except Exception as e:
                print(f"  ❌ Error reading: {e}")
                files_status[path] = 'error'
        else:
            print(f"❌ {path} - NOT FOUND")
            files_status[path] = 'missing'
        print()
    
    return files_status

def check_credentials():
    """Check if credentials file exists"""
    print("=" * 60)
    print("CREDENTIALS CHECK")
    print("=" * 60)
    
    creds_path = 'betfair-creds.json'
    
    if os.path.exists(creds_path):
        try:
            with open(creds_path, 'r') as f:
                creds = json.load(f)
                
            print(f"✓ Credentials file found")
            print(f"  Username: {creds.get('username', 'NOT SET')}")
            print(f"  App Key: {'SET' if creds.get('app_key') else 'NOT SET'}")
            print(f"  Password: {'SET' if creds.get('password') else 'NOT SET'}")
            return True
        except Exception as e:
            print(f"❌ Error reading credentials: {e}")
            return False
    else:
        print(f"❌ Credentials file not found: {creds_path}")
        return False

def print_instructions():
    """Print instructions for fixing certificate issues"""
    print("\n" + "=" * 60)
    print("DIAGNOSIS & NEXT STEPS")
    print("=" * 60)
    
    print("""
The error "CERT_AUTH_REQUIRED" means:

❌ Your certificate is NOT registered with Betfair yet
   (or is not matching what Betfair has on file)

TO FIX THIS, YOU NEED TO:

1. Upload Certificate to Betfair Website
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   a) Go to: https://myaccount.betfair.com/accountdetails/mysecurity
   
   b) Login with your Betfair username and password
   
   c) Look for "Automated Access" or "API Certificate" section
   
   d) Click "Generate New Certificate" OR "Upload Certificate"
   
   e) If GENERATING new:
      - Download the certificate file (.p12 or .pfx)
      - Extract it to .crt and .key files
   
   f) If UPLOADING existing:
      - Use the betfair-client.pfx file (or .crt file)
      - Upload it to Betfair
   
   g) IMPORTANT: You may need to wait 5-10 minutes after uploading
      for Betfair to activate the certificate

2. Alternative: Generate NEW Certificate via Betfair
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   If the existing certificate isn't working, you can generate
   a fresh one directly from Betfair:
   
   a) Go to your Betfair account security settings
   b) Generate a NEW SSL certificate
   c) Download the .p12/.pfx file
   d) Convert it to .crt and .key files
   e) Replace the existing files

3. Check Certificate Upload Status
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   After uploading, verify in Betfair account settings that
   you see:
   - "Certificate Status: Active" or similar
   - The certificate fingerprint/serial number

COMMON ISSUES:
━━━━━━━━━━━━━━
✗ Certificate was generated but never uploaded to Betfair
✗ Certificate was uploaded to wrong Betfair account  
✗ Certificate hasn't been activated yet (wait 10 mins)
✗ Using old certificate that has been replaced on Betfair
✗ Certificate files are corrupted or in wrong format

NEXT COMMAND TO RUN:
━━━━━━━━━━━━━━━━━━━
After uploading your certificate to Betfair website and waiting
5-10 minutes, run the test again:

    python test_betfair_odds_debug.py
""")

def main():
    print("\n╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "BETFAIR CERTIFICATE STATUS CHECK" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝\n")
    
    files_status = check_cert_files()
    print()
    creds_ok = check_credentials()
    
    print_instructions()

if __name__ == "__main__":
    main()

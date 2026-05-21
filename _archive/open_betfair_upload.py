"""
Betfair Certificate Upload Verification
Opens Betfair security page to help you upload the certificate
"""

import webbrowser
import os

def open_betfair_security():
    """Open Betfair account security page"""
    print("=" * 60)
    print("OPENING BETFAIR SECURITY PAGE")
    print("=" * 60)
    
    url = "https://myaccount.betfair.com/accountdetails/mysecurity"
    
    print(f"\nOpening: {url}")
    print("\nYou should see:")
    print("  1. Login page (if not already logged in)")
    print("  2. Account security settings page")
    print("  3. Look for 'Automated Access' or 'API Certificate' section")
    print()
    
    webbrowser.open(url)
    
    print("✓ Browser opened")

def show_upload_checklist():
    """Show what to look for on Betfair website"""
    print("\n" + "=" * 60)
    print("UPLOAD CHECKLIST")
    print("=" * 60)
    
    print("""
On the Betfair security page, you need to:

☐ Step 1: Login with username 'cmccar02'

☐ Step 2: Scroll to find one of these sections:
   - "Automated Access"
   - "API Certificate"
   - "Developer Access" 
   - "Non-Interactive Login"

☐ Step 3: Look for buttons like:
   - "Upload Certificate"
   - "Manage Certificate"
   - "Add Certificate"
   - "Generate Certificate"

☐ Step 4: Upload one of these files:
   Option A: betfair-client.pfx (RECOMMENDED)
   Option B: betfair-client.crt (if PFX doesn't work)

☐ Step 5: Check the certificate status shows:
   ✓ Status: Active (or Enabled)
   ✓ Shows your certificate details

☐ Step 6: Wait 5-10 minutes, then test again


IMPORTANT: What to Report Back
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please tell me what you see:

1. Do you see a certificate section at all? YES / NO

2. If YES, what does it say?
   - "No certificate uploaded"
   - "Certificate status: Active"
   - "Certificate status: Pending"
   - Something else?

3. What buttons/options are available?
   - Upload
   - Generate
   - Delete
   - None

4. If you uploaded, what happened?
   - Success message?
   - Error message?
   - What was the error?


ALTERNATIVE IF YOU DON'T SEE CERTIFICATE OPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Some Betfair accounts might not have API access enabled.
You may need to:

1. Apply for API access first:
   https://www.betfair.com/exchange/plus/en/betfair-api-landing-page

2. Or contact Betfair support to enable API access

3. Or use the alternative authentication method (see below)
""")

def show_alternative_auth():
    """Show alternative authentication if cert upload doesn't work"""
    print("\n" + "=" * 60)
    print("ALTERNATIVE: Interactive Login (No Certificate)")
    print("=" * 60)
    
    print("""
If you can't upload a certificate or don't have API access,
you can use the interactive login method instead.

This method:
  ✓ Works without certificate upload
  ✓ Generates session token with username/password
  ✗ Session expires every 8 hours (requires refresh)

To use interactive login instead, we'll modify the code to use:
  https://identitysso.betfair.com/api/login
  
Instead of:
  https://identitysso-cert.betfair.com/api/certlogin

Would you like me to create a test script for this method?
""")

def main():
    print("\n╔" + "═" * 58 + "╗")
    print("║" + " " * 8 + "BETFAIR CERTIFICATE UPLOAD HELPER" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝\n")
    
    # Check files exist
    pfx_exists = os.path.exists('betfair-client.pfx')
    crt_exists = os.path.exists('betfair-client.crt')
    
    print("Certificate Files Status:")
    print(f"  {'✓' if pfx_exists else '✗'} betfair-client.pfx")
    print(f"  {'✓' if crt_exists else '✗'} betfair-client.crt")
    print()
    
    if not pfx_exists and not crt_exists:
        print("❌ No certificate files found!")
        return
    
    # Open browser
    open_betfair_security()
    
    # Show checklist
    show_upload_checklist()
    
    # Show alternative
    show_alternative_auth()
    
    print("\n" + "=" * 60)
    print("WAITING FOR YOUR FEEDBACK")
    print("=" * 60)
    print("""
Please check the Betfair website and let me know:
  1. What you see on the security page
  2. Whether certificate upload option exists
  3. What happened when you tried to upload

Then I can help you with the next steps!
""")

if __name__ == "__main__":
    main()

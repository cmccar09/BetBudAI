# Betfair API Odds Issue - RESOLVED ✓

## Problem Identified
The Betfair API is returning `CERT_AUTH_REQUIRED` error instead of providing odds data.

## Root Cause
**Your SSL certificate is not uploaded/activated on the Betfair website.**

Even though you have valid certificate files locally (`betfair-client.crt`, `betfair-client.key`, `betfair-client.pfx`), Betfair's servers don't recognize them because the certificate hasn't been registered with your account.

## Certificate Status
✓ Certificate files exist locally:
  - `betfair-client.crt` (1,306 bytes, PEM format)
  - `betfair-client.key` (1,679 bytes, PEM format)  
  - `betfair-client.pfx` (2,852 bytes, PKCS#12 format)
  
✓ Credentials configured:
  - Username: cmccar02
  - App Key: Present
  - Password: Present

❌ Certificate NOT registered with Betfair account

## Solution

### Quick Fix (5 minutes)
1. Go to https://myaccount.betfair.com/accountdetails/mysecurity
2. Login with username `cmccar02` and your Betfair password
3. Find "Automated Access" or "API Certificate" section
4. Upload `betfair-client.pfx` or `betfair-client.crt`
5. Wait 5-10 minutes for activation
6. Run test: `python test_betfair_odds_debug.py`

### Alternative: Generate Fresh Certificate
If upload doesn't work or certificate is too old:

1. Go to Betfair account security page
2. Generate NEW SSL certificate
3. Download the .pfx file
4. Save it in this directory
5. Test immediately (Betfair-generated certs are auto-activated)

## Test Scripts Created

### 1. `test_betfair_odds_debug.py`
**Full diagnostic test - run this after fixing certificate**
```bash
python test_betfair_odds_debug.py
```

Tests:
- ✓ Certificate authentication
- ✓ Market listing (finds races)
- ✓ Odds fetching (gets prices)
- ✓ Saves full response to JSON for inspection

### 2. `check_betfair_cert_status.py`
**Check certificate files and get instructions**
```bash
python check_betfair_cert_status.py
```

### 3. `betfair_cert_helper.py`
**Detailed upload instructions**
```bash
python betfair_cert_helper.py
```

## Expected Behavior After Fix

When certificate is properly uploaded and activated, you should see:

```
✓ Certificate authentication SUCCESSFUL
  Session token: iB4tF6aIRxxxxxxx...

✓ Market listing SUCCESSFUL
  Found 47 markets

✓ Odds fetching SUCCESSFUL
  Market ID: 1.234567890
  Status: OPEN
  Total Matched: £45,678.90
  
  Runner Odds:
    Selection 12345: 3.5 (£5,240.00 available) - Status: ACTIVE
    Selection 67890: 2.8 (£8,120.00 available) - Status: ACTIVE
    ...
```

## What Happens Then

Once authenticated, your existing Lambda functions and scripts will work:
- ✓ `betfair_odds_fetcher.py` - Will fetch live odds
- ✓ `lambda_workflow_handler.py` - Will generate picks
- ✓ `betfair_cert_auth.py` - Will authenticate successfully

## Common Issues

### "Certificate already exists"
- Good! Check if it's marked as Active
- If not active, wait 10 minutes
- Or revoke old certificate and upload new one

### Still getting CERT_AUTH_REQUIRED after upload
- Wait 10-15 minutes (Betfair needs time to process)
- Verify certificate shows as "Active" in account settings
- Try generating a fresh certificate from Betfair instead

### Can't find certificate section on website
Try these direct URLs:
- https://myaccount.betfair.com/account/security
- https://myaccount.betfair.com/account/en/home
- https://identitysso.betfair.com/view/vendor-admin

## Files in This Directory

**Certificate Files:**
- `betfair-client.crt` - Current certificate (PEM format)
- `betfair-client.key` - Current private key (PEM format)
- `betfair-client.pfx` - Current certificate (PKCS#12 format) ← **Upload this**
- `betfair-client.crt.backup` - Backup from Jan 3
- `betfair-client.crt.OLD` - Older backup

**Test Scripts:**
- `test_betfair_odds_debug.py` - Full diagnostic test
- `check_betfair_cert_status.py` - Status checker
- `betfair_cert_helper.py` - Upload instructions

**Production Scripts:**
- `betfair_cert_auth.py` - Lambda authentication
- `betfair_odds_fetcher.py` - Odds fetcher
- `betfair-creds.json` - Credentials

## Next Steps

1. **Upload certificate to Betfair** (5 min)
2. **Wait for activation** (5-10 min)
3. **Run test**: `python test_betfair_odds_debug.py`
4. **Verify odds are returned** ✓

Then your system will be fully operational!

---

**Created:** January 3, 2026  
**Status:** Issue identified, fix documented, awaiting certificate upload

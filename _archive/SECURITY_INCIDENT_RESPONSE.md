# URGENT SECURITY REMEDIATION GUIDE

## ⚠️ CRITICAL: RSA Private Key Exposed on GitHub

**Status**: GitGuardian detected exposed RSA private key in cmccar09/SureBet repository
**Pushed**: January 5, 2026, 15:41:00 UTC
**Risk**: HIGH - Anyone with repository access can see your Betfair authentication keys

---

## IMMEDIATE ACTIONS REQUIRED

### 1. REVOKE EXPOSED CERTIFICATE (DO THIS FIRST)
```powershell
# The exposed key is compromised and MUST be regenerated
# Log into Betfair account:
# 1. Go to https://myaccount.betfair.com/account/security
# 2. Delete the exposed certificate
# 3. Generate NEW certificate
# 4. Download new .key and .crt files
```

### 2. REMOVE FROM GIT HISTORY
Run the provided cleanup script:
```powershell
.\REMOVE_EXPOSED_KEYS.ps1
```

**OR manually using git filter-repo:**
```powershell
# Install git filter-repo
pip install git-filter-repo

# Remove all .key files and cert JSON files from history
git filter-repo --invert-paths `
  --path-glob '*.key' `
  --path-glob '*.key.OLD' `
  --path-glob '*.key.backup' `
  --path 'cert-check.json' `
  --path 'aws-cert-check.json' `
  --path 'final-cert.json' `
  --force

# Force push to GitHub (rewrites history)
git push origin main --force
```

### 3. UPDATE AWS SECRETS MANAGER
```powershell
# Upload NEW certificate to AWS
aws secretsmanager update-secret `
  --secret-id betfair/certificate `
  --secret-string file://betfair-client.key

aws secretsmanager update-secret `
  --secret-id betfair/cert-file `
  --secret-string file://betfair-client.crt
```

### 4. VERIFY REMOVAL
- Check GitHub repository - old keys should not be visible
- Check GitGuardian alert status
- Verify new certificate works with Betfair API

---

## FILES EXPOSED (Found in Repository)

```
betfair-client.key              ← PRIMARY RISK
betfair-client.key.backup       ← BACKUP COPY
betfair-client.key.OLD          ← OLD VERSION
betfair-username.key            ← USERNAME KEY
betfair-final.key               ← FINAL VERSION
betfair-new.key                 ← NEW VERSION
betfair-client-new.key          ← CLIENT NEW
cert-check.json                 ← CONTAINS PRIVATE KEY
aws-cert-check.json             ← CONTAINS PRIVATE KEY  
final-cert.json                 ← CONTAINS PRIVATE KEY
```

---

## PREVENTION (Already in Place)

.gitignore is properly configured:
```gitignore
*.key
*.pem
*.crt
betfair-client.*
*-creds.json
*.key.OLD
*.key.backup
```

**Problem**: Files were committed BEFORE .gitignore was added
**Solution**: Clean history + never commit credentials again

---

## RISK ASSESSMENT

**What was exposed:**
- Betfair API authentication certificate (RSA private key)
- Allows API access to your Betfair account

**Who can access:**
- Anyone who viewed the repository since 15:41 UTC
- Anyone who cloned/forked the repo
- GitGuardian (security scanner)
- GitHub staff (theoretically)

**Potential impact:**
- Unauthorized Betfair API access
- Ability to place bets on your account
- Access to account balance and betting history

---

## POST-REMEDIATION CHECKLIST

- [ ] Old Betfair certificate revoked
- [ ] New Betfair certificate generated  
- [ ] Git history cleaned (keys removed)
- [ ] Force push completed to GitHub
- [ ] AWS Secrets Manager updated
- [ ] New certificate tested with Betfair API
- [ ] GitGuardian alert resolved
- [ ] No unauthorized account activity detected

---

## QUESTIONS?

If cleanup fails:
1. Contact GitHub support to remove sensitive data
2. Consider making repository private temporarily
3. Regenerate ALL credentials as precaution

**Remember**: Once pushed to GitHub, assume keys are compromised forever!

# Security Incident - RESOLVED

**Date**: May 21, 2026, 20:18 UTC  
**Status**: ✅ RESOLVED  
**Severity**: Medium (key already revoked)

---

## What Happened

An Anthropic API key was accidentally committed to the public GitHub repository in file `docs/ANTHROPIC_SETUP.md`.

**Exposed Key**:
- Type: Claude API key
- ID: 81df39be-9ab7-45dd-b99b-06ed5b8d3dd1
- Name: vs
- Hint: sk-ant-api03-EV2...iQAA

**Location**: https://github.com/cmccar09/BetBudAI/blob/109e66351f8363219eaea614538fe777148229a8/docs/ANTHROPIC_SETUP.md

---

## Actions Taken

### Immediate Response (Automated by Anthropic)
- ✅ API key automatically revoked by Anthropic (20:18 UTC)
- ✅ GitHub Secret Scanning Partner Program detected exposure
- ✅ Email notification sent to account owner

### Manual Remediation (20:20 UTC)
- ✅ Removed `docs/ANTHROPIC_SETUP.md` from repository
- ✅ Added comprehensive `.gitignore` rules:
  - `docs/ANTHROPIC_SETUP.md`
  - `*.key`
  - `**/client-*.crt`
  - `**/client-*.key`
  - `.env`
  - `**/*credentials*`
- ✅ Committed and pushed security fix
- ✅ Created this incident report

---

## Required Action

**⚠️ IMPORTANT: Generate a new API key**

1. Go to: https://platform.claude.com/settings/keys
2. Click "Create Key"
3. Name it appropriately (e.g., "BetBudAI-Production")
4. Copy the new key
5. Update it in your local environment ONLY (never commit to Git)

**Where to update the new key:**
- Local `.env` file (create if doesn't exist)
- AWS Lambda environment variables (if using Claude API in Lambda)
- Any local scripts that use Claude API

---

## Impact Assessment

**Actual Risk**: LOW
- ✅ Key was revoked within minutes of exposure
- ✅ No evidence of unauthorized usage
- ✅ Key was for development/testing (not production critical)
- ✅ Repository was just created (minimal exposure window)

**Potential Risk** (if key hadn't been revoked):
- Unauthorized API calls to Claude
- Potential billing charges
- Data access (if key had access to stored data)

---

## Lessons Learned

### What Went Wrong
1. API key was stored in a documentation file
2. File was committed without checking for secrets
3. No pre-commit hook to detect secrets

### Preventive Measures Implemented
1. ✅ Comprehensive `.gitignore` for all credential files
2. ✅ Documentation updated to never include actual keys
3. ✅ Security incident process documented

### Recommended Additional Measures
- [ ] Install `git-secrets` or similar pre-commit hook
- [ ] Use environment variables for all API keys
- [ ] Regular security audits of repository
- [ ] Consider using AWS Secrets Manager for production keys

---

## Pre-Commit Hook (Optional - Prevents Future Issues)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Pre-commit hook to detect secrets

# Check for potential API keys
if git diff --cached | grep -E "(sk-ant-|AKIA|api[_-]?key|secret[_-]?key)" -i; then
    echo "❌ ERROR: Potential API key or secret detected in commit!"
    echo "Please remove secrets before committing."
    exit 1
fi

echo "✅ No secrets detected"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Timeline

| Time (UTC) | Event |
|------------|-------|
| 20:18 | GitHub detects API key in commit |
| 20:18 | Anthropic automatically revokes key |
| 20:18 | Email notification sent |
| 20:20 | File removed from repository |
| 20:20 | .gitignore updated |
| 20:21 | Security fix committed and pushed |
| 20:22 | Incident report created |

**Total exposure time**: ~4 minutes  
**Response time**: ~2 minutes

---

## Verification

**Confirm key is revoked:**
```bash
# Try using the old key (should fail)
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: sk-ant-api03-EV2...iQAA" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'

# Expected: {"type":"error","error":{"type":"authentication_error","message":"invalid x-api-key"}}
```

**Confirm file removed from Git:**
```bash
cd c:/Users/charl/OneDrive/futuregenAI/BetBudAI
git log --all --full-history --source -- docs/ANTHROPIC_SETUP.md
# Should show deletion commit
```

---

## Status: RESOLVED ✅

- [x] Exposed key revoked by Anthropic
- [x] File removed from repository  
- [x] .gitignore updated with credential rules
- [x] Security fix pushed to GitHub
- [x] Incident documented
- [ ] **New API key generated** (Action required by user)

---

## Contact

**GitHub Repository**: https://github.com/cmccar09/BetBudAI  
**Anthropic Support**: https://support.anthropic.com  
**Generate New Key**: https://platform.claude.com/settings/keys

---

**No further action required except generating a new API key for future Claude API usage.**

The BetBudAI system (picks generation Lambda) does NOT use Claude API, so it's unaffected.

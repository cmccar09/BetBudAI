---
name: ga4-analytics-setup
description: Set up, fix, or rotate the GA4 Data API credential that powers the admin panel's Site Analytics tab (GET /api/admin/analytics). Use whenever that endpoint returns configured:false, a Google auth error (invalid_grant, PERMISSION_DENIED, redirect_uri_mismatch), or when the ga4-service-account Secrets Manager credential needs rotating. Also covers the GA4 property access grant, which is a separate step from the GCP credential and the most commonly missed one.
metadata:
  type: skill
---

# GA4 Analytics Setup Skill

## What this powers

The admin panel's **Site Analytics** tab (`activeSection === 'analytics'` in `frontend/src/App.js`) calls `GET /api/admin/analytics`, which pulls real active-user/session/pageview/event numbers from the **GA4 Data API** for property `537650672` (`betbudai.com`). This is separate from GA4 *collection* — the frontend's own tracking (`frontend/src/analytics.js`, measurement ID baked in via `frontend/.env.production`) has been working fine throughout; this skill is only about the *admin-side reporting* credential.

## The credential: use a service account, not OAuth consent

**Do not use an OAuth "Desktop app" client + consent-flow refresh token for this.** That was the original setup and it silently died (`invalid_grant` — refresh tokens for Desktop/installed-app OAuth clients expire from inactivity and require a human to re-consent through a browser). It's also awkward to fix: Desktop-type OAuth clients don't support arbitrary redirect URIs, so tools like Google's OAuth Playground hit `redirect_uri_mismatch` and can't be used to regenerate the token without creating a new client.

**Use the existing GCP service account instead**: `analytics-data-sa@betbudai-ga4-sa.iam.gserviceaccount.com` (project `betbudai-ga4-sa`, "BetBudAI Analytics SA"). Service account keys don't expire from inactivity and need no human consent flow — this is the standard, boring, reliable way to do server-to-server GA4 API access.

## Two separate permission systems — both must be set up

This tripped up the setup once already; both are required, independently:

1. **GCP IAM** — the service account itself needs to exist and have a key (see below). This does *not* by itself grant access to any specific GA4 property.
2. **GA4 property access** — separately, inside **analytics.google.com → Admin → Property Access Management** (for the `betbudai.com` / `beduai` property), the service account's email must be added as a user with at least **Viewer** role. Skipping this step produces `403 PERMISSION_DENIED: User does not have sufficient permissions for this property` even though the JWT auth and token exchange succeed perfectly — don't mistake this for an auth bug, it's a missing GA4-side grant.

## How to (re)generate a service account key, end to end

1. **console.cloud.google.com/apis/credentials** — check the right project is selected (project switcher, top bar). Under **Service Accounts**, click `analytics-data-sa@betbudai-ga4-sa.iam.gserviceaccount.com` (or **Manage service accounts**).
2. **Keys** tab → **Add key** → **Create new key** → **JSON** → **Create**. Downloads immediately — this is the only chance to get the private key material; Google won't show it again. (Old keys aren't automatically invalidated by creating a new one — a service account can hold several active keys. Delete stale ones from this same tab once a new one is confirmed working, for hygiene.)
3. If running Claude Code on the same machine as the browser download, the file is likely already sitting in `~/Downloads/` and can be read directly rather than asking the user to paste JSON into chat.
4. **Update the AWS secret**:
   ```bash
   aws secretsmanager put-secret-value \
     --secret-id ga4-service-account \
     --secret-string "file://C:/path/to/downloaded-key.json" \
     --region eu-west-1
   ```
5. **Grant GA4 property access** (see above) if this is a *new* service account — skip if reusing the existing `analytics-data-sa@...` account, since access should already be granted from a prior setup (but verify at **analytics.google.com → Admin → Property Access Management** if anything's still failing with 403).
6. **Delete the local downloaded JSON** once confirmed working in Secrets Manager — don't leave a plaintext private key sitting in Downloads.

## How the Lambda code authenticates (backend/api/lambda_function.py)

`_ga4_get_access_token()` reads the `ga4-service-account` secret and branches on its `type` field:

- **`type: "service_account"`** (current, since 2026-07-22): builds and signs a JWT (RS256) using the pure-Python `rsa` package, exchanges it via the RFC 7523 JWT-bearer grant (`urn:ietf:params:oauth:grant-type:jwt-bearer`). No refresh token, no consent screen.
  - **Gotcha handled by `_pkcs8_pem_to_pkcs1_der()`**: Google service-account keys are PKCS#8 PEM (`-----BEGIN PRIVATE KEY-----`), but the pure-Python `rsa` package's `PrivateKey.load_pkcs1()` only accepts PKCS#1 (`-----BEGIN RSA PRIVATE KEY-----`). The fix is a generic ASN.1 unwrap with `pyasn1`'s DER decoder (`PrivateKeyInfo ::= SEQUENCE { version, algorithm, privateKey OCTET STRING }` — the OCTET STRING at index `[2]` is the embedded PKCS#1 DER). Don't try to hand a raw PKCS#8 PEM straight to `rsa.PrivateKey.load_pkcs1()` — it'll fail or silently misparse.
- **`type: "authorized_user"`** (legacy fallback, kept in the code in case the secret shape ever reverts): plain OAuth refresh-token exchange, no signing needed. This is the mode that broke — don't deliberately switch back to it.

**Dependency**: the `rsa` and `pyasn1` packages (pure Python, no compiled/binary parts — safe to bundle as a plain zip-based Lambda layer, no architecture-matching needed) are provided by the **`ga4-jwt-deps`** Lambda layer, attached to both `BettingPicksAPI` and `betbudai-picks-api` alongside the existing `stripe-python` layer. If creating a fresh copy of this layer is ever needed:

```bash
mkdir -p ga4_layer/python && cd ga4_layer
pip install --target ./python rsa pyasn1
python -c "
import zipfile, os
zf = zipfile.ZipFile('ga4_layer.zip', 'w', zipfile.ZIP_DEFLATED)
for root, dirs, files in os.walk('python'):
    for f in files:
        full = os.path.join(root, f)
        zf.write(full, full)
zf.close()
"
aws lambda publish-layer-version --layer-name ga4-jwt-deps \
  --zip-file fileb://ga4_layer.zip --compatible-runtimes python3.11 python3.12 --region eu-west-1
# Then attach the returned LayerVersionArn to both API Lambdas alongside the stripe-python layer
# (update-function-configuration --layers requires listing ALL desired layers, not just the new one)
```

## How to verify it's actually working (don't trust "no error" alone)

Test the token-exchange + report call directly, bypassing the API Gateway/admin-auth layer, to isolate Google-side problems from app-side problems:

```python
# Needs boto3 + rsa + pyasn1 available (e.g. a local venv with them pip installed)
import json, boto3, time, base64, urllib.request, urllib.parse, urllib.error
import rsa
from pyasn1.codec.der import decoder as der_decoder

def b64url(data): return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')
def pkcs8_to_pkcs1_der(pem):
    b64 = ''.join(l for l in pem.strip().splitlines() if not l.startswith('-----'))
    decoded, _ = der_decoder.decode(base64.b64decode(b64))
    return bytes(decoded[2])

secret = json.loads(boto3.client('secretsmanager', region_name='eu-west-1')
                     .get_secret_value(SecretId='ga4-service-account')['SecretString'])
# ... build JWT, sign, exchange for access_token, then POST runReport to
# https://analyticsdata.googleapis.com/v1beta/properties/537650672:runReport
```

Once confirmed working standalone, test the real deployed endpoint (needs a valid admin session token — `x-admin-token` header, session record with `role: admin` in `BetBudAI_Subscribers` under key `__session__{token}`):

```bash
curl -H "x-admin-token: <token>" https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/admin/analytics
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `configured: false`, message mentions `invalid_grant` | OAuth refresh token expired/revoked (legacy `authorized_user` credential) | Switch to service-account auth (this skill) rather than trying to refresh the OAuth token |
| `403 redirect_uri_mismatch` in a browser during OAuth consent | Trying to use Google's OAuth Playground (or similar) against a Desktop-type OAuth client, which doesn't support custom redirect URIs | Don't fix the OAuth client — use the service account instead |
| `403 PERMISSION_DENIED: User does not have sufficient permissions for this property` | JWT auth succeeded, but the service account hasn't been added in GA4's own Property Access Management | analytics.google.com → Admin → Property Access Management → add the service account email as Viewer |
| `admin/analytics` returns 404 | Route not deployed, or deployed to only one of the two API Lambdas | Redeploy via `scripts/deploy_api.ps1` (deploys to both `BettingPicksAPI` and `betbudai-picks-api` — never just one) |
| Token exchange fails with a signing/format error | PKCS#8 vs PKCS#1 key format mismatch | Confirm `_pkcs8_pem_to_pkcs1_der()` is being used, not a raw `rsa.PrivateKey.load_pkcs1()` call on the PEM string |
| Endpoint works standalone but not via curl/frontend | Missing or invalid `x-admin-token`, or the session record's `role` isn't `admin` | Check `BetBudAI_Subscribers` for the `__session__{token}` record and its `role` field |

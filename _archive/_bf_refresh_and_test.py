"""Refresh Betfair session via non-cert login, then test listMarketCatalogue."""
import json, boto3, requests

# Load creds with username/password
with open("betfair-creds.json") as f:
    creds = json.load(f)

print("Username:", creds.get("username", "?"))
print("App key (first 10):", creds.get("app_key", "")[:10])

# Re-login
r = requests.post(
    "https://identitysso.betfair.com/api/login",
    headers={
        "X-Application": creds["app_key"],
        "Content-Type":  "application/x-www-form-urlencoded",
    },
    data={"username": creds["username"], "password": creds["password"]},
    timeout=20,
)
print("Login status:", r.status_code)
print("Login response:", r.text[:500])

if r.status_code == 200:
    resp = r.json()
    status = resp.get("status") or resp.get("loginStatus")
    tok    = resp.get("sessionToken") or resp.get("token") or resp.get("session")
    print("Status:", status, "| Token prefix:", str(tok)[:20] if tok else "None")

    if tok:
        # Save to both files
        creds["session_token"] = tok
        with open("betfair-creds.json", "w") as f:
            json.dump(creds, f, indent=2)

        # Also save to Secrets Manager
        sm = boto3.client("secretsmanager", region_name="eu-west-1")
        sm_raw = sm.get_secret_value(SecretId="betfair-credentials")["SecretString"]
        sm_creds = json.loads(sm_raw)
        sm_creds["session_token"] = tok
        sm.put_secret_value(SecretId="betfair-credentials", SecretString=json.dumps(sm_creds))
        print("Saved fresh token to betfair-creds.json + Secrets Manager")

        # Quick API test
        headers = {
            "X-Application":    creds["app_key"],
            "X-Authentication": tok,
            "Content-Type":     "application/json",
        }
        r2 = requests.post(
            "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/",
            headers=headers,
            json={
                "filter": {
                    "eventTypeIds":    ["7"],
                    "marketCountries": ["GB"],
                    "marketTypeCodes": ["WIN"],
                    "textQuery":       "Cheltenham",
                    "marketStartTime": {
                        "from": "2026-03-11T00:00:00Z",
                        "to":   "2026-03-14T00:00:00Z",
                    },
                },
                "sort":             "FIRST_TO_START",
                "maxResults":       50,
                "marketProjection": ["MARKET_NAME", "EVENT", "MARKET_START_TIME", "RUNNER_DESCRIPTION"],
            },
            timeout=20,
        )
        print("Catalogue test status:", r2.status_code)
        if r2.status_code == 200:
            data = r2.json()
            print(f"  Found {len(data)} markets:")
            for m in data:
                start = m.get("marketStartTime", "")[:16].replace("T", " ")
                mname = m.get("marketName", "")
                mid   = m["marketId"]
                nrun  = len(m.get("runners", []))
                print(f"  {start}  {mname:<52}  {mid}  ({nrun} runners)")
        else:
            print("  Error:", r2.text[:400])
    else:
        print("No token in login response")

"""Diagnose Betfair API - try progressively more specific filters."""
import json, boto3, requests

# Use SM token
sm = boto3.client("secretsmanager", region_name="eu-west-1")
raw = sm.get_secret_value(SecretId="betfair-credentials")["SecretString"]
creds = json.loads(raw)

headers = {
    "X-Application":   creds["app_key"],
    "X-Authentication": creds["session_token"],
    "Content-Type":    "application/json",
}

BASE = "https://api.betfair.com/exchange/betting/rest/v1.0"


def post(endpoint, payload):
    r = requests.post(f"{BASE}/{endpoint}/", headers=headers, json=payload, timeout=20)
    return r.status_code, r.text[:500]


# Test 1: listMarketTypes (very lightweight)
s, t = post("listMarketTypes", {"filter": {"eventTypeIds": ["7"]}})
print(f"Test1 listMarketTypes: {s} | {t[:200]}")

# Test 2: Minimal listMarketCatalogue - just eventType + WIN, UK, next 24h
s, t = post("listMarketCatalogue", {
    "filter": {
        "eventTypeIds":    ["7"],
        "marketTypeCodes": ["WIN"],
        "marketCountries": ["GB"],
    },
    "maxResults": 5,
    "marketProjection": ["MARKET_NAME"],
})
print(f"\nTest2 catalogue minimal: {s} | {t[:300]}")

# Test 3: With specific marketStartTime only
s, t = post("listMarketCatalogue", {
    "filter": {
        "eventTypeIds":    ["7"],
        "marketTypeCodes": ["WIN"],
        "marketStartTime": {
            "from": "2026-03-11T00:00:00Z",
            "to":   "2026-03-12T00:00:00Z",
        },
    },
    "maxResults": 10,
    "marketProjection": ["MARKET_NAME", "MARKET_START_TIME"],
})
print(f"\nTest3 catalogue with date range only: {s} | {t[:500]}")

# Test 4: Betfair listEvents to confirm session is alive
s, t = post("listEvents", {
    "filter": {"eventTypeIds": ["7"], "textQuery": "Cheltenham"},
})
print(f"\nTest4 listEvents: {s} | {t[:300]}")

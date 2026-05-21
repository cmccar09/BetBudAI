"""Use Secrets Manager token to list Cheltenham WIN markets."""
import json, boto3, requests

sm = boto3.client("secretsmanager", region_name="eu-west-1")
raw = sm.get_secret_value(SecretId="betfair-credentials")["SecretString"]
creds = json.loads(raw)
print("SM token (first 20):", creds.get("session_token", "")[:20])

headers = {
    "X-Application":   creds["app_key"],
    "X-Authentication": creds["session_token"],
    "Content-Type":    "application/json",
}

r = requests.post(
    "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/",
    headers=headers,
    json={
        "filter": {
            "eventTypeIds":    ["7"],
            "marketCountries": ["GB", "IE"],
            "marketTypeCodes": ["WIN"],
            "textQuery":       "Cheltenham",
            "marketStartTime": {
                "from": "2026-03-10T00:00:00Z",
                "to":   "2026-03-14T00:00:00Z",
            },
        },
        "sort":             "FIRST_TO_START",
        "maxResults":       50,
        "marketProjection": ["MARKET_NAME", "EVENT", "MARKET_START_TIME"],
    },
    timeout=20,
)
print("Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    print(f"Found {len(data)} markets:")
    for m in data:
        start = m.get("marketStartTime", "")[:16].replace("T", " ")
        mname = m.get("marketName", "")
        mid   = m["marketId"]
        nrun  = len(m.get("runners", []))
        print(f"  {start}  {mname:<50}  {mid}  ({nrun} runners)")
else:
    print("Error:", r.text[:500])

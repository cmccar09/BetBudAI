import requests

# Test /api/picks/yesterday endpoint
url = "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/yesterday"
print(f"Testing: {url}\n")

r = requests.get(url)
print(f"Status: {r.status_code}")

data = r.json()
print(f"Keys: {list(data.keys())}")
print(f"Picks count: {len(data.get('picks', []))}")

if data.get('picks'):
    print(f"\nFirst 3 picks:")
    for pick in data['picks'][:3]:
        print(f"  {pick.get('horse'):25} {pick.get('comprehensive_score'):3.0f}/100  {pick.get('outcome', 'pending'):8}  {pick.get('course')}")

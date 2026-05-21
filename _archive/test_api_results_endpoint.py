import requests

# Test /api/results endpoint
url = "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/results"
print(f"Testing: {url}")

r = requests.get(url)
print(f"Status: {r.status_code}")

data = r.json()
print(f"Keys: {list(data.keys())}")
print(f"Results count: {len(data.get('results', []))}")

if data.get('results'):
    print(f"\nFirst result:")
    print(data['results'][0])

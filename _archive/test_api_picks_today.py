import requests

# Test /api/picks/today
url = "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/today"
print(f"Testing: {url}\n")

r = requests.get(url)
print(f"Status: {r.status_code}")

data = r.json()
print(f"Keys: {list(data.keys())}")
print(f"Total picks: {len(data.get('picks', []))}")

if data.get('picks'):
    print("\nPicks returned:")
    for pick in data['picks']:
        print(f"  {pick.get('horse'):30} {pick.get('course'):12} {pick.get('comprehensive_score'):3.0f}/100  outcome: {pick.get('outcome', 'pending')}")
    
    # Check for Ballymackie
    ballymackie = [p for p in data['picks'] if 'Ballymackie' in p.get('horse', '')]
    if ballymackie:
        print(f"\n✓ Ballymackie found in /api/picks/today")
    else:
        print(f"\n❌ Ballymackie NOT in /api/picks/today")

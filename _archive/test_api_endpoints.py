import requests
import json

# Test the API endpoints
API_BASE = "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com"

print("Testing API endpoints...\n")

# Test 1: Yesterday's picks
print("="*80)
print("TEST 1: /api/picks/yesterday")
print("="*80)
response = requests.get(f"{API_BASE}/api/picks/yesterday")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Success: {data.get('success')}")
    print(f"Count: {data.get('count')}")
    print(f"Date: {data.get('date')}")
    
    if data.get('picks'):
        print(f"\nFirst pick sample:")
        first_pick = data['picks'][0]
        print(json.dumps(first_pick, indent=2, default=str))
        
        print(f"\nField check:")
        print(f"  horse: {first_pick.get('horse', 'MISSING')}")
        print(f"  horse_name: {first_pick.get('horse_name', 'MISSING')}")
        print(f"  venue: {first_pick.get('venue', 'MISSING')}")
        print(f"  course: {first_pick.get('course', 'MISSING')}")
        print(f"  outcome: {first_pick.get('outcome', 'MISSING')}")
        print(f"  odds: {first_pick.get('odds', 'MISSING')}")
        print(f"  combined_confidence: {first_pick.get('combined_confidence', 'MISSING')}")
        
        # Count outcomes
        outcomes = {}
        for pick in data['picks']:
            outcome = pick.get('outcome', 'None/Missing')
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
        
        print(f"\nOutcome breakdown:")
        for outcome, count in sorted(outcomes.items()):
            print(f"  {outcome}: {count}")
    else:
        print("No picks found")
else:
    print(f"Error: {response.text}")

print("\n" + "="*80)
print("TEST 2: /api/results/today")
print("="*80)
response = requests.get(f"{API_BASE}/api/results/today")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Success: {data.get('success')}")
    print(f"Count: {data.get('count')}")
    print(f"Summary: {data.get('summary', {})}")
else:
    print(f"Error: {response.text}")

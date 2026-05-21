import requests
import json

url = "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/today"
response = requests.get(url)
data = response.json()

print(f"Total picks: {len(data['picks'])}\n")

for pick in data['picks'][:3]:
    print(f"{pick['horse']}:")
    print(f"  combined_confidence: {pick.get('combined_confidence', 'MISSING')}")
    print(f"  comprehensive_score: {pick.get('comprehensive_score', 'MISSING')}")
    print(f"  race_coverage_pct: {pick.get('race_coverage_pct', 'MISSING')}")
    print(f"  odds: {pick.get('odds', 'MISSING')}")
    print(f"  expected_roi: {pick.get('expected_roi', 'MISSING')}")
    print()

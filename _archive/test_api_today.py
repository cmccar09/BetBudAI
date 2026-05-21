import requests
import json

# Test get_today_picks endpoint
print("Testing GET /picks (today's future picks)...")
print("=" * 80)
response = requests.get('https://ypjwmhqmg3.execute-api.eu-west-1.amazonaws.com/prod/picks')
picks = response.json()

print(f"Status: {response.status_code}")
print(f"Total picks returned: {len(picks)}")
print()

if picks:
    print("Today's picks:")
    for i, pick in enumerate(picks, 1):
        show = "UI" if pick.get('show_in_ui') else ""
        rec = "REC" if pick.get('recommended_bet') else ""
        score = pick.get('comprehensive_score', 0)
        print(f"{i:2}. {show:3} {rec:3} {score:3.0f}/100  {pick.get('horse'):25} @ {pick.get('course'):20} {pick.get('race_time')}")

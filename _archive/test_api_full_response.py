import requests
import json

r = requests.get('https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/results')
data = r.json()

picks = data.get('picks', [])
print(f"Total picks: {len(picks)}\n")

for pick in picks:
    print(f"Horse: {pick.get('horse')}")
    print(f"  outcome: {pick.get('outcome')}")
    print(f"  stake: {pick.get('stake')}")
    print(f"  odds: {pick.get('odds')}")
    print(f"  show_in_ui: {pick.get('show_in_ui')}")
    print()

print(f"Summary: {json.dumps(data.get('summary'), indent=2)}")

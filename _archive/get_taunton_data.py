import json

# Read response_horses.json and filter for Taunton 13:40
with open('response_horses.json', 'r') as f:
    data = json.load(f)

taunton = [h for h in data if h.get('track') == 'Taunton' and h.get('race_time') == '13:40']

print(f'\nTaunton 13:40: {len(taunton)} horses\n')
print(f"{'Horse Name':<30} {'Score':<6} {'Odds':<7} {'Form':<15}")
print("-" * 70)

for h in sorted(taunton, key=lambda x: x.get('confidence_score', 0), reverse=True):
    score = h.get('confidence_score', 0)
    odds = h.get('odds', 0)
    form = h.get('form', '')[:15]
    print(f"{h['horse_name']:<30} {score:>3}/100 {odds:>6.1f}  {form:<15}")

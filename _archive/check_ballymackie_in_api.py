import requests
import json

url = "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/results"
r = requests.get(url)
data = r.json()

print(f"Total results: {len(data.get('results', []))}")

# Filter for ones with outcomes
completed = [x for x in data.get('results', []) if x.get('outcome')]
print(f"With outcomes: {len(completed)}")

print("\nCompleted races today:")
for result in completed:
    print(f"  {result.get('horse')[:30]:30} {result.get('course'):12} {result.get('race_time')[11:16]} {result.get('outcome'):8}")

# Check for Ballymackie specifically
ballymackie = [x for x in data.get('results', []) if 'Ballymackie' in x.get('horse', '')]
if ballymackie:
    print(f"\n✓ Ballymackie found in results:")
    print(json.dumps(ballymackie[0], indent=2, default=str))
else:
    print("\n❌ Ballymackie NOT in results")
    
# Check for Ayr races
ayr_races = [x for x in data.get('results', []) if x.get('course') == 'Ayr']
print(f"\nAyr races in results: {len(ayr_races)}")
for race in ayr_races:
    print(f"  {race.get('horse'):30} {race.get('race_time')[11:16]} outcome: {race.get('outcome', 'pending')}")

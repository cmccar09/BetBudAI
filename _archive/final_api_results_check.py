import requests

r = requests.get('https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/results')
data = r.json()

print(f"API /results response:")
print(f"Total picks: {len(data.get('picks', []))}")
print(f"\nPicks:")
for p in data.get('picks', []):
    print(f"  {p.get('horse'):30} {p.get('course'):12} {p.get('outcome', 'pending'):10}")

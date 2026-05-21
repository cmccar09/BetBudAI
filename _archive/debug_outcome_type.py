import requests

r = requests.get('https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/results')
picks = r.json().get('picks', [])
b = [p for p in picks if 'Ballymackie' in p.get('horse', '')][0]

print(f"outcome value: '{b.get('outcome')}'")
print(f"outcome type: {type(b.get('outcome'))}")
print(f"outcome repr: {repr(b.get('outcome'))}")
print(f"outcome == 'win': {b.get('outcome') == 'win'}")
print(f"outcome.lower() if str: {b.get('outcome').lower() if isinstance(b.get('outcome'), str) else 'N/A'}")

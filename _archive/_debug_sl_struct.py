import requests, json, re

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36'}
DATE = '2026-03-29'
r = requests.get('https://www.sportinglife.com/racing/results/' + DATE, headers=HEADERS, timeout=30)
m = re.search('<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
data = json.loads(m.group(1))
meetings = data['props']['pageProps']['meetings']
print('First meeting keys:', list(meetings[0].keys()))
first = {k: v for k, v in meetings[0].items() if k != 'races'}
print(json.dumps(first, indent=2)[:800])
# Also check first race keys
if meetings[0].get('races'):
    print('\nFirst race keys:', list(meetings[0]['races'][0].keys()))

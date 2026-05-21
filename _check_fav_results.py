import json, urllib.request, re

req = urllib.request.Request(
    'https://www.sportinglife.com/racing/fast-results/all',
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
    },
)
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='replace')

m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
data = json.loads(m.group(1))
fast = data.get('props', {}).get('pageProps', {}).get('fastResults', [])

# Check Ripon 13:00, 13:35 and Limerick 13:10, Newmarket 15:10
targets = [('ripon','13:00'), ('ripon','13:35'), ('limerick','13:10'), ('newmarket','15:10')]
for fr in fast:
    course = fr.get('courseName', '').lower()
    t = fr.get('time', '')
    for tc, tt in targets:
        if tc in course and t == tt:
            top = sorted(fr.get('top_horses', []), key=lambda h: h.get('position', 99))
            print(f"\n{fr.get('courseName')} {t}:")
            for h in top[:4]:
                print(f"  #{h.get('position')} {h.get('horse_name','')}")

# Also check: who was the favourite?
print("\n\n--- Checking favourites from our DB ---")
import boto3
from datetime import datetime
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)
items = resp.get('Items', [])
while 'LastEvaluatedKey' in resp:
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today),
        ExclusiveStartKey=resp['LastEvaluatedKey']
    )
    items.extend(resp.get('Items', []))

# Group by race, find lowest odds horse (the favourite)
from collections import defaultdict
races = defaultdict(list)
for item in items:
    rt = item.get('race_time', '')
    course = item.get('course', '')
    races[(course, rt)].append(item)

target_courses = ['ripon', 'limerick', 'newmarket']
target_times = ['13:00', '13:10', '13:35', '15:10']

for (course, rt), runners in sorted(races.items()):
    c_lower = course.lower()
    if not any(tc in c_lower for tc in target_courses):
        continue
    utc_hhmm = rt[11:16] if len(rt) >= 16 else ''
    if utc_hhmm not in target_times:
        continue
    
    sorted_runners = sorted(runners, key=lambda h: float(h.get('odds', 99) or 99))
    fav = sorted_runners[0] if sorted_runners else None
    print(f"\n{course} {utc_hhmm} UTC:")
    print(f"  Favourite: {fav.get('horse','')} @ {float(fav.get('odds',0)):.2f}")
    print(f"  Outcome: {fav.get('outcome', 'pending')}")
    print(f"  Winner: {fav.get('winner_horse', '?')}")
    for r in sorted_runners[:4]:
        print(f"    {r.get('horse',''):30} odds={float(r.get('odds',0)):6.2f}  outcome={r.get('outcome','pending'):8}  finish={r.get('finish_position','?')}")

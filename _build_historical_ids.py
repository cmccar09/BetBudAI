"""
Harvest SL horse IDs for all horses in our March 22-30 picks.

Strategy:
1. Pull all horse names + race dates + courses from DynamoDB
2. For each date, fetch /racing/results/{date} to get meetings + race IDs
3. For each race at a course where we had picks, fetch:
   /racing/racecards/{date}/{course}/racecard/{race_id}/race
   → gets all runners + previous_results in one request
4. Save horse IDs to _sl_horse_ids.json and form data to form_cache.json
"""
import json, re, time, os, sys
import boto3
import requests
from boto3.dynamodb.conditions import Attr
from collections import defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# ── DynamoDB: get all horse names from picks ──────────────────────────────
db  = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

print("Loading picks from DynamoDB...")
items = []
kwargs = {'FilterExpression': Attr('bet_date').between('2026-03-22', '2026-03-30')}
while True:
    resp = tbl.scan(**kwargs)
    items += resp['Items']
    if not resp.get('LastEvaluatedKey'):
        break
    kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

items = [i for i in items if i.get('bet_id') != 'SYSTEM_ANALYSIS_MANIFEST']

# Collect all horse names and date+course combos
all_horses = set()
date_course_pairs = defaultdict(set)  # date -> set of course slugs to try
for item in items:
    horse = item.get('horse') or item.get('name') or ''
    if horse:
        all_horses.add(horse.lower().strip())
    bet_date = item.get('bet_date', '')
    course = item.get('course', '')
    if bet_date and course:
        date_course_pairs[bet_date].add(course)

print(f"Found {len(all_horses)} unique horses across {len(date_course_pairs)} dates")
for d, courses in sorted(date_course_pairs.items()):
    print(f"  {d}: {sorted(courses)}")

# ── SL HTTP ───────────────────────────────────────────────────────────────
SL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.sportinglife.com/',
    'Upgrade-Insecure-Requests': '1',
}
NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL)
RACE_URL_RE  = re.compile(r'(/racing/racecards/(\d{4}-\d{2}-\d{2})/([^/\s"]+)/racecard/(\d+)/[^"?\s]+)')

def get_html(url):
    try:
        r = requests.get(url, headers=SL_HEADERS, timeout=15, allow_redirects=True)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print(f"  HTTP error {url}: {e}")
    return None

def venue_slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower().strip()).strip('-')

# ── Load existing IDs ─────────────────────────────────────────────────────
ID_FILE = '_sl_horse_ids.json'
if os.path.exists(ID_FILE):
    with open(ID_FILE) as f:
        sl_ids = {k.lower(): int(v) for k, v in json.load(f).items()}
else:
    sl_ids = {}
print(f"\nLoaded {len(sl_ids)} existing IDs")

# ── For each date, fetch SL results page to discover race IDs ────────────
# Results at /racing/results/{date} → meetings[].races[].race_summary_reference.id
# Then fetch /racing/racecards/{date}/{course}/racecard/{race_id}/race
# (using "race" as a dummy slug — SL accepts it)

RESULTS_URL = 'https://www.sportinglife.com/racing/results/{date}'

def parse_runs(prev_results, max_runs=6):
    def dist_to_f(s):
        if not s: return None
        s = str(s).lower()
        total = 0.0
        m = re.search(r'(\d+)m', s)
        if m: total += int(m.group(1)) * 8
        f = re.search(r'(\d+)f', s)
        if f: total += int(f.group(1))
        y = re.search(r'(\d+)y', s)
        if y: total += int(y.group(1)) / 220
        return round(total, 2) if total > 0 else None
    runs = []
    for r in prev_results[:max_runs]:
        going_raw = r.get('going') or r.get('going_shortcode', '')
        runs.append({
            'date': r.get('date', ''),
            'course': r.get('course_name', ''),
            'distance_f': dist_to_f(r.get('distance', '')),
            'going': going_raw,
            'position': int(r['position']) if r.get('position') else None,
            'field_size': int(r['runner_count']) if r.get('runner_count') else None,
            'official_rating': int(r['or']) if r.get('or') else None,
            'race_class': str(r.get('race_class', '')),
            'beaten_lengths': None,
        })
    return runs

found_race_urls = defaultdict(list)  # date -> [(course_slug, race_id)]

for bet_date in sorted(date_course_pairs.keys()):
    url = RESULTS_URL.format(date=bet_date)
    print(f"\nFetching SL results for {bet_date}...")
    html = get_html(url)
    if not html:
        print(f"  -> Failed")
        continue
    m = NEXT_DATA_RE.search(html)
    if not m:
        print(f"  -> No NEXT_DATA")
        continue
    try:
        nd = json.loads(m.group(1))
        meetings_data = nd['props']['pageProps'].get('meetings', [])
    except Exception as e:
        print(f"  -> JSON error: {e}")
        continue
    
    # Which courses did we have picks at this date?
    our_courses = {venue_slug(c) for c in date_course_pairs[bet_date]}
    
    for mtg in meetings_data:
        course_name = mtg.get('meeting_summary', {}).get('course', {}).get('name', '')
        cs = venue_slug(course_name)
        # Only fetch races for courses where we had picks
        if not any(c in cs or cs in c for c in our_courses):
            continue
        for race in mtg.get('races', []):
            race_id = race.get('race_summary_reference', {}).get('id')
            if race_id:
                found_race_urls[bet_date].append((cs, race_id))
    
    n = sum(len(v) for v in found_race_urls.values())
    print(f"  -> {len(found_race_urls[bet_date])} race IDs at our courses (total so far: {n})")
    time.sleep(0.5)

total_races = sum(len(v) for v in found_race_urls.values())
print(f"\nTotal race IDs to fetch: {total_races}")

# ── Fetch each race racecard to harvest horse IDs + previous_results ──────
print("\n" + "="*60)
print("Fetching race racecards to harvest horse IDs...")

all_form_data = {}  # horse_name.lower() -> [run dicts]
new_ids_found = 0
done = 0

for bet_date, race_list in sorted(found_race_urls.items()):
    for course_slug, race_id in race_list:
        done += 1
        url = f'https://www.sportinglife.com/racing/racecards/{bet_date}/{course_slug}/racecard/{race_id}/race'
        print(f"  [{done}/{total_races}] {bet_date} {course_slug} race/{race_id}")
        html = get_html(url)
        if not html:
            continue
        m = NEXT_DATA_RE.search(html)
        if not m:
            continue
        try:
            nd = json.loads(m.group(1))
            rides = nd['props']['pageProps']['race']['rides']
        except (KeyError, ValueError) as e:
            print(f"    -> parse error: {e}")
            continue

        for ride in rides:
            horse = ride.get('horse', {})
            name = horse.get('name', '').strip()
            if not name:
                continue
            h_ref = (horse.get('horse_reference') or {})
            h_id = h_ref.get('id')
            if h_id and name.lower() not in sl_ids:
                sl_ids[name.lower()] = int(h_id)
                new_ids_found += 1
            prev = horse.get('previous_results', [])
            if prev and name.lower() not in all_form_data:
                all_form_data[name.lower()] = parse_runs(prev)
        time.sleep(0.35)

print(f"\nNew IDs found: {new_ids_found}, Total IDs: {len(sl_ids)}")
print(f"Horses with form data: {len(all_form_data)}")

# ── Check coverage for our picks ──────────────────────────────────────────
covered = [h for h in all_horses if h in all_form_data]
missing = [h for h in all_horses if h not in all_form_data]
print(f"\nCoverage of our picks:")
print(f"  With form data: {len(covered)}/{len(all_horses)}")
if covered:
    print(f"  Covered: {sorted(covered)[:20]}")
if missing:
    print(f"  Still missing ({len(missing)}): {sorted(missing)[:20]}")

# ── Save updated IDs ──────────────────────────────────────────────────────
with open(ID_FILE, 'w') as f:
    json.dump(sl_ids, f, indent=2)
print(f"\nSaved {len(sl_ids)} IDs to {ID_FILE}")

# ── Save form data to form_cache.json ─────────────────────────────────────
CACHE_FILE = 'form_cache.json'
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        cache = json.load(f)
else:
    cache = {}

now_str = datetime.utcnow().isoformat()
added = 0
for name, runs in all_form_data.items():
    if runs and (name not in cache or not cache[name].get('runs')):
        cache[name] = {'runs': runs, 'cached_at': now_str, 'source': 'sl_racecard_historical'}
        added += 1

with open(CACHE_FILE, 'w') as f:
    json.dump(cache, f, indent=2)
print(f"Added {added} new entries to form_cache.json (total: {len(cache)})")
print("\nDone! Now run: python _sim_form_enricher.py")

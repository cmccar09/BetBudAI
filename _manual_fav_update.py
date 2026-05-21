"""
Manual backfill: fetch SL race results for specific horses and update DynamoDB fav_outcome.
"""
import json, re, urllib.request, urllib.error, boto3
from datetime import datetime

DATE = '2026-04-07'         # DynamoDB partition key (racecard fetched this day)
SL_RESULTS_DATE = '2026-04-08'  # actual race date — bet_ids confirm Apr 8
REGION = 'eu-west-1'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': 'https://www.sportinglife.com/',
}

# Horses we need to resolve  { horse_name_lower: (utc_hhmm, course) }
TARGETS = {
    'infraad':        ('13:17', 'Nottingham'),
    'olympic charter':('13:47', 'Nottingham'),
    'final appeal':   ('14:22', 'Nottingham'),
    'spendmore lane': ('14:57', 'Nottingham'),
    'sinmara':        ('15:15', 'Gowran Park'),
    'tupero':         ('15:58', 'Catterick'),
}

SL_BASE = 'https://www.sportinglife.com'

# Course slug mappings
COURSE_SLUGS = {
    'nottingham': 'nottingham',
    'catterick':  'catterick',
    'gowran park': 'gowran-park',
}


def fetch(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'  [fetch] Error {url}: {e}')
        return ''


def norm(n):
    return re.sub(r"['\-\s]+", ' ', re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', (n or ''))).strip().lower()


def parse_winner_from_page(html):
    """Extract winner name from SL race result HTML."""
    # 1. ResultRunner CSS class (finish order)
    runners = re.findall(
        r'ResultRunner__StyledHorseName[^"]*"[^>]*><a\s+href="/racing/profiles/horse/\d+"[^>]*>([^<]+)</a>',
        html,
    )
    if runners:
        return re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', runners[0]).strip()

    # 2. og:description "X won the ..."
    for pat in [
        r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"',
        r'<meta[^>]+content="([^"]*)"[^>]+property="og:description"',
    ]:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            wm = re.match(r'^([A-Z][^.]+?)\s+won\b', m.group(1))
            if wm:
                return wm.group(1).strip()
    return None


def find_race_ids_from_index(date_str, courses):
    """Fetch index page and return {course_slug: [(race_id, path)]}."""
    print(f'\nFetching SL results index for {date_str}...')
    html = fetch(f'{SL_BASE}/racing/results/{date_str}/')
    if not html:
        return {}

    print(f'  Index page: {len(html)} bytes')

    result = {}

    # Try plain href first
    pat = re.compile(
        r'href="(/racing/results/' + re.escape(date_str) + r'/([^/]+)/(\d+)/[^"]+)"'
    )
    for m in pat.finditer(html):
        path, slug, rid = m.group(1), m.group(2), m.group(3)
        if slug in courses:
            result.setdefault(slug, []).append((rid, path))

    # Try __NEXT_DATA__
    nd = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if nd:
        try:
            raw = json.dumps(json.loads(nd.group(1)))
            pat2 = re.compile(
                r'/racing/results/' + re.escape(date_str) + r'/([^/\"\'\\]+)/(\d+)'
            )
            for m in pat2.finditer(raw):
                slug, rid = m.group(1), m.group(2)
                # decode any JSON-escaped characters
                slug = slug.replace('\\/', '/')
                if slug in courses:
                    path = f'/racing/results/{date_str}/{slug}/{rid}/race'
                    result.setdefault(slug, []).append((rid, path))
            print(f'  NEXT_DATA parsed — found slugs: {list(result.keys())}')
            # show what we found
            for s, races in result.items():
                print(f'    {s}: {len(races)} race IDs → {[r for r,_ in races[:5]]}')
        except Exception as e:
            print(f'  NEXT_DATA parse error: {e}')

    # Deduplicate
    for k in result:
        seen = set()
        deduped = []
        for rid, path in result[k]:
            if rid not in seen:
                seen.add(rid)
                deduped.append((rid, path))
        result[k] = deduped

    return result


def main():
    dyn = boto3.resource('dynamodb', region_name=REGION)
    tbl = dyn.Table('SureBetBets')

    # Load all items for date
    all_items = []
    kwargs = {'KeyConditionExpression': boto3.dynamodb.conditions.Key('bet_date').eq(DATE)}
    while True:
        resp = tbl.query(**kwargs)
        all_items.extend(resp.get('Items', []))
        last = resp.get('LastEvaluatedKey')
        if not last:
            break
        kwargs['ExclusiveStartKey'] = last

    # Find our target rows in DB — match by horse name
    target_rows = {}  # horse_norm → db item
    for it in all_items:
        hn = norm(it.get('horse', ''))
        if hn in TARGETS:
            target_rows[hn] = it

    print(f'\nTarget horses found in DynamoDB:')
    for hn, it in target_rows.items():
        print(f'  {it.get("horse")} | course: {it.get("course")} | fav_outcome: {it.get("fav_outcome")} | bet_id: {it.get("bet_id","?")}')

    missing = set(TARGETS) - set(target_rows)
    if missing:
        print(f'\nNOT found in DynamoDB: {missing}')

    # Unique course slugs needed
    needed_courses = set()
    for hn in target_rows:
        _, course = TARGETS[hn]
        slug = COURSE_SLUGS.get(course.lower())
        if slug:
            needed_courses.add(slug)

    print(f'\nCourses to scrape: {needed_courses}')

    # Find race IDs from index (use SL_RESULTS_DATE, not DynamoDB DATE)
    race_ids = find_race_ids_from_index(SL_RESULTS_DATE, needed_courses)
    print(f'Race IDs found: { {k: len(v) for k,v in race_ids.items()} }')

    # For each course, fetch each race page and collect (off_time, winner)
    course_results = {}  # course_slug → [(off_time_hhmm, winner)]
    for slug, races in race_ids.items():
        print(f'\n  Fetching {len(races)} race page(s) for {slug}...')
        for rid, path in races:
            # Try the direct path; SL sometimes redirects if the slug is wrong
            urls_to_try = [SL_BASE + path]
            # Also try direct race ID URL (some SL versions accept this)
            urls_to_try.append(f'{SL_BASE}/racing/results/{SL_RESULTS_DATE}/{slug}/{rid}/')
            html = ''
            for url in urls_to_try:
                html = fetch(url)
                if html and ('Off time' in html or 'ResultRunner' in html or 'won the' in html.lower()):
                    break
            if not html:
                continue
            off_m = re.search(r'Off time:\s*(\d{1,2}:\d{2})', html)
            off_time = off_m.group(1).zfill(5) if off_m else None
            winner = parse_winner_from_page(html)
            if winner:
                print(f'    {slug} {off_time} → {winner}')
                course_results.setdefault(slug, []).append((off_time, winner))
            else:
                print(f'    {slug} {off_time} → no winner found (rid={rid})')

    # BST offset: Apr 7 = BST so UTC+1 → local = UTC+1
    def utc_to_bst(hhmm):
        h, m = map(int, hhmm.split(':'))
        total = h * 60 + m + 60
        return f'{(total//60)%24:02d}:{total%60:02d}'

    # Match and update
    updated = 0
    print('\n--- Matching results to target horses ---')
    for hn, it in target_rows.items():
        utc_hhmm, course = TARGETS[hn]
        local_hhmm = utc_to_bst(utc_hhmm)
        slug = COURSE_SLUGS.get(course.lower())
        fav_name = it.get('horse', '')
        bet_id = it.get('bet_id', '')
        existing = it.get('fav_outcome', '')

        if existing and str(existing).lower() not in ('', 'pending', 'none'):
            print(f'  {fav_name}: already resolved ({existing}) — skipping')
            continue

        winner_name = None
        for off_t, w in course_results.get(slug, []):
            if off_t:
                try:
                    lh, lm = map(int, local_hhmm.split(':'))
                    oh, om = map(int, off_t.split(':'))
                    if abs((lh*60+lm) - (oh*60+om)) <= 15:
                        winner_name = w
                        break
                except Exception:
                    pass

        if not winner_name:
            print(f'  {fav_name} ({course} {utc_hhmm} UTC / {local_hhmm} local): NO RESULT FOUND')
            continue

        fav_outcome = 'win' if norm(winner_name) == norm(fav_name) else 'loss'
        result_label = '✓ FAV LOST (LAY WIN)' if fav_outcome == 'loss' else '✗ FAV WON'
        print(f'  {result_label}: {fav_name} — winner was {winner_name}')

        tbl.update_item(
            Key={'bet_date': DATE, 'bet_id': bet_id},
            UpdateExpression='SET fav_outcome = :fo, race_winner_name = :wn',
            ExpressionAttributeValues={':fo': fav_outcome, ':wn': winner_name},
        )
        updated += 1

    print(f'\nDone — {updated} records updated.')


if __name__ == '__main__':
    main()

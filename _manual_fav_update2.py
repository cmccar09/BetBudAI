"""
Fetch Nottingham/Catterick/Gowran Park race results from SL NEXT_DATA and update DynamoDB.
"""
import urllib.request, re, json, boto3
from decimal import Decimal

DATE = '2026-04-07'      # DynamoDB partition key
SL_DATE = '2026-04-08'   # actual race date
REGION = 'eu-west-1'
SL_BASE = 'https://www.sportinglife.com'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': 'https://www.sportinglife.com/',
}

TARGET_COURSES = {'nottingham', 'catterick', 'gowran park'}

# Horses we need (lower-case name → (utc_hhmm, course_display))
TARGETS = {
    'infraad':         ('13:17', 'Nottingham'),
    'olympic charter': ('13:47', 'Nottingham'),
    'final appeal':    ('14:22', 'Nottingham'),
    'spendmore lane':  ('14:57', 'Nottingham'),
    'sinmara':         ('15:15', 'Gowran Park'),
    'tupero':          ('15:58', 'Catterick'),
}


def norm(n):
    return re.sub(r"['\-\s]+", ' ', re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', (n or ''))).strip().lower()


def utc_to_bst(hhmm, date_str=SL_DATE):
    """Convert UTC HH:MM to BST (UTC+1) for April 2026."""
    h, m = map(int, hhmm.split(':'))
    total = h * 60 + m + 60
    return f'{(total//60)%24:02d}:{total%60:02d}'


def fetch_nextdata_meetings():
    """Fetch SL results index for SL_DATE and return meetings list from NEXT_DATA."""
    req = urllib.request.Request(
        f'{SL_BASE}/racing/results/{SL_DATE}/',
        headers=HEADERS,
    )
    html = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'replace')
    print(f'Fetched results index: {len(html)} bytes')
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        print('ERROR: No __NEXT_DATA__ found')
        return []
    data = json.loads(m.group(1))
    meetings = data.get('props', {}).get('pageProps', {}).get('meetings', [])
    print(f'Found {len(meetings)} meetings in NEXT_DATA')
    return meetings


def parse_race_winner_from_meeting(race):
    """
    Extract winner from a race dict in NEXT_DATA.
    Returns (off_time_hhmm, winner_name) or (None, None).
    """
    # off_time: 'off_dt' or 'off_time' or 'scheduled_off' 
    off_time = None
    for key in ('off_dt', 'off_time', 'scheduled_off', 'time'):
        v = race.get(key, '')
        if v:
            t_m = re.search(r'(\d{2}:\d{2})', str(v))
            if t_m:
                off_time = t_m.group(1)
                break

    # Winner from runners list
    runners = race.get('runners', [])
    winner_name = None

    # Sort by position
    def pos_key(r):
        try:
            return int(r.get('position', 99))
        except Exception:
            return 99

    sorted_runners = sorted(runners, key=pos_key)
    if sorted_runners:
        r1 = sorted_runners[0]
        # position should be 1
        if str(r1.get('position', '')).strip() in ('1', '1st'):
            winner_name = r1.get('horse', {})
            if isinstance(winner_name, dict):
                winner_name = winner_name.get('name', '')
            elif not isinstance(winner_name, str):
                winner_name = str(winner_name)
            winner_name = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', winner_name).strip()

    # Fallback: look for 'result' or 'winner' key
    if not winner_name:
        winner_name = race.get('winner_name') or race.get('winner', {})
        if isinstance(winner_name, dict):
            winner_name = winner_name.get('name', '')
        winner_name = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', str(winner_name or '')).strip()

    return off_time, winner_name or None


def main():
    # 1. Get meetings from NEXT_DATA
    meetings = fetch_nextdata_meetings()

    # 2. Build results map: (course_lower, off_time_local_bst) → winner_name
    results_map = {}
    for meeting in meetings:
        ms = meeting.get('meeting_summary', {})
        course_name = (ms.get('course', {}).get('name', '') or '').strip()
        if course_name.lower() not in TARGET_COURSES:
            continue
        races = meeting.get('races', [])
        print(f'\n{course_name}: {len(races)} races')
        for race in races:
            off_utc, winner = parse_race_winner_from_meeting(race)
            # Print full race dict keys to understand structure
            print(f'  Race keys: {list(race.keys())}')
            if off_utc:
                off_local = utc_to_bst(off_utc)
            else:
                off_local = None
            print(f'  off_utc={off_utc} off_local={off_local} winner={winner}')
            if off_local and winner:
                results_map[(course_name.lower(), off_local)] = winner

    print(f'\nResults map: {len(results_map)} entries')
    for k, v in sorted(results_map.items()):
        print(f'  {k[0]} {k[1]} → {v}')

    # 3. Load DynamoDB rows for target horses
    dyn = boto3.resource('dynamodb', region_name=REGION)
    tbl = dyn.Table('SureBetBets')
    all_items = []
    kwargs = {'KeyConditionExpression': boto3.dynamodb.conditions.Key('bet_date').eq(DATE)}
    while True:
        resp = tbl.query(**kwargs)
        all_items.extend(resp.get('Items', []))
        last = resp.get('LastEvaluatedKey')
        if not last:
            break
        kwargs['ExclusiveStartKey'] = last

    target_rows = {norm(it.get('horse', '')): it for it in all_items
                   if norm(it.get('horse', '')) in TARGETS}

    # 4. Match and update
    updated = 0
    print('\n--- Updates ---')
    for hn, it in target_rows.items():
        utc_hhmm, course = TARGETS[hn]
        local_hhmm = utc_to_bst(utc_hhmm)
        fav_name = it.get('horse', '')
        bet_id = it.get('bet_id', '')

        # try to find winner
        winner_name = None
        for (c, t), w in results_map.items():
            if c == course.lower():
                try:
                    lh, lm = map(int, local_hhmm.split(':'))
                    th, tm = map(int, t.split(':'))
                    if abs((lh*60+lm) - (th*60+tm)) <= 15:
                        winner_name = w
                        break
                except Exception:
                    pass

        if not winner_name:
            print(f'  NO RESULT: {fav_name} @ {course} {utc_hhmm} UTC / {local_hhmm} BST')
            continue

        fav_outcome = 'win' if norm(winner_name) == norm(fav_name) else 'loss'
        label = '✓ FAV LOST (LAY WIN)' if fav_outcome == 'loss' else '✗ FAV WON'
        print(f'  {label}: {fav_name} — winner: {winner_name}')

        tbl.update_item(
            Key={'bet_date': DATE, 'bet_id': bet_id},
            UpdateExpression='SET fav_outcome = :fo, race_winner_name = :wn',
            ExpressionAttributeValues={':fo': fav_outcome, ':wn': winner_name},
        )
        updated += 1

    print(f'\nTotal updated: {updated}')


if __name__ == '__main__':
    main()

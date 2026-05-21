"""Test the racecard pre-fetch and enrich_runners pipeline."""
from form_enricher import _get_sl_race_urls, _fetch_sl_race_form, _sl_id_map
from datetime import datetime
import time

# Step 1: Get today's race URLs
today = datetime.now().strftime('%Y-%m-%d')
print(f'Testing for date: {today}')
sl_race_urls = _get_sl_race_urls(today)
print(f'Venues found: {list(sl_race_urls.keys())[:10]}')
n_urls = sum(len(v) for v in sl_race_urls.values())
print(f'Total race URLs: {n_urls}')
print()

# Step 2: Pick first venue and fetch its first race
if sl_race_urls:
    first_venue = list(sl_race_urls.keys())[0]
    first_url = sl_race_urls[first_venue][0]
    print(f'Fetching: {first_venue} -> {first_url}')
    race_form = _fetch_sl_race_form(first_url)
    print(f'Horses from racecard: {len(race_form)}')
    for name, runs in list(race_form.items())[:3]:
        print(f'  {name}: {len(runs)} runs')
        if runs:
            r = runs[0]
            print(f'    Last run: {r["date"]} {r["course"]} pos={r["position"]} OR={r["official_rating"]} bl={r["beaten_lengths"]}')
    
    print(f'\nNew IDs discovered: {len(_sl_id_map)} total in map (was 360)')
else:
    print('No race URLs found for today (might be early or no racing today)')
    # Test with a known historical URL from last session
    test_url = 'https://www.sportinglife.com/racing/racecards/2026-03-30/ludlow/racecard/909672/weatherbys-nhstallionscouk-novices-hurdle-gbb-race'
    print(f'\nTesting with known historical URL...')
    race_form = _fetch_sl_race_form(test_url)
    print(f'Horses: {len(race_form)}')
    for name, runs in list(race_form.items())[:3]:
        print(f'  {name}: {len(runs)} runs')
        if runs:
            r = runs[0]
            print(f'    Last run: {r["date"]} {r["course"]} pos={r["position"]} OR={r["official_rating"]}')

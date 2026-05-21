"""Test enrich_runners with simulated race data."""
from form_enricher import enrich_runners

# Simulate race data with Betfair-style structure
test_races = [
    {
        'race_id': 'test_1',
        'course': 'Ludlow',
        'time': '13:10',
        'runners': [
            {'name': 'Jimbo Sport'},
            {'name': 'Snatch A Glance'},
            {'name': 'Current Edition'},
        ]
    },
]

print('Running enrich_runners...')
enriched = enrich_runners(test_races, verbose=True)

print('\nResults:')
for race in enriched:
    print(f"\nRace: {race['course']} {race['time']}")
    for runner in race['runners']:
        runs = runner.get('form_runs', [])
        print(f"  {runner['name']}: {len(runs)} form runs")
        for r in runs[:2]:
            print(f"    {r['date']} {r['course']} | pos={r['position']}/{r['field_size']} | {r['going']} | {r['distance_f']}f")

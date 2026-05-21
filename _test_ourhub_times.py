from ourhub_enricher import fetch_ourhub_data, enrich_races
import json

data = fetch_ourhub_data('2026-04-13')

# Simulate races with UTC ISO times (13:40 UTC = 14:40 BST)
races = [
    {
        'course': 'Fakenham',
        'start_time': '2026-04-13T13:40:00+00:00',
        'marketId': 'test',
        'market_name': 'Racing TV Handicap Hurdle',
        'runners': [
            {'name': 'Ilitch', 'odds': 5.0, 'jockey': 'Charlie Hammond', 'trainer': 'Stuart Edmunds'},
            {'name': 'Blues Singer', 'odds': 4.5, 'jockey': 'Tom Bellamy', 'trainer': 'Alan King'},
        ]
    }
]

races = enrich_races(races, data)

for race in races:
    print(f"Race: {race['course']}")
    print(f"  ourhub_going: {race.get('ourhub_going', 'N/A')}")
    print(f"  ourhub_distance: {race.get('ourhub_distance', 'N/A')}")
    print(f"  ourhub_race_class: {race.get('ourhub_race_class', 'N/A')}")
    for r in race['runners']:
        print(f"  {r['name']}: twr={r.get('ourhub_trainer_win_rate', '?')} "
              f"jwr={r.get('ourhub_jockey_win_rate', '?')} "
              f"wp={r.get('ourhub_win_prob', '?')}")

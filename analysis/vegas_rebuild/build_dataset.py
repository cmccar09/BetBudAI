"""
Reconstruct races from the pulled per-day settled-record files and apply the
same data-quality filter as the 2026-09-01 vegas.md analysis: keep a race
only if reconstruction shows EXACTLY one winner among its settled runners.

Writes analysis/vegas_rebuild/dataset.json:
{
  "races": [ { "race_key": [date, course, race_time], "runners": [ {horse, odds,
      outcome, finish_position, score_breakdown} ... ] }, ... ],
  "factor_keys": [...all score_breakdown keys ever seen...]
}
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'
OUT_PATH = Path(__file__).parent / 'dataset.json'


def main():
    races = defaultdict(list)
    day_files = sorted(DATA_DIR.glob('2026-*.json'))
    n_loaded = 0
    for f in day_files:
        recs = json.loads(f.read_text())
        for r in recs:
            key = (r['bet_date'], r.get('course') or 'Unknown', r.get('race_time') or '')
            races[key].append(r)
            n_loaded += 1

    print(f'Loaded {n_loaded} records across {len(day_files)} day-files, '
          f'{len(races)} raw race groups')

    # Data-quality filter: exactly one winner
    kept = []
    reject_reasons = Counter()
    for key, runners in races.items():
        wins = [r for r in runners if r.get('outcome') == 'win']
        if len(wins) != 1:
            reject_reasons['not_exactly_one_winner'] += 1
            continue
        if len(runners) < 2:
            reject_reasons['fewer_than_2_runners'] += 1
            continue
        kept.append({'race_key': list(key), 'runners': runners})

    print(f'Kept {len(kept)} races after exactly-one-winner filter '
          f'({sum(reject_reasons.values())} rejected: {dict(reject_reasons)})')

    n_obs = sum(len(r['runners']) for r in kept)
    print(f'{n_obs} settled horse-observations in kept races')

    # Collect every score_breakdown key ever seen
    factor_keys = set()
    for race in kept:
        for r in race['runners']:
            bd = r.get('score_breakdown') or {}
            factor_keys.update(bd.keys())
    factor_keys = sorted(factor_keys)
    print(f'{len(factor_keys)} distinct score_breakdown keys observed: {factor_keys}')

    with open(OUT_PATH, 'w') as f:
        json.dump({'races': kept, 'factor_keys': factor_keys}, f)
    print(f'Wrote {OUT_PATH}')


if __name__ == '__main__':
    main()

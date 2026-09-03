"""
Fire-rate stats for every score_breakdown key across the rebuilt dataset
(2026-06-01 -> 2026-09-02, 3,367 races / 33,552 settled horse-observations).

Dead = literally zero nonzero observations across the whole window.
"""
import json
from collections import Counter
from pathlib import Path

DATASET = Path(__file__).parent / 'dataset.json'


def main():
    data = json.loads(DATASET.read_text())
    races = data['races']
    factor_keys = data['factor_keys']

    nonzero_counts = Counter()
    total_obs = 0
    for race in races:
        for r in race['runners']:
            bd = r.get('score_breakdown') or {}
            total_obs += 1
            for k in factor_keys:
                v = bd.get(k, 0) or 0
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    v = 0
                if v != 0:
                    nonzero_counts[k] += 1

    print(f'{total_obs} total observations, {len(races)} races\n')
    print(f'{"factor":30s} {"nonzero":>8s} {"pct":>7s}')
    dead = []
    thin = []
    for k in sorted(factor_keys, key=lambda k: -nonzero_counts[k]):
        n = nonzero_counts[k]
        pct = 100.0 * n / total_obs if total_obs else 0
        flag = ''
        if n == 0:
            flag = '  <-- DEAD (never fires)'
            dead.append(k)
        elif n < 30:
            flag = '  <-- THIN (<30 obs)'
            thin.append(k)
        print(f'{k:30s} {n:8d} {pct:6.2f}%{flag}')

    print(f'\n{len(dead)} DEAD factors (0 nonzero obs): {dead}')
    print(f'\n{len(thin)} THIN factors (<30 nonzero obs, incl dead): {thin}')


if __name__ == '__main__':
    main()

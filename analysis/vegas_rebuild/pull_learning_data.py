"""
Pull settled per-horse score_breakdown records from SureBetBets for the
feature-level Plackett-Luce rebuild (2026-09-03 session).

Deliberate methodology choice vs the 2026-09-01 vegas.md analysis: this pulls
ALL analysis_type='comprehensive_7factor' items per date (any pick_type -
learning/morning/value/extended/dropped), not just pick_type='learning'.
The daily top-5 UI picks (pick_type='morning'/'value') are a small fraction
of a day's records but CAN be the actual race winner - excluding them would
silently drop races where our own top-ranked horse won, which is exactly the
subset most informative about model calibration. Filtering on analysis_type
alone avoids that bias for free (no extra reads).

Date window: 2026-06-01 -> 2026-09-02 (yesterday; today is not yet settled).
2026-06-01 was chosen, not the earliest data available (schema confirmed
present back to at least 2026-06-15, and DEFAULT_WEIGHTS / gate logic history
shows the last score_breakdown-relevant formula changes were 2026-05-29
[consistency cap, maiden_fav_penalty, unexposed_bonus threshold] - everything
from 2026-06-02 onward only touched already-excluded meta/cap factors
(deep_form cap, no_form_cap, final_score_cap, TARGET_PICKS/MAX_DAILY_UI_PICKS
gates). Starting 06-01 keeps every pulled record on a materially consistent
scoring formula while maximizing sample size versus a narrower window.

Writes one JSON file per settled date to ./data/<date>.json so the pull can
be resumed/inspected incrementally. Re-run is idempotent (overwrites).
"""
import boto3
import decimal
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REGION = 'eu-west-1'
TABLE = 'SureBetBets'
START_DATE = '2026-06-01'
END_DATE = '2026-09-02'  # inclusive, last fully-settled day
OUT_DIR = Path(__file__).parent / 'data'

KEEP_FIELDS = [
    'bet_id', 'bet_date', 'course', 'race_time', 'market_id', 'market_name',
    'horse', 'odds', 'decimal_odds', 'outcome', 'finish_position',
    'result_winner_name', 'race_total_count', 'race_analyzed_count',
    'race_coverage_pct', 'form_enriched', 'pick_type', 'pick_rank',
    'comprehensive_score', 'combined_confidence', 'score_breakdown',
    'race_type', 'non_runners_count',
]


def conv(o):
    if isinstance(o, decimal.Decimal):
        f = float(o)
        return int(f) if f.is_integer() else f
    if isinstance(o, list):
        return [conv(x) for x in o]
    if isinstance(o, dict):
        return {k: conv(v) for k, v in o.items()}
    return o


def daterange(start, end):
    d = datetime.strptime(start, '%Y-%m-%d')
    e = datetime.strptime(end, '%Y-%m-%d')
    while d <= e:
        yield d.strftime('%Y-%m-%d')
        d += timedelta(days=1)


def pull_day(table, date_str):
    items = []
    kwargs = dict(
        KeyConditionExpression='bet_date = :d',
        FilterExpression='analysis_type = :at AND attribute_exists(score_breakdown)',
        ExpressionAttributeValues={':d': date_str, ':at': 'comprehensive_7factor'},
    )
    while True:
        resp = table.query(**kwargs)
        items.extend(resp.get('Items', []))
        lek = resp.get('LastEvaluatedKey')
        if not lek:
            break
        kwargs['ExclusiveStartKey'] = lek
    trimmed = []
    for it in items:
        outcome = it.get('outcome')
        if outcome not in ('win', 'placed', 'loss'):
            continue  # unsettled / pending / non-runner - skip
        rec = {k: it.get(k) for k in KEEP_FIELDS}
        trimmed.append(conv(rec))
    return trimmed


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ddb = boto3.resource('dynamodb', region_name=REGION)
    table = ddb.Table(TABLE)

    total = 0
    manifest = {}
    t0 = time.time()
    for date_str in daterange(START_DATE, END_DATE):
        out_path = OUT_DIR / f'{date_str}.json'
        try:
            recs = pull_day(table, date_str)
        except Exception as e:
            print(f'{date_str}: ERROR {e}', file=sys.stderr)
            manifest[date_str] = {'error': str(e)}
            continue
        with open(out_path, 'w') as f:
            json.dump(recs, f)
        n_races = len({(r['course'], r['race_time']) for r in recs})
        manifest[date_str] = {'n_records': len(recs), 'n_races': n_races}
        total += len(recs)
        print(f'{date_str}: {len(recs):4d} settled records, {n_races:3d} races  '
              f'(elapsed {time.time()-t0:5.0f}s)')

    with open(OUT_DIR / '_manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'\nDONE. {total} total settled records across '
          f'{sum(1 for v in manifest.values() if "n_records" in v)} days. '
          f'{time.time()-t0:.0f}s elapsed.')


if __name__ == '__main__':
    main()

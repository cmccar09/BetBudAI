"""
Lambda: surebet-validate
============================
Phase : Morning / Refresh
Input : {"date": "YYYY-MM-DD", "picks_count": N}
Output: {"success": true, "date": "...", "valid_picks": N, "errors": [...]}

Raises an exception (fails the Step Functions task) if any pick is invalid.
'Invalid' means: all_horses list is empty / too small, odds <= 1, or score == 0.
"""

import os
import json
import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

REGION    = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')
MIN_FIELD = 2   # minimum runners in all_horses to consider a pick valid


def lambda_handler(event, context):
    date_str = event.get('date', datetime.datetime.utcnow().strftime('%Y-%m-%d'))

    db    = boto3.resource('dynamodb', region_name=REGION)
    table = db.Table('SureBetBets')

    resp = table.query(
        KeyConditionExpression = Key('bet_date').eq(date_str),
        FilterExpression       = Attr('show_in_ui').eq(True),
    )
    picks = resp.get('Items', [])

    if not picks:
        raise RuntimeError(f"[sf_validate] No show_in_ui picks for {date_str} — analysis may have failed")

    errors   = []
    warnings = []
    form_enriched_count   = 0
    form_unenriched_count = 0

    for p in picks:
        horse   = p.get('horse', p.get('horse_name', 'unknown'))
        score   = float(p.get('comprehensive_score', p.get('analysis_score', 0)))
        odds    = float(p.get('odds', 0))
        all_h   = p.get('all_horses', [])
        n_runners = len(all_h) if isinstance(all_h, list) else 0

        if n_runners < MIN_FIELD:
            errors.append(f"{horse}: all_horses={n_runners} (need ≥{MIN_FIELD})")
        if score <= 0:
            errors.append(f"{horse}: score={score} (must be > 0)")
        if odds <= 1:
            errors.append(f"{horse}: odds={odds} (must be > 1)")

        # Form enrichment check — was this horse scored with actual form data?
        if p.get('form_enriched') is True:
            form_enriched_count += 1
        elif p.get('form_enriched') is False:
            form_unenriched_count += 1
            warnings.append(f"{horse}: no form data — pick scored on market signals only")

        # Coverage check — what was overall field coverage when this pick was made?
        cov = float(p.get('race_coverage_pct', 100))
        if cov < 25:
            warnings.append(f"{horse}: race_coverage_pct={cov:.0f}% (below 25% gate at analysis time)")

    if errors:
        raise RuntimeError(f"[sf_validate] FAILED — {len(errors)} pick error(s): " + "; ".join(errors))

    if warnings:
        print(f"[sf_validate] DATA WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")
    else:
        print(f"[sf_validate] All picks have form data (form_enriched=True)")

    print(f"[sf_validate] PASSED — all {len(picks)} pick(s) valid for {date_str} "
          f"| form_enriched={form_enriched_count} unenriched={form_unenriched_count}")
    return {
        'success'              : True,
        'date'                 : date_str,
        'valid_picks'          : len(picks),
        'errors'               : [],
        'warnings'             : warnings,
        'form_enriched_picks'  : form_enriched_count,
        'form_unenriched_picks': form_unenriched_count,
    }

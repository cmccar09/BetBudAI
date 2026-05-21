"""
Lambda: surebet-learning
============================
Phase : Learning (nightly)
Input : {"date": "YYYY-MM-DD"}   (optional — used for logging only)
Output: {"success": true, "results_scanned": N, "patterns_found": N, "insights": [...]}

1. Scans DynamoDB SureBetBets for the last 7 days of settled picks
2. Calls learning_engine.analyze_performance_patterns()
3. Calls learning_engine.generate_learning_insights()
4. Persists updated weights / insights to DynamoDB under
      bet_date='LEARNING_INSIGHTS', bet_id='latest'
5. Returns a compact summary

Bundled source: learning_engine.py
"""

import os
import sys
import json
import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
from collections import defaultdict

REGION   = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')
DAYS_BACK = int(os.environ.get('LEARNING_DAYS_BACK', '7'))

sys.path.insert(0, '/var/task')


# ── DynamoDB helpers ──────────────────────────────────────────────────────────

def _load_results_from_dynamodb(table):
    """Query last DAYS_BACK days of settled picks from DynamoDB by bet_date."""
    today   = datetime.datetime.utcnow().date()
    results = []
    SETTLED = {'win', 'won', 'WIN', 'loss', 'lost', 'LOSS', 'placed', 'PLACED'}

    for days_ago in range(DAYS_BACK):
        d = (today - datetime.timedelta(days=days_ago)).isoformat()
        kwargs = {
            'KeyConditionExpression': Key('bet_date').eq(d),
            'FilterExpression': Attr('show_in_ui').eq(True),
        }
        while True:
            resp  = table.query(**kwargs)
            items = resp.get('Items', [])
            for item in items:
                outcome = str(item.get('outcome', '')).lower().strip()
                if outcome not in {'win', 'won', 'loss', 'lost', 'placed'}:
                    continue  # skip pending / unresolved

                def _f(v):
                    try: return float(v)
                    except: return 0.0

                is_winner = outcome in ('win', 'won')
                is_placed = outcome in ('win', 'won', 'placed')

                results.append({
                    'date'  : item.get('bet_date', d),
                    'sport' : item.get('sport', 'horses'),
                    'selection': {
                        'selection_id' : item.get('selection_id', ''),
                        'runner_name'  : item.get('horse', item.get('dog', '')),
                        'venue'        : item.get('course', ''),
                        'odds'         : _f(item.get('odds')),
                        'bet_type'     : item.get('bet_type', 'WIN'),
                        'confidence'   : _f(item.get('comprehensive_score', item.get('confidence'))),
                        'tags'         : item.get('tags', ''),
                        'why_now'      : item.get('why_now', ''),
                        'stake'        : _f(item.get('stake', 10)),
                    },
                    'result': {
                        'is_winner'      : is_winner,
                        'is_placed'      : is_placed,
                        'final_odds'     : _f(item.get('odds')),
                        'actual_position': item.get('actual_position'),
                        'profit_loss'    : _f(item.get('profit_loss')),
                    },
                })
            lk = resp.get('LastEvaluatedKey')
            if not lk:
                break
            kwargs['ExclusiveStartKey'] = lk

    return results


def _persist_insights(table, insights, date_str):
    """Save learning insights to DynamoDB for next analysis cycle to consume."""
    table.put_item(Item={
        'bet_date'        : 'LEARNING_INSIGHTS',
        'bet_id'          : 'latest',
        'date'            : date_str,
        'insights'        : json.dumps(insights, default=str),
        'updated_at'      : datetime.datetime.utcnow().isoformat(),
    })


# ── main handler ──────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    date_str = event.get('date', datetime.datetime.utcnow().strftime('%Y-%m-%d'))

    db    = boto3.resource('dynamodb', region_name=REGION)
    table = db.Table('SureBetBets')

    print(f"[sf_learning] Loading results for last {DAYS_BACK} days ...")
    results = _load_results_from_dynamodb(table)
    print(f"[sf_learning] {len(results)} settled picks found")

    if not results:
        print("[sf_learning] No results to learn from — skipping")
        return {'success': True, 'date': date_str, 'results_scanned': 0, 'patterns_found': 0, 'insights': []}

    from learning_engine import analyze_performance_patterns, generate_learning_insights

    print("[sf_learning] Analysing performance patterns ...")
    analysis = analyze_performance_patterns(results)

    print("[sf_learning] Generating insights ...")
    insights = generate_learning_insights(analysis)

    _persist_insights(table, insights, date_str)

    patterns_found = sum(
        len(v) if isinstance(v, (list, dict)) else 1
        for v in analysis.values()
    ) if isinstance(analysis, dict) else 0

    # Compact insight summaries for Step Functions output
    insight_summaries = [str(i)[:200] for i in (insights or [])[:10]]

    print(f"[sf_learning] Done — {patterns_found} pattern entries, {len(insights or [])} insights persisted")
    return {
        'success'         : True,
        'date'            : date_str,
        'results_scanned' : len(results),
        'patterns_found'  : patterns_found,
        'insights'        : insight_summaries,
    }

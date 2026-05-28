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
                        'race_type'    : item.get('race_type', ''),
                        'market_name'  : item.get('market_name', ''),
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


def _persist_insights(table, insights, analysis, date_str, raw_results=None):
    """Save learning insights + structured signals to DynamoDB.

    Structured fields consumed by complete_daily_analysis.py STAGE 0:
      odds_roi     — {category: {roi, win_rate, n}} for categories with ≥5 bets
      best_courses — venue names with ≥5 bets and ≥40% win rate
    """
    # Build odds_roi from raw analysis buckets
    odds_roi = {}
    for cat, stats in (analysis.get('by_odds_range') or {}).items():
        n = int(stats.get('total', 0))
        if n >= 5:
            roi = round(float(stats['roi']) / n * 100, 1)
            wr  = round(float(stats['wins']) / n * 100, 1)
            odds_roi[cat] = {'roi': roi, 'win_rate': wr, 'n': n}

    # Best courses: ≥5 bets, ≥40% WR
    best_courses = [
        course for course, stats in (analysis.get('by_course') or {}).items()
        if int(stats.get('total', 0)) >= 5
        and int(stats.get('wins', 0)) / int(stats.get('total', 1)) >= 0.40
    ]

    # Race type performance breakdown — saved alongside odds/course signals
    race_type_perf = {}
    for r in (raw_results or []):
        rt = r.get('selection', {}).get('race_type', '') or 'Unknown'
        is_w = r.get('result', {}).get('is_winner', False)
        is_p = r.get('result', {}).get('is_placed', False)
        if rt not in race_type_perf:
            race_type_perf[rt] = {'wins': 0, 'placed': 0, 'losses': 0}
        if is_w:
            race_type_perf[rt]['wins'] += 1
        elif is_p:
            race_type_perf[rt]['placed'] += 1
        else:
            race_type_perf[rt]['losses'] += 1
    for rt, s in race_type_perf.items():
        n = s['wins'] + s['placed'] + s['losses']
        s['total'] = n
        s['win_rate'] = round(s['wins'] / n * 100, 1) if n else 0

    _rt_summary = {k: str(v['wins']) + 'W/' + str(v['total']) + 'n=' + str(v['win_rate']) + '%'
                   for k, v in race_type_perf.items()}
    print(f"[sf_learning] odds_roi signals: {odds_roi}")
    print(f"[sf_learning] best_courses: {best_courses}")
    print(f"[sf_learning] race_type_perf: {_rt_summary}")

    table.put_item(Item={
        'bet_date'        : 'LEARNING_INSIGHTS',
        'bet_id'          : 'latest',
        'date'            : date_str,
        'insights'        : json.dumps(insights,        default=str),
        'odds_roi'        : json.dumps(odds_roi,         default=str),
        'best_courses'    : json.dumps(best_courses,     default=str),
        'race_type_perf'  : json.dumps(race_type_perf,   default=str),
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
        # On Mon-Sat (weekdays + Saturday), 0 settled results almost always means
        # sf_results_fetch.py failed to match market_id/selection_id — alert so we
        # catch the results settlement gap before the learning cycle falls too far behind.
        _today_dow = datetime.datetime.utcnow().weekday()  # 0=Mon … 6=Sun
        if _today_dow != 6:  # not Sunday (no UK racing)
            try:
                import boto3 as _boto3
                _ses = _boto3.client('ses', region_name=REGION)
                _ses.send_email(
                    Source='charles.mccarthy@gmail.com',
                    Destination={'ToAddresses': ['charles.mccarthy@gmail.com']},
                    Message={
                        'Subject': {'Data': f'⚠ BetBudAI: Learning cycle found 0 settled results ({date_str})'},
                        'Body': {'Text': {'Data': (
                            f"sf_learning ran for {date_str} but found 0 settled picks.\n\n"
                            f"This usually means sf_results_fetch.py failed to match market_id/selection_id "
                            f"for today's picks. Check:\n"
                            f"  1. CloudWatch logs for surebet-results-fetch Lambda\n"
                            f"  2. DynamoDB SureBetBets — today's picks still show outcome='pending'\n"
                            f"  3. Betfair session token may have expired\n\n"
                            f"Without settled results, learning weights will not update."
                        )}},
                    }
                )
                print(f"[sf_learning] ⚠ 0 settled results alert sent via SES")
            except Exception as _ses_e:
                print(f"[sf_learning] SES alert failed (non-fatal): {_ses_e}")
        print("[sf_learning] No results to learn from — skipping")
        return {'success': True, 'date': date_str, 'results_scanned': 0, 'patterns_found': 0, 'insights': []}

    from learning_engine import analyze_performance_patterns, generate_learning_insights

    print("[sf_learning] Analysing performance patterns ...")
    analysis = analyze_performance_patterns(results)

    print("[sf_learning] Generating insights ...")
    insights = generate_learning_insights(analysis)

    _persist_insights(table, insights, analysis, date_str, raw_results=results)

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

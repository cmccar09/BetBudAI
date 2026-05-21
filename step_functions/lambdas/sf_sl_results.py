"""
Lambda: surebet-sl-results
==========================
Phase : Evening (runs before Betfair results fetch)
Input : {"date": "YYYY-MM-DD"}
Output: {"success": true, "date": "...", "results_recorded": N, "winners": N, "source": "sporting_life"}

Scrapes https://www.sportinglife.com/racing/fast-results/all  (__NEXT_DATA__ JSON)
to get today's race results, then updates any matching DynamoDB picks with
outcome / profit / winner_name etc.

SL fast-results fires as soon as a horse is weighed-in — typically 10–30 min
ahead of Betfair market settlement — so this runs FIRST in the evening pipeline
and catches the majority of picks.  The Betfair step that follows cleans up
any remainder that have a market_id but weren't yet in the SL feed.

Bundled alongside this file in the Lambda ZIP: sl_results_fetcher.py
"""

import datetime
import os
import sys

# Lambda /var/task is the working directory — sl_results_fetcher.py is bundled there
sys.path.insert(0, os.path.dirname(__file__))


def lambda_handler(event, context):
    date_str = event.get('date', datetime.datetime.utcnow().strftime('%Y-%m-%d'))

    print(f'[sf_sl_results] Running for date: {date_str}')

    try:
        # Import here so cold-start errors are surfaced clearly
        import sl_results_fetcher as slr

        # update_results() does everything: fetch SL fast-results, match DynamoDB picks,
        # write outcome / profit / winner_name and returns (updated, winners)
        result = slr.update_results(date_str)

        # update_results returns None (prints inline); count settled picks post-run
        import boto3
        from boto3.dynamodb.conditions import Key, Attr
        db = boto3.resource('dynamodb', region_name=os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1'))
        t  = db.Table('SureBetBets')
        resp = t.query(
            KeyConditionExpression=Key('bet_date').eq(date_str),
            FilterExpression=Attr('show_in_ui').eq(True)
        )
        picks = resp.get('Items', [])
        settled  = [p for p in picks if p.get('outcome') and p['outcome'] not in ('pending', 'PENDING')]
        winners  = [p for p in settled if str(p.get('outcome', '')).lower() in ('win', 'won')]

        print(f'[sf_sl_results] Settled: {len(settled)}, Winners: {len(winners)}')
        return {
            'success'         : True,
            'date'            : date_str,
            'results_recorded': len(settled),
            'winners'         : len(winners),
            'source'          : 'sporting_life',
        }

    except Exception as e:
        import traceback
        print(f'[sf_sl_results] ERROR: {e}')
        traceback.print_exc()
        return {
            'success'         : False,
            'date'            : date_str,
            'results_recorded': 0,
            'winners'         : 0,
            'source'          : 'sporting_life',
            'error'           : str(e),
        }

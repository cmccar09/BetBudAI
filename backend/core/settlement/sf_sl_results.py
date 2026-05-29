"""
Lambda handler for Sporting Life fast-results fetcher
Deployed as: surebet-sl-results
Runs every 30 minutes to fetch and settle race results
"""

import logging
import os
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key, Attr
from core.settlement.sl_results_fetcher import update_results

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')


def _count_settled(date_str):
    """Paginated count of settled UI picks for the date."""
    db = boto3.resource('dynamodb', region_name=REGION)
    t = db.Table('SureBetBets')
    picks, kw = [], {'KeyConditionExpression': Key('bet_date').eq(date_str),
                     'FilterExpression': Attr('show_in_ui').eq(True)}
    while True:
        resp = t.query(**kw)
        picks.extend(resp.get('Items', []))
        if not resp.get('LastEvaluatedKey'):
            break
        kw['ExclusiveStartKey'] = resp['LastEvaluatedKey']
    settled = [p for p in picks if p.get('outcome') and
               str(p['outcome']).lower() not in ('pending', '')]
    winners = [p for p in settled if str(p.get('outcome', '')).lower() in ('win', 'won')]
    return len(settled), len(winners)


def lambda_handler(event, context):
    try:
        target_date = event.get('date') or datetime.now(timezone.utc).strftime('%Y-%m-%d')
        logger.info(f"[sf_sl_results] Starting SL results fetch for {target_date}")

        update_results(target_date)

        results_recorded, winners = _count_settled(target_date)
        logger.info(f"[sf_sl_results] settled={results_recorded} winners={winners}")

        return {
            'success'         : True,
            'date'            : target_date,
            'results_recorded': results_recorded,
            'winners'         : winners,
            'source'          : 'sporting_life',
        }

    except Exception as e:
        logger.error(f"[sf_sl_results] ERROR: {e}", exc_info=True)
        return {
            'success'         : False,
            'date'            : event.get('date', ''),
            'results_recorded': 0,
            'winners'         : 0,
            'source'          : 'sporting_life',
            'error'           : str(e),
        }

"""
Daily ROI Cache Script
Run this once per day (via EventBridge) to pre-calculate and cache the cumulative ROI.
This eliminates the need to calculate ROI on every API request.
"""

import boto3
import json
from datetime import datetime, timedelta, date as _date
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
cache_table = dynamodb.Table('BetBudAICache')

CUMULATIVE_ROI_START = '2026-03-22'


def _is_ranked_daily_pick(item):
    """Check if this is a ranked daily pick that should count toward ROI."""
    raw_show = item.get('show_in_ui')
    show_in_ui = raw_show is True or str(raw_show).strip().lower() == 'true'
    pick_rank = int(item.get('pick_rank', 0) or 0)
    if not (show_in_ui and pick_rank > 0):
        return False
    return True


def _settlement_odds(pick):
    """Return the odds used for settlement (sp_odds if available, else odds)."""
    sp = pick.get('sp_odds')
    if sp and sp > 0:
        return float(sp)
    return float(pick.get('odds', 0) or 0)


def decimal_to_float(obj):
    """Recursively convert Decimal to float."""
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


def calculate_roi():
    """Calculate cumulative ROI - same logic as get_cumulative_roi endpoint."""
    from boto3.dynamodb.conditions import Key

    print(f"[{datetime.now().isoformat()}] Starting ROI calculation...")

    # Query day-by-day
    all_items = []
    start_d = _date.fromisoformat(CUMULATIVE_ROI_START)
    today_d = _date.today()
    cur = start_d

    while cur <= today_d:
        day_kwargs = {
            'KeyConditionExpression': Key('bet_date').eq(str(cur)),
            'ProjectionExpression': 'bet_date, bet_id, horse, course, race_time, show_in_ui, pick_rank, is_learning_pick, outcome, sp_odds, odds, ew_fraction, bet_type',
        }
        while True:
            resp = table.query(**day_kwargs)
            all_items.extend(resp.get('Items', []))
            lek = resp.get('LastEvaluatedKey')
            if not lek:
                break
            day_kwargs['ExclusiveStartKey'] = lek
        cur += timedelta(days=1)

    print(f"Retrieved {len(all_items)} total items from DynamoDB")

    picks = [decimal_to_float(i) for i in all_items]
    picks = [
        p for p in picks
        if p.get('course') and p.get('course') != 'Unknown'
        and p.get('horse') and p.get('horse') != 'Unknown'
        and _is_ranked_daily_pick(p)
        and not p.get('is_learning_pick', False)
        and not p.get('is_dropped', False)
    ]

    print(f"Filtered to {len(picks)} ranked daily picks")

    # Deduplicate by race identity
    seen = {}
    for p in picks:
        k = (p.get('course', ''), p.get('race_time', ''))
        if k not in seen or p.get('bet_date', '') > seen[k].get('bet_date', ''):
            seen[k] = p
    picks = list(seen.values())

    print(f"After deduplication: {len(picks)} unique races")

    # Normalize outcome spellings
    for p in picks:
        oc = (p.get('outcome') or '').lower()
        if oc in ('won',):    p['outcome'] = 'win'
        elif oc in ('lost',): p['outcome'] = 'loss'

    # Level-stakes ROI calculation
    UNIT = 1.0
    total_stake = total_return = 0.0
    wins = places = losses = pending = 0

    for p in picks:
        outcome = (p.get('outcome') or '').lower()
        odds = _settlement_odds(p)
        ef = float(p.get('ew_fraction') or 0.25)

        if outcome == 'win':
            wins += 1
            total_stake += UNIT
            total_return += UNIT * odds
        elif outcome == 'placed':
            places += 1
            total_stake += UNIT
            total_return += (UNIT/2) * (1 + (odds-1) * ef)
        elif outcome == 'loss':
            losses += 1
            total_stake += UNIT
        else:
            pending += 1

    profit = total_return - total_stake
    roi = round((profit / total_stake * 100) if total_stake > 0 else 0, 1)
    settled = wins + places + losses

    result = {
        'success': True,
        'start_date': CUMULATIVE_ROI_START,
        'roi': roi,
        'profit': round(profit, 2),
        'total_stake': round(total_stake, 2),
        'total_return': round(total_return, 2),
        'wins': wins,
        'places': places,
        'losses': losses,
        'pending': pending,
        'settled': settled,
        'methodology_note': 'ROI includes ranked daily picks; featured-meeting picks count only when they win.',
        'cached_at': datetime.now().isoformat(),
    }

    print(f"ROI Calculation Complete: {roi}% over {settled} races")
    return result


def cache_roi(roi_data):
    """Store ROI data in cache table."""
    print(f"[{datetime.now().isoformat()}] Caching ROI data...")

    # Convert floats to Decimal for DynamoDB compatibility
    def convert_floats_to_decimal(obj):
        if isinstance(obj, dict):
            return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_floats_to_decimal(i) for i in obj]
        elif isinstance(obj, float):
            return Decimal(str(obj))
        return obj

    cache_item = {
        'cache_key': 'cumulative_roi',
        'cache_type': 'daily_roi',
        'data': convert_floats_to_decimal(roi_data),
        'updated_at': datetime.now().isoformat(),
        'ttl': int((datetime.now() + timedelta(days=2)).timestamp()),  # Auto-expire after 2 days
    }

    cache_table.put_item(Item=cache_item)
    print(f"[{datetime.now().isoformat()}] ROI cached successfully")


def lambda_handler(event, context):
    """Lambda handler for scheduled execution."""
    try:
        roi_data = calculate_roi()
        cache_roi(roi_data)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'ROI cached successfully',
                'roi': roi_data['roi'],
                'settled': roi_data['settled'],
                'cached_at': roi_data['cached_at']
            })
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }


if __name__ == '__main__':
    # For local testing
    print("Running ROI cache calculation locally...")
    result = lambda_handler({}, {})
    print(json.dumps(json.loads(result['body']), indent=2))

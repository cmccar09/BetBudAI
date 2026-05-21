"""
Field Verification Lambda Handler

ADDED 2026-05-20 (Expert Tipster Review)
Real-time field verification before finalizing picks.
Checks Betfair field against model field at T-30 minutes.
Triggers re-analysis if significant changes detected.

Expected impact: +40-50 winners/week (67 "winner not in field" cases)
"""

import json
import boto3
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
lambda_client = boto3.client('lambda', region_name='eu-west-1')


def get_races_in_window(target_date: str, minutes_ahead: int = 30) -> List[Dict]:
    """
    Get all races starting in the next X minutes.

    Args:
        target_date: Date to check (YYYY-MM-DD)
        minutes_ahead: Look ahead window (default 30)

    Returns:
        List of race records needing verification
    """
    table = dynamodb.Table('SureBetBets')

    now = datetime.now(timezone.utc)
    window_end = now + timedelta(minutes=minutes_ahead)

    # SureBetBets has no GSIs — query by partition key (bet_date) then filter in Python
    from boto3.dynamodb.conditions import Key
    response = table.query(
        KeyConditionExpression=Key('bet_date').eq(target_date)
    )

    all_items = response.get('Items', [])
    now_iso = now.isoformat()
    window_iso = window_end.isoformat()
    return [
        i for i in all_items
        if i.get('race_time') and now_iso <= i['race_time'] <= window_iso
    ]


def fetch_current_betfair_field(market_id: str) -> List[Dict]:
    """
    Fetch current runners from Betfair API.

    Args:
        market_id: Betfair market ID

    Returns:
        List of current runners
    """
    try:
        # Invoke betfair fetcher to get current field
        response = lambda_client.invoke(
            FunctionName='surebet-betfair-fetch',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'market_id': market_id,
                'fetch_type': 'field_only'
            }).encode()
        )

        body = response['Payload'].read()
        result = json.loads(body) if body else {}

        if response.get('FunctionError'):
            logger.error(f"Betfair fetch failed: {result}")
            return []

        # Extract runners from response
        if isinstance(result, dict) and 'body' in result:
            body_data = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            return body_data.get('runners', [])

        return result.get('runners', [])

    except Exception as e:
        logger.error(f"Failed to fetch Betfair field for {market_id}: {e}")
        return []


def compare_fields(original_field: List, current_field: List) -> Dict[str, Any]:
    """
    Compare original analyzed field with current Betfair field.

    Args:
        original_field: Runners from model analysis
        current_field: Current Betfair runners

    Returns:
        Comparison results
    """
    from backend.external.field_change_detector import compare_field_states, extract_runner_ids

    original_ids = extract_runner_ids(original_field)
    current_ids = extract_runner_ids(current_field)

    should_reanalyze, details = compare_field_states(
        original_ids,
        current_ids,
        change_threshold=0.15,  # 15% field change
        nonrunner_count_threshold=2  # 2+ nonrunners
    )

    return {
        'should_reanalyze': should_reanalyze,
        'details': details,
        'original_field_size': len(original_ids),
        'current_field_size': len(current_ids),
        'nonrunners': list(original_ids - current_ids),
        'additions': list(current_ids - original_ids)
    }


def trigger_reanalysis(market_id: str, race_time: str, current_field: List, comparison: Dict) -> Dict:
    """
    Trigger full re-analysis with updated field.

    Args:
        market_id: Betfair market ID
        race_time: Race start time
        current_field: Updated field from Betfair
        comparison: Field comparison results

    Returns:
        Re-analysis results
    """
    try:
        logger.warning(
            f"Triggering re-analysis for {market_id}: "
            f"{len(comparison['nonrunners'])} nonrunners, "
            f"{comparison['details'].get('change_percentage', 0):.1%} field change"
        )

        # Invoke surebet-analysis with force flag and updated field
        response = lambda_client.invoke(
            FunctionName='surebet-analysis',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'market_id': market_id,
                'race_time': race_time,
                'force_reanalysis': True,
                'reanalysis_reason': 'field_change_detected',
                'updated_field': current_field,
                'field_comparison': comparison
            }).encode()
        )

        body = response['Payload'].read()
        result = json.loads(body) if body else {}

        if response.get('FunctionError'):
            logger.error(f"Re-analysis failed: {result}")
            return {'success': False, 'error': result}

        logger.info(f"Re-analysis completed for {market_id}")
        return {'success': True, 'result': result}

    except Exception as e:
        logger.error(f"Failed to trigger re-analysis for {market_id}: {e}")
        return {'success': False, 'error': str(e)}


def lambda_handler(event, context):
    """
    Field verification handler.

    Event payload:
    {
        "target_date": "2026-05-20",
        "verification_window_minutes": 30
    }

    Returns:
        Summary of races checked and re-analyses triggered
    """
    try:
        logger.info(f"Field verification triggered: {json.dumps(event)}")

        target_date = event.get('target_date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        window_minutes = event.get('verification_window_minutes', 30)

        # Get races in verification window
        races_to_check = get_races_in_window(target_date, window_minutes)

        logger.info(f"Found {len(races_to_check)} races in T-{window_minutes} min window")

        verifications = []
        reanalyses_triggered = 0

        for race in races_to_check:
            market_id = race.get('market_id')
            race_time = race.get('race_time')
            original_field = race.get('analyzed_field', [])

            if not market_id or not original_field:
                logger.warning(f"Skipping race {race.get('race_id')}: missing market_id or field")
                continue

            # Fetch current Betfair field
            current_field = fetch_current_betfair_field(market_id)

            if not current_field:
                logger.warning(f"Could not fetch current field for {market_id}")
                continue

            # Compare fields
            comparison = compare_fields(original_field, current_field)

            verification = {
                'market_id': market_id,
                'race_time': race_time,
                'course': race.get('course'),
                'comparison': comparison,
                'verified_at': datetime.now(timezone.utc).isoformat()
            }

            # Trigger re-analysis if needed
            if comparison['should_reanalyze']:
                reanalysis_result = trigger_reanalysis(
                    market_id,
                    race_time,
                    current_field,
                    comparison
                )
                verification['reanalysis'] = reanalysis_result

                if reanalysis_result.get('success'):
                    reanalyses_triggered += 1

            verifications.append(verification)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Field verification complete',
                'target_date': target_date,
                'races_checked': len(races_to_check),
                'verifications_performed': len(verifications),
                'reanalyses_triggered': reanalyses_triggered,
                'verifications': verifications,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

    except Exception as e:
        logger.error(f"Field verification failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'target_date': event.get('target_date')
            })
        }

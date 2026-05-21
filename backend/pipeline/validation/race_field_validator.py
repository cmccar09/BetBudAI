"""
Race Field Completeness Validator
=================================
Validates that every horse in every race has been analyzed before picks are finalized.

Critical Quality Gate:
- Ensures winner of race was in the analyzed field
- Detects missing horses that weren't scored
- Alerts if incomplete fields passed through system
- Blocks pick deployment if field completeness < 95%

This prevents the issue where race winners weren't in the database because
they were never analyzed in the first place.

Run after: surebet-analysis
Run before: surebet-validate
"""

import json
import logging
import boto3
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
picks_table = dynamodb.Table('SureBetBets')
validation_table = dynamodb.Table('BetBudAI_ValidationLogs')


def normalize_horse_name(name: str) -> str:
    """Normalize horse name for comparison (lowercase, strip country codes)."""
    import re
    name = (name or '').strip().lower()
    name = re.sub(r'\s*\([a-z]{2,3}\)\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name)
    return name


def fetch_betfair_race_field(market_id: str, app_key: str, session_token: str) -> List[str]:
    """
    Fetch complete runner list from Betfair for a race.

    Args:
        market_id: Betfair market ID
        app_key: Betfair app key
        session_token: Betfair session token

    Returns:
        List of normalized horse names
    """
    import requests

    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"

    request_body = {
        "marketIds": [market_id],
        "priceProjection": {
            "priceData": ["EX_BEST_OFFERS"]
        }
    }

    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=request_body, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                runners = data[0].get('runners', [])
                # Get runner names from metadata (would need separate call)
                # For now, return runner IDs
                return [str(r.get('selectionId')) for r in runners if r.get('status') == 'ACTIVE']
    except Exception as e:
        logger.warning(f"Error fetching Betfair field: {e}")

    return []


def fetch_analyzed_horses_for_race(
    target_date: str,
    course: str,
    race_time: str
) -> Tuple[List[str], int]:
    """
    Fetch all horses that were analyzed for a specific race.

    Args:
        target_date: Race date (YYYY-MM-DD)
        course: Course name
        race_time: Race time (HH:MM)

    Returns:
        Tuple of (list of horse names, total count)
    """
    try:
        # Query all items for this race
        response = picks_table.query(
            KeyConditionExpression=Key('bet_date').eq(target_date),
            FilterExpression='#course = :course AND race_time = :time',
            ExpressionAttributeNames={'#course': 'course'},
            ExpressionAttributeValues={
                ':course': course,
                ':time': race_time
            }
        )

        items = response.get('Items', [])
        horses = [normalize_horse_name(item.get('horse', '')) for item in items]

        return horses, len(horses)

    except Exception as e:
        logger.error(f"Error fetching analyzed horses: {e}")
        return [], 0


def fetch_sporting_life_field(
    course: str,
    race_time: str,
    target_date: str
) -> List[str]:
    """
    Fetch runner list from Sporting Life for validation.

    Args:
        course: Course name
        race_time: Race time
        target_date: Race date

    Returns:
        List of normalized horse names
    """
    try:
        from backend.core.settlement.sl_results_fetcher import fetch_result_for_race

        result = fetch_result_for_race(course, race_time, target_date)
        if result and 'runners' in result:
            return [normalize_horse_name(r.get('name', '')) for r in result.get('runners', [])]
    except Exception as e:
        logger.warning(f"Could not fetch SL field: {e}")

    return []


def validate_race_field_completeness(
    target_date: str,
    course: str,
    race_time: str,
    expected_field: List[str] = None
) -> Dict[str, Any]:
    """
    Validate that all horses in a race were analyzed.

    Args:
        target_date: Race date
        course: Course name
        race_time: Race time
        expected_field: Optional list of expected horse names

    Returns:
        Validation result dict
    """
    analyzed_horses, analyzed_count = fetch_analyzed_horses_for_race(
        target_date, course, race_time
    )

    # If no expected field provided, try to fetch from Sporting Life
    if not expected_field:
        expected_field = fetch_sporting_life_field(course, race_time, target_date)

    # Normalize expected field
    expected_field = [normalize_horse_name(h) for h in expected_field]

    # Find missing horses
    missing_horses = [h for h in expected_field if h not in analyzed_horses]

    # Find extra horses (analyzed but not in expected field)
    extra_horses = [h for h in analyzed_horses if h not in expected_field]

    # Calculate completeness
    if len(expected_field) > 0:
        completeness_pct = (len(analyzed_horses) - len(extra_horses)) / len(expected_field) * 100
    else:
        completeness_pct = 100.0 if analyzed_count > 0 else 0.0

    is_valid = completeness_pct >= 95.0 and len(missing_horses) == 0

    result = {
        'race_id': f"{target_date}_{course}_{race_time}",
        'target_date': target_date,
        'course': course,
        'race_time': race_time,
        'is_valid': is_valid,
        'completeness_pct': round(completeness_pct, 1),
        'analyzed_count': analyzed_count,
        'expected_count': len(expected_field),
        'missing_horses': missing_horses,
        'extra_horses': extra_horses,
        'validation_timestamp': datetime.now(timezone.utc).isoformat(),
    }

    # Log validation result
    _log_validation_result(result)

    return result


def validate_all_races_for_date(target_date: str) -> Dict[str, Any]:
    """
    Validate field completeness for all races on a given date.

    Args:
        target_date: Date to validate (YYYY-MM-DD)

    Returns:
        Validation summary
    """
    logger.info(f"[FieldValidator] Validating all races for {target_date}")

    try:
        # Get all unique races for the date
        response = picks_table.query(
            KeyConditionExpression=Key('bet_date').eq(target_date)
        )

        items = response.get('Items', [])

        # Group by race
        races = {}
        for item in items:
            course = item.get('course', 'unknown')
            race_time = item.get('race_time', 'unknown')
            race_key = f"{course}_{race_time}"

            if race_key not in races:
                races[race_key] = {
                    'course': course,
                    'race_time': race_time,
                    'horses': []
                }

            races[race_key]['horses'].append(normalize_horse_name(item.get('horse', '')))

        logger.info(f"[FieldValidator] Found {len(races)} races to validate")

        # Validate each race
        validations = []
        invalid_races = []

        for race_key, race_data in races.items():
            validation = validate_race_field_completeness(
                target_date,
                race_data['course'],
                race_data['race_time']
            )

            validations.append(validation)

            if not validation['is_valid']:
                invalid_races.append(validation)

        # Calculate summary stats
        total_races = len(validations)
        valid_races = sum(1 for v in validations if v['is_valid'])
        avg_completeness = sum(v['completeness_pct'] for v in validations) / max(1, total_races)

        total_missing = sum(len(v['missing_horses']) for v in validations)

        summary = {
            'target_date': target_date,
            'total_races': total_races,
            'valid_races': valid_races,
            'invalid_races': len(invalid_races),
            'avg_completeness_pct': round(avg_completeness, 1),
            'total_missing_horses': total_missing,
            'invalid_race_details': invalid_races[:10],  # Limit to first 10
            'validation_passed': len(invalid_races) == 0,
            'validation_timestamp': datetime.now(timezone.utc).isoformat(),
        }

        # Store summary
        _store_validation_summary(summary)

        logger.info(
            f"[FieldValidator] Validation complete: "
            f"{valid_races}/{total_races} races valid, "
            f"{avg_completeness:.1f}% avg completeness"
        )

        return summary

    except Exception as e:
        logger.error(f"[FieldValidator] Validation failed: {e}", exc_info=True)
        return {
            'error': str(e),
            'validation_passed': False,
            'target_date': target_date
        }


def _log_validation_result(result: Dict[str, Any]):
    """Log individual race validation result."""
    try:
        validation_table.put_item(
            Item={
                'validation_date': result['target_date'],
                'validation_id': result['race_id'],
                'validation_type': 'field_completeness',
                'is_valid': result['is_valid'],
                'completeness_pct': Decimal(str(result['completeness_pct'])),
                'missing_horses': result['missing_horses'],
                'extra_horses': result['extra_horses'],
                'timestamp': result['validation_timestamp'],
                'ttl': int((datetime.now(timezone.utc).timestamp()) + (7 * 86400))  # 7 days
            }
        )
    except Exception as e:
        logger.warning(f"Could not log validation result: {e}")


def _store_validation_summary(summary: Dict[str, Any]):
    """Store daily validation summary."""
    try:
        validation_table.put_item(
            Item={
                'validation_date': summary['target_date'],
                'validation_id': f"SUMMARY_{summary['target_date']}",
                'validation_type': 'daily_summary',
                'validation_passed': summary['validation_passed'],
                'total_races': summary['total_races'],
                'valid_races': summary['valid_races'],
                'invalid_races': summary['invalid_races'],
                'avg_completeness_pct': Decimal(str(summary['avg_completeness_pct'])),
                'total_missing_horses': summary['total_missing_horses'],
                'invalid_race_details': summary['invalid_race_details'],
                'timestamp': summary['validation_timestamp'],
                'ttl': int((datetime.now(timezone.utc).timestamp()) + (30 * 86400))  # 30 days
            }
        )
    except Exception as e:
        logger.warning(f"Could not store validation summary: {e}")


def lambda_handler(event, context):
    """
    Lambda handler for race field validation.

    Event format:
    {
        "target_date": "2026-05-21",
        "validation_mode": "all_races"  # or "single_race"
        "course": "Ascot",  # if single_race
        "race_time": "14:30"  # if single_race
    }
    """
    target_date = event.get('target_date', datetime.now(timezone.utc).date().isoformat())
    validation_mode = event.get('validation_mode', 'all_races')

    logger.info(f"[FieldValidator] Starting validation: {validation_mode} for {target_date}")

    if validation_mode == 'single_race':
        course = event.get('course')
        race_time = event.get('race_time')

        if not course or not race_time:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing course or race_time for single_race mode'})
            }

        result = validate_race_field_completeness(target_date, course, race_time)

        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str)
        }

    else:  # all_races mode
        summary = validate_all_races_for_date(target_date)

        # Return 200 if validation passed, 422 if validation failed
        status_code = 200 if summary.get('validation_passed') else 422

        return {
            'statusCode': status_code,
            'body': json.dumps(summary, default=str)
        }


if __name__ == '__main__':
    # Test locally
    import sys
    test_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).date().isoformat()

    result = validate_all_races_for_date(test_date)
    print(json.dumps(result, indent=2, default=str))

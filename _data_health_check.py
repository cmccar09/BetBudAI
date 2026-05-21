"""
BetBudAI Data Feed Health Check
================================
Tests all data sources and reports status for 2026-05-20
"""

import json
import sys
import os
from datetime import datetime, timezone, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_betfair():
    """Test Betfair API connectivity and data availability."""
    print("\n=== BETFAIR API ===")
    try:
        from core.enrichment.betfair_fetcher import get_betfair_session, fetch_betfair_markets

        # Test authentication
        print("Testing authentication...")
        app_key, session_token = get_betfair_session()

        if not app_key or not session_token:
            return {"status": "FAIL", "error": "Authentication failed", "data_available": False}

        print(f"✓ Authenticated (app_key: {app_key[:10]}...)")

        # Test market fetch
        print("Fetching today's markets...")
        markets = fetch_betfair_markets(app_key, session_token, sport='horse_racing')

        if not markets:
            return {"status": "WARN", "error": "No markets found for today", "data_available": False}

        # Count today's races
        today = datetime.now(timezone.utc).date()
        today_markets = [m for m in markets if m.get('marketStartTime', '').startswith(str(today))]

        print(f"✓ Found {len(markets)} total markets, {len(today_markets)} for today")

        return {
            "status": "OK",
            "total_markets": len(markets),
            "today_markets": len(today_markets),
            "data_available": len(markets) > 0,
            "sample_venue": markets[0].get('event', {}).get('venue') if markets else None
        }

    except Exception as e:
        return {"status": "FAIL", "error": str(e), "data_available": False}


def test_racing_api():
    """Test Racing API connectivity and form data."""
    print("\n=== RACING API ===")
    try:
        from core.enrichment.racing_api_client import get_racing_api_creds, get_free_racecards

        # Test credentials
        print("Checking credentials...")
        username, password = get_racing_api_creds()

        if not username:
            return {"status": "FAIL", "error": "No credentials found", "data_available": False}

        print(f"✓ Credentials loaded for: {username}")

        # Test racecard fetch
        print("Fetching today's racecards...")
        racecards = get_free_racecards(day='today', region_codes='gb,ire')

        if not racecards:
            return {"status": "WARN", "error": "No racecards found for today", "data_available": False}

        print(f"✓ Found {len(racecards)} racecards for today")

        # Check data quality
        sample = racecards[0] if racecards else {}
        has_going = bool(sample.get('going'))
        has_runners = len(sample.get('runners', [])) > 0

        return {
            "status": "OK",
            "racecards_today": len(racecards),
            "data_available": True,
            "has_going_data": has_going,
            "has_runner_data": has_runners,
            "sample_course": sample.get('course')
        }

    except Exception as e:
        return {"status": "FAIL", "error": str(e), "data_available": False}


def test_ourhub_api():
    """Test OurHub API enrichment data."""
    print("\n=== OURHUB API ===")
    try:
        from core.enrichment.ourhub_enricher import fetch_ourhub_data

        # Test with today's date
        today_str = datetime.now().strftime('%Y-%m-%d')
        print(f"Fetching OurHub data for {today_str}...")

        data = fetch_ourhub_data(today_str)

        if not data:
            return {"status": "FAIL", "error": "No data returned", "data_available": False}

        course_count = sum(len(v) for v in data.get('course_info', {}).values())
        perf_count = len(data.get('perf_stats', {}))
        pred_count = len(data.get('predictions', {}))

        print(f"✓ Course info: {course_count} entries")
        print(f"✓ Performance stats: {perf_count} races")
        print(f"✓ Predictions: {pred_count} races")

        has_data = course_count > 0 or perf_count > 0 or pred_count > 0

        return {
            "status": "OK" if has_data else "WARN",
            "course_info_entries": course_count,
            "perf_stats_races": perf_count,
            "prediction_races": pred_count,
            "data_available": has_data
        }

    except Exception as e:
        return {"status": "FAIL", "error": str(e), "data_available": False}


def test_dynamodb():
    """Test DynamoDB connectivity and data access."""
    print("\n=== DYNAMODB ===")
    try:
        import boto3
        from botocore.exceptions import ClientError

        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('SureBetBets')

        print("Testing table access...")

        # Test 1: Check weights config
        print("Checking weights configuration...")
        try:
            response = table.get_item(Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'})
            has_weights = 'Item' in response
            weights_count = len(response.get('Item', {}).get('weights', {}))
            print(f"✓ Weights config: {weights_count} weights loaded" if has_weights else "⚠ No weights config found")
        except Exception as e:
            has_weights = False
            weights_count = 0
            print(f"✗ Weights check failed: {e}")

        # Test 2: Check recent picks
        print("Checking recent picks...")
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            from boto3.dynamodb.conditions import Key
            response = table.query(
                IndexName='date-index',
                KeyConditionExpression=Key('bet_date').eq(today),
                Limit=10
            )
            picks_today = response.get('Count', 0)
            print(f"✓ Found {picks_today} picks for today")
        except Exception as e:
            picks_today = 0
            print(f"⚠ Could not query picks: {e}")

        # Test 3: Write test
        print("Testing write access...")
        try:
            test_item = {
                'bet_id': f'HEALTH_CHECK_{int(datetime.now().timestamp())}',
                'bet_date': today,
                'test_timestamp': datetime.now().isoformat()
            }
            table.put_item(Item=test_item)

            # Clean up
            table.delete_item(Key={'bet_id': test_item['bet_id'], 'bet_date': today})
            print("✓ Write/delete successful")
            can_write = True
        except Exception as e:
            print(f"⚠ Write test failed: {e}")
            can_write = False

        return {
            "status": "OK" if (has_weights and can_write) else "WARN",
            "table_accessible": True,
            "weights_available": has_weights,
            "weights_count": weights_count,
            "picks_today": picks_today,
            "can_write": can_write,
            "data_available": has_weights
        }

    except Exception as e:
        return {"status": "FAIL", "error": str(e), "data_available": False}


def main():
    """Run all health checks and generate report."""
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   BetBudAI Data Feed Health Check - 2026-05-20           ║")
    print("╚═══════════════════════════════════════════════════════════╝")

    results = {
        "timestamp": datetime.now().isoformat(),
        "date": "2026-05-20",
        "feeds": {}
    }

    # Run all tests
    results["feeds"]["betfair"] = test_betfair()
    results["feeds"]["racing_api"] = test_racing_api()
    results["feeds"]["ourhub"] = test_ourhub_api()
    results["feeds"]["dynamodb"] = test_dynamodb()

    # Generate summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    all_ok = True
    for feed, result in results["feeds"].items():
        status = result["status"]
        symbol = {"OK": "✓", "WARN": "⚠", "FAIL": "✗"}.get(status, "?")
        print(f"{symbol} {feed.upper()}: {status}")

        if status != "OK":
            all_ok = False
            if "error" in result:
                print(f"  └─ Error: {result['error']}")

    print("="*60)

    # Overall status
    if all_ok:
        print("\n✓ All feeds operational")
    else:
        print("\n⚠ Some feeds need attention")

    # Save detailed report
    report_file = f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed report saved to: {report_file}")

    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())

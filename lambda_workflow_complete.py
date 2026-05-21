"""
AWS Lambda Handler for Complete Betting Workflow
Replaces local laptop execution with fully automated cloud execution
"""
import json
import os
import sys
import boto3
from datetime import datetime, timedelta
from decimal import Decimal

# Import workflow modules
from comprehensive_pick_logic import analyze_horse_comprehensive, get_comprehensive_pick, should_skip_race
from enforce_comprehensive_analysis import validate_pick_for_ui, add_pick_to_ui

def lambda_handler(event, context):
    """
    Main Lambda handler - triggered by EventBridge at 11:00 AM BST daily
    """
    print("="*80)
    print("BETBUDAI WORKFLOW - Lambda Execution Starting")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"Event: {json.dumps(event)}")
    print("="*80)

    try:
        # Run the comprehensive workflow
        result = run_comprehensive_workflow()

        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'picks_generated': result.get('picks_written', 0),
                'races_analyzed': result.get('races_analyzed', 0),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

    except Exception as e:
        print(f"[ERROR] Workflow failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def _get_lock_table():
    db = boto3.resource('dynamodb', region_name='eu-west-1')
    return db.Table('SureBetBets')

def _acquire_workflow_lock(today: str) -> bool:
    """
    Attempt to write a WORKFLOW_RUN_LOCK record for today.
    Returns True  → lock acquired (safe to run).
    Returns False → lock already exists (another run completed today — abort).
    """
    table = _get_lock_table()
    try:
        table.put_item(
            Item={
                'bet_date': today,
                'bet_id': 'WORKFLOW_RUN_LOCK',
                'locked_at': datetime.utcnow().isoformat(),
                'status': 'running',
            },
            ConditionExpression='attribute_not_exists(bet_id)',
        )
        print(f'[LOCK] Workflow lock acquired for {today}')
        return True
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        print(f'[LOCK] Workflow lock already exists for {today} — aborting duplicate run')
        return False
    except Exception as e:
        print(f'[LOCK] WARNING: Could not write workflow lock: {e} — proceeding without lock')
        return True

def _release_workflow_lock(today: str, picks_written: int, large_drops: list):
    """
    Update the lock record to status='completed' and stamp the finish time.
    """
    table = _get_lock_table()
    try:
        table.update_item(
            Key={'bet_date': today, 'bet_id': 'WORKFLOW_RUN_LOCK'},
            UpdateExpression='SET #s = :s, finished_at = :f, picks_written = :p, large_score_drops = :d',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':s': 'completed',
                ':f': datetime.utcnow().isoformat(),
                ':p': picks_written,
                ':d': large_drops,
            },
        )
        print(f'[LOCK] Workflow lock released — {picks_written} picks written')
    except Exception as e:
        print(f'[LOCK] WARNING: Could not release workflow lock: {e}')

def fetch_upcoming_races_from_betfair(hours_ahead=8):
    """
    Fetch upcoming races directly from Betfair API
    Lambda version - no local file dependency
    """
    print("[BETFAIR] Fetching upcoming races...")

    try:
        # Import Betfair fetcher
        from betfair_odds_fetcher import get_live_betfair_races

        races_data = get_live_betfair_races()
        races = races_data.get('races', []) if isinstance(races_data, dict) else races_data

        # Filter to upcoming races
        now = datetime.utcnow()
        upcoming = []

        for race in races:
            race_time_str = race.get('start_time', '')
            if race_time_str:
                try:
                    race_dt = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
                    race_dt_utc = race_dt.replace(tzinfo=None)

                    if now < race_dt_utc < now + timedelta(hours=hours_ahead):
                        upcoming.append(race)
                except Exception as e:
                    print(f"[WARN] Could not parse race time: {race_time_str} - {e}")
                    continue

        print(f"[BETFAIR] Found {len(upcoming)} upcoming races")
        return upcoming

    except Exception as e:
        print(f"[ERROR] Failed to fetch from Betfair: {e}")
        return []

def process_race_comprehensive(race, meeting_context=None):
    """
    Process a single race using comprehensive analysis
    Returns pick dict if suitable horse found, None otherwise
    """
    venue = race.get('venue', 'Unknown')
    race_time = race.get('start_time', '')
    race_name = race.get('market_name', 'Unknown Race')
    runners = race.get('runners', [])

    # Skip filter
    skip, skip_reason = should_skip_race(race)
    if skip:
        print(f"\n[SKIP] {race_time} {venue} | {race_name}")
        print(f"   Reason: {skip_reason}")
        return None

    print(f"\n{'='*80}")
    print(f"ANALYZING: {race_time} - {venue} - {race_name}")
    print(f"Runners: {len(runners)}")
    print(f"{'='*80}")

    # Course stats
    course_stats = {
        'avg_winner_odds': 4.75 if 'wolverhampton' in venue.lower() else 4.65,
        'optimal_range': (4.0, 6.0) if 'wolverhampton' in venue.lower() else (3.5, 7.0)
    }

    # Get comprehensive pick
    pick = get_comprehensive_pick({
        'course': venue,
        'race_time': race_time,
        'race_name': race_name,
        'runners': runners
    }, course_stats, meeting_context=meeting_context)

    if pick:
        # Validate for UI
        is_valid, score, reason = validate_pick_for_ui(pick)

        if is_valid:
            horse_name = pick['horse'].get('name', 'Unknown') if isinstance(pick['horse'], dict) else str(pick['horse'])
            horse_odds = pick['horse'].get('odds', 0) if isinstance(pick['horse'], dict) else 0
            print(f"\n[APPROVED] {horse_name} @ {horse_odds}")
            print(f"   Score: {score}/100")
            return pick
        else:
            horse_name = pick['horse'].get('name', 'Unknown') if isinstance(pick.get('horse'), dict) else str(pick.get('horse', 'Unknown'))
            print(f"\n[REJECTED] {horse_name}")
            print(f"   {reason}")
            return None

    return None

def run_comprehensive_workflow():
    """
    Main workflow: Fetch races from Betfair, analyze comprehensively, add approved picks to UI
    """
    today = str(datetime.now().date())

    print(f"\n{'='*80}")
    print("COMPREHENSIVE BETTING WORKFLOW")
    print(f"{'='*80}")
    print(f"Started: {datetime.utcnow().isoformat()}")
    print(f"Analysis: 7-factor comprehensive (minimum 60/100)")
    print(f"{'='*80}\n")

    # Check workflow lock
    if not _acquire_workflow_lock(today):
        print("[ABORT] Workflow already completed today")
        return {'picks_written': 0, 'races_analyzed': 0, 'status': 'already_completed'}

    try:
        # Fetch upcoming races
        races = fetch_upcoming_races_from_betfair(hours_ahead=8)

        if not races:
            print("[ERROR] No races found - aborting")
            _release_workflow_lock(today, 0, [])
            return {'picks_written': 0, 'races_analyzed': 0, 'status': 'no_races'}

        print(f"\n[INFO] Processing {len(races)} races...\n")

        picks_written = 0
        races_analyzed = 0
        large_drops = []

        # Process each race
        for i, race in enumerate(races, 1):
            races_analyzed += 1
            print(f"\n[{i}/{len(races)}] Processing race...")

            pick = process_race_comprehensive(race, meeting_context=None)

            if pick:
                # Add to UI
                success = add_pick_to_ui(pick, today)
                if success:
                    picks_written += 1
                    print(f"[OK] Pick #{picks_written} added to UI")
                else:
                    print("[WARN] Failed to add pick to UI")

        # Release lock
        _release_workflow_lock(today, picks_written, large_drops)

        print(f"\n{'='*80}")
        print("WORKFLOW COMPLETE")
        print(f"{'='*80}")
        print(f"Races analyzed: {races_analyzed}")
        print(f"Picks written: {picks_written}")
        print(f"Finished: {datetime.utcnow().isoformat()}")
        print(f"{'='*80}\n")

        return {
            'picks_written': picks_written,
            'races_analyzed': races_analyzed,
            'status': 'success'
        }

    except Exception as e:
        print(f"[ERROR] Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        _release_workflow_lock(today, 0, [])
        raise

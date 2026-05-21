"""
surebet-analysis Lambda Handler
================================
Comprehensive 50-signal scoring + pick selection
Called by morning pipeline to analyze today's races
Enhanced with EV-based selection and quality filtering
"""

import json
import boto3
import logging
from datetime import datetime, timezone
from decimal import Decimal

# Import scoring module with Phase 1 signals
try:
    from backend.core.scoring import get_comprehensive_pick, get_dynamic_weights
    SCORING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import from backend.core.scoring: {e}")
    SCORING_AVAILABLE = False
    # Define fallback functions
    def get_comprehensive_pick(*args, **kwargs):
        return None
    def get_dynamic_weights():
        return {}

# Import enhanced pick selector
try:
    from backend.core.enhanced_pick_selector import select_top_picks
    from backend.core.ev_calculator import categorize_by_ev
    from backend.core.race_quality_filter import is_quality_race
    ENHANCED_SELECTOR_AVAILABLE = True
    print("[sf_analysis] Enhanced selector loaded successfully")
except ImportError as e:
    ENHANCED_SELECTOR_AVAILABLE = False
    print(f"[sf_analysis] Enhanced selector not available: {e}")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
picks_table = dynamodb.Table('SureBetBets')


def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def fetch_todays_races_from_db(target_date):
    """
    Fetch today's races from DynamoDB - fallback if not provided in event
    Queries SureBetBets table for cached race data
    """
    try:
        # Try to get cached race data from today's run
        response = picks_table.get_item(
            Key={'date': target_date, 'bet_date': 'RACE_DATA_CACHE'}
        )
        item = response.get('Item')
        if item and item.get('races'):
            races_data = item.get('races')
            # Convert DynamoDB format to dict if needed
            if hasattr(races_data, 'items'):
                return list(races_data)
            return races_data

        logger.warning(f"No cached race data found for {target_date}")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch races from DB: {e}")
        return []


def lambda_handler(event, context):
    """
    Lambda handler for comprehensive race analysis

    Event payload can be:
    1. From pipeline with race data:
       {
           "target_date": "2026-05-20",
           "races": [...],  # Provided by upstream surebet-betfair-fetch
           "force": false
       }

    2. Standalone invocation:
       {
           "target_date": "2026-05-20",
           "force": false
       }

    Returns:
    {
        "statusCode": 200,
        "body": {
            "all_horses": [...],
            "top_picks": [...],
            "analysis_timestamp": "...",
            "phase1_active": true
        }
    }
    """
    try:
        logger.info(f"[surebet-analysis] Starting comprehensive analysis: {json.dumps(event, default=str)[:500]}")

        target_date = event.get('target_date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        force = event.get('force', False)

        # Check if analysis already completed today (unless force=true)
        if not force:
            # Check DynamoDB for existing analysis
            try:
                response = picks_table.scan(
                    FilterExpression='#dt = :date AND begins_with(#bd, :prefix)',
                    ExpressionAttributeNames={'#dt': 'date', '#bd': 'bet_date'},
                    ExpressionAttributeValues={':date': target_date, ':prefix': 'ANALYSIS'}
                )
                if response.get('Items'):
                    logger.info(f"[surebet-analysis] Analysis already exists for {target_date}, skipping")
                    existing_item = response['Items'][0]
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'message': 'Analysis already completed',
                            'cached': True,
                            'target_date': target_date,
                            'picks_count': len(existing_item.get('picks', []))
                        })
                    }
            except Exception as e:
                logger.warning(f"Could not check for existing analysis: {e}")

        # Get races from event or fetch from DB
        races = event.get('races', [])
        if not races:
            logger.info(f"[surebet-analysis] No races in event, fetching from DB...")
            races = fetch_todays_races_from_db(target_date)

        if not races:
            logger.warning(f"[surebet-analysis] No races to analyze for {target_date}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No races to analyze',
                    'target_date': target_date,
                    'races_found': 0
                })
            }

        logger.info(f"[surebet-analysis] Analyzing {len(races)} races")

        # Analyze each race with comprehensive scoring + Phase 1 signals
        all_horses = []
        top_picks = []

        for race in races:
            try:
                # Get comprehensive pick for this race
                pick = get_comprehensive_pick(
                    race,
                    course_stats={
                        'avg_winner_odds': race.get('avg_winner_odds', 3.80),
                        'winners_today': 0
                    }
                )

                if pick:
                    horse_data = pick.get('horse', {})
                    all_horses.append({
                        'name': horse_data.get('name'),
                        'course': race.get('venue') or race.get('course'),
                        'race_time': race.get('time') or race.get('race_time'),
                        'odds': float(horse_data.get('odds', 0)),
                        'score': float(pick.get('score', 0)),
                        'breakdown': pick.get('breakdown', {}),
                        'reasons': pick.get('reasons', []),
                        'market_id': race.get('market_id'),
                    })

                    # Add to top picks if score is high enough
                    if pick.get('score', 0) >= 70:
                        top_picks.append(all_horses[-1])

            except Exception as e:
                logger.error(f"Failed to analyze race {race.get('venue')} {race.get('time')}: {e}")
                continue

        # Sort top picks by score
        top_picks.sort(key=lambda x: x.get('score', 0), reverse=True)

        # Enhanced pick selection with EV filtering and quality gates
        if ENHANCED_SELECTOR_AVAILABLE and len(all_horses) > 0:
            logger.info(f"[surebet-analysis] Using enhanced pick selector with EV filtering")

            # Enrich horses with race data for quality filtering
            for horse in all_horses:
                # Find corresponding race
                for race in races:
                    race_runners = race.get('runners', [])
                    if any(r.get('name') == horse.get('name') for r in race_runners):
                        horse['race_data'] = race
                        break

            # Select picks using expert strategy
            selection_result = select_top_picks(
                all_horses,
                max_picks=5,
                min_long_odds=2  # Require 2 picks at 4/1+
            )

            final_picks = selection_result.get('picks', [])

            # Log selection stats
            stats = selection_result.get('stats', {})
            logger.info(
                f"[surebet-analysis] Enhanced selection: {len(final_picks)} picks selected | "
                f"NAP: {stats.get('nap_count', 0)} | Strong: {stats.get('strong_count', 0)} | "
                f"Value: {stats.get('value_count', 0)} | Long odds (4/1+): {stats.get('long_odds_count', 0)} | "
                f"Expected ROI: {stats.get('expected_roi', 0)}%"
            )

            # Warn if 4/1+ requirement not met
            if not stats.get('long_odds_requirement_met', False):
                logger.warning(
                    f"[surebet-analysis] Only {stats.get('long_odds_count', 0)} picks at 4/1+ "
                    f"(need 2 minimum). Selections may be suboptimal today."
                )

            # Convert enhanced picks back to simple format for DynamoDB
            for pick in final_picks:
                # Add enhanced fields for UI
                pick['bet_tier'] = pick.get('bet_tier', 'standard')
                pick['confidence_pct'] = pick.get('confidence_pct', 0)
                pick['ev_pct'] = pick.get('ev_pct', 0)
                pick['stake_units'] = pick.get('stake_units', 1)
                pick['display_label'] = pick.get('display_label', '')

        else:
            # Fallback: Simple top 5 selection
            logger.info(f"[surebet-analysis] Using simple top-5 selection (enhanced selector not available)")
            final_picks = top_picks[:5]

        logger.info(f"[surebet-analysis] Analysis complete: {len(all_horses)} horses scored, {len(final_picks)} picks selected")

        # Check if Phase 1 signals are active
        weights = get_dynamic_weights()
        phase1_active = 'pace_match_bonus' in weights

        result = {
            'all_horses': all_horses,
            'top_picks': final_picks,
            'picks_count': len(final_picks),
            'horses_analyzed': len(all_horses),
            'races_analyzed': len(races),
            'target_date': target_date,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'phase1_signals_active': phase1_active,
        }

        # Save analysis results to DynamoDB
        try:
            picks_table.put_item(
                Item={
                    'date': target_date,
                    'pick_type': 'daily_analysis',
                    'picks': final_picks,
                    'all_horses': all_horses,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'phase1_active': phase1_active,
                }
            )
            logger.info(f"[surebet-analysis] Saved analysis results to DynamoDB")
        except Exception as e:
            logger.error(f"Failed to save analysis to DynamoDB: {e}")

        return {
            'statusCode': 200,
            'body': json.dumps(result, default=decimal_default)
        }

    except Exception as e:
        logger.error(f"[surebet-analysis] Failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'target_date': event.get('target_date', 'unknown')
            })
        }

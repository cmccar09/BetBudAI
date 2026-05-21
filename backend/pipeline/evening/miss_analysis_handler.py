"""Lambda handler: evening-miss-analysis.

Analyzes yesterday's races to identify miss patterns and model improvement opportunities.
Runs at 20:15 UTC after race results have been fetched.
"""

import json
import boto3
import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter
import sys

# Add core modules to path for imports
sys.path.insert(0, '/opt/python')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Import miss analyzer
try:
    from backend.core.miss_analyzer import analyze_single_miss, aggregate_miss_patterns
    HAS_MISS_ANALYZER = True
except ImportError:
    logger.warning("Could not import miss_analyzer; will use inline functions")
    HAS_MISS_ANALYZER = False


def _fetch_yesterday_races(yesterday_date: str) -> list:
    """Fetch all bets/picks from yesterday's racing."""
    try:
        response = table.query(
            KeyConditionExpression='bet_date = :date',
            ExpressionAttributeValues={':date': yesterday_date}
        )
        items = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression='bet_date = :date',
                ExpressionAttributeValues={':date': yesterday_date},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
        
        return items
    except Exception as e:
        logger.error(f"Error fetching yesterday's races: {e}")
        return []


def _extract_race_data(race_items: list) -> dict:
    """
    Group race items by market_id/race_time and extract picks vs actual winner.
    
    Returns dict: {market_id: {picks: [...], actual_winner: {...}, ...}}
    """
    races = defaultdict(lambda: {
        'picks': [],
        'all_runners': [],
        'actual_winner': None,
        'race_time': None,
        'course': None,
        'nonrunners': []
    })
    
    for item in race_items:
        key = item.get('market_id') or f"{item.get('course')}_{item.get('race_time')}"
        
        races[key]['race_time'] = item.get('race_time')
        races[key]['course'] = item.get('course')
        races[key]['market_id'] = item.get('market_id')
        
        # Add to all runners
        runner_entry = {
            'horse_id': item.get('horse_id'),
            'horse_name': item.get('horse'),
            'score': item.get('comprehensive_score', 0),
            'odds_at_start': item.get('odds_at_start', 0),
            'odds_at_win': item.get('odds_at_win', 0),
            'rank': item.get('pick_rank', 99),
            'potential_improver_flag': item.get('potential_improver_flag', False),
            'trip_suitability_score': item.get('trip_suitability_score', 0),
            'trainer_form_rank': item.get('trainer_form_rank', 0),
            'jockey_form_score': item.get('jockey_form_score', 0),
            'course_wins': item.get('course_wins', 0),
            'distance_wins': item.get('distance_wins', 0),
            'class_drop': item.get('class_drop', False),
            'going_score': item.get('going_score', 0),
            'form_trend': item.get('form_trend', 'stable'),
            'outcome': item.get('outcome'),
        }
        races[key]['all_runners'].append(runner_entry)
        
        # If this is an official pick, add to picks
        pick_rank = item.get('pick_rank', 0)
        if pick_rank > 0:
            races[key]['picks'].append(runner_entry)
        
        # If this is the winner, mark it
        outcome = item.get('outcome', '').lower()
        if outcome == 'won':
            races[key]['actual_winner'] = runner_entry
    
    return races


def _inline_analyze_miss(race_key: str, race_data: dict) -> dict:
    """Inline miss analysis if miss_analyzer import failed."""
    picks = race_data.get('picks', [])
    winner = race_data.get('actual_winner')
    
    if not picks or not winner:
        return {'race_key': race_key, 'status': 'incomplete_data'}
    
    top_pick = picks[0]
    score_gap = winner.get('score', 0) - top_pick.get('score', 0)
    
    # Categorize the miss
    if score_gap > 10:
        category = 'model_miss'
    elif winner.get('potential_improver_flag') and not top_pick.get('potential_improver_flag'):
        category = 'improver_demoted'
    elif winner.get('rank', 99) >= 6:
        category = 'underranked'
    elif winner.get('odds_at_start', 0) > 10:
        category = 'long_shot'
    else:
        category = 'other'
    
    return {
        'race_key': race_key,
        'race_time': race_data.get('race_time'),
        'course': race_data.get('course'),
        'status': 'analyzed',
        'top_pick': {
            'name': top_pick.get('horse_name'),
            'score': top_pick.get('score'),
            'odds': top_pick.get('odds_at_start')
        },
        'actual_winner': {
            'name': winner.get('horse_name'),
            'score': winner.get('score'),
            'odds': winner.get('odds_at_start'),
            'rank': winner.get('rank', 99)
        },
        'categorization': {
            'category': category,
        },
        'score_gap': score_gap,
    }


def lambda_handler(event, context):
    """
    Evening miss analysis handler.
    
    Event payload (optional):
    {
      "target_date": "2026-05-14",  # defaults to yesterday
      "store_insights": true
    }
    """
    try:
        # Default to yesterday
        target_date = event.get('target_date')
        if not target_date:
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            target_date = yesterday.strftime('%Y-%m-%d')
        
        store_insights = event.get('store_insights', True)
        
        logger.info(f"Starting miss analysis for {target_date}")
        
        # Fetch yesterday's races
        race_items = _fetch_yesterday_races(target_date)
        if not race_items:
            logger.info(f"No races found for {target_date}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No races for date',
                    'target_date': target_date,
                    'races_analyzed': 0
                })
            }
        
        # Extract race data structure
        races = _extract_race_data(race_items)
        logger.info(f"Extracted {len(races)} unique races from {len(race_items)} items")
        
        # Analyze each miss
        miss_analyses = []
        hits = []
        for race_key, race_data in races.items():
            picks = race_data.get('picks', [])
            winner = race_data.get('actual_winner')
            
            if not picks or not winner:
                continue
            
            top_pick_id = picks[0].get('horse_id')
            winner_id = winner.get('horse_id')
            
            if top_pick_id == winner_id:
                # Hit
                hits.append({
                    'race': race_key,
                    'pick': picks[0].get('horse_name'),
                    'odds': picks[0].get('odds_at_start')
                })
            else:
                # Miss
                if HAS_MISS_ANALYZER:
                    analysis = analyze_single_miss(race_key, race_data)
                else:
                    analysis = _inline_analyze_miss(race_key, race_data)
                miss_analyses.append(analysis)
        
        # Aggregate patterns
        if miss_analyses:
            # Build category counts inline
            categories = [m.get('categorization', {}).get('category') for m in miss_analyses]
            category_counts = Counter(categories)
            
            score_gaps = [m.get('score_gap', 0) for m in miss_analyses]
            
            aggregation = {
                'total_misses': len(miss_analyses),
                'category_distribution': dict(category_counts),
                'top_miss_reason': category_counts.most_common(1)[0][0] if category_counts else None,
                'avg_score_gap': sum(score_gaps) / len(score_gaps) if score_gaps else 0,
            }
        else:
            aggregation = {'total_misses': 0, 'note': 'Perfect day!'}
        
        total_races = len(hits) + len(miss_analyses)
        hit_rate = len(hits) / total_races if total_races > 0 else 0
        
        # Build response
        response_data = {
            'target_date': target_date,
            'total_races': total_races,
            'hits': len(hits),
            'misses': len(miss_analyses),
            'hit_rate': f"{hit_rate:.1%}",
            'patterns': aggregation,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        logger.info(
            f"Miss analysis complete: {len(hits)} hits, {len(miss_analyses)} misses "
            f"({hit_rate:.1%} hit rate)"
        )
        
        # Optional: Store insights to CloudWatch or DynamoDB
        if store_insights:
            logger.info(f"Insights: {json.dumps(response_data, default=str)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data, default=str)
        }
    
    except Exception as e:
        logger.error(f"Evening miss analysis failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'target_date': event.get('target_date', 'unknown')
            })
        }

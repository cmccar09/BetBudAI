"""
Apply improver boost to featured meeting picks.

Purpose: Enforce improver-boosted scoring for featured meeting to match daily picks optimization.
- Accepts featured course + boosted horses
- Applies improver boost to featured picks
- Re-ranks by new_score
- Returns featured_picks_updated with improver boost applied

Handler: featured-improver-enforcer Lambda
Timeout: 60s
Memory: 256 MB
"""

import json
import boto3
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')


def lambda_handler(event, context):
    """
    Apply improver boost to featured meeting picks.
    
    Input:
    {
        "target_date": "2026-05-15",
        "featured_course": "York",
        "all_horses": [
            {
                "horse": "Highland Oilly",
                "course": "York",
                "race_time": "13:45",
                "comprehensive_score": 87.5,
                "boost_applied": true,
                "boost_amount": 15
            },
            ...
        ]
    }
    
    Output:
    {
        "statusCode": 200,
        "featured_course": "York",
        "featured_picks_updated": [...],
        "boost_summary": {
            "total_featured_picks": 7,
            "picks_boosted": 7,
            "avg_boost_amount": 15.0
        }
    }
    """
    
    try:
        logger.info(f"[featured-improver-enforcer] Input: {json.dumps(event)}")
        
        target_date = event.get('target_date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        featured_course = event.get('featured_course', '').strip()
        all_horses = event.get('all_horses', [])
        
        if not featured_course or not all_horses:
            return {
                'statusCode': 400,
                'message': 'Missing featured_course or all_horses',
                'featured_picks_updated': [],
                'boost_summary': {
                    'total_featured_picks': 0,
                    'picks_boosted': 0,
                    'avg_boost_amount': 0
                }
            }
        
        # Filter to featured course horses only
        featured_horses = [
            h for h in all_horses
            if (h.get('course', '').strip().lower() == featured_course.strip().lower())
        ]
        
        if not featured_horses:
            return {
                'statusCode': 200,
                'message': f'No horses found for featured course: {featured_course}',
                'featured_course': featured_course,
                'featured_picks_updated': [],
                'boost_summary': {
                    'total_featured_picks': 0,
                    'picks_boosted': 0,
                    'avg_boost_amount': 0
                }
            }
        
        # Group by race
        races_by_key = {}
        for horse in featured_horses:
            race_key = (
                horse.get('course', '').strip(),
                horse.get('race_time', '').strip()
            )
            if race_key not in races_by_key:
                races_by_key[race_key] = []
            races_by_key[race_key].append(horse)
        
        # For each featured race, pick the highest-boosted score
        featured_picks = []
        total_boost_amount = 0
        picks_boosted = 0
        
        for race_key, horses_in_race in races_by_key.items():
            # Sort by new_score (boosted) descending
            horses_in_race.sort(
                key=lambda h: float(h.get('new_score', h.get('comprehensive_score', 0)) or 0),
                reverse=True
            )
            
            top_pick = horses_in_race[0]
            
            # Calculate boost amount
            original_score = float(top_pick.get('comprehensive_score', 0) or 0)
            boosted_score = float(top_pick.get('new_score', original_score) or original_score)
            boost_amount = boosted_score - original_score
            
            pick_with_boost = {
                **top_pick,
                'final_score': boosted_score,
                'boost_applied': True,
                'boost_amount': round(boost_amount, 2),
                'improver_enforced': True,
                'featured_rank': len(featured_picks) + 1
            }
            
            featured_picks.append(pick_with_boost)
            
            if boost_amount > 0:
                picks_boosted += 1
                total_boost_amount += boost_amount
        
        # Sort by final score descending
        featured_picks.sort(
            key=lambda p: float(p.get('final_score', 0) or 0),
            reverse=True
        )
        
        # Re-rank after final sort
        for idx, pick in enumerate(featured_picks, start=1):
            pick['featured_rank'] = idx
        
        avg_boost = (
            round(total_boost_amount / picks_boosted, 2)
            if picks_boosted > 0
            else 0
        )
        
        logger.info(
            f"[featured-improver-enforcer] Updated {len(featured_picks)} featured picks "
            f"for {featured_course} ({picks_boosted} boosted, avg +{avg_boost})"
        )
        
        return {
            'statusCode': 200,
            'message': f'Featured improver boost applied to {len(featured_picks)} {featured_course} picks',
            'featured_course': featured_course,
            'featured_picks_updated': featured_picks,
            'boost_summary': {
                'total_featured_picks': len(featured_picks),
                'picks_boosted': picks_boosted,
                'avg_boost_amount': avg_boost,
                'total_boost_amount': round(total_boost_amount, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"[featured-improver-enforcer] Error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'message': f'Error applying featured improver boost: {str(e)}',
            'error': str(e),
            'featured_picks_updated': [],
            'boost_summary': {
                'total_featured_picks': 0,
                'picks_boosted': 0,
                'avg_boost_amount': 0
            }
        }

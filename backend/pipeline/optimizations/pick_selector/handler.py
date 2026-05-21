"""
Elite Pick Selector Lambda Handler

ADDED 2026-05-20 (Expert Tipster Review)
Strict top-5 selection with odds distribution enforcement.
Quality over quantity - professional tipster approach.

Policy:
- Analyze all races, but give tips for ONLY 5 horses
- 3 picks in 2.0-4.0 odds range (bread & butter)
- 2 picks in 4.0-8.0 odds range (value plays)
- NO picks < 1.8 odds (low ROI)
- NO picks > 10.0 odds (too unpredictable)

Expected impact: Higher ROI, clearer user experience
"""

import json
import boto3
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')


def calculate_pick_priority(horse: Dict[str, Any]) -> float:
    """
    Calculate priority score for pick selection.

    Combines:
    - Base score (post-improver-boost)
    - Confidence score
    - Improver boost weighting (1.5x multiplier)

    Args:
        horse: Horse pick data

    Returns:
        Priority score (higher = better)
    """
    base_score = horse.get('score', 0)
    confidence = horse.get('confidence_score', 0)
    improver_boosted = horse.get('improver_boost_applied', False)

    # Priority formula
    priority = base_score * confidence

    # Boost improver-flagged horses by 50%
    if improver_boosted:
        priority *= 1.5

    return priority


def filter_by_odds_range(horses: List[Dict], min_odds: float, max_odds: float) -> List[Dict]:
    """
    Filter horses within specified odds range.

    Args:
        horses: List of horse picks
        min_odds: Minimum odds (inclusive)
        max_odds: Maximum odds (inclusive)

    Returns:
        Filtered list
    """
    return [
        h for h in horses
        if min_odds <= h.get('odds', 0) <= max_odds
    ]


def enforce_odds_distribution(all_horses: List[Dict]) -> List[Dict]:
    """
    Select top 5 picks with enforced odds distribution.

    Distribution policy:
    - 3 picks in 2.0-4.0 range (mid-odds, 40% strike target)
    - 2 picks in 4.0-8.0 range (value odds, 25% strike but higher ROI)

    Args:
        all_horses: All analyzed horses from all races

    Returns:
        5 official picks with balanced odds distribution
    """
    logger.info(f"Applying odds distribution policy to {len(all_horses)} horses")

    # Exclude extreme odds
    filtered = [
        h for h in all_horses
        if 1.8 <= h.get('odds', 0) <= 10.0
    ]

    logger.info(f"After odds filtering (1.8-10.0): {len(filtered)} horses")

    # Split by odds range
    mid_odds = filter_by_odds_range(filtered, 2.0, 4.0)
    value_odds = filter_by_odds_range(filtered, 4.0, 8.0)

    # Sort by priority
    mid_odds.sort(key=calculate_pick_priority, reverse=True)
    value_odds.sort(key=calculate_pick_priority, reverse=True)

    # Select top 3 from mid-range
    official_picks = mid_odds[:3]

    # Select top 2 from value range
    official_picks.extend(value_odds[:2])

    # If we don't have enough in value range, backfill from mid-range
    if len(official_picks) < 5:
        remaining_needed = 5 - len(official_picks)
        backfill = [h for h in mid_odds if h not in official_picks][:remaining_needed]
        official_picks.extend(backfill)

    # If still not enough, take from all filtered horses
    if len(official_picks) < 5:
        remaining_needed = 5 - len(official_picks)
        backfill = [h for h in filtered if h not in official_picks]
        backfill.sort(key=calculate_pick_priority, reverse=True)
        official_picks.extend(backfill[:remaining_needed])

    # Final sort by priority
    official_picks.sort(key=calculate_pick_priority, reverse=True)

    logger.info(
        f"Selected {len(official_picks)} official picks: "
        f"{len([p for p in official_picks if 2.0 <= p.get('odds', 0) <= 4.0])} mid-odds, "
        f"{len([p for p in official_picks if 4.0 < p.get('odds', 0) <= 8.0])} value-odds"
    )

    return official_picks[:5]  # Strict top 5


def mark_official_picks(official_picks: List[Dict], target_date: str) -> int:
    """
    Mark selected picks as official in DynamoDB.

    Args:
        official_picks: List of 5 official picks
        target_date: Date of picks

    Returns:
        Count of picks marked
    """
    table = dynamodb.Table('SureBetBets')
    marked_count = 0

    for pick in official_picks:
        try:
            # Update pick record
            table.update_item(
                Key={
                    'bet_id': pick['bet_id'],
                    'bet_date': target_date
                },
                UpdateExpression='SET pick_type = :official, selection_priority = :priority, updated_at = :now',
                ExpressionAttributeValues={
                    ':official': 'official',
                    ':priority': calculate_pick_priority(pick),
                    ':now': datetime.now(timezone.utc).isoformat()
                }
            )
            marked_count += 1

        except Exception as e:
            logger.error(f"Failed to mark pick {pick.get('bet_id')} as official: {e}")

    return marked_count


def lambda_handler(event, context):
    """
    Elite pick selector handler.

    Event payload:
    {
        "target_date": "2026-05-20",
        "all_horses": [...],  # Optional: provide horses directly
        "fetch_from_db": true  # Or fetch from DynamoDB
    }

    Returns:
        5 official picks with odds distribution enforced
    """
    try:
        logger.info(f"Pick selector triggered: {json.dumps(event)}")

        target_date = event.get('target_date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        all_horses = event.get('all_horses', [])
        fetch_from_db = event.get('fetch_from_db', True)

        # Fetch horses from DynamoDB if not provided
        if not all_horses and fetch_from_db:
            table = dynamodb.Table('SureBetBets')
            response = table.query(
                IndexName='DateIndex',
                KeyConditionExpression='bet_date = :date',
                FilterExpression='attribute_exists(score)',
                ExpressionAttributeValues={':date': target_date}
            )
            all_horses = response.get('Items', [])

        logger.info(f"Selecting from {len(all_horses)} analyzed horses")

        if not all_horses:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No horses available for selection',
                    'target_date': target_date,
                    'official_picks': []
                })
            }

        # Apply odds distribution policy
        official_picks = enforce_odds_distribution(all_horses)

        # Mark in DynamoDB
        marked_count = mark_official_picks(official_picks, target_date)

        # Calculate statistics
        stats = {
            'total_analyzed': len(all_horses),
            'official_picks_count': len(official_picks),
            'mid_odds_count': len([p for p in official_picks if 2.0 <= p.get('odds', 0) <= 4.0]),
            'value_odds_count': len([p for p in official_picks if 4.0 < p.get('odds', 0) <= 8.0]),
            'improver_picks_count': len([p for p in official_picks if p.get('improver_boost_applied')]),
            'average_score': sum(p.get('score', 0) for p in official_picks) / len(official_picks) if official_picks else 0,
            'average_odds': sum(p.get('odds', 0) for p in official_picks) / len(official_picks) if official_picks else 0,
            'picks_marked_in_db': marked_count
        }

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Elite pick selection complete',
                'target_date': target_date,
                'official_picks': [
                    {
                        'bet_id': p.get('bet_id'),
                        'horse_name': p.get('horse_name'),
                        'course': p.get('course'),
                        'race_time': p.get('race_time'),
                        'odds': p.get('odds'),
                        'score': p.get('score'),
                        'confidence': p.get('confidence_score'),
                        'improver_boosted': p.get('improver_boost_applied', False),
                        'priority': calculate_pick_priority(p)
                    }
                    for p in official_picks
                ],
                'statistics': stats,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

    except Exception as e:
        logger.error(f"Pick selection failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'target_date': event.get('target_date')
            })
        }

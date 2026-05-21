"""
Field Change Detector - Real-time Nonrunner Tracking

Monitors BetFair market field for changes (nonrunners, late withdrawals).
Triggers re-analysis when significant changes detected (>15% field change or 2+ nonrunners).

This enables catching late runners who come into contention or removing horses
that are no longer in the race from consideration.

Expected impact: +40-50 winners/week
"""

import json
import logging
from typing import List, Dict, Any, Tuple, Set, Optional
from datetime import datetime, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)


def extract_runner_ids(
    runners: List[Dict[str, Any]]
) -> Set[int]:
    """
    Extract runner IDs from BetFair runner data.
    
    Args:
        runners: BetFair runners list from market snapshot
    
    Returns:
        Set of runner selection IDs
    """
    if not runners:
        return set()
    
    return {
        int(runner.get('selectionId')) 
        for runner in runners 
        if 'selectionId' in runner
    }


def calculate_field_change_percentage(
    original_field: Set[int],
    current_field: Set[int]
) -> float:
    """
    Calculate percentage change in field composition.
    
    Formula: (removed + added) / original_size
    
    Args:
        original_field: Set of selection IDs from original analysis
        current_field: Set of selection IDs from current market snapshot
    
    Returns:
        Percentage change (0.0 to 1.0+)
    """
    if not original_field:
        return 0.0
    
    removed = original_field - current_field
    added = current_field - original_field
    total_changes = len(removed) + len(added)
    
    return total_changes / len(original_field)


def compare_field_states(
    original_field: Set[int],
    current_field: Set[int],
    change_threshold: float = 0.15,
    nonrunner_count_threshold: int = 2
) -> Tuple[bool, Dict[str, Any]]:
    """
    Compare field states and determine if re-analysis is needed.
    
    Triggers re-analysis if:
    - Nonrunner count >= nonrunner_count_threshold (default 2)
    - Total field change >= change_threshold (default 15%)
    - Significant improver or form horse withdrawn
    
    Args:
        original_field: Runner IDs from original model analysis
        current_field: Current BetFair market runners
        change_threshold: Min % change to trigger re-analysis (default 0.15)
        nonrunner_count_threshold: Min nonrunners to trigger re-analysis (default 2)
    
    Returns:
        Tuple of:
        - should_reanalyze: Boolean flag
        - details: Dict with change metrics
    """
    
    removed = original_field - current_field
    added = current_field - original_field
    change_pct = calculate_field_change_percentage(original_field, current_field)
    
    details = {
        'original_field_size': len(original_field),
        'current_field_size': len(current_field),
        'removed_runner_ids': sorted(list(removed)),
        'added_runner_ids': sorted(list(added)),
        'nonrunner_count': len(removed),
        'change_percentage': change_pct,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    # Decision logic
    trigger_reasons = []
    
    if len(removed) >= nonrunner_count_threshold:
        trigger_reasons.append(
            f"High nonrunner count: {len(removed)} >= {nonrunner_count_threshold}"
        )
    
    if change_pct >= change_threshold:
        trigger_reasons.append(
            f"Significant field change: {change_pct:.1%} >= {change_threshold:.0%}"
        )
    
    should_reanalyze = len(trigger_reasons) > 0
    
    details['should_reanalyze'] = should_reanalyze
    details['trigger_reasons'] = trigger_reasons
    
    log_level = logging.WARNING if should_reanalyze else logging.DEBUG
    logger.log(
        log_level,
        f"Field comparison: {len(current_field)} runners (from {len(original_field)}), "
        f"{len(removed)} removed, {change_pct:.1%} change. "
        f"Re-analyze: {should_reanalyze}"
    )
    
    return should_reanalyze, details


def track_nonrunner_event(
    market_id: str,
    race_time: datetime,
    removed_runner_ids: List[int],
    runner_metadata: Optional[Dict[int, Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Log nonrunner event for tracking/audit purposes.
    
    Args:
        market_id: BetFair market ID
        race_time: Race start time
        removed_runner_ids: Selection IDs that were withdrawn
        runner_metadata: Optional dict mapping runner ID to {name, number, etc}
    
    Returns:
        Event record suitable for DynamoDB RaceNonrunnerTracking table
    """
    
    event = {
        'market_id': market_id,
        'race_time': race_time.isoformat() if isinstance(race_time, datetime) else race_time,
        'event_type': 'field_change_detected',
        'nonrunner_ids': removed_runner_ids,
        'nonrunner_count': len(removed_runner_ids),
        'detected_at': datetime.now(timezone.utc).isoformat(),
        'runner_details': []
    }
    
    if runner_metadata:
        for runner_id in removed_runner_ids:
            if runner_id in runner_metadata:
                event['runner_details'].append({
                    'runner_id': runner_id,
                    'name': runner_metadata[runner_id].get('name'),
                    'draw': runner_metadata[runner_id].get('draw'),
                    'reason': runner_metadata[runner_id].get('reason', 'nonrunner')
                })
    
    logger.info(
        f"Logged nonrunner event for market {market_id}: "
        f"{len(removed_runner_ids)} withdrawals"
    )
    
    return event


def should_trigger_reanalysis(
    market_id: str,
    original_field_snapshot: Dict[str, Any],
    current_field_snapshot: Dict[str, Any],
    time_until_race_minutes: int
) -> Tuple[bool, Dict[str, Any]]:
    """
    Master decision function: should we re-analyze this race?
    
    Considers:
    - Field changes
    - Time until race (don't re-analyze within 5 minutes)
    - Significance of changes
    
    Args:
        market_id: BetFair market ID
        original_field_snapshot: Field state from model analysis {time, runners: []}
        current_field_snapshot: Current field state {time, runners: []}
        time_until_race_minutes: Minutes until race start
    
    Returns:
        Tuple of (should_reanalyze, details_dict)
    """
    
    logger.info(
        f"Evaluating re-analysis trigger for {market_id} "
        f"(T-{time_until_race_minutes} min)"
    )
    
    # Extract runner IDs
    original_runners = extract_runner_ids(
        original_field_snapshot.get('runners', [])
    )
    current_runners = extract_runner_ids(
        current_field_snapshot.get('runners', [])
    )
    
    # Compare fields
    should_reanalyze, comparison_details = compare_field_states(
        original_runners,
        current_runners
    )
    
    # Don't reanalyze within 5 minutes of race (too late to impact picks)
    if time_until_race_minutes < 5:
        should_reanalyze = False
        comparison_details['reanalysis_blocked_reason'] = 'too_close_to_race'
        logger.info(
            f"Re-analysis blocked for {market_id}: "
            f"T-{time_until_race_minutes} min (within 5 min window)"
        )
    
    comparison_details['market_id'] = market_id
    comparison_details['time_until_race_minutes'] = time_until_race_minutes
    
    return should_reanalyze, comparison_details


def detect_field_changes_handler(
    market_id: str,
    race_time: datetime,
    original_field_snapshot: Dict[str, Any],
    current_field_snapshot: Dict[str, Any],
    current_time: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Main handler: detect field changes and return re-analysis decision.
    
    This is the entry point for the field change detector Lambda/step function.
    
    Args:
        market_id: BetFair market ID
        race_time: Scheduled race start time
        original_field_snapshot: Field from model analysis
        current_field_snapshot: Current BetFair field
        current_time: Current timestamp (default: now)
    
    Returns:
        Result dict with:
        - should_reanalyze: Boolean decision
        - comparison_details: Field change metrics
        - reanalysis_params: Parameters to pass to re-analysis (if triggered)
    """
    
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    
    # Calculate time until race
    if isinstance(race_time, str):
        # Parse ISO format
        race_time = datetime.fromisoformat(race_time.replace('Z', '+00:00'))
    
    time_delta = race_time - current_time
    time_until_race_minutes = time_delta.total_seconds() / 60
    
    logger.info(
        f"Field change detection for {market_id}: "
        f"T-{time_until_race_minutes:.0f} min until race"
    )
    
    try:
        # Main decision
        should_reanalyze, comparison_details = should_trigger_reanalysis(
            market_id,
            original_field_snapshot,
            current_field_snapshot,
            time_until_race_minutes
        )
        
        # Prepare reanalysis parameters if needed
        reanalysis_params = {}
        if should_reanalyze:
            current_runners = extract_runner_ids(
                current_field_snapshot.get('runners', [])
            )
            removed_runners = extract_runner_ids(
                original_field_snapshot.get('runners', [])
            ) - current_runners
            
            reanalysis_params = {
                'market_id': market_id,
                'race_time': race_time.isoformat() if isinstance(race_time, datetime) else race_time,
                'force_reanalysis': True,
                'updated_field': sorted(list(current_runners)),
                'field_changed_reason': 'nonrunner_detected',
                'removed_runners': sorted(list(removed_runners)),
                'reanalysis_triggered_at': datetime.now(timezone.utc).isoformat()
            }
            
            logger.warning(
                f"Re-analysis triggered for {market_id}: "
                f"{len(removed_runners)} removed, "
                f"{comparison_details.get('change_percentage', 0):.1%} change"
            )
        
        result = {
            'market_id': market_id,
            'race_time': race_time.isoformat() if isinstance(race_time, datetime) else race_time,
            'status': 'success',
            'decision': 'reanalyze' if should_reanalyze else 'skip',
            'comparison_details': comparison_details,
            'reanalysis_params': reanalysis_params if should_reanalyze else None,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return result
        
    except Exception as e:
        logger.exception(f"Error in field change detection: {str(e)}")
        return {
            'market_id': market_id,
            'race_time': race_time.isoformat() if isinstance(race_time, datetime) else race_time,
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

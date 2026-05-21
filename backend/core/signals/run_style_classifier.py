"""
RUN STYLE CLASSIFIER
====================
Classifies horses as FRONT_RUNNER, STALKER, or CLOSER based on racing pattern.

Data sources:
  - form_runs position data
  - Race comments from Sporting Life
  - Position at various stages (if available)

Implementation: FREE - built from existing data
Expected Impact: +5-8% strike rate
"""

import re
from typing import List, Dict, Optional


def classify_run_style(form_runs: List[Dict], form_string: str = '') -> str:
    """
    Classify horse's preferred running style from race history.

    Returns:
        'FRONT_RUNNER' - Leads early, likes to set pace
        'STALKER' - Tracks leaders, sits 2nd-4th
        'CLOSER' - Held up, finishes from behind
        'UNKNOWN' - Insufficient data
    """
    if not form_runs or len(form_runs) < 2:
        return 'UNKNOWN'

    # Analyze race comments for position keywords
    front_count = 0
    held_up_count = 0
    tracked_count = 0

    for run in form_runs[-6:]:  # Last 6 runs
        comment = str(run.get('comment', '')).lower()
        position = run.get('position')

        # Front running indicators
        if any(phrase in comment for phrase in [
            'led', 'made all', 'front', 'set pace', 'disputed lead',
            'prominent', 'chased leader', 'raced keenly'
        ]):
            front_count += 1

        # Held up / closer indicators
        elif any(phrase in comment for phrase in [
            'held up', 'rear', 'slowly away', 'behind', 'towards rear',
            'stayed on', 'headway', 'ran on', 'finished well',
            'closed', 'progress'
        ]):
            held_up_count += 1

        # Stalker indicators (tracked leaders, mid-division)
        elif any(phrase in comment for phrase in [
            'tracked', 'chased', 'mid-division', 'handy', 'close up'
        ]):
            tracked_count += 1

        # Infer from finishing position if no comments
        # Front runners tend to finish in first 3 positions or fade badly
        # Closers show improvement from poor early positions
        elif position:
            if position <= 2:
                # Could be front runner or closer who got there
                # Check if there's a pattern of early positions
                pass

    # Determine primary style based on frequency
    total_runs = len([r for r in form_runs[-6:] if r.get('comment') or r.get('position')])

    if total_runs < 2:
        return 'UNKNOWN'

    # Calculate percentages
    front_pct = front_count / total_runs if total_runs > 0 else 0
    held_up_pct = held_up_count / total_runs if total_runs > 0 else 0
    tracked_pct = tracked_count / total_runs if total_runs > 0 else 0

    # Classification thresholds
    if front_pct >= 0.40:  # 40%+ of runs show front running
        return 'FRONT_RUNNER'
    elif held_up_pct >= 0.35:  # 35%+ show closer pattern
        return 'CLOSER'
    elif tracked_pct >= 0.30 or (front_pct < 0.40 and held_up_pct < 0.35):
        return 'STALKER'  # Default to stalker for mid-pack runners

    return 'UNKNOWN'


def predict_race_pace(runners: List[Dict]) -> str:
    """
    Predict expected race pace based on runner styles.

    Returns:
        'CONTESTED' - Multiple front runners, fast early pace
        'STEADY' - Few front runners, moderate pace
        'SLOW' - No clear pace angle, tactical race
    """
    if not runners:
        return 'STEADY'

    # Count horses with front running tendencies
    front_runners = sum(1 for r in runners if r.get('run_style') == 'FRONT_RUNNER')
    total_runners = len(runners)

    if total_runners == 0:
        return 'STEADY'

    front_runner_pct = front_runners / total_runners

    if front_runners >= 3:  # 3+ front runners = speed duel
        return 'CONTESTED'
    elif front_runners <= 1:  # 0-1 front runners = lack of pace
        return 'SLOW'
    else:  # 2 front runners = moderate pace
        return 'STEADY'


def calculate_pace_match_bonus(run_style: str, predicted_pace: str, weights: Dict) -> tuple[int, str]:
    """
    Calculate bonus/penalty for run style matching predicted race pace.

    Perfect matches:
        - CLOSER in CONTESTED pace (pace to close into) → +12pts
        - FRONT_RUNNER in SLOW pace (solo lead) → +10pts

    Poor matches:
        - CLOSER in SLOW pace (no pace to close into) → -8pts
        - FRONT_RUNNER in CONTESTED pace (speed duel) → -8pts

    Returns:
        (points, reason_string)
    """
    if run_style == 'UNKNOWN' or predicted_pace == 'STEADY':
        return 0, ''

    # Positive scenarios
    if run_style == 'CLOSER' and predicted_pace == 'CONTESTED':
        pts = int(weights.get('pace_match_bonus', 12))
        return pts, f"Closer in contested pace (perfect setup): +{pts}pts"

    if run_style == 'FRONT_RUNNER' and predicted_pace == 'SLOW':
        pts = int(weights.get('pace_match_bonus', 12)) - 2  # Slightly less than closer
        return pts, f"Front runner in steady pace (solo lead likely): +{pts}pts"

    # Negative scenarios
    if run_style == 'CLOSER' and predicted_pace == 'SLOW':
        pts = int(weights.get('pace_mismatch_penalty', 8))
        return -pts, f"Closer in slow pace (no pace to close into): -{pts}pts"

    if run_style == 'FRONT_RUNNER' and predicted_pace == 'CONTESTED':
        pts = int(weights.get('pace_mismatch_penalty', 8))
        return -pts, f"Front runner in speed duel (will tire): -{pts}pts"

    # Stalker is versatile, small bonus in any scenario
    if run_style == 'STALKER':
        pts = 4
        return pts, f"Versatile stalker (adapts to pace): +{pts}pts"

    return 0, ''


def enrich_runners_with_run_style(runners: List[Dict]) -> List[Dict]:
    """
    Add run_style classification to each runner.
    Modifies runners in place and returns the list.
    """
    for runner in runners:
        form_runs = runner.get('form_runs', [])
        form_string = runner.get('form', '')

        run_style = classify_run_style(form_runs, form_string)
        runner['run_style'] = run_style

    return runners


# Example usage:
if __name__ == '__main__':
    # Test classification
    test_runs = [
        {'comment': 'led throughout, won going away', 'position': 1},
        {'comment': 'made all, clear 2f out', 'position': 1},
        {'comment': 'prominent, led 3f out', 'position': 2},
        {'comment': 'chased leaders, every chance', 'position': 3},
    ]

    style = classify_run_style(test_runs)
    print(f"Classification: {style}")
    # Expected: FRONT_RUNNER (3/4 runs show leading/prominent)

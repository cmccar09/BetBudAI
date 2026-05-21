"""
Enhanced Pick Selector
======================
Expert betting strategy with EV-based selection, confidence tiers,
and max 5 picks per day (2 must be 4/1+).

Implements professional betting principles:
1. Quality over quantity (2-4 picks max)
2. Only bet when clear edge exists (EV > +15%)
3. Confidence-based tiers (NAP/Strong/Value)
4. Race quality filtering
5. Kelly Criterion staking
"""

from typing import List, Dict, Tuple
from decimal import Decimal

try:
    from .ev_calculator import (
        categorize_by_ev,
        calculate_kelly_stake,
        score_to_win_probability
    )
    from .race_quality_filter import (
        is_quality_race,
        should_recommend_each_way
    )
except ImportError:
    from ev_calculator import (
        categorize_by_ev,
        calculate_kelly_stake,
        score_to_win_probability
    )
    from race_quality_filter import (
        is_quality_race,
        should_recommend_each_way
    )


def select_top_picks(all_scored_horses: List[Dict], max_picks: int = 5,
                    min_long_odds: int = 2, long_odds_threshold: float = 5.0) -> Dict:
    """
    Select top daily picks with expert betting strategy.

    Strategy:
    1. Filter to quality races only
    2. Calculate EV for each pick
    3. Categorize into tiers (NAP/Strong/Value)
    4. Select max 5 picks with 2x 4/1+ requirement
    5. Add staking recommendations

    Args:
        all_scored_horses: List of scored horses from all races
        max_picks: Maximum picks to return (default 5)
        min_long_odds: Minimum number of 4/1+ picks required (default 2)
        long_odds_threshold: Decimal odds for "long odds" (default 5.0 = 4/1)

    Returns:
        {
            'picks': [...],  # Final picks with tiers
            'nap': {...},  # Best bet of the day
            'strong': [{...}],  # Strong selections
            'value': [{...}],  # Value plays
            'stats': {...},
            'filtered_count': int,
            'filter_reasons': {...}
        }
    """
    # Track filtering
    total_candidates = len(all_scored_horses)
    filtered_low_ev = 0
    filtered_bad_race = 0
    filtered_low_score = 0

    # Step 1: Filter to quality races
    quality_candidates = []
    for horse in all_scored_horses:
        race_data = horse.get('race_data', {})
        is_good, skip_reason = is_quality_race(race_data)

        if not is_good:
            filtered_bad_race += 1
            continue

        quality_candidates.append(horse)

    print(f"[PICK SELECTOR] Quality filter: {len(quality_candidates)}/{total_candidates} horses from bet-worthy races")

    # Step 2: Calculate EV and categorize
    categorized = []
    for horse in quality_candidates:
        score = float(horse.get('comprehensive_score') or horse.get('analysis_score') or 0)
        decimal_odds = float(horse.get('odds', 0))

        # Minimum score threshold (below 70 = unreliable)
        if score < 70:
            filtered_low_score += 1
            continue

        # Calculate EV and categorize
        ev_analysis = categorize_by_ev(score, decimal_odds)

        # Skip if EV says "no_bet"
        if ev_analysis['tier'] == 'no_bet':
            filtered_low_ev += 1
            continue

        # Calculate Kelly stake
        win_prob = ev_analysis['win_probability']
        kelly_stake = calculate_kelly_stake(win_prob, decimal_odds)

        # Check if Each-Way recommended
        n_runners = len(horse.get('race_data', {}).get('runners', []))
        ew_recommended, ew_reason = should_recommend_each_way(
            decimal_odds, n_runners, ev_analysis['confidence']
        )

        # Enrich horse data with EV analysis
        enriched = {
            **horse,
            'bet_tier': ev_analysis['tier'],
            'confidence_pct': ev_analysis['confidence'],
            'ev_pct': ev_analysis['ev_pct'],
            'win_probability': ev_analysis['win_probability'],
            'stake_units': ev_analysis['stake_units'],
            'kelly_stake': kelly_stake,
            'ev_reason': ev_analysis['reason'],
            'show_prominence': ev_analysis['show_prominence'],
            'bet_type': 'each_way' if ew_recommended else 'win',
            'ew_reason': ew_reason if ew_recommended else None,
            'n_runners': n_runners
        }

        categorized.append(enriched)

    print(f"[PICK SELECTOR] EV filter: {len(categorized)} horses with positive EV")

    if not categorized:
        return {
            'picks': [],
            'nap': None,
            'strong': [],
            'value': [],
            'stats': {
                'total_analyzed': total_candidates,
                'quality_races': len(quality_candidates),
                'positive_ev': 0,
                'filtered_low_ev': filtered_low_ev,
                'filtered_bad_race': filtered_bad_race,
                'filtered_low_score': filtered_low_score
            },
            'message': 'No picks with sufficient edge found today'
        }

    # Step 3: Sort by EV within each tier
    categorized.sort(key=lambda x: (
        {'nap': 3, 'strong': 2, 'value': 1}.get(x['bet_tier'], 0),  # Tier priority
        x['ev_pct']  # Then by EV within tier
    ), reverse=True)

    # Step 4: Select picks with 4/1+ requirement
    nap_picks = [p for p in categorized if p['bet_tier'] == 'nap']
    strong_picks = [p for p in categorized if p['bet_tier'] == 'strong']
    value_picks = [p for p in categorized if p['bet_tier'] == 'value']

    # Get long odds picks (4/1+) across all tiers
    long_odds_picks = [p for p in categorized if float(p.get('odds', 0)) >= long_odds_threshold]
    standard_odds_picks = [p for p in categorized if float(p.get('odds', 0)) < long_odds_threshold]

    final_picks = []

    # Ensure we have 2 long odds picks first (requirement)
    if len(long_odds_picks) >= min_long_odds:
        # Take top 2 long odds by EV
        final_picks.extend(long_odds_picks[:min_long_odds])
        print(f"[PICK SELECTOR] Added {min_long_odds} required 4/1+ picks")
    elif len(long_odds_picks) > 0:
        # Take what we have
        final_picks.extend(long_odds_picks)
        print(f"[PICK SELECTOR] WARNING: Only {len(long_odds_picks)} picks at 4/1+ (need {min_long_odds})")

    # Fill remaining slots (up to max_picks) with best by EV
    remaining_slots = max_picks - len(final_picks)
    if remaining_slots > 0:
        # Get picks not already selected
        selected_ids = {p['bet_id'] for p in final_picks}
        remaining_candidates = [p for p in categorized if p['bet_id'] not in selected_ids]

        # Sort by EV and take top N
        remaining_candidates.sort(key=lambda x: x['ev_pct'], reverse=True)
        final_picks.extend(remaining_candidates[:remaining_slots])

    # Cap at max_picks
    final_picks = final_picks[:max_picks]

    print(f"[PICK SELECTOR] Final selection: {len(final_picks)} picks")

    # Step 5: Assign display ranking
    # Sort by tier priority, then EV
    final_picks.sort(key=lambda x: (
        {'nap': 3, 'strong': 2, 'value': 1}.get(x['bet_tier'], 0),
        x['ev_pct']
    ), reverse=True)

    # Add pick rank
    for idx, pick in enumerate(final_picks, 1):
        pick['pick_rank'] = idx
        pick['display_label'] = _get_display_label(pick, idx)

    # Identify NAP (best bet)
    nap = final_picks[0] if final_picks and final_picks[0]['bet_tier'] == 'nap' else None

    # Group by tier
    strong = [p for p in final_picks if p['bet_tier'] == 'strong']
    value = [p for p in final_picks if p['bet_tier'] == 'value']

    # Calculate stats
    total_stake = sum(p['stake_units'] for p in final_picks)
    avg_odds = sum(float(p.get('odds', 0)) for p in final_picks) / len(final_picks) if final_picks else 0
    long_odds_count = sum(1 for p in final_picks if float(p.get('odds', 0)) >= long_odds_threshold)

    return {
        'picks': final_picks,
        'nap': nap,
        'strong': strong,
        'value': value,
        'stats': {
            'total_analyzed': total_candidates,
            'quality_races': len(quality_candidates),
            'positive_ev': len(categorized),
            'final_picks': len(final_picks),
            'nap_count': 1 if nap else 0,
            'strong_count': len(strong),
            'value_count': len(value),
            'total_stake_units': total_stake,
            'avg_odds': round(avg_odds, 2),
            'long_odds_count': long_odds_count,
            'long_odds_requirement_met': long_odds_count >= min_long_odds,
            'filtered_low_ev': filtered_low_ev,
            'filtered_bad_race': filtered_bad_race,
            'filtered_low_score': filtered_low_score,
            'expected_roi': _calculate_expected_roi(final_picks)
        },
        'message': f'{len(final_picks)} picks with positive EV ({long_odds_count} at 4/1+)'
    }


def _get_display_label(pick: Dict, rank: int) -> str:
    """Generate display label for pick."""
    tier = pick.get('bet_tier', '')
    if tier == 'nap':
        return f"🔥 NAP - Best Bet"
    elif tier == 'strong':
        return f"💪 Strong Selection #{rank}"
    elif tier == 'value':
        return f"💎 Value Play"
    else:
        return f"Pick #{rank}"


def _calculate_expected_roi(picks: List[Dict]) -> float:
    """Calculate expected ROI across all picks."""
    if not picks:
        return 0.0

    total_stake = sum(p['stake_units'] for p in picks)
    total_expected_return = sum(
        p['stake_units'] * p['win_probability'] * float(p.get('odds', 0))
        for p in picks
    )

    roi = ((total_expected_return - total_stake) / total_stake) * 100 if total_stake > 0 else 0
    return round(roi, 1)


def format_pick_for_ui(pick: Dict) -> Dict:
    """Format pick for UI display with all betting information."""
    horse_name = pick.get('horse', pick.get('name', 'Unknown'))
    course = pick.get('course', 'Unknown')
    race_time = pick.get('race_time', '')
    decimal_odds = float(pick.get('odds', 0))

    # Convert decimal to fractional odds for display
    fractional_odds = _decimal_to_fractional(decimal_odds)

    # Format staking info
    stake_units = pick.get('stake_units', 0)
    kelly_stake = pick.get('kelly_stake', 0)
    bet_type = pick.get('bet_type', 'win')

    # Calculate returns
    win_return = stake_units * decimal_odds if decimal_odds > 0 else 0
    win_profit = win_return - stake_units

    return {
        # Basic info
        'pick_rank': pick.get('pick_rank', 0),
        'display_label': pick.get('display_label', ''),
        'horse': horse_name,
        'course': course,
        'race_time': race_time,

        # Odds
        'odds_decimal': decimal_odds,
        'odds_fractional': fractional_odds,
        'odds_display': f"{fractional_odds} ({decimal_odds:.2f})",

        # Confidence & EV
        'bet_tier': pick.get('bet_tier', ''),
        'confidence_pct': pick.get('confidence_pct', 0),
        'ev_pct': pick.get('ev_pct', 0),
        'win_probability': pick.get('win_probability', 0),
        'ev_reason': pick.get('ev_reason', ''),

        # Staking
        'stake_units': stake_units,
        'kelly_stake': kelly_stake,
        'bet_type': bet_type,
        'ew_recommended': bet_type == 'each_way',
        'ew_reason': pick.get('ew_reason', ''),

        # Returns
        'potential_return': round(win_return, 2),
        'potential_profit': round(win_profit, 2),

        # Analysis
        'score': pick.get('comprehensive_score', pick.get('analysis_score', 0)),
        'reasons': pick.get('reasons', pick.get('why_selected', [])),
        'breakdown': pick.get('analysis_breakdown', {}),

        # Race info
        'n_runners': pick.get('n_runners', 0),
        'race_type': pick.get('race_type', ''),

        # Original data
        'bet_id': pick.get('bet_id', ''),
        'selection_id': pick.get('selection_id', ''),
        'trainer': pick.get('trainer', ''),
        'jockey': pick.get('jockey', ''),
        'form': pick.get('form', '')
    }


def _decimal_to_fractional(decimal_odds: float) -> str:
    """Convert decimal odds to fractional display."""
    if decimal_odds <= 1.0:
        return "EVS"

    # Calculate fractional odds
    numerator = decimal_odds - 1
    denominator = 1.0

    # Try common fractions
    common_fractions = [
        (1, 2), (4, 5), (5, 6), (10, 11), (1, 1),  # Evens to EVS
        (11, 10), (6, 5), (5, 4), (11, 8), (6, 4), (13, 8), (7, 4), (15, 8), (2, 1),  # 2/1 range
        (9, 4), (5, 2), (11, 4), (3, 1), (100, 30), (7, 2), (4, 1), (9, 2), (5, 1),  # 3/1-5/1
        (11, 2), (6, 1), (13, 2), (7, 1), (15, 2), (8, 1), (9, 1), (10, 1),  # 6/1-10/1
        (12, 1), (14, 1), (16, 1), (18, 1), (20, 1), (25, 1), (33, 1), (40, 1), (50, 1)  # Long odds
    ]

    best_diff = float('inf')
    best_fraction = None

    for num, den in common_fractions:
        frac_decimal = (num / den) + 1
        diff = abs(frac_decimal - decimal_odds)
        if diff < best_diff:
            best_diff = diff
            best_fraction = (num, den)

    if best_fraction:
        num, den = best_fraction
        if num == den:
            return "EVS"
        return f"{num}/{den}"

    # Fallback: approximate
    if decimal_odds >= 100:
        approx = int(decimal_odds - 1)
        return f"{approx}/1"

    return f"{decimal_odds - 1:.1f}/1"

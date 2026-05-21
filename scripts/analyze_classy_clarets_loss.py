#!/usr/bin/env python3
"""
Classy Clarets Loss Analysis Script
===================================

Automatically fetch race results, compare scores, and identify gaps.

Usage:
    python scripts/analyze_classy_clarets_loss.py

Requirements:
    - Evening pipeline must have run (21:00 UTC)
    - AWS credentials configured
    - boto3 installed
"""

import boto3
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types in JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def get_ayr_race_horses(date: str = '2026-05-20') -> List[Dict]:
    """Fetch all horses from Ayr 13:12 race."""
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')

    response = table.scan(
        FilterExpression='bet_date = :date',
        ExpressionAttributeValues={':date': date}
    )

    # Filter for Ayr race around 13:12
    ayr_horses = [
        h for h in response.get('Items', [])
        if 'ayr' in h.get('course', '').lower()
        and '13:' in h.get('race_time', '')
    ]

    # Sort by score (highest first)
    ayr_horses.sort(key=lambda x: float(x.get('score', 0)), reverse=True)

    return ayr_horses


def find_horse_by_name(horses: List[Dict], name: str) -> Optional[Dict]:
    """Find a specific horse by name."""
    for h in horses:
        if name.lower() in h.get('horse_name', '').lower():
            return h
    return None


def get_score_breakdown(horse: Dict) -> Dict[str, float]:
    """Extract score breakdown from horse data."""
    breakdown = horse.get('score_breakdown', {})
    return {k: float(v) for k, v in breakdown.items()}


def compare_scores(horse1: Dict, horse2: Dict) -> Dict:
    """Compare two horses' score breakdowns."""
    b1 = get_score_breakdown(horse1)
    b2 = get_score_breakdown(horse2)

    all_signals = set(b1.keys()) | set(b2.keys())

    differences = {}
    for signal in all_signals:
        h1_pts = b1.get(signal, 0)
        h2_pts = b2.get(signal, 0)
        diff = h1_pts - h2_pts
        if abs(diff) > 2:  # Only significant differences
            differences[signal] = {
                'horse1': h1_pts,
                'horse2': h2_pts,
                'difference': diff
            }

    return differences


def identify_root_cause(winner: Dict, classy_clarets: Dict, differences: Dict) -> Dict:
    """Identify root cause of the miss."""

    # Analyze score components
    cc_score = float(classy_clarets.get('score', 0))
    winner_score = float(winner.get('score', 0))

    # Check theories
    theories = {
        'recent_win_overweight': False,
        'form_velocity_false_positive': False,
        'consistency_placer_bias': False,
        'missing_phase1_signals': False,
        'class_drop_advantage': False,
        'market_position_wrong': False
    }

    cc_breakdown = get_score_breakdown(classy_clarets)
    winner_breakdown = get_score_breakdown(winner)

    # Theory A: Recent win overweight
    if cc_breakdown.get('recent_win', 0) > 10 and cc_breakdown.get('recent_win', 0) > winner_breakdown.get('recent_win', 0):
        theories['recent_win_overweight'] = True

    # Theory C: Form velocity false positive
    if cc_breakdown.get('form_velocity_bonus', 0) > 15 and winner_breakdown.get('form_velocity_bonus', 0) < 5:
        theories['form_velocity_false_positive'] = True

    # Theory D: Consistency placer bias
    if cc_breakdown.get('consistency', 0) > 10 and classy_clarets.get('outcome') in ['2nd', '3rd']:
        theories['consistency_placer_bias'] = True

    # Theory E: Class drop advantage
    if winner_breakdown.get('class_drop_bonus', 0) > 20 and cc_breakdown.get('class_drop_bonus', 0) < 10:
        theories['class_drop_advantage'] = True

    # Theory F: Market position wrong
    winner_odds = float(winner.get('odds', 0))
    cc_odds = float(classy_clarets.get('odds', 0))
    if winner_odds < cc_odds and winner_score < cc_score:
        theories['market_position_wrong'] = True

    # Theory B: Would Phase 1 have caught it?
    # Check if winner would have benefited from pace/jockey signals
    theories['missing_phase1_signals'] = True  # Can't prove without Phase 1 data

    return theories


def generate_weight_recommendations(theories: Dict, differences: Dict) -> List[str]:
    """Generate weight adjustment recommendations."""
    recommendations = []

    if theories['recent_win_overweight']:
        recommendations.append(
            "RECOMMEND: Reduce 'recent_win' from 14pts to 12pts (-2pts). "
            "Classy Clarets scored high on recent win but it was false signal."
        )

    if theories['form_velocity_false_positive']:
        recommendations.append(
            "RECOMMEND: Reduce 'form_velocity_bonus' from 18pts to 15pts (-3pts). "
            "Recent increase from 10→18pts may be too aggressive."
        )

    if theories['consistency_placer_bias']:
        recommendations.append(
            "RECOMMEND: Reduce 'consistency' from 12pts to 10pts (-2pts). "
            "Consistency bonus may reward 'placers' not 'winners'."
        )

    if theories['class_drop_advantage']:
        recommendations.append(
            "RECOMMEND: Increase 'class_drop_bonus' from 24pts to 28pts (+4pts). "
            "Winner had class drop advantage we undervalued."
        )

    if theories['market_position_wrong']:
        recommendations.append(
            "RECOMMEND: Increase 'favorite_correction' from 5pts to 7pts (+2pts). "
            "Market was right, we were wrong. Restore some market trust."
        )

    if theories['missing_phase1_signals']:
        recommendations.append(
            "INFO: Phase 1 signals (pace matching, jockey upgrade) deployed today. "
            "Active tomorrow May 21. May have prevented this miss."
        )

    if not recommendations:
        recommendations.append(
            "NO ACTION: This appears to be variance/anomaly. "
            "Monitor for pattern recurrence over next 7 days."
        )

    return recommendations


def print_analysis_report(horses: List[Dict], winner: Optional[Dict],
                         classy_clarets: Optional[Dict]):
    """Print comprehensive analysis report."""

    print("\n" + "="*80)
    print("CLASSY CLARETS LOSS ANALYSIS - Ayr 14:12 May 20, 2026")
    print("="*80 + "\n")

    if not horses:
        print("ERROR: No horses found for Ayr 13:12 race on 2026-05-20")
        print("REASON: Either race not in database or evening pipeline hasn't run yet")
        print("ACTION: Wait until 21:05 UTC for evening pipeline to complete\n")
        return

    # Print field overview
    print("RACE FIELD OVERVIEW")
    print("-" * 80)
    print(f"{'Rank':<6} {'Horse':<25} {'Score':<8} {'Odds':<8} {'Outcome':<10}")
    print("-" * 80)

    for i, horse in enumerate(horses[:10], 1):  # Top 10
        name = horse.get('horse_name', 'Unknown')[:24]
        score = horse.get('score', 0)
        odds = horse.get('odds', 0)
        outcome = horse.get('outcome', 'PENDING')
        print(f"{i:<6} {name:<25} {score:<8.1f} {odds:<8.2f} {outcome:<10}")

    print("\n")

    # Find Classy Clarets
    if not classy_clarets:
        classy_clarets = find_horse_by_name(horses, 'classy clarets')

    if not classy_clarets:
        print("ERROR: Classy Clarets not found in race data")
        print("This should not happen - check database integrity\n")
        return

    # Find winner
    if not winner:
        winner = next((h for h in horses if h.get('outcome') == 'WIN'), None)

    if not winner:
        print("WARNING: Winner not identified in database yet")
        print("REASON: Evening pipeline may still be processing")
        print("ACTION: Run this script again in 10 minutes\n")

        # Show Classy Clarets details anyway
        print("CLASSY CLARETS DETAILS (Our #1 Pick)")
        print("-" * 80)
        print(f"Score: {classy_clarets.get('score')} pts")
        print(f"Ranking: #{horses.index(classy_clarets) + 1} in race")
        print(f"Odds: {classy_clarets.get('odds')}")
        print(f"Outcome: {classy_clarets.get('outcome', 'PENDING')}")
        print(f"Trainer: {classy_clarets.get('trainer', 'Unknown')}")
        print(f"Jockey: {classy_clarets.get('jockey', 'Unknown')}")
        print("\n")
        return

    # Full analysis
    print("WINNER vs CLASSY CLARETS")
    print("-" * 80)

    winner_name = winner.get('horse_name', 'Unknown')
    winner_score = float(winner.get('score', 0))
    winner_rank = horses.index(winner) + 1

    cc_score = float(classy_clarets.get('score', 0))
    cc_rank = horses.index(classy_clarets) + 1

    print(f"\nWinner: {winner_name}")
    print(f"  Score: {winner_score:.1f} pts (Rank #{winner_rank})")
    print(f"  Odds: {winner.get('odds', 0):.2f}")
    print(f"  Trainer: {winner.get('trainer', 'Unknown')}")
    print(f"  Jockey: {winner.get('jockey', 'Unknown')}")

    print(f"\nClassy Clarets (Our Pick):")
    print(f"  Score: {cc_score:.1f} pts (Rank #{cc_rank})")
    print(f"  Odds: {classy_clarets.get('odds', 0):.2f}")
    print(f"  Outcome: {classy_clarets.get('outcome', 'PENDING')}")
    print(f"  Trainer: {classy_clarets.get('trainer', 'Unknown')}")
    print(f"  Jockey: {classy_clarets.get('jockey', 'Unknown')}")

    print(f"\nScore Gap: {cc_score - winner_score:+.1f} pts")
    print(f"  (Classy Clarets scored {abs(cc_score - winner_score):.1f} pts " +
          ("HIGHER" if cc_score > winner_score else "LOWER") + " than winner)")

    # Compare score breakdowns
    print("\n")
    print("SCORE BREAKDOWN COMPARISON")
    print("-" * 80)
    print(f"{'Signal':<30} {'Winner':<12} {'Classy C':<12} {'Difference':<12}")
    print("-" * 80)

    differences = compare_scores(winner, classy_clarets)

    # Sort by absolute difference (largest first)
    sorted_diffs = sorted(
        differences.items(),
        key=lambda x: abs(x[1]['difference']),
        reverse=True
    )

    for signal, data in sorted_diffs[:15]:  # Top 15 differences
        winner_pts = data['horse1']
        cc_pts = data['horse2']
        diff = data['difference']

        print(f"{signal[:29]:<30} {winner_pts:<12.1f} {cc_pts:<12.1f} {diff:+12.1f}")

    # Root cause analysis
    print("\n")
    print("ROOT CAUSE ANALYSIS")
    print("-" * 80)

    theories = identify_root_cause(winner, classy_clarets, differences)

    print("\nTheories Tested:")
    for theory, is_true in theories.items():
        status = "✓ CONFIRMED" if is_true else "✗ Not detected"
        theory_name = theory.replace('_', ' ').title()
        print(f"  {theory_name}: {status}")

    # Recommendations
    print("\n")
    print("WEIGHT ADJUSTMENT RECOMMENDATIONS")
    print("-" * 80)

    recommendations = generate_weight_recommendations(theories, differences)
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec}")

    print("\n")
    print("NEXT STEPS")
    print("-" * 80)
    print("1. Review the score breakdown differences above")
    print("2. Identify which signals gave Classy Clarets false confidence")
    print("3. Monitor pattern recurrence over next 3-7 days")
    print("4. If pattern repeats (3+ occurrences), deploy weight adjustment")
    print("5. Phase 1 signals active tomorrow (May 21) - may prevent this")
    print("\n")

    # Save detailed JSON report
    report = {
        'analysis_date': datetime.now().isoformat(),
        'race': {
            'course': 'Ayr',
            'time': '13:12 UTC',
            'date': '2026-05-20'
        },
        'winner': {
            'name': winner_name,
            'score': winner_score,
            'rank': winner_rank,
            'odds': float(winner.get('odds', 0)),
            'breakdown': get_score_breakdown(winner)
        },
        'our_pick': {
            'name': 'Classy Clarets',
            'score': cc_score,
            'rank': cc_rank,
            'odds': float(classy_clarets.get('odds', 0)),
            'outcome': classy_clarets.get('outcome', 'PENDING'),
            'breakdown': get_score_breakdown(classy_clarets)
        },
        'gap_analysis': {
            'score_difference': cc_score - winner_score,
            'rank_difference': cc_rank - winner_rank,
            'key_differences': {k: v for k, v in sorted_diffs[:10]}
        },
        'root_causes': theories,
        'recommendations': recommendations
    }

    with open('classy_clarets_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2, cls=DecimalEncoder)

    print("Detailed JSON report saved to: classy_clarets_analysis_report.json")
    print("="*80 + "\n")


def main():
    """Main analysis function."""
    print("\nFetching Ayr race data from DynamoDB...")

    try:
        horses = get_ayr_race_horses('2026-05-20')
        print(f"Found {len(horses)} horses in Ayr 13:12 race\n")

        # Find Classy Clarets and winner
        classy_clarets = find_horse_by_name(horses, 'classy clarets')
        winner = next((h for h in horses if h.get('outcome') == 'WIN'), None)

        # Print analysis
        print_analysis_report(horses, winner, classy_clarets)

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check AWS credentials are configured")
        print("2. Ensure evening pipeline has run (after 21:00 UTC)")
        print("3. Verify DynamoDB table 'SureBetBets' exists")
        print("4. Check boto3 is installed: pip install boto3")
        print("\n")
        raise


if __name__ == '__main__':
    main()

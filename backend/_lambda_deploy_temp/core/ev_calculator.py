"""
Expected Value (EV) Calculator
===============================
Calculates betting EV and identifies positive expected value opportunities.
Only recommend bets when we have a genuine edge over the market.
"""

from typing import Dict, Tuple


def calculate_expected_value(model_probability: float, decimal_odds: float) -> float:
    """
    Calculate Expected Value for a bet.

    Formula: EV = (Win Probability × Decimal Odds) - 1

    Args:
        model_probability: Our model's win probability (0.0-1.0)
        decimal_odds: Market odds in decimal format

    Returns:
        Expected value as decimal (0.20 = +20% edge)

    Examples:
        >>> calculate_expected_value(0.30, 4.0)
        0.20  # +20% edge (30% chance @ 4.0 odds)

        >>> calculate_expected_value(0.20, 4.0)
        -0.20  # -20% edge (no value)
    """
    if decimal_odds <= 1.0 or model_probability <= 0:
        return -1.0

    ev = (model_probability * decimal_odds) - 1.0
    return ev


def score_to_win_probability(score: float, max_score: float = 120.0) -> float:
    """
    Convert model score to win probability estimate.

    Uses calibrated curve based on historical performance:
    - Score 120+ → 50% win probability
    - Score 100-120 → 35-50%
    - Score 85-100 → 25-35%
    - Score 70-85 → 18-25%
    - Score <70 → <18%

    Args:
        score: Model score (0-120+)
        max_score: Maximum expected score

    Returns:
        Win probability (0.0-1.0)
    """
    if score <= 0:
        return 0.0

    # Calibrated curve based on historical strike rates
    if score >= 120:
        # Top tier: 50%+ strike rate
        return min(0.50 + (score - 120) * 0.002, 0.65)
    elif score >= 100:
        # Very high confidence: 35-50%
        return 0.35 + ((score - 100) / 20) * 0.15
    elif score >= 85:
        # High confidence: 25-35%
        return 0.25 + ((score - 85) / 15) * 0.10
    elif score >= 70:
        # Medium confidence: 18-25%
        return 0.18 + ((score - 70) / 15) * 0.07
    else:
        # Low confidence: <18%
        return min(score / 70 * 0.18, 0.18)


def check_minimum_ev(score: float, decimal_odds: float, tier: str = "strong") -> Tuple[bool, float, str]:
    """
    Check if pick meets minimum EV threshold for its tier.

    Thresholds:
    - NAP: EV must be > +20%
    - Strong: EV must be > +15%
    - Value: EV must be > +10%

    Args:
        score: Model score
        decimal_odds: Market odds
        tier: Bet tier ("nap", "strong", "value")

    Returns:
        (passes_threshold, ev_percentage, reason)
    """
    min_ev_thresholds = {
        'nap': 0.20,     # +20% minimum
        'strong': 0.15,  # +15% minimum
        'value': 0.10    # +10% minimum
    }

    min_ev = min_ev_thresholds.get(tier.lower(), 0.15)

    # Calculate EV
    win_prob = score_to_win_probability(score)
    ev = calculate_expected_value(win_prob, decimal_odds)
    ev_pct = ev * 100

    passes = ev >= min_ev

    reason = f"{ev_pct:+.1f}% EV ({win_prob*100:.0f}% win prob @ {decimal_odds:.2f} odds)"
    if not passes:
        reason += f" - BELOW {min_ev*100:.0f}% threshold"

    return passes, ev, reason


def categorize_by_ev(score: float, decimal_odds: float) -> Dict[str, any]:
    """
    Categorize pick by EV and determine recommended bet tier.

    Returns dict with:
    - tier: "nap", "strong", "value", or "no_bet"
    - ev: Expected value decimal
    - ev_pct: EV as percentage
    - win_prob: Model win probability
    - confidence: Confidence level
    - stake_units: Recommended stake (1-4 units)
    - reason: Explanation
    """
    win_prob = score_to_win_probability(score)
    ev = calculate_expected_value(win_prob, decimal_odds)
    ev_pct = ev * 100

    result = {
        'win_probability': win_prob,
        'ev': ev,
        'ev_pct': ev_pct,
        'score': score,
        'odds': decimal_odds
    }

    # NAP criteria: High score + Strong EV
    if score >= 140 and ev >= 0.28:
        result.update({
            'tier': 'nap',
            'confidence': 85,
            'stake_units': 4,
            'reason': f'Best bet of the day (score {score:.0f}, {ev_pct:+.1f}% EV)',
            'show_prominence': 'primary'
        })
    elif score >= 125 and ev >= 0.20:
        result.update({
            'tier': 'nap',
            'confidence': 80,
            'stake_units': 3,
            'reason': f'NAP (score {score:.0f}, {ev_pct:+.1f}% EV)',
            'show_prominence': 'primary'
        })

    # Strong selection criteria: Good score + Good EV
    elif score >= 110 and ev >= 0.18:
        result.update({
            'tier': 'strong',
            'confidence': 72,
            'stake_units': 2,
            'reason': f'Strong selection (score {score:.0f}, {ev_pct:+.1f}% EV)',
            'show_prominence': 'secondary'
        })
    elif score >= 95 and ev >= 0.15:
        result.update({
            'tier': 'strong',
            'confidence': 68,
            'stake_units': 2,
            'reason': f'Strong selection (score {score:.0f}, {ev_pct:+.1f}% EV)',
            'show_prominence': 'secondary'
        })

    # Value play criteria: Longer odds + Decent EV
    elif decimal_odds >= 5.0 and ev >= 0.15 and score >= 75:
        result.update({
            'tier': 'value',
            'confidence': 58,
            'stake_units': 1,
            'reason': f'Value play (score {score:.0f}, {ev_pct:+.1f}% EV at {decimal_odds:.1f})',
            'show_prominence': 'tertiary'
        })
    elif decimal_odds >= 6.0 and ev >= 0.10 and score >= 70:
        result.update({
            'tier': 'value',
            'confidence': 55,
            'stake_units': 1,
            'reason': f'Longshot value (score {score:.0f}, {ev_pct:+.1f}% EV)',
            'show_prominence': 'tertiary'
        })

    # No bet - insufficient edge
    else:
        result.update({
            'tier': 'no_bet',
            'confidence': 0,
            'stake_units': 0,
            'reason': f'Insufficient edge ({ev_pct:+.1f}% EV below threshold)',
            'show_prominence': 'none'
        })

    return result


def calculate_kelly_stake(win_probability: float, decimal_odds: float,
                         bankroll: float = 100, fractional: float = 0.25) -> float:
    """
    Calculate optimal stake using Kelly Criterion.

    Formula: kelly = (odds × win_prob - 1) / (odds - 1)

    Uses fractional Kelly (default 25%) for safety.

    Args:
        win_probability: Model win probability (0.0-1.0)
        decimal_odds: Market odds
        bankroll: Total bankroll (default 100 units)
        fractional: Fraction of Kelly to use (default 0.25 = 25%)

    Returns:
        Recommended stake in units (capped at 4% of bankroll)
    """
    if decimal_odds <= 1.0 or win_probability <= 0:
        return 0.0

    # Kelly formula
    kelly = (decimal_odds * win_probability - 1) / (decimal_odds - 1)

    # Apply fractional Kelly for safety
    fractional_kelly = kelly * fractional

    # Convert to stake
    stake = fractional_kelly * bankroll

    # Cap at 4% of bankroll maximum
    max_stake = bankroll * 0.04
    stake = min(stake, max_stake)

    # Round to 2 decimal places
    return round(max(0, stake), 2)

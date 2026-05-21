"""
MARKET LIQUIDITY ANALYZER
==========================
Analyzes Betfair market liquidity to distinguish informed money from noise.

Signals:
  - High-volume gamble (£50k+ matched + price shortened) = smart money
  - High-volume drift (£50k+ matched + price lengthened) = stable dump
  - Low liquidity (< £10k matched) = unreliable odds

Data source: Betfair API (already integrated, just extract matched volume)
Expected Impact: +2-3% strike rate
"""

from typing import Dict, Tuple, Optional


def analyze_market_liquidity(
    runner_data: Dict,
    weights: Dict
) -> Tuple[int, str]:
    """
    Analyze market liquidity and price movement to detect informed money.

    Signals:
        - High-volume shortening (smart money/gamble): +12pts
        - High-volume drift (stable confidence lost): -10pts
        - Low liquidity (unreliable market): -5pts

    Args:
        runner_data: Dict with keys:
            - matched_volume: Total £ matched on this runner (float)
            - price_movement: 'steaming' | 'drifting' | '' (str)
            - price_move_pct: Percentage change (int/float)
            - odds: Current odds (float)

        weights: Scoring weights dict

    Returns:
        (points, reason_string)
    """
    matched_volume = runner_data.get('matched_volume', 0)
    price_movement = str(runner_data.get('price_movement', '')).lower()
    price_move_pct = abs(int(runner_data.get('price_move_pct', 0) or 0))
    current_odds = float(runner_data.get('odds', 0) or 0)

    # Thresholds
    HIGH_VOLUME_THRESHOLD = 50000  # £50k
    MEDIUM_VOLUME_THRESHOLD = 20000  # £20k
    LOW_VOLUME_THRESHOLD = 10000  # £10k
    SIGNIFICANT_MOVE_THRESHOLD = 20  # 20% price change

    # Convert to float for comparison
    matched_volume = float(matched_volume) if matched_volume else 0

    # Low liquidity warning
    if matched_volume < LOW_VOLUME_THRESHOLD and current_odds > 0:
        penalty = int(weights.get('low_liquidity_penalty', 5))
        return -penalty, (
            f"Low market liquidity (£{matched_volume:,.0f} matched) "
            f"— odds may be unreliable: -{penalty}pts"
        )

    # High-volume moves (informed money)
    if matched_volume >= HIGH_VOLUME_THRESHOLD:

        # Smart money coming in (gamble)
        if price_movement == 'steaming' and price_move_pct >= SIGNIFICANT_MOVE_THRESHOLD:
            bonus = int(weights.get('high_volume_gamble_bonus', 12))
            return bonus, (
                f"Major gamble: £{matched_volume:,.0f} matched, "
                f"price shortened {price_move_pct}% (informed money): +{bonus}pts"
            )

        # Stable dumping (confidence lost)
        elif price_movement == 'drifting' and price_move_pct >= SIGNIFICANT_MOVE_THRESHOLD:
            penalty = int(weights.get('high_volume_drift_penalty', 10))
            return -penalty, (
                f"Stable dump: £{matched_volume:,.0f} matched, "
                f"price drifted {price_move_pct}% (confidence lost): -{penalty}pts"
            )

        # High volume, stable price (strong market confidence)
        elif price_move_pct < 10:
            bonus = int(weights.get('high_volume_stable_bonus', 6))
            return bonus, (
                f"Strong market: £{matched_volume:,.0f} matched, "
                f"stable price (market confidence): +{bonus}pts"
            )

    # Medium-volume moves (moderate signal)
    elif matched_volume >= MEDIUM_VOLUME_THRESHOLD:

        if price_movement == 'steaming' and price_move_pct >= SIGNIFICANT_MOVE_THRESHOLD:
            bonus = int(weights.get('medium_volume_gamble_bonus', 8))
            return bonus, (
                f"Moderate gamble: £{matched_volume:,.0f} matched, "
                f"price shortened {price_move_pct}%: +{bonus}pts"
            )

        elif price_movement == 'drifting' and price_move_pct >= SIGNIFICANT_MOVE_THRESHOLD:
            penalty = int(weights.get('medium_volume_drift_penalty', 6))
            return -penalty, (
                f"Moderate drift: £{matched_volume:,.0f} matched, "
                f"price drifted {price_move_pct}%: -{penalty}pts"
            )

    # Normal volume, no special signal
    return 0, ''


def calculate_market_confidence_score(
    runner_data: Dict,
    field_runners: list
) -> float:
    """
    Calculate 0-100 market confidence score based on liquidity metrics.

    Factors:
        - Absolute matched volume
        - Relative matched volume (vs field average)
        - Price stability
        - Market depth (if available)

    Returns:
        Float 0-100 (higher = more confident market)
    """
    matched_volume = float(runner_data.get('matched_volume', 0) or 0)
    price_move_pct = abs(int(runner_data.get('price_move_pct', 0) or 0))

    # Calculate field average volume
    field_volumes = []
    for r in field_runners:
        vol = float(r.get('matched_volume', 0) or 0)
        if vol > 0:
            field_volumes.append(vol)

    field_avg = sum(field_volumes) / len(field_volumes) if field_volumes else 10000

    # Component 1: Absolute volume (0-40 points)
    if matched_volume >= 100000:
        volume_score = 40
    elif matched_volume >= 50000:
        volume_score = 30
    elif matched_volume >= 20000:
        volume_score = 20
    elif matched_volume >= 10000:
        volume_score = 10
    else:
        volume_score = 0

    # Component 2: Relative volume vs field (0-30 points)
    if field_avg > 0:
        relative = matched_volume / field_avg
        if relative >= 2.0:  # 2x field average
            relative_score = 30
        elif relative >= 1.5:
            relative_score = 20
        elif relative >= 1.0:
            relative_score = 10
        else:
            relative_score = 5
    else:
        relative_score = 0

    # Component 3: Price stability (0-30 points)
    if price_move_pct <= 5:
        stability_score = 30  # Very stable
    elif price_move_pct <= 10:
        stability_score = 20  # Stable
    elif price_move_pct <= 20:
        stability_score = 10  # Moderate movement
    else:
        stability_score = 0  # Volatile

    total = volume_score + relative_score + stability_score
    return min(total, 100)


def enrich_runners_with_liquidity(runners: list, weights: Dict) -> list:
    """
    Add market liquidity signals to runners.

    Modifies runners in place and returns the list.
    """
    for runner in runners:
        # Analyze liquidity
        points, reason = analyze_market_liquidity(runner, weights)

        runner['liquidity_bonus'] = points
        runner['liquidity_reason'] = reason

        # Calculate confidence score
        confidence = calculate_market_confidence_score(runner, runners)
        runner['market_confidence_score'] = confidence

    return runners


def get_market_summary(runners: list) -> Dict:
    """
    Get summary statistics for the market.

    Returns:
        Dict with:
            - total_matched: Total £ matched across all runners
            - avg_matched: Average matched per runner
            - max_matched: Highest matched runner
            - market_strength: 'STRONG' | 'MEDIUM' | 'WEAK'
    """
    volumes = [float(r.get('matched_volume', 0) or 0) for r in runners]

    if not volumes:
        return {
            'total_matched': 0,
            'avg_matched': 0,
            'max_matched': 0,
            'market_strength': 'WEAK'
        }

    total = sum(volumes)
    avg = total / len(volumes)
    max_vol = max(volumes)

    # Determine market strength
    if total >= 500000:  # £500k+ total
        strength = 'STRONG'
    elif total >= 200000:  # £200k+ total
        strength = 'MEDIUM'
    else:
        strength = 'WEAK'

    return {
        'total_matched': total,
        'avg_matched': avg,
        'max_matched': max_vol,
        'market_strength': strength
    }


# Example usage:
if __name__ == '__main__':
    # Test liquidity analysis
    test_runner = {
        'matched_volume': 75000,  # £75k matched
        'price_movement': 'steaming',
        'price_move_pct': 25,  # Shortened 25%
        'odds': 5.0
    }

    weights = {
        'high_volume_gamble_bonus': 12,
        'high_volume_drift_penalty': 10,
        'low_liquidity_penalty': 5,
    }

    points, reason = analyze_market_liquidity(test_runner, weights)
    print(f"Points: {points}")
    print(f"Reason: {reason}")
    # Expected: +12pts for high-volume gamble

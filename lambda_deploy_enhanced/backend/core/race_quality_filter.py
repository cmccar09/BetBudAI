"""
Race Quality Filter
===================
Filters out low-quality, unpredictable races where our model has no edge.
Focus resources on races where form signals are reliable.
"""

import re
from typing import Tuple, Optional

# Races to actively bet on
BET_RACE_TYPES = [
    'handicap', 'conditions', 'listed', 'group', 'grade', 'stakes',
    'classified', 'novice stakes', 'maiden stakes'
]

# Races to avoid (low quality/unpredictable)
AVOID_RACE_TYPES = [
    'maiden', 'seller', 'claimer', 'selling',
    'amateur', 'apprentice', 'conditional'
]

# Race classes to bet on (avoid Class 7)
BET_RACE_CLASSES = [1, 2, 3, 4, 5, 6]

AVOID_RACE_CLASSES = [7]  # Class 7 = sellers/claimers


def is_quality_race(race_data: dict) -> Tuple[bool, Optional[str]]:
    """
    Determine if race is high enough quality to analyze.

    Criteria for BETTING:
    - Class 1-6 handicaps, conditions, listed, group races
    - 5-15 runners (not lottery fields)
    - NOT maidens, sellers, claimers
    - NOT all-weather unless winter

    Args:
        race_data: Race information dict

    Returns:
        (is_quality, skip_reason)
    """
    race_name = str(race_data.get('market_name', '') or race_data.get('race_name', '')).lower()
    race_class = race_data.get('race_class', race_data.get('class', ''))
    runners = race_data.get('runners', [])
    n_runners = len(runners)
    venue = str(race_data.get('venue', '') or race_data.get('course', '')).lower()

    # 1. Check race class
    if race_class:
        try:
            class_num = int(str(race_class).strip().replace('class', '').strip())
            if class_num in AVOID_RACE_CLASSES:
                return False, f"Class {class_num} (sellers/claimers - avoid)"
        except (ValueError, AttributeError):
            pass

    # Extract class from name if not in field
    class_match = re.search(r'class\s*([1-7])', race_name)
    if class_match:
        class_num = int(class_match.group(1))
        if class_num in AVOID_RACE_CLASSES:
            return False, f"Class {class_num} (low quality)"

    # 2. Check race type - AVOID specific types
    for avoid_type in AVOID_RACE_TYPES:
        if avoid_type in race_name:
            # Exception: "maiden stakes" and "novice stakes" are OK (higher quality)
            if 'stakes' in race_name and avoid_type in ['maiden', 'novice']:
                continue
            return False, f"{avoid_type.title()} race (unreliable form)"

    # 3. Check field size
    if n_runners > 16:
        return False, f"Large field ({n_runners} runners - pace/draw lottery)"

    if n_runners < 5:
        return False, f"Small field ({n_runners} runners - limited betting opportunity)"

    # 4. Check distance - avoid very short sprints
    dist_match = re.search(r'(\d+)f', race_name)
    if dist_match:
        distance_f = int(dist_match.group(1))
        if distance_f <= 5:
            return False, f"{distance_f}f sprint (lottery/draw-dependent)"

    # 5. Check if race type is explicitly in our BET list
    is_good_type = any(rt in race_name for rt in BET_RACE_TYPES)
    if not is_good_type:
        # Not explicitly a type we bet on, but not explicitly avoided either
        # Allow it through unless field size rules it out
        pass

    # Passed all filters
    return True, None


def count_quality_races(races: list) -> dict:
    """
    Count how many races at each quality level.

    Returns:
        {
            'total': int,
            'quality': int,  # Bet on these
            'filtered': int,  # Skipped
            'reasons': {'reason': count}
        }
    """
    total = len(races)
    quality = 0
    filtered = 0
    reasons = {}

    for race in races:
        is_good, reason = is_quality_race(race)
        if is_good:
            quality += 1
        else:
            filtered += 1
            reason_key = reason.split(' (')[0] if reason else 'Unknown'
            reasons[reason_key] = reasons.get(reason_key, 0) + 1

    return {
        'total': total,
        'quality': quality,
        'filtered': filtered,
        'filter_reasons': reasons,
        'quality_pct': round((quality / total * 100) if total > 0 else 0, 1)
    }


def select_best_races_from_meeting(races: list, max_races: int = 3) -> list:
    """
    Select the N best races from a meeting to bet on.

    Prioritizes:
    1. Graded/Listed/Group races
    2. Class 1-3 handicaps
    3. Optimal field sizes (6-12 runners)
    4. Races with quality form data

    Args:
        races: List of race dicts from meeting
        max_races: Maximum races to return

    Returns:
        List of best N races to bet on
    """
    scored_races = []

    for race in races:
        is_good, _ = is_quality_race(race)
        if not is_good:
            continue

        race_name = str(race.get('market_name', '') or race.get('race_name', '')).lower()
        runners = race.get('runners', [])
        n_runners = len(runners)

        score = 0

        # Priority 1: Graded/Listed/Group races (highest quality)
        if any(kw in race_name for kw in ['listed', 'group', 'grade', 'g1', 'g2', 'g3', 'grd']):
            score += 50

        # Priority 2: Stakes races
        if 'stakes' in race_name:
            score += 40

        # Priority 3: Class-based quality
        race_class = race.get('race_class', race.get('class', ''))
        class_match = re.search(r'class\s*([1-6])', race_name)
        if class_match:
            class_num = int(class_match.group(1))
        elif race_class:
            try:
                class_num = int(str(race_class).strip().replace('class', '').strip())
            except:
                class_num = 4  # Default to mid-tier
        else:
            class_num = 4

        # Class 1-2: +30pts, Class 3: +20pts, Class 4-6: +10pts
        if class_num <= 2:
            score += 30
        elif class_num == 3:
            score += 20
        else:
            score += 10

        # Priority 4: Optimal field size (6-12 runners = sweet spot)
        if 6 <= n_runners <= 12:
            score += 20
        elif 5 <= n_runners <= 15:
            score += 10

        # Priority 5: Handicaps (predictable competitive races)
        if 'handicap' in race_name or 'hcap' in race_name:
            score += 15

        # Priority 6: Distance preference (avoid extremes)
        dist_match = re.search(r'(\d+)f', race_name)
        if dist_match:
            distance_f = int(dist_match.group(1))
            if 8 <= distance_f <= 14:  # Mile to 1m6f = optimal
                score += 10
            elif 6 <= distance_f <= 16:  # 6f to 2m = acceptable
                score += 5

        scored_races.append({
            'race': race,
            'score': score,
            'runners': n_runners,
            'class': class_num
        })

    # Sort by score (highest first)
    scored_races.sort(key=lambda x: x['score'], reverse=True)

    # Return top N races
    best_races = [item['race'] for item in scored_races[:max_races]]

    return best_races


def should_recommend_each_way(decimal_odds: float, n_runners: int, confidence: float) -> Tuple[bool, str]:
    """
    Determine if Each-Way bet is better value than Win-only.

    Each-Way pays:
    - 5-7 runners: 1st-2nd, 1/4 odds
    - 8-11 runners: 1st-2nd-3rd, 1/5 odds
    - 12-15 runners: 1st-2nd-3rd, 1/5 odds
    - 16+ runners: 1st-2nd-3rd-4th, 1/4 odds

    Args:
        decimal_odds: Horse's odds
        n_runners: Field size
        confidence: Model confidence (0-100)

    Returns:
        (recommend_ew, reason)
    """
    # Only consider EW for longer odds
    if decimal_odds < 5.0:
        return False, "Odds too short for EW (use win-only)"

    # Calculate EW terms based on field size
    if n_runners <= 4:
        return False, f"Only {n_runners} runners (EW not offered)"

    elif 5 <= n_runners <= 7:
        places = 2
        fraction = 0.25  # 1/4 odds
    elif 8 <= n_runners <= 11:
        places = 3
        fraction = 0.20  # 1/5 odds
    elif 12 <= n_runners <= 15:
        places = 3
        fraction = 0.20  # 1/5 odds
    else:  # 16+ runners
        places = 4
        fraction = 0.25  # 1/4 odds

    # Calculate place odds
    place_odds = 1 + ((decimal_odds - 1) * fraction)

    # EW is better when:
    # 1. Odds are long (5/1+)
    # 2. Large field (more places paid)
    # 3. Moderate confidence (likely to place but not guaranteed to win)

    # Simple heuristic: EW recommended for 5/1+ in fields of 8+
    if decimal_odds >= 5.0 and n_runners >= 8:
        if 55 <= confidence <= 75:
            # Sweet spot: good enough to place, not overwhelming favorite
            return True, f"EW recommended ({places} places @ {fraction} odds = {place_odds:.2f} place return)"

    return False, "Win-only better value"

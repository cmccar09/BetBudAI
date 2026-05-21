"""
JOCKEY BOOKING UPGRADE DETECTOR
================================
Detects when trainer upgrades jockey booking vs recent runs.

Signal: Elite jockey booked today vs usual 7lb claimer = trainer confidence

Data source: Compare today's jockey to form_runs jockey history
Expected Impact: +2-4% strike rate
"""

from typing import List, Dict, Tuple


# Elite jockeys (Tier 1 - Champion level)
ELITE_JOCKEYS_T1 = {
    'paul townend', 'p townend', 'p. townend',
    'jack kennedy', 'j kennedy', 'j. kennedy',
    'rachael blackmore', 'r blackmore', 'r. blackmore',
    'mark walsh', 'm walsh', 'm. walsh',
    'ryan moore', 'r moore', 'r. moore',
    'william buick', 'w buick', 'w. buick',
    'frankie dettori', 'f dettori', 'f. dettori',
    'oisin murphy', 'o murphy', 'o. murphy',
}

# Good jockeys (Tier 2 - Regular champion level)
ELITE_JOCKEYS_T2 = {
    'davy russell', 'd russell', 'd. russell',
    'patrick mullins', 'p mullins', 'mr p. mullins', 'mr p mullins',
    'danny mullins', 'd mullins', 'd. mullins',
    'harry cobden', 'h cobden', 'h. cobden',
    'nico de boinville', 'n de boinville', 'n. de boinville',
    'harry skelton', 'h skelton', 'h. skelton',
    'sam twiston-davies', 's twiston-davies', 's. twiston-davies',
    'bryony frost', 'b frost', 'b. frost',
    'tom scudamore', 't scudamore', 't. scudamore',
    'aidan coleman', 'a coleman', 'a. coleman',
    'jim crowley', 'j crowley', 'j. crowley',
    'tom marquand', 't marquand', 't. marquand',
    'hollie doyle', 'h doyle', 'h. doyle',
}


def normalize_jockey_name(jockey: str) -> str:
    """Normalize jockey name for comparison."""
    if not jockey:
        return ''

    jockey = str(jockey).lower().strip()

    # Remove claiming allowance indicators: "Tom McCain (5)" → "tom mccain"
    jockey = jockey.split('(')[0].strip()

    # Remove titles: "Mr P. Mullins" → "p. mullins"
    jockey = jockey.replace('mr ', '').replace('miss ', '').replace('ms ', '')

    return jockey


def get_jockey_tier(jockey: str) -> int:
    """
    Get jockey tier (1=Elite, 2=Good, 3=Average, 4=Claimer).

    Returns:
        1 - Elite (Champion level)
        2 - Good (Regular winners)
        3 - Average (Competent)
        4 - Claimer (7lb/5lb allowance)
    """
    if not jockey:
        return 3

    normalized = normalize_jockey_name(jockey)

    # Check for claiming allowance
    if '(' in str(jockey) and ')' in str(jockey):
        return 4  # Claimer

    # Check elite tiers
    if normalized in ELITE_JOCKEYS_T1:
        return 1
    if normalized in ELITE_JOCKEYS_T2:
        return 2

    return 3  # Average


def detect_jockey_upgrade(
    current_jockey: str,
    form_runs: List[Dict],
    weights: Dict
) -> Tuple[int, str]:
    """
    Detect jockey booking upgrade and calculate bonus.

    Significant upgrades:
        - Claimer → Elite (4 → 1): +10pts
        - Average → Elite (3 → 1): +8pts
        - Claimer → Good (4 → 2): +6pts

    Args:
        current_jockey: Today's jockey
        form_runs: Previous race results with jockey field
        weights: Scoring weights dict

    Returns:
        (bonus_points, reason_string)
    """
    if not current_jockey or not form_runs:
        return 0, ''

    current_tier = get_jockey_tier(current_jockey)

    # Get recent jockeys (last 3-6 runs)
    recent_jockeys = []
    for run in form_runs[-6:]:
        jockey = run.get('jockey', '')
        if jockey:
            recent_jockeys.append(jockey)

    if not recent_jockeys:
        return 0, ''

    # Calculate average tier of recent jockeys
    recent_tiers = [get_jockey_tier(j) for j in recent_jockeys]
    avg_recent_tier = sum(recent_tiers) / len(recent_tiers)

    # Round to nearest tier
    typical_tier = round(avg_recent_tier)

    # Check for upgrade (lower tier number = better jockey)
    if current_tier >= typical_tier:
        return 0, ''  # No upgrade or downgrade

    # Calculate upgrade magnitude
    tier_improvement = typical_tier - current_tier

    # Bonus points based on improvement
    upgrade_bonus = int(weights.get('jockey_upgrade_bonus', 10))

    if tier_improvement >= 3:  # 4 → 1 (claimer to elite)
        bonus = upgrade_bonus
        reason = (
            f"Major jockey upgrade: {current_jockey} (Elite) "
            f"vs usual tier {typical_tier} — trainer backing: +{bonus}pts"
        )
    elif tier_improvement == 2:  # 4 → 2 or 3 → 1
        bonus = int(upgrade_bonus * 0.8)
        reason = (
            f"Significant jockey upgrade: {current_jockey} "
            f"vs usual tier {typical_tier}: +{bonus}pts"
        )
    elif tier_improvement == 1:  # 3 → 2 or 2 → 1
        bonus = int(upgrade_bonus * 0.5)
        reason = (
            f"Jockey upgrade: {current_jockey} booked "
            f"(better than usual): +{bonus}pts"
        )
    else:
        return 0, ''

    return bonus, reason


def detect_jockey_downgrade(
    current_jockey: str,
    form_runs: List[Dict],
    weights: Dict
) -> Tuple[int, str]:
    """
    Detect jockey booking downgrade (negative signal).

    Concerning downgrades:
        - Elite → Claimer (1 → 4): -8pts
        - Good → Claimer (2 → 4): -6pts

    Returns:
        (penalty_points, reason_string) - penalty is negative
    """
    if not current_jockey or not form_runs:
        return 0, ''

    current_tier = get_jockey_tier(current_jockey)

    # Get recent jockeys
    recent_jockeys = []
    for run in form_runs[-6:]:
        jockey = run.get('jockey', '')
        if jockey:
            recent_jockeys.append(jockey)

    if not recent_jockeys:
        return 0, ''

    recent_tiers = [get_jockey_tier(j) for j in recent_jockeys]
    avg_recent_tier = sum(recent_tiers) / len(recent_tiers)
    typical_tier = round(avg_recent_tier)

    # Check for downgrade (higher tier number = worse jockey)
    if current_tier <= typical_tier:
        return 0, ''  # No downgrade

    tier_decline = current_tier - typical_tier

    downgrade_penalty = int(weights.get('jockey_downgrade_penalty', 8))

    if tier_decline >= 2:  # Elite/Good → Claimer
        penalty = downgrade_penalty
        reason = (
            f"Jockey downgrade: {current_jockey} (tier {current_tier}) "
            f"vs usual tier {typical_tier} — reduced confidence: -{penalty}pts"
        )
    elif tier_decline == 1:
        penalty = int(downgrade_penalty * 0.5)
        reason = (
            f"Minor jockey downgrade: {current_jockey} "
            f"vs usual booking: -{penalty}pts"
        )
    else:
        return 0, ''

    return -penalty, reason


def enrich_runners_with_jockey_change(runners: List[Dict], weights: Dict) -> List[Dict]:
    """
    Add jockey upgrade/downgrade signals to runners.

    Modifies runners in place and returns the list.
    """
    for runner in runners:
        current_jockey = runner.get('jockey', '')
        form_runs = runner.get('form_runs', [])

        if not current_jockey or not form_runs:
            runner['jockey_upgrade_bonus'] = 0
            runner['jockey_upgrade_reason'] = ''
            continue

        # Check for upgrade
        upgrade_bonus, upgrade_reason = detect_jockey_upgrade(
            current_jockey, form_runs, weights
        )

        # Check for downgrade
        downgrade_penalty, downgrade_reason = detect_jockey_downgrade(
            current_jockey, form_runs, weights
        )

        # Store the net result
        if upgrade_bonus > 0:
            runner['jockey_upgrade_bonus'] = upgrade_bonus
            runner['jockey_upgrade_reason'] = upgrade_reason
        elif downgrade_penalty < 0:
            runner['jockey_upgrade_bonus'] = downgrade_penalty
            runner['jockey_upgrade_reason'] = downgrade_reason
        else:
            runner['jockey_upgrade_bonus'] = 0
            runner['jockey_upgrade_reason'] = ''

    return runners


# Example usage:
if __name__ == '__main__':
    # Test jockey upgrade detection
    test_runs = [
        {'jockey': 'A Smith (7)', 'date': '2026-04-01'},  # 7lb claimer
        {'jockey': 'B Jones (5)', 'date': '2026-04-08'},  # 5lb claimer
        {'jockey': 'C Brown', 'date': '2026-04-15'},      # Average jockey
    ]

    weights = {
        'jockey_upgrade_bonus': 10,
    }

    # Today: Ryan Moore (Elite Tier 1)
    bonus, reason = detect_jockey_upgrade('Ryan Moore', test_runs, weights)
    print(f"Bonus: {bonus} points")
    print(f"Reason: {reason}")
    # Expected: +10pts for major upgrade (claimer/average → elite)

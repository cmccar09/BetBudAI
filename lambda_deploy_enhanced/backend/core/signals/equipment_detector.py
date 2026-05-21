"""
EQUIPMENT CHANGE DETECTOR
=========================
Detects first-time equipment changes from Sporting Life racecards.

Signals stable confidence when trainer applies:
  - Blinkers first time
  - Tongue tie first time
  - Visor first time
  - Cheekpieces first time

Data source: Sporting Life racecards (FREE - extract from HTML)
Expected Impact: +3-5% strike rate
"""

import re
from typing import List, Dict, Tuple, Optional


# Equipment keywords and their standard names
EQUIPMENT_PATTERNS = {
    'blinkers': ['b', 'blinkers', 'blnkr'],
    'visor': ['v', 'visor', 'vis'],
    'tongue_tie': ['t', 'tt', 'tongue tie', 'tongue strap'],
    'cheekpieces': ['c', 'cp', 'cheekpieces', 'cheek pieces'],
    'hood': ['h', 'hood'],
    'eyeshield': ['e', 'eyeshield', 'eye shield'],
}


def normalize_equipment(equipment_str: str) -> set:
    """
    Normalize equipment string to standard set of equipment types.

    Examples:
        "b" → {'blinkers'}
        "b, t" → {'blinkers', 'tongue_tie'}
        "first time blinkers" → {'blinkers'}

    Returns:
        Set of normalized equipment names
    """
    if not equipment_str:
        return set()

    equipment_str = str(equipment_str).lower().strip()
    detected = set()

    for equipment_name, patterns in EQUIPMENT_PATTERNS.items():
        for pattern in patterns:
            # Check if pattern appears as standalone or with delimiters
            if re.search(rf'\b{re.escape(pattern)}\b', equipment_str):
                detected.add(equipment_name)
                break

    return detected


def detect_equipment_changes(
    current_equipment: str,
    form_runs: List[Dict],
    weights: Dict
) -> Tuple[int, List[str]]:
    """
    Detect first-time equipment and calculate bonus points.

    Args:
        current_equipment: Today's equipment (e.g., "b, t" or "blinkers, tongue tie")
        form_runs: List of previous race results with equipment field
        weights: Scoring weights dict

    Returns:
        (total_bonus_points, list_of_reasons)
    """
    if not current_equipment:
        return 0, []

    current = normalize_equipment(current_equipment)

    if not current:
        return 0, []

    # Gather all previous equipment
    previous_equipment = set()
    for run in form_runs:
        prev_equip = run.get('equipment', '')
        previous_equipment.update(normalize_equipment(prev_equip))

    # Find first-time equipment
    first_time = current - previous_equipment

    if not first_time:
        return 0, []

    # Calculate bonus based on equipment significance
    equipment_weights = {
        'blinkers': int(weights.get('first_time_blinkers', 12)),
        'visor': int(weights.get('first_time_visor', 10)),
        'tongue_tie': int(weights.get('first_time_tongue_tie', 8)),
        'cheekpieces': int(weights.get('first_time_cheekpieces', 6)),
        'hood': int(weights.get('first_time_hood', 4)),
        'eyeshield': int(weights.get('first_time_eyeshield', 4)),
    }

    total_bonus = 0
    reasons = []

    for equip in first_time:
        bonus = equipment_weights.get(equip, 6)  # Default 6pts
        total_bonus += bonus

        equip_display = equip.replace('_', ' ').title()
        reasons.append(
            f"First-time {equip_display} (stable confidence signal): +{bonus}pts"
        )

    return total_bonus, reasons


def extract_equipment_from_sl_html(html: str, horse_name: str) -> Optional[str]:
    """
    Extract equipment string from Sporting Life racecard HTML.

    Sporting Life shows equipment in runner tables, typically as:
        <span class="equipment">b</span>
        or in runner details section

    Args:
        html: Full HTML of racecard page
        horse_name: Name of horse to find equipment for

    Returns:
        Equipment string (e.g., "b, t") or None
    """
    if not html or not horse_name:
        return None

    # Normalize horse name for matching
    horse_name_lower = horse_name.lower().strip()

    # Pattern 1: Look for equipment span near horse name
    # Example: <td class="horse-name">Horse Name</td>...<span class="equipment">b</span>
    pattern1 = rf'(?i){re.escape(horse_name_lower)}.*?(?:equipment|gear)[^>]*>([^<]+)<'
    match1 = re.search(pattern1, html, re.IGNORECASE | re.DOTALL)
    if match1:
        return match1.group(1).strip()

    # Pattern 2: Equipment in data attribute
    # Example: data-equipment="b, t"
    pattern2 = rf'(?i)data-equipment=["\']([^"\']+)["\'][^>]*{re.escape(horse_name_lower)}'
    match2 = re.search(pattern2, html, re.IGNORECASE)
    if match2:
        return match2.group(1).strip()

    # Pattern 3: Equipment in runner JSON (Sporting Life often embeds JSON)
    pattern3 = rf'(?i)"horse_name":\s*"{re.escape(horse_name_lower)}"[^}}]*"equipment":\s*"([^"]+)"'
    match3 = re.search(pattern3, html, re.IGNORECASE)
    if match3:
        return match3.group(1).strip()

    return None


def enrich_runners_with_equipment(runners: List[Dict], racecard_html: str = None) -> List[Dict]:
    """
    Add equipment and first_time_equipment flags to runners.

    If racecard_html is provided, extracts equipment from HTML.
    Otherwise uses equipment field if already present.

    Modifies runners in place and returns the list.
    """
    for runner in runners:
        # Extract equipment if HTML provided
        if racecard_html:
            horse_name = runner.get('name', '')
            equipment = extract_equipment_from_sl_html(racecard_html, horse_name)
            if equipment:
                runner['equipment'] = equipment

        # Detect first-time equipment
        current_equipment = runner.get('equipment', '')
        form_runs = runner.get('form_runs', [])

        if current_equipment and form_runs:
            current = normalize_equipment(current_equipment)

            previous_equipment = set()
            for run in form_runs:
                prev_equip = run.get('equipment', '')
                previous_equipment.update(normalize_equipment(prev_equip))

            first_time = current - previous_equipment

            if first_time:
                runner['first_time_equipment'] = list(first_time)
            else:
                runner['first_time_equipment'] = []
        else:
            runner['first_time_equipment'] = []

    return runners


# Example usage:
if __name__ == '__main__':
    # Test equipment detection
    test_runs = [
        {'equipment': '', 'date': '2026-04-01'},
        {'equipment': 't', 'date': '2026-04-08'},
        {'equipment': 't', 'date': '2026-04-15'},
    ]

    weights = {
        'first_time_blinkers': 12,
        'first_time_tongue_tie': 8,
    }

    bonus, reasons = detect_equipment_changes('b, t', test_runs, weights)
    print(f"Bonus: {bonus} points")
    print(f"Reasons: {reasons}")
    # Expected: +12pts for first-time blinkers

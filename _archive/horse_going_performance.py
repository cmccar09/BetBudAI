"""
Horse Going Performance Analyzer
Analyzes horse form under different ground conditions
"""
import re

def analyze_form_by_going(horse_data, current_going):
    """
    Analyze horse's historical performance under current going conditions
    
    Form string format: positions like "1-23F" where:
    - Numbers = finishing positions
    - F = Fell
    - P = Pulled up
    - U = Unseated rider
    
    Returns adjustment based on going suitability
    """
    form = horse_data.get('form', '')
    
    if not form or len(form) < 3:
        return 0, "Limited form data"
    
    # Extract horse characteristics from available data
    recent_form = form[:6]  # Last ~6 runs
    
    # Count recent wins (1s) and places (1-3)
    wins = recent_form.count('1')
    places = sum(1 for c in recent_form if c.isdigit() and 1 <= int(c) <= 3)
    failures = sum(1 for c in recent_form if c in ['F', 'P', 'U', '0'])
    
    # Going-based performance patterns
    # Heavy/Soft = favors stamina horses (consistent placers)
    # Good/Firm = favors speed horses (winners or nothing)
    
    going_lower = current_going.lower()
    
    # Heavy or Soft ground
    if 'heavy' in going_lower or 'soft' in going_lower:
        # Favor horses with consistent form (lots of places, few failures)
        if places >= 3 and failures == 0:
            return +3, "Consistent form suits soft ground"
        elif places >= 2 and failures <= 1:
            return +2, "Good stamina profile"
        elif wins >= 2 and places < 3:
            # Speed horses may struggle in soft
            return -2, "Speed profile may struggle soft"
        else:
            return 0, "Neutral on soft ground"
    
    # Good to Firm or Firm ground
    elif 'firm' in going_lower:
        # Favor horses with wins (speed horses)
        if wins >= 2:
            return +3, "Speed profile suits firm ground"
        elif wins >= 1 and places >= 2:
            return +2, "Good form on faster ground"
        elif places >= 4 and wins == 0:
            # Grinders may struggle on fast ground
            return -2, "Stamina profile may struggle firm"
        else:
            return 0, "Neutral on firm ground"
    
    # Good ground (optimal for most horses)
    else:
        # Good ground suits most horses, slight boost for balanced form
        if wins >= 1 and places >= 2:
            return +2, "Balanced form suits good ground"
        elif places >= 3:
            return +1, "Consistent on good ground"
        else:
            return 0, "Neutral on good ground"


def get_going_suitability_bonus(horse_data, going_info):
    """
    Calculate bonus/penalty based on horse's suitability to going
    
    Args:
        horse_data: Dict with horse info (form, etc)
        going_info: Dict with going, rainfall_mm, adjustment, etc
    
    Returns:
        (adjustment, reason)
    """
    if not going_info or going_info.get('surface') == 'all-weather':
        return 0, "All-weather surface"
    
    current_going = going_info.get('going', 'Good')
    
    # Analyze form patterns for going suitability
    adjustment, reason = analyze_form_by_going(horse_data, current_going)
    
    return adjustment, reason


if __name__ == "__main__":
    # Test cases
    test_horses = [
        {'name': 'Speed Horse', 'form': '112-45'},  # Winner, struggles when not winning
        {'name': 'Stamina Horse', 'form': '23-3221'},  # Consistent placer
        {'name': 'Balanced Horse', 'form': '12-2314'},  # Mix of wins and places
    ]
    
    test_conditions = [
        {'going': 'Heavy', 'surface': 'turf'},
        {'going': 'Good', 'surface': 'turf'},
        {'going': 'Good to Firm', 'surface': 'turf'},
    ]
    
    print("\n" + "="*80)
    print("HORSE GOING SUITABILITY ANALYZER")
    print("="*80 + "\n")
    
    for horse in test_horses:
        print(f"\n{horse['name']} (Form: {horse['form']})")
        print("-" * 60)
        for condition in test_conditions:
            adj, reason = get_going_suitability_bonus(horse, condition)
            adj_text = f"+{adj}" if adj > 0 else str(adj) if adj < 0 else "±0"
            print(f"  {condition['going']:15} → {adj_text:4} | {reason}")

"""
ROI IMPROVEMENT STRATEGY
Based on 7-day analysis showing 75+ is best bucket but still -10.2% ROI

CHANGES:
1. Raise threshold to 80+ (more selective)
2. Add mandatory filters (avoid overleveraged races)
3. Implement stake sizing (variable stakes based on confidence)
4. Add value betting logic (only when odds > expected)
"""

import boto3
from decimal import Decimal

# Updated configuration
ROI_CONFIG = {
    'ui_threshold': Decimal('80'),  # Raised from 75 - be more selective
    'max_picks_per_day': Decimal('8'),  # Reduced from 10 - quality over quantity
    'min_odds': Decimal('2.0'),  # Avoid heavy favorites
    'max_odds': Decimal('12.0'),  # Avoid long shots
    'stake_multipliers': {
        '90+': Decimal('2.0'),  # Double stake for ultra-high confidence
        '85-89': Decimal('1.5'),  # 50% more
        '80-84': Decimal('1.0'),  # Standard
        '75-79': Decimal('0.5'),  # Half stake (data gathering only)
    },
    'filters': {
        'avoid_novice_handicaps': True,  # Too unpredictable
        'require_recent_form': True,  # Must have run in last 60 days
        'value_check': True,  # Only bet if implied prob < our confidence
    }
}

def calculate_variable_stake(confidence, base_stake=2):
    """Calculate stake based on confidence level"""
    if confidence >= 90:
        return base_stake * 2.0
    elif confidence >= 85:
        return base_stake * 1.5
    elif confidence >= 80:
        return base_stake * 1.0
    elif confidence >= 75:
        return base_stake * 0.5
    else:
        return 0  # Don't bet

def check_value(confidence, odds):
    """
    Value check: Only bet if we have an edge
    If our confidence is 80% but odds imply 40% (2.5), we have value
    """
    implied_prob = 1 / odds if odds > 0 else 0
    our_prob = confidence / 100
    
    # Need at least 10% edge
    edge = our_prob - implied_prob
    return edge >= 0.10

def should_bet_under_new_rules(pick_data):
    """Apply new ROI filters"""
    conf = pick_data.get('combined_confidence', 0)
    odds = float(pick_data.get('odds', 0))
    race_type = pick_data.get('race_type', '').lower()
    
    # 1. Minimum confidence threshold
    if conf < 80:
        return False, "Below 80 confidence threshold"
    
    # 2. Odds range
    if odds < 2.0:
        return False, "Odds too short (<2.0)"
    if odds > 12.0:
        return False, "Odds too long (>12.0)"
    
    # 3. Avoid unpredictable race types
    if 'novice' in race_type and 'handicap' in race_type:
        return False, "Novice handicap too unpredictable"
    
    # 4. Value check
    if not check_value(conf, odds):
        return False, f"No value: conf={conf}% vs implied={1/odds*100:.0f}%"
    
    return True, "Passed all filters"

# Save config to DynamoDB
def save_roi_config():
    from datetime import datetime
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    table.put_item(Item={
        'bet_id': 'ROI_CONFIG',
        'bet_date': 'CONFIG',
        'config': ROI_CONFIG,
        'updated': str(datetime.now()),
        'reason': '7-day analysis shows 75+ is best but -10.2% ROI. Raising to 80+ with filters.'
    })
    print("✅ ROI config saved to DynamoDB")

if __name__ == '__main__':
    save_roi_config()
    print("\n📊 New ROI Strategy:")
    print(f"   - Threshold: 80+ (was 75+)")
    print(f"   - Max picks: 8/day (was 10)")
    print(f"   - Odds range: 2.0-12.0")
    print(f"   - Variable stakes: 0.5x to 2.0x")
    print(f"   - Value betting: Required 10% edge")

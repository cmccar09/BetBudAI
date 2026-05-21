#!/usr/bin/env python3
"""
Fix component scores for all picks in the database
The comprehensive_score exists but component scores (form_score, class_score, etc.) are all 0
This script will properly calculate and set all component scores
"""

import boto3
from decimal import Decimal
from datetime import datetime
import sys

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Elite trainers list
ELITE_TRAINERS = [
    'nicholls', 'mullins', 'elliott', 'henderson', 'skelton', 'hobbs', 
    'tizzard', 'pipe', 'twiston-davies', 'king', 'carroll', 'barron',
    'murphy', 'williams', 'mcmanus', 'appleby', 'haggas', 'gosden',
    'stoute'
]

# Elite jockeys list
ELITE_JOCKEYS = [
    'blackmore', 'townend', 'coleman', 'walsh', 'power', 'de boinville',
    'moore', 'oisin murphy', 'william buick', 'frankie dettori', 'james doyle',
    'keane', 'geraghty'
]

def calculate_form_score(form_string):
    """Calculate form score out of 25 - LEARNING: Form matters more than trainer!"""
    if not form_string or form_string == 'Unknown':
        return 0
    
    score = 0
    
    # Count pull-ups (P) - MASSIVE penalty
    pull_ups = form_string.count('P') + form_string.count('p')
    score -= pull_ups * 8  # Heavy penalty for unreliability
    
    cleaned = ''.join(c for c in form_string if c.isdigit())
    
    if not cleaned:
        return max(0, int(score))
    
    positions = [int(c) for c in cleaned[:5]]  # Last 5 runs
    
    # Position scores - increased from original
    position_scores = {1: 15, 2: 9, 3: 5, 4: 2, 5: 0, 6: -2, 7: -3, 8: -5, 9: -6, 0: -8}
    weights = [0.50, 0.30, 0.15, 0.03, 0.02]  # Heavy weighting on recent
    
    for idx, pos in enumerate(positions):
        if idx < len(weights):
            pos_score = position_scores.get(pos, -8)
            score += pos_score * weights[idx]
    
    # Bonus for wins - increased
    wins = sum(1 for p in positions if p == 1)
    score += wins * 5  # Increased from 3
    
    # Cap at 25
    return min(max(0, int(score)), 25)

def calculate_class_score(odds):
    """Calculate class score based on odds out of 15"""
    try:
        odds_val = float(odds)
        # Favorites get higher class scores (they're in better races)
        if odds_val < 2.0:
            return 15
        elif odds_val < 3.0:
            return 12
        elif odds_val < 5.0:
            return 10
        elif odds_val < 8.0:
            return 8
        elif odds_val < 12.0:
            return 5
        else:
            return 2
    except:
        return 5

def calculate_weight_score():
    """Calculate weight score out of 10 - placeholder"""
    return 5  # Default average score

def calculate_jockey_score(jockey):
    """Calculate jockey score out of 10"""
    if not jockey:
        return 3
    
    jockey_lower = jockey.lower()
    for elite in ELITE_JOCKEYS:
        if elite in jockey_lower:
            return 10
    
    return 4  # Average jockey

def calculate_trainer_score(trainer):
    """Calculate trainer score out of 5 - LEARNING: Reduced from 10, name doesn't guarantee wins!"""
    if not trainer:
        return 2
    
    trainer_lower = trainer.lower()
    for elite in ELITE_TRAINERS:
        if elite in trainer_lower:
            return 5  # Reduced from 10
    
    return 3  # Average trainer

def calculate_distance_score():
    """Calculate distance suitability score out of 10 - placeholder"""
    return 5  # Default

def calculate_track_score(course, form):
    """Calculate track/course score out of 10"""
    # If horse has shown form, assume some track suitability
    if form and any(c in form for c in ['1', '2', '3']):
        return 7
    return 5

def calculate_pace_score():
    """Calculate pace score out of 5 - placeholder"""
    return 3  # Default

def calculate_value_score(odds):
    """Calculate value score out of 5 based on sweet spot"""
    try:
        odds_val = float(odds)
        # Sweet spot 3-9 gets full score
        if 3.0 <= odds_val <= 9.0:
            return 5
        elif 2.0 <= odds_val < 3.0 or 9.0 < odds_val <= 12.0:
            return 3
        else:
            return 1
    except:
        return 2

def calculate_recent_performance_score(form):
    """Calculate recent performance score out of 15 - LEARNING: Recent form is critical!"""
    if not form:
        return 2
    
    # Penalize pull-ups in last 5 runs (not just 3)
    if 'P' in form[:10] or 'p' in form[:10]:
        return 0  # Any recent pull-up = unreliable
    
    # Check last 3 runs
    cleaned = ''.join(c for c in form if c.isdigit())
    if not cleaned:
        return 2
    
    last_3 = [int(c) for c in cleaned[:3]]
    
    # LTO winner - massive boost
    if last_3[0] == 1:
        score = 15
    # LTO placed
    elif last_3[0] in [2, 3]:
        score = 10
    # LTO in top 4
    elif last_3[0] == 4:
        score = 6
    else:
        score = 3
    
    # Consistency bonus
    top_3_count = sum(1 for p in last_3 if p <= 3)
    if top_3_count >= 2:
        score += 3
    
    return min(score, 15)

def calculate_component_scores(item):
    """Calculate all component scores for a horse"""
    form = str(item.get('form', ''))
    odds = item.get('odds', 5.0)
    trainer = str(item.get('trainer', ''))
    jockey = str(item.get('jockey', ''))
    course = str(item.get('course', ''))
    
    components = {
        'form_score': calculate_form_score(form),
        'class_score': calculate_class_score(odds),
        'weight_score': calculate_weight_score(),
        'jockey_score': calculate_jockey_score(jockey),
        'trainer_score': calculate_trainer_score(trainer),
        'distance_score': calculate_distance_score(),
        'track_score': calculate_track_score(course, form),
        'pace_score': calculate_pace_score(),
        'value_score': calculate_value_score(odds),
        'recent_performance_score': calculate_recent_performance_score(form)
    }
    
    total = sum(components.values())
    components['calculated_total'] = total
    
    return components

def fix_todays_scores(bet_date=None):
    """Fix component scores for all horses on a given date"""
    if not bet_date:
        bet_date = datetime.now().strftime('%Y-%m-%d')
    print(f"\n{'='*80}")
    print(f"FIXING COMPONENT SCORES FOR {bet_date}")
    print(f"{'='*80}\n")
    
    # Get all items for the date
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(bet_date)
    )
    
    items = response.get('Items', [])
    print(f"Found {len(items)} horses to process\n")
    
    updated_count = 0
    
    for item in items:
        horse = item.get('horse', 'Unknown')
        bet_id = item.get('bet_id')
        
        # Calculate component scores
        components = calculate_component_scores(item)
        
        # Update in database
        try:
            update_expr = 'SET '
            expr_values = {}
            
            for key, value in components.items():
                update_expr += f'{key} = :{key}, '
                expr_values[f':{key}'] = Decimal(str(value))
            
            # Remove trailing comma
            update_expr = update_expr.rstrip(', ')
            
            table.update_item(
                Key={'bet_date': bet_date, 'bet_id': bet_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            
            updated_count += 1
            
            # Show first 10 in detail
            if updated_count <= 10:
                print(f"✓ {horse:30} - Components: Form:{components['form_score']}/25 Class:{components['class_score']}/15 Trainer:{components['trainer_score']}/10 Total:{components['calculated_total']}/100")
        
        except Exception as e:
            print(f"✗ Error updating {horse}: {e}")
    
    print(f"\n{'='*80}")
    print(f"✓ Updated {updated_count}/{len(items)} horses with component scores")
    print(f"{'='*80}\n")
    
    return updated_count

if __name__ == '__main__':
    # Fix today's scores
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    fix_todays_scores(today)
    
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    # Verify by checking a few picks
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
    )
    
    items = response.get('Items', [])
    top_picks = sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[:5]
    
    print("\nTop 5 picks with component scores:\n")
    for i, item in enumerate(top_picks, 1):
        print(f"{i}. {item.get('horse')} - {item.get('course')}")
        print(f"   Comprehensive: {item.get('comprehensive_score', 0)}/100")
        print(f"   Form: {item.get('form_score', 0)}/25")
        print(f"   Class: {item.get('class_score', 0)}/15")
        print(f"   Trainer: {item.get('trainer_score', 0)}/10")
        print(f"   Jockey: {item.get('jockey_score', 0)}/10")
        print(f"   Value: {item.get('value_score', 0)}/5")
        print(f"   Recent Perf: {item.get('recent_performance_score', 0)}/10")
        print(f"   Calculated Total: {item.get('calculated_total', 0)}/100")
        print()

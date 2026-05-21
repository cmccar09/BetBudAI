"""
Store ALL analyzed horses (picks + rejects) for comprehensive learning
This enables:
- Missed winner analysis
- Filter calibration
- Understanding why horses were rejected
"""
import boto3
import json
from datetime import datetime
from decimal import Decimal

# Elite lists
ELITE_TRAINERS = [
    'nicholls', 'mullins', 'elliott', 'henderson', 'skelton', 'hobbs', 
    'tizzard', 'pipe', 'twiston-davies', 'king', 'carroll', 'barron',
    'murphy', 'williams', 'mcmanus', 'appleby', 'haggas', 'gosden', 'stoute'
]

ELITE_JOCKEYS = [
    'blackmore', 'townend', 'coleman', 'walsh', 'power', 'de boinville',
    'moore', 'oisin murphy', 'william buick', 'frankie dettori', 'james doyle',
    'keane', 'geraghty'
]

def calculate_form_score(form_string):
    if not form_string or form_string == 'Unknown':
        return 0
    score = 0
    pull_ups = form_string.count('P') + form_string.count('p')
    score -= pull_ups * 8
    cleaned = ''.join(c for c in form_string if c.isdigit())
    if not cleaned:
        return max(0, int(score))
    positions = [int(c) for c in cleaned[:5]]
    position_scores = {1: 15, 2: 9, 3: 5, 4: 2, 5: 0, 6: -2, 7: -3, 8: -5, 9: -6, 0: -8}
    weights = [0.50, 0.30, 0.15, 0.03, 0.02]
    for idx, pos in enumerate(positions):
        if idx < len(weights):
            pos_score = position_scores.get(pos, -8)
            score += pos_score * weights[idx]
    wins = sum(1 for p in positions if p == 1)
    score += wins * 5
    return min(max(0, int(score)), 25)

def calculate_class_score(odds):
    try:
        odds_val = float(odds)
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

def calculate_trainer_score(trainer):
    if not trainer:
        return 2
    trainer_lower = trainer.lower()
    for elite in ELITE_TRAINERS:
        if elite in trainer_lower:
            return 5
    return 3

def calculate_jockey_score(jockey):
    if not jockey:
        return 3
    jockey_lower = jockey.lower()
    for elite in ELITE_JOCKEYS:
        if elite in jockey_lower:
            return 10
    return 4

def calculate_value_score(odds):
    try:
        odds_val = float(odds)
        if 3.0 <= odds_val <= 9.0:
            return 5
        elif 2.0 <= odds_val < 3.0 or 9.0 < odds_val <= 12.0:
            return 3
        else:
            return 1
    except:
        return 2

def calculate_recent_performance_score(form):
    if not form:
        return 2
    if 'P' in form[:10] or 'p' in form[:10]:
        return 0
    cleaned = ''.join(c for c in form if c.isdigit())\n    if not cleaned:
        return 2
    last_3 = [int(c) for c in cleaned[:3]]
    if last_3[0] == 1:
        score = 15
    elif last_3[0] in [2, 3]:
        score = 10
    elif last_3[0] == 4:
        score = 6
    else:
        score = 3
    top_3_count = sum(1 for p in last_3 if p <= 3)
    if top_3_count >= 2:
        score += 3
    return min(score, 15)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Load Betfair data
with open('response_horses.json', 'r') as f:
    betfair_data = json.load(f)

races = betfair_data.get('races', [])
today = datetime.now().strftime('%Y-%m-%d')

print(f"Storing ALL analyzed horses for {today}")
print("="*80)

total_stored = 0
total_skipped = 0

for race in races:
    course = race['course']
    race_name = race['market_name']
    race_time = race['start_time']
    
    print(f"\n{course} {race_time[:16]} - {race_name}")
    print(f"  Runners: {len(race['runners'])}")
    
    for runner in race['runners']:
        horse_name = runner['name']
        odds = float(runner.get('odds', 5.0))
        form = runner.get('form', '')
        trainer = runner.get('trainer', '')
        jockey = runner.get('jockey', '')
        selection_id = str(runner.get('selectionId', ''))
        
        # Calculate comprehensive score
        form_score = calculate_form_score(form)
        class_score = calculate_class_score(odds)
        trainer_score = calculate_trainer_score(trainer)
        jockey_score = calculate_jockey_score(jockey)
        value_score = calculate_value_score(odds)
        recent_perf = calculate_recent_performance_score(form)
        
        # Simple total (same logic as comprehensive_workflow.py)
        comprehensive_score = (
            form_score + class_score + trainer_score + jockey_score +
            value_score + recent_perf + 15  # Base scores
        )
        
        # Determine if this would be shown in UI
        show_in_ui = comprehensive_score >= 70
        recommended = comprehensive_score >= 85
        
        # Create bet_id
        bet_id = f"{race_time}_{course}_{horse_name.replace(' ', '_')}"
        
        # Check if already exists
        try:
            existing = table.get_item(
                Key={'bet_date': today, 'bet_id': bet_id}
            )
            if 'Item' in existing:
                print(f"    ✓ {horse_name[:30]:30} {comprehensive_score:3.0f}/100 (exists)")
                total_skipped += 1
                continue
        except:
            pass
        
        # Store ALL horses
        item = {
            'bet_date': today,
            'bet_id': bet_id,
            'horse': horse_name,
            'course': course,
            'race_name': race_name,
            'race_time': race_time,
            'odds': Decimal(str(odds)),
            'form': form,
            'trainer': trainer,
            'jockey': jockey if jockey else 'Unknown',
            'selection_id': selection_id,
            'comprehensive_score': Decimal(str(comprehensive_score)),
            'combined_confidence': Decimal(str(comprehensive_score)),
            'race_coverage_pct': Decimal('100'),
            'form_score': Decimal(str(form_score)),
            'class_score': Decimal(str(class_score)),
            'trainer_score': Decimal(str(trainer_score)),
            'jockey_score': Decimal(str(jockey_score)),
            'value_score': Decimal(str(value_score)),
            'recent_performance_score': Decimal(str(recent_perf)),
            'show_in_ui': show_in_ui,
            'recommended_bet': recommended,
            'outcome': 'pending',
            'bet_type': 'WIN',
            'analysis_method': 'COMPREHENSIVE_ALL_HORSES',
            'timestamp': datetime.now().isoformat(),
            'stake': Decimal('0')  # 0 for non-picks
        }
        
        try:
            table.put_item(Item=item)
            status = "UI" if show_in_ui else "hidden"
            print(f"    + {horse_name[:30]:30} {comprehensive_score:3.0f}/100 ({status})")
            total_stored += 1
        except Exception as e:
            print(f"    ✗ Error storing {horse_name}: {e}")

print(f"\n{'='*80}")
print(f"Stored {total_stored} new horses")
print(f"Skipped {total_skipped} existing horses")
print(f"Total in database: {total_stored + total_skipped}")
print(f"\nNow the learning system can analyze:")
print(f"  - Which picks won/lost")
print(f"  - Which non-picks won (missed opportunities)")
print(f"  - Score distribution vs outcomes")
print(f"  - Filter effectiveness")

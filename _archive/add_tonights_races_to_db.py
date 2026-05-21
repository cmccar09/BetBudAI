import boto3
import json
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Load tonight's picks
with open('tonights_picks.json', 'r') as f:
    data = json.load(f)

print(f"\n{'='*80}")
print("ADDING TONIGHT'S PICKS TO DYNAMODB")
print(f"{'='*80}\n")

today = datetime.now().strftime('%Y-%m-%d')
added_count = 0

for pick in data['picks']:
    race_time = pick['race_time']
    horse = pick['horse']
    odds = Decimal(str(pick['odds']))
    
    # Parse race time to create bet_id
    race_dt = datetime.fromisoformat(race_time.replace('Z', '+00:00'))
    bet_id = f"{race_time}_{data['venue']}_{horse}"
    
    # Check if already exists
    try:
        existing = table.get_item(Key={'bet_date': today, 'bet_id': bet_id})
        if 'Item' in existing:
            print(f"⏭️  {race_dt.strftime('%H:%M')} {horse} @ {odds} - Already in database")
            continue
    except:
        pass
    
    # Add to database
    item = {
        'bet_date': today,
        'bet_id': bet_id,
        'race_time': race_time,
        'horse': horse,
        'course': data['venue'],
        'odds': odds,
        'confidence': pick['confidence'],
        'form': pick.get('form', ''),
        'trainer': pick.get('trainer', ''),
        'race_name': pick.get('race_name', ''),
        'reasoning': pick['reasoning'],
        'stake': Decimal('6.0'),  # €6 as per RECOMMENDED STAKE
        'bet_type': 'WIN',
        'outcome': 'pending',
        'show_in_ui': True,  # CRITICAL: Make visible on UI
        'strategy': data['strategy'],
        'timestamp': datetime.now().isoformat()
    }
    
    table.put_item(Item=item)
    print(f"✓ {race_dt.strftime('%H:%M')} {horse} @ {odds} - {pick['confidence']} confidence")
    added_count += 1

print(f"\n{'='*80}")
print(f"✓ Added {added_count} picks to database")
print(f"√ All picks have show_in_ui=True - will appear on UI")
print(f"{'='*80}\n")

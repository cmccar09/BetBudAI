import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('BettingPicks')

print("\n" + "="*80)
print("ADDING TONIGHT'S WOLVERHAMPTON PICKS TO UI")
print("="*80)

picks = [
    {
        'time': '19:00',
        'horse': 'Skycutter',
        'odds': Decimal('3.35'),
        'form': '97769-3',
        'race_name': '1m6f Hcap',
        'confidence': 'MEDIUM',
        'reasoning': 'Edge of sweet spot (3.35). Recent 3rd place shows form. No horses in optimal 4-6 zone.',
        'why_selected': [
            'In sweet spot range (3-9 odds)',
            'Recent form shows 3rd place',
            'Best available in this race',
            'Based on 80% win rate today'
        ]
    },
    {
        'time': '19:30',
        'horse': 'Market House',
        'odds': Decimal('5.9'),
        'form': '112215-',
        'trainer': 'James Owen',
        'race_name': '2m Hcap',
        'confidence': 'HIGH',
        'reasoning': 'EXCELLENT form: 1st, 1st, 2nd, 2nd, 1st, 5th. Only 1.15 away from optimal 4.75. In perfect sweet spot zone.',
        'why_selected': [
            'In optimal zone (4-6 odds) - only 1.15 from 4.75',
            'Exceptional recent form: multiple wins and places',
            'Matches today\'s 80% success pattern',
            'James Owen trainer'
        ]
    },
    {
        'time': '20:00',
        'horse': 'Crimson Rambler',
        'odds': Decimal('4.0'),
        'form': '0876-',
        'trainer': 'George Scott',
        'race_name': '7f Hcap',
        'confidence': 'HIGH',
        'reasoning': 'PERFECT match to today\'s winners (4.0, 4.0, 5.0, 6.0). Only 0.75 from optimal 4.75. Exact odds as 2 winners today.',
        'why_selected': [
            'Exact match to today\'s winning odds (4.0)',
            'Only 0.75 from optimal (4.75)',
            'In optimal zone (4-6 odds)',
            'Today had TWO winners @ 4.0'
        ]
    }
]

added_count = 0

for pick in picks:
    bet_id = f"2026-02-02T{pick['time'].replace(':', '')}00.000Z_Wolverhampton_{pick['horse'].replace(' ', '_')}"
    
    try:
        item = {
            'bet_date': '2026-02-02',
            'bet_id': bet_id,
            'horse': pick['horse'],
            'odds': pick['odds'],
            'course': 'Wolverhampton',
            'race_time': f"2026-02-02T{pick['time']}:00.000Z",
            'race_name': pick['race_name'],
            'form': pick['form'],
            'confidence': pick['confidence'],
            'analysis_method': 'SWEET_SPOT',
            'sweet_spot_validated': True,
            'show_in_ui': True,
            'reasoning': pick['reasoning'],
            'why_selected': pick['why_selected'],
            'outcome': 'pending',
            'created_at': datetime.now().isoformat(),
            'strategy': 'Wolverhampton 80% sweet spot (4-6 optimal)',
            'todays_performance': '4/5 wins (80%)',
            'optimal_odds': Decimal('4.75')
        }
        
        # Add trainer if present
        if 'trainer' in pick:
            item['trainer'] = pick['trainer']
        
        table.put_item(Item=item)
        
        print(f"\n✓ Added: {pick['time']} - {pick['horse']} @ {pick['odds']}")
        print(f"  Confidence: {pick['confidence']}")
        print(f"  Reasoning: {pick['reasoning'][:80]}...")
        
        added_count += 1
        
    except Exception as e:
        print(f"\n✗ Error adding {pick['horse']}: {e}")

print(f"\n{'='*80}")
print(f"SUMMARY: Added {added_count} picks to UI")
print("="*80)

# Verify what's visible in UI
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-02')
)

visible = [item for item in response['Items'] if item.get('show_in_ui') == True]

print(f"\nTotal visible picks in UI: {len(visible)}")
print("\nTonight's picks:")
for item in sorted(visible, key=lambda x: x.get('race_time', '')):
    race_time = item.get('race_time', '')[:16] if item.get('race_time') else 'Unknown'
    print(f"  {race_time} - {item.get('horse')} @ {item.get('odds')} ({item.get('confidence', 'N/A')})")

print("\n" + "="*80)
print("Picks are now live on the UI!")
print("Users will see tonight's Wolverhampton races with confidence levels")
print("="*80 + "\n")

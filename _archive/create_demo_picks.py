#!/usr/bin/env python3
"""Generate sample picks for today to demonstrate the UI"""

import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import random

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('SureBetBets')

# Sample venues and horses
venues = ['Cheltenham', 'Newmarket', 'York', 'Ascot', 'The Curragh']
prefixes = ['Speed', 'Swift', 'Lucky', 'Royal', 'Golden']
suffixes = ['Runner', 'Flash', 'King', 'Spirit', 'Star']

today = datetime.now().strftime('%Y-%m-%d')
base_time = datetime.now() + timedelta(hours=2)

print(f"Generating 5 demo picks for {today}...")
print("="*70)

picks = []

for i in range(5):
    race_time = base_time + timedelta(minutes=30*i)
    horse = f"{random.choice(prefixes)} {random.choice(suffixes)}"
    venue = random.choice(venues)
    odds = round(random.uniform(2.5, 8.0), 2)
    confidence = 90 - (i * 5)  # Descending confidence
    roi = round(random.uniform(8.0, 18.0), 2)
    p_win = round(confidence / 100.0 * 0.4, 2)  # Rough estimate
    
    bet_id = f"{race_time.isoformat()}Z_{horse}"
    
    item = {
        'bet_id': bet_id,
        'bet_date': today,
        'date': today,
        'timestamp': datetime.now().isoformat(),
        'horse': horse,
        'course': venue,
        'race_time': race_time.isoformat() + 'Z',
        'bet_type': 'WIN',
        'odds': Decimal(str(odds)),
        'p_win': Decimal(str(p_win)),
        'confidence': Decimal(str(confidence)),
        'roi': Decimal(str(roi)),
        'recommendation': 'BET' if confidence >= 75 and roi >= 15 else 'CONSIDER',
        'why_now': f"Strong {confidence}% confidence with {roi}% ROI. Race in optimal betting window.",
        'market_id': f"1.{random.randint(250000000, 260000000)}",
        'selection_id': str(random.randint(10000000, 99999999)),
        'outcome': None,
        'actual_position': None,
        'learning_notes': None,
        'feedback_processed': False,
        'ev': Decimal(str(round(roi / 100, 4))),
        'audit': {
            'created_by': 'demo_generator',
            'created_at': datetime.now().isoformat(),
            'status': 'pending_outcome'
        },
        'bet': {
            'horse': horse,
            'course': venue,
            'race_time': race_time.isoformat() + 'Z',
            'bet_type': 'WIN',
            'odds': Decimal(str(odds)),
            'p_win': Decimal(str(p_win)),
            'confidence': Decimal(str(confidence)),
            'roi': Decimal(str(roi)),
            'recommendation': 'BET' if confidence >= 75 and roi >= 15 else 'CONSIDER',
            'why_now': f"Strong {confidence}% confidence with {roi}% ROI. Race in optimal betting window.",
            'ev': Decimal(str(round(roi / 100, 4)))
        }
    }
    
    table.put_item(Item=item)
    picks.append(item)
    
    print(f"{i+1}. {horse} @ {venue} - {race_time.strftime('%H:%M')}")
    print(f"   Confidence: {confidence}% | ROI: {roi}% | Odds: {odds} | {item['recommendation']}")

print("="*70)
print(f"✓ Created {len(picks)} picks for {today}")
print("\nView them at: https://d2hmpykfsdweob.amplifyapp.com/")

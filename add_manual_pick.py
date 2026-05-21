"""Add Saladins Son (17:05 Haydock) as a manual pick to DynamoDB"""
import boto3
import uuid
from decimal import Decimal
from datetime import datetime

db    = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

bet_id   = f"manual_{uuid.uuid4().hex[:12]}"
bet_date = '2026-04-04'

item = {
    'bet_date':           bet_date,
    'bet_id':             bet_id,
    'horse':              'Saladins Son',
    'course':             'Haydock',
    'race_time':          '2026-04-04T17:05:00',
    'odds':               Decimal('4.5'),   # 9/2
    'odds_fraction':      '9/2',
    'stake':              Decimal('2'),
    'bet_type':           'Each Way',
    'trainer':            'Anthony Honeyball',
    'jockey':             'Jonathan Burke',
    'result':             'PENDING',
    'outcome':            'PENDING',
    'result_emoji':       'PENDING',
    'profit_loss':        Decimal('0'),
    'show_in_ui':         True,
    'is_learning_pick':   False,
    'manual_pick':        True,
    'analysis_note':      'C&D form (2nd+4th at Haydock 3m1f GS), OR 122 top-rated, 4 places paid',
    'comprehensive_score': Decimal('82'),
    'created_at':         datetime.utcnow().isoformat(),
}

table.put_item(Item=item)
print(f"Added: Saladins Son @ 9/2 EW | Haydock 17:05 | bet_id={bet_id}")

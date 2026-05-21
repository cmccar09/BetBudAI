"""Re-add Saladins Son with correct stake."""
import boto3
import uuid
from decimal import Decimal
from datetime import datetime, timezone

db    = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

bet_id   = f"manual_{uuid.uuid4().hex[:12]}"
bet_date = '2026-04-04'

item = {
    'bet_date':            bet_date,
    'bet_id':              bet_id,
    'horse':               'Saladins Son',
    'course':              'Haydock',
    'race_time':           '2026-04-04T17:05:00',
    'odds':                Decimal('4.5'),
    'odds_fraction':       '9/2',
    'stake':               Decimal('50'),
    'bet_type':            'Each Way',
    'trainer':             'Anthony Honeyball',
    'jockey':              'Jonathan Burke',
    'result':              'PENDING',
    'outcome':             'PENDING',
    'result_emoji':        'PENDING',
    'profit_loss':         Decimal('0'),
    'show_in_ui':          True,
    'is_learning_pick':    False,
    'manual_pick':         True,
    'analysis_note':       'C&D form (2nd+4th Haydock 3m1f GS), OR 122 top-rated, 4 places paid',
    'comprehensive_score': Decimal('82'),
    'created_at':          datetime.now(timezone.utc).isoformat(),
}

table.put_item(Item=item)
print(f"Added: Saladins Son @ 9/2 EW | €50 EW stake | Haydock 17:05 | bet_id={bet_id}")

# Verify it's there
from boto3.dynamodb.conditions import Key
resp = table.get_item(Key={'bet_date': bet_date, 'bet_id': bet_id})
stored = resp.get('Item', {})
print(f"Verified: horse={stored.get('horse')}, stake={stored.get('stake')}, show_in_ui={stored.get('show_in_ui')}")

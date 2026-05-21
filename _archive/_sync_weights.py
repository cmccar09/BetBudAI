"""Sync DEFAULT_WEIGHTS → DynamoDB SYSTEM_WEIGHTS record"""
import boto3
from decimal import Decimal
from comprehensive_pick_logic import DEFAULT_WEIGHTS

ddb   = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# Read current DB weights
r = table.get_item(Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'})
if 'Item' in r:
    db_weights = dict(r['Item'].get('weights', {}))
    print('Current DB aw_low_class_penalty:', db_weights.get('aw_low_class_penalty', 'NOT SET'))
    print('Current DB heavy_going_penalty: ', db_weights.get('heavy_going_penalty', 'NOT SET'))
else:
    db_weights = {}
    print('No SYSTEM_WEIGHTS record — will create one')

# Merge DEFAULT_WEIGHTS on top (DEFAULT is the authoritative source)
merged = {k: Decimal(str(v)) for k, v in DEFAULT_WEIGHTS.items()}

table.put_item(Item={
    'bet_id':   'SYSTEM_WEIGHTS',
    'bet_date': 'CONFIG',
    'weights':  merged,
    'version':  'v4.4',
    'last_updated': '2026-03-17',
    'notes': 'aw_low_class_penalty raised to 50, heavy_going_penalty added at 12',
})

print('Updated SYSTEM_WEIGHTS in DynamoDB:')
print(f'  aw_low_class_penalty : {DEFAULT_WEIGHTS["aw_low_class_penalty"]}')
print(f'  heavy_going_penalty  : {DEFAULT_WEIGHTS["heavy_going_penalty"]}')
print(f'  (total weights synced: {len(merged)})')

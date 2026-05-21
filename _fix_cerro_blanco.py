"""Fix Cerro Blanco fav_outcome: was incorrectly set to 'loss' (race_winner=Talk Of New York)
but Cerro Blanco actually WON the 13:15 Newmarket (12:15 UTC)."""
import boto3
from boto3.dynamodb.conditions import Key

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-14'))
items = resp['Items']

# Find Cerro Blanco's bet_id
for it in items:
    if it.get('horse', '') == 'Cerro Blanco' and '12:15' in it.get('race_time', ''):
        bet_id = it['bet_id']
        print(f"Found: {it['horse']} bet_id={bet_id}")
        print(f"  BEFORE: fav_outcome={it.get('fav_outcome')}, race_winner_name={it.get('race_winner_name')}")
        
        tbl.update_item(
            Key={'bet_date': '2026-04-14', 'bet_id': bet_id},
            UpdateExpression='SET fav_outcome = :fo, race_winner_name = :wn',
            ExpressionAttributeValues={':fo': 'win', ':wn': 'Cerro Blanco'},
        )
        
        # Verify
        updated = tbl.get_item(Key={'bet_date': '2026-04-14', 'bet_id': bet_id})['Item']
        print(f"  AFTER:  fav_outcome={updated.get('fav_outcome')}, race_winner_name={updated.get('race_winner_name')}")
        break

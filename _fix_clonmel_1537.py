"""Fix Clonmel 15:37 race: Arcadian Emperor is the true favourite (1.74), not Lamikal Dairy (odds=0 = missing)."""
import boto3
from boto3.dynamodb.conditions import Key

REGION = 'eu-west-1'
DATE_STR = '2026-04-14'

tbl = boto3.resource('dynamodb', region_name=REGION).Table('SureBetBets')
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq(DATE_STR))
items = [dict(it) for it in resp['Items']]

clonmel = [it for it in items if 'clonmel' in str(it.get('course', '')).lower() and '15:37' in str(it.get('race_time', ''))]

for it in clonmel:
    horse = it.get('horse', '')
    bet_id = it['bet_id']

    if horse == 'Arcadian Emperor':
        print(f"Setting Arcadian Emperor fav_outcome=win (true fav, odds=1.74, WON the race)")
        tbl.update_item(
            Key={'bet_date': DATE_STR, 'bet_id': bet_id},
            UpdateExpression='SET fav_outcome = :fo, race_winner_name = :wn',
            ExpressionAttributeValues={':fo': 'win', ':wn': 'Arcadian Emperor'},
        )

    elif horse == 'Lamikal Dairy':
        print(f"Removing Lamikal Dairy fav_outcome (odds=0 = missing data, NOT the real favourite)")
        tbl.update_item(
            Key={'bet_date': DATE_STR, 'bet_id': bet_id},
            UpdateExpression='REMOVE fav_outcome, race_winner_name',
        )

print("Done!")

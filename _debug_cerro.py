import boto3
from boto3.dynamodb.conditions import Key

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-14'))
items = resp['Items']

# Show ALL favs with fav_outcome and their race_winner_name
for it in items:
    fo = it.get('fav_outcome', '')
    if fo:
        horse = it.get('horse', '')
        rt = it.get('race_time', '')
        course = it.get('race_course', '') or it.get('course', '')
        rwn = it.get('race_winner_name', '')
        print(f"{rt[11:16]} {course:15s} | fav={horse:25s} | fav_outcome={fo:4s} | race_winner={rwn}")

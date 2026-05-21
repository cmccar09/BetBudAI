import boto3
from boto3.dynamodb.conditions import Attr

db = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

horses = [
    'Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted',
    'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan'
]

for horse in horses:
    resp = tbl.scan(FilterExpression=Attr('horse').eq(horse))
    items = resp.get('Items', [])
    if items:
        for it in items:
            outcome = it.get('outcome', '-')
            pos = it.get('finish_position', it.get('position', '-'))
            winner = it.get('result_winner_name', '-')
            bdate = it.get('bet_date', '-')
            course = it.get('course', '-')
            print(f"{horse} | {bdate} | {course} | outcome={outcome} | pos={pos} | winner={winner}")
    else:
        print(f"{horse} | NOT IN DB")

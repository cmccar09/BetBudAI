"""
One-shot: update Pertemps DynamoDB record to Supremely West (3/1, Skelton/Skelton)
SureBet pick = Supremely West | MacFitz pick = Ace Of Spades
"""
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime, timedelta

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('CheltenhamPicks')

# Scan last 5 days for Pertemps records
base = datetime.now().date()
dates = [(base - timedelta(days=n)).strftime('%Y-%m-%d') for n in range(5)]
found = []
for d in dates:
    resp = table.scan(FilterExpression=Attr('pick_date').eq(d))
    for item in resp['Items']:
        rn = item.get('race_name', '')
        if 'pertemps' in rn.lower() or 'Pertemps' in rn:
            found.append(item)
            print(f"Found: race_name='{rn}' horse='{item.get('horse')}' date='{d}' pk={item.get('race_name')} sk={item.get('pick_date')}")

if not found:
    print("No Pertemps record found in last 5 days.")
else:
    for item in found:
        rn = item['race_name']
        pd = item['pick_date']
        print(f"\nUpdating {rn} / {pd}: {item.get('horse')} -> Supremely West")
        # Update pick to Supremely West (SureBet), note MacFitz=Ace Of Spades in reason
        table.update_item(
            Key={'race_name': rn, 'pick_date': pd},
            UpdateExpression="""SET horse=:h, trainer=:t, jockey=:j, odds=:o,
                                    confidence=:c, bet_recommendation=:br,
                                    change_reason=:cr, pick_changed=:pc,
                                    previous_horse=:ph""",
            ExpressionAttributeValues={
                ':h':  'Supremely West',
                ':t':  'Dan Skelton',
                ':j':  'Harry Skelton',
                ':o':  '3/1',
                ':c':  'STRONG (market mover, Skelton two-hander target)',
                ':br': False,
                ':cr': 'LIVE SPLIT 12/03/2026: Skelton two-runner race. SureBet=Supremely West (3/1, Harry Skelton, stable first-string, D symbol, 2lb less than Oct run). MacFitz=Ace Of Spades (16/1, C winner, soft-ground qualifier Jan 2026 EW). Staffordshire Knot (model #1, topweight 152, all wins heavy Irish mud, no C/D) overridden.',
                ':pc': True,
                ':ph': item.get('horse', 'Staffordshire Knot'),
            }
        )
        print(f"Updated OK.")
    print("\nDone.")

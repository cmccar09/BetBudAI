"""
Fix today's DB issues:
1. Set show_in_ui=False for Halftheworldaway (14:15+0100) and Crack Ops (13:15+0100) - retrospective
2. Fix Simplify race_time from T18:30:00+00:00 to T19:30:00+01:00 (BST display fix)
"""
import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# ── 1. Fix retrospective picks ─────────────────────────────────
retrospective = [
    ('2026-03-31', "2026-03-31T141500+0100_Bangor-on-Dee_Halftheworldaway"),
    ('2026-03-31', "2026-03-31T131500+0100_Bangor-on-Dee_Crack Ops"),
]

for bet_date, bet_id in retrospective:
    table.update_item(
        Key={'bet_date': bet_date, 'bet_id': bet_id},
        UpdateExpression='SET show_in_ui = :f',
        ExpressionAttributeValues={':f': False}
    )
    print(f'Retrospective hidden: {bet_id}')

# ── 2. Fix Simplify race_time (18:30 UTC → 19:30 BST) ─────────
# Find the Simplify +00:00 record
resp = table.query(KeyConditionExpression='bet_date = :d', ExpressionAttributeValues={':d': '2026-03-31'})

for item in resp['Items']:
    if item.get('horse') == 'Simplify' and 'Wolverhampton' in str(item.get('course', '')):
        bet_id = item['bet_id']
        old_rt = str(item.get('race_time', ''))
        print(f'Found Simplify: bet_id={bet_id}  race_time={old_rt}')
        if '+00:00' in old_rt and 'T18:30' in old_rt:
            new_rt = '2026-03-31T19:30:00+01:00'
            table.update_item(
                Key={'bet_date': '2026-03-31', 'bet_id': bet_id},
                UpdateExpression='SET race_time = :rt',
                ExpressionAttributeValues={':rt': new_rt}
            )
            print(f'  Updated race_time: {old_rt} -> {new_rt}')

print('\nDone.')

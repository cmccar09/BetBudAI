"""
Hide Egbert, Ribee, and Court In A Storm from the 2026-03-23 results.
These were incorrectly stored with show_in_ui=True due to a lower score
threshold (75) in enforce_comprehensive_analysis.py (now fixed to 85).
"""
import boto3
from boto3.dynamodb.conditions import Key

ddb   = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

DATE = '2026-03-23'

TARGETS = [
    {'horse': 'Egbert',           'course': 'Exeter', 'approx_time': '15:02'},
    {'horse': 'Ribee',            'course': 'Naas',   'approx_time': '16:22'},
    {'horse': 'Court In A Storm', 'course': 'Exeter', 'approx_time': '16:47'},
]

REASON = 'Manual override: score below 85-point UI threshold — removed from results display'

# Fetch all items for the date
resp  = table.query(KeyConditionExpression=Key('bet_date').eq(DATE))
items = resp['Items']
while 'LastEvaluatedKey' in resp:
    resp  = table.query(
        KeyConditionExpression=Key('bet_date').eq(DATE),
        ExclusiveStartKey=resp['LastEvaluatedKey']
    )
    items.extend(resp['Items'])

print(f"Fetched {len(items)} items for {DATE}")

for target in TARGETS:
    match = next(
        (i for i in items
         if i.get('horse', '').strip().lower() == target['horse'].lower()
         and i.get('course', '').strip().lower() == target['course'].lower()),
        None
    )
    if not match:
        print(f"  NOT FOUND: {target['horse']} @ {target['course']}")
        continue

    table.update_item(
        Key={'bet_date': match['bet_date'], 'bet_id': match['bet_id']},
        UpdateExpression='SET show_in_ui = :f, ui_hidden_reason = :r',
        ExpressionAttributeValues={':f': False, ':r': REASON}
    )
    score = match.get('comprehensive_score', match.get('analysis_score', '?'))
    print(f"  HIDDEN: {match['horse']} @ {match['course']} "
          f"(score={score}, bet_id={match['bet_id']})")

print("\nDone. Refresh the results page to confirm.")

"""
Update today's UI picks:
- REMOVE Fahrenheit Seven (only +1pt gap - too close to call)
- ADD Eric Carmen (16:30 Bangor, +73pts clear, score 101)
- ADD Koukeo (16:10 Newbury, +42pts clear, score 95)
- KEEP Khrisma (14:10 Kelso, +82pts clear - already in UI)
"""
import boto3
from datetime import date
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = str(date.today())
resp = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today))
items = resp['Items']

changes = 0

for item in items:
    course = item.get('course','')
    race_time = item.get('race_time','')
    horse = item.get('horse','')
    score = float(item.get('comprehensive_score', 0) or 0)
    bet_id = item.get('bet_id')
    
    # REMOVE: Fahrenheit Seven (Southwell 16:38) - only 1pt gap
    if 'Southwell' in course and '16:38' in race_time and horse == 'Fahrenheit Seven':
        table.update_item(
            Key={'bet_date': today, 'bet_id': bet_id},
            UpdateExpression='SET show_in_ui = :f, rejection_reason = :r',
            ExpressionAttributeValues={
                ':f': False,
                ':r': 'Score gap too narrow (+1pt) - model cannot separate from Gaeli with confidence'
            }
        )
        print(f"REMOVED: {horse} @ {course} {race_time}")
        changes += 1
    
    # ADD: Eric Carmen (Bangor-on-Dee 16:30, top scorer in race)
    if 'Bangor' in course and '16:30' in race_time and horse == 'Eric Carmen':
        table.update_item(
            Key={'bet_date': today, 'bet_id': bet_id},
            UpdateExpression='SET show_in_ui = :t, score_gap = :g, recommended_bet = :b',
            ExpressionAttributeValues={
                ':t': True,
                ':g': Decimal('73'),
                ':b': 'WIN'
            }
        )
        print(f"ADDED:   {horse} @ {course} {race_time} | score={score}")
        changes += 1
    
    # ADD: Koukeo (Newbury 16:10, top scorer in race)
    if 'Newbury' in course and '16:10' in race_time and horse == 'Koukeo':
        table.update_item(
            Key={'bet_date': today, 'bet_id': bet_id},
            UpdateExpression='SET show_in_ui = :t, score_gap = :g, recommended_bet = :b',
            ExpressionAttributeValues={
                ':t': True,
                ':g': Decimal('42'),
                ':b': 'WIN'
            }
        )
        print(f"ADDED:   {horse} @ {course} {race_time} | score={score}")
        changes += 1

print(f"\nTotal changes: {changes}")

# Verify final picks
resp2 = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today))
items2 = resp2['Items']
picks = [i for i in items2 if str(i.get('show_in_ui','')).lower() == 'true']
print(f"\nFinal UI picks ({len(picks)}):")
for p in sorted(picks, key=lambda x: x.get('race_time','')):
    score = float(p.get('comprehensive_score', 0) or 0)
    gap = float(p.get('score_gap', 0) or 0)
    print(f"  {p['race_time'][11:16]} {p.get('course','')} | {p.get('horse','?')} @ {p.get('odds','?')} | score={score:.0f} gap=+{gap:.0f}pts")

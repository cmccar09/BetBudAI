import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-03-30'))
items = resp['Items']

def d2f(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, dict): return {k: d2f(v) for k,v in obj.items()}
    if isinstance(obj, list): return [d2f(i) for i in obj]
    return obj

items = [d2f(i) for i in items]

# Show unique bet_id prefixes and sport values
prefixes = set()
sports = set()
for i in items:
    bid = i.get('bet_id', '')
    prefixes.add(bid.split('_')[0] if '_' in bid else bid[:10])
    sports.add(i.get('sport', ''))
print("bet_id prefixes:", sorted(prefixes))
print("sports:", sports)
print()

horse_items = [i for i in items if i.get('sport', 'horses') in ['horses', 'Horse Racing', 'horse racing']]
print("Horse items:", len(horse_items))

shown = [i for i in horse_items if i.get('show_in_ui') == True]
hidden = [i for i in horse_items if i.get('show_in_ui') == False]
no_flag = [i for i in horse_items if i.get('show_in_ui') is None]
print("show_in_ui=True:", len(shown), "False:", len(hidden), "None:", len(no_flag))
print()

print("=== show_in_ui=True ===")
for h in sorted(shown, key=lambda x: x.get('race_time', '')):
    rt = h.get('race_time', '')[11:16] if h.get('race_time') else '?'
    score = float(h.get('comprehensive_score', 0) or 0)
    stake = h.get('stake', 0)
    outcome = h.get('outcome', '')
    rejection = h.get('rejection_reason', '')
    course = h.get('course', '?')
    horse = h.get('horse', '?')
    gap = float(h.get('score_gap', 0) or 0)
    print("  " + rt + " | " + str(course).ljust(22) + " | " + str(horse).ljust(30) + " | score=" + str(int(score)).rjust(4) + " gap=" + str(int(gap)).rjust(4) + " | stake=" + str(stake) + " | outcome=" + str(outcome) + " | " + str(rejection))

print()
print("=== show_in_ui=False (rejected) ===")
for h in sorted(hidden, key=lambda x: x.get('race_time', '')):
    rt = h.get('race_time', '')[11:16] if h.get('race_time') else '?'
    score = float(h.get('comprehensive_score', 0) or 0)
    rejection = h.get('rejection_reason', '')
    course = h.get('course', '?')
    horse = h.get('horse', '?')
    print("  " + rt + " | " + str(course).ljust(22) + " | " + str(horse).ljust(30) + " | score=" + str(int(score)).rjust(4) + " | " + str(rejection))

print()
print("=== show_in_ui=None (no flag) - first 30 ===")
for h in sorted(no_flag, key=lambda x: x.get('race_time', ''))[:30]:
    rt = h.get('race_time', '')[11:16] if h.get('race_time') else '?'
    score = float(h.get('comprehensive_score', 0) or 0)
    course = h.get('course', '?')
    horse = h.get('horse', '?')
    stake = h.get('stake', 0)
    print("  " + rt + " | " + str(course).ljust(22) + " | " + str(horse).ljust(30) + " | score=" + str(int(score)).rjust(4) + " | stake=" + str(stake))

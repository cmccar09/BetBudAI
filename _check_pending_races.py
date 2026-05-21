"""Check pending races from the API to see if they should be settled."""
import boto3
from boto3.dynamodb.conditions import Key

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-14'))
items = resp['Items']

# Check the specific pending races from API: Arcadian Emperor (Clonmel 15:37 UTC)
# and any with fav_outcome missing
print("=== Races with fav_outcome set ===")
fav_count = 0
for it in items:
    fo = it.get('fav_outcome', '')
    if fo:
        fav_count += 1
print(f"Total items with fav_outcome: {fav_count}")

# Check for Arcadian Emperor specifically
print("\n=== Arcadian Emperor entries ===")
for it in items:
    if 'arcadian' in it.get('horse', '').lower():
        rt = str(it.get('race_time', ''))
        course = it.get('race_course', '') or it.get('course', '')
        odds = it.get('odds', '')
        fo = it.get('fav_outcome', '')
        score = it.get('comprehensive_score', '')
        print(f"  {rt} {course} odds={odds} score={score} fav_outcome={fo}")

# Check races at Leopardstown, Beverley, Haydock on Apr 14
print("\n=== Apr 14 Leopardstown/Beverley/Haydock ===")
for it in items:
    course = (it.get('race_course', '') or it.get('course', '')).lower()
    if any(c in course for c in ['leopardstown', 'beverley', 'haydock']):
        rt = str(it.get('race_time', ''))
        horse = it.get('horse', '')
        odds = it.get('odds', '')
        print(f"  {rt} {course} {horse} odds={odds}")

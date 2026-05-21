"""
One-shot script: patch DynamoDB items where course=Unknown for today (2026-04-04)
by looking up the correct course from the S3 race JSON.
"""
import boto3, json
from boto3.dynamodb.conditions import Key

TARGET_DATE = '2026-04-04'

s3 = boto3.client('s3', region_name='eu-west-1')
obj = s3.get_object(Bucket='surebet-pipeline-data', Key=f'daily/{TARGET_DATE}/response_horses.json')
data = json.loads(obj['Body'].read())
races = data.get('races', [])

# Build start_time -> course lookup
time_to_course = {}
for r in races:
    rt = r.get('start_time', r.get('race_time', ''))
    course = r.get('course') or r.get('venue') or ''
    if rt and course:
        time_to_course[rt] = course
        time_to_course[rt.replace('+00:00', '').replace('Z', '')] = course

print(f'S3 time->course entries: {len(time_to_course)}')

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

resp = table.query(KeyConditionExpression=Key('bet_date').eq(TARGET_DATE))
all_items = resp.get('Items', [])
unknowns = [x for x in all_items if x.get('course', '') == 'Unknown']
print(f'Unknown course items to patch: {len(unknowns)}')

patched = 0
for item in unknowns:
    rt = item.get('race_time', '')
    rt_clean = rt.replace('+00:00', '').replace('Z', '')
    course = time_to_course.get(rt) or time_to_course.get(rt_clean)
    if not course:
        print(f'  No S3 match for race_time: {rt}')
        continue
    table.update_item(
        Key={'bet_date': item['bet_date'], 'bet_id': item['bet_id']},
        UpdateExpression='SET course = :c, race_course = :c',
        ExpressionAttributeValues={':c': course}
    )
    patched += 1
    horse = item.get('horse', '?')
    print(f'  Patched: {horse}  {rt[:16]}  ->  {course}')

print(f'\nDone. Patched {patched}/{len(unknowns)} items.')

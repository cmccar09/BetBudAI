"""Fix all Wolverhampton records that have wrong UTC times (missing the BST +1 hour)"""
import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

resp = table.query(KeyConditionExpression='bet_date = :d', ExpressionAttributeValues={':d': '2026-03-31'})

# All Wolverhampton races stored with +00:00 (pre-fix) need their times bumped by 1 hour for display
# Race times are stored as UTC, but actual UK times are UTC+1 (BST)
# e.g. 18:30+00:00 should display as 19:30 -> store as 19:30+01:00

time_map = {
    '16:30': '17:30',
    '17:00': '18:00',
    '17:30': '18:30',
    '18:00': '19:00',
    '18:30': '19:30',
    '19:00': '20:00',
    '19:30': '20:30',
}

fixes = []
for item in resp['Items']:
    if 'Wolverhampton' not in str(item.get('course', '')):
        continue
    rt = str(item.get('race_time', ''))
    if '+00:00' not in rt:  # already fixed or different format
        continue
    # Extract HH:MM
    time_part = rt[11:16]
    if time_part in time_map:
        new_time = time_map[time_part]
        new_rt = f"2026-03-31T{new_time}:00+01:00"
        fixes.append((item['bet_date'], item['bet_id'], rt, new_rt))

print(f"Found {len(fixes)} Wolverhampton +00:00 records to fix:")
for bet_date, bet_id, old_rt, new_rt in fixes:
    horse = next((i.get('horse') for i in resp['Items'] if i['bet_id'] == bet_id), '?')
    print(f"  {horse}: {old_rt} -> {new_rt}")
    table.update_item(
        Key={'bet_date': bet_date, 'bet_id': bet_id},
        UpdateExpression='SET race_time = :rt',
        ExpressionAttributeValues={':rt': new_rt}
    )

print('\nDone. Re-running audit...')

import boto3
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

# Results: 1st Royal Velvet, 2nd Jordan Electrics, 3rd Crimson Spirit, 4th Eminency
# This is a handicap with 18 runners -> 16+ hcap = 4 places at 1/4 odds
winner = 'Royal Velvet'
finishers = {
    'Royal Velvet': 1,
    'Jordan Electrics': 2,
    'Crimson Spirit': 3,
    'Eminency': 4,
}
num_places = 4  # 18 runners handicap

from boto3.dynamodb.conditions import Key
resp = table.query(KeyConditionExpression=Key('bet_date').eq(today))
items = resp.get('Items', [])
while 'LastEvaluatedKey' in resp:
    resp = table.query(KeyConditionExpression=Key('bet_date').eq(today), ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp.get('Items', []))

updated = 0
for item in items:
    rt = item.get('race_time', '')
    course = (item.get('course', '') or '').lower()
    if 'newmarket' not in course or '16:20' not in rt:
        continue
    horse = item.get('horse', '')
    finish = finishers.get(horse, 99)
    
    if finish == 1:
        outcome = 'win'
    elif 2 <= finish <= num_places:
        outcome = 'placed'
    else:
        outcome = 'loss'
    
    table.update_item(
        Key={'bet_id': item['bet_id'], 'bet_date': item['bet_date']},
        UpdateExpression='SET outcome = :o, finish_position = :f, winner_horse = :w, result_recorded_at = :t, number_of_places = :np',
        ExpressionAttributeValues={
            ':o': outcome,
            ':f': finish,
            ':w': winner,
            ':t': datetime.now(timezone.utc).isoformat() + 'Z',
            ':np': num_places,
        }
    )
    updated += 1
    print(f"  {horse:30} -> {outcome} (finish={finish})")

print(f"\nUpdated {updated} records")

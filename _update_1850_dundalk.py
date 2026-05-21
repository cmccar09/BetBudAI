"""Record 18:50 Dundalk result: Celtic Druid WON (5/1), Jawhary 2nd (4/1 j), Desert Friend 3rd (4/1 j)"""
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Find Celtic Druid's bet_id
resp = table.query(
    KeyConditionExpression='bet_date = :d',
    FilterExpression='contains(course, :c) AND race_time = :rt',
    ExpressionAttributeValues={
        ':d': '2026-04-10',
        ':c': 'undalk',
        ':rt': '2026-04-10T18:50:00+00:00'
    }
)

items = resp.get('Items', [])
print(f"Found {len(items)} items for 18:50 Dundalk")

for item in items:
    horse = item.get('horse', '')
    bet_id = item.get('bet_id', '')
    score = item.get('comprehensive_score', 0)
    show = item.get('show_in_ui', False)
    print(f"  {horse}: score={score}, show_in_ui={show}, bet_id={bet_id[:20]}...")

# Find Celtic Druid
celtic = next((i for i in items if 'celtic druid' in i.get('horse', '').lower()), None)
if not celtic:
    print("ERROR: Celtic Druid not found!")
    exit(1)

bet_id = celtic['bet_id']
odds = float(celtic.get('odds') or celtic.get('sp_odds') or 5.0) or 5.0
print(f"\nRecording WIN for Celtic Druid (bet_id={bet_id[:20]}..., odds={odds})")

# EW bet: £50 EW = £100 total stake; at 5/1 = 6.0 decimal
# Win part: £50 * 6.0 = £300; Place part (1/5 odds): £50 * (1 + 5/5) = £50 * 2 = £100; Total return = £400, profit = £300
# Record as WIN with profit calculation
table.update_item(
    Key={'bet_date': '2026-04-10', 'bet_id': bet_id},
    UpdateExpression='''SET outcome = :outcome,
        finish_position = :fp,
        result_emoji = :emoji,
        result_winner_name = :winner,
        result_settled = :settled,
        result_analysis = :analysis,
        profit = :profit''',
    ExpressionAttributeValues={
        ':outcome': 'win',
        ':fp': Decimal('1'),
        ':emoji': 'WIN',
        ':winner': 'Celtic Druid',
        ':settled': True,
        ':analysis': 'Celtic Druid (5/1) won the 18:50 Dundalk. Jawhary (4/1 j) 2nd, Desert Friend (4/1 j) 3rd. System pick confirmed correct.',
        ':profit': Decimal('300')  # £50 EW: win leg £50*6 = £300 return + £100 place return - £100 stake = £300 profit
    }
)
print("Celtic Druid WIN recorded successfully")
print(f"  odds: 5/1 (6.0 dec)")
print(f"  profit: +£300 (£50 EW: win £300 + place £100 - £100 stake)")

from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.utcnow().strftime('%Y-%m-%d')
response = table.query(KeyConditionExpression=Key('bet_date').eq(today))
items = [i for i in response['Items'] if i.get('sport') == 'horses']

finished = [i for i in items if i.get('outcome')]
pending = [i for i in items if not i.get('outcome')]
wins = [i for i in finished if i['outcome'] == 'win']
losses = [i for i in finished if i['outcome'] == 'loss']

total_profit = sum(i.get('profit', 0) for i in finished)
total_stake = sum(i.get('stake', 0) for i in finished)

print(f'\n📊 TODAY SUMMARY ({today}):')
print(f'  {len(wins)} wins / {len(losses)} losses / {len(pending)} pending')
print(f'  Total P/L: €{total_profit:.2f} from €{total_stake:.2f} staked')
print(f'  ROI: {(total_profit/total_stake*100) if total_stake > 0 else 0:.1f}%')

if wins:
    print(f'\n✅ WINS ({len(wins)}):')
    for i in wins:
        print(f'  {i["horse"]} @ {i["course"]} - €{i["profit"]:.2f}')

if losses:
    print(f'\n❌ LOSSES ({len(losses)}):')
    for i in losses:
        print(f'  {i["horse"]} @ {i["course"]} - €{i["profit"]:.2f}')

if pending:
    print(f'\n⏳ PENDING ({len(pending)}):')
    for i in sorted(pending, key=lambda x: x['race_time']):
        print(f'  {i["horse"]} @ {i["course"]} {i["race_time"]} - {i.get("bet_type", "WIN")} €{i.get("stake", 0):.2f}')

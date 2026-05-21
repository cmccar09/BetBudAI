"""Find and fix Saladins Son record."""
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

db    = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

resp = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-04-04'),
    FilterExpression=Attr('horse').begins_with('Saladins')
)
items = resp.get('Items', [])
print(f"Found {len(items)} Saladins Son records")

for item in items:
    print(f"  bet_id={item.get('bet_id')}")
    print(f"  show_in_ui={item.get('show_in_ui')} type={type(item.get('show_in_ui'))}")
    print(f"  stake={item.get('stake')}, odds={item.get('odds')}, bet_type={item.get('bet_type')}")
    print(f"  result={item.get('result')}")

    table.update_item(
        Key={'bet_date': item['bet_date'], 'bet_id': item['bet_id']},
        UpdateExpression='SET stake = :s, bet_type = :bt, show_in_ui = :ui',
        ExpressionAttributeValues={
            ':s':  Decimal('50'),
            ':bt': 'Each Way',
            ':ui': True,
        }
    )
    print("  => Updated: stake=50, bet_type=Each Way, show_in_ui=True")

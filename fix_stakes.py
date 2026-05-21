"""Fix Team Player profit and update Saladins Son stake to €50 EW."""
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

db    = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

resp  = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-04'))
items = resp.get('Items', [])

print(f"Total items: {len(items)}")
for item in items:
    horse = item.get('horse', '')
    if 'Saladins' in horse:
        print(f"\nSaladins Son found: bet_id={item.get('bet_id')}, show_in_ui={item.get('show_in_ui')}, stake={item.get('stake')}")

        # Update stake to €50 each way, profit stays pending
        table.update_item(
            Key={'bet_date': item['bet_date'], 'bet_id': item['bet_id']},
            UpdateExpression='SET stake = :s, bet_type = :bt, show_in_ui = :ui',
            ExpressionAttributeValues={
                ':s':  Decimal('50'),
                ':bt': 'Each Way',
                ':ui': True,
            }
        )
        print("  => Updated stake to €50 EW")

    if 'Team Player' in horse and item.get('show_in_ui'):
        odds  = float(item.get('odds') or 16.5)
        stake = Decimal('2')
        # WIN: profit = stake * (odds - 1)
        profit = round(stake * Decimal(str(odds - 1)), 2)
        print(f"\nTeam Player: odds={odds}, stake=2, calculated profit=+£{profit}")

        table.update_item(
            Key={'bet_date': item['bet_date'], 'bet_id': item['bet_id']},
            UpdateExpression='SET stake = :s, profit_loss = :pl',
            ExpressionAttributeValues={
                ':s':  stake,
                ':pl': Decimal(str(profit)),
            }
        )
        print("  => Updated stake and profit_loss")

print("\nDone.")

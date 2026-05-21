#!/usr/bin/env python3
"""Update Mask Of Zorro to WON"""

import boto3
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Get all today's picks
response = table.scan(
    FilterExpression='#d = :today',
    ExpressionAttributeNames={'#d': 'date'},
    ExpressionAttributeValues={':today': '2026-01-23'}
)

items = response.get('Items', [])
print(f'\nToday\'s picks:')
print('='*70)

mask_pick = None
for item in items:
    horse = item.get('horse', 'Unknown')
    course = item.get('course', 'Unknown')
    print(f'  {horse} @ {course}')
    
    if 'Mask' in horse or 'Zorro' in horse:
        mask_pick = item

print('='*70)

if mask_pick:
    bet_id = mask_pick.get('bet_id')
    horse = mask_pick.get('horse')
    course = mask_pick.get('course')
    odds = float(mask_pick.get('odds', 3.3))
    stake = float(mask_pick.get('stake', 20))
    bet_type = mask_pick.get('bet_type', 'WIN')
    
    print(f'\n🏆 WINNER FOUND!')
    print(f'  Horse: {horse}')
    print(f'  Course: {course}')
    print(f'  Odds: {odds}')
    print(f'  Stake: £{stake}')
    print(f'  Bet Type: {bet_type}')
    
    # Calculate profit for WIN bet
    profit = stake * (odds - 1)
    
    print(f'  💰 Profit: £{profit:.2f}')
    
    # Update the record
    try:
        table.update_item(
            Key={'bet_id': bet_id},
            UpdateExpression='SET outcome = :outcome, profit = :profit, audit.#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':outcome': 'won',
                ':profit': Decimal(str(round(profit, 2))),
                ':status': 'settled'
            }
        )
        
        print(f'\n✅ SUCCESS! Updated {horse} to WON with profit £{profit:.2f}')
    except Exception as e:
        print(f'\n❌ Error updating: {e}')
        print('Trying alternative key...')
        # Try with different primary key structure
        try:
            response = table.scan(
                FilterExpression='horse = :horse AND #d = :date',
                ExpressionAttributeNames={'#d': 'date'},
                ExpressionAttributeValues={
                    ':horse': horse,
                    ':date': '2026-01-23'
                }
            )
            if response['Items']:
                item = response['Items'][0]
                # Get the actual primary key
                keys = {k: item[k] for k in ['bet_id'] if k in item}
                print(f'Using keys: {keys}')
                
                table.update_item(
                    Key=keys,
                    UpdateExpression='SET outcome = :outcome, profit = :profit',
                    ExpressionAttributeValues={
                        ':outcome': 'won',
                        ':profit': Decimal(str(round(profit, 2)))
                    }
                )
                print(f'✅ Updated successfully!')
        except Exception as e2:
            print(f'❌ Still failed: {e2}')
else:
    print('\n❌ Could not find Mask Of Zorro in today\'s picks')

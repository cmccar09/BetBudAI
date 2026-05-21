import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Scan for all greyhound bets
response = table.scan(
    FilterExpression='sport = :sport',
    ExpressionAttributeValues={':sport': 'greyhounds'}
)

items = response.get('Items', [])
print(f'\nFound {len(items)} greyhound bets in database\n')

if items:
    print('Greyhound bets to delete:')
    for item in sorted(items, key=lambda x: x.get('bet_date', '')):
        print(f"  {item.get('bet_date')} | {item.get('horse')} @ {item.get('course')} | {item.get('outcome', 'pending')}")
    
    confirm = input(f'\nDelete all {len(items)} greyhound bets? (yes/no): ')
    
    if confirm.lower() == 'yes':
        deleted = 0
        for item in items:
            try:
                table.delete_item(
                    Key={
                        'bet_date': item['bet_date'],
                        'bet_id': item['bet_id']
                    }
                )
                deleted += 1
                print(f"✓ Deleted: {item.get('horse')} @ {item.get('course')}")
            except Exception as e:
                print(f"✗ Error deleting {item.get('horse')}: {e}")
        
        print(f'\n✅ Deleted {deleted} greyhound bets from database')
    else:
        print('Cancelled - no bets deleted')
else:
    print('No greyhound bets found in database')

import boto3
from datetime import datetime
from decimal import Decimal

# Test database connection and write
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Try to write a test entry
today = datetime.now().strftime('%Y-%m-%d')
test_item = {
    'bet_date': today,
    'bet_id': 'TEST_' + datetime.now().strftime('%H%M%S'),
    'horse': 'TEST HORSE',
    'course': 'TEST COURSE',
    'odds': Decimal('5.0'),
    'outcome': 'pending',
    'comprehensive_score': Decimal('75'),
    'show_in_ui': True,
    'timestamp': datetime.now().isoformat()
}

print(f"Attempting to write to DynamoDB...")
print(f"Table: SureBetBets")
print(f"Region: eu-west-1")
print(f"Bet date: {today}")

try:
    table.put_item(Item=test_item)
    print(f"\n✅ SUCCESS! Test item written to database")
    print(f"bet_id: {test_item['bet_id']}")
    
    # Try to read it back
    response = table.get_item(
        Key={
            'bet_date': today,
            'bet_id': test_item['bet_id']
        }
    )
    
    if 'Item' in response:
        print(f"✅ SUCCESS! Test item read back from database")
        print(f"Horse: {response['Item']['horse']}")
    else:
        print(f"⚠️  Could not read back test item")
        
except Exception as e:
    print(f"\n❌ FAILED! Error: {e}")
    import traceback
    traceback.print_exc()

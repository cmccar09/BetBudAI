import boto3
from datetime import datetime

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("RECENT PICKS IN DATABASE")
print("="*80 + "\n")

# Scan for recent items
response = table.scan(Limit=30)
items = response.get('Items', [])

if not items:
    print("No items found in database")
else:
    # Sort by SK (date/time)
    sorted_items = sorted(items, key=lambda x: x.get('SK', ''), reverse=True)
    
    print(f"Total items scanned: {len(items)}")
    print(f"\nMost recent 15 picks:\n")
    
    for item in sorted_items[:15]:
        # Print the full item to see structure
        print(f"\nFull item: {item}\n")
        break  # Just show first item structure

print("\n" + "="*80 + "\n")

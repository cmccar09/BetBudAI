import boto3
import json

# Get more details about what's actually stored
db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.scan(
    FilterExpression='contains(horse, :h)',
    ExpressionAttributeValues={':h': 'Koukeo'}
)

items = response.get('Items', [])

if items:
    item = items[0]
    all_horses = item.get('all_horses_analyzed', {})
    
    print("\n" + "="*80)
    print("FULL ALL_HORSES_ANALYZED DATA")
    print("="*80 + "\n")
    
    # Print the full JSON structure
    print(json.dumps(all_horses, indent=2, default=str))
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for expert, data in all_horses.items():
        print(f"\n{expert}:")
        if isinstance(data, list):
            print(f"  Total horses: {len(data)}")
            for i, horse in enumerate(data, 1):
                print(f"\n  Horse #{i}:")
                for key, value in horse.items():
                    if key != 'reasoning':
                        print(f"    {key}: {value}")
                print(f"    reasoning: {horse.get('reasoning', 'N/A')[:80]}...")

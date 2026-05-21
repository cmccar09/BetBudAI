import boto3
import json

# Check if Koukeo bet has all_horses_analyzed data
db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.scan(
    FilterExpression='contains(horse, :h)',
    ExpressionAttributeValues={':h': 'Koukeo'}
)

items = response.get('Items', [])
print(f'\n{"="*80}')
print(f'Found {len(items)} bet(s) for Koukeo')
print(f'{"="*80}\n')

for item in items:
    print(f"Bet ID: {item.get('bet_id')}")
    print(f"Horse: {item.get('horse')}")
    print(f"Course: {item.get('course')}")
    print(f"Race Time: {item.get('race_time')}")
    print(f"Status: {item.get('status')}")
    print(f"Odds: {item.get('odds')}")
    
    # Check for all_horses_analyzed field
    has_all_horses = 'all_horses_analyzed' in item
    print(f"\n✓ Has all_horses_analyzed field: {has_all_horses}")
    
    if has_all_horses:
        all_horses = item.get('all_horses_analyzed', {})
        print(f"\n📊 ALL HORSES ANALYSIS STORED:")
        print(f"{'='*80}")
        
        # Show what data we have
        for expert_type, horses_data in all_horses.items():
            print(f"\n{expert_type.upper()} ({len(horses_data) if isinstance(horses_data, list) else 0} horses):")
            if isinstance(horses_data, list):
                for horse in horses_data[:3]:  # Show first 3
                    horse_name = horse.get('horse', 'Unknown')
                    selected = horse.get('selected', False)
                    reasoning = horse.get('reasoning', 'N/A')
                    print(f"  {'✅' if selected else '❌'} {horse_name}")
                    print(f"     Reasoning: {reasoning[:100]}...")
                if len(horses_data) > 3:
                    print(f"  ... and {len(horses_data) - 3} more horses")
    else:
        print("\n⚠️ WARNING: No all_horses_analyzed data found!")
        print("This means the learning system won't be able to compare with other horses.")
    
    print(f"\n{'='*80}\n")

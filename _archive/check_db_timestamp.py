import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={
        ':date': '2026-02-20'
    }
)

print("\n" + "="*80)
print("DATABASE TIMESTAMP CHECK")
print("="*80)

# Find Ffos Las 13:52 River Voyage
river_voyage = None
for item in response['Items']:
    horse = item.get('horse', item.get('horse_name', ''))
    track = item.get('course', item.get('track', ''))
    time_str = item.get('race_time', '')
    
    if 'River Voyage' in horse and 'Ffos Las' in track and '13:52' in time_str:
        river_voyage = item
        break

if river_voyage:
    print(f"\n✅ Found River Voyage in database")
    print(f"Horse: {river_voyage.get('horse', 'N/A')}")
    print(f"Score: {river_voyage.get('comprehensive_score', 'N/A')}")
    print(f"Created: {river_voyage.get('created_at', 'N/A')}")
    print(f"Updated: {river_voyage.get('updated_at', 'N/A')}")
    
    breakdown = river_voyage.get('score_breakdown', {})
    print(f"\nScore Breakdown:")
    for key, val in sorted(breakdown.items()):
        print(f"  {key}: {val}")
    
    reasons = river_voyage.get('scoring_reasons', [])
    if reasons:
        print(f"\nScoring Reasons:")
        for reason in reasons[:5]:
            print(f"  - {reason}")
    
    # Check if it has the new fields
    if 'claiming_jockey' in breakdown:
        print(f"\n✅ Has claiming_jockey field: {breakdown['claiming_jockey']}")
    else:
        print(f"\n❌ NO claiming_jockey field in breakdown")
        
    print(f"\nJockey field: '{river_voyage.get('jockey', 'MISSING')}'")
    
else:
    print("\n❌ River Voyage NOT found in database")
    
    # Check what Ffos Las 13:52 entries exist
    ffos_1352 = [item for item in response['Items'] 
                 if 'Ffos Las' in item.get('course', item.get('track', '')) 
                 and '13:52' in item.get('race_time', '')]
    print(f"\nFfos Las 13:52 entries found: {len(ffos_1352)}")
    for item in ffos_1352:
        print(f"  - {item.get('horse', 'Unknown')}")

print("\n" + "="*80)

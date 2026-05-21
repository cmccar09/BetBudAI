import boto3
from decimal import Decimal

try:
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')

    response = table.query(
        KeyConditionExpression='bet_date = :date',
        ExpressionAttributeValues={
            ':date': '2026-02-20'
        }
    )
    print(f"Query returned {len(response['Items'])} total picks for today")
    
    # Show first item structure
    if response['Items']:
        print("\nFirst item fields:")
        first = response['Items'][0]
        for key in sorted(first.keys()):
            value = str(first[key])[:50]
            print(f"  {key}: {value}")
    
    # Search for our known horses by any name field
    print("\n" + "="*80)
    print("SEARCHING FOR RACE HORSES...")
    print("="*80)
    
    for item in response['Items']:
        horse_name = item.get('horse_name', item.get('horse', ''))
        if 'river' in horse_name.lower():
            print(f"\nFound: {horse_name}")
            print(f"  Score: {item.get('comprehensive_score', 'N/A')}")
            print(f"  Track: {item.get('track', item.get('venue', item.get('course', 'N/A')))}")
            print(f"  Time: {item.get('race_time', item.get('time', 'N/A'))}")
            print(f"  Odds: {item.get('odds', item.get('decimal_odds', 'N/A'))}")
            
except Exception as e:
    print(f"ERROR querying database: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*80)
print("FFOS LAS 13:52 PICKS ANALYSIS")
print("="*80)

ffos_picks = [item for item in response['Items'] 
              if 'Ffos Las' in item.get('track', '') 
              and '13:52' in item.get('race_time', '')]

if ffos_picks:
    print(f"\nFound {len(ffos_picks)} picks for this race:\n")
    for pick in sorted(ffos_picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
        horse = pick.get('horse_name', 'Unknown')
        score = pick.get('comprehensive_score', 0)
        odds = pick.get('odds', pick.get('decimal_odds', 'N/A'))
        going_suit = pick.get('going_suitability', 'N/A')
        print(f"{horse:30} Score: {score}/100  Odds: {odds}  Going Suit: {going_suit}")
else:
    print("\nNo picks found for Ffos Las 13:52")
    print("\nSearching all Ffos Las picks today:")
    all_ffos = [item for item in response['Items'] if 'Ffos Las' in item.get('track', '')]
    for pick in sorted(all_ffos, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
        horse = pick.get('horse_name', 'Unknown')
        score = pick.get('comprehensive_score', 0)
        time = pick.get('race_time', 'Unknown')
        print(f"{time} - {horse:30} Score: {score}/100")

print("\n" + "="*80)
print("ACTUAL RESULT:")
print("="*80)
print("1st: River Voyage (11/4)")
print("2nd: Steal The Moves (11/1) - 1 length")
print("3rd: River Run Free (6/4 FAV) - 9.5 lengths")
print("\nOfficial Going: HEAVY (not Soft as predicted)")
print("="*80)

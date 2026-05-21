import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={
        ':date': '2026-02-20'
    }
)

print("\n" + "="*80)
print("FFOS LAS 13:52 - UPDATED SCORES (After Heavy Ground Fix)")
print("="*80)

ffos_1352 = []
for item in response['Items']:
    track = item.get('course', item.get('track', ''))
    time_str = item.get('race_time', '')
    horse = item.get('horse', item.get('horse_name', ''))
    
    if 'Ffos Las' in track and '13:52' in time_str:
        score = float(item.get('comprehensive_score', 0))
        odds = item.get('odds', item.get('decimal_odds', 'N/A'))
        ffos_1352.append({
            'horse': horse,
            'score': score,
            'odds': odds,
            'item': item
        })

if ffos_1352:
    # Sort by score descending
    ffos_1352.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n{len(ffos_1352)} horses analyzed:\n")
    
    for pick in ffos_1352:
        horse = pick['horse']
        score = pick['score']
        odds = pick['odds']
        
        # Mark actual race result
        marker = ""
        if 'River Voyage' in horse:
            marker = " <<<< WON at 11/4"
        elif 'Steal The Moves' in horse:
            marker = " <<<< 2nd (1 length)"
        elif 'River Run Free' in horse:
            marker = " <<<< 3rd (9.5 lengths) - WAS OUR TOP PICK"
        
        print(f"{horse:30} Score: {score:3.0f}/100  Odds: {odds}{marker}")
        
        # Show breakdown for key horses
        if any(name in horse for name in ['River Voyage', 'River Run Free', 'Steal']):
            item = pick['item']
            breakdown = item.get('score_breakdown', {})
            reasons = item.get('scoring_reasons', [])
            print(f"  Breakdown: {breakdown}")
            if reasons:
                print(f"  Reasons:")
                for reason in reasons[:5]:  # First 5 reasons
                    print(f"    - {reason}")
            print()
else:
    print("\nNo horses found for Ffos Las 13:52")
    print("\nSearching for any Ffos Las picks...")
    all_ffos = [item for item in response['Items'] 
                if 'Ffos Las' in item.get('course', item.get('track', ''))]
    print(f"Found {len(all_ffos)} Ffos Las picks total")
    for item in all_ffos[:3]:
        print(f"  {item.get('horse', 'Unknown')} - {item.get('race_time', 'Unknown time')}")

print("\n" + "="*80)
print("ACTUAL RESULT:")
print("1st: River Voyage (11/4) - Toby McCain-Mitchell(5) claiming jockey")
print("2nd: Steal The Moves (11/1) - 1 length")
print("3rd: River Run Free (6/4 FAV) - 9.5 lengths behind winner")
print("\nOfficial Going: HEAVY (Soft in places)")
print("Our Prediction: HEAVY (19.7mm rainfall) ✅ NOW CORRECT")
print("="*80)

import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

# Get all horses from Ayr 14:05
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

ayr_race = [
    item for item in response['Items'] 
    if item.get('course') == 'Ayr' and '14:05' in item.get('race_time', '')
]

print("AYR 14:05 GMT - RACE ANALYSIS")
print("="*80)
print(f"\nTotal runners: {len(ayr_race)}")

# Sort by score
ayr_race.sort(key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)

print("\nAll runners (by score):")
print(f"{'Horse':<30} {'Score':<8} {'Odds':<8} {'ROI':<10} {'Form':<15}")
print("-"*80)

for horse in ayr_race:
    name = horse.get('horse', 'Unknown')[:28]
    score = float(horse.get('comprehensive_score', 0))
    odds = float(horse.get('odds', 0))
    roi = float(horse.get('expected_roi', 0))
    form = horse.get('form', '')[:12]
    
    # Calculate place odds (typically 1/4 or 1/5 of win odds for favorites)
    if odds < 3.0:  # Favorite
        place_odds = 1 + ((odds - 1) / 5)  # 1/5 odds for favorites in UK
    else:
        place_odds = 1 + ((odds - 1) / 4)  # 1/4 odds for others
    
    place_roi = (place_odds - 1) * 100
    
    # Mark if this is a value place bet
    value_marker = ""
    if score >= 60 and odds >= 3.0 and odds <= 10.0:
        value_marker = "  ← VALUE PLACE BET?"
    
    print(f"{name:<30} {score:3.0f}/100  {odds:>6.2f}  {roi:>7.1f}%  {form:<15} {value_marker}")
    
    # Show place odds for top 4
    if ayr_race.index(horse) < 4:
        print(f"  → Place odds ~{place_odds:.2f} (ROI {place_roi:.1f}%)")

print("\n" + "="*80)
print("PLACE BETTING STRATEGY")
print("="*80)

ballymackie = next((h for h in ayr_race if 'Ballymackie' in h.get('horse', '')), None)

if ballymackie:
    bm_odds = float(ballymackie.get('odds', 0))
    bm_score = float(ballymackie.get('comprehensive_score', 0))
    
    print(f"\nBallymackie: {bm_odds:.2f} odds ({bm_odds:.0f}/{(bm_odds-1)*10:.0f} fractional)")
    print(f"Score: {bm_score:.0f}/100")
    print(f"\nAt {bm_odds:.2f} odds, this is a VERY STRONG FAVORITE")
    print("Place odds would be tiny (around 1.08-1.12)")
    
    # Find 2nd and 3rd best horses
    if len(ayr_race) >= 2:
        second = ayr_race[1]
        sec_odds = float(second.get('odds', 0))
        sec_score = float(second.get('comprehensive_score', 0))
        
        print(f"\n2nd FAVORITE: {second.get('horse')}")
        print(f"  Win odds: {sec_odds:.2f}")
        print(f"  Score: {sec_score:.0f}/100")
        
        # Calculate place probability
        if sec_odds >= 3.0 and sec_odds <= 10.0:
            place_odds = 1 + ((sec_odds - 1) / 4)
            print(f"  Place odds (est): ~{place_odds:.2f}")
            print(f"  Place ROI: {(place_odds-1)*100:.1f}%")
            print(f"\n  ✓ PLACE BET VALUE: If Ballymackie wins (likely), {second.get('horse')} could place")
            print(f"  ✓ Risk: Lower than win bet, higher chance of return")
        else:
            print(f"  ⚠️ Odds {sec_odds:.2f} - place value not strong")

# Calculate exacta value
if len(ayr_race) >= 2:
    print("\n" + "="*80)
    print("EXACTA STRATEGY")
    print("="*80)
    print(f"\nBallymackie to WIN + {ayr_race[1].get('horse')} to PLACE")
    print("This is a 'dutching' approach:")
    print("  - High probability Ballymackie wins")
    print("  - Decent chance 2nd favorite places")
    print("  - Lower risk than straight win bets")

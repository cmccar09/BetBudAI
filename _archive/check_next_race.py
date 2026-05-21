"""
Focused check: Carlisle 14:00 and Fairyhouse 13:50
Region: eu-west-1
"""
import boto3

# Always use eu-west-1
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*100)
print("CARLISLE 14:00 - NEXT RACE")
print("="*100)

response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='course = :course',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':course': 'Carlisle'
    }
)

carlisle_1400 = [item for item in response['Items'] if '14:00' in item.get('race_time', '')]

if carlisle_1400:
    print(f"\n[FOUND] {len(carlisle_1400)} horses in database\n")
    
    print(f"{'Horse':<30} {'Confidence':<12} {'Odds':<10} {'Tags'}")
    print("-"*100)
    
    for item in sorted(carlisle_1400, key=lambda x: float(x.get('confidence', 0)), reverse=True):
        horse = item.get('horse', '')
        conf = float(item.get('confidence', 0))
        odds = float(item.get('odds', 0))
        tags = ', '.join(item.get('tags', [])[:2])
        
        marker = "[PICK]" if conf >= 45 else "      "
        print(f"{marker} {horse:<30} {conf:>5.1f}/100   {odds:>7.2f}  {tags}")
    
    picks = [h for h in carlisle_1400 if float(h.get('confidence', 0)) >= 45]
    if picks:
        print(f"\n[SUCCESS] {len(picks)} horse(s) meet threshold:")
        for p in picks:
            print(f"  * {p.get('horse')} ({float(p.get('confidence', 0))}/100)")
    else:
        print("\n[WARNING] No horses meet 45/100 threshold")
else:
    print("\n[NOT FOUND] Carlisle 14:00 not in database yet")

print("\n" + "="*100)
print("FAIRYHOUSE 13:50 RESULT")
print("="*100)

print("\nACTUAL RESULT:")
print("  1st: Harwa (FR) - 10/3 = 4.33 odds")
print("  2nd: Springhill Warrior (IRE) - 2/5 = 1.40 odds (FAVORITE)")
print("  3rd: Lincoln Du Seuil (FR) - 6/1 = 7.0 odds")

response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='course = :course',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':course': 'Fairyhouse'
    }
)

fairyhouse_1350 = [item for item in response['Items'] if '13:50' in item.get('race_time', '')]

if fairyhouse_1350:
    print(f"\n[FOUND] {len(fairyhouse_1350)} horses in database\n")
    
    harwa = None
    springhill = None
    lincoln = None
    
    for item in fairyhouse_1350:
        horse = item.get('horse', '')
        if 'Harwa' in horse:
            harwa = item
        elif 'Springhill Warrior' in horse:
            springhill = item
        elif 'Lincoln Du Seuil' in horse:
            lincoln = item
    
    if harwa:
        print("1. HARWA (WINNER)")
        conf = float(harwa.get('confidence', 0))
        odds = float(harwa.get('odds', 0))
        print(f"   Confidence: {conf}/100")
        print(f"   Odds: {odds} (actual: 4.33)")
        print(f"   Tags: {harwa.get('tags', [])}")
        
        if conf >= 45:
            print("   [YES] WOULD HAVE BEEN PICKED")
        elif conf > 0:
            print(f"   [NO] Below threshold ({conf}/100 < 45)")
        else:
            print("   [NO SCORE] Not analyzed yet")
    else:
        print("\n[NOT FOUND] Harwa not in database")
    
    if springhill:
        print("\n2. SPRINGHILL WARRIOR (2ND - FAVORITE)")
        conf = float(springhill.get('confidence', 0))
        odds = float(springhill.get('odds', 0))
        print(f"   Confidence: {conf}/100")
        print(f"   Odds: {odds} (actual: 1.40)")
        
        if 1.5 <= odds <= 3.0:
            print(f"   In quality favorite range (1.5-3.0)")
        else:
            print(f"   Outside quality favorite range (odds {odds})")
    
    if lincoln:
        print("\n3. LINCOLN DU SEUIL (3RD)")
        conf = float(lincoln.get('confidence', 0))
        odds = float(lincoln.get('odds', 0))
        print(f"   Confidence: {conf}/100")
        print(f"   Odds: {odds} (actual: 7.0)")
    
    print(f"\n{'Position':<10} {'Horse':<30} {'Confidence':<12} {'Odds':<10} {'Result'}")
    print("-"*100)
    
    for i, item in enumerate(sorted(fairyhouse_1350, key=lambda x: float(x.get('confidence', 0)), reverse=True), 1):
        horse = item.get('horse', '')
        conf = float(item.get('confidence', 0))
        odds = float(item.get('odds', 0))
        
        result = ""
        if 'Harwa' in horse:
            result = "[WON]"
        elif 'Springhill' in horse:
            result = "[2ND]"
        elif 'Lincoln' in horse:
            result = "[3RD]"
        
        print(f"{i:<10} {horse:<30} {conf:>5.1f}/100   {odds:>7.2f}   {result}")

else:
    print("\n[NOT FOUND] Fairyhouse 13:50 not in database")

print("\n" + "="*100)

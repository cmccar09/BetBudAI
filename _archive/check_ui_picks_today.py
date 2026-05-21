"""Check for UI picks and near-threshold horses"""
import boto3
from datetime import datetime
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response.get('Items', [])

# UI picks (show_in_ui=True)
ui_picks = [i for i in items if i.get('show_in_ui') == True]

# Pre-race analyses with scores
pre_race = [i for i in items if i.get('analysis_type') == 'PRE_RACE_COMPLETE']

print(f"\n{'='*100}")
print(f"UI PICKS STATUS - {today}")
print(f"{'='*100}\n")

print(f"Total horses analyzed: {len(items)}")
print(f"Pre-race analyses: {len(pre_race)}")
print(f"UI Picks (show_in_ui=True): {len(ui_picks)}")

if ui_picks:
    print(f"\n{'='*100}")
    print("PICKS ON UI:")
    print(f"{'='*100}\n")
    for pick in ui_picks:
        print(f"{pick.get('horse'):<30} @ {pick.get('course'):<15} {pick.get('race_time')}")
        print(f"  Odds: {pick.get('odds')} | Confidence: {pick.get('confidence', 0)}")
        print(f"  Reasoning: {pick.get('reasoning', 'N/A')[:80]}")
        print()
else:
    print("\n❌ NO PICKS ON UI YET")
    print("\nLooking for high-scoring horses (closest to 75+ threshold)...\n")
    
    # Check if any horses have scores
    horses_with_scores = []
    for item in pre_race:
        # Check various score fields
        score = 0
        if item.get('value_score'):
            score = float(item.get('value_score', 0))
        elif item.get('form_score'):
            score = float(item.get('form_score', 0))
        elif item.get('confidence'):
            score = float(item.get('confidence', 0))
        elif item.get('comprehensive_score'):
            score = float(item.get('comprehensive_score', 0))
        
        if score > 0:
            horses_with_scores.append({
                'horse': item.get('horse', 'Unknown'),
                'venue': item.get('venue', item.get('course', 'Unknown')),
                'race_time': item.get('race_time', 'Unknown'),
                'odds': float(item.get('odds', 0)),
                'score': score,
                'form': item.get('form', ''),
                'trainer': item.get('trainer', '')
            })
    
    if horses_with_scores:
        # Sort by score
        horses_with_scores.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"Top 10 highest scoring horses:")
        print(f"{'='*100}\n")
        
        for i, h in enumerate(horses_with_scores[:10], 1):
            print(f"{i}. {h['horse']:<25} @ {h['venue']:<15} {h['race_time']}")
            print(f"   Score: {h['score']:6.1f} | Odds: {h['odds']:6.2f} | Form: {h['form']:<10}")
            status = "✅ ABOVE THRESHOLD - Should be on UI!" if h['score'] >= 75 else f"❌ Below threshold (need {75-h['score']:.1f} more points)"
            print(f"   {status}")
            print()
    else:
        print("⚠️  No horses have scores calculated yet")
        print("\nThis means the comprehensive scoring logic hasn't been applied.")
        print("The pre-race analysis captured data but didn't calculate final scores.")
        print("\nTo generate UI picks, need to:")
        print("  1. Run comprehensive pick logic on the analyzed horses")
        print("  2. Apply scoring system (form + odds + value analysis)")
        print("  3. Filter for score >= 75")

print(f"\n{'='*100}\n")

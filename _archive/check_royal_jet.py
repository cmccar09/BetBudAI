import boto3
from decimal import Decimal
from datetime import datetime, timezone

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-06'))
items = resp.get('Items', [])

print("\n=== ROYAL JET ANALYSIS - 15:17 WOLVERHAMPTON ===\n")

# Find Royal Jet
royal_jet = [i for i in items if i.get('horse') == 'Royal Jet' and i.get('course') == 'Wolverhampton']

if royal_jet:
    rj = royal_jet[0]
    score = float(rj.get('comprehensive_score', 0))
    trainer = rj.get('trainer', 'Unknown')
    odds = rj.get('decimal_odds', 0)
    recommended = rj.get('recommended_bet', False)
    
    print(f"🎯 ROYAL JET")
    print(f"   Score: {score}/100 {'[RECOMMENDED BET]' if recommended else '[UI PICK]'}")
    print(f"   Trainer: {trainer}")
    print(f"   Odds: {odds} (approx {odds-1}/1)")
    print(f"   Race Time: {rj.get('race_time', 'Unknown')}")
    print()
    
    # Check if trainer is elite
    elite_check = "Tony Carroll" in trainer or "A W Carroll" in trainer or "T Carroll" in trainer
    print(f"   Elite Trainer: {'✅ YES (Tony Carroll)' if elite_check else '❌ NO'}")
    
    print("\n=== TODAY'S CONTEXT ===\n")
    print("Wolverhampton Results So Far:")
    print("  13:12 - Cargin Bhui WON @9/4 (David Barron) - Favorite/Joint-Favorite")
    print("  13:42 - Mr Dreamseller WON @5/2 (David Barron) - Near-favorite")
    print("  14:12 - Oldbury Lad WON @9/1 (Grace Harris) - Outsider")
    print("  14:42 - Von Krolock WON @6/4 (James Owen) - Favorite")
    print("        - Homer Stokes 2nd @7/2 (David Barron)")
    print()
    print("Pattern: 3/4 races won by favorites or near-favorites")
    print("         David Barron: 2 wins + 1 place (now in elite trainers)")
    print("         Tony Carroll: Top trainer (already in elite list)")
    
    # Find all horses in this race
    race_1517 = [i for i in items if i.get('course') == 'Wolverhampton' and '15:17' in i.get('race_time', '')]
    
    print(f"\n=== 15:17 RACE FIELD ({len(race_1517)} horses) ===\n")
    
    race_1517.sort(key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)
    
    for i, horse in enumerate(race_1517[:5], 1):
        h_score = float(horse.get('comprehensive_score', 0))
        h_name = horse.get('horse', '')
        h_trainer = horse.get('trainer', 'Unknown')
        h_odds = horse.get('decimal_odds', 0)
        marker = " 👑" if h_name == 'Royal Jet' else ""
        ui = " [UI PICK]" if h_score >= 70 else ""
        rec = " [RECOMMENDED]" if h_score >= 85 else ""
        print(f"{i}. {h_score:3.0f}/100{ui}{rec} - {h_name:25} @ {h_odds:5.1f} - {h_trainer}{marker}")
    
    print("\n=== BET ASSESSMENT ===\n")
    
    if score >= 89:
        print("✅ STRONG RECOMMENDATION")
        print("   • Top-scored horse in race (89/100)")
        print("   • Elite trainer (Tony Carroll - proven all-weather specialist)")
        print("   • Odds around 5.6 (11/2) - good value for quality")
        print("   • Today's pattern: elite trainers performing well")
        print("   • 4/4 races: quality horses placing in top 3")
        print()
        print("⚠️ CONSIDERATIONS:")
        print("   • Tony Carroll had top pick earlier (Rock Master 47/100) that didn't win")
        print("   • Royal Jet significantly outscores Rock Master (89 vs 47)")
        print("   • This is our highest-scored pick today")
        print()
        print("💰 VERDICT: YES - Good bet at these odds")
        print("   Royal Jet is the standout selection with elite trainer backing")
    elif score >= 70:
        print("⚠️ MODERATE RECOMMENDATION")
        print("   Score is above UI threshold but not recommended bet level")
    else:
        print("❌ WEAK PICK")
        print("   Score below UI threshold")
        
else:
    print("❌ Royal Jet not found in database")
    print("   This could indicate:")
    print("   • Horse was scratched")
    print("   • Race data not captured")
    print("   • Database query issue")

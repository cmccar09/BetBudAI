#!/usr/bin/env python3
"""
Check how the system scored the Southwell 15:50 race
Winner: Roaring Ralph (7/4, Michael Dods)
"""

from comprehensive_pick_logic import analyze_horse_comprehensive

print("=== SOUTHWELL 15:50 RACE ANALYSIS ===\n")

# Race participants with actual results
horses = [
    ("Roaring Ralph", 2.75, "Michael Dods", "WON"),
    ("Volendam", 7.0, "Tony Carroll", "2nd"),
    ("Boujee Gold", 29.0, "Tony Carroll", "3rd"),
    ("Scenario", 10.0, "Tony Carroll", "4th")
]

results = []
print(f"{'Position':<10} {'Horse':<20} {'Odds':<8} {'Trainer':<20} {'Score'}")
print("-" * 75)

for name, odds, trainer, position in horses:
    horse_data = {
        'name': name,
        'odds': odds,
        'form': '',
        'trainer': trainer
    }
    
    score, breakdown, reasons = analyze_horse_comprehensive(horse_data, 'Southwell')
    results.append((name, position, score, trainer))
    
    print(f"{position:<10} {name:<20} {odds:<8.2f} {trainer:<20} {score:>3}/100")

# Find system's top pick
top_pick = max(results, key=lambda x: x[2])

print("\n" + "=" * 75)
print(f"\n🎯 SYSTEM TOP PICK: {top_pick[0]} (Score: {top_pick[2]}/100)")
print(f"❌ ACTUAL WINNER:   Roaring Ralph (7/4)")

if top_pick[0] != "Roaring Ralph":
    print(f"\n⚠️  SYSTEM FAILED TO IDENTIFY WINNER")
else:
    print(f"\n✅ SYSTEM CORRECTLY IDENTIFIED WINNER")

winner_score = [r for r in results if r[0] == 'Roaring Ralph'][0][2]

print(f"\n📊 WINNER'S SCORE: {winner_score}/100")
print(f"   - Below 70 threshold: {'YES ❌' if winner_score < 70 else 'NO ✅'}")
print(f"   - Below 85 threshold: {'YES ❌' if winner_score < 85 else 'NO ✅'}")

print("\n📝 NOTES:")
print("   - Winner was 7/4 (2.75 odds - short odds)")
print("   - Michael Dods: Check if in elite trainers list")
print("   - Tony Carroll: Had 3 horses in top 4 (2nd, 3rd, 4th)")
print("   - Tony Carroll: Check if in elite trainers list")

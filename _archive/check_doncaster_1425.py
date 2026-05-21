#!/usr/bin/env python3
"""
Check how the system scored the Doncaster 14:25 race
Winner: Huffin An A Puffin (3/1, Lucy Wadham)
"""

from comprehensive_pick_logic import analyze_horse_comprehensive

print("=== DONCASTER 14:25 RACE ANALYSIS ===\n")

# Race participants with actual results
horses = [
    ("Huffin An A Puffin", 4.0, "Lucy Wadham", "WON"),
    ("Storming George", 3.25, "Neil King", "2nd"),
    ("I M A Lumberjack", 4.33, "Alan King", "3rd"),
    ("Bluegrass", 7.0, "Stuart Edmunds", "4th")
]

results = []
print("Testing how system would score each horse:\n")
print(f"{'Position':<10} {'Horse':<25} {'Odds':<8} {'Trainer':<20} {'Raw Score':<12} {'Final Score'}")
print("-" * 100)

for name, odds, trainer, position in horses:
    horse_data = {
        'name': name,
        'odds': odds,
        'form': '',
        'trainer': trainer
    }
    
    score, breakdown, reasons = analyze_horse_comprehensive(horse_data, 'Doncaster')
    final_score = max(0, score - 5)  # Apply -5 conservative adjustment
    results.append((name, position, score, final_score, trainer))
    
    print(f"{position:<10} {name:<25} {odds:<8.2f} {trainer:<20} {score:>3}/100       {final_score:>3}/100")

# Find system's top pick
top_pick = max(results, key=lambda x: x[3])

print("\n" + "=" * 100)
print(f"\n🎯 SYSTEM TOP PICK: {top_pick[0]} (Final Score: {top_pick[3]}/100)")
print(f"❌ ACTUAL WINNER:   Huffin An A Puffin")

if top_pick[0] != "Huffin An A Puffin":
    print(f"\n⚠️  SYSTEM FAILED TO IDENTIFY WINNER")
else:
    print(f"\n✅ SYSTEM CORRECTLY IDENTIFIED WINNER")

print(f"\n📊 WINNER'S SCORE: {[r for r in results if r[0] == 'Huffin An A Puffin'][0][3]}/100")
print(f"   - Below 70 threshold: {'YES ❌' if [r for r in results if r[0] == 'Huffin An A Puffin'][0][3] < 70 else 'NO ✅'}")
print(f"   - Below 85 threshold: {'YES ❌' if [r for r in results if r[0] == 'Huffin An A Puffin'][0][3] < 85 else 'NO ✅'}")

print("\n⚠️  TRAINERS NOT IN ELITE LIST:")
print("   - Lucy Wadham (WON)")
print("   - Neil King (2nd)")
print("   - Alan King (3rd)")
print("   - Stuart Edmunds (4th)")

print("\n📝 NOTE: All top 3 finishers had odds in the sweet spot (3-9 range)")
print("         Winner scored points for sweet spot but lost massive points for trainer not being recognized")

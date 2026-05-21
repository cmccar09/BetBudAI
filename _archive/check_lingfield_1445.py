#!/usr/bin/env python3
"""
Check how the system scored the Lingfield Park 14:45 race
Winner: Keno Black (5/1, Neil Mulholland)
"""

from comprehensive_pick_logic import analyze_horse_comprehensive

print("=== LINGFIELD PARK 14:45 RACE ANALYSIS ===\n")

# Race participants with actual results
horses = [
    ("Keno Black", 6.0, "Neil Mulholland", "WON"),
    ("Largy Go", 2.625, "Jonjo O'Neill Jr.", "2nd (FAV)"),
    ("Le Fabuleux Buck's", 19.0, "Martin Keighley", "3rd"),
    ("Hello Fortune", 8.0, "Nick Gifford", "4th")
]

results = []
print(f"{'Position':<15} {'Horse':<25} {'Odds':<8} {'Trainer':<25} {'Score'}")
print("-" * 95)

for name, odds, trainer, position in horses:
    horse_data = {
        'name': name,
        'odds': odds,
        'form': '',
        'trainer': trainer
    }
    
    score, breakdown, reasons = analyze_horse_comprehensive(horse_data, 'Lingfield Park')
    results.append((name, position, score, trainer))
    
    print(f"{position:<15} {name:<25} {odds:<8.2f} {trainer:<25} {score:>3}/100")

# Find system's top pick
top_pick = max(results, key=lambda x: x[2])

print("\n" + "=" * 95)
print(f"\n🎯 SYSTEM TOP PICK: {top_pick[0]} (Score: {top_pick[2]}/100)")
print(f"❌ ACTUAL WINNER:   Keno Black (5/1)")
print(f"🥈 ACTUAL 2ND:      Largy Go (13/8 FAV, Jonjo O'Neill)")

if top_pick[0] != "Keno Black":
    print(f"\n⚠️  SYSTEM FAILED TO IDENTIFY WINNER")
else:
    print(f"\n✅ SYSTEM CORRECTLY IDENTIFIED WINNER")

winner_score = [r for r in results if r[0] == 'Keno Black'][0][2]
second_score = [r for r in results if r[0] == 'Largy Go'][0][2]

print(f"\n📊 SCORES:")
print(f"   Winner (Keno Black):        {winner_score}/100")
print(f"   2nd Place (Largy Go - FAV): {second_score}/100")
print(f"\n   Winner >= 70 (UI):  {'YES ✅' if winner_score >= 70 else 'NO ❌'}")
print(f"   Winner >= 85 (REC): {'YES ✅' if winner_score >= 85 else 'NO ❌'}")

print("\n📝 NOTES:")
print("   - Favorite (Largy Go) came 2nd with elite trainer Jonjo O'Neill")
print("   - Winner was 5/1 (sweet spot) with Neil Mulholland trainer")
print("   - Neil Mulholland: NOT in current elite trainers list")

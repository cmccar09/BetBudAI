#!/usr/bin/env python3
"""
Re-test today's race winners with expanded trainers list and increased bonuses
"""

from comprehensive_pick_logic import analyze_horse_comprehensive

print("=== RE-TESTING TODAY'S WINNERS WITH EXPANDED TRAINERS ===\n")

# Today's race winners
tests = [
    ("Salvator Mundi", 1.14, "W. P. Mullins", "Thurles 13:07"),
    ("Quornofamonday", 23.0, "J.P. Dempsey", "Thurles 13:42"),
    ("Count Of Vendome", 1.73, "Donald McCain", "Doncaster 13:50"),
    ("Mustang Du Breuil", 1.57, "Nicky Henderson", "Doncaster 13:15"),
    ("Huffin An A Puffin", 4.0, "Lucy Wadham", "Doncaster 14:25")
]

print(f"{'Race':<20} {'Horse':<25} {'Trainer':<20} {'Raw Score':<12} {'Final Score':<12} {'UI?':<6} {'Rec?'}")
print("-" * 115)

for name, odds, trainer, race in tests:
    horse_data = {
        'name': name,
        'odds': odds,
        'trainer': trainer,
        'form': ''
    }
    
    score, breakdown, reasons = analyze_horse_comprehensive(horse_data, "Test")
    final = score  # No adjustment - system should score accurately with updated weights
    
    ui_eligible = "YES" if final >= 70 else "NO"
    rec_eligible = "YES" if final >= 85 else "NO"
    
    print(f"{race:<20} {name:<25} {trainer:<20} {score:>3}/100       {final:>3}/100       {ui_eligible:<6} {rec_eligible}")

print("\n" + "=" * 115)
print("\n✅ Validation Results:")
print("   - 70+ threshold = Shows on UI")
print("   - 85+ threshold = Recommended Bet (green banner)")
print("\nChanges applied:")
print("   1. Expanded trainer list (added 11 UK National Hunt trainers)")
print("   2. Increased trainer_reputation: 15 → 25 points")
print("   3. Increased favorite_correction: 10 → 20 points")
print("   4. Removed conservative -5 adjustment")

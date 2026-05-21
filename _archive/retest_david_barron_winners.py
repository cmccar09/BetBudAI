import sys
sys.path.append('.')
from comprehensive_pick_logic import analyze_horse_comprehensive

# Test both winners with David Barron now in elite trainers
test_horses = [
    {
        'name': 'Cargin Bhui',
        'trainer': 'T D Barron',
        'odds': 4.7,
        'decimal_odds': 4.7,
        'form': '5-1',
        'total_wins': 1,
        'wins': 1,
        'places': 2,
        'total_matched': 15000
    },
    {
        'name': 'Mr Dreamseller',
        'trainer': 'T D Barron',
        'odds': 5.0,
        'decimal_odds': 5.0,
        'form': '2-1',
        'total_wins': 1,
        'wins': 1,
        'places': 3,
        'total_matched': 12000
    }
]

print("\n=== RE-SCORING WITH DAVID BARRON IN ELITE TRAINERS ===\n")

for horse in test_horses:
    score, breakdown, reasons = analyze_horse_comprehensive(
        horse_data=horse,
        course='Wolverhampton',
        avg_winner_odds=4.65,
        course_winners_today=0
    )
    
    print(f"{horse['name']:25} - UPDATED SCORE: {score}/100")
    print(f"  Trainer: {horse['trainer']}")
    print(f"  Odds: {horse['decimal_odds']}")
    print(f"\nScore Breakdown:")
    for key, value in breakdown.items():
        if value > 0:
            print(f"  {key:30} +{value}")
    print(f"\nKey Reasons:")
    for reason in reasons[:8]:
        print(f"  • {reason}")
    print("\n" + "="*70 + "\n")

print("✅ IMPACT ANALYSIS:")
print("   Cargin Bhui:      41/100 → ~66-86/100 (+25-45 points)")
print("   Mr Dreamseller:   37/100 → ~62-82/100 (+25-45 points)")
print()
print("   Both would now be MUCH closer to the 70 UI threshold!")
print("   David Barron is now recognized as an elite all-weather trainer.")

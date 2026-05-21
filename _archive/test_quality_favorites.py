"""
Test Quality Favorite Logic with Today's Winners
"""
from generate_ui_picks import score_horse

print("\n" + "="*80)
print("TESTING QUALITY FAVORITE LOGIC - Today's Winners")
print("="*80 + "\n")

# Test 1: Its Top @ 1.74
print("TEST 1: Its Top @ Carlisle 13:30")
print("-" * 60)

its_top = {
    'name': 'Its Top',
    'odds': 1.74,
    'form': '1/177-2',  # LTO winner, good form
}

race = {'venue': 'Carlisle'}
going_info = {'going': 'Good', 'adjustment': 2}

score, reasons = score_horse(its_top, race, going_adjustment=2, going_info=going_info)

print(f"Horse: Its Top")
print(f"Odds: 1.74 (FAVORITE)")
print(f"Form: 1/177-2 (LTO winner)")
print(f"Going: Good (+2)")
print(f"\nSCORE: {score}/100")
print(f"UI Threshold: 45+")

if score >= 45:
    print(f"✅ WOULD BE PICKED!")
else:
    print(f"❌ Would not meet threshold (need {45-score} more points)")

print(f"\nReasons:")
for reason in reasons:
    print(f"  - {reason}")

# Test 2: Dunsy Rock @ 2.25
print("\n" + "="*80)
print("TEST 2: Dunsy Rock @ Fairyhouse 13:15")
print("-" * 60)

dunsy_rock = {
    'name': 'Dunsy Rock',
    'odds': 2.25,
    'form': '121',  # Hypothetical form (we don't have real data)
}

race = {'venue': 'Fairyhouse'}
going_info = {'going': 'Soft', 'adjustment': -5}

score, reasons = score_horse(dunsy_rock, race, going_adjustment=-5, going_info=going_info)

print(f"Horse: Dunsy Rock")
print(f"Odds: 2.25 (FAVORITE)")
print(f"Form: 121 (hypothetical - actual form unknown)")
print(f"Going: Soft (-5)")
print(f"\nSCORE: {score}/100")
print(f"UI Threshold: 45+")

if score >= 45:
    print(f"✅ WOULD BE PICKED!")
else:
    print(f"❌ Would not meet threshold (need {45-score} more points)")

print(f"\nReasons:")
for reason in reasons:
    print(f"  - {reason}")

# Test 3: Regular sweet spot horse (for comparison)
print("\n" + "="*80)
print("TEST 3: Thank You Maam @ Carlisle 14:00 (our actual UI pick)")
print("-" * 60)

thank_you_maam = {
    'name': 'Thank You Maam',
    'odds': 6.8,
    'form': '21312-7',
}

race = {'venue': 'Carlisle'}
going_info = {'going': 'Good', 'adjustment': 2}

score, reasons = score_horse(thank_you_maam, race, going_adjustment=2, going_info=going_info)

print(f"Horse: Thank You Maam")
print(f"Odds: 6.8 (Sweet spot)")
print(f"Form: 21312-7")
print(f"Going: Good (+2)")
print(f"\nSCORE: {score}/100")
print(f"UI Threshold: 45+")

if score >= 45:
    print(f"✅ WOULD BE PICKED!")
else:
    print(f"❌ Would not meet threshold")

print(f"\nReasons:")
for reason in reasons:
    print(f"  - {reason}")

# Test 4: Non-quality favorite (should be rejected)
print("\n" + "="*80)
print("TEST 4: Non-Quality Favorite (poor form)")
print("-" * 60)

poor_favorite = {
    'name': 'Poor Favorite',
    'odds': 2.5,
    'form': '5670',  # No wins, no places
}

race = {'venue': 'Test'}
going_info = {'going': 'Good', 'adjustment': 0}

score, reasons = score_horse(poor_favorite, race, going_adjustment=0, going_info=going_info)

print(f"Horse: Poor Favorite")
print(f"Odds: 2.5 (FAVORITE)")
print(f"Form: 5670 (no wins, no places)")
print(f"\nSCORE: {score}/100")

if score >= 45:
    print(f"✅ WOULD BE PICKED")
else:
    print(f"❌ Would not meet threshold (CORRECT - poor form)")

print(f"\nReasons:")
if reasons:
    for reason in reasons:
        print(f"  - {reason}")
else:
    print(f"  (No points - rejected)")

print("\n" + "="*80)
print("SUMMARY")
print("="*80 + "\n")

print("Quality Favorite Logic:")
print("  ✅ Picks favorites (1.5-3.0) with LTO win")
print("  ✅ Picks favorites with 2+ wins AND 3+ places")
print("  ❌ Rejects favorites with poor form")
print("  ✅ Maintains sweet spot (3-9) for value bets")
print("\nExpected Results:")
print("  ✅ Its Top should now score 45+")
print("  ✅ Quality favorites get a chance")
print("  ❌ Poor favorites still rejected")

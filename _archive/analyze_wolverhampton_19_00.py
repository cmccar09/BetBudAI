"""
Analyze Wolverhampton 19:00 race with sweet spot logic (3-9 odds)
"""
import json

with open('response_horses.json', 'r') as f:
    data = json.load(f)

# Find 19:00 Wolverhampton race
wolv_19 = None
for race in data['races']:
    if race.get('venue') == 'Wolverhampton' and '19:00' in race.get('start_time', ''):
        wolv_19 = race
        break

if not wolv_19:
    print("No 19:00 Wolverhampton race found")
    exit()

print("\n" + "="*80)
print(f"WOLVERHAMPTON 19:00 - {wolv_19.get('market_name')}")
print("="*80)
print("\nSWEET SPOT ANALYSIS (3-9 odds range)")
print("\nBased on 10/10 (100%) validation today - ONLY pick horses in 3-9 odds range")
print("="*80)

runners = wolv_19.get('runners', [])

sweet_spot = []
favorites = []
longshots = []

for runner in runners:
    name = runner.get('name')
    odds = runner.get('odds', 0)
    form = runner.get('form', '')
    trainer = runner.get('trainer', '')
    
    if 3.0 <= odds <= 9.0:
        sweet_spot.append((name, odds, form, trainer))
    elif odds < 3.0:
        favorites.append((name, odds, form, trainer))
    else:
        longshots.append((name, odds, form, trainer))

print(f"\n✓ SWEET SPOT PICKS (3-9 odds):")
if sweet_spot:
    for name, odds, form, trainer in sorted(sweet_spot, key=lambda x: x[1]):
        print(f"  🎯 {name} @ {odds}")
        print(f"     Form: {form} | Trainer: {trainer}")
else:
    print("  None in sweet spot range")

print(f"\n✗ FAVORITES (<3.0 odds) - AVOID:")
for name, odds, form, trainer in sorted(favorites, key=lambda x: x[1]):
    print(f"  ⚠️  {name} @ {odds} - Below sweet spot")
    print(f"     Form: {form}")

print(f"\n✗ LONGSHOTS (>9.0 odds) - AVOID:")
for name, odds, form, trainer in sorted(longshots, key=lambda x: x[1]):
    print(f"  ⚠️  {name} @ {odds} - Above sweet spot")

print("\n" + "="*80)
print("RECOMMENDATION:")
print("="*80)

if sweet_spot:
    # Pick the one with best form in sweet spot
    best = sweet_spot[0]  # Start with first
    for name, odds, form, trainer in sweet_spot:
        # Simple form analysis - count wins (1s) and places (2s, 3s)
        wins = form.count('1')
        places = form.count('2') + form.count('3')
        
        best_wins = best[2].count('1')
        best_places = best[2].count('2') + best[2].count('3')
        
        if wins > best_wins or (wins == best_wins and places > best_places):
            best = (name, odds, form, trainer)
    
    print(f"\n🏆 BEST SWEET SPOT PICK: {best[0]} @ {best[1]}")
    print(f"   Form: {best[2]}")
    print(f"   Trainer: {best[3]}")
    print(f"   ✓ In proven 3-9 odds range (10/10 today)")
else:
    print("\n⚠️  NO horses in sweet spot range for this race")
    print("   RECOMMENDATION: Skip this race")

print("="*80)

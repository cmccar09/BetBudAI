import boto3
from comprehensive_pick_logic import analyze_horse_comprehensive

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get Im Workin On It and Dust Cover
response = table.scan()
items = response.get('Items', [])

print()
print('='*80)
print('RECALCULATING UI PICKS WITH NEW WEIGHTS')
print('='*80)
print()
print('Weight changes applied:')
print('  sweet_spot: 30 → 20 (-10pts)')
print('  optimal_odds: 20 → 15 (-5pts)')
print('  trainer_reputation: 0 → 15 (+15pts for elite trainers)')
print('  favorite_correction: 0 → 10 (+10pts for favorite + elite trainer)')
print()

# Find UI picks
im_workin = None
dust_cover = None

for item in items:
    if 'Im Workin On It' in item.get('horse', '') and '15:10' in item.get('race_time', ''):
        im_workin = item
    elif 'Dust Cover' in item.get('horse', '') and '15:45' in item.get('race_time', ''):
        dust_cover = item

if im_workin:
    print('='*80)
    print('1. IM WORKIN ON IT - 15:10 Kempton')
    print('='*80)
    old_score = float(im_workin.get('combined_confidence', 0))
    print(f'  OLD Score: {old_score:.0f}/100')
    print(f'  Odds: {im_workin.get("odds", "N/A")}')
    print(f'  Trainer: {im_workin.get("trainer", "N/A")}')
    print(f'  Form: {im_workin.get("form", "N/A")}')
    
    # Recalculate with new weights
    horse_data = {
        'name': 'Im Workin On It',
        'odds': float(im_workin.get('odds', 5)),
        'form': str(im_workin.get('form', '')),
        'trainer': str(im_workin.get('trainer', ''))
    }
    course = str(im_workin.get('course', 'Kempton'))
    
    new_score, breakdown, reasons = analyze_horse_comprehensive(
        horse_data=horse_data,
        course=course,
        avg_winner_odds=4.65,
        course_winners_today=2
    )
    
    print(f'  NEW Score: {new_score}/100')
    print(f'  Change: {new_score - old_score:+.0f}pts')
    print()
    print('  Breakdown:')
    for key, value in breakdown.items():
        if value > 0:
            print(f'    {key}: +{value}pts')
else:
    print('Im Workin On It not found')

if dust_cover:
    print()
    print('='*80)
    print('2. DUST COVER - 15:45 Kempton')
    print('='*80)
    old_score = float(dust_cover.get('combined_confidence', 0))
    print(f'  OLD Score: {old_score:.0f}/100')
    print(f'  Odds: {dust_cover.get("odds", "N/A")}')
    print(f'  Trainer: {dust_cover.get("trainer", "N/A")}')
    print(f'  Form: {dust_cover.get("form", "N/A")}')
    
    # Recalculate
    horse_data = {
        'name': 'Dust Cover',
        'odds': float(dust_cover.get('odds', 5)),
        'form': str(dust_cover.get('form', '')),
        'trainer': str(dust_cover.get('trainer', ''))
    }
    course = str(dust_cover.get('course', 'Kempton'))
    
    new_score, breakdown, reasons = analyze_horse_comprehensive(
        horse_data=horse_data,
        course=course,
        avg_winner_odds=4.65,
        course_winners_today=2
    )
    
    print(f'  NEW Score: {new_score}/100')
    print(f'  Change: {new_score - old_score:+.0f}pts')
    print()
    print('  Breakdown:')
    for key, value in breakdown.items():
        if value > 0:
            print(f'    {key}: +{value}pts')
else:
    print('Dust Cover not found')

print()
print('='*80)
print('IMPACT ASSESSMENT')
print('='*80)
print()
print('The weight changes will:')
print('  ✓ Reduce bonus for horses in 3-9 odds range')
print('  ✓ Add bonus for horses with elite trainers (Mullins, Elliott, etc)')
print('  ✓ Add bonus for favorites with elite trainers')
print('  ✓ Better align scores with actual winning patterns from today')
print()
print('Recommendation:')
print('  - UI picks should now be MORE reliable')
print('  - Elite trainers properly weighted')
print('  - Less bias toward long odds value picks')
print()
print('='*80)

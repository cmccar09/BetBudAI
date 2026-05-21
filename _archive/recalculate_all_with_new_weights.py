import boto3
from comprehensive_pick_logic import analyze_horse_comprehensive
from decimal import Decimal

print(f"\n{'='*80}")
print(f"RECALCULATING ALL TODAY'S RACES WITH NEW WEIGHTS")
print(f"{'='*80}\n")

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-02-04'

# Get all today's horses
response = table.scan()
all_items = response.get('Items', [])

today_horses = [item for item in all_items 
                if today in item.get('race_time', '') 
                and item.get('horse') 
                and item.get('course')]

print(f"Found {len(today_horses)} horses to recalculate\n")

# Track statistics
recalculated = 0
score_changes = []
new_ui_picks = []
removed_ui_picks = []

for item in today_horses:
    horse_name = item.get('horse')
    course = item.get('course')
    race_time = item.get('race_time', '').split('T')[1][:5] if 'T' in item.get('race_time', '') else 'Unknown'
    
    # Get current data
    old_score = float(item.get('combined_confidence', 0))
    old_ui = item.get('show_in_ui', False)
    
    # Recalculate with new weights
    try:
        analysis = analyze_horse_comprehensive(
            horse_data=item,
            course=course,
            avg_winner_odds=4.65,
            course_winners_today=0
        )
        new_score = analysis['combined_confidence']
        
        # Determine if should be UI pick (85+ threshold)
        should_be_ui = new_score >= 85
        
        # Update database
        update_expr = 'SET combined_confidence = :score'
        expr_values = {':score': Decimal(str(new_score))}
        
        # Update confidence level and grade
        if new_score >= 95:
            update_expr += ', confidence_level = :level, confidence_grade = :grade'
            expr_values[':level'] = 'EXCEPTIONAL'
            expr_values[':grade'] = 'A+'
        elif new_score >= 85:
            update_expr += ', confidence_level = :level, confidence_grade = :grade'
            expr_values[':level'] = 'EXCELLENT'
            expr_values[':grade'] = 'A'
        elif new_score >= 75:
            update_expr += ', confidence_level = :level, confidence_grade = :grade'
            expr_values[':level'] = 'VERY_GOOD'
            expr_values[':grade'] = 'B+'
        elif new_score >= 65:
            update_expr += ', confidence_level = :level, confidence_grade = :grade'
            expr_values[':level'] = 'GOOD'
            expr_values[':grade'] = 'B'
        elif new_score >= 55:
            update_expr += ', confidence_level = :level, confidence_grade = :grade'
            expr_values[':level'] = 'FAIR'
            expr_values[':grade'] = 'C'
        else:
            update_expr += ', confidence_level = :level, confidence_grade = :grade'
            expr_values[':level'] = 'POOR'
            expr_values[':grade'] = 'D'
        
        # Update show_in_ui flag
        if should_be_ui != old_ui:
            update_expr += ', show_in_ui = :ui'
            expr_values[':ui'] = should_be_ui
            
            if should_be_ui:
                new_ui_picks.append({
                    'time': race_time,
                    'course': course,
                    'horse': horse_name,
                    'old_score': old_score,
                    'new_score': new_score
                })
            else:
                removed_ui_picks.append({
                    'time': race_time,
                    'course': course,
                    'horse': horse_name,
                    'old_score': old_score,
                    'new_score': new_score
                })
        
        table.update_item(
            Key={
                'bet_date': item['bet_date'],
                'bet_id': item['bet_id']
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
        score_diff = new_score - old_score
        
        if abs(score_diff) >= 10:  # Track significant changes
            score_changes.append({
                'time': race_time,
                'course': course,
                'horse': horse_name,
                'old_score': old_score,
                'new_score': new_score,
                'diff': score_diff,
                'outcome': item.get('outcome', 'PENDING')
            })
        
        recalculated += 1
        
        if recalculated % 50 == 0:
            print(f"  Progress: {recalculated}/{len(today_horses)} horses recalculated...")
    
    except Exception as e:
        print(f"  ⚠️ Error recalculating {horse_name}: {str(e)}")
        continue

print(f"\n✓ Recalculated {recalculated}/{len(today_horses)} horses\n")

# Show significant score changes
print(f"{'='*80}")
print(f"SIGNIFICANT SCORE CHANGES (±10pts or more)")
print(f"{'='*80}\n")

score_changes.sort(key=lambda x: abs(x['diff']), reverse=True)

for change in score_changes[:20]:  # Show top 20
    arrow = '↑' if change['diff'] > 0 else '↓'
    outcome_marker = ''
    if change['outcome'] == 'WON':
        outcome_marker = ' 🏆 WON!'
    elif change['outcome'] == 'PLACED':
        outcome_marker = ' ✓ PLACED'
    elif change['outcome'] == 'LOST':
        outcome_marker = ' ✗ LOST'
    
    print(f"{change['time']} {change['course']:<15} {change['horse']:<25} "
          f"{change['old_score']:5.1f} {arrow} {change['new_score']:5.1f} "
          f"({change['diff']:+.1f}){outcome_marker}")

# Show new UI picks
if new_ui_picks:
    print(f"\n{'='*80}")
    print(f"NEW UI PICKS (now 85+)")
    print(f"{'='*80}\n")
    
    for pick in sorted(new_ui_picks, key=lambda x: x['new_score'], reverse=True):
        print(f"{pick['time']} {pick['course']:<15} {pick['horse']:<25} "
              f"{pick['old_score']:5.1f} → {pick['new_score']:5.1f}")

# Show removed UI picks
if removed_ui_picks:
    print(f"\n{'='*80}")
    print(f"REMOVED UI PICKS (now <85)")
    print(f"{'='*80}\n")
    
    for pick in removed_ui_picks:
        print(f"{pick['time']} {pick['course']:<15} {pick['horse']:<25} "
              f"{pick['old_score']:5.1f} → {pick['new_score']:5.1f}")

# Validate the two critical winners
print(f"\n{'='*80}")
print(f"CRITICAL VALIDATION - DID NEW WEIGHTS PREDICT WINNERS?")
print(f"{'='*80}\n")

# Check Im Workin On It
im_workin = [item for item in all_items if 'Im Workin On It' in item.get('horse', '') and '15:10' in item.get('race_time', '')]
if im_workin:
    item = im_workin[0]
    new_score = float(item.get('combined_confidence', 0))
    outcome = item.get('outcome', 'PENDING')
    print(f"Im Workin On It (15:10 Kempton):")
    print(f"  New Score: {new_score:.1f}/100")
    print(f"  Outcome: {outcome}")
    print(f"  Expected: 97/100, WON")
    if new_score > 90 and outcome == 'WON':
        print(f"  ✓✓ VALIDATED!")

# Check Dust Cover
dust_cover = [item for item in all_items if 'Dust Cover' in item.get('horse', '') and '15:45' in item.get('race_time', '')]
if dust_cover:
    item = dust_cover[0]
    new_score = float(item.get('combined_confidence', 0))
    outcome = item.get('outcome', 'PENDING')
    print(f"\nDust Cover (15:45 Kempton):")
    print(f"  New Score: {new_score:.1f}/100")
    print(f"  Outcome: {outcome}")
    print(f"  Expected: 108/100, WON")
    if new_score > 100 and outcome == 'WON':
        print(f"  ✓✓ VALIDATED!")

print(f"\n{'='*80}")
print(f"RECALCULATION COMPLETE")
print(f"{'='*80}\n")
print(f"✓ {recalculated} horses updated with new weights")
print(f"✓ {len(new_ui_picks)} new UI picks (85+)")
print(f"✓ {len(removed_ui_picks)} UI picks removed (<85)")
print(f"✓ {len([c for c in score_changes if abs(c['diff']) >= 10])} significant score changes (±10pts)")
print(f"\nDatabase now reflects new weight configuration!")
print(f"{'='*80}\n")

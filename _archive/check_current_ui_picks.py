"""
Check if current UI picks are valid under new validation rules
"""
import boto3
from race_analysis_validator import validate_race_analysis
from weighted_form_analyzer import get_form_adjustment_for_confidence

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*80)
print("VALIDATING CURRENT UI PICKS - Feb 3, 2026")
print("="*80)

# Get all picks marked for UI display
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='show_in_ui = :show',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':show': True
    }
)

ui_picks = response.get('Items', [])

if not ui_picks:
    print("\nNo picks currently on UI")
else:
    print(f"\nFound {len(ui_picks)} picks on UI\n")
    
    # Group by race
    races = {}
    for pick in ui_picks:
        race_key = f"{pick.get('course')} {pick.get('race_time', '')}"
        if race_key not in races:
            races[race_key] = []
        races[race_key].append(pick)
    
    valid_count = 0
    invalid_count = 0
    
    for race_key, picks in races.items():
        print("-" * 80)
        print(f"RACE: {race_key}")
        print("-" * 80)
        
        # Get race details
        sample = picks[0]
        course = sample.get('course')
        race_time = sample.get('race_time', '')
        
        # Extract time part (HH:MM)
        if 'T' in race_time:
            time_part = race_time.split('T')[1].split(':')[0:2]
            time_str = ':'.join(time_part)
        else:
            time_str = race_time
        
        # Validate race completion
        is_valid, num_analyzed, total_horses, issues = validate_race_analysis(
            course, 
            time_str,
            '2026-02-03'
        )
        
        print(f"Analysis: {num_analyzed}/{total_horses} horses ({num_analyzed/total_horses*100 if total_horses > 0 else 0:.0f}%)")
        print(f"Validation: {'PASS' if is_valid else 'FAIL'}")
        
        if issues:
            print("Issues:")
            for issue in issues:
                print(f"  - {issue}")
        
        # Check each pick
        for pick in picks:
            horse = pick.get('horse', '')
            try:
                confidence = float(pick.get('confidence', 0))
            except:
                confidence = 0
            form = pick.get('form', '')
            
            # Determine threshold
            threshold = 55 if total_horses < 6 else 45
            
            # Get weighted form adjustment
            if form:
                adjustment, _ = get_form_adjustment_for_confidence(form)
            else:
                adjustment = 0
            
            adjusted_confidence = confidence + adjustment
            meets_threshold = adjusted_confidence >= threshold
            
            print(f"\n  Pick: {horse}")
            print(f"    Form: {form}")
            print(f"    Base confidence: {confidence:.0f}/100")
            print(f"    Form adjustment: {adjustment:+d}")
            print(f"    Adjusted: {adjusted_confidence:.0f}/100")
            print(f"    Threshold: {threshold}/100 ({'small field' if total_horses < 6 else 'normal'})")
            print(f"    Meets threshold: {'YES' if meets_threshold else 'NO'}")
        
        if is_valid:
            print(f"\n[VALID] This pick should STAY on UI")
            valid_count += 1
        else:
            print(f"\n[INVALID] This pick should be REMOVED from UI")
            invalid_count += 1
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total UI picks: {len(races)} races")
    print(f"Valid under new rules: {valid_count}")
    print(f"Invalid (should remove): {invalid_count}")
    
    if invalid_count > 0:
        print(f"\n[WARNING] {invalid_count} races on UI do not meet new validation requirements")
        print("Recommendation: Remove these picks and wait for complete analysis")
    else:
        print(f"\n[OK] All UI picks meet new validation requirements")

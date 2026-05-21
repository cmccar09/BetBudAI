"""
Update Today's Results with UI Picks Only - 4-Tier Grading Validation
This script generates a comprehensive results report for all UI picks

4-Tier Grading System:
- EXCELLENT (70+): Green - 2.0x stake - Should win or place consistently
- GOOD (55-69): Light amber - 1.5x stake - Strong contenders
- FAIR (40-54): Dark amber - 1.0x stake - Moderate chances
- POOR (<40): Red - 0.5x stake - Long shots

Only shows picks that were marked show_in_ui=True (validated picks)
"""

import boto3
from datetime import datetime
from decimal import Decimal

def get_todays_ui_picks():
    """Get all UI picks for today with 4-tier grading"""
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Query only picks that passed validation and were set as UI picks
    response = table.query(
        KeyConditionExpression='bet_date = :today',
        FilterExpression='show_in_ui = :true',
        ExpressionAttributeValues={
            ':today': today,
            ':true': True
        }
    )
    
    return response.get('Items', [])

def validate_4tier_grading(score, grade):
    """Validate that grade matches 4-tier system"""
    expected_grade = (
        'EXCELLENT' if score >= 75 else
        'GOOD' if score >= 60 else
        'FAIR' if score >= 45 else
        'POOR'
    )
    return grade == expected_grade

def generate_results_summary():
    """Generate comprehensive results summary for UI picks only"""
    
    print("="*80)
    print("TODAY'S RESULTS - UI PICKS ONLY (4-TIER GRADING VALIDATION)")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    picks = get_todays_ui_picks()
    
    if not picks:
        print("No UI picks found for today.")
        print("Run the workflow: python value_betting_workflow.py")
        return
    
    # Group by race
    races = {}
    for pick in picks:
        race_key = f"{pick.get('race_time', 'N/A')} {pick.get('course', 'N/A')}"
        if race_key not in races:
            races[race_key] = []
        races[race_key].append(pick)
    
    print(f"TOTAL UI PICKS: {len(picks)}")
    print(f"RACES: {len(races)}\n")
    
    # Stats
    by_grade = {'EXCELLENT': 0, 'GOOD': 0, 'FAIR': 0, 'POOR': 0}
    validation_issues = []
    
    print("="*80)
    print("PICKS BY RACE (Sorted by Time)")
    print("="*80)
    
    for race_key in sorted(races.keys()):
        race_picks = races[race_key]
        pick = race_picks[0]  # Should only be 1 per race
        
        if len(race_picks) > 1:
            print(f"\nWARNING: {race_key} has {len(race_picks)} picks (should be 1)")
        
        score = float(pick.get('combined_confidence', 0))
        grade = pick.get('confidence_grade', 'N/A')
        
        # Validate 4-tier grading
        is_valid = validate_4tier_grading(score, grade)
        
        if not is_valid:
            expected = (
                'EXCELLENT' if score >= 70 else
                'GOOD' if score >= 55 else
                'FAIR' if score >= 40 else
                'POOR'
            )
            validation_issues.append(f"{race_key} - {pick['horse']}: Grade={grade} but score={score:.0f} (should be {expected})")
        
        # Count by grade
        by_grade[grade] = by_grade.get(grade, 0) + 1
        
        # Display pick
        validation_mark = "[OK]" if is_valid else "[FAIL]"
        
        # Get coverage info
        coverage = pick.get('race_coverage_pct', 'N/A')
        analyzed = pick.get('race_analyzed_count', '?')
        total = pick.get('race_total_count', '?')
        
        print(f"\n{race_key}")
        if coverage != 'N/A':
            coverage_status = "[OK]" if float(coverage) >= 90 else "[LOW]"
            print(f"  Coverage: {analyzed}/{total} horses ({coverage}%) {coverage_status}")
        print(f"  {validation_mark} {pick['horse']:30} {score:5.1f}/100 {grade:10}")
        
        # Show form
        form = pick.get('form', 'N/A')
        if form and form != 'N/A':
            print(f"     Form: {form}")
        
        # Show analysis quality and coverage
        analysis_type = pick.get('analysis_type', 'N/A')
        coverage = pick.get('race_coverage_pct', 'N/A')
        if analysis_type == 'PRE_RACE_COMPLETE' or analysis_type == 'COMPLETE_ANALYSIS':
            print(f"     Analysis: Complete [OK]")
            if coverage != 'N/A':
                print(f"     Coverage: {coverage}% of field analyzed")
    
    # Summary
    print("\n" + "="*80)
    print("GRADING DISTRIBUTION")
    print("="*80)
    
    total = sum(by_grade.values())
    for grade in ['EXCELLENT', 'GOOD', 'FAIR', 'POOR']:
        count = by_grade.get(grade, 0)
        pct = (count / total * 100) if total > 0 else 0
        
        # Get color
        color_emoji = {
            'EXCELLENT': '[GREEN]',
            'GOOD': '[AMBER]',
            'FAIR': '[ORANGE]',
            'POOR': '[RED]'
        }.get(grade, '')
        
        # Get stake multiplier
        multiplier = {
            'EXCELLENT': '2.0x',
            'GOOD': '1.5x',
            'FAIR': '1.0x',
            'POOR': '0.5x'
        }.get(grade, '')
        
        print(f"{color_emoji} {grade:10} {count:3} picks ({pct:5.1f}%) - {multiplier} stake")
    
    # Validation report
    if validation_issues:
        print("\n" + "="*80)
        print("WARNING: GRADING VALIDATION ISSUES")
        print("="*80)
        for issue in validation_issues:
            print(f"  {issue}")
        print("\nRun: python calculate_all_confidence_scores.py to fix")
    else:
        print("\n" + "="*80)
        print("ALL PICKS PASS 4-TIER GRADING VALIDATION")
        print("="*80)
    
    # Expected thresholds
    print("\n" + "="*80)
    print("4-TIER GRADING THRESHOLDS")
    print("="*80)
    print("EXCELLENT: 75+ points  (Green)       2.0x stake")
    print("GOOD:      60-74 points (Light amber) 1.5x stake")
    print("FAIR:      45-59 points (Dark amber)  1.0x stake")
    print("POOR:      <45 points   (Red)         0.5x stake")
    
    print("\n" + "="*80)
    print("VALIDATION REQUIREMENTS")
    print("="*80)
    print("* One pick per race (highest scored)")
    print("* >=75% race coverage required")
    print("* >=90% coverage for small fields (<6 runners)")
    print("* Conservative scoring (100/100 should be rare)")
    print("* Improvement pattern detection active")

if __name__ == "__main__":
    generate_results_summary()

"""
Race Analysis Validator - Ensures complete race analysis before betting
Critical fixes based on Carlisle 14:00 loss (Feb 3, 2026)
"""
import boto3
from datetime import datetime

# Always use eu-west-1
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')


def validate_race_analysis(course, race_time, bet_date='2026-02-03'):
    """
    Validate that a race has complete analysis before allowing bets
    
    Requirements based on Carlisle 14:00 lessons:
    1. At least 75% of horses must be analyzed (have confidence > 0)
    2. All LTO winners (form starts with '1') must be analyzed
    3. Small fields (<6 runners) need stricter validation
    
    Returns: (is_valid, num_analyzed, total_horses, issues)
    """
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        FilterExpression='course = :course',
        ExpressionAttributeValues={
            ':date': bet_date,
            ':course': course
        }
    )
    
    items = response.get('Items', [])
    race_horses = [item for item in items if race_time in item.get('race_time', '')]
    
    if not race_horses:
        return False, 0, 0, ["No horses found for this race"]
    
    # Remove duplicates (take highest confidence version)
    unique_horses = {}
    for item in race_horses:
        horse_name = item.get('horse', '')
        conf = float(item.get('confidence', 0))
        
        if horse_name not in unique_horses or conf > float(unique_horses[horse_name].get('confidence', 0)):
            unique_horses[horse_name] = item
    
    race_horses = list(unique_horses.values())
    total_horses = len(race_horses)
    
    # Count analyzed horses
    analyzed = []
    for h in race_horses:
        try:
            conf = float(h.get('confidence', 0))
            if conf > 0:
                analyzed.append(h)
        except (ValueError, TypeError):
            pass  # Skip non-numeric confidence values
            
    num_analyzed = len(analyzed)
    
    analysis_percentage = (num_analyzed / total_horses * 100) if total_horses > 0 else 0
    
    issues = []
    
    # Check 1: Minimum 75% analyzed
    if analysis_percentage < 75:
        issues.append(f"Only {analysis_percentage:.0f}% analyzed (need >=75%)")
    
    # Check 2: All LTO winners must be analyzed
    unanalyzed_lto_winners = []
    for horse in race_horses:
        try:
            conf = float(horse.get('confidence', 0))
        except (ValueError, TypeError):
            conf = 0
        
        form = horse.get('form', '')
        horse_name = horse.get('horse', '')
        
        # LTO winner = form starts with '1'
        if form and len(form) > 0 and form[0] == '1' and conf == 0:
            unanalyzed_lto_winners.append(horse_name)
    
    if unanalyzed_lto_winners:
        issues.append(f"LTO winners not analyzed: {', '.join(unanalyzed_lto_winners)}")
    
    # Check 3: Small field validation (stricter for <6 runners)
    if total_horses < 6:
        if analysis_percentage < 90:
            issues.append(f"Small field ({total_horses} runners) needs >=90% analyzed")
    
    is_valid = len(issues) == 0
    
    return is_valid, num_analyzed, total_horses, issues


def get_validated_picks(bet_date='2026-02-03', min_confidence=45):
    """
    Get picks that pass validation checks
    
    Based on Carlisle 14:00 lessons:
    - Require complete race analysis
    - Adjust threshold for small fields
    - Prioritize LTO winners
    """
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        ExpressionAttributeValues={':date': bet_date}
    )
    
    items = response.get('Items', [])
    
    # Group by race
    races = {}
    for item in items:
        course = item.get('course', '')
        race_time = item.get('race_time', '')
        key = f"{course}_{race_time}"
        
        if key not in races:
            races[key] = []
        races[key].append(item)
    
    validated_picks = []
    validation_report = []
    
    for race_key, horses in races.items():
        course, race_time = race_key.split('_', 1)
        
        # Deduplicate horses (take highest confidence)
        unique_horses = {}
        for item in horses:
            horse_name = item.get('horse', '')
            try:
                conf = float(item.get('confidence', 0))
            except (ValueError, TypeError):
                conf = 0
            
            if horse_name not in unique_horses:
                unique_horses[horse_name] = item
            else:
                try:
                    existing_conf = float(unique_horses[horse_name].get('confidence', 0))
                except (ValueError, TypeError):
                    existing_conf = 0
                    
                if conf > existing_conf:
                    unique_horses[horse_name] = item
        
        horses = list(unique_horses.values())
        total_horses = len(horses)
        
        # Validate race analysis
        is_valid, num_analyzed, total, issues = validate_race_analysis(course, race_time, bet_date)
        
        # Adjust threshold for small fields (<6 runners = higher threshold)
        threshold = 55 if total_horses < 6 else min_confidence
        
        # Find picks in this race
        race_picks = []
        for horse in horses:
            try:
                conf = float(horse.get('confidence', 0))
            except (ValueError, TypeError):
                conf = 0  # Handle non-numeric confidence values
                
            form = horse.get('form', '')
            horse_name = horse.get('horse', '')
            
            try:
                odds = float(horse.get('odds', 0))
            except (ValueError, TypeError):
                odds = 0
            
            # LTO winner priority (form starts with '1' and odds 1.5-3.0)
            is_lto_winner = form and len(form) > 0 and form[0] == '1'
            is_quality_favorite = 1.5 <= odds < 3.0
            
            if conf >= threshold:
                race_picks.append({
                    'horse': horse_name,
                    'course': course,
                    'race_time': race_time,
                    'confidence': conf,
                    'odds': odds,
                    'form': form,
                    'is_lto_winner': is_lto_winner,
                    'is_quality_favorite': is_quality_favorite,
                    'threshold_used': threshold,
                    'data': horse
                })
        
        if race_picks:
            validation_report.append({
                'race': race_key,
                'valid': is_valid,
                'analyzed': f"{num_analyzed}/{total}",
                'issues': issues,
                'picks': len(race_picks),
                'threshold': threshold
            })
            
            if is_valid:
                validated_picks.extend(race_picks)
            else:
                print(f"\n[WARNING] {course} {race_time}:")
                print(f"  Picks found: {len(race_picks)}")
                print(f"  Validation: FAILED")
                for issue in issues:
                    print(f"    - {issue}")
                print(f"  [ACTION] Skipping picks from incomplete race analysis")
    
    return validated_picks, validation_report


if __name__ == '__main__':
    print("="*100)
    print("RACE ANALYSIS VALIDATION - Feb 3, 2026")
    print("="*100)
    
    # Test validation on today's races
    picks, report = get_validated_picks()
    
    print(f"\n{'='*100}")
    print("VALIDATION REPORT")
    print("="*100)
    
    for r in report:
        status = "[OK]" if r['valid'] else "[FAIL]"
        print(f"\n{status} {r['race']}")
        print(f"  Analyzed: {r['analyzed']}")
        print(f"  Threshold: {r['threshold']}/100")
        print(f"  Picks: {r['picks']}")
        if r['issues']:
            print(f"  Issues:")
            for issue in r['issues']:
                print(f"    - {issue}")
    
    print(f"\n{'='*100}")
    print(f"VALIDATED PICKS: {len(picks)}")
    print("="*100)
    
    for pick in sorted(picks, key=lambda x: x['confidence'], reverse=True):
        lto = " [LTO WINNER]" if pick['is_lto_winner'] else ""
        qf = " [QUALITY FAV]" if pick['is_quality_favorite'] else ""
        print(f"\n{pick['horse']:<30} {pick['confidence']:>5.1f}/100 @ {pick['odds']:>6.2f}{lto}{qf}")
        print(f"  {pick['course']} {pick['race_time']}")
        print(f"  Form: {pick['form']}")
        print(f"  Threshold: {pick['threshold_used']}/100")

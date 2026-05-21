"""
Generate UI picks from validated database entries
Uses race_analysis_validator to ensure only complete races appear on UI
"""
import boto3
from decimal import Decimal
from datetime import datetime
from race_analysis_validator import get_validated_picks, validate_race_analysis
from weighted_form_analyzer import get_form_adjustment_for_confidence

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*80)
print("GENERATING UI PICKS FROM VALIDATED RACES")
print("="*80)
print("Strategy: Pick TOP 10 best horses across ALL races (not 1 per race)")
print("="*80)

# Get all validated picks
bet_date = '2026-02-03'
validated_picks, validation_report = get_validated_picks(bet_date, min_confidence=0)

print(f"\nFound {len(validated_picks)} horses in validated races")

# Group by race
races = {}
for pick in validated_picks:
    race_key = f"{pick.get('course')}_{pick.get('race_time')}"
    if race_key not in races:
        races[race_key] = []
    races[race_key].append(pick)

print(f"Across {len(races)} races\n")

# NEW STRATEGY: Instead of 1 pick per race, find BEST horses across ALL races
all_candidates = []
MAX_UI_PICKS = 10  # Only show top 10 picks per day

for race_key, picks in races.items():
    if not picks:
        continue
    
    sample = picks[0]
    course = sample.get('course', '')
    race_time = sample.get('race_time', '')
    
    # Extract time for validation
    if 'T' in race_time:
        time_str = race_time.split('T')[1].split(':')[0:2]
        time_str = ':'.join(time_str)
    else:
        time_str = race_time
    
    # Validate race
    is_valid, num_analyzed, total_horses, issues = validate_race_analysis(
        course, time_str, bet_date
    )
    
    if not is_valid:
        continue  # Skip invalid races silently
    
    # Calculate coverage percentage
    coverage = (num_analyzed / total_horses) * 100 if total_horses > 0 else 0
    threshold = 55  # FAIR minimum (15-25% win probability)
    
    # Evaluate ALL horses in this race
    for pick in picks:
        try:
            base_conf = float(pick.get('confidence', 0))
        except:
            base_conf = 0
        
        # Apply weighted form adjustment
        form = pick.get('form', '')
        if form:
            form_adj, _ = get_form_adjustment_for_confidence(form)
        else:
            form_adj = 0
        
        adjusted_score = base_conf + form_adj
        
        # Only consider horses above threshold
        if adjusted_score >= threshold:
            horse = pick['data'].get('horse', '')
            bet_id = pick['data'].get('bet_id', '')
            
            if bet_id:  # Valid bet_id
                all_candidates.append({
                    'bet_id': bet_id,
                    'horse': horse,
                    'course': course,
                    'race_time': race_time,
                    'adjusted_score': adjusted_score,
                    'base_confidence': base_conf,
                    'form_adjustment': form_adj,
                    'form': form,
                    'coverage': coverage,
                    'num_analyzed': num_analyzed,
                    'total_horses': total_horses
                })

# Sort all candidates by adjusted score (highest first)
all_candidates.sort(key=lambda x: x['adjusted_score'], reverse=True)

# Take only top MAX_UI_PICKS
top_picks = all_candidates[:MAX_UI_PICKS]

print(f"\nEvaluated {len(all_candidates)} horses above threshold across all races")
print(f"Selecting TOP {MAX_UI_PICKS} for UI display\n")

# Set show_in_ui for the top picks
ui_picks_set = 0
for pick in top_picks:
    try:
        table.update_item(
            Key={
                'bet_date': bet_date,
                'bet_id': pick['bet_id']
            },
            UpdateExpression='SET show_in_ui = :true, combined_confidence = :conf, confidence_level = :level, confidence_grade = :grade, confidence_color = :color, race_coverage_pct = :coverage, race_analyzed_count = :analyzed, race_total_count = :total',
            ExpressionAttributeValues={
                ':true': True,
                ':conf': Decimal(str(pick['adjusted_score'])),
                ':level': 'HIGH' if pick['adjusted_score'] >= 85 else 'MEDIUM' if pick['adjusted_score'] >= 70 else 'LOW',
                ':grade': 'EXCELLENT' if pick['adjusted_score'] >= 85 else 'GOOD' if pick['adjusted_score'] >= 70 else 'FAIR' if pick['adjusted_score'] >= 55 else 'POOR',
                ':color': 'green' if pick['adjusted_score'] >= 85 else '#FFB84D' if pick['adjusted_score'] >= 70 else '#FF8C00' if pick['adjusted_score'] >= 55 else 'red',
                ':coverage': Decimal(str(int(pick['coverage']))),
                ':analyzed': pick['num_analyzed'],
                ':total': pick['total_horses']
            }
        )
        
        print(f"[UI PICK #{ui_picks_set + 1}] {pick['course']} {pick['race_time']}")
        print(f"  {pick['horse']}")
        print(f"  Score: {pick['adjusted_score']:.0f}/100 (base: {pick['base_confidence']:.0f}, form adj: {pick['form_adjustment']:+.0f})")
        print(f"  Form: {pick['form']}")
        print(f"  Coverage: {pick['coverage']:.0f}% ({pick['num_analyzed']}/{pick['total_horses']} horses)")
        print()
        
        ui_picks_set += 1
    except Exception as e:
        print(f"  ERROR updating {pick['horse']}: {str(e)}")

print("="*80)
print("SUMMARY")
print("="*80)
print(f"Total candidates evaluated: {len(all_candidates)}")
print(f"UI picks set: {ui_picks_set} (max {MAX_UI_PICKS})")
print(f"Remaining horses: {len(all_candidates) - ui_picks_set} (for learning/training)")
print(f"\nPicks now visible on UI!")

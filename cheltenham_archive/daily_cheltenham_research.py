"""
Daily Cheltenham Research Workflow
Monitors all potential Cheltenham horses daily, tracks improving form, identifies winners

This runs daily to:
1. Analyze horses in Grade 1/2 races that could run at Cheltenham
2. Track form improvements over time
3. Identify horses peaking for the Festival
4. Build historical profiles for Cheltenham analysis

Usage:
    python daily_cheltenham_research.py
    python daily_cheltenham_research.py --track-only  # Just update tracking, no new analysis
"""

import boto3
from datetime import datetime, timedelta
import json
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from comprehensive_pick_logic import (
    analyze_horse_comprehensive,
    DEFAULT_WEIGHTS,
    get_confidence_tier
)

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
research_table = dynamodb.Table('CheltenhamResearch')  # New table for tracking
picks_table = dynamodb.Table('SureBetBets')

# Cheltenham target trainers (monitor their runners daily)
CHELTENHAM_TARGET_TRAINERS = [
    'W. P. Mullins', 'Willie Mullins',
    'Gordon Elliott', 'G. Elliott',
    'Nicky Henderson', 'N. Henderson',
    'Paul Nicholls', 'P. Nicholls',
    'Henry de Bromhead', 'H. de Bromhead',
    'Dan Skelton', 'D. Skelton',
    'Fergal O\'Brien', 'F. O\'Brien',
    'Evan Williams', 'E. Williams'
]

# Cheltenham-relevant race types
CHELTENHAM_RACE_TYPES = [
    'Grade 1', 'Grade 2', 'Grade 3',
    'Listed', 'Graded'
]

def fetch_todays_graded_races():
    """
    Fetch all Grade 1/2/3 races from today's schedule
    These are potential Cheltenham prep races
    """
    # This would integrate with your race API
    # For now, placeholder that shows the structure
    
    print("Fetching today's graded races...")
    
    # TODO: Replace with actual API call to racing API
    # races = fetch_races_from_api(date=datetime.now())
    
    # Example structure
    races = []
    
    return races

def get_horse_history(horse_name):
    """
    Get historical tracking data for a horse from research table
    """
    try:
        response = research_table.query(
            KeyConditionExpression=Key('horse_name').eq(horse_name),
            ScanIndexForward=False,  # Most recent first
            Limit=10
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error fetching history for {horse_name}: {e}")
        return []

def calculate_form_trend(history):
    """
    Analyze if horse is improving, declining, or stable
    
    Returns:
        trend: 'improving', 'declining', 'stable'
        trend_score: numeric indicator
    """
    if len(history) < 2:
        return 'unknown', 0
    
    # Get scores from last 5 runs
    scores = [float(h.get('score', 0)) for h in history[:5]]
    
    if len(scores) < 2:
        return 'unknown', 0
    
    # Calculate trend
    recent_avg = sum(scores[:2]) / 2
    older_avg = sum(scores[2:]) / len(scores[2:]) if len(scores) > 2 else scores[0]
    
    trend_score = recent_avg - older_avg
    
    if trend_score > 10:
        return 'improving', trend_score
    elif trend_score < -10:
        return 'declining', trend_score
    else:
        return 'stable', trend_score

def is_cheltenham_candidate(horse_data, race_data):
    """
    Determine if this horse is a Cheltenham Festival candidate
    
    Criteria:
    - Elite trainer
    - Grade 1/2 race
    - Age appropriate (4yo+ for most races)
    - Good recent form
    """
    trainer = horse_data.get('trainer', '')
    race_type = race_data.get('type', '')
    
    # Must have elite trainer
    if not any(target in trainer for target in CHELTENHAM_TARGET_TRAINERS):
        return False
    
    # Must be in graded race
    if not any(grade in race_type for grade in CHELTENHAM_RACE_TYPES):
        return False
    
    return True

def save_research_entry(horse_data, race_data, analysis):
    """
    Save daily research entry for a horse to tracking table
    """
    today = datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.now().isoformat()
    
    item = {
        'horse_name': horse_data.get('name', 'Unknown'),
        'research_date': today,
        'timestamp': timestamp,
        'trainer': horse_data.get('trainer', ''),
        'jockey': horse_data.get('jockey', ''),
        'score': Decimal(str(analysis['score'])),
        'confidence_tier': analysis['confidence_tier'],
        'race_name': race_data.get('name', ''),
        'race_type': race_data.get('type', ''),
        'course': race_data.get('course', ''),
        'odds': Decimal(str(horse_data.get('odds', 0))),
        'form': horse_data.get('form', ''),
        'going': race_data.get('going', ''),
        'reasoning': analysis['reasoning'],
        'cheltenham_candidate': analysis.get('cheltenham_candidate', False),
        'form_trend': analysis.get('form_trend', 'unknown'),
        'trend_score': Decimal(str(analysis.get('trend_score', 0))),
    }
    
    try:
        research_table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"Error saving research for {item['horse_name']}: {e}")
        return False

def generate_daily_cheltenham_report():
    """
    Generate daily report of Cheltenham candidates and trends
    """
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n{'='*80}")
    print(f"DAILY CHELTENHAM RESEARCH REPORT - {today}")
    print(f"{'='*80}\n")
    
    # Query all today's research entries
    try:
        response = research_table.query(
            IndexName='ResearchDateIndex',  # Need to create this GSI
            KeyConditionExpression=Key('research_date').eq(today)
        )
        entries = response.get('Items', [])
    except:
        print("Note: Need to create CheltenhamResearch table and ResearchDateIndex GSI")
        entries = []
    
    if not entries:
        print("No Cheltenham candidates analyzed today.")
        return
    
    # Categorize entries
    improving = [e for e in entries if e.get('form_trend') == 'improving']
    high_scores = [e for e in entries if float(e.get('score', 0)) >= 75]
    new_candidates = [e for e in entries if e.get('cheltenham_candidate')]
    
    print(f"SUMMARY:")
    print(f"  Total horses analyzed: {len(entries)}")
    print(f"  High scorers (75+): {len(high_scores)}")
    print(f"  Improving form: {len(improving)}")
    print(f"  New candidates identified: {len(new_candidates)}\n")
    
    if improving:
        print(f"🔥 IMPROVING FORM (Watch for Cheltenham):")
        print(f"{'='*80}")
        for horse in sorted(improving, key=lambda x: float(x.get('trend_score', 0)), reverse=True)[:10]:
            print(f"  {horse['horse_name']:25s} {float(horse['score']):3.0f}pts (+{float(horse['trend_score']):.1f} trend)")
            print(f"    Trainer: {horse.get('trainer', 'Unknown'):30s} Race: {horse.get('race_name', 'Unknown')}")
            print()
    
    if high_scores:
        print(f"\n⭐ HIGH SCORERS TODAY (75+ pts):")
        print(f"{'='*80}")
        for horse in sorted(high_scores, key=lambda x: float(x.get('score', 0)), reverse=True):
            print(f"  {horse['horse_name']:25s} {float(horse['score']):3.0f}pts {horse.get('confidence_tier', '')}")
            print(f"    {horse.get('race_name', 'Unknown')} - {horse.get('course', 'Unknown')}")
            print()
    
    print(f"\n{'='*80}\n")

def analyze_cheltenham_prep_race(race_data):
    """
    Analyze a single race for Cheltenham candidates
    """
    race_name = race_data.get('name', 'Unknown')
    print(f"\nAnalyzing: {race_name}")
    
    runners = race_data.get('runners', [])
    candidates_found = 0
    
    for horse in runners:
        # Check if Cheltenham candidate
        if not is_cheltenham_candidate(horse, race_data):
            continue
        
        # Get comprehensive analysis
        score, reasoning, breakdown = analyze_horse_comprehensive(
            horse,
            race_data,
            DEFAULT_WEIGHTS
        )
        
        # Get historical data
        history = get_horse_history(horse.get('name', ''))
        
        # Calculate trend
        trend, trend_score = calculate_form_trend(history)
        
        # Package analysis
        analysis = {
            'score': score,
            'confidence_tier': get_confidence_tier(score),
            'reasoning': reasoning,
            'breakdown': breakdown,
            'cheltenham_candidate': True,
            'form_trend': trend,
            'trend_score': trend_score,
            'history_count': len(history)
        }
        
        # Save to research table
        if save_research_entry(horse, race_data, analysis):
            candidates_found += 1
            
            # Print interesting findings
            if score >= 75 or trend == 'improving':
                print(f"  ✓ {horse.get('name', 'Unknown'):25s} {score:.0f}pts (trend: {trend} {trend_score:+.1f})")
    
    return candidates_found

def main():
    """
    Main daily Cheltenham research workflow
    """
    print(f"\n{'#'*80}")
    print(f"DAILY CHELTENHAM RESEARCH - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}\n")
    
    print("OBJECTIVE:")
    print("  1. Monitor all Grade 1/2/3 races daily")
    print("  2. Track elite trainer runners (Mullins, Elliott, Henderson, etc.)")
    print("  3. Identify improving form trends")
    print("  4. Build profiles for Cheltenham Festival picks\n")
    
    # Fetch today's graded races
    races = fetch_todays_graded_races()
    
    if not races:
        print("⚠️  No graded races found today - checking API connection...")
        print("Note: This would normally fetch from racing API")
        print("For testing, run comprehensive_workflow.py to see today's races\n")
        return
    
    # Analyze each race
    total_candidates = 0
    for race in races:
        candidates = analyze_cheltenham_prep_race(race)
        total_candidates += candidates
    
    print(f"\nTotal Cheltenham candidates tracked today: {total_candidates}")
    
    # Generate daily report
    generate_daily_cheltenham_report()
    
    print(f"\n{'#'*80}")
    print("NEXT STEPS:")
    print("  • Review improving form horses")
    print("  • Monitor for Festival entries")
    print("  • Track scores over next runs")
    print("  • Identify horses peaking in March")
    print(f"{'#'*80}\n")

if __name__ == '__main__':
    import sys
    
    if '--track-only' in sys.argv:
        generate_daily_cheltenham_report()
    else:
        main()

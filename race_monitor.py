"""
RACE MONITOR - Watch upcoming recommended picks
Monitor races happening BEFORE our picks to gather intelligence

This script:
1. Lists all recommended picks for today
2. Shows which races happen before each pick
3. Highlights learnings to watch for
4. Updates confidence based on pattern changes
"""

import boto3
from datetime import datetime
from collections import defaultdict

def get_todays_picks():
    """Get all recommended picks for today"""
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
    )
    
    items = resp.get('Items', [])
    
    # Filter to recommended picks only
    picks = [i for i in items if i.get('show_in_ui') and i.get('recommended_bet')]
    
    # Sort by race time
    picks.sort(key=lambda x: x.get('race_time', ''))
    
    return picks

def analyze_pre_race_intel(pick):
    """Identify what to watch in races before this pick"""
    course = pick.get('course', '')
    trainer = pick.get('trainer', '')
    odds = float(pick.get('odds', 0))
    race_time = pick.get('race_time', '')
    
    intel = {
        'watch_for': []
    }
    
    # Watch same trainer in earlier races
    intel['watch_for'].append(f"Trainer {trainer} performance in earlier races today")
    
    # Watch odds range performance
    if 3 <= odds < 9:
        intel['watch_for'].append("Sweet spot (3-9) performance at this track today")
    elif 2 <= odds < 3:
        intel['watch_for'].append("Favorite (2-3) performance at this track today")
    
    # Watch same track
    intel['watch_for'].append(f"Winner odds patterns at {course} today")
    
    # Watch going conditions
    intel['watch_for'].append(f"Heavy going performance (if turf)")
    
    return intel

def display_race_monitor():
    """Display monitoring dashboard for today's picks"""
    picks = get_todays_picks()
    
    if not picks:
        print("\n⚠️  No recommended picks found for today")
        print("   Run comprehensive_workflow.py first")
        return
    
    current_time = datetime.now()
    current_time_utc = datetime.utcnow()
    
    print("\n" + "="*80)
    print(f"RACE MONITOR - Today's Recommended Picks")
    print("="*80)
    print(f"Current time (UTC): {current_time_utc.strftime('%H:%M')}")
    print(f"Total recommended picks: {len(picks)}")
    print("="*80 + "\n")
    
    upcoming_picks = []
    finished_picks = []
    
    for pick in picks:
        race_time_str = pick.get('race_time', '')
        try:
            race_dt = datetime.fromisoformat(race_time_str.replace('Z', ''))
            race_time_local = race_dt.strftime('%H:%M')
            
            if race_dt > current_time_utc:
                upcoming_picks.append((pick, race_dt, race_time_local))
            else:
                finished_picks.append((pick, race_dt, race_time_local))
        except:
            pass
    
    if finished_picks:
        print("⏱️  RACES THAT HAVE PASSED:")
        for pick, race_dt, race_time_local in finished_picks:
            horse = pick.get('horse', '')
            course = pick.get('course', '')
            score = float(pick.get('comprehensive_score', 0))
            outcome = pick.get('outcome', 'pending')
            
            outcome_icon = "✓" if outcome == "WON" else "✗" if outcome == "LOST" else "⏳"
            print(f"   {outcome_icon} {race_time_local} {course:20} {horse:25} {score:.0f}/100")
        print()
    
    if not upcoming_picks:
        print("ℹ️  All picks have finished or no upcoming picks")
        return
    
    print("🎯 UPCOMING RECOMMENDED PICKS:\n")
    
    for i, (pick, race_dt, race_time_local) in enumerate(upcoming_picks, 1):
        horse = pick.get('horse', '')
        course = pick.get('course', '')
        trainer = pick.get('trainer', '')
        odds = float(pick.get('odds', 0))
        score = float(pick.get('comprehensive_score', 0))
        
        time_until = race_dt - current_time_utc
        minutes_until = int(time_until.total_seconds() / 60)
        
        print(f"{i}. {race_time_local} - {course}")
        print(f"   🐴 {horse} @ {odds}")
        print(f"   📊 Score: {score:.0f}/100")
        print(f"   👤 Trainer: {trainer}")
        print(f"   ⏰ In {minutes_until} minutes")
        
        # Show intelligence to gather
        intel = analyze_pre_race_intel(pick)
        print(f"   👁️  WATCH BEFORE THIS RACE:")
        for item in intel['watch_for']:
            print(f"      • {item}")
        print()
    
    print("="*80)
    print("MONITORING STRATEGY:")
    print("="*80)
    print("1. Run intraday_learning_system.py after each hour")
    print("2. Check if patterns support our picks")
    print("3. Adjust stakes if trainer/odds patterns change")
    print("4. Update intraday_learnings.json with fresh insights")
    print("="*80 + "\n")

if __name__ == "__main__":
    display_race_monitor()

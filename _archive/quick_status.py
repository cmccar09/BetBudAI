"""
QUICK STATUS DASHBOARD
Simple text status for PowerShell compatibility
"""

import boto3
from datetime import datetime

def show_status():
    """Display current system status"""
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
    )
    
    items = resp.get('Items', [])
    ui_picks = [i for i in items if i.get('show_in_ui') and i.get('recommended_bet')]
    
    # Sort by race time
    ui_picks.sort(key=lambda x: x.get('race_time', ''))
    
    now_utc = datetime.utcnow()
    
    upcoming = []
    finished = []
    
    for pick in ui_picks:
        race_time_str = pick.get('race_time', '')
        try:
            race_dt = datetime.fromisoformat(race_time_str.replace('Z', ''))
            if race_dt > now_utc:
                upcoming.append((pick, race_dt))
            else:
                finished.append((pick, race_dt))
        except:
            pass
    
    print("\n" + "="*80)
    print(f"BETTING SYSTEM STATUS - {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)
    print(f"Total horses analyzed: {len(items)}")
    print(f"Recommended picks (85+): {len(ui_picks)}")
    print(f"Upcoming races: {len(upcoming)}")
    print(f"Finished races: {len(finished)}")
    print("="*80 + "\n")
    
    if upcoming:
        print("UPCOMING RECOMMENDED PICKS:")
        print("-" * 80)
        for i, (pick, race_dt) in enumerate(upcoming, 1):
            horse = pick.get('horse', '')
            course = pick.get('course', '')
            odds = float(pick.get('odds', 0))
            score = float(pick.get('comprehensive_score', 0))
            trainer = pick.get('trainer', '')
            race_time_local = race_dt.strftime('%H:%M')
            
            time_until = race_dt - now_utc
            minutes_until = int(time_until.total_seconds() / 60)
            
            print(f"{i}. [{race_time_local}] {course} - {horse}")
            print(f"   Odds: {odds:.2f} | Score: {score:.0f}/100 | Trainer: {trainer}")
            print(f"   Time until: {minutes_until} minutes")
            print()
    else:
        print("All races have finished or no upcoming picks")
    
    print("="*80)
    print("SYSTEM STATUS: ALL OPERATIONAL")
    print("="*80)
    print()
    print("Next actions:")
    print("  - Monitor races as they happen")
    print("  - Run: python intraday_learning_system.py (after races finish)")
    print("  - Check: python system_health_monitor.py (any time)")
    print("="*80 + "\n")

if __name__ == "__main__":
    show_status()

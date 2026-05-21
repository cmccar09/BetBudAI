"""
SYSTEM HEALTH MONITOR
Continuously check that betting workflow is running correctly
"""

import boto3
from datetime import datetime
import json
import os

def check_database_connection():
    """Verify DynamoDB is accessible"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('SureBetBets')
        today = datetime.now().strftime('%Y-%m-%d')
        
        resp = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today),
            Limit=1
        )
        return True, "Database accessible"
    except Exception as e:
        return False, f"Database error: {str(e)}"

def check_race_data():
    """Verify we have fresh race data"""
    try:
        if not os.path.exists('response_horses.json'):
            return False, "response_horses.json missing"
        
        with open('response_horses.json', 'r') as f:
            data = json.load(f)
        
        races = data.get('races', [])
        if not races:
            return False, "No races in response_horses.json"
        
        # Check file age
        file_age_hours = (datetime.now().timestamp() - os.path.getmtime('response_horses.json')) / 3600
        
        if file_age_hours > 2:
            return False, f"Race data is {file_age_hours:.1f}h old (refresh needed)"
        
        return True, f"{len(races)} races loaded ({file_age_hours:.1f}h old)"
    except Exception as e:
        return False, f"Race data error: {str(e)}"

def check_todays_picks():
    """Verify we have recommended picks for today"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('SureBetBets')
        today = datetime.now().strftime('%Y-%m-%d')
        
        resp = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
        )
        
        items = resp.get('Items', [])
        ui_picks = [i for i in items if i.get('show_in_ui') and i.get('recommended_bet')]
        
        if not ui_picks:
            return False, "No recommended picks (85+) found for today"
        
        # Check for upcoming races
        now_utc = datetime.utcnow()
        upcoming = []
        for pick in ui_picks:
            race_time_str = pick.get('race_time', '')
            try:
                race_dt = datetime.fromisoformat(race_time_str.replace('Z', ''))
                if race_dt > now_utc:
                    upcoming.append(pick)
            except:
                pass
        
        return True, f"{len(ui_picks)} recommended picks ({len(upcoming)} upcoming)"
    except Exception as e:
        return False, f"Picks check error: {str(e)}"

def check_key_files():
    """Verify critical workflow files exist"""
    required_files = [
        'comprehensive_workflow.py',
        'comprehensive_pick_logic.py',
        'enforce_comprehensive_analysis.py',
        'weather_going_inference.py',
        'intraday_learning_system.py',
        'race_monitor.py'
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        return False, f"Missing files: {', '.join(missing)}"
    
    return True, f"All {len(required_files)} critical files present"

def check_going_system():
    """Verify going inference is working"""
    try:
        from weather_going_inference import check_all_tracks_going
        
        # Test with one track
        result = check_all_tracks_going(['Kempton'], use_official=False)
        
        if result and 'Kempton' in result:
            going = result['Kempton']['going']
            return True, f"Going system working (Kempton: {going})"
        else:
            return False, "Going system returned no data"
    except Exception as e:
        return False, f"Going system error: {str(e)}"

def run_health_check():
    """Run all health checks"""
    print("\n" + "="*80)
    print("SYSTEM HEALTH MONITOR")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    checks = [
        ("Database Connection", check_database_connection),
        ("Race Data", check_race_data),
        ("Today's Picks", check_todays_picks),
        ("Critical Files", check_key_files),
        ("Going System", check_going_system)
    ]
    
    all_passed = True
    results = []
    
    for check_name, check_func in checks:
        try:
            status, message = check_func()
            results.append((check_name, status, message))
            
            icon = "✓" if status else "✗"
            color = "green" if status else "red"
            
            print(f"{icon} {check_name:.<50} {message}")
            
            if not status:
                all_passed = False
        except Exception as e:
            print(f"✗ {check_name:.<50} EXCEPTION: {str(e)}")
            all_passed = False
            results.append((check_name, False, f"Exception: {str(e)}"))
    
    print("\n" + "="*80)
    if all_passed:
        print("STATUS: ✓ ALL SYSTEMS OPERATIONAL")
        print("="*80 + "\n")
        print("Workflow is ready:")
        print("  • Database accessible")
        print("  • Fresh race data loaded")
        print("  • Recommended picks generated")
        print("  • All critical files present")
        print("  • Going system functional")
    else:
        print("STATUS: ⚠️  ISSUES DETECTED")
        print("="*80 + "\n")
        print("Action required:")
        for name, status, message in results:
            if not status:
                print(f"  ✗ {name}: {message}")
    
    print("\n" + "="*80 + "\n")
    
    return all_passed

if __name__ == "__main__":
    run_health_check()

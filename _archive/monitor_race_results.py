"""
Monitor for race results
Checks every 2 minutes if results have come in
Checks both database and Betfair API
"""
import boto3
import time
import subprocess
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def check_betfair_results():
    """Try to fetch latest results from Betfair"""
    try:
        print("  Checking Betfair for results...")
        result = subprocess.run(
            ['python', 'betfair_results_fetcher_v2.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Check if any results were updated
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Updated' in line or 'Result:' in line:
                    print(f"  Betfair: {line.strip()}")
            return True
        else:
            return False
    except Exception as e:
        print(f"  Betfair check error: {e}")
        return False

def check_race_results(course, race_time):
    """Check if a specific race has results"""
    response = table.scan()
    items = response.get('Items', [])
    
    race_horses = [item for item in items if course in item.get('course', '') and race_time in item.get('race_time', '')]
    
    if not race_horses:
        return None, None
    
    # Check for winner
    winner = None
    for horse in race_horses:
        if horse.get('outcome') == 'WON':
            winner = horse
            break
    
    # Count pending/completed
    pending = sum(1 for h in race_horses if h.get('outcome') in [None, '', 'PENDING'])
    completed = len(race_horses) - pending
    
    return winner, (completed, len(race_horses))

def monitor_until(target_time, course='Kempton', race_time='12:50'):
    """Monitor until target time, checking for results"""
    print(f"\nMonitoring {race_time} {course} for results...")
    print(f"Will check until {target_time}")
    print("="*60)
    
    last_status = None
    check_count = 0
    
    while datetime.now().strftime('%H:%M') < target_time:
        current_time = datetime.now().strftime('%H:%M:%S')
        check_count += 1
        
        # Every other check (4 min), try Betfair
        if check_count % 2 == 1:
            print(f"\n[{current_time}] Check #{check_count}")
            check_betfair_results()
        
        winner, stats = check_race_results(course, race_time)
        
        if winner:
            print(f"\n[{current_time}] ✓ RESULT IN!")
            print(f"Winner: {winner.get('horse')} @{winner.get('odds')}")
            print(f"My tip score: {float(winner.get('combined_confidence', 0)):.1f}/100")
            
            # Check if it was my tip
            response = table.scan()
            items = response.get('Items', [])
            race_horses = [item for item in items if course in item.get('course', '') and race_time in item.get('race_time', '')]
            sorted_horses = sorted(race_horses, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True)
            
            if sorted_horses and sorted_horses[0].get('horse') == winner.get('horse'):
                print("🎉 MY TIP WON!")
            else:
                if sorted_horses:
                    my_tip = sorted_horses[0]
                    print(f"My tip was: {my_tip.get('horse')} ({float(my_tip.get('combined_confidence', 0)):.1f}/100)")
            
            return True
        
        if stats:
            status_msg = f"[{current_time}] {stats[0]}/{stats[1]} horses have results"
            if status_msg != last_status:
                print(status_msg)
                last_status = status_msg
        else:
            status_msg = f"[{current_time}] Waiting for results..."
            if status_msg != last_status:
                print(status_msg)
                last_status = status_msg
        
        time.sleep(120)  # Check every 2 minutes
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Target time {target_time} reached")
    print("No results captured yet")
    return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) >= 2:
        target_time = sys.argv[1]  # e.g., "13:30"
    else:
        target_time = "13:30"
    
    course = sys.argv[2] if len(sys.argv) >= 3 else "Kempton"
    race_time = sys.argv[3] if len(sys.argv) >= 4 else "12:50"
    
    try:
        monitor_until(target_time, course, race_time)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")

"""
Continuous monitoring: Fetch results every 30 minutes and update learning database
Run this in the background throughout the day
"""

import time
import subprocess
import boto3
from datetime import datetime

def check_and_update_results():
    """Fetch latest results and update database"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking for new results...")
    
    try:
        # Fetch results from Betfair
        result = subprocess.run(
            ['python', 'betfair_results_fetcher_v2.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Check how many completed
            dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
            table = dynamodb.Table('SureBetBets')
            
            today = '2026-02-05'
            response = table.query(
                KeyConditionExpression='bet_date = :date',
                ExpressionAttributeValues={':date': today}
            )
            
            items = response.get('Items', [])
            completed = sum(1 for item in items if item.get('outcome') in ['WON', 'PLACED', 'LOST'])
            total = len(items)
            
            print(f"  ✓ {completed}/{total} races completed")
            
            # If all done, run full analysis
            if completed == total and total > 0:
                print("  ✓ ALL RACES COMPLETE - Running full analysis...")
                subprocess.run(['python', 'analyze_todays_learning.py'])
                return True  # Signal to stop monitoring
                
        else:
            print(f"  ⚠ Error fetching results")
            
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    return False  # Continue monitoring

print("="*70)
print("CONTINUOUS RESULTS MONITORING")
print("="*70)
print("Will check for results every 30 minutes")
print("Press Ctrl+C to stop")
print("="*70)
print()

try:
    while True:
        all_complete = check_and_update_results()
        
        if all_complete:
            print("\n✓ All races complete - monitoring stopped")
            break
        
        # Wait 30 minutes
        print(f"  Next check in 30 minutes...")
        time.sleep(1800)  # 30 minutes
        
except KeyboardInterrupt:
    print("\n\n✓ Monitoring stopped by user")

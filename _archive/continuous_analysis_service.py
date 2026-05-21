"""
Continuous Race Analysis Service
Runs every 30 minutes from 7 AM to 11 PM to analyze new races and generate UI picks
"""

import time
import subprocess
import schedule
from datetime import datetime

def run_analysis():
    """Run the complete daily analysis"""
    now = datetime.now()
    
    # Only run between 7 AM and 11 PM
    if now.hour < 7 or now.hour >= 23:
        print(f"[{now.strftime('%H:%M:%S')}] Outside operating hours (7 AM - 11 PM). Skipping.")
        return
    
    print("=" * 70)
    print(f"CONTINUOUS ANALYSIS - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # Run complete daily analysis
        result = subprocess.run(
            ['python', 'complete_daily_analysis.py'],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max
        )
        
        if result.returncode == 0:
            # Show summary from output
            lines = result.stdout.split('\n')
            
            # Find UI picks line
            for line in lines:
                if 'UI picks' in line or 'HIGH-CONFIDENCE' in line:
                    print(f"  {line}")
            
            print(f"  ✓ Analysis complete at {datetime.now().strftime('%H:%M:%S')}")
        else:
            print(f"  ⚠ Analysis had errors (exit code {result.returncode})")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
    
    except subprocess.TimeoutExpired:
        print(f"  ⚠ Analysis timed out after 10 minutes")
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    print()

# Schedule the task
schedule.every(30).minutes.do(run_analysis)

print("=" * 70)
print("CONTINUOUS RACE ANALYSIS SERVICE")
print("=" * 70)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print("Schedule: Every 30 minutes from 7:00 AM to 11:00 PM")
print()
print("This service will:")
print("  1. Fetch latest races from Betfair")
print("  2. Analyze all horses with comprehensive scoring")
print("  3. Generate UI picks for 85+ confidence")
print("  4. Update database throughout the day")
print()
print("Press Ctrl+C to stop")
print("=" * 70)
print()

# Run immediately on startup
print("Running initial analysis...")
run_analysis()

# Run scheduled tasks
try:
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
except KeyboardInterrupt:
    print("\n\n✓ Service stopped by user")

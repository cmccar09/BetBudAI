import boto3
from datetime import datetime, timedelta
import json

# Check what's happening with today's workflow
db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

print("\n" + "="*80)
print("INVESTIGATING: Why only 1 pick today?")
print("="*80)

# Get today's picks vs yesterday's
today = datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

for date_str, label in [(today, "TODAY"), (yesterday, "YESTERDAY")]:
    response = table.scan(
        FilterExpression='contains(#dt, :date)',
        ExpressionAttributeNames={'#dt': 'date'},
        ExpressionAttributeValues={':date': date_str}
    )
    
    items = response.get('Items', [])
    
    print(f"\n{label} ({date_str}): {len(items)} picks")
    
    if items:
        # Analyze why picks were made/rejected
        for item in sorted(items, key=lambda x: x.get('race_time', '')):
            print(f"\n  {item.get('race_time', '?')[:16]} - {item.get('course', '?')}")
            print(f"    Horse: {item.get('horse', '?')}")
            print(f"    Odds: {item.get('odds', '?')}")
            print(f"    Confidence: {item.get('confidence', '?')}")
            print(f"    Value Score: {item.get('all_horses_analyzed', {}).get('value_analysis', [{}])[0].get('value_score', 'N/A') if 'all_horses_analyzed' in item else 'N/A'}")

print("\n" + "="*80)
print("POSSIBLE REASONS FOR LOW PICK COUNT:")
print("="*80)

reasons = """
1. ⏰ TIME FILTERS:
   - Races must be 30+ minutes away (min_lead_time)
   - Races must be within 24 hours (max_future_hours)
   → Saturday might have already had morning races finish

2. 📊 STRICT CRITERIA (from prompt.txt):
   - Odds must be 3.0-9.0 (avoiding favorites <3.0)
   - Must be recent winner in last 3 races
   - Avoiding: favorites (losing 89% ROI), mid-price (losing 95% ROI)
   
3. 🏇 RACE AVAILABILITY:
   - Saturday = lighter racing schedule than weekdays
   - Many races might be outside the 3-9 odds sweet spot
   
4. 🎯 QUALITY OVER QUANTITY:
   - System only picks 1 horse per race (best quality score)
   - Might be filtering out races with no clear value picks

5. 📉 RECENT PERFORMANCE ADJUSTMENTS:
   - Win rate 0% recently → system being VERY cautious
   - High calibration error (21%) → tightening criteria
"""

print(reasons)

# Check if there are races today that we haven't picked
print("\n" + "="*80)
print("SOLUTION: Check CSV output files for filtered picks")
print("="*80)

import os
from pathlib import Path

history_dir = Path('history')
today_slug = datetime.now().strftime("%Y%m%d")

csv_files = list(history_dir.glob(f"selections_{today_slug}*.csv"))

if csv_files:
    print(f"\nFound {len(csv_files)} selection CSV files for today")
    latest = max(csv_files, key=lambda p: p.stat().st_mtime)
    print(f"Latest: {latest}")
    
    # Read and show what was filtered out
    import csv
    with open(latest, 'r') as f:
        reader = csv.DictReader(f)
        all_selections = list(reader)
    
    print(f"\nTotal selections in CSV: {len(all_selections)}")
    
    if len(all_selections) > 1:
        print("\n⚠️ MULTIPLE PICKS WERE GENERATED BUT FILTERED OUT!")
        print("\nAll generated picks:")
        for sel in all_selections[:10]:  # Show first 10
            print(f"  - {sel.get('runner_name', '?')} @ {sel.get('venue', '?')} ({sel.get('start_time_dublin', '?')[:16]})")
            print(f"    Odds: {sel.get('odds', '?')}, p_win: {sel.get('p_win', '?')}")
        
        if len(all_selections) > 10:
            print(f"  ... and {len(all_selections) - 10} more")
else:
    print("\n❌ No selection CSV files found for today")
    print("The workflow might not have run yet or failed")

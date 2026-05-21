"""
Gather Complete Race Data for Phase 1 Analysis - May 20, 2026
==============================================================
Checks data completeness for Phase 1 signal generation
"""

import boto3
import json
from datetime import datetime
from collections import defaultdict

print("="*80)
print("GATHERING RACE DATA FOR PHASE 1 ANALYSIS")
print("="*80)
print(f"Date: 2026-05-20")
print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
print()

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Phase 1 Requirements:
# 1. form_runs with race comments (for run style classification)
# 2. Previous jockey data (for upgrade detection)
# 3. Current jockey names
# 4. Race details (venue, time, distance)

print("[1] CHECKING DYNAMODB FOR TODAY'S DATA")
print("-" * 80)

# Try different query strategies
target_date = '2026-05-20'

# Strategy 1: Scan for items with today's date in bet_date field
try:
    response = table.scan(
        FilterExpression='bet_date = :date',
        ExpressionAttributeValues={':date': target_date},
        Limit=100
    )
    today_items = response.get('Items', [])
    print(f"  Items with bet_date={target_date}: {len(today_items)}")

    if today_items:
        print(f"\n  Sample item types:")
        for item in today_items[:3]:
            print(f"    - bet_id: {item.get('bet_id', 'N/A')[:60]}")
            print(f"      keys: {list(item.keys())[:8]}")
except Exception as e:
    print(f"  [ERROR] {e}")
    today_items = []

# Strategy 2: Check for CONFIG/WEIGHTS items that show system state
try:
    config_response = table.get_item(
        Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'}
    )
    if 'Item' in config_response:
        weights_item = config_response['Item']
        print(f"\n  Weights Configuration Found:")
        print(f"    Version: {weights_item.get('version', 'N/A')}")
        print(f"    Phase: {weights_item.get('phase', 'N/A')}")
        print(f"    Updated: {weights_item.get('updated_at', 'N/A')}")

        # Check if Phase 1 signals are in weights
        weights = weights_item.get('weights', {})
        phase1_signals = ['pace_match', 'jockey_upgrade']
        has_phase1 = any(sig in weights for sig in phase1_signals)
        print(f"    Phase 1 in weights: {'YES' if has_phase1 else 'NO'}")
except Exception as e:
    print(f"  [WARNING] Could not check weights: {e}")

print()
print("[2] CHECKING FOR CACHED RACE DATA")
print("-" * 80)

# Look for race data stored with different key patterns
race_data_found = False
race_items = []

# Pattern 1: Individual race items
for item in today_items:
    # Check if this item has race/horse data
    if any(key in item for key in ['horse_name', 'name', 'runners', 'all_horses']):
        race_items.append(item)

if race_items:
    print(f"  Found {len(race_items)} items with race/horse data")
    race_data_found = True

    # Analyze data completeness
    horses_with_form = 0
    horses_with_jockey = 0
    horses_with_previous_jockey = 0
    horses_with_comments = 0

    for item in race_items:
        # Check for form_runs
        if 'form_runs' in item:
            form_runs = item['form_runs']
            if form_runs and len(form_runs) > 0:
                horses_with_form += 1
                # Check for race comments
                for run in form_runs[:3]:
                    if run.get('race_comment') or run.get('comment'):
                        horses_with_comments += 1
                        break

        # Check for current jockey
        if item.get('jockey') or item.get('jockey_name'):
            horses_with_jockey += 1

        # Check for previous jockey (in form_runs)
        if 'form_runs' in item:
            form_runs = item['form_runs']
            if form_runs and len(form_runs) > 0:
                for run in form_runs[:3]:
                    if run.get('jockey'):
                        horses_with_previous_jockey += 1
                        break

    print(f"\n  Data Completeness:")
    print(f"    Horses with form_runs: {horses_with_form}/{len(race_items)} ({horses_with_form*100//max(len(race_items),1)}%)")
    print(f"    Horses with current jockey: {horses_with_jockey}/{len(race_items)} ({horses_with_jockey*100//max(len(race_items),1)}%)")
    print(f"    Horses with previous jockey: {horses_with_previous_jockey}/{len(race_items)} ({horses_with_previous_jockey*100//max(len(race_items),1)}%)")
    print(f"    Horses with race comments: {horses_with_comments}/{len(race_items)} ({horses_with_comments*100//max(len(race_items),1)}%)")

    # Sample one item to show structure
    if race_items:
        print(f"\n  Sample Race Item Structure:")
        sample = race_items[0]
        print(f"    Horse: {sample.get('horse_name', sample.get('name', 'N/A'))}")
        print(f"    Jockey: {sample.get('jockey', sample.get('jockey_name', 'N/A'))}")
        print(f"    Form runs: {len(sample.get('form_runs', []))} runs")
        if sample.get('form_runs'):
            first_run = sample['form_runs'][0]
            print(f"      First run has comment: {'YES' if first_run.get('race_comment') or first_run.get('comment') else 'NO'}")
            print(f"      First run has jockey: {'YES' if first_run.get('jockey') else 'NO'}")
else:
    print(f"  No race data found in today's items")

print()
print("[3] CHECKING BETFAIR FETCH STATUS")
print("-" * 80)

# Check if Betfair fetch has run today
# Look for system status or pipeline execution records
try:
    # Check for pipeline execution record
    response = table.scan(
        FilterExpression='contains(bet_id, :pipeline) AND bet_date = :date',
        ExpressionAttributeValues={
            ':pipeline': 'pipeline',
            ':date': target_date
        },
        Limit=10
    )
    pipeline_items = response.get('Items', [])

    if pipeline_items:
        print(f"  Found {len(pipeline_items)} pipeline execution records")
        for item in pipeline_items[:3]:
            print(f"    - {item.get('bet_id')}: {item.get('status', 'N/A')}")
    else:
        print(f"  No pipeline execution records found for today")
        print(f"  (This is normal if pipeline hasn't run yet)")
except Exception as e:
    print(f"  [INFO] Could not check pipeline records: {e}")

print()
print("[4] PHASE 1 READINESS ASSESSMENT")
print("-" * 80)

# Determine if we can run Phase 1 analysis
phase1_ready = False
missing_requirements = []

if not race_data_found:
    missing_requirements.append("No race data available for today")
elif len(race_items) == 0:
    missing_requirements.append("No horses found in race data")
else:
    # Check data quality
    if horses_with_form < len(race_items) * 0.5:
        missing_requirements.append(f"Insufficient form data ({horses_with_form}/{len(race_items)} horses)")

    if horses_with_jockey < len(race_items) * 0.8:
        missing_requirements.append(f"Missing jockey data ({horses_with_jockey}/{len(race_items)} horses)")

    if horses_with_comments < len(race_items) * 0.3:
        missing_requirements.append(f"Limited race comments for run style ({horses_with_comments}/{len(race_items)} horses)")

    # If no major issues, we're ready
    if len(missing_requirements) == 0:
        phase1_ready = True

if phase1_ready:
    print(f"  ✅ READY FOR PHASE 1 ANALYSIS")
    print(f"     {len(race_items)} horses with sufficient data")
    print(f"     Data completeness: {min(horses_with_form, horses_with_jockey)*100//max(len(race_items),1)}%")
else:
    print(f"  ❌ NOT READY FOR PHASE 1 ANALYSIS")
    print(f"\n  Missing requirements:")
    for req in missing_requirements:
        print(f"    - {req}")

print()
print("[5] RACE AVAILABILITY SUMMARY")
print("-" * 80)

# Count distinct races
races_by_venue = defaultdict(list)
for item in race_items:
    venue = item.get('course', item.get('venue', 'Unknown'))
    race_time = item.get('race_time', item.get('time', 'Unknown'))
    horse = item.get('horse_name', item.get('name', 'Unknown'))
    races_by_venue[venue].append((race_time, horse))

if races_by_venue:
    print(f"  Races Available: {len(races_by_venue)} venues")
    print()
    for venue, horses in sorted(races_by_venue.items()):
        # Group by time
        by_time = defaultdict(list)
        for time, horse in horses:
            by_time[time].append(horse)
        print(f"  {venue}:")
        for time in sorted(by_time.keys()):
            print(f"    {time}: {len(by_time[time])} horses")
else:
    print(f"  No races found with venue/time information")

print()
print("="*80)
print("SUMMARY")
print("="*80)

if phase1_ready:
    print(f"STATUS: ✅ Can generate Phase 1 picks right now")
    print()
    print(f"Available Data:")
    print(f"  - Races: {len(races_by_venue)} venues")
    print(f"  - Horses: {len(race_items)} total")
    print(f"  - Data Completeness: {min(horses_with_form, horses_with_jockey)*100//max(len(race_items),1)}%")
    print()
    print(f"Phase 1 Signals Ready:")
    print(f"  - Run Style Classification: {horses_with_comments}/{len(race_items)} horses")
    print(f"  - Jockey Upgrade Detection: {horses_with_previous_jockey}/{len(race_items)} horses")
else:
    print(f"STATUS: ❌ Cannot generate Phase 1 picks yet")
    print()
    print(f"Reason:")
    for req in missing_requirements[:3]:
        print(f"  - {req}")
    print()
    print(f"Action Required:")
    if not race_data_found:
        print(f"  1. Run Betfair fetch to get today's race data")
        print(f"  2. Run morning pipeline to enrich with form data")
    else:
        print(f"  1. Re-run morning pipeline with force flag")
        print(f"  2. Check data enrichment pipeline logs")

print()
print(f"Report generated: {datetime.utcnow().isoformat()}Z")
print("="*80)

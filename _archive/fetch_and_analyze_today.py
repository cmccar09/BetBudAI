"""
Fetch and analyze all races for today
"""

import subprocess
import sys
from datetime import datetime

print("="*70)
print("FETCH & ANALYZE TODAY'S RACES")
print("="*70)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Expected courses today
courses_today = [
    "Doncaster",
    "Huntingdon", 
    "Lingfield",
    "Southwell",
    "Thurles"
]

print("Expected courses:")
for course in courses_today:
    print(f"  - {course}")
print()

# Step 1: Fetch today's races from Betfair
print("STEP 1: Fetching races from Betfair...")
print("-" * 70)
try:
    result = subprocess.run(
        ['python', 'betfair_odds_fetcher.py'],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode == 0:
        print("✓ Betfair fetch completed")
        if result.stdout:
            # Show last 20 lines
            lines = result.stdout.strip().split('\n')
            for line in lines[-20:]:
                print(f"  {line}")
    else:
        print(f"⚠ Betfair fetch had errors (exit code {result.returncode})")
        if result.stderr:
            print(result.stderr[:500])
except subprocess.TimeoutExpired:
    print("⚠ Betfair fetch timed out after 120s")
except Exception as e:
    print(f"⚠ Error: {e}")

print()

# Step 2: Analyze with comprehensive pick logic
print("STEP 2: Running comprehensive analysis...")
print("-" * 70)
try:
    result = subprocess.run(
        ['python', 'comprehensive_pick_logic.py'],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode == 0:
        print("✓ Analysis completed")
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[-30:]:
                print(f"  {line}")
    else:
        print(f"⚠ Analysis had errors (exit code {result.returncode})")
        if result.stderr:
            print(result.stderr[:500])
except subprocess.TimeoutExpired:
    print("⚠ Analysis timed out after 300s")
except Exception as e:
    print(f"⚠ Error: {e}")

print()

# Step 3: Check what we got in the database
print("STEP 3: Checking database...")
print("-" * 70)
try:
    check_code = """
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response.get('Items', [])

print(f'Total horses analyzed: {len(items)}')

if items:
    courses = {}
    for item in items:
        course = item.get('course', 'Unknown')
        if course not in courses:
            courses[course] = []
        courses[course].append(item)
    
    print()
    print('By course:')
    for course in sorted(courses.keys()):
        print(f'  {course:<20} {len(courses[course])} horses')
    
    ui_picks = [item for item in items if item.get('show_in_ui') == True]
    
    print()
    if ui_picks:
        print(f'✓ UI PICKS: {len(ui_picks)}')
        print()
        for pick in sorted(ui_picks, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True):
            score = float(pick.get('combined_confidence', 0))
            horse = pick.get('horse', 'Unknown')
            course = pick.get('course', 'Unknown')
            odds = pick.get('odds', 'N/A')
            race_time = pick.get('race_time', '')
            time_part = race_time.split('T')[1][:5] if 'T' in race_time else ''
            print(f'  {score:5.1f}/100  {horse:<25} @{odds:<6} {course} {time_part}')
    else:
        print('⚠ No UI picks (need 85+ combined_confidence)')
else:
    print('⚠ No data in database for today')
"""
    
    result = subprocess.run(
        ['python', '-c', check_code],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(result.stdout)
    
except Exception as e:
    print(f"⚠ Error checking database: {e}")

print()
print("="*70)
print("COMPLETE")
print("="*70)

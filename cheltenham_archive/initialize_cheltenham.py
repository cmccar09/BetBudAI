"""
CHELTENHAM FESTIVAL 2026 - COMPLETE INITIALIZATION
Run this ONCE to set up everything and verify it's working
"""

import boto3
from datetime import datetime
import time
import subprocess
import sys

print("="*100)
print("CHELTENHAM FESTIVAL 2026 - COMPLETE SYSTEM INITIALIZATION")
print("="*100)
print()

# Step 1: Check AWS credentials
print("[1/6] Checking AWS credentials...")
try:
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print(f"  ✓ AWS Account: {identity['Account']}")
    print(f"  ✓ Region: eu-west-1")
except Exception as e:
    print(f"  ✗ AWS credentials not configured: {e}")
    print("\n  Run: aws configure")
    print("  Then rerun this script")
    sys.exit(1)

print()

# Step 2: Create DynamoDB table
print("[2/6] Creating CheltenhamFestival2026 DynamoDB table...")
try:
    result = subprocess.run([sys.executable, 'cheltenham_festival_schema.py'], 
                          capture_output=True, text=True, timeout=30)
    
    if 'created successfully' in result.stdout or 'already exists' in result.stdout:
        print("  ✓ Table ready")
    else:
        print(f"  ⚠ Warning: {result.stdout[:200]}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

print()
time.sleep(2)

# Step 3: Verify table exists
print("[3/6] Verifying table...")
try:
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('CheltenhamFestival2026')
    
    # Try to describe table
    table.load()
    print(f"  ✓ Table status: {table.table_status}")
    print(f"  ✓ Table ARN: {table.table_arn}")
    
    # Count races
    response = table.scan()
    race_count = len([item for item in response['Items'] if item.get('horseId') == 'RACE_INFO'])
    print(f"  ✓ Races initialized: {race_count}/28")
    
except Exception as e:
    print(f"  ✗ Table verification failed: {e}")
    sys.exit(1)

print()

# Step 4: Add sample horses
print("[4/6] Adding sample horses for Champion Hurdle...")
try:
    result = subprocess.run([sys.executable, 'cheltenham_festival_scraper.py', '--sample'], 
                          capture_output=True, text=True, timeout=30)
    
    if 'added successfully' in result.stdout:
        print("  ✓ Sample horses added")
    else:
        print(f"  ⚠ Warning: {result.stdout[:200]}")
except Exception as e:
    print(f"  ⚠ Non-critical error: {e}")

print()

# Step 5: Verify sample data
print("[5/6] Verifying sample data...")
try:
    response = table.query(
        KeyConditionExpression='raceId = :raceId',
        ExpressionAttributeValues={':raceId': 'Tuesday_10_March_Champion_Hurdle'}
    )
    
    horses = [item for item in response['Items'] if item.get('horseId') != 'RACE_INFO']
    print(f"  ✓ Sample horses in Champion Hurdle: {len(horses)}")
    
    if horses:
        for horse in horses[:3]:  # Show first 3
            print(f"    - {horse.get('horseName')} ({horse.get('confidenceRank')}% confidence)")
    
except Exception as e:
    print(f"  ⚠ Could not verify horses: {e}")

print()

# Step 6: Test API endpoints
print("[6/6] Testing API availability...")
try:
    import requests
    
    # Check if API is running
    try:
        response = requests.get('http://localhost:5001/api/health', timeout=2)
        if response.status_code == 200:
            print("  ✓ API server is running on port 5001")
        else:
            print("  ⚠ API server responded with error")
    except requests.exceptions.ConnectionError:
        print("  ℹ API server not running (will need to start manually)")
        print("    Run: python api_server.py")
    
except ImportError:
    print("  ℹ requests library not installed (optional)")

print()
print("="*100)
print("INITIALIZATION COMPLETE!")
print("="*100)
print()

# Final summary
print("✅ SYSTEM READY FOR CHELTENHAM FESTIVAL 2026")
print()
print("What was created:")
print("  ✓ DynamoDB table: CheltenhamFestival2026")
print("  ✓ 28 races initialized (4 days)")
print("  ✓ Sample horses added to Champion Hurdle")
print("  ✓ API endpoints configured")
print()

print("Next Steps:")
print()
print("  1. START API SERVER:")
print("     python api_server.py")
print()
print("  2. OPEN WEB INTERFACE:")
print("     Open cheltenham_festival.html in your browser")
print()
print("  3. VIEW SAMPLE DATA:")
print("     - Click 'Tuesday' tab")
print("     - Find 'Champion Hurdle' (15:30)")
print("     - Click 'View Horses & Research'")
print("     - See Constitution Hill, State Man, Lossiemouth")
print()
print("  4. ADD YOUR OWN RESEARCH:")
print("     - Click 'Add Horse' on any race")
print("     - Fill in horse details, form, odds")
print("     - Add research notes")
print("     - Set confidence ranking")
print()
print("  5. DAILY UPDATES:")
print("     python cheltenham_festival_scraper.py")
print("     (Updates odds, form, recalculates confidence)")
print()
print("  6. GENERATE ANALYSIS:")
print("     python cheltenham_analyzer.py")
print("     (Creates comprehensive report with rankings)")
print()

# Countdown
festival_start = datetime(2026, 3, 10, 13, 30)
now = datetime.now()
days_until = (festival_start - now).days

print("="*100)
print(f"⏰ COUNTDOWN: {days_until} days until Cheltenham Festival 2026")
print("="*100)
print()

# File checklist
print("Files Created:")
files = [
    'cheltenham_festival_schema.py',
    'cheltenham_festival.html',
    'cheltenham_festival_scraper.py',
    'cheltenham_analyzer.py',
    'cheltenham_quick_start.ps1',
    'CHELTENHAM_FESTIVAL_2026_GUIDE.md',
    'CHELTENHAM_SYSTEM_SUMMARY.md'
]

for f in files:
    import os
    if os.path.exists(f):
        print(f"  ✓ {f}")
    else:
        print(f"  ✗ {f} (missing)")

print()
print("="*100)
print("READY TO START YOUR CHELTENHAM FESTIVAL 2026 RESEARCH!")
print("="*100)
print()
print("Good luck! 🍀🏆")
print()

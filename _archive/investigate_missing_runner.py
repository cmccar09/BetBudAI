"""
Investigate Missing Runner - Dunsy Rock
Check data capture completeness
"""
import json
import boto3
from datetime import datetime

print("\n" + "="*80)
print("INVESTIGATING MISSING RUNNER: Dunsy Rock @ Fairyhouse 13:15")
print("="*80 + "\n")

# Check response_horses.json
try:
    with open('response_horses.json', 'r') as f:
        data = json.load(f)
    
    fairyhouse_races = [
        r for r in data.get('races', [])
        if 'Fairyhouse' in r.get('venue', '') and '13:' in r.get('start_time', '')
    ]
    
    if fairyhouse_races:
        race = fairyhouse_races[0]
        print(f"RACE DATA CAPTURED:")
        print(f"  Venue: {race.get('venue')}")
        print(f"  Time: {race.get('start_time')}")
        print(f"  Market: {race.get('market_name')}")
        print(f"  Market ID: {race.get('marketId')}")
        print(f"  Runners Captured: {len(race.get('runners', []))}")
        
        print(f"\n{'-'*80}")
        print("HORSES IN OUR DATA:")
        print(f"{'-'*80}\n")
        
        runners = sorted(race.get('runners', []), key=lambda x: x.get('odds', 999))
        
        for i, runner in enumerate(runners, 1):
            name = runner.get('name', 'Unknown')
            odds = runner.get('odds', 0)
            form = runner.get('form', '')
            status = runner.get('status', 'ACTIVE')
            
            print(f"{i:2d}. {name:30s} @ {odds:6.1f}  Form: {form:10s}  Status: {status}")
        
        # Check if Dunsy Rock variants exist
        print(f"\n{'-'*80}")
        print("SEARCHING FOR WINNER VARIANTS:")
        print(f"{'-'*80}\n")
        
        search_terms = ['Dunsy', 'Rock', 'dunsy', 'rock']
        found = False
        
        for runner in runners:
            name = runner.get('name', '')
            for term in search_terms:
                if term in name:
                    print(f"✓ FOUND: {name} contains '{term}'")
                    found = True
                    break
        
        if not found:
            print("❌ NO MATCH FOUND - Dunsy Rock not in our data")
            print("\nPOSSIBLE CAUSES:")
            print("1. Late declaration (horse added after we fetched data)")
            print("2. Betfair API filtering issue")
            print("3. Horse name mismatch/spelling difference")
            print("4. Market not fully loaded when we fetched")
            print("5. Horse status was REMOVED/NON_RUNNER initially")
        
        # Check for non-runners
        print(f"\n{'-'*80}")
        print("NON-RUNNERS CHECK:")
        print(f"{'-'*80}\n")
        
        non_runners = [r for r in runners if r.get('status') != 'ACTIVE']
        if non_runners:
            print(f"Found {len(non_runners)} non-active runners:")
            for nr in non_runners:
                print(f"  - {nr.get('name')} (Status: {nr.get('status')})")
        else:
            print("No non-runners in our data")
        
        # Expected vs Actual
        print(f"\n{'-'*80}")
        print("DATA COMPLETENESS:")
        print(f"{'-'*80}\n")
        
        expected_runners = 16  # From user's result data (15 ran + 1 non-runner)
        actual_runners = len(runners)
        missing = expected_runners - actual_runners
        
        print(f"Expected Runners: {expected_runners}")
        print(f"Captured Runners: {actual_runners}")
        print(f"Missing Runners: {missing}")
        
        if missing > 0:
            print(f"\n⚠️ DATA QUALITY ISSUE: {missing} runner(s) not captured")
            print(f"   This includes the WINNER (Dunsy Rock)")
            print(f"\n   RECOMMENDATION: Add data completeness check to workflow")
            print(f"   - Fetch runner count from market metadata")
            print(f"   - Compare with captured runners")
            print(f"   - Retry fetch if mismatch detected")
            print(f"   - Log missing runners for analysis")
        
    else:
        print("❌ Race not found in response_horses.json")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Check database to see what was saved
print(f"\n{'='*80}")
print("DATABASE CHECK:")
print(f"{'='*80}\n")

try:
    db = boto3.resource('dynamodb', region_name='eu-west-1')
    table = db.Table('SureBetBets')
    
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        ExpressionAttributeValues={':date': '2026-02-03'}
    )
    
    fairyhouse_db = [
        p for p in response['Items']
        if 'Fairyhouse' in p.get('course', '') and '13:' in p.get('race_time', '')
    ]
    
    print(f"Fairyhouse 13:xx entries in database: {len(fairyhouse_db)}")
    
    # Check if any match winner
    winner_found = False
    for entry in fairyhouse_db:
        if 'Dunsy' in entry.get('horse', '') or 'Rock' in entry.get('horse', ''):
            winner_found = True
            print(f"\n✓ Winner found in database:")
            print(f"  {entry.get('horse')} @ {entry.get('odds')}")
            break
    
    if not winner_found:
        print("\n❌ Winner NOT in database (expected - not in source data)")
        print("   Data capture issue prevented winner from being analyzed")

except Exception as e:
    print(f"❌ Database error: {e}")

print(f"\n{'='*80}")
print("LEARNING OUTCOME:")
print(f"{'='*80}\n")
print("✓ Weather/Going prediction: CORRECT (Soft ground)")
print("❌ Data completeness: FAILED (Missing winner)")
print("\nACTION REQUIRED:")
print("1. Add runner count validation to betfair_odds_fetcher.py")
print("2. Implement retry logic if runner count mismatch")
print("3. Log missing runners to data_quality_issues.json")
print("4. Background learning workflow should detect and flag these issues")

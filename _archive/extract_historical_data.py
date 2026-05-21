"""
Step 1: Extract Historical Data for Backtesting
Gather all completed races from database with outcomes
"""
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
from decimal import Decimal
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*80)
print("EXTRACTING HISTORICAL DATA FOR BACKTESTING")
print("="*80)
print()

# Scan for all dates we have data for
print("Scanning database for historical races...")
print()

all_races = []
dates_checked = []

# Check last 60 days
for days_ago in range(60):
    check_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    
    try:
        response = table.query(
            KeyConditionExpression=Key('bet_date').eq(check_date)
        )
        
        items = response.get('Items', [])
        
        if items:
            # Filter for items with outcomes
            completed = [item for item in items 
                        if item.get('outcome') and 
                        str(item.get('outcome', '')).upper() in ['WON', 'WIN', 'LOST', 'LOSS']]
            
            if completed:
                dates_checked.append(check_date)
                all_races.extend(completed)
                print(f"  {check_date}: {len(completed)} completed races")
    
    except Exception as e:
        pass

print()
print("="*80)
print("DATA COLLECTION SUMMARY")
print("="*80)
print(f"Total days with data: {len(dates_checked)}")
print(f"Total completed races: {len(all_races)}")
print()

if len(all_races) < 100:
    print("WARNING: Less than 100 races found")
    print("Need 500+ races for proper backtesting")
    print()
    print("Options:")
    print("1. Wait and collect more data over time")
    print("2. Import historical data from external source")
    print("3. Use Racing Post/Betfair historical API")
    print()
else:
    print(f"SUCCESS: Found {len(all_races)} completed races")
    print()

# Analyze what data we have
print("="*80)
print("DATA QUALITY ANALYSIS")
print("="*80)
print()

# Check for required fields - minimum needed for backtesting
horses_with_minimum_fields = []
missing_fields_summary = {
    'odds': 0,
    'comprehensive_score': 0,
    'outcome': 0
}

for race in all_races:
    has_minimum = True
    
    if not race.get('odds'):
        missing_fields_summary['odds'] += 1
        has_minimum = False
    
    if not race.get('comprehensive_score'):
        missing_fields_summary['comprehensive_score'] += 1
        has_minimum = False
    
    if not race.get('outcome'):
        missing_fields_summary['outcome'] += 1
        has_minimum = False
    
    if has_minimum:
        horses_with_minimum_fields.append(race)

print(f"Races with minimum required data: {len(horses_with_minimum_fields)}")
print()
if missing_fields_summary['odds'] + missing_fields_summary['comprehensive_score'] + missing_fields_summary['outcome'] > 0:
    print("Missing fields breakdown:")
    for field, count in missing_fields_summary.items():
        if count > 0:
            print(f"  {field}: {count} races missing ({count/len(all_races)*100:.1f}%)")

print()
print("="*80)
print("PREPARING BACKTEST DATASET")
print("="*80)
print()

# Convert to JSON-serializable format
backtest_data = []

for race in horses_with_minimum_fields:
    # Convert Decimal to float for JSON serialization
    race_data = {
        'bet_date': race.get('bet_date', ''),
        'horse': race.get('horse', ''),
        'course': race.get('course', ''),
        'race_time': race.get('race_time', ''),
        'odds': float(race.get('odds', 0)),
        'outcome': str(race.get('outcome', '')).upper(),
        'comprehensive_score': int(race.get('comprehensive_score', 0)),
        'trainer': race.get('trainer', ''),
        'form': race.get('form', ''),
        'going': race.get('going', '')
    }
    
    # Extract individual factor scores if available
    score_breakdown = race.get('score_breakdown', {})
    race_data['factors'] = {
        'form_score': float(score_breakdown.get('form_score', 0)) if score_breakdown else 0,
        'trainer_score': float(score_breakdown.get('trainer_score', 0)) if score_breakdown else 0,
        'going_score': float(score_breakdown.get('going_score', 0)) if score_breakdown else 0,
        'odds_score': float(score_breakdown.get('odds_score', 0)) if score_breakdown else 0,
        'jockey_score': float(score_breakdown.get('jockey_score', 0)) if score_breakdown else 0,
        'track_score': float(score_breakdown.get('track_score', 0)) if score_breakdown else 0,
        'database_score': float(score_breakdown.get('database_score', 0)) if score_breakdown else 0
    }
    
    backtest_data.append(race_data)

# Save to file
with open('backtest_dataset.json', 'w') as f:
    json.dump(backtest_data, f, indent=2)

print(f"SUCCESS: Saved {len(backtest_data)} races to backtest_dataset.json")
print()

# Show sample statistics
wins = sum(1 for r in backtest_data if r['outcome'] in ['WON', 'WIN'])
losses = sum(1 for r in backtest_data if r['outcome'] in ['LOST', 'LOSS'])

print("Dataset Statistics:")
print(f"  Total races: {len(backtest_data)}")
if len(backtest_data) > 0:
    print(f"  Wins: {wins} ({wins/len(backtest_data)*100:.1f}%)")
    print(f"  Losses: {losses} ({losses/len(backtest_data)*100:.1f}%)")
else:
    print("  No complete data found")
print()

if len(backtest_data) >= 500:
    print("SUCCESS: SUFFICIENT DATA FOR BACKTESTING")
elif len(backtest_data) >= 200:
    print("WARNING: MODERATE DATA - Results may not be fully reliable")
elif len(backtest_data) >= 100:
    print("WARNING: LIMITED DATA - Use caution with conclusions")
else:
    print("ERROR: INSUFFICIENT DATA - Cannot perform reliable backtesting")
    print(f"Need {500 - len(backtest_data)} more races")

print()
print("="*80)
print("NEXT STEPS:")
print("="*80)
print("1. Run: python backtest_individual_factors.py")
print("2. Run: python backtest_baseline_strategies.py")
print("3. Run: python backtest_comprehensive_analysis.py")
print("="*80)

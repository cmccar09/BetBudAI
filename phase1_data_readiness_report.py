"""
Phase 1 Data Readiness Report - May 20, 2026
============================================
Comprehensive check of race data availability for Phase 1 analysis
"""

import boto3
import json
from datetime import datetime
from collections import defaultdict

def print_header(title):
    print()
    print("="*80)
    print(title)
    print("="*80)
    print()

def print_section(title):
    print()
    print("-" * 80)
    print(title)
    print("-" * 80)

print_header("PHASE 1 DATA READINESS REPORT")
print(f"Target Date: 2026-05-20")
print(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
lambda_client = boto3.client('lambda', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

target_date = '2026-05-20'
stats = {
    'races_available': 0,
    'horses_total': 0,
    'horses_with_form_runs': 0,
    'horses_with_jockey': 0,
    'horses_with_prev_jockey': 0,
    'horses_with_comments': 0,
    'data_completeness_pct': 0,
    'phase1_ready': False,
    'missing_requirements': []
}

# ============================================================================
# 1. CHECK LAMBDA FUNCTIONS
# ============================================================================
print_section("1. LAMBDA FUNCTION STATUS")

critical_lambdas = [
    'surebet-betfair-fetch',
    'surebet-analysis',
    'betbudai-morning'
]

for fn_name in critical_lambdas:
    try:
        response = lambda_client.get_function(FunctionName=fn_name)
        config = response['Configuration']
        print(f"  ✅ {fn_name}")
        print(f"     Last Modified: {config['LastModified']}")
        print(f"     Size: {config['CodeSize'] / 1024:.1f} KB")
    except Exception as e:
        print(f"  ❌ {fn_name}: {str(e)[:50]}")

# ============================================================================
# 2. CHECK DYNAMODB FOR TODAY'S DATA
# ============================================================================
print_section("2. DYNAMODB DATA CHECK")

# Scan for today's picks/races
race_items = []
all_items = []

try:
    # Get items for today
    response = table.scan(
        FilterExpression='bet_date = :date',
        ExpressionAttributeValues={':date': target_date},
        Limit=200
    )
    all_items = response.get('Items', [])
    print(f"  Total items for {target_date}: {len(all_items)}")

    # Filter for race/horse data
    for item in all_items:
        # Check if this looks like a horse/race item
        has_horse_data = any(key in item for key in [
            'horse_name', 'name', 'runners', 'all_horses',
            'form_runs', 'jockey', 'course', 'venue'
        ])
        if has_horse_data:
            race_items.append(item)

    print(f"  Race/horse items: {len(race_items)}")

    if not race_items and all_items:
        print(f"\n  Sample item types found:")
        for item in all_items[:3]:
            print(f"    bet_id: {item.get('bet_id', 'N/A')[:50]}")
            print(f"    keys: {', '.join(list(item.keys())[:6])}")

except Exception as e:
    print(f"  ❌ Error scanning table: {e}")

# ============================================================================
# 3. ANALYZE DATA COMPLETENESS
# ============================================================================
print_section("3. DATA COMPLETENESS ANALYSIS")

if race_items:
    stats['horses_total'] = len(race_items)

    # Analyze each horse for Phase 1 requirements
    for item in race_items:
        # Check for form_runs
        form_runs = item.get('form_runs', [])
        if form_runs and len(form_runs) > 0:
            stats['horses_with_form_runs'] += 1

            # Check for race comments (needed for run style)
            for run in form_runs[:3]:
                if run.get('race_comment') or run.get('comment'):
                    stats['horses_with_comments'] += 1
                    break

            # Check for previous jockey (needed for upgrade detection)
            for run in form_runs[:3]:
                if run.get('jockey'):
                    stats['horses_with_prev_jockey'] += 1
                    break

        # Check for current jockey
        if item.get('jockey') or item.get('jockey_name'):
            stats['horses_with_jockey'] += 1

    # Calculate completeness
    if stats['horses_total'] > 0:
        stats['data_completeness_pct'] = (
            min(stats['horses_with_form_runs'], stats['horses_with_jockey']) * 100
            // stats['horses_total']
        )

    print(f"  Total Horses: {stats['horses_total']}")
    print(f"  With form_runs: {stats['horses_with_form_runs']} ({stats['horses_with_form_runs']*100//stats['horses_total']}%)")
    print(f"  With current jockey: {stats['horses_with_jockey']} ({stats['horses_with_jockey']*100//stats['horses_total']}%)")
    print(f"  With previous jockey: {stats['horses_with_prev_jockey']} ({stats['horses_with_prev_jockey']*100//stats['horses_total']}%)")
    print(f"  With race comments: {stats['horses_with_comments']} ({stats['horses_with_comments']*100//max(stats['horses_total'],1)}%)")
    print(f"\n  Overall Completeness: {stats['data_completeness_pct']}%")
else:
    print(f"  ⚠️ No race data found for {target_date}")

# ============================================================================
# 4. IDENTIFY AVAILABLE RACES
# ============================================================================
print_section("4. AVAILABLE RACES BY VENUE")

races_by_venue = defaultdict(lambda: defaultdict(list))

for item in race_items:
    venue = item.get('course') or item.get('venue') or 'Unknown'
    race_time = item.get('race_time') or item.get('time') or 'Unknown'
    horse = item.get('horse_name') or item.get('name') or 'Unknown'

    races_by_venue[venue][race_time].append(horse)

if races_by_venue:
    stats['races_available'] = sum(len(times) for times in races_by_venue.values())
    print(f"  Total Venues: {len(races_by_venue)}")
    print(f"  Total Races: {stats['races_available']}")
    print()

    for venue in sorted(races_by_venue.keys())[:5]:  # Show first 5 venues
        print(f"  {venue}:")
        for time in sorted(races_by_venue[venue].keys())[:3]:  # Show first 3 races
            horses = races_by_venue[venue][time]
            print(f"    {time}: {len(horses)} horses")

    if len(races_by_venue) > 5:
        print(f"  ... and {len(races_by_venue) - 5} more venues")
else:
    print(f"  ⚠️ No races with venue/time information")

# ============================================================================
# 5. CHECK PHASE 1 WEIGHTS DEPLOYMENT
# ============================================================================
print_section("5. PHASE 1 WEIGHTS STATUS")

try:
    response = table.get_item(
        Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'}
    )
    if 'Item' in response:
        weights_item = response['Item']
        print(f"  ✅ Weights configuration found")
        print(f"     Version: {weights_item.get('version', 'N/A')}")
        print(f"     Phase: {weights_item.get('phase', 'N/A')}")
        print(f"     Updated: {weights_item.get('updated_at', 'N/A')}")

        # Check for Phase 1 signals
        weights = weights_item.get('weights', {})
        phase1_signals = ['pace_match', 'jockey_upgrade']
        found_signals = [sig for sig in phase1_signals if sig in weights]

        if found_signals:
            print(f"     Phase 1 signals: {', '.join(found_signals)}")
        else:
            print(f"     ⚠️ Phase 1 signals not in weights config")
    else:
        print(f"  ⚠️ No weights configuration found")
except Exception as e:
    print(f"  ⚠️ Could not check weights: {e}")

# ============================================================================
# 6. PHASE 1 READINESS ASSESSMENT
# ============================================================================
print_section("6. PHASE 1 READINESS ASSESSMENT")

# Determine if we can generate Phase 1 picks
if not race_items:
    stats['missing_requirements'].append("No race data available")
elif stats['horses_total'] == 0:
    stats['missing_requirements'].append("No horses found")
else:
    # Quality thresholds for Phase 1
    if stats['horses_with_form_runs'] < stats['horses_total'] * 0.5:
        stats['missing_requirements'].append(
            f"Insufficient form data: {stats['horses_with_form_runs']}/{stats['horses_total']} horses"
        )

    if stats['horses_with_jockey'] < stats['horses_total'] * 0.7:
        stats['missing_requirements'].append(
            f"Missing jockey data: {stats['horses_with_jockey']}/{stats['horses_total']} horses"
        )

    # Phase 1 signals are selective, so comments don't need to be 100%
    if stats['horses_with_comments'] < stats['horses_total'] * 0.2:
        stats['missing_requirements'].append(
            f"Very few race comments: {stats['horses_with_comments']}/{stats['horses_total']} horses (limits run style detection)"
        )

# Set readiness flag
stats['phase1_ready'] = len(stats['missing_requirements']) == 0

if stats['phase1_ready']:
    print(f"  ✅ READY FOR PHASE 1 ANALYSIS")
    print(f"\n  Available Data:")
    print(f"    - Races: {stats['races_available']}")
    print(f"    - Horses: {stats['horses_total']}")
    print(f"    - Completeness: {stats['data_completeness_pct']}%")
    print(f"\n  Phase 1 Signals:")
    print(f"    - Run Style: {stats['horses_with_comments']}/{stats['horses_total']} horses eligible")
    print(f"    - Jockey Upgrade: {stats['horses_with_prev_jockey']}/{stats['horses_total']} horses eligible")
else:
    print(f"  ❌ NOT READY FOR PHASE 1 ANALYSIS")
    print(f"\n  Missing Requirements:")
    for req in stats['missing_requirements']:
        print(f"    - {req}")

# ============================================================================
# 7. SAMPLE DATA INSPECTION
# ============================================================================
if race_items and stats['horses_with_form_runs'] > 0:
    print_section("7. SAMPLE DATA STRUCTURE")

    # Find a horse with good data
    sample = None
    for item in race_items:
        if item.get('form_runs') and len(item.get('form_runs', [])) > 0:
            sample = item
            break

    if sample:
        print(f"  Sample Horse: {sample.get('horse_name', sample.get('name', 'N/A'))}")
        print(f"  Venue: {sample.get('course', sample.get('venue', 'N/A'))}")
        print(f"  Time: {sample.get('race_time', sample.get('time', 'N/A'))}")
        print(f"  Current Jockey: {sample.get('jockey', sample.get('jockey_name', 'N/A'))}")
        print(f"  Form Runs: {len(sample.get('form_runs', []))}")

        if sample.get('form_runs'):
            first_run = sample['form_runs'][0]
            print(f"\n  First Form Run:")
            print(f"    Date: {first_run.get('date', 'N/A')}")
            print(f"    Course: {first_run.get('course', 'N/A')}")
            print(f"    Position: {first_run.get('position', 'N/A')}")
            print(f"    Jockey: {first_run.get('jockey', 'N/A')}")
            print(f"    Comment: {'YES' if first_run.get('race_comment') or first_run.get('comment') else 'NO'}")

# ============================================================================
# 8. FINAL SUMMARY
# ============================================================================
print_header("EXECUTIVE SUMMARY")

if stats['phase1_ready']:
    print("STATUS: ✅ CAN GENERATE PHASE 1 PICKS NOW")
    print()
    print(f"Race Data Available:")
    print(f"  • {stats['races_available']} races across {len(races_by_venue)} venues")
    print(f"  • {stats['horses_total']} horses with data")
    print(f"  • {stats['data_completeness_pct']}% data completeness")
    print()
    print(f"Phase 1 Signal Coverage:")
    print(f"  • Run Style Classification: {stats['horses_with_comments']}/{stats['horses_total']} horses ({stats['horses_with_comments']*100//max(stats['horses_total'],1)}%)")
    print(f"  • Jockey Upgrade Detection: {stats['horses_with_prev_jockey']}/{stats['horses_total']} horses ({stats['horses_with_prev_jockey']*100//max(stats['horses_total'],1)}%)")
    print()
    print("RECOMMENDATION: Run Phase 1 analysis pipeline now")
else:
    print("STATUS: ❌ CANNOT GENERATE PHASE 1 PICKS YET")
    print()
    print(f"Current State:")
    print(f"  • DynamoDB items: {len(all_items)}")
    print(f"  • Race items: {len(race_items)}")
    print(f"  • Horses with data: {stats['horses_total']}")
    print()
    print(f"Missing:")
    for req in stats['missing_requirements'][:3]:
        print(f"  • {req}")
    print()
    print("RECOMMENDATION:")
    if not race_items:
        print("  1. Run morning pipeline: betbudai-morning Lambda")
        print("  2. This will trigger Betfair fetch + enrichment")
    else:
        print("  1. Check if morning pipeline has completed")
        print("  2. Verify data enrichment (form_runs) succeeded")

print()
print(f"Report Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
print("="*80)

# ============================================================================
# OUTPUT JSON SUMMARY
# ============================================================================
print()
print("JSON SUMMARY:")
print(json.dumps(stats, indent=2))

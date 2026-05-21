"""
Full System Health Check for BetBudAI
Validates all components before tomorrow's automated runs
"""

import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal

print("\n" + "="*70)
print("BetBudAI Full System Health Check")
print(f"Run Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
print("="*70 + "\n")

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name='eu-west-1')
events_client = boto3.client('events', region_name='eu-west-1')
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
sfn_client = boto3.client('stepfunctions', region_name='eu-west-1')

health_status = {
    'lambda_functions': [],
    'eventbridge_rules': [],
    'dynamodb_tables': [],
    'step_functions': [],
    'errors': [],
    'warnings': []
}

# ============================================================================
# 1. Lambda Functions Health Check
# ============================================================================
print("[1/5] Checking Lambda Functions...")
print("-" * 70)

critical_functions = [
    'betbudai-morning',
    'betbudai-refresh',
    'betbudai-evening',
    'surebet-betfair-fetch',
    'surebet-analysis',
    'surebet-validate',
    'surebet-featured-meeting',
    'surebet-notify',
    'surebet-free-feeds',
    'surebet-sl-results',
    'surebet-fav-results',
    'surebet-results-fetch',
    'surebet-loss-report',
    'surebet-cache-roi',
    'surebet-learning',
]

optional_functions = [
    'calculate-improver-boost-scores',
    'apply-improver-boosted-picks',
    'featured-improver-enforcer',
    'compare-race-fields',
    'evening-miss-analysis',
    'betbudai-learning-orchestrator',
]

for func_name in critical_functions:
    try:
        response = lambda_client.get_function(FunctionName=func_name)
        state = response['Configuration']['State']
        last_modified = response['Configuration']['LastModified']

        if state == 'Active':
            print(f"  [OK] {func_name:<40} State: {state}")
            health_status['lambda_functions'].append({
                'name': func_name,
                'status': 'OK',
                'state': state
            })
        else:
            print(f"  [WARNING] {func_name:<40} State: {state}")
            health_status['warnings'].append(f"Lambda {func_name} not Active: {state}")

    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"  [ERROR] {func_name:<40} NOT FOUND")
        health_status['errors'].append(f"Critical Lambda {func_name} not found")
    except Exception as e:
        print(f"  [ERROR] {func_name:<40} Error: {str(e)[:30]}")
        health_status['errors'].append(f"Lambda {func_name}: {str(e)}")

print(f"\nOptional Functions:")
for func_name in optional_functions:
    try:
        response = lambda_client.get_function(FunctionName=func_name)
        state = response['Configuration']['State']
        print(f"  [OK] {func_name:<40} State: {state}")
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"  [INFO] {func_name:<40} Not deployed (optional)")

# ============================================================================
# 2. EventBridge Rules Health Check
# ============================================================================
print(f"\n[2/5] Checking EventBridge Schedules...")
print("-" * 70)

critical_rules = [
    'betbudai-morning-trigger',           # 08:30 UTC
    'betbudai-refresh-12-trigger',        # 12:00 UTC
    'betbudai-featured-lock-trigger',     # 13:30 UTC
    'betbudai-refresh-14-30-trigger',     # 14:30 UTC (NEW)
    'betbudai-refresh-16-trigger',        # 16:00 UTC
    'betbudai-refresh-17-30-trigger',     # 17:30 UTC (NEW)
    'betbudai-evening-trigger',           # 20:00 UTC
]

for rule_name in critical_rules:
    try:
        response = events_client.describe_rule(Name=rule_name)
        state = response['State']
        schedule = response.get('ScheduleExpression', 'N/A')

        if state == 'ENABLED':
            print(f"  [OK] {rule_name:<40} {schedule}")
            health_status['eventbridge_rules'].append({
                'name': rule_name,
                'status': 'OK',
                'state': state,
                'schedule': schedule
            })
        else:
            print(f"  [WARNING] {rule_name:<40} State: {state}")
            health_status['warnings'].append(f"EventBridge rule {rule_name} not enabled")

    except events_client.exceptions.ResourceNotFoundException:
        print(f"  [ERROR] {rule_name:<40} NOT FOUND")
        health_status['errors'].append(f"Critical EventBridge rule {rule_name} not found")
    except Exception as e:
        print(f"  [ERROR] {rule_name:<40} Error: {str(e)[:30]}")

# Check polling schedules
print(f"\nResults Polling Schedules (13:00-21:00 every 20 min):")
polling_count = 0
polling_errors = 0
for hour in range(13, 22):
    for minute in ['00', '20', '40']:
        rule_name = f'betbudai-results-poll-{hour:02d}-{minute}'
        try:
            response = events_client.describe_rule(Name=rule_name)
            if response['State'] == 'ENABLED':
                polling_count += 1
        except:
            polling_errors += 1

print(f"  [OK] Found {polling_count} polling schedules active")
if polling_errors > 0:
    print(f"  [WARNING] {polling_errors} polling schedules missing")

# ============================================================================
# 3. DynamoDB Tables Health Check
# ============================================================================
print(f"\n[3/5] Checking DynamoDB Tables...")
print("-" * 70)

critical_tables = [
    'SureBetBets',
]

for table_name in critical_tables:
    try:
        table = dynamodb.Table(table_name)
        table.load()

        status = table.table_status
        item_count = table.item_count

        if status == 'ACTIVE':
            print(f"  [OK] {table_name:<30} Status: {status}, Items: {item_count:,}")
            health_status['dynamodb_tables'].append({
                'name': table_name,
                'status': 'OK',
                'state': status,
                'items': item_count
            })
        else:
            print(f"  [WARNING] {table_name:<30} Status: {status}")
            health_status['warnings'].append(f"DynamoDB table {table_name} not ACTIVE: {status}")

    except Exception as e:
        print(f"  [ERROR] {table_name:<30} Error: {str(e)[:30]}")
        health_status['errors'].append(f"DynamoDB table {table_name}: {str(e)}")

# Test write permissions
print(f"\n  Testing DynamoDB write permissions...")
try:
    table = dynamodb.Table('SureBetBets')
    test_item = {
        'bet_date': '9999-99-99',
        'bet_id': 'HEALTH_CHECK_TEST',
        'test': 'health_check',
        'timestamp': datetime.utcnow().isoformat()
    }
    table.put_item(Item=test_item)
    table.delete_item(Key={'bet_date': '9999-99-99', 'bet_id': 'HEALTH_CHECK_TEST'})
    print(f"  [OK] DynamoDB write/delete permissions confirmed")
except Exception as e:
    print(f"  [ERROR] DynamoDB write test failed: {str(e)}")
    health_status['errors'].append(f"DynamoDB write permissions issue: {str(e)}")

# ============================================================================
# 4. Step Functions Health Check
# ============================================================================
print(f"\n[4/5] Checking Step Functions...")
print("-" * 70)

try:
    # List step functions
    response = sfn_client.list_state_machines()
    step_functions = [sm for sm in response['stateMachines'] if 'surebet' in sm['name'].lower() or 'betbudai' in sm['name'].lower()]

    for sm in step_functions:
        name = sm['name']
        status = sm['status']

        if status == 'ACTIVE':
            print(f"  [OK] {name:<40} Status: {status}")
            health_status['step_functions'].append({
                'name': name,
                'status': 'OK',
                'state': status
            })
        else:
            print(f"  [WARNING] {name:<40} Status: {status}")

except Exception as e:
    print(f"  [WARNING] Could not list Step Functions: {str(e)}")

# ============================================================================
# 5. Data Freshness Check
# ============================================================================
print(f"\n[5/5] Checking Data Freshness...")
print("-" * 70)

try:
    table = dynamodb.Table('SureBetBets')

    # Check yesterday's data
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.utcnow().strftime('%Y-%m-%d')

    yesterday_response = table.query(
        KeyConditionExpression='bet_date = :date',
        ExpressionAttributeValues={':date': yesterday},
        Limit=10
    )

    today_response = table.query(
        KeyConditionExpression='bet_date = :date',
        ExpressionAttributeValues={':date': today},
        Limit=10
    )

    yesterday_count = yesterday_response['Count']
    today_count = today_response['Count']

    print(f"  [INFO] Yesterday ({yesterday}): {yesterday_count} picks (sample)")
    print(f"  [INFO] Today ({today}): {today_count} picks (sample)")

    if yesterday_count > 0:
        print(f"  [OK] Data pipeline generating picks")
    else:
        print(f"  [WARNING] No picks found for yesterday - check pipelines")
        health_status['warnings'].append("No picks found for yesterday")

except Exception as e:
    print(f"  [ERROR] Data freshness check failed: {str(e)}")
    health_status['errors'].append(f"Data freshness check: {str(e)}")

# ============================================================================
# Summary Report
# ============================================================================
print(f"\n{'='*70}")
print("HEALTH CHECK SUMMARY")
print("="*70)

total_checks = (len(health_status['lambda_functions']) +
                len(health_status['eventbridge_rules']) +
                len(health_status['dynamodb_tables']) +
                len(health_status['step_functions']))

print(f"\nComponents Checked:")
print(f"  Lambda Functions:    {len(health_status['lambda_functions'])} OK")
print(f"  EventBridge Rules:   {len(health_status['eventbridge_rules'])} OK")
print(f"  DynamoDB Tables:     {len(health_status['dynamodb_tables'])} OK")
print(f"  Step Functions:      {len(health_status['step_functions'])} OK")
print(f"  Total:               {total_checks} components")

error_count = len(health_status['errors'])
warning_count = len(health_status['warnings'])

if error_count > 0:
    print(f"\n[ERROR] {error_count} CRITICAL ERRORS FOUND:")
    for i, error in enumerate(health_status['errors'], 1):
        print(f"  {i}. {error}")

if warning_count > 0:
    print(f"\n[WARNING] {warning_count} Warnings:")
    for i, warning in enumerate(health_status['warnings'], 1):
        print(f"  {i}. {warning}")

if error_count == 0 and warning_count == 0:
    print(f"\n[SUCCESS] All systems operational!")
    print(f"  System is ready for tomorrow's automated runs")
    print(f"  No critical issues detected")
    status_code = 0
elif error_count == 0:
    print(f"\n[PASS] System operational with minor warnings")
    print(f"  Core functionality intact")
    print(f"  Warnings should be reviewed but not blocking")
    status_code = 0
else:
    print(f"\n[FAIL] Critical errors detected")
    print(f"  System may not function correctly tomorrow")
    print(f"  Immediate attention required")
    status_code = 1

# Tomorrow's Schedule Preview
print(f"\n{'='*70}")
print("TOMORROW'S SCHEDULE PREVIEW")
print("="*70)
print(f"\nScheduled Runs (all times UTC):")
print(f"  08:30 - Morning Pipeline (betbudai-morning)")
print(f"  12:00 - Refresh Pipeline")
print(f"  13:00 - Results polling begins (every 20 min)")
print(f"  13:30 - Featured Meeting Lock (CRITICAL)")
print(f"  14:30 - Refresh Pipeline (NEW)")
print(f"  16:00 - Refresh Pipeline")
print(f"  17:30 - Refresh Pipeline (NEW)")
print(f"  20:00 - Evening Pipeline + Learning")
print(f"  21:00 - Results polling ends")
print(f"  22:00 - Deep Learning Analysis (NEW)")

print(f"\n{'='*70}")
print("Health Check Complete")
print(f"Status: {'PASS' if status_code == 0 else 'FAIL'}")
print("="*70 + "\n")

# Save report
with open('health_check_report.json', 'w') as f:
    json.dump(health_status, f, indent=2, default=str)
print("Report saved to: health_check_report.json")

exit(status_code)

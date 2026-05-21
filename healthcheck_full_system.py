"""
BetBudAI Full System Healthcheck
=================================
Checks all Lambda functions, Step Functions, EventBridge rules, and data feeds
"""

import boto3
import json
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError

print("="*80)
print("BETBUDAI FULL SYSTEM HEALTHCHECK")
print("="*80)
print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
print()

# AWS clients
lambda_client = boto3.client('lambda', region_name='eu-west-1')
events_client = boto3.client('events', region_name='eu-west-1')
stepfunctions_client = boto3.client('stepfunctions', region_name='eu-west-1')
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
logs_client = boto3.client('logs', region_name='eu-west-1')

health_status = {
    'healthy': [],
    'warnings': [],
    'errors': [],
}

# ============================================================================
# 1. LAMBDA FUNCTIONS CHECK
# ============================================================================
print("[1/6] CHECKING LAMBDA FUNCTIONS")
print("-" * 80)

CRITICAL_LAMBDAS = [
    'betbudai-morning',
    'betbudai-evening',
    'betbudai-refresh',
    'surebet-analysis',
    'surebet-betfair-fetch',
    'surebet-validate',
    'surebet-featured-meeting',
    'surebet-notify',
]

OPTIONAL_LAMBDAS = [
    'calculate-improver-boost-scores',
    'apply-improver-boosted-picks',
    'featured-improver-enforcer',
    'compare-race-fields',
    'betbudai-learning',
    'betbudai-free-feeds',
]

def check_lambda_function(function_name, is_critical=True):
    """Check Lambda function exists and get its last execution"""
    try:
        # Get function config
        response = lambda_client.get_function(FunctionName=function_name)
        config = response['Configuration']

        status_code = config.get('State', 'Unknown')
        last_modified = config.get('LastModified', 'Unknown')
        runtime = config.get('Runtime', 'Unknown')

        # Check for recent invocations (last 24 hours)
        log_group = f"/aws/lambda/{function_name}"
        try:
            start_time = int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp() * 1000)
            log_response = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=start_time,
                limit=10
            )
            recent_invocations = len(log_response.get('events', []))
        except:
            recent_invocations = 'N/A'

        if status_code == 'Active':
            health_status['healthy'].append(f"Lambda: {function_name}")
            print(f"  [OK] {function_name:40s} State: {status_code:10s} Invocations(24h): {recent_invocations}")
            return True
        else:
            msg = f"Lambda {function_name} state: {status_code}"
            if is_critical:
                health_status['errors'].append(msg)
                print(f"  [ERROR] {function_name:40s} State: {status_code:10s}")
            else:
                health_status['warnings'].append(msg)
                print(f"  [WARN] {function_name:40s} State: {status_code:10s}")
            return False

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            msg = f"Lambda {function_name} not found"
            if is_critical:
                health_status['errors'].append(msg)
                print(f"  [ERROR] {function_name:40s} NOT FOUND")
            else:
                health_status['warnings'].append(msg)
                print(f"  [WARN] {function_name:40s} NOT FOUND")
            return False
        else:
            raise

print("\nCritical Lambdas:")
for func in CRITICAL_LAMBDAS:
    check_lambda_function(func, is_critical=True)

print("\nOptional Lambdas:")
for func in OPTIONAL_LAMBDAS:
    check_lambda_function(func, is_critical=False)

# ============================================================================
# 2. EVENTBRIDGE SCHEDULED RULES CHECK
# ============================================================================
print("\n[2/6] CHECKING EVENTBRIDGE SCHEDULED RULES")
print("-" * 80)

EXPECTED_RULES = [
    'betbudai-morning-schedule',
    'betbudai-evening-schedule',
    'betbudai-refresh-schedule',
]

try:
    rules_response = events_client.list_rules(NamePrefix='betbudai')
    rules = rules_response.get('Rules', [])

    for rule in rules:
        name = rule['Name']
        state = rule['State']
        schedule = rule.get('ScheduleExpression', 'N/A')

        if state == 'ENABLED':
            health_status['healthy'].append(f"EventBridge: {name}")
            print(f"  [OK] {name:40s} State: {state:10s} Schedule: {schedule}")
        else:
            health_status['warnings'].append(f"EventBridge {name} is {state}")
            print(f"  [WARN] {name:40s} State: {state:10s} Schedule: {schedule} [DISABLED]")

    # Check for missing expected rules
    found_rule_names = [r['Name'] for r in rules]
    for expected in EXPECTED_RULES:
        if expected not in found_rule_names:
            health_status['warnings'].append(f"EventBridge rule {expected} not found")
            print(f"  [WARN] {expected:40s} NOT FOUND [WARNING]")

except Exception as e:
    health_status['errors'].append(f"Failed to check EventBridge rules: {e}")
    print(f"  [ERROR] Failed to check EventBridge rules: {e}")

# ============================================================================
# 3. STEP FUNCTIONS CHECK
# ============================================================================
print("\n[3/6] CHECKING STEP FUNCTIONS")
print("-" * 80)

try:
    sf_response = stepfunctions_client.list_state_machines(maxResults=50)
    state_machines = sf_response.get('stateMachines', [])

    if not state_machines:
        print("  [INFO] No Step Functions found (system may use Lambda orchestration)")
    else:
        for sm in state_machines:
            name = sm['name']
            arn = sm['stateMachineArn']

            # Get recent executions
            exec_response = stepfunctions_client.list_executions(
                stateMachineArn=arn,
                maxResults=10
            )
            recent_execs = exec_response.get('executions', [])

            if recent_execs:
                latest = recent_execs[0]
                status = latest['status']
                start_time = latest['startDate']

                if status == 'SUCCEEDED':
                    health_status['healthy'].append(f"StepFunction: {name}")
                    print(f"  [OK] {name:40s} Latest: {status:10s} At: {start_time}")
                elif status in ['RUNNING', 'PENDING']:
                    health_status['healthy'].append(f"StepFunction: {name}")
                    print(f"  [RUNNING] {name:40s} Latest: {status:10s} At: {start_time}")
                else:
                    health_status['warnings'].append(f"StepFunction {name} latest status: {status}")
                    print(f"  [WARN] {name:40s} Latest: {status:10s} At: {start_time} [WARNING]")
            else:
                print(f"  [INFO] {name:40s} No recent executions")

except Exception as e:
    print(f"  [INFO] Step Functions check: {e}")

# ============================================================================
# 4. DYNAMODB TABLES CHECK
# ============================================================================
print("\n[4/6] CHECKING DYNAMODB TABLES")
print("-" * 80)

REQUIRED_TABLES = [
    'SureBetBets',
    'SureBetWeights',
]

for table_name in REQUIRED_TABLES:
    try:
        table = dynamodb.Table(table_name)
        table.load()

        status = table.table_status
        item_count = table.item_count

        if status == 'ACTIVE':
            health_status['healthy'].append(f"DynamoDB: {table_name}")
            print(f"  [OK] {table_name:40s} Status: {status:10s} Items: {item_count:,}")
        else:
            health_status['warnings'].append(f"DynamoDB {table_name} status: {status}")
            print(f"  [WARN] {table_name:40s} Status: {status:10s} [WARNING]")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            health_status['errors'].append(f"DynamoDB table {table_name} not found")
            print(f"  [ERROR] {table_name:40s} NOT FOUND [ERROR]")
        else:
            health_status['errors'].append(f"DynamoDB {table_name}: {e}")
            print(f"  [ERROR] {table_name:40s} Error: {e} [ERROR]")

# ============================================================================
# 5. WEIGHTS & CONFIGURATION CHECK
# ============================================================================
print("\n[5/6] CHECKING WEIGHTS & CONFIGURATION")
print("-" * 80)

try:
    weights_table = dynamodb.Table('SureBetWeights')
    response = weights_table.get_item(Key={'weight_id': 'current'})

    if 'Item' in response:
        weights = response['Item']
        version = weights.get('version', 'Unknown')
        updated = weights.get('updated_at', 'Unknown')
        weight_count = len([k for k in weights.keys() if k not in ['weight_id', 'version', 'updated_at']])

        # Check for Phase 1 weights
        phase1_weights = [
            'pace_match_bonus',
            'jockey_upgrade_bonus',
            'first_time_blinkers',
            'high_volume_gamble_bonus'
        ]
        phase1_present = sum(1 for w in phase1_weights if w in weights)

        print(f"  [OK] Weights Version: {version}")
        print(f"  [OK] Total Weight Parameters: {weight_count}")
        print(f"  [OK] Phase 1 Weights Present: {phase1_present}/4")
        print(f"  [OK] Last Updated: {updated}")

        if phase1_present == 4:
            health_status['healthy'].append("Phase 1 weights deployed")
            print(f"  [OK] Phase 1 weights FULLY DEPLOYED")
        elif phase1_present > 0:
            health_status['warnings'].append(f"Phase 1 weights partially deployed ({phase1_present}/4)")
            print(f"  [WARN] Phase 1 weights PARTIALLY deployed ({phase1_present}/4) [WARNING]")
        else:
            health_status['warnings'].append("Phase 1 weights not found")
            print(f"  [WARN] Phase 1 weights NOT found [WARNING]")

    else:
        health_status['errors'].append("Weights configuration not found")
        print(f"  [ERROR] Weights configuration NOT FOUND [ERROR]")

except Exception as e:
    health_status['errors'].append(f"Failed to check weights: {e}")
    print(f"  [ERROR] Failed to check weights: {e} [ERROR]")

# ============================================================================
# 6. RECENT PICKS & DATA FEEDS CHECK
# ============================================================================
print("\n[6/6] CHECKING RECENT PICKS & DATA FEEDS")
print("-" * 80)

try:
    picks_table = dynamodb.Table('SureBetBets')

    # Get today's date
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

    # Check for today's picks
    response = picks_table.scan(
        FilterExpression='#dt = :today',
        ExpressionAttributeNames={'#dt': 'date'},
        ExpressionAttributeValues={':today': today},
        Limit=20
    )

    today_items = response.get('Items', [])
    today_count = len(today_items)

    if today_count > 0:
        health_status['healthy'].append(f"Today's data: {today_count} items")
        print(f"  [OK] Today's Data ({today}): {today_count} items found")

        # Check for specific data types
        data_types = {}
        for item in today_items:
            bet_date = item.get('bet_date', 'UNKNOWN')
            data_types[bet_date] = data_types.get(bet_date, 0) + 1

        print(f"    Data types found:")
        for dtype, count in sorted(data_types.items()):
            print(f"      - {dtype}: {count}")
    else:
        health_status['warnings'].append(f"No data found for today ({today})")
        print(f"  [WARN] No data found for today ({today}) [WARNING]")

    # Check yesterday for comparison
    response = picks_table.scan(
        FilterExpression='#dt = :yesterday',
        ExpressionAttributeNames={'#dt': 'date'},
        ExpressionAttributeValues={':yesterday': yesterday},
        Limit=20
    )

    yesterday_items = response.get('Items', [])
    yesterday_count = len(yesterday_items)

    print(f"  [INFO] Yesterday's Data ({yesterday}): {yesterday_count} items (for comparison)")

except Exception as e:
    health_status['errors'].append(f"Failed to check recent picks: {e}")
    print(f"  [ERROR] Failed to check recent picks: {e} [ERROR]")

# ============================================================================
# HEALTH SUMMARY
# ============================================================================
print("\n" + "="*80)
print("HEALTH SUMMARY")
print("="*80)

total_checks = len(health_status['healthy']) + len(health_status['warnings']) + len(health_status['errors'])
healthy_count = len(health_status['healthy'])
warning_count = len(health_status['warnings'])
error_count = len(health_status['errors'])

print(f"\nTotal Checks: {total_checks}")
print(f"  [OK] Healthy: {healthy_count}")
print(f"  [WARN] Warnings: {warning_count}")
print(f"  [ERROR] Errors: {error_count}")

if error_count > 0:
    print(f"\n[DEGRADED] SYSTEM STATUS: DEGRADED")
    print(f"\nCritical Issues ({error_count}):")
    for error in health_status['errors']:
        print(f"  [ERROR] {error}")
elif warning_count > 0:
    print(f"\n[WARN]️  SYSTEM STATUS: HEALTHY (with warnings)")
    print(f"\nWarnings ({warning_count}):")
    for warning in health_status['warnings']:
        print(f"  [WARN] {warning}")
else:
    print(f"\n[HEALTHY] SYSTEM STATUS: FULLY HEALTHY")

print("\n" + "="*80)
print("HEALTHCHECK COMPLETE")
print("="*80)

# Return exit code based on health
import sys
if error_count > 0:
    sys.exit(1)
elif warning_count > 0:
    sys.exit(0)  # Warnings are OK, just informational
else:
    sys.exit(0)

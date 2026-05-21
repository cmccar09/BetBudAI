"""
Invoke Analysis Lambda and Check Its Logs
==========================================
See what Phase 1 is actually doing
"""

import boto3
import json
import time
from datetime import datetime

print("="*70)
print("INVOKING ANALYSIS LAMBDA AND CHECKING LOGS")
print("="*70)
print()

lambda_client = boto3.client('lambda', region_name='eu-west-1')
logs_client = boto3.client('logs', region_name='eu-west-1')

target_date = datetime.now().strftime('%Y-%m-%d')

# Invoke the Lambda
print(f"[1/2] Invoking surebet-analysis Lambda...")
print(f"  Date: {target_date}")
print()

payload = {'target_date': target_date, 'force': True}

try:
    response = lambda_client.invoke(
        FunctionName='surebet-analysis',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    status = response['StatusCode']
    result = json.loads(response['Payload'].read())

    print(f"[STATUS] HTTP {status}")

    if response.get('FunctionError'):
        print(f"[ERROR] Lambda execution failed:")
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"[SUCCESS] Lambda executed")

        # Parse result
        body = result.get('body', result)
        if isinstance(body, str):
            body = json.loads(body)

        print(f"\nResults:")
        print(f"  Horses analyzed: {body.get('horses_analyzed', 0)}")
        print(f"  Races analyzed: {body.get('races_analyzed', 0)}")
        print(f"  Picks count: {body.get('picks_count', 0)}")
        print(f"  Phase 1 active: {body.get('phase1_signals_active', 'Unknown')}")

        if body.get('message'):
            print(f"  Message: {body.get('message')}")

except Exception as e:
    print(f"[ERROR] Failed to invoke: {e}")
    import sys
    sys.exit(1)

# Wait a moment for logs to be available
print(f"\n[2/2] Retrieving CloudWatch logs...")
print(f"  Waiting 3 seconds for logs to propagate...")
time.sleep(3)

try:
    log_group = '/aws/lambda/surebet-analysis'

    # Get latest log stream
    streams_response = logs_client.describe_log_streams(
        logGroupName=log_group,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )

    if not streams_response.get('logStreams'):
        print(f"[WARNING] No log streams found")
    else:
        log_stream = streams_response['logStreams'][0]['logStreamName']
        print(f"  Log stream: {log_stream}")
        print()

        # Get recent log events
        events_response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            limit=100,
            startFromHead=False  # Get most recent
        )

        events = events_response.get('events', [])
        print(f"[LOGS] Last {len(events)} log messages:")
        print()

        # Filter for relevant messages
        for event in events[-30:]:  # Last 30 messages
            message = event['message'].strip()

            # Highlight important messages
            if any(keyword in message for keyword in ['PHASE1', 'analysis', 'ERROR', 'races', 'picks', 'signals']):
                print(f"  {message}")

except Exception as e:
    print(f"[WARNING] Could not retrieve logs: {e}")

print()
print("="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print()
print("Key Findings:")
print("  - If 'races_analyzed: 0' then no race data was available to analyze")
print("  - If 'phase1_active: true' then Phase 1 code is loaded")
print("  - If 'phase1_active: false' then weights not found")
print("  - Logs show actual Lambda execution details")

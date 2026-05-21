#!/usr/bin/env python3
"""Invoke morning pipeline for today's picks with all optimizations."""

import boto3
import json
from datetime import datetime, timezone

lc = boto3.client('lambda', region_name='eu-west-1')

payload = {
    'stage': 'morning',
    'target_date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
    'force_analysis': False,
    'run_optimizations': True
}

print('[INVOKING] betbudai-morning with optimizations enabled')
print(f'  Date: {payload["target_date"]}')
print(f'  Field comparison: enabled')
print(f'  Improver boost: enabled')
print()

try:
    resp = lc.invoke(
        FunctionName='betbudai-morning',
        InvocationType='Event',  # Async - don't wait for result
        Payload=json.dumps(payload).encode()
    )
    
    status = resp.get('StatusCode')
    
    print(f'[RESULT] Status: {status}')
    
    if status == 202:
        print('[SUCCESS] Pipeline invoked asynchronously')
        print()
        print('✓ Morning pipeline is running in the background')
        print('  Target date: ' + payload['target_date'])
        print('  Optimizations: field comparison, improver boost')
        print()
        print('📊 Check results:')
        print('  - API: /api/picks/today')
        print('  - Logs: CloudWatch → betbudai-morning')
        print('  - DynamoDB: SureBetBets table')
    else:
        print(f'[WARNING] Unexpected status: {status}')

    
except Exception as e:
    print(f'[EXCEPTION] {e}')
    import traceback
    traceback.print_exc()

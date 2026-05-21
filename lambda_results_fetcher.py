"""
BettingResultsFetcher Lambda handler.
Delegates to auto_record_pending_results() in the main API module.
Triggered hourly by EventBridge (cron 14-23 UTC).
"""
import json
import sys
import os

# Allow importing the main API module from the same zip
sys.path.insert(0, os.path.dirname(__file__))

from _bpapi_patched import auto_record_pending_results


def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
    }
    print(f'BettingResultsFetcher triggered: {json.dumps(event)}')
    try:
        return auto_record_pending_results(headers)
    except Exception as e:
        print(f'BettingResultsFetcher error: {e}')
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'success': False, 'error': str(e)}),
        }

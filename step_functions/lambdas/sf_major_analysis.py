"""
Lambda: surebet-major-analysis
================================
Phase : Weekly major-race early-bird analysis
Input : {"date": "YYYY-MM-DD"}  (from Step Functions InjectDate)
Output: {"success": true, "races_analysed": N, "message": "..."}

Invokes the BettingPicksAPI Lambda's /api/major-race-analysis/run endpoint
(via direct Lambda invocation) to scrape ante-post markets from Sporting Life,
score each horse, and store predictions in DynamoDB.

Runs weekly — Monday 07:00 UTC (08:00 BST).
"""

import json
import boto3

REGION = 'eu-west-1'
API_LAMBDA_NAME = 'BettingPicksAPI'


def lambda_handler(event, context):
    """Invoke BettingPicksAPI with a synthetic API Gateway event for major-race-analysis/run."""
    date_str = event.get('date', 'unknown')
    print(f'[sf_major_analysis] Starting weekly major-race analysis for week of {date_str}')

    lam = boto3.client('lambda', region_name=REGION)

    # Build a synthetic API Gateway event that the BettingPicksAPI handler understands
    api_event = {
        'httpMethod': 'POST',
        'path': '/api/major-race-analysis/run',
        'headers': {},
        'body': '{}',
        'source': 'scheduled-major-analysis',  # bypass admin auth check
    }

    resp = lam.invoke(
        FunctionName=API_LAMBDA_NAME,
        InvocationType='RequestResponse',
        Payload=json.dumps(api_event),
    )

    payload = json.loads(resp['Payload'].read().decode('utf-8'))
    status = payload.get('statusCode', 500)
    body = json.loads(payload.get('body', '{}'))

    print(f'[sf_major_analysis] API response: status={status}, body={json.dumps(body)[:500]}')

    if status == 200 and body.get('success'):
        analysed = body.get('analysed', [])
        return {
            'success': True,
            'races_analysed': len(analysed),
            'message': body.get('message', f'Analysed {len(analysed)} races'),
            'date': date_str,
        }
    else:
        raise Exception(f"Major race analysis failed: {body.get('error', 'Unknown error')}")

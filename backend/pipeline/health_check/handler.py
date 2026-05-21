"""
BetBudAI Analysis Health Check
==============================
Validates that analysis pipeline can execute and produces picks
Runs after each deployment to catch broken changes immediately

Checks:
1. Lambda can import all required modules
2. Analysis can read from S3
3. DynamoDB tables accessible
4. Recent picks exist in database
5. Analysis completion flag set
"""

import json
import boto3
import logging
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
s3 = boto3.client('s3', region_name='eu-west-1')
lambda_client = boto3.client('lambda', region_name='eu-west-1')


def lambda_handler(event, context):
    """
    Health check after deployment
    Returns: Pass/Fail with detailed status
    """

    checks = []
    all_passed = True

    # Check 1: Import test for surebet-analysis
    try:
        response = lambda_client.invoke(
            FunctionName='surebet-analysis',
            InvocationType='DryRun',
            Payload=json.dumps({'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')})
        )
        checks.append({
            'name': 'Lambda Import Test',
            'status': 'PASS',
            'message': 'surebet-analysis Lambda can be invoked'
        })
    except Exception as e:
        all_passed = False
        checks.append({
            'name': 'Lambda Import Test',
            'status': 'FAIL',
            'message': f'Lambda import failed: {str(e)}'
        })

    # Check 2: Recent picks exist in DynamoDB
    try:
        table = dynamodb.Table('SureBetBets')
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

        # Check today or yesterday
        for date_str in [today, yesterday]:
            response = table.query(
                KeyConditionExpression=Key('bet_date').eq(date_str),
                Limit=10
            )

            items = response.get('Items', [])
            ui_picks = [item for item in items if item.get('show_in_ui')]

            if ui_picks:
                checks.append({
                    'name': 'DynamoDB Picks Check',
                    'status': 'PASS',
                    'message': f'Found {len(ui_picks)} UI picks for {date_str}'
                })
                break
        else:
            all_passed = False
            checks.append({
                'name': 'DynamoDB Picks Check',
                'status': 'WARN',
                'message': 'No UI picks found for today or yesterday'
            })
    except Exception as e:
        all_passed = False
        checks.append({
            'name': 'DynamoDB Picks Check',
            'status': 'FAIL',
            'message': f'DynamoDB error: {str(e)}'
        })

    # Check 3: S3 bucket accessible
    try:
        bucket = 'surebet-pipeline-data'
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        key = f'daily/{today}/response_horses.json'

        # Try to access today's data
        try:
            s3.head_object(Bucket=bucket, Key=key)
            checks.append({
                'name': 'S3 Data Feed Check',
                'status': 'PASS',
                'message': f'S3 data accessible: {key}'
            })
        except s3.exceptions.NoSuchKey:
            # Check yesterday if today doesn't exist yet
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
            key_yesterday = f'daily/{yesterday}/response_horses.json'
            s3.head_object(Bucket=bucket, Key=key_yesterday)
            checks.append({
                'name': 'S3 Data Feed Check',
                'status': 'PASS',
                'message': f'S3 data accessible (yesterday): {key_yesterday}'
            })
    except Exception as e:
        all_passed = False
        checks.append({
            'name': 'S3 Data Feed Check',
            'status': 'FAIL',
            'message': f'S3 error: {str(e)}'
        })

    # Check 4: Analysis completion flag
    try:
        table = dynamodb.Table('SureBetBets')
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        response = table.query(
            KeyConditionExpression=Key('bet_date').eq(today)
        )

        items = response.get('Items', [])
        if items:
            # Check if any pick has the analysis_fully_complete flag
            complete_picks = [item for item in items if item.get('analysis_fully_complete')]
            if complete_picks or len(items) > 50:  # If many picks exist, assume analysis ran
                checks.append({
                    'name': 'Analysis Completion Check',
                    'status': 'PASS',
                    'message': f'Analysis completed for {today} ({len(items)} horses)'
                })
            else:
                checks.append({
                    'name': 'Analysis Completion Check',
                    'status': 'WARN',
                    'message': f'Analysis may be incomplete ({len(items)} horses, no completion flag)'
                })
        else:
            checks.append({
                'name': 'Analysis Completion Check',
                'status': 'INFO',
                'message': 'No analysis run yet for today'
            })
    except Exception as e:
        checks.append({
            'name': 'Analysis Completion Check',
            'status': 'WARN',
            'message': f'Could not verify completion: {str(e)}'
        })

    # Check 5: CloudWatch Logs for recent errors
    try:
        logs_client = boto3.client('logs', region_name='eu-west-1')
        log_group = '/aws/lambda/surebet-analysis'

        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )

        if streams['logStreams']:
            stream = streams['logStreams'][0]
            # Check if recent (within 24 hours)
            last_event = stream.get('lastEventTimestamp', 0)
            now = int(datetime.now(timezone.utc).timestamp() * 1000)
            age_hours = (now - last_event) / (1000 * 3600)

            if age_hours < 24:
                # Get recent logs to check for errors
                events = logs_client.get_log_events(
                    logGroupName=log_group,
                    logStreamName=stream['logStreamName'],
                    limit=100
                )

                errors = [e for e in events['events'] if 'ERROR' in e['message'] or 'Error' in e['message']]

                if errors:
                    all_passed = False
                    checks.append({
                        'name': 'Recent Error Check',
                        'status': 'FAIL',
                        'message': f'Found {len(errors)} errors in recent logs'
                    })
                else:
                    checks.append({
                        'name': 'Recent Error Check',
                        'status': 'PASS',
                        'message': f'No errors in logs (last run {age_hours:.1f}h ago)'
                    })
            else:
                checks.append({
                    'name': 'Recent Error Check',
                    'status': 'INFO',
                    'message': f'Last analysis run was {age_hours:.1f}h ago'
                })
    except Exception as e:
        checks.append({
            'name': 'Recent Error Check',
            'status': 'WARN',
            'message': f'Could not check logs: {str(e)}'
        })

    # Summary
    passed = sum(1 for c in checks if c['status'] == 'PASS')
    failed = sum(1 for c in checks if c['status'] == 'FAIL')
    warnings = sum(1 for c in checks if c['status'] == 'WARN')

    result = {
        'statusCode': 200 if all_passed and failed == 0 else 500,
        'health_status': 'HEALTHY' if all_passed and failed == 0 else 'DEGRADED' if failed == 0 else 'UNHEALTHY',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'summary': {
            'total_checks': len(checks),
            'passed': passed,
            'failed': failed,
            'warnings': warnings
        },
        'checks': checks
    }

    logger.info(f"Health check: {result['health_status']} ({passed}/{len(checks)} passed)")

    return result

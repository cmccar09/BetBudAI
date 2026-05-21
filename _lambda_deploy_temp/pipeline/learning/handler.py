"""
Lambda handler for learning pipeline.
Runs at 22:00 UTC daily and orchestrates surebet functions:
  1. surebet-learning
  2. surebet-cache-roi
"""

import json
import boto3
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client('lambda', region_name='eu-west-1')

PIPELINE_FUNCTIONS = [
    ('surebet-learning', 'Run learning cycle and recalibrate weights'),
    ('surebet-cache-roi', 'Cache updated ROI summary after weight changes'),
]


def _invoke(function_name: str, payload: dict) -> dict:
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload).encode(),
    )
    body = response['Payload'].read()
    status = response.get('StatusCode', 0)
    result = json.loads(body) if body else {}
    if response.get('FunctionError'):
        raise RuntimeError(f"{function_name} returned error: {result}")
    return {'status': status, 'result': result}


def lambda_handler(event, context):
    """Learning pipeline orchestrator."""
    try:
        logger.info(f"Learning pipeline triggered: {json.dumps(event)}")

        stage = event.get('stage', 'learning')
        target_date = event.get('target_date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        min_samples = event.get('min_samples', 10)

        base_payload = {'target_date': target_date, 'min_samples': min_samples}
        results = {}
        errors = []

        for fn_name, description in PIPELINE_FUNCTIONS:
            logger.info(f"[{fn_name}] {description}")
            try:
                results[fn_name] = _invoke(fn_name, base_payload)
                logger.info(f"[{fn_name}] OK (status={results[fn_name]['status']})")
            except Exception as exc:
                logger.error(f"[{fn_name}] FAILED: {exc}", exc_info=True)
                errors.append({'function': fn_name, 'error': str(exc)})

        success = len(errors) == 0
        return {
            'statusCode': 200 if success else 207,
            'body': json.dumps({
                'message': 'Learning pipeline complete' if success else 'Learning pipeline completed with errors',
                'stage': stage,
                'target_date': target_date,
                'steps_ok': len(results) - len(errors),
                'steps_failed': len(errors),
                'errors': errors,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            })
        }

    except Exception as e:
        logger.error(f"Learning pipeline failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e), 'stage': event.get('stage', 'learning')})
        }

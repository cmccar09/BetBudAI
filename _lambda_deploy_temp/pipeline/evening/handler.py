"""
Lambda handler for evening pipeline.
Runs at 20:00 UTC daily and orchestrates surebet functions:
  1. surebet-sl-results
  2. surebet-fav-results
  3. surebet-results-fetch
  4. surebet-loss-report
  5. surebet-cache-roi
  
Also runs optional analysis steps:
  - evening-miss-analysis: Analyze model misses from yesterday
"""

import json
import boto3
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client('lambda', region_name='eu-west-1')

PIPELINE_FUNCTIONS = [
    ('surebet-sl-results', 'Fetch race results from Sporting Life'),
    ('surebet-fav-results', 'Update fav/form stats'),
    ('surebet-results-fetch', 'Fetch Betfair SP and settlement prices'),
    ('surebet-loss-report', 'Generate P&L report and send email'),
    ('surebet-cache-roi', 'Cache ROI summary to DynamoDB'),
]

OPTIONAL_ANALYSIS_FUNCTIONS = [
    ('evening-miss-analysis', 'Analyze model misses and identify improvement patterns'),
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


def _invoke_optional(function_name: str, payload: dict) -> dict:
    """Invoke optional analysis functions without failing the whole pipeline."""
    try:
        return _invoke(function_name, payload)
    except lambda_client.exceptions.ResourceNotFoundException:
        logger.warning(f"[{function_name}] SKIPPED: function not deployed yet")
        return {'status': 0, 'result': {'skipped': True, 'reason': 'function_not_deployed'}}
    except Exception as exc:
        logger.warning(f"[{function_name}] SKIPPED: {exc}")
        return {'status': 0, 'result': {'skipped': True, 'reason': str(exc)}}


def lambda_handler(event, context):
    """Evening pipeline orchestrator."""
    try:
        logger.info(f"Evening pipeline triggered: {json.dumps(event)}")

        stage = event.get('stage', 'evening')
        target_date = event.get('target_date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        send_email = event.get('send_email', True)
        run_analysis = event.get('run_analysis', True)

        base_payload = {'target_date': target_date, 'send_email': send_email}
        results = {}
        errors = []
        analysis_results = {}

        for fn_name, description in PIPELINE_FUNCTIONS:
            logger.info(f"[{fn_name}] {description}")
            try:
                results[fn_name] = _invoke(fn_name, base_payload)
                logger.info(f"[{fn_name}] OK (status={results[fn_name]['status']})")
            except Exception as exc:
                logger.error(f"[{fn_name}] FAILED: {exc}", exc_info=True)
                errors.append({'function': fn_name, 'error': str(exc)})

        # Optional analysis steps
        if run_analysis:
            analysis_payload = {
                'target_date': target_date,
                'store_insights': True,
            }
            
            for fn_name, description in OPTIONAL_ANALYSIS_FUNCTIONS:
                logger.info(f"[{fn_name}] {description}")
                analysis_results[fn_name] = _invoke_optional(fn_name, analysis_payload)
        else:
            logger.info("Optional analysis steps disabled by event.run_analysis=false")

        success = len(errors) == 0
        return {
            'statusCode': 200 if success else 207,
            'body': json.dumps({
                'message': 'Evening pipeline complete' if success else 'Evening pipeline completed with errors',
                'stage': stage,
                'target_date': target_date,
                'steps_ok': len(results) - len(errors),
                'steps_failed': len(errors),
                'errors': errors,
                'analysis_steps': analysis_results,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            })
        }

    except Exception as e:
        logger.error(f"Evening pipeline failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e), 'stage': event.get('stage', 'evening')})
        }

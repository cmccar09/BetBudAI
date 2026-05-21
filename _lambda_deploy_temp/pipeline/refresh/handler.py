"""
Lambda handler for refresh pipeline
Runs at 12:00, 14:00, 16:00, 18:00 UTC daily — orchestrates surebet-* Lambda functions:
  1. surebet-betfair-fetch    — refresh live Betfair odds
  2. surebet-analysis         — re-score with updated odds
  3. surebet-validate         — re-validate picks
  4. surebet-featured-meeting — update featured meeting
  5. surebet-sl-results       — check for newly settled races
  6. surebet-fav-results      — update form/fav stats
"""

import json
import boto3
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')


lambda_client = boto3.client('lambda', region_name='eu-west-1')

PIPELINE_FUNCTIONS = [
    ('surebet-betfair-fetch',    'Refresh live Betfair odds'),
    ('surebet-analysis',         'Re-score horses with updated odds'),
    ('surebet-validate',         'Re-validate picks'),
    ('surebet-featured-meeting', 'Update featured meeting analysis'),
    ('surebet-sl-results',       'Check for newly settled races'),
    ('surebet-fav-results',      'Update form/fav stats'),
]

# Optional optimization checks are non-blocking for intraday refresh cycles.
OPTIONAL_OPTIMIZATION_FUNCTIONS = [
    ('compare-race-fields', 'Detect nonrunner/field changes before post-refresh picks'),
]


def _parse_result_payload(result_obj: dict) -> dict:
    """Normalize lambda payloads that may return nested JSON in body."""
    if not isinstance(result_obj, dict):
        return {}
    body = result_obj.get('body')
    if isinstance(body, str):
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return result_obj
    return result_obj


def _extract_runner_list(payload: dict, candidates: list[str]) -> list:
    for key in candidates:
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _build_compare_payload(results: dict, target_date: str, refresh_hour: int) -> dict:
    betfair_raw = (results.get('surebet-betfair-fetch') or {}).get('result') or {}
    analysis_raw = (results.get('surebet-analysis') or {}).get('result') or {}
    betfair_data = _parse_result_payload(betfair_raw)
    analysis_data = _parse_result_payload(analysis_raw)

    current_field = _extract_runner_list(
        betfair_data,
        ['current_betfair_field', 'runners', 'field', 'market_runners']
    )
    model_field = _extract_runner_list(
        analysis_data,
        ['model_field', 'all_horses', 'runners', 'race_field']
    )

    payload = {
        'target_date': target_date,
        'refresh_hour': refresh_hour,
        'market_id': betfair_data.get('market_id') or analysis_data.get('market_id'),
        'course': betfair_data.get('course') or analysis_data.get('course'),
        'race_time': betfair_data.get('race_time') or analysis_data.get('race_time'),
        'change_threshold_pct': 15,
        'current_betfair_field': current_field,
        'model_field': model_field,
    }

    payload['payload_complete'] = bool(current_field) and bool(model_field)
    payload['payload_status'] = {
        'current_field_count': len(current_field),
        'model_field_count': len(model_field),
        'has_market_id': bool(payload.get('market_id')),
        'has_course': bool(payload.get('course')),
        'has_race_time': bool(payload.get('race_time')),
    }
    return payload


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
    """Invoke optional optimization functions without failing the refresh run."""
    try:
        return _invoke(function_name, payload)
    except lambda_client.exceptions.ResourceNotFoundException:
        logger.warning(f"[{function_name}] SKIPPED: function not deployed yet")
        return {'status': 0, 'result': {'skipped': True, 'reason': 'function_not_deployed'}}
    except Exception as exc:
        logger.warning(f"[{function_name}] SKIPPED: {exc}")
        return {'status': 0, 'result': {'skipped': True, 'reason': str(exc)}}


def lambda_handler(event, context):
    """
    Refresh pipeline orchestrator
    
    Event payload:
    {
        "stage": "refresh",
        "refresh_hour": 12,
        "target_date": "2026-05-09"
    }
    """
    
    try:
        logger.info(f"Refresh pipeline triggered: {json.dumps(event)}")
        
        stage = event.get('stage', 'refresh')
        refresh_hour = event.get('refresh_hour', 12)
        target_date = event.get('target_date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        run_optimizations = event.get('run_optimizations', True)
        
        base_payload = {'target_date': target_date, 'refresh_hour': refresh_hour}
        results = {}
        errors = []
        optimization_results = {}

        for fn_name, description in PIPELINE_FUNCTIONS:
            logger.info(f"[{fn_name}] {description}")
            try:
                results[fn_name] = _invoke(fn_name, base_payload)
                logger.info(f"[{fn_name}] OK (status={results[fn_name]['status']})")
            except Exception as exc:
                logger.error(f"[{fn_name}] FAILED: {exc}", exc_info=True)
                errors.append({'function': fn_name, 'error': str(exc)})

        if run_optimizations:
            optimization_payload = {
                'target_date': target_date,
                'refresh_hour': refresh_hour,
                'stage': stage,
                'source': 'betbudai-refresh',
            }

            compare_payload = _build_compare_payload(results, target_date, refresh_hour)
            logger.info("[compare-race-fields] Detect nonrunner/field changes before post-refresh picks")
            compare_result = _invoke_optional('compare-race-fields', compare_payload)
            optimization_results['compare-race-fields'] = compare_result
            optimization_results['compare_payload_status'] = compare_payload.get('payload_status', {})
            optimization_results['compare_payload_complete'] = compare_payload.get('payload_complete', False)

            compare_data = _parse_result_payload(compare_result.get('result') or {})
            should_reanalyze = bool(compare_data.get('should_reanalyze')) and bool(compare_payload.get('payload_complete'))

            if should_reanalyze:
                logger.warning("[forced-reanalysis] Triggered during refresh cycle")
                reanalysis_payload = {
                    'target_date': target_date,
                    'refresh_hour': refresh_hour,
                    'force': True,
                    'force_reanalysis': True,
                    'reanalysis_reason': 'field_change_detected',
                    'field_compare': compare_data,
                    'current_betfair_field': compare_payload.get('current_betfair_field', []),
                    'model_field': compare_payload.get('model_field', []),
                    'market_id': compare_payload.get('market_id'),
                    'course': compare_payload.get('course'),
                    'race_time': compare_payload.get('race_time'),
                }
                reanalysis_result = _invoke_optional('surebet-analysis', reanalysis_payload)
                revalidate_result = _invoke_optional('surebet-validate', {'target_date': target_date, 'force': True})
                optimization_results['forced_reanalysis'] = {
                    'triggered': True,
                    'analysis': reanalysis_result,
                    'validate': revalidate_result,
                }
            else:
                optimization_results['forced_reanalysis'] = {
                    'triggered': False,
                    'reason': 'incomplete_field_payload' if not compare_payload.get('payload_complete') else 'no_significant_field_change',
                }
        else:
            logger.info("Optional optimization steps disabled by event.run_optimizations=false")

        success = len(errors) == 0
        return {
            'statusCode': 200 if success else 207,
            'body': json.dumps({
                'message': f'Refresh pipeline at {refresh_hour}:00 complete' if success else f'Refresh at {refresh_hour}:00 completed with errors',
                'stage': stage,
                'target_date': target_date,
                'steps_ok': len(results) - len(errors),
                'steps_failed': len(errors),
                'errors': errors,
                'optimizations_requested': run_optimizations,
                'optimization_steps': optimization_results,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            })
        }
    
    except Exception as e:
        logger.error(f"Refresh pipeline failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e), 'stage': event.get('stage', 'refresh')})
        }

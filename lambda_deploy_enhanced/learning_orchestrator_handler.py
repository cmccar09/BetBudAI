"""
Learning Orchestrator Lambda Handler
=====================================
AWS Lambda function that orchestrates the automated learning pipeline.
Designed to be invoked by the evening pipeline after results are settled.

Deployment:
- Runtime: Python 3.11
- Timeout: 600 seconds (10 minutes)
- Memory: 1024 MB
- Environment Variables:
  - CONFIDENCE_THRESHOLD: 0.80 (default)
  - ENABLE_AUTO_DEPLOY: true
  - DRY_RUN: false
  - MAX_WORKERS: 10
"""

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda handler for learning orchestrator.

    Event schema:
    {
        "target_date": "2026-05-20",  # Date to analyze
        "learning_confidence_threshold": 0.80,  # Optional
        "learning_auto_deploy": true,  # Optional
        "learning_dry_run": false,  # Optional
        "learning_max_races": 50  # Optional
    }

    Returns:
    {
        "statusCode": 200,
        "body": {
            "status": "success",
            "session_id": "LEARN_2026-05-20_211500",
            "target_date": "2026-05-20",
            "races_analyzed": 15,
            "insights_generated": 12,
            "patterns_detected": 4,
            "adjustments_proposed": 6,
            "adjustments_deployed": 3,
            "high_confidence_adjustments": [...],
            "dry_run": false
        }
    }
    """
    try:
        logger.info(f"[LearningOrchestrator] Invoked with event: {json.dumps(event)}")

        # Import here to avoid Lambda cold start issues
        from backend.pipeline.evening.learning_integration import invoke_learning_orchestrator

        # Extract parameters
        target_date = event.get('target_date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))

        # Override with environment variables if set
        learning_event = {
            'learning_confidence_threshold': float(
                os.getenv('CONFIDENCE_THRESHOLD', event.get('learning_confidence_threshold', 0.80))
            ),
            'learning_auto_deploy': os.getenv('ENABLE_AUTO_DEPLOY', 'true').lower() == 'true',
            'learning_dry_run': os.getenv('DRY_RUN', 'false').lower() == 'true',
            'learning_max_races': int(
                os.getenv('MAX_RACES', event.get('learning_max_races', 50))
            )
        }

        # Merge with event
        learning_event.update({
            k: v for k, v in event.items()
            if k.startswith('learning_')
        })

        logger.info(
            f"[LearningOrchestrator] Configuration: "
            f"confidence_threshold={learning_event['learning_confidence_threshold']}, "
            f"auto_deploy={learning_event['learning_auto_deploy']}, "
            f"dry_run={learning_event['learning_dry_run']}"
        )

        # Invoke learning integrator
        results = invoke_learning_orchestrator(target_date, learning_event)

        # Log summary
        if results.get('status') == 'success':
            logger.info(
                f"[LearningOrchestrator] SUCCESS: "
                f"Analyzed {results.get('races_analyzed', 0)} races, "
                f"deployed {results.get('adjustments_deployed', 0)} adjustments"
            )
        else:
            logger.warning(
                f"[LearningOrchestrator] {results.get('status', 'unknown').upper()}: "
                f"{results.get('reason', results.get('error', 'unknown'))}"
            )

        return {
            'statusCode': 200 if results.get('status') == 'success' else 207,
            'body': json.dumps(results)
        }

    except Exception as e:
        logger.error(f"[LearningOrchestrator] FAILED: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e),
                'target_date': event.get('target_date', 'unknown')
            })
        }


def test_invoke_local():
    """Test function for local development."""
    from datetime import datetime, timezone, timedelta

    # Test with yesterday's data
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

    test_event = {
        'target_date': yesterday,
        'learning_confidence_threshold': 0.80,
        'learning_auto_deploy': False,  # Dry run for testing
        'learning_dry_run': True,
        'learning_max_races': 10
    }

    class MockContext:
        function_name = "betbudai-learning-orchestrator"
        invoked_function_arn = "arn:aws:lambda:eu-west-1:123456789012:function:betbudai-learning-orchestrator"

    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    # For local testing
    test_invoke_local()

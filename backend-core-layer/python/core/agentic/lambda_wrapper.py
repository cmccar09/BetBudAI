"""
Lambda wrapper for agentic parallel orchestrator.
Invoked by Step Functions to run agentic orchestrator before canonical analysis.
"""
import json
import subprocess
import os
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PIPELINE_BUCKET = os.environ.get('PIPELINE_BUCKET', 'surebet-pipeline-data')


def _resolve_s3_location(raw_s3_key: str):
    value = str(raw_s3_key or '').strip()
    if not value:
        return None, None
    if value.startswith('s3://'):
        parts = value.split('/', 3)
        if len(parts) < 4 or not parts[2] or not parts[3]:
            return None, None
        return parts[2], parts[3]
    return PIPELINE_BUCKET, value.lstrip('/')

def lambda_handler(event, context):
    """
    Handler: Executes agentic parallel orchestrator on fetched horse data.
    
    Input event:
        {
            "date": "2026-04-26",
            "s3_key": "s3://betbudai-racing-data/horses/2026-04-26.json",
            "race_count": 22
        }
    
    Returns:
        {
            "agentic_executed": true,
            "races_processed": 22,
            "avg_confidence": 87.47,
            "duration_seconds": 1.83,
            "status": "success",
            "timestamp": "2026-04-26T10:38:59Z"
        }
    """
    try:
        date = event.get('date', '')
        s3_key = event.get('s3_key', '')
        race_count = event.get('race_count', 0)
        
        logger.info(f"AGENTIC_WRAPPER_INVOKED date={date} races={race_count} s3_key={s3_key}")
        
        bucket, key = _resolve_s3_location(s3_key)

        # Validate s3_key
        if not bucket or not key:
            logger.warning(f"Invalid s3_key: {s3_key}, checking for local response_horses.json")
            local_input = '/tmp/response_horses.json'
            if not os.path.exists(local_input):
                raise ValueError(f"Invalid s3_key and no local response_horses.json found")
        else:
            # Set environment variables for orchestrator
            os.environ['AGENTIC_DISABLE_BETTING_ACTIONS'] = '1'  # Safety gate
            os.environ['AGENTIC_CW_METRICS_ENABLED'] = '1'
            os.environ['AGENTIC_CW_NAMESPACE'] = 'BetBudAI/Agentic'
            
            # Download the response_horses.json from S3
            s3 = boto3.client('s3')
            try:
                local_input = f"/tmp/response_horses_{date}.json"
                logger.info(f"Downloading race input from S3 (bucket={bucket}, key={key})...")
                s3.download_file(bucket, key, local_input)
            except Exception as s3_err:
                logger.error(f"S3 download failed: {str(s3_err)}, trying local file")
                local_input = '/tmp/response_horses.json'
                if not os.path.exists(local_input):
                    raise
        
        # Set environment variables if not already set
        if 'AGENTIC_DISABLE_BETTING_ACTIONS' not in os.environ:
            os.environ['AGENTIC_DISABLE_BETTING_ACTIONS'] = '1'
        if 'AGENTIC_CW_METRICS_ENABLED' not in os.environ:
            os.environ['AGENTIC_CW_METRICS_ENABLED'] = '1'
        if 'AGENTIC_CW_NAMESPACE' not in os.environ:
            os.environ['AGENTIC_CW_NAMESPACE'] = 'BetBudAI/Agentic'

        # The job-state table is optional telemetry. Clear it so missing IAM does
        # not block the fail-open agentic analysis path in production.
        os.environ.pop('AGENTIC_JOB_TABLE', None)
        
        local_output = f"/tmp/agentic_output_{date}.json"
        
        # Execute orchestrator
        logger.info(f"Starting orchestrator with {race_count} races...")
        cmd = [
            'python3',
            'agentic_parallel_orchestrator.py',
            '--input', local_input,
            '--output', local_output,
            '--region', 'eu-west-1'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        logger.info(f"Orchestrator stdout:\n{result.stdout}")
        if result.returncode != 0:
            logger.error(f"Orchestrator stderr:\n{result.stderr}")
            raise RuntimeError(f"Orchestrator failed: {result.stderr}")
        
        # Parse metrics from output
        output_lines = result.stdout.split('\n')
        metrics = {'status': 'success', 'timestamp': datetime.utcnow().isoformat() + 'Z'}
        
        for line in output_lines:
            if 'AGENTIC_ORCHESTRATION_COMPLETE' in line:
                parts = line.split()
                for part in parts:
                    if part.startswith('races='):
                        metrics['races_processed'] = int(part.split('=')[1])
                    elif part.startswith('completed='):
                        metrics['completed'] = int(part.split('=')[1])
                    elif part.startswith('failed='):
                        metrics['failed'] = int(part.split('=')[1])
            elif 'AGENTIC_ORCHESTRATION_SUMMARY' in line:
                parts = line.split()
                for part in parts:
                    if part.startswith('avg_race_latency_s='):
                        metrics['avg_latency_seconds'] = float(part.split('=')[1])
                    elif part.startswith('p95_race_latency_s='):
                        metrics['p95_latency_seconds'] = float(part.split('=')[1])
                    elif part.startswith('avg_confidence='):
                        metrics['avg_confidence'] = float(part.split('=')[1])
                    elif part.startswith('failure_rate_pct='):
                        metrics['failure_rate_pct'] = float(part.split('=')[1])
        
        metrics['agentic_executed'] = True
        metrics['duration_seconds'] = metrics.get('avg_latency_seconds', 0)
        
        logger.info(f"AGENTIC_WRAPPER_COMPLETE metrics={json.dumps(metrics)}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"AGENTIC_WRAPPER_ERROR: {str(e)}", exc_info=True)
        return {
            'agentic_executed': False,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

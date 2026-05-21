#!/usr/bin/env python3
"""
AWS Lambda handler for betting workflow trigger
This is a placeholder that returns success - actual workflow runs on your laptop
"""
import json
from datetime import datetime

def lambda_handler(event, context):
    """
    Workflow trigger endpoint
    Returns success to indicate trigger was received
    """
    print(f"Workflow trigger received at {datetime.utcnow().isoformat()}")
    print(f"Event: {json.dumps(event)}")
    
    return {
        'statusCode': 202,
        'body': json.dumps({
            'success': True,
            'message': 'Workflow trigger received',
            'timestamp': datetime.utcnow().isoformat(),
            'info': 'The workflow is scheduled to run hourly. New picks will appear within 60-90 minutes.'
        })
    }

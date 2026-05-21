"""
Deployment orchestrator for Lambda functions and Step Functions.
This replaces the old deploy_step_functions.py with improved modularity and safety.
"""

import os
import json
import boto3
import zipfile
import tempfile
import shutil
from pathlib import Path

# Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'eu-west-1')
LAMBDA_RUNTIME = 'python3.11'
LAMBDA_TIMEOUT = 300
LAMBDA_MEMORY = 512

# Lambda configurations
LAMBDAS = [
    {
        'name': 'betbudai-fetch-betfair',
        'handler': 'handler.lambda_handler',
        'timeout': 120,
        'memory': 256,
    },
    {
        'name': 'betbudai-analysis',
        'handler': 'handler.lambda_handler',
        'timeout': 600,
        'memory': 512,
    },
    {
        'name': 'betbudai-fetch-results',
        'handler': 'handler.lambda_handler',
        'timeout': 120,
        'memory': 256,
    },
    {
        'name': 'betbudai-learning',
        'handler': 'handler.lambda_handler',
        'timeout': 300,
        'memory': 256,
    },
]


def create_lambda_zip(lambda_dir: str, zip_path: str) -> bool:
    """Create deployment ZIP for Lambda."""
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(lambda_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, lambda_dir)
                        zf.write(file_path, arcname)
        
        size_mb = os.path.getsize(zip_path) / 1024 / 1024
        print(f"✓ Created {zip_path} ({size_mb:.2f} MB)")
        return True
    except Exception as e:
        print(f"✗ Error creating ZIP: {e}")
        return False


def deploy_lambda(lambda_config: dict) -> bool:
    """Deploy a Lambda function."""
    try:
        client = boto3.client('lambda', region_name=AWS_REGION)
        
        lambda_name = lambda_config['name']
        zip_path = f"/tmp/{lambda_name}.zip"
        
        # Create ZIP
        pipeline_dir = os.path.join(os.path.dirname(__file__), f"pipeline/{lambda_name}")
        if not create_lambda_zip(pipeline_dir, zip_path):
            return False
        
        # Read ZIP
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        # Try to update existing function
        try:
            response = client.update_function_code(
                FunctionName=lambda_name,
                ZipFile=zip_content,
            )
            print(f"✓ Updated Lambda: {lambda_name} (v{response['Version']})")
            return True
        except client.exceptions.ResourceNotFoundException:
            # Function doesn't exist, create it
            response = client.create_function(
                FunctionName=lambda_name,
                Runtime=LAMBDA_RUNTIME,
                Role=f"arn:aws:iam::ACCOUNT_ID:role/lambda-role",
                Handler=lambda_config['handler'],
                Code={'ZipFile': zip_content},
                Timeout=lambda_config['timeout'],
                MemorySize=lambda_config['memory'],
                Description=f"BetBudAI {lambda_name}",
            )
            print(f"✓ Created Lambda: {lambda_name}")
            return True
    
    except Exception as e:
        print(f"✗ Error deploying {lambda_config['name']}: {e}")
        return False


def deploy_all():
    """Deploy all Lambda functions."""
    print("=" * 60)
    print("BetBudAI Lambda Deployment")
    print("=" * 60)
    
    for lambda_config in LAMBDAS:
        deploy_lambda(lambda_config)
    
    print("=" * 60)
    print("Deployment complete!")


if __name__ == '__main__':
    deploy_all()

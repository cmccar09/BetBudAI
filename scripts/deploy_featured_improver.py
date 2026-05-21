#!/usr/bin/env python3
"""Deploy featured improver enforcer Lambda."""

import boto3
import json
import zipfile
import io
import os
import time
from pathlib import Path

s3 = boto3.client('s3', region_name='eu-west-1')
lc = boto3.client('lambda', region_name='eu-west-1')
iam = boto3.client('iam', region_name='eu-west-1')

LAMBDA_NAME = 'featured-improver-enforcer'
LAMBDA_ROLE = 'betbudai-lambda-execution-role'
LAMBDA_TIMEOUT = 60
LAMBDA_MEMORY = 256

def _get_role_arn():
    """Get the ARN of the Lambda execution role."""
    try:
        role = iam.get_role(RoleName=LAMBDA_ROLE)
        return role['Role']['Arn']
    except Exception:
        # Fallback to alternate role name
        try:
            role = iam.get_role(RoleName='SureBetLambdaRole')
            return role['Role']['Arn']
        except Exception as e:
            print(f"Error getting role: {e}")
            raise


def _create_zip(source_dir):
    """Create a zip file from source directory."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zf.write(file_path, arcname)
    zip_buffer.seek(0)
    return zip_buffer.read()


def deploy_lambda():
    """Deploy featured-improver-enforcer Lambda."""
    
    print(f"Deploying {LAMBDA_NAME}...")
    
    # Get role ARN
    role_arn = _get_role_arn()
    print(f"  Using role: {role_arn}")
    
    # Create zip
    source_dir = r'backend\pipeline\optimizations\featured_improver_enforcer'
    zip_data = _create_zip(source_dir)
    print(f"  Package size: {len(zip_data) / 1024 / 1024:.2f} MB")
    
    # Deploy
    try:
        # Try to update existing function
        lc.update_function_code(
            FunctionName=LAMBDA_NAME,
            ZipFile=zip_data
        )
        print(f"  Code updated: {LAMBDA_NAME}")
    except lc.exceptions.ResourceNotFoundException:
        # Function doesn't exist, create it
        response = lc.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime='python3.11',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Code={'ZipFile': zip_data},
            Timeout=LAMBDA_TIMEOUT,
            MemorySize=LAMBDA_MEMORY,
            Description='Apply improver boost to featured meeting picks',
        )
        print(f"  Created: {response['FunctionArn']}")
        # Wait for function to be active before updating config
        print(f"  Waiting for function to become active...")
        time.sleep(2)
    
    # Update configuration with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            lc.update_function_configuration(
                FunctionName=LAMBDA_NAME,
                Timeout=LAMBDA_TIMEOUT,
                MemorySize=LAMBDA_MEMORY,
                Description='Apply improver boost to featured meeting picks'
            )
            print(f"  Config updated: {LAMBDA_TIMEOUT}s timeout, {LAMBDA_MEMORY}MB memory")
            break
        except lc.exceptions.ResourceConflictException as e:
            if attempt < max_retries - 1:
                print(f"  Waiting for function to settle... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                raise
    
    # Get function info
    func = lc.get_function(FunctionName=LAMBDA_NAME)
    print(f"  ✓ {LAMBDA_NAME} [DEPLOYED]")
    print(f"    ARN: {func['Configuration']['FunctionArn']}")


if __name__ == '__main__':
    try:
        deploy_lambda()
        print("\n✓ Deployment complete")
    except Exception as e:
        print(f"\n✗ Deployment failed: {e}")
        import traceback
        traceback.print_exc()


#!/usr/bin/env python3
"""Deploy updated pipeline handlers with new analysis integration."""

import boto3
import zipfile
import os
import json
from pathlib import Path
import time

AWS_REGION = "eu-west-1"
s3_client = boto3.client("s3", region_name=AWS_REGION)
lambda_client = boto3.client("lambda", region_name=AWS_REGION)

# Updated pipeline handlers
HANDLERS = [
    {
        "name": "betbudai-morning",
        "handler": "handler.lambda_handler",
        "source_dir": "backend/pipeline/morning",
        "runtime": "python3.11",
        "timeout": 600,
        "memory": 512,
        "description": "Morning pipeline with improver boost enforcement and field change detection",
    },
    {
        "name": "betbudai-evening",
        "handler": "handler.lambda_handler",
        "source_dir": "backend/pipeline/evening",
        "runtime": "python3.11",
        "timeout": 600,
        "memory": 512,
        "description": "Evening pipeline with miss analysis",
    },
]


def _get_role_arn():
    """Get Lambda execution role."""
    iam_client = boto3.client("iam", region_name=AWS_REGION)
    try:
        role = iam_client.get_role(RoleName="betbudai-lambda-execution-role")
        return role["Role"]["Arn"]
    except:
        role = iam_client.get_role(RoleName="SureBetLambdaRole")
        return role["Role"]["Arn"]


def _create_zip(source_dir, zip_path):
    """Create a deployment zip from source directory."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zf.write(file_path, arcname)
    print(f"Created deployment zip: {zip_path}")


def deploy_handler(config, role_arn):
    """Deploy a pipeline handler Lambda."""
    lambda_name = config["name"]
    source_dir = config["source_dir"]
    handler = config["handler"]
    
    print(f"\n{'='*60}")
    print(f"Deploying: {lambda_name}")
    print(f"{'='*60}")
    
    # Create deployment zip
    zip_file = f"/tmp/{lambda_name}-deployment.zip"
    _create_zip(source_dir, zip_file)
    
    # Read zip file
    with open(zip_file, "rb") as f:
        zip_content = f.read()
    
    try:
        # Try to get existing function
        existing = lambda_client.get_function(FunctionName=lambda_name)
        print(f"Updating existing Lambda: {lambda_name}")
        
        response = lambda_client.update_function_code(
            FunctionName=lambda_name,
            ZipFile=zip_content,
        )
        print(f"  Code updated: {response['CodeSha256'][:12]}...")
        
        # Wait for code update to complete
        print("  Waiting for update to complete...")
        time.sleep(5)
        
        # Update configuration with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                lambda_client.update_function_configuration(
                    FunctionName=lambda_name,
                    Handler=handler,
                    Timeout=config.get("timeout", 60),
                    MemorySize=config.get("memory", 256),
                    Description=config.get("description", ""),
                )
                print(f"  Configuration updated")
                break
            except lambda_client.exceptions.ResourceConflictException:
                if attempt < max_retries - 1:
                    print(f"  Update in progress, retrying ({attempt+1}/{max_retries})...")
                    time.sleep(3)
                else:
                    print(f"  Skipping config update (update still in progress)")
                    break
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"Creating new Lambda: {lambda_name}")
        
        response = lambda_client.create_function(
            FunctionName=lambda_name,
            Runtime=config.get("runtime", "python3.11"),
            Role=role_arn,
            Handler=handler,
            Code={"ZipFile": zip_content},
            Timeout=config.get("timeout", 60),
            MemorySize=config.get("memory", 256),
            Description=config.get("description", ""),
            Environment={
                "Variables": {
                    "REGION": AWS_REGION,
                }
            },
        )
        print(f"  Function created: {response['FunctionArn']}")
    
    finally:
        # Cleanup
        if os.path.exists(zip_file):
            os.remove(zip_file)


def main():
    print("Pipeline Handler Deployment")
    print(f"Region: {AWS_REGION}")
    
    # Get role
    print("\n[1/2] Getting IAM role...")
    role_arn = _get_role_arn()
    print(f"Role ARN: {role_arn}")
    
    # Deploy each handler
    print(f"\n[2/2] Deploying {len(HANDLERS)} pipeline handlers...")
    for config in HANDLERS:
        deploy_handler(config, role_arn)
    
    print(f"\n{'='*60}")
    print("Deployment complete!")
    print("='*60}")
    
    print("\nDeployed Handlers:")
    for config in HANDLERS:
        print(f"  ✓ {config['name']}")
    
    print("\nNext: Run smoke tests on deployed handlers")


if __name__ == "__main__":
    main()

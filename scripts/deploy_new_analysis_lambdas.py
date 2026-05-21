#!/usr/bin/env python3
"""Deploy new optimization lambdas for improver boost enforcement and miss analysis."""

import boto3
import zipfile
import os
import json
from pathlib import Path

AWS_REGION = "eu-west-1"
s3_client = boto3.client("s3", region_name=AWS_REGION)
lambda_client = boto3.client("lambda", region_name=AWS_REGION)
iam_client = boto3.client("iam", region_name=AWS_REGION)

# Lambda configurations
LAMBDAS = [
    {
        "name": "apply-improver-boosted-picks",
        "handler": "handler.lambda_handler",
        "source_dir": "backend/pipeline/optimizations/improver_picks_enforcer",
        "runtime": "python3.11",
        "timeout": 60,
        "memory": 256,
        "description": "Enforce improver-boosted ranking as official picks",
    },
    {
        "name": "evening-miss-analysis",
        "handler": "miss_analysis_handler.lambda_handler",
        "source_dir": "backend/pipeline/evening",
        "runtime": "python3.11",
        "timeout": 300,
        "memory": 512,
        "description": "Analyze model misses and identify improvement patterns",
    },
]

ROLE_NAME = "betbudai-lambda-execution-role"


def _get_role_arn():
    """Get or create the Lambda execution role."""
    try:
        role = iam_client.get_role(RoleName=ROLE_NAME)
        print(f"Using existing role: {ROLE_NAME}")
        return role["Role"]["Arn"]
    except iam_client.exceptions.NoSuchEntityException:
        print(f"Role {ROLE_NAME} not found, trying SureBetLambdaRole...")
        try:
            role = iam_client.get_role(RoleName="SureBetLambdaRole")
            print(f"Using existing SureBetLambdaRole")
            return role["Role"]["Arn"]
        except Exception as e:
            print(f"Error getting role: {e}")
            raise


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


def deploy_lambda(config, role_arn):
    """Deploy a single Lambda function."""
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
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=lambda_name,
            Handler=handler,
            Timeout=config.get("timeout", 60),
            MemorySize=config.get("memory", 256),
            Description=config.get("description", ""),
        )
        print(f"  Configuration updated")
        
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
    print("BetBudAI Lambda Deployment Tool")
    print(f"Region: {AWS_REGION}")
    
    # Get or create role
    print("\n[1/3] Setting up IAM role...")
    role_arn = _get_role_arn()
    print(f"Role ARN: {role_arn}")
    
    # Deploy each Lambda
    print(f"\n[2/3] Deploying {len(LAMBDAS)} Lambda functions...")
    for config in LAMBDAS:
        deploy_lambda(config, role_arn)
    
    print(f"\n[3/3] Deployment complete!")
    print("\nDeployed Lambdas:")
    for config in LAMBDAS:
        print(f"  ✓ {config['name']}")
    
    print("\nNext steps:")
    print("  1. Verify functions deployed: aws lambda list-functions --region eu-west-1")
    print("  2. Test with smoke test")
    print("  3. Update EventBridge triggers if needed")


if __name__ == "__main__":
    main()

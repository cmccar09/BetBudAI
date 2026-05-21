#!/usr/bin/env python3
"""
BetBudAI Lambda Deployment Script
===================================
Deploys new BetBudAI Lambda functions to AWS.
These run alongside (and eventually replace) old surebet-* functions.

Usage:
  python deploy_lambdas.py                    # Deploy all
  python deploy_lambdas.py --function morning # Deploy one function
  python deploy_lambdas.py --dry-run          # Preview only

New functions (prefixed betbudai-*):
  betbudai-morning     - Morning pipeline (08:30 UTC)
  betbudai-refresh     - Refresh pipeline (12:00 14:00 16:00 18:00 UTC)
  betbudai-evening     - Evening results + settlement (20:00 UTC)
  betbudai-learning    - Weight optimization (22:00 UTC)
"""

import os
import sys
import json
import boto3
import zipfile
import argparse
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
AWS_REGION = os.environ.get('AWS_REGION', 'eu-west-1')
LAMBDA_ROLE_ARN = os.environ.get('LAMBDA_ROLE_ARN', 'arn:aws:iam::813281204422:role/SureBetLambdaRole')
LAMBDA_RUNTIME = 'python3.11'

ROOT_DIR = Path(__file__).parent.parent.parent  # BetBudAI/ root

LAMBDA_CONFIGS = {
    'morning': {
        'function_name': 'betbudai-morning',
        'description': 'BetBudAI morning pipeline - race fetch, scoring, picks (08:30 UTC)',
        'handler': 'handler.lambda_handler',
        'source_dir': ROOT_DIR / 'backend' / 'pipeline' / 'morning',
        'timeout': 600,
        'memory': 512,
        'environment': {
            'ENV': 'production',
            'DYNAMODB_TABLE': 'SureBetBets',
        }
    },
    'refresh': {
        'function_name': 'betbudai-refresh',
        'description': 'BetBudAI refresh pipeline - odds validation, featured meeting (12/14/16/18 UTC)',
        'handler': 'handler.lambda_handler',
        'source_dir': ROOT_DIR / 'backend' / 'pipeline' / 'refresh',
        'timeout': 300,
        'memory': 256,
        'environment': {
            'ENV': 'production',
            'DYNAMODB_TABLE': 'SureBetBets',
        }
    },
    'evening': {
        'function_name': 'betbudai-evening',
        'description': 'BetBudAI evening pipeline - results, settlement, P&L (20:00 UTC)',
        'handler': 'handler.lambda_handler',
        'source_dir': ROOT_DIR / 'backend' / 'pipeline' / 'evening',
        'timeout': 300,
        'memory': 256,
        'environment': {
            'ENV': 'production',
            'DYNAMODB_TABLE': 'SureBetBets',
        }
    },
    'learning': {
        'function_name': 'betbudai-learning',
        'description': 'BetBudAI learning pipeline - weight optimization (22:00 UTC)',
        'handler': 'handler.lambda_handler',
        'source_dir': ROOT_DIR / 'backend' / 'pipeline' / 'learning',
        'timeout': 600,
        'memory': 256,
        'environment': {
            'ENV': 'production',
            'DYNAMODB_TABLE': 'SureBetBets',
        }
    },
}


# ── ZIP Builder ───────────────────────────────────────────────────────────────

def create_lambda_zip(source_dir: Path, output_path: Path, include_core: bool = True) -> bool:
    """
    Create deployment ZIP for Lambda.
    Includes: handler files + core modules needed by handler.
    """
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            
            # 1. Add handler files
            if source_dir.exists():
                for file_path in source_dir.rglob('*.py'):
                    arcname = file_path.relative_to(source_dir)
                    zf.write(file_path, str(arcname))
                    print(f"   + {arcname}")
            else:
                print(f"   ⚠ Source dir not found: {source_dir}")
                return False
            
            # 2. Add shared core modules (config, database, utils)
            if include_core:
                core_dirs = ['config', 'database', 'utils']
                backend_dir = ROOT_DIR / 'backend'
                
                for core in core_dirs:
                    core_path = backend_dir / core
                    if core_path.exists():
                        for file_path in core_path.rglob('*.py'):
                            arcname = file_path.relative_to(backend_dir)
                            zf.write(file_path, str(arcname))
                            print(f"   + {arcname}")
        
        size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"   ✓ Created {output_path.name} ({size_mb:.2f} MB)")
        return True
    
    except Exception as e:
        print(f"   ✗ Error creating ZIP: {e}")
        return False


# ── Lambda Deployment ─────────────────────────────────────────────────────────

def deploy_function(config: dict, client, dry_run: bool = False) -> bool:
    """Deploy or update a Lambda function."""
    
    fn_name = config['function_name']
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Deploying {fn_name}...")
    
    # Create ZIP
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = Path(tmp_dir) / f"{fn_name}.zip"
        
        print(f"   Building ZIP from {config['source_dir'].name}/...")
        if not create_lambda_zip(config['source_dir'], zip_path):
            return False
        
        if dry_run:
            print(f"   [DRY-RUN] Would deploy {fn_name} ({zip_path.stat().st_size} bytes)")
            return True
        
        # Check if function exists
        try:
            client.get_function(FunctionName=fn_name)
            fn_exists = True
        except client.exceptions.ResourceNotFoundException:
            fn_exists = False
        
        zip_bytes = zip_path.read_bytes()
        
        if fn_exists:
            # Update existing function
            client.update_function_code(FunctionName=fn_name, ZipFile=zip_bytes)

            # Wait for code update to settle before updating configuration
            waiter = client.get_waiter('function_updated')
            waiter.wait(FunctionName=fn_name)

            client.update_function_configuration(
                FunctionName=fn_name,
                Description=config['description'],
                Timeout=config['timeout'],
                MemorySize=config['memory'],
                Environment={'Variables': config['environment']},
            )

            # Wait for configuration update to settle
            waiter.wait(FunctionName=fn_name)
            print(f"   ✓ Updated {fn_name}")
        
        else:
            # Create new function
            client.create_function(
                FunctionName=fn_name,
                Runtime=LAMBDA_RUNTIME,
                Role=LAMBDA_ROLE_ARN,
                Handler=config['handler'],
                Code={'ZipFile': zip_bytes},
                Description=config['description'],
                Timeout=config['timeout'],
                MemorySize=config['memory'],
                Environment={'Variables': config['environment']},
                Tags={
                    'Project': 'BetBudAI',
                    'Version': '2.0',
                    'ManagedBy': 'deploy_lambdas.py',
                }
            )
            print(f"   ✓ Created {fn_name}")
    
    return True


# ── EventBridge Rules ─────────────────────────────────────────────────────────

def setup_eventbridge_rules(dry_run: bool = False):
    """Create EventBridge schedule rules for new pipeline."""
    
    events = boto3.client('events', region_name=AWS_REGION)
    
    schedules = [
        {
            'name': 'betbudai-morning-trigger',
            'schedule': 'cron(30 8 * * ? *)',  # 08:30 UTC daily
            'description': 'BetBudAI morning pipeline',
            'function': 'betbudai-morning',
            'input': '{"stage":"morning"}',
        },
        {
            'name': 'betbudai-refresh-12-trigger',
            'schedule': 'cron(0 12 * * ? *)',  # 12:00 UTC
            'description': 'BetBudAI refresh at 12:00',
            'function': 'betbudai-refresh',
            'input': '{"stage":"refresh","refresh_hour":12}',
        },
        {
            'name': 'betbudai-refresh-14-trigger',
            'schedule': 'cron(0 14 * * ? *)',  # 14:00 UTC
            'description': 'BetBudAI refresh at 14:00',
            'function': 'betbudai-refresh',
            'input': '{"stage":"refresh","refresh_hour":14}',
        },
        {
            'name': 'betbudai-refresh-16-trigger',
            'schedule': 'cron(0 16 * * ? *)',  # 16:00 UTC
            'description': 'BetBudAI refresh at 16:00',
            'function': 'betbudai-refresh',
            'input': '{"stage":"refresh","refresh_hour":16}',
        },
        {
            'name': 'betbudai-refresh-18-trigger',
            'schedule': 'cron(0 18 * * ? *)',  # 18:00 UTC
            'description': 'BetBudAI refresh at 18:00',
            'function': 'betbudai-refresh',
            'input': '{"stage":"refresh","refresh_hour":18}',
        },
        {
            'name': 'betbudai-evening-trigger',
            'schedule': 'cron(0 20 * * ? *)',  # 20:00 UTC
            'description': 'BetBudAI evening pipeline',
            'function': 'betbudai-evening',
            'input': '{"stage":"evening","send_email":true}',
        },
        {
            'name': 'betbudai-learning-trigger',
            'schedule': 'cron(0 22 * * ? *)',  # 22:00 UTC
            'description': 'BetBudAI learning pipeline',
            'function': 'betbudai-learning',
            'input': '{"stage":"learning"}',
        },
    ]
    
    lambda_client = boto3.client('lambda', region_name=AWS_REGION)
    account_id = boto3.client('sts', region_name=AWS_REGION).get_caller_identity()['Account']
    
    print("\n=== Setting up EventBridge Rules ===")
    
    for sched in schedules:
        print(f"\n{'[DRY-RUN] ' if dry_run else ''}Creating rule: {sched['name']} ({sched['schedule']})")
        
        if dry_run:
            continue
        
        # Create rule
        events.put_rule(
            Name=sched['name'],
            ScheduleExpression=sched['schedule'],
            State='ENABLED',
            Description=sched['description'],
        )
        
        fn_arn = f"arn:aws:lambda:{AWS_REGION}:{account_id}:function:{sched['function']}"
        
        # Add target
        events.put_targets(
            Rule=sched['name'],
            Targets=[{
                'Id': '1',
                'Arn': fn_arn,
                'Input': sched['input'],
            }]
        )
        
        # Grant permission for EventBridge to invoke Lambda
        try:
            lambda_client.add_permission(
                FunctionName=sched['function'],
                StatementId=f"allow-events-{sched['name']}",
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=f"arn:aws:events:{AWS_REGION}:{account_id}:rule/{sched['name']}",
            )
        except lambda_client.exceptions.ResourceConflictException:
            pass  # Permission already exists
        
        print(f"   ✓ Rule '{sched['name']}' created → {sched['function']}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='BetBudAI Lambda Deployment')
    parser.add_argument('--function', choices=list(LAMBDA_CONFIGS.keys()), help='Deploy single function')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, do not deploy')
    parser.add_argument('--skip-events', action='store_true', help='Skip EventBridge rule setup')
    args = parser.parse_args()
    
    dry_run = args.dry_run
    
    print(f"=== BetBudAI Lambda Deployment {'[DRY-RUN] ' if dry_run else ''}===")
    print(f"Region: {AWS_REGION}")
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    
    # Select functions to deploy
    if args.function:
        configs_to_deploy = {args.function: LAMBDA_CONFIGS[args.function]}
    else:
        configs_to_deploy = LAMBDA_CONFIGS
    
    lambda_client = boto3.client('lambda', region_name=AWS_REGION)
    
    # Deploy each function
    results = {}
    for fn_key, config in configs_to_deploy.items():
        success = deploy_function(config, lambda_client, dry_run=dry_run)
        results[fn_key] = 'OK' if success else 'FAILED'
    
    # Set up EventBridge rules
    if not args.skip_events:
        setup_eventbridge_rules(dry_run=dry_run)
    
    # Summary
    print("\n=== Deployment Summary ===")
    for fn_key, status in results.items():
        emoji = '✓' if status == 'OK' else '✗'
        print(f"  {emoji} {LAMBDA_CONFIGS[fn_key]['function_name']}: {status}")
    
    all_ok = all(s == 'OK' for s in results.values())
    
    if all_ok:
        print(f"\n✅ All {len(results)} functions deployed successfully")
        if not dry_run and not args.skip_events:
            print("✅ EventBridge rules configured")
        print("\n⚠  Note: New functions run alongside existing surebet-* functions")
        print("   Validate before switching traffic to betbudai-* functions")
    else:
        failed = [k for k, v in results.items() if v != 'OK']
        print(f"\n✗ {len(failed)} function(s) failed: {', '.join(failed)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

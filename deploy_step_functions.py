#!/usr/bin/env python3
"""
deploy_step_functions.py
========================
One-shot deployment of the entire SureBet Step Functions infrastructure.

Creates / updates:
  ✅ S3 bucket         surebet-pipeline-data
  ✅ IAM role          SureBetLambdaRole         (for all 7 pipeline Lambdas)
  ✅ IAM role          SureBetStepFunctionsRole   (for Step Functions → Lambda invoke)
  ✅ Lambda functions  surebet-betfair-fetch, surebet-analysis, surebet-validate,
                       surebet-notify, surebet-results-fetch, surebet-loss-report,
                       surebet-learning
  ✅ State machines    SureBet-Morning, SureBet-Refresh, SureBet-Evening, SureBet-Learning
  ✅ EventBridge rules Morning 08:30, Refresh 12/14/16/18:00, Evening 20:00, Learning 21:00

Usage:
    python deploy_step_functions.py              # deploy everything
    python deploy_step_functions.py --lambdas    # redeploy Lambda code only
    python deploy_step_functions.py --status     # print current infrastructure status
"""

import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# ── Configuration ─────────────────────────────────────────────────────────────
REGION               = 'eu-west-1'
ACCOUNT_ID           = None   # resolved at runtime
BUCKET               = 'surebet-pipeline-data'
LAMBDA_ROLE_NAME     = 'SureBetLambdaRole'
SF_ROLE_NAME         = 'SureBetStepFunctionsRole'
LAMBDA_RUNTIME       = 'python3.11'
REPO_DIR             = Path(__file__).parent

SF_DIR               = REPO_DIR / 'step_functions'
LAMBDAS_DIR          = SF_DIR   / 'lambdas'

# ── Lambda definitions ────────────────────────────────────────────────────────
#   name              handler_file              timeout  memory  bundled_source_files
LAMBDAS = [
    {
        'name'   : 'surebet-betfair-fetch',
        'handler': 'sf_betfair_fetch.lambda_handler',
        'src'    : 'sf_betfair_fetch.py',
        'timeout': 120,
        'memory' : 256,
        'bundle' : ['betfair_odds_fetcher.py'],
        'env'    : {'PIPELINE_BUCKET': BUCKET},
    },
    {
        'name'   : 'surebet-analysis',
        'handler': 'sf_analysis.lambda_handler',
        'src'    : 'sf_analysis.py',
        'timeout': 600,
        'memory' : 512,
        'bundle' : [
            'complete_daily_analysis.py',
            'comprehensive_pick_logic.py',
            'form_enricher.py',
            'notify_picks.py',
            'weather_going_inference.py',
            'betfair_odds_fetcher.py',
            'ourhub_enricher.py',
            'trainer_form_stats.py',
        ],
        'optional_bundle': [
            'track_daily_insights.py',
        ],
        'env'    : {'PIPELINE_BUCKET': BUCKET},
    },
    {
        'name'   : 'surebet-validate',
        'handler': 'sf_validate.lambda_handler',
        'src'    : 'sf_validate.py',
        'timeout': 30,
        'memory' : 128,
        'bundle' : [],
        'env'    : {},
    },
    {
        'name'   : 'surebet-notify',
        'handler': 'sf_notify.lambda_handler',
        'src'    : 'sf_notify.py',
        'timeout': 60,
        'memory' : 128,
        'bundle' : [],
        'env'    : {},
    },
    {
        'name'   : 'surebet-results-fetch',
        'handler': 'sf_results_fetch.lambda_handler',
        'src'    : 'sf_results_fetch.py',
        'timeout': 120,
        'memory' : 256,
        'bundle' : [],
        'env'    : {},
    },
    {
        'name'   : 'surebet-sl-results',
        'handler': 'sf_sl_results.lambda_handler',
        'src'    : 'sf_sl_results.py',
        'timeout': 120,
        'memory' : 256,
        'bundle' : ['sl_results_fetcher.py'],
        'env'    : {},
    },
    {
        'name'   : 'surebet-fav-results',
        'handler': 'sf_fav_results.lambda_handler',
        'src'    : 'sf_fav_results.py',
        'timeout': 120,
        'memory' : 256,
        'bundle' : [],
        'env'    : {},
    },
    {
        'name'   : 'surebet-loss-report',
        'handler': 'sf_loss_report.lambda_handler',
        'src'    : 'sf_loss_report.py',
        'timeout': 60,
        'memory' : 256,
        'bundle' : [],
        'env'    : {
            'PIPELINE_BUCKET'   : BUCKET,
            'REPORT_RECIPIENT'  : 'charles.mccarthy@gmail.com',
            'REPORT_SENDER'     : 'charles.mccarthy@gmail.com',
        },
    },
    {
        'name'   : 'surebet-learning',
        'handler': 'sf_learning.lambda_handler',
        'src'    : 'sf_learning.py',
        'timeout': 300,
        'memory' : 256,
        'bundle' : ['learning_engine.py'],
        'env'    : {'LEARNING_DAYS_BACK': '7'},
    },
    {
        'name'   : 'surebet-major-analysis',
        'handler': 'sf_major_analysis.lambda_handler',
        'src'    : 'sf_major_analysis.py',
        'timeout': 300,
        'memory' : 256,
        'bundle' : [],
        'env'    : {},
    },
]

# ── State machine definitions ─────────────────────────────────────────────────
STATE_MACHINES = [
    {'name': 'SureBet-Morning',  'file': 'morning_sm.json'},
    {'name': 'SureBet-Refresh',  'file': 'refresh_sm.json'},
    {'name': 'SureBet-Evening',  'file': 'evening_sm.json'},
    {'name': 'SureBet-Learning',        'file': 'learning_sm.json'},
    {'name': 'SureBet-Major-Analysis',  'file': 'major_analysis_sm.json'},
]

# ── EventBridge schedules ─────────────────────────────────────────────────────
#  cron(min hour dom month dow year)  — all UTC, ? = any
SCHEDULES = [
    {
        'rule_name'     : 'SureBet-Morning-Schedule',
        'cron'          : 'cron(30 8 * * ? *)',
        'state_machine' : 'SureBet-Morning',
        'description'   : 'SureBet morning pipeline — 08:30 UTC',
    },
    {
        'rule_name'     : 'SureBet-Refresh-12-Schedule',
        'cron'          : 'cron(0 12 * * ? *)',
        'state_machine' : 'SureBet-Refresh',
        'description'   : 'SureBet midday refresh — 12:00 UTC',
    },
    {
        'rule_name'     : 'SureBet-Refresh-14-Schedule',
        'cron'          : 'cron(0 14 * * ? *)',
        'state_machine' : 'SureBet-Refresh',
        'description'   : 'SureBet afternoon refresh — 14:00 UTC',
    },
    {
        'rule_name'     : 'SureBet-Refresh-16-Schedule',
        'cron'          : 'cron(0 16 * * ? *)',
        'state_machine' : 'SureBet-Refresh',
        'description'   : 'SureBet late-afternoon refresh — 16:00 UTC',
    },
    {
        'rule_name'     : 'SureBet-Refresh-18-Schedule',
        'cron'          : 'cron(0 18 * * ? *)',
        'state_machine' : 'SureBet-Refresh',
        'description'   : 'SureBet evening refresh — 18:00 UTC',
    },
    {
        'rule_name'     : 'SureBet-Evening-Schedule',
        'cron'          : 'cron(0 20 * * ? *)',
        'state_machine' : 'SureBet-Evening',
        'description'   : 'SureBet evening results & report — 20:00 UTC',
    },
    {
        'rule_name'     : 'SureBet-Learning-Schedule',
        'cron'          : 'cron(0 21 * * ? *)',
        'state_machine' : 'SureBet-Learning',
        'description'   : 'SureBet nightly learning cycle — 21:00 UTC',
    },
    {
        'rule_name'     : 'SureBet-MajorAnalysis-Schedule',
        'cron'          : 'cron(0 7 ? * MON *)',
        'state_machine' : 'SureBet-Major-Analysis',
        'description'   : 'SureBet weekly major-race early-bird analysis — Monday 07:00 UTC',
    },
]

# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════

def _ok(msg):  print(f'  ✅ {msg}')
def _info(msg): print(f'  ℹ  {msg}')
def _warn(msg): print(f'  ⚠️  {msg}')
def _err(msg):  print(f'  ❌ {msg}')

def _get_account_id():
    sts = boto3.client('sts', region_name=REGION)
    return sts.get_caller_identity()['Account']


# ── S3 ────────────────────────────────────────────────────────────────────────

def ensure_s3_bucket(s3, bucket_name):
    print(f'\n[S3] Ensuring bucket: {bucket_name}')
    try:
        s3.head_bucket(Bucket=bucket_name)
        _ok(f'Bucket already exists: {bucket_name}')
    except ClientError as e:
        if e.response['Error']['Code'] in ('404', 'NoSuchBucket'):
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': REGION},
            )
            # Enable versioning for safety
            s3.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'},
            )
            # Block public access
            s3.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True, 'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True, 'RestrictPublicBuckets': True,
                },
            )
            _ok(f'Created bucket with versioning + public-access block: {bucket_name}')
        else:
            raise


# ── IAM ───────────────────────────────────────────────────────────────────────

LAMBDA_TRUST = json.dumps({
    'Version': '2012-10-17',
    'Statement': [{
        'Effect'   : 'Allow',
        'Principal': {'Service': 'lambda.amazonaws.com'},
        'Action'   : 'sts:AssumeRole',
    }],
})

SF_TRUST = json.dumps({
    'Version': '2012-10-17',
    'Statement': [{
        'Effect'   : 'Allow',
        'Principal': {'Service': 'states.amazonaws.com'},
        'Action'   : 'sts:AssumeRole',
    }],
})

LAMBDA_POLICY = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect'  : 'Allow',
            'Action'  : [
                'dynamodb:GetItem', 'dynamodb:PutItem', 'dynamodb:UpdateItem',
                'dynamodb:DeleteItem', 'dynamodb:Query', 'dynamodb:Scan',
                'dynamodb:BatchGetItem', 'dynamodb:BatchWriteItem',
            ],
            'Resource': [
                f'arn:aws:dynamodb:{REGION}:*:table/SureBetBets',
                f'arn:aws:dynamodb:{REGION}:*:table/SureBetBets/index/*',
            ],
        },
        {
            'Effect'  : 'Allow',
            'Action'  : ['s3:GetObject', 's3:PutObject', 's3:ListBucket'],
            'Resource': [
                f'arn:aws:s3:::{BUCKET}',
                f'arn:aws:s3:::{BUCKET}/*',
            ],
        },
        {
            'Effect'  : 'Allow',
            'Action'  : ['secretsmanager:GetSecretValue'],
            'Resource': [
                f'arn:aws:secretsmanager:{REGION}:*:secret:betfair-credentials*',
                f'arn:aws:secretsmanager:{REGION}:*:secret:twilio-credentials*',
            ],
        },
        {
            'Effect'  : 'Allow',
            'Action'  : ['ses:SendEmail', 'ses:SendRawEmail'],
            'Resource': '*',
        },
        {
            'Effect'  : 'Allow',
            'Action'  : [
                'logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents',
            ],
            'Resource': 'arn:aws:logs:*:*:*',
        },
    ],
}


def ensure_iam_role(iam, role_name, trust_policy, inline_policy_name, inline_policy_doc):
    """Create role if it doesn't exist; always update the inline policy."""
    print(f'\n[IAM] Ensuring role: {role_name}')
    try:
        role = iam.get_role(RoleName=role_name)['Role']
        _info(f'Role exists: {role["Arn"]}')
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            role = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=trust_policy,
                Description=f'SureBet pipeline role: {role_name}',
            )['Role']
            _ok(f'Created role: {role["Arn"]}')
            time.sleep(10)   # IAM propagation delay
        else:
            raise

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName=inline_policy_name,
        PolicyDocument=json.dumps(inline_policy_doc),
    )
    _ok(f'Inline policy applied: {inline_policy_name}')
    return role['Arn']


# ── Lambda packaging ──────────────────────────────────────────────────────────

def _build_zip(lf_config):
    """
    Build an in-memory zip for a Lambda function.
    Includes:
      - the handler file (renamed to handler module name)
      - any bundled source files from REPO_DIR
      - pip-installed dependencies for 'requests' (Lambda needs it, not in runtime)
    """
    buf = io.BytesIO()
    handler_module = lf_config['src'].replace('.py', '')

    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Handler
        handler_path = LAMBDAS_DIR / lf_config['src']
        zf.write(handler_path, lf_config['src'])

        # Bundled source files
        for src_file in lf_config.get('bundle', []):
            full = REPO_DIR / src_file
            if full.exists():
                zf.write(full, src_file)
                _info(f'  bundled: {src_file}')
            else:
                _warn(f'  MISSING bundled file: {src_file} — skipping')

        # Optional bundled files (no warning if absent)
        for src_file in lf_config.get('optional_bundle', []):
            full = REPO_DIR / src_file
            if full.exists():
                zf.write(full, src_file)
                _info(f'  bundled (optional): {src_file}')

        # pip dependencies — install to a temp dir, zip everything in
        pip_deps = lf_config.get('pip_deps', [])
        # requests is needed by betfair_odds_fetcher and form_enricher
        if any(f in lf_config.get('bundle', []) + [lf_config['src']]
               for f in ['betfair_odds_fetcher.py', 'form_enricher.py', 'sf_betfair_fetch.py', 'ourhub_enricher.py']):
            pip_deps = list(set(pip_deps + ['requests']))

        if pip_deps:
            with tempfile.TemporaryDirectory() as tmpdir:
                _info(f'  Installing pip deps: {pip_deps}')
                subprocess.run(
                    [
                        sys.executable, '-m', 'pip', 'install',
                        '--quiet',
                        '--platform', 'manylinux2014_x86_64',
                        '--implementation', 'cp',
                        '--python-version', '3.11',
                        '--only-binary', ':all:',
                        '-t', tmpdir,
                    ] + pip_deps,
                    check=True,
                )
                for root, dirs, files in os.walk(tmpdir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arc_path  = os.path.relpath(full_path, tmpdir)
                        zf.write(full_path, arc_path)

    buf.seek(0)
    return buf.read()


def deploy_lambda(lam, iam_role_arn, lf_config):
    """Create or update a Lambda function."""
    name     = lf_config['name']
    env_vars = {**lf_config.get('env', {})}

    print(f'\n[Lambda] Deploying: {name}')
    zip_bytes = _build_zip(lf_config)
    _info(f'Package size: {len(zip_bytes):,} bytes')

    base_kwargs = dict(
        FunctionName = name,
        Runtime      = LAMBDA_RUNTIME,
        Role         = iam_role_arn,
        Handler      = lf_config['handler'],
        Timeout      = lf_config['timeout'],
        MemorySize   = lf_config['memory'],
        Environment  = {'Variables': env_vars},
    )

    try:
        resp = lam.get_function(FunctionName=name)
        lam.update_function_code(FunctionName=name, ZipFile=zip_bytes, Publish=True)
        # Wait for code update to complete before changing configuration
        lam.get_waiter('function_updated').wait(FunctionName=name)
        lam.update_function_configuration(**base_kwargs)
        _ok(f'Updated: {resp["Configuration"]["FunctionArn"]}')
        return resp['Configuration']['FunctionArn'].split(':')[:-1]  # strip version
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            resp = lam.create_function(
                **base_kwargs,
                Code={'ZipFile': zip_bytes},
                Publish=True,
            )
            _ok(f'Created: {resp["FunctionArn"]}')
            return resp['FunctionArn']
        raise


def get_lambda_arn(lam, name):
    resp = lam.get_function(FunctionName=name)
    return resp['Configuration']['FunctionArn']


# ── State machine helpers ─────────────────────────────────────────────────────

def _substitute_arns(definition_dict, lambda_arns):
    """Replace PLACEHOLDER_<fn-name> strings in the ASL dict with real ARNs."""
    text = json.dumps(definition_dict)
    for fn_name, arn in lambda_arns.items():
        text = text.replace(f'PLACEHOLDER_{fn_name}', arn)
    return json.loads(text)


def deploy_state_machine(sfn, sm_config, role_arn, lambda_arns):
    name = sm_config['name']
    print(f'\n[StepFunctions] Deploying: {name}')

    raw = json.loads((SF_DIR / sm_config['file']).read_text(encoding='utf-8'))
    definition = _substitute_arns(raw, lambda_arns)
    definition_str = json.dumps(definition)

    try:
        existing = sfn.list_state_machines(maxResults=100)
        existing_arns = {m['name']: m['stateMachineArn']
                         for m in existing.get('stateMachines', [])}

        if name in existing_arns:
            sfn.update_state_machine(
                stateMachineArn = existing_arns[name],
                definition      = definition_str,
                roleArn         = role_arn,
            )
            _ok(f'Updated: {existing_arns[name]}')
            return existing_arns[name]
        else:
            resp = sfn.create_state_machine(
                name       = name,
                definition = definition_str,
                roleArn    = role_arn,
                type       = 'STANDARD',
            )
            _ok(f'Created: {resp["stateMachineArn"]}')
            return resp['stateMachineArn']
    except Exception:
        raise


# ── EventBridge ───────────────────────────────────────────────────────────────

def deploy_eventbridge_rule(eb, iam, schedule, sm_arn, sf_role_arn):
    rule_name = schedule['rule_name']
    print(f'\n[EventBridge] Rule: {rule_name}  ({schedule["cron"]})')

    eb.put_rule(
        Name               = rule_name,
        ScheduleExpression = schedule['cron'],
        State              = 'ENABLED',
        Description        = schedule['description'],
    )
    rule_arn = eb.describe_rule(Name=rule_name)['Arn']

    eb.put_targets(
        Rule   = rule_name,
        Targets = [{
            'Id'      : 'SureBetTarget',
            'Arn'     : sm_arn,
            'RoleArn' : sf_role_arn,
            'Input'   : json.dumps({}),
        }],
    )
    _ok(f'Rule {rule_name} → {sm_arn.split(":")[-1]}')


# ═════════════════════════════════════════════════════════════════════════════
# Status command
# ═════════════════════════════════════════════════════════════════════════════

def cmd_status():
    print('\n=== SureBet Step Functions — Infrastructure Status ===\n')
    lam = boto3.client('lambda', region_name=REGION)
    sfn = boto3.client('stepfunctions', region_name=REGION)
    eb  = boto3.client('events', region_name=REGION)

    print('Lambdas:')
    for lf in LAMBDAS:
        try:
            resp    = lam.get_function(FunctionName=lf['name'])
            config  = resp['Configuration']
            updated = config.get('LastModified', '?')[:19]
            print(f'  ✅ {lf["name"]:40s}  {config["Runtime"]}  {config["MemorySize"]}MB  '
                  f'timeout={config["Timeout"]}s  updated={updated}')
        except ClientError:
            print(f'  ❌ {lf["name"]:40s}  NOT DEPLOYED')

    print('\nState machines:')
    existing = {m['name']: m for m in sfn.list_state_machines(maxResults=100).get('stateMachines', [])}
    for sm in STATE_MACHINES:
        if sm['name'] in existing:
            m = existing[sm['name']]
            print(f'  ✅ {sm["name"]:30s}  {m["stateMachineArn"].split(":")[-1]}')
        else:
            print(f'  ❌ {sm["name"]:30s}  NOT DEPLOYED')

    print('\nEventBridge rules:')
    for sched in SCHEDULES:
        try:
            rule = eb.describe_rule(Name=sched['rule_name'])
            state = rule['State']
            print(f'  ✅ {sched["rule_name"]:40s}  {sched["cron"]:30s}  [{state}]')
        except ClientError:
            print(f'  ❌ {sched["rule_name"]:40s}  NOT DEPLOYED')

    print()


# ═════════════════════════════════════════════════════════════════════════════
# Main deployment
# ═════════════════════════════════════════════════════════════════════════════

def deploy_all(lambdas_only=False):
    global ACCOUNT_ID
    ACCOUNT_ID = _get_account_id()
    print(f'\n=== SureBet Step Functions Deploy ===')
    print(f'Account : {ACCOUNT_ID}')
    print(f'Region  : {REGION}')
    print(f'Bucket  : {BUCKET}')

    iam = boto3.client('iam', region_name=REGION)
    lam = boto3.client('lambda', region_name=REGION)
    s3  = boto3.client('s3', region_name=REGION)
    sfn = boto3.client('stepfunctions', region_name=REGION)
    eb  = boto3.client('events', region_name=REGION)

    if not lambdas_only:
        # ── S3 ────────────────────────────────────────────────────────────────
        ensure_s3_bucket(s3, BUCKET)

        # ── IAM roles ─────────────────────────────────────────────────────────
        lambda_role_arn = ensure_iam_role(
            iam, LAMBDA_ROLE_NAME, LAMBDA_TRUST,
            'SureBetLambdaPolicy', LAMBDA_POLICY,
        )

        sf_policy = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect'  : 'Allow',
                    'Action'  : ['lambda:InvokeFunction'],
                    'Resource': f'arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:surebet-*',
                },
                {
                    'Effect'  : 'Allow',
                    'Action'  : [
                        'logs:CreateLogDelivery', 'logs:GetLogDelivery',
                        'logs:UpdateLogDelivery', 'logs:DeleteLogDelivery',
                        'logs:ListLogDeliveries', 'logs:PutResourcePolicy',
                        'logs:DescribeResourcePolicies', 'logs:DescribeLogGroups',
                        'xray:GetSamplingRules', 'xray:GetSamplingTargets',
                        'xray:PutTraceSegments',
                    ],
                    'Resource': '*',
                },
            ],
        }
        sf_role_arn = ensure_iam_role(
            iam, SF_ROLE_NAME, SF_TRUST,
            'SureBetStepFunctionsPolicy', sf_policy,
        )

        # EventBridge also needs to start Step Functions executions
        eb_role_name = 'SureBetEventBridgeRole'
        eb_trust = json.dumps({
            'Version': '2012-10-17',
            'Statement': [{
                'Effect'   : 'Allow',
                'Principal': {'Service': 'events.amazonaws.com'},
                'Action'   : 'sts:AssumeRole',
            }],
        })
        eb_policy = {
            'Version': '2012-10-17',
            'Statement': [{
                'Effect'  : 'Allow',
                'Action'  : ['states:StartExecution'],
                'Resource': f'arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:SureBet-*',
            }],
        }
        eb_role_arn = ensure_iam_role(iam, eb_role_name, eb_trust, 'SureBetEventBridgePolicy', eb_policy)

    else:
        # Lambdas-only mode: fetch existing role ARN
        lambda_role_arn = iam.get_role(RoleName=LAMBDA_ROLE_NAME)['Role']['Arn']
        sf_role_arn     = iam.get_role(RoleName=SF_ROLE_NAME)['Role']['Arn']
        eb_role_arn     = iam.get_role(RoleName='SureBetEventBridgeRole')['Role']['Arn']

    # ── Lambda functions ───────────────────────────────────────────────────────
    print('\n=== Deploying Lambda functions ===')
    lambda_arns = {}
    for lf in LAMBDAS:
        deploy_lambda(lam, lambda_role_arn, lf)
        lambda_arns[lf['name']] = get_lambda_arn(lam, lf['name'])

    if lambdas_only:
        print('\n✅ Lambda-only deploy complete.')
        return

    # ── State machines ─────────────────────────────────────────────────────────
    print('\n=== Deploying Step Functions state machines ===')
    sm_arns = {}
    for sm in STATE_MACHINES:
        sm_arns[sm['name']] = deploy_state_machine(sfn, sm, sf_role_arn, lambda_arns)

    # ── EventBridge rules ──────────────────────────────────────────────────────
    print('\n=== Deploying EventBridge schedules ===')
    # Use the SF_ROLE_ARN — EventBridge needs permission to start executions
    # (same role that the state machines use to invoke Lambdas, but really we want
    #  the EventBridge role to start state machine executions)
    for sched in SCHEDULES:
        sm_arn = sm_arns.get(sched['state_machine'])
        if sm_arn:
            deploy_eventbridge_rule(eb, iam, sched, sm_arn, eb_role_arn)
        else:
            _warn(f"State machine {sched['state_machine']} not found — skipping rule {sched['rule_name']}")

    # ── Summary ────────────────────────────────────────────────────────────────
    print('\n' + '='*60)
    print('✅ SureBet Step Functions infrastructure deployed!\n')
    print('State machine ARNs:')
    for name, arn in sm_arns.items():
        print(f'  {name}: {arn}')
    print('\nTo check status:')
    print('  python deploy_step_functions.py --status')
    print('\nTo test the morning pipeline manually:')
    sm_morning = sm_arns.get('SureBet-Morning', '<morning-arn>')
    print(f'  aws stepfunctions start-execution \\')
    print(f'    --state-machine-arn {sm_morning} \\')
    print(f'    --input \'{{"date": "2026-04-07"}}\'')
    print('='*60 + '\n')


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deploy SureBet Step Functions infrastructure')
    parser.add_argument('--lambdas', action='store_true', help='Redeploy Lambda code only (skip IAM/S3/SM/EB)')
    parser.add_argument('--status',  action='store_true', help='Print current infrastructure status')
    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.lambdas:
        deploy_all(lambdas_only=True)
    else:
        deploy_all(lambdas_only=False)

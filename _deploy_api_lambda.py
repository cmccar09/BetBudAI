"""
Package and deploy betbudai-picks-api Lambda function.
Bundles: Flask app + routes + mangum + flask + flask-cors + boto3 deps.
"""
import subprocess
import sys
import zipfile
import shutil
import boto3
import io
import os
from pathlib import Path

ROOT = Path(r'C:\Users\charl\OneDrive\futuregenAI\BetBudAI')
API_DIR = ROOT / 'backend' / 'api'
VENV_DIR = ROOT / '.venv'
LAMBDA_NAME = os.environ.get('LAMBDA_NAME', 'betbudai-picks-api')
ROLE_ARN = os.environ.get('ROLE_ARN', 'arn:aws:iam::813281204422:role/SureBetLambdaRole')
REGION = os.environ.get('AWS_REGION', 'eu-west-1')

print(f'Building Lambda package for {LAMBDA_NAME}...')

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    # 1. API source files
    for py_file in API_DIR.rglob('*.py'):
        rel = py_file.relative_to(API_DIR)
        # Skip __pycache__ and middleware
        if '__pycache__' in str(rel):
            continue
        zf.write(py_file, str(rel))
        print(f'  + {rel}')

    # 2. Required packages from .venv/Lib/site-packages
    site_packages = VENV_DIR / 'Lib' / 'site-packages'
    required_packages = [
        'mangum', 'flask', 'flask_cors', 'click', 'itsdangerous',
        'jinja2', 'markupsafe', 'werkzeug',
        'stripe', 'requests', 'certifi', 'urllib3', 'charset_normalizer',
        'idna', 'typing_extensions',
        'google', 'google_auth_oauthlib', 'oauthlib', 'requests_oauthlib',
        'pyasn1', 'pyasn1_modules', 'six',
        'cryptography', 'cffi', 'pycparser',
        # boto3 is available in Lambda runtime, no need to bundle
    ]
    for pkg in required_packages:
        pkg_path = site_packages / pkg
        if pkg_path.exists():
            for f in pkg_path.rglob('*'):
                if '__pycache__' in str(f):
                    continue
                rel = f.relative_to(site_packages)
                if f.is_file():
                    zf.write(f, str(rel))
            print(f'  + pkg: {pkg}')
        else:
            # Try .dist-info / egg-info style single file
            for pat in [f'{pkg}.py', f'{pkg}-*.dist-info']:
                matches = list(site_packages.glob(pat))
                for m in matches:
                    if m.is_file():
                        zf.write(m, m.name)
                    print(f'  + {m.name}')

    for native_lib in site_packages.glob('_cffi_backend*.pyd'):
        if native_lib.is_file():
            zf.write(native_lib, native_lib.name)
            print(f'  + native: {native_lib.name}')

buf.seek(0)
zip_bytes = buf.read()
size_mb = len(zip_bytes) / 1024 / 1024
print(f'\nPackage size: {size_mb:.2f} MB')

# Deploy to AWS Lambda
lc = boto3.client('lambda', region_name=REGION)

try:
    lc.get_function(FunctionName=LAMBDA_NAME)
    fn_exists = True
    print(f'Updating existing {LAMBDA_NAME}...')
except lc.exceptions.ResourceNotFoundException:
    fn_exists = False
    print(f'Creating new {LAMBDA_NAME}...')

if fn_exists:
    current_config = lc.get_function_configuration(FunctionName=LAMBDA_NAME)
    current_env = (current_config.get('Environment') or {}).get('Variables') or {}
    merged_env = {
        **current_env,
        'ENV': 'production',
        'DYNAMODB_TABLE': 'SureBetBets',
    }
    existing_layers = [layer['Arn'] for layer in current_config.get('Layers', [])]
    lc.update_function_code(FunctionName=LAMBDA_NAME, ZipFile=zip_bytes)
    lc.get_waiter('function_updated').wait(FunctionName=LAMBDA_NAME)
    lc.update_function_configuration(
        FunctionName=LAMBDA_NAME,
        Description='BetBudAI modular Flask API (Mangum adapter)',
        Timeout=30,
        MemorySize=256,
        Environment={'Variables': merged_env},
        Layers=existing_layers,
    )
    lc.get_waiter('function_updated').wait(FunctionName=LAMBDA_NAME)
else:
    lc.create_function(
        FunctionName=LAMBDA_NAME,
        Runtime='python3.11',
        Role=ROLE_ARN,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_bytes},
        Description='BetBudAI modular Flask API (Mangum adapter)',
        Timeout=30,
        MemorySize=256,
        Environment={'Variables': {
            'ENV': 'production',
            'DYNAMODB_TABLE': 'SureBetBets',
        }},
        Tags={'Project': 'BetBudAI', 'Version': '2.0'},
    )
    lc.get_waiter('function_active').wait(FunctionName=LAMBDA_NAME)

fn_config = lc.get_function_configuration(FunctionName=LAMBDA_NAME)
fn_arn = fn_config['FunctionArn']
print(f'\nDeployed: {fn_arn}')
print(f'Handler: {fn_config["Handler"]}')

# Add permission for API Gateway to invoke
account_id = '813281204422'
api_id = os.environ.get('API_GATEWAY_ID', 'e5na6ldp35')
try:
    lc.add_permission(
        FunctionName=LAMBDA_NAME,
        StatementId='APIGatewayInvoke',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f'arn:aws:execute-api:{REGION}:{account_id}:{api_id}/*',
    )
    print('Added API Gateway invoke permission.')
except lc.exceptions.ResourceConflictException:
    print('API Gateway permission already exists.')

print(f'\nFunction ARN: {fn_arn}')
print('Next: Update API Gateway integration to use this ARN.')

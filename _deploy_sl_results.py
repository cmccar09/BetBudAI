"""Deploy surebet-sl-results Lambda with sl_results_fetcher unplaced→LOSS fix."""
import boto3
import zipfile
import io
from pathlib import Path

LAMBDA_NAME = 'surebet-sl-results'
REGION = 'eu-west-1'
ROOT = Path(r'C:\Users\charl\OneDrive\futuregenAI\BetBudAI')
DEPLOY_DIR = ROOT / '_lambda_deploy_temp'

print(f'Building package for {LAMBDA_NAME}...')

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    for py_file in DEPLOY_DIR.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        rel = py_file.relative_to(DEPLOY_DIR)
        zf.write(py_file, str(rel))
        print(f'  + {rel}')

buf.seek(0)
zip_bytes = buf.read()
size_kb = len(zip_bytes) // 1024
print(f'\nPackage: {size_kb} KB')

lc = boto3.client('lambda', region_name=REGION)
print(f'Deploying to {LAMBDA_NAME}...')
resp = lc.update_function_code(FunctionName=LAMBDA_NAME, ZipFile=zip_bytes)
print(f'OK: {resp["FunctionName"]} updated, runtime={resp["Runtime"]}, handler={resp["Handler"]}')
print('Waiting for update to complete...')
lc.get_waiter('function_updated').wait(FunctionName=LAMBDA_NAME)
print(f'Done: {LAMBDA_NAME} is live with unplaced→LOSS fix.')

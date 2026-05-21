"""Deploy updated betbudai-* handler.py files to AWS Lambda."""
import boto3
import zipfile
import io
from pathlib import Path

lc = boto3.client('lambda', region_name='eu-west-1')
root = Path(__file__).parent

for name in ['morning', 'refresh', 'evening', 'learning']:
    fn = f'betbudai-{name}'
    src = root / 'backend' / 'pipeline' / name / 'handler.py'
    print(f'Deploying {fn}...')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(str(src), 'handler.py')
    buf.seek(0)
    lc.update_function_code(FunctionName=fn, ZipFile=buf.read())
    lc.get_waiter('function_updated').wait(FunctionName=fn)
    print(f'  OK: {fn}')

print('\nAll 4 handlers deployed successfully.')

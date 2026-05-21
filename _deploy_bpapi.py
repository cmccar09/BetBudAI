"""Deploy _bpapi_patched.py as lambda_function.py to BettingPicksAPI in eu-west-1"""
import boto3
import zipfile
import io
import os
import shutil

FUNCTION_NAME = 'BettingPicksAPI'
REGION        = 'eu-west-1'
SRC_FILE      = os.path.join('_lambda_build', '_bpapi_patched.py')
STRIPE_DIR    = os.path.join('_lambda_build', 'stripe_layer')

# Read patched source
with open(SRC_FILE, 'r', encoding='utf-8') as f:
    source = f.read()

# Create in-memory zip with the file named lambda_function.py
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    info = zipfile.ZipInfo('lambda_function.py')
    info.compress_type = zipfile.ZIP_DEFLATED
    zf.writestr(info, source.encode('utf-8'))

    # Bundle stripe package
    if os.path.isdir(STRIPE_DIR):
        for root, dirs, files in os.walk(STRIPE_DIR):
            for fname in files:
                full = os.path.join(root, fname)
                arcname = os.path.relpath(full, STRIPE_DIR)
                zf.write(full, arcname)
        print(f"Bundled stripe from {STRIPE_DIR}")
buf.seek(0)
zip_bytes = buf.read()
print(f"Zip size: {len(zip_bytes):,} bytes")

# Deploy
client = boto3.client('lambda', region_name=REGION)
resp = client.update_function_code(
    FunctionName=FUNCTION_NAME,
    ZipFile=zip_bytes,
    Publish=True,
)
print(f"Status  : {resp['ResponseMetadata']['HTTPStatusCode']}")
print(f"Version : {resp.get('Version')}")
print(f"Modified: {resp.get('LastModified')}")
print(f"SHA256  : {resp.get('CodeSha256')}")
print("Deploy: OK")

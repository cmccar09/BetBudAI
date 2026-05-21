"""
Deploy stripe Python package as a Lambda Layer, then attach it to BettingPicksAPI.
Run once: python deploy_stripe_layer.py
"""
import boto3
import subprocess
import zipfile
import io
import os
import shutil
import tempfile

FUNCTION_NAME = 'BettingPicksAPI'
LAYER_NAME    = 'stripe-python'
REGION        = 'eu-west-1'

print("=== Step 1: Install stripe into temp directory ===")
tmpdir = tempfile.mkdtemp()
pkg_dir = os.path.join(tmpdir, 'python')
os.makedirs(pkg_dir)

subprocess.check_call([
    'pip', 'install', 'stripe', '-t', pkg_dir, '--no-cache-dir', '--quiet'
])
print(f"Installed stripe to {pkg_dir}")

print("=== Step 2: Create layer zip ===")
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(tmpdir):
        for f in files:
            full_path = os.path.join(root, f)
            arc_name = os.path.relpath(full_path, tmpdir)
            zf.write(full_path, arc_name)
buf.seek(0)
zip_bytes = buf.read()
print(f"Layer zip size: {len(zip_bytes):,} bytes")

# Cleanup
shutil.rmtree(tmpdir, ignore_errors=True)

print("=== Step 3: Publish Lambda Layer ===")
client = boto3.client('lambda', region_name=REGION)
layer_resp = client.publish_layer_version(
    LayerName=LAYER_NAME,
    Description='stripe Python SDK for payment processing',
    Content={'ZipFile': zip_bytes},
    CompatibleRuntimes=['python3.11', 'python3.12'],
)
layer_arn = layer_resp['LayerVersionArn']
print(f"Layer ARN: {layer_arn}")

print("=== Step 4: Attach layer to Lambda ===")
# Get existing config
config = client.get_function_configuration(FunctionName=FUNCTION_NAME)
existing_layers = [l['Arn'] for l in config.get('Layers', [])]

# Remove any old stripe layer and add new one
new_layers = [l for l in existing_layers if 'stripe' not in l.lower()]
new_layers.append(layer_arn)

client.update_function_configuration(
    FunctionName=FUNCTION_NAME,
    Layers=new_layers,
)
print(f"Attached layer to {FUNCTION_NAME}")
print("Done!")

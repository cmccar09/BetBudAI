"""Deploy frontend/build to AWS Amplify (app: d2hmpykfsdweob, branch: main)"""
import boto3
import zipfile
import io
import os
import subprocess
import urllib.request

APP_ID  = 'd2hmpykfsdweob'
BRANCH  = 'main'
REGION  = 'eu-west-1'
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), 'frontend')
BUILD_DIR = os.path.join(FRONTEND_DIR, 'build')

# Always rebuild from source before deploying
print("Running npm run build...")
result = subprocess.run(['npm', 'run', 'build'], cwd=FRONTEND_DIR, shell=True, capture_output=True, text=True)
if result.returncode != 0:
    print(result.stderr[-2000:] if result.stderr else 'No stderr')
    raise SystemExit(f"ERROR: npm run build failed (exit {result.returncode})")
print("Build complete.")

print(f"Build dir: {BUILD_DIR}")
if not os.path.isdir(BUILD_DIR):
    raise SystemExit(f"ERROR: {BUILD_DIR} not found — build failed")

# 1. Zip the build folder
print("Zipping build artefacts...")
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(BUILD_DIR):
        # skip hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in files:
            full_path = os.path.join(root, fname)
            arc_name  = os.path.relpath(full_path, BUILD_DIR)
            zf.write(full_path, arc_name)
buf.seek(0)
zip_bytes = buf.read()
print(f"Zip size: {len(zip_bytes):,} bytes")

# 2. Ask Amplify for a pre-signed upload URL
client = boto3.client('amplify', region_name=REGION)
print("Requesting Amplify deployment slot...")
dep = client.create_deployment(appId=APP_ID, branchName=BRANCH)
job_id    = dep['jobId']
upload_url = dep['zipUploadUrl']
print(f"Job ID : {job_id}")

# 3. Upload zip via PUT to the pre-signed S3 URL
print("Uploading zip to S3...")
req = urllib.request.Request(
    upload_url,
    data=zip_bytes,
    method='PUT',
    headers={'Content-Type': 'application/zip'},
)
with urllib.request.urlopen(req) as resp:
    print(f"S3 upload HTTP status: {resp.status}")

# 4. Start the deployment
print("Starting Amplify deployment...")
client.start_deployment(appId=APP_ID, branchName=BRANCH, jobId=job_id)

# 5. Save job id for monitoring
with open('_amplify_job_id.txt', 'w') as f:
    f.write(job_id)
print(f"Job ID saved to _amplify_job_id.txt")
print(f"\nDeployment started. Monitor at:")
print(f"  https://eu-west-1.console.aws.amazon.com/amplify/home#/{APP_ID}/{BRANCH}/deployments")
print(f"  Live URL: https://main.{APP_ID}.amplifyapp.com")

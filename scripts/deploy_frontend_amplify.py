#!/usr/bin/env python3
"""Deploy frontend/build to an Amplify app branch via artifact upload."""

import argparse
import io
import json
import sys
import time
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import boto3


def zip_build(build_dir: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in build_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(build_dir).as_posix())
    buf.seek(0)
    return buf.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy frontend build to Amplify")
    parser.add_argument("--app-id", default="d2cp2pfnzl7t60")
    parser.add_argument("--branch", default="dev")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--build-dir", default="frontend/build")
    parser.add_argument("--wait-seconds", type=int, default=300)
    args = parser.parse_args()

    build_dir = Path(args.build_dir)
    if not build_dir.exists():
        print(f"[ERROR] Build directory not found: {build_dir}")
        return 2

    artifact = zip_build(build_dir)
    print(f"[INFO] Zipped build: {len(artifact) / (1024 * 1024):.2f} MB")

    client = boto3.client("amplify", region_name=args.region)

    dep = client.create_deployment(appId=args.app_id, branchName=args.branch)
    job_id = dep["jobId"]
    upload_url = dep["zipUploadUrl"]
    print(f"[INFO] Created deployment job: {job_id}")

    req = Request(upload_url, method="PUT", data=artifact)
    with urlopen(req, timeout=120) as resp:
        if resp.status not in (200, 201):
            print(f"[ERROR] Upload failed: HTTP {resp.status}")
            return 3

    client.start_deployment(appId=args.app_id, branchName=args.branch, jobId=job_id)
    print("[INFO] Deployment started")

    deadline = time.time() + args.wait_seconds
    last_status = None
    while time.time() < deadline:
        job = client.get_job(appId=args.app_id, branchName=args.branch, jobId=job_id)["job"]
        status = job.get("status", "UNKNOWN")
        if status != last_status:
            print(f"[INFO] Job status: {status}")
            last_status = status
        if status in ("SUCCEED", "FAILED", "CANCELLED"):
            if status == "SUCCEED":
                print("[DONE] Amplify deployment succeeded")
                return 0
            print("[ERROR] Amplify deployment did not succeed")
            print(json.dumps(job, indent=2, default=str))
            return 4
        time.sleep(5)

    print("[WARN] Timed out waiting for deployment completion")
    return 5


if __name__ == "__main__":
    sys.exit(main())

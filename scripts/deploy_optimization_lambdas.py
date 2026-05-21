"""Deploy optimization Lambda handlers used by morning/refresh orchestrators."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import boto3

REGION = "eu-west-1"
ROOT = Path(__file__).resolve().parents[1]

SPECS = [
    {
        "name": "calculate-improver-boost-scores",
        "src": ROOT / "backend" / "pipeline" / "optimizations" / "improver_boost" / "handler.py",
        "description": "Apply improver score boosts and rerank horses",
        "timeout": 30,
        "memory": 256,
    },
    {
        "name": "compare-race-fields",
        "src": ROOT / "backend" / "pipeline" / "optimizations" / "field_compare" / "handler.py",
        "description": "Compare modeled field vs current BetFair field",
        "timeout": 30,
        "memory": 256,
    },
]


def zip_handler(src: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(str(src), "handler.py")
    buf.seek(0)
    return buf.read()


def main() -> None:
    client = boto3.client("lambda", region_name=REGION)

    base_cfg = client.get_function_configuration(FunctionName="betbudai-morning")
    role = base_cfg["Role"]
    runtime = base_cfg["Runtime"]

    for spec in SPECS:
        code = zip_handler(spec["src"])
        name = spec["name"]

        print(f"Deploying {name}...")
        try:
            client.get_function(FunctionName=name)
            exists = True
        except client.exceptions.ResourceNotFoundException:
            exists = False

        if exists:
            client.update_function_code(FunctionName=name, ZipFile=code)
            client.get_waiter("function_updated").wait(FunctionName=name)
            client.update_function_configuration(
                FunctionName=name,
                Handler="handler.lambda_handler",
                Runtime=runtime,
                Timeout=spec["timeout"],
                MemorySize=spec["memory"],
                Description=spec["description"],
            )
            client.get_waiter("function_updated").wait(FunctionName=name)
            print(f"  OK updated {name}")
        else:
            client.create_function(
                FunctionName=name,
                Runtime=runtime,
                Role=role,
                Handler="handler.lambda_handler",
                Code={"ZipFile": code},
                Timeout=spec["timeout"],
                MemorySize=spec["memory"],
                Description=spec["description"],
                Publish=True,
            )
            print(f"  OK created {name}")


if __name__ == "__main__":
    main()

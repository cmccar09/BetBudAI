#!/usr/bin/env python3
"""Update Stripe price IDs on the API Lambda environment.

Usage:
  python scripts/update_stripe_price_ids.py \
    --function betbudai-picks-api \
    --region eu-west-1 \
    --premium price_123 \
    --vip price_456
"""

import argparse
import sys

import boto3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update Stripe price IDs in Lambda env vars")
    parser.add_argument("--function", required=True, help="Lambda function name")
    parser.add_argument("--region", default="eu-west-1", help="AWS region (default: eu-west-1)")
    parser.add_argument("--premium", required=True, help="Stripe Premium price ID (price_...)")
    parser.add_argument("--vip", required=True, help="Stripe VIP price ID (price_...)")
    return parser.parse_args()


def validate_price_id(label: str, value: str) -> None:
    if not value.startswith("price_"):
        raise ValueError(f"{label} must start with 'price_': {value}")


def main() -> int:
    args = parse_args()

    try:
        validate_price_id("Premium price ID", args.premium)
        validate_price_id("VIP price ID", args.vip)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 2

    client = boto3.client("lambda", region_name=args.region)

    try:
        current = client.get_function_configuration(FunctionName=args.function)
    except client.exceptions.ResourceNotFoundException:
        print(f"[ERROR] Lambda not found: {args.function} in {args.region}")
        return 3

    env = (current.get("Environment") or {}).get("Variables") or {}

    merged = {
        **env,
        "STRIPE_PRICE_PREMIUM": args.premium,
        "STRIPE_PRICE_VIP": args.vip,
    }

    print("[UPDATING] Lambda environment")
    print(f"  Function: {args.function}")
    print(f"  Region:   {args.region}")
    print(f"  Premium:  {args.premium}")
    print(f"  VIP:      {args.vip}")

    client.update_function_configuration(
        FunctionName=args.function,
        Environment={"Variables": merged},
    )

    client.get_waiter("function_updated").wait(FunctionName=args.function)

    updated = client.get_function_configuration(FunctionName=args.function)
    updated_env = (updated.get("Environment") or {}).get("Variables") or {}

    print("[DONE] Stripe price IDs updated")
    print(f"  STRIPE_PRICE_PREMIUM={updated_env.get('STRIPE_PRICE_PREMIUM', '')}")
    print(f"  STRIPE_PRICE_VIP={updated_env.get('STRIPE_PRICE_VIP', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

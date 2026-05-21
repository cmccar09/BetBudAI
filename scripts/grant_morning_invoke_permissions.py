#!/usr/bin/env python3
"""Grant betbudai-morning execution role permission to invoke optimization lambdas."""

import json
import boto3

REGION = "eu-west-1"
ROLE_NAME = "SureBetLambdaRole"
ACCOUNT_ID = "813281204422"

FUNCTIONS = [
    "surebet-betfair-fetch",
    "surebet-analysis",
    "surebet-validate",
    "surebet-featured-meeting",
    "surebet-notify",
    "calculate-improver-boost-scores",
    "apply-improver-boosted-picks",
    "featured-improver-enforcer",
    "compare-race-fields",
]


def main() -> None:
    iam = boto3.client("iam", region_name=REGION)

    resources = [f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{name}" for name in FUNCTIONS]

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowInvokePipelineFunctions",
                "Effect": "Allow",
                "Action": ["lambda:InvokeFunction"],
                "Resource": resources,
            }
        ],
    }

    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="betbudai-morning-invoke-permissions",
        PolicyDocument=json.dumps(policy),
    )

    print("[DONE] Updated inline IAM policy")
    print(f"  Role: {ROLE_NAME}")
    print("  Functions allowed:")
    for fn in FUNCTIONS:
        print(f"    - {fn}")


if __name__ == "__main__":
    main()

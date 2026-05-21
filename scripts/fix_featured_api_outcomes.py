#!/usr/bin/env python3
"""
Fix featured meeting API outcomes by re-triggering the Lambda with force_refresh.
The Lambda should re-query DynamoDB and get the correct WIN outcomes.
"""

import boto3
import json

lambda_client = boto3.client('lambda', region_name='eu-west-1')

# Trigger Lambda with force_refresh parameter
payload = {
    "queryStringParameters": {
        "date": "2026-05-20",
        "course": "Gowran Park",
        "force_refresh": "true"
    }
}

print("Invoking surebet-featured-meeting Lambda with force_refresh...")
response = lambda_client.invoke(
    FunctionName='surebet-featured-meeting',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read())
print(f"Status Code: {response['StatusCode']}")
print(f"\nResponse preview:")
print(json.dumps(result, indent=2)[:500])

# Check if it worked
if response['StatusCode'] == 200:
    body = json.loads(result.get('body', '{}'))
    if 'races' in body:
        print("\n[OK] Featured meeting data refreshed")
        print("\nOutcomes:")
        for race in body['races'][:5]:
            if race.get('runners'):
                top = race['runners'][0]
                print(f"  {race['time_user']} {top['horse']}: {top.get('outcome', 'MISSING')}")
    else:
        print("\n[ERROR] No races in response")
else:
    print(f"\n[ERROR] Lambda invocation failed: {response['StatusCode']}")

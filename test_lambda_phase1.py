"""
Test Lambda with sample race data to verify Phase 1 signals load correctly
"""

import json
import boto3

# Create a minimal test race
test_race = {
    "venue": "Ascot",
    "time": "14:00",
    "race_name": "Test Handicap",
    "market_id": "test-123",
    "runners": [
        {
            "name": "Test Horse",
            "odds": 5.0,
            "form": "1-2-1",
            "trainer": "W P Mullins",
            "jockey": "Paul Townend",
            "weight": 11.0,
        }
    ]
}

payload = {
    "target_date": "2026-05-20",
    "races": [test_race],
    "force": True
}

print("Testing Lambda with sample race data...")
print(f"Payload: {json.dumps(payload, indent=2)}\n")

lambda_client = boto3.client('lambda', region_name='eu-west-1')

response = lambda_client.invoke(
    FunctionName='surebet-analysis',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

# Read response
response_payload = json.loads(response['Payload'].read())
print(f"Status Code: {response['StatusCode']}")
print(f"\nLambda Response:")
print(json.dumps(response_payload, indent=2))

# Check logs for Phase 1 message
log_result = response.get('LogResult', '')
if log_result:
    import base64
    logs = base64.b64decode(log_result).decode('utf-8')
    print("\n" + "="*70)
    print("LAMBDA EXECUTION LOGS:")
    print("="*70)
    print(logs)
    print("="*70)

    # Check if Phase 1 signals loaded
    if "[PHASE1] Signals loaded" in logs:
        print("\n✅ SUCCESS: Phase 1 signals are ACTIVE in Lambda")
    elif "[PHASE1] Signals not available" in logs:
        print("\n❌ FAILURE: Phase 1 signals failed to load")
        print("Check import error in logs above")
    else:
        print("\n⚠️  WARNING: No Phase 1 signal log found (may need to check CloudWatch)")
else:
    print("\nNo LogResult in response (check CloudWatch for logs)")

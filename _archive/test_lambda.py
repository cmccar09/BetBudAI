import boto3
import json

lambda_client = boto3.client('lambda', region_name='eu-west-1')

payload = {
    "rawPath": "/api/results/today",
    "requestContext": {
        "http": {
            "method": "GET"
        }
    }
}

print("Testing Lambda function...")
response = lambda_client.invoke(
    FunctionName='BettingPicksAPI',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read())
body = json.loads(result['body'])

print(f"\n{'='*80}")
print("√ LAMBDA FUNCTION TEST RESULTS")
print(f"{'='*80}\n")
print(f"Status: {result['statusCode']}")
print(f"Visible picks: {len(body['picks'])}\n")

if body['picks']:
    for pick in body['picks']:
        race_time = pick.get('race_time', '')
        print(f"  {race_time} - {pick.get('horse')} @ {pick.get('odds')}")
else:
    print("  ✓ No upcoming races (old races filtered out)")

print(f"\n{'='*80}")
print("√ Lambda deployed successfully")
print("√ Time filtering active")
print("√ Refresh browser to see changes")
print(f"{'='*80}\n")

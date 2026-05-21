"""Test the results API endpoint"""
import boto3
import json

lambda_client = boto3.client('lambda', region_name='eu-west-1')

# Invoke the Lambda for results endpoint
response = lambda_client.invoke(
    FunctionName='BettingPicksAPI',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'rawPath': '/results/today',
        'requestContext': {
            'http': {
                'method': 'GET'
            }
        }
    })
)

# Read the response
result = json.loads(response['Payload'].read())
print(f"Status Code: {result['statusCode']}")

# Parse the body
body = json.loads(result['body'])

print(f"\n{'='*70}")
print(f"RESULTS API RESPONSE")
print(f"{'='*70}\n")

if 'summary' in body:
    summary = body['summary']
    print(f"Summary:")
    print(f"  Total picks: {summary.get('total_picks', 0)}")
    print(f"  Wins: {summary.get('wins', 0)}")
    print(f"  Losses: {summary.get('losses', 0)}")
    print(f"  Pending: {summary.get('pending', 0)}")
    print(f"  Total stake: £{summary.get('total_stake', 0):.2f}")
    print(f"  Profit: £{summary.get('profit', 0):.2f}")
    print(f"  ROI: {summary.get('roi', 0):.1f}%")

if 'picks' in body:
    picks = body['picks']
    print(f"\nPicks with results: {len(picks)}")
    for pick in picks:
        print(f"  - {pick.get('horse')} at {pick.get('course')}: {pick.get('outcome', 'pending')}")
elif 'horses' in body and body['horses'].get('picks'):
    picks = body['horses']['picks']
    print(f"\nHorse picks with results: {len(picks)}")
    for pick in picks:
        print(f"  - {pick.get('horse')} at {pick.get('course')}: {pick.get('outcome', 'pending')}")
else:
    print(f"\n⚠️  No picks returned")
    print(f"Message: {body.get('message', 'No message')}")

print(f"\n{'='*70}\n")

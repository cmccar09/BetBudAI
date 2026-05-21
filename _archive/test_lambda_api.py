"""Test the actual Lambda/API Gateway endpoint"""
import boto3
import json

lambda_client = boto3.client('lambda', region_name='eu-west-1')

# Invoke the Lambda directly
response = lambda_client.invoke(
    FunctionName='BettingPicksAPI',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'rawPath': '/picks/today',
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

if 'picks' in body:
    picks = body['picks']
    print(f"\n=== API RESPONSE ===")
    print(f"Total picks returned: {len(picks)}")
    print(f"\nTop picks:")
    for i, pick in enumerate(picks[:10], 1):
        horse = pick.get('horse', 'Unknown')
        score = pick.get('comprehensive_score', 0)
        course = pick.get('course', 'Unknown')
        race_time = pick.get('race_time', 'Unknown')
        rec = "⭐" if pick.get('recommended_bet') else "  "
        print(f"{i}. {rec} {horse:25} | {course:15} | Score: {score:5.1f}")
else:
    print("ERROR - No 'picks' in response!")
    print(json.dumps(body, indent=2))

"""
Test yesterday results API locally - bypassing API Gateway
"""
import json
from lambda_api_picks import get_yesterday_picks

# Simulate headers
headers = {
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json'
}

print("Testing get_yesterday_picks function locally...\n")

result = get_yesterday_picks(headers)

print(f"Status Code: {result['statusCode']}")

if result['statusCode'] == 200:
    body = json.loads(result['body'])
    print(f"Success: {body.get('success')}")
    print(f"Date: {body.get('date')}")
    print(f"Count: {body.get('count')}")
    
    if body.get('count', 0) > 0:
        picks = body.get('picks', [])
        
        # Check outcomes
        outcomes = {}
        for pick in picks:
            outcome = pick.get('outcome', 'None')
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
        
        print("\nOutcome distribution:")
        for outcome, count in sorted(outcomes.items()):
            print(f"  {outcome}: {count}")
        
        print(f"\n✅ Lambda function working correctly - {body.get('count')} picks returned")
    else:
        print("\n⚠️  Lambda returns 0 picks")
else:
    print(f"Error: {result.get('body')}")

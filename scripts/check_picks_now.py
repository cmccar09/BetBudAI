#!/usr/bin/env python3
"""Check if today's picks are ready via API."""

import boto3
import json

lc = boto3.client('lambda', region_name='eu-west-1')

# Call the API lambda to get today's picks
resp = lc.invoke(
    FunctionName='betbudai-picks-api',
    InvocationType='RequestResponse',
    Payload=json.dumps({'path': '/api/picks/today', 'httpMethod': 'GET'}).encode()
)

body = json.loads(resp['Payload'].read())
if isinstance(body, str):
    body = json.loads(body)

# Parse the response
if 'body' in body:
    result = json.loads(body['body'])
else:
    result = body

print('[API RESPONSE] /api/picks/today')
print()

payload_status = result.get('payload_status', {})
print(f"Payload Complete: {payload_status.get('payload_complete')}")
print(f"Analysis Status: {payload_status.get('analysis_status', 'N/A')}")
print()

top_calls = result.get('top_calls', {})
if top_calls:
    print('[TOP PICKS]')
    for pick_type, pick_data in top_calls.items():
        print(f"  {pick_type}:")
        if isinstance(pick_data, dict):
            for key, val in pick_data.items():
                print(f"    {key}: {val}")
        else:
            print(f"    {pick_data}")
    print()

all_picks = result.get('all_picks', [])
print(f"Total picks for today: {len(all_picks)}")

if all_picks:
    print()
    print('[SAMPLE PICKS]')
    for i, pick in enumerate(all_picks[:5]):
        print(f"  Pick {i+1}:")
        for key in ['horse', 'course', 'race_time', 'pick_rank', 'comprehensive_score', 'potential_improver_flag']:
            if key in pick:
                print(f"    {key}: {pick[key]}")

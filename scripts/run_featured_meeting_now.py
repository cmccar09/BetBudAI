#!/usr/bin/env python3
"""Run featured meeting picks analysis now."""

import boto3
import json
from datetime import datetime, timezone

lc = boto3.client('lambda', region_name='eu-west-1')

target_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')

print('[INVOKING] Featured meeting picks analysis')
print(f'  Date: {target_date}')
print()

try:
    # Invoke surebet-featured-meeting
    resp = lc.invoke(
        FunctionName='surebet-featured-meeting',
        InvocationType='RequestResponse',
        Payload=json.dumps({'target_date': target_date, 'date': target_date}).encode()
    )
    
    body = json.loads(resp['Payload'].read())
    if isinstance(body, str):
        body = json.loads(body)
    
    status = resp.get('StatusCode', 0)
    print(f'[RESULT] Status: {status}')
    
    if 'body' in body:
        result = json.loads(body['body'])
    else:
        result = body
    
    print(f"[FEATURED MEETING]")
    print(f"  Course: {result.get('course', 'N/A')}")
    print(f"  Race count: {result.get('race_count', 0)}")
    print(f"  Settled count: {result.get('settled_count', 0)}")
    print(f"  Success: {result.get('success')}")
    print()
    
    # Now invoke featured-improver-enforcer to boost the picks
    if result.get('race_count', 0) > 0:
        print('[INVOKING] Featured improver enforcer')
        
        # First get the boosted horses from calculate-improver-boost-scores
        print('  1. Calculating improver boosts...')
        boost_resp = lc.invoke(
            FunctionName='calculate-improver-boost-scores',
            InvocationType='RequestResponse',
            Payload=json.dumps({'target_date': target_date}).encode()
        )
        
        boost_body = json.loads(boost_resp['Payload'].read())
        if isinstance(boost_body, str):
            boost_body = json.loads(boost_body)
        
        if 'body' in boost_body:
            boost_result = json.loads(boost_body['body'])
        else:
            boost_result = boost_body
        
        all_horses = boost_result.get('all_horses', [])
        print(f"    Horses evaluated: {len(all_horses)}")
        print(f"    Boost summary: {boost_result.get('boost_summary', {})}")
        
        # Now apply featured improver boost
        print('  2. Applying improver boost to featured picks...')
        featured_resp = lc.invoke(
            FunctionName='featured-improver-enforcer',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'target_date': target_date,
                'featured_course': result.get('course'),
                'all_horses': all_horses
            }).encode()
        )
        
        featured_body = json.loads(featured_resp['Payload'].read())
        if isinstance(featured_body, str):
            featured_body = json.loads(featured_body)
        
        if 'body' in featured_body:
            featured_result = json.loads(featured_body['body'])
        else:
            featured_result = featured_body
        
        print(f"    Featured picks updated: {len(featured_result.get('featured_picks_updated', []))}")
        print(f"    Boost summary: {featured_result.get('boost_summary', {})}")
        print()
        
        print('✓ Featured meeting picks with improver boost generated successfully')
        print(f'  Course: {result.get("course")}')
        print(f'  Races: {result.get("race_count")}')
        print(f'  Picks boosted: {featured_result.get("boost_summary", {}).get("picks_boosted", 0)}')
        print(f'  Avg boost: +{featured_result.get("boost_summary", {}).get("avg_boost_amount", 0):.1f} pts')
    else:
        print('✓ Featured meeting analyzed (no races or all settled)')
    
except Exception as e:
    print(f'[ERROR] {e}')
    import traceback
    traceback.print_exc()

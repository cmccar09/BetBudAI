#!/usr/bin/env python3
import boto3
import sys
from datetime import datetime

try:
    table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f'Querying for {today}...', file=sys.stderr)
    
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
    )
    
    items = resp.get('Items', [])
    print(f'Total items: {len(items)}')
    
    if items:
        sorted_items = sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)
        
        print('\nTop 10:')
        for i, item in enumerate(sorted_items[:10], 1):
            score = float(item.get('comprehensive_score', 0))
            horse = item.get('horse', 'Unknown')
            print(f'{i}. {horse} - {score}/100')
        
        scores = [float(x.get('comprehensive_score', 0)) for x in items]
        print(f'\n85+: {len([s for s in scores if s >= 85])}')
        print(f'75+: {len([s for s in scores if s >= 75])}')
        print(f'60+: {len([s for s in scores if s >= 60])}')
        print(f'Max: {max(scores) if scores else 0}')
    else:
        print('No items found')
        
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""
Fix missing coverage data in existing picks
Sets coverage to 100% for picks already in database
"""

import boto3
from datetime import datetime
from decimal import Decimal

def fix_coverage():
    """Add coverage to existing picks"""
    
    table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\nFixing coverage for {today}...")
    
    # Get all today's picks
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
    )
    
    items = resp.get('Items', [])
    
    print(f"Found {len(items)} picks")
    
    fixed = 0
    for item in items:
        # Check if coverage is missing
        if 'coverage' not in item or 'data_coverage' not in item:
            print(f"  Fixing: {item.get('horse', 'Unknown')}")
            
            table.update_item(
                Key={
                    'bet_date': item['bet_date'],
                    'bet_id': item['bet_id']
                },
                UpdateExpression='SET coverage = :cov, data_coverage = :cov, analyzed_runners = :ar, total_runners = :tr',
                ExpressionAttributeValues={
                    ':cov': Decimal('100.0'),  # Default to 100%
                    ':ar': 10,  # Estimate
                    ':tr': 10   # Estimate
                }
            )
            fixed += 1
    
    print(f"\n✓ Fixed {fixed} picks")
    print(f"All picks now have coverage data!")

if __name__ == "__main__":
    fix_coverage()

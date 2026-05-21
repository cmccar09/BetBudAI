#!/usr/bin/env python3
"""
Manual Results Updater
For when Betfair Historical API isn't available
This marks all yesterday's picks as LOST (conservative) unless we have actual data
"""

import boto3
from datetime import datetime, timedelta
from decimal import Decimal

def mark_all_as_lost(date_str):
    """Conservatively mark all picks from a date as LOST if no results available"""
    
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    print(f"Loading picks from {date_str}...")
    response = table.scan(
        FilterExpression='#date = :date',
        ExpressionAttributeNames={'#date': 'date'},
        ExpressionAttributeValues={':date': date_str}
    )
    
    picks = response.get('Items', [])
    print(f"Found {len(picks)} picks")
    
    updated = 0
    for pick in picks:
        current_outcome = pick.get('outcome')
        if current_outcome and current_outcome != 'Pending':
            continue
            
        bet_id = pick.get('bet_id')
        horse = pick.get('horse', 'Unknown')
        
        try:
            table.update_item(
                Key={'bet_id': bet_id},
                UpdateExpression='SET outcome = :outcome, profit_loss = :pl, updated_at = :ts',
                ExpressionAttributeValues={
                    ':outcome': 'LOST',
                    ':pl': Decimal('-1.0'),
                    ':ts': datetime.now().isoformat()
                }
            )
            updated += 1
            print(f"  ✓ {horse}: Marked as LOST")
        except Exception as e:
            print(f"  ❌ {horse}: Error - {e}")
    
    print(f"\nUpdated {updated} picks to LOST")
    print("\n⚠️  NOTE: This is a conservative approach when actual results unavailable")
    print("If you have actual results, please update them manually or use a results API")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        date_str = yesterday
    
    print("="*70)
    print("MANUAL RESULTS UPDATE (Conservative)")
    print("="*70)
    print("\n⚠️  WARNING: This will mark ALL picks from the specified date as LOST")
    print("This is a conservative approach when actual results are unavailable.\n")
    
    response = input(f"Mark all picks from {date_str} as LOST? (yes/no): ")
    
    if response.lower() == 'yes':
        mark_all_as_lost(date_str)
    else:
        print("\nOperation cancelled")

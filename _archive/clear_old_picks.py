#!/usr/bin/env python3
"""Clear old picks from DynamoDB for today's date"""

import boto3
from datetime import datetime
import sys

def clear_todays_picks():
    """Delete all picks from today's date"""
    
    region = 'eu-west-1'
    table_name = 'SureBetBets'
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    print(f"Connecting to DynamoDB table: {table_name}")
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(table_name)
    
    print(f"Scanning for picks from {today}...")
    
    # Scan for today's picks
    response = table.scan(
        FilterExpression='#d = :date',
        ExpressionAttributeNames={'#d': 'date'},
        ExpressionAttributeValues={':date': today}
    )
    
    items = response.get('Items', [])
    print(f"Found {len(items)} picks to delete")
    
    if len(items) == 0:
        print("No picks to delete")
        return
    
    # Show what we're deleting
    print("\nPicks to delete:")
    for item in items:
        horse = item.get('horse', 'Unknown')
        roi = item.get('roi', 'N/A')
        timestamp = item.get('timestamp', 'N/A')
        print(f"  - {horse} (ROI: {roi}%, {timestamp})")
    
    confirm = input(f"\nDelete {len(items)} picks? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled")
        return
    
    # Delete each item
    deleted = 0
    for item in items:
        bet_id = item.get('bet_id')
        if bet_id:
            try:
                table.delete_item(Key={'bet_id': bet_id})
                deleted += 1
                print(f"✓ Deleted: {item.get('horse', 'Unknown')}")
            except Exception as e:
                print(f"✗ Error deleting {bet_id}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Deleted {deleted} of {len(items)} picks")
    print(f"{'='*60}")
    print("\nFrontend will now show empty state")
    print("Next scheduled run will generate fresh picks")

if __name__ == "__main__":
    try:
        clear_todays_picks()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

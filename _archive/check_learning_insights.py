#!/usr/bin/env python3
"""Check recent learning insights from the system"""

import boto3
from datetime import datetime

def check_recent_learnings():
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetLearnings')
    
    response = table.scan()
    items = response.get('Items', [])
    
    if not items:
        print("No learning insights found in database")
        return
    
    # Sort by timestamp
    recent = sorted(items, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
    
    print(f"Found {len(items)} total learning insights")
    print(f"\nMost Recent 10 Learnings:\n")
    
    for i, item in enumerate(recent, 1):
        print(f"{i}. {item.get('timestamp', 'N/A')}")
        print(f"   Type: {item.get('learning_type', 'N/A')}")
        print(f"   Insight: {item.get('insight', 'N/A')}")
        print(f"   Confidence: {item.get('confidence', 'N/A')}")
        print()

if __name__ == '__main__':
    check_recent_learnings()

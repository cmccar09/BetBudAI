"""
Data Migration Script
====================
Migrates data from old Betting project to new BetBudAI structure.
Safe: read-only from source, creates new DynamoDB items in target environment.
"""

import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone
import sys

SOURCE_REGION = 'eu-west-1'
TARGET_REGION = 'eu-west-1'
SOURCE_TABLE = 'SureBetBets'
TARGET_TABLE = 'SureBetBets'

def migrate_picks_data():
    """Migrate all picks from old table to new table."""
    source_db = boto3.resource('dynamodb', region_name=SOURCE_REGION)
    target_db = boto3.resource('dynamodb', region_name=TARGET_REGION)
    
    source_table = source_db.Table(SOURCE_TABLE)
    target_table = target_db.Table(TARGET_TABLE)
    
    print("[Migration] Starting picks data migration...")
    
    # Scan all items from source
    items_migrated = 0
    items_skipped = 0
    
    kwargs = {}
    while True:
        response = source_table.scan(**kwargs)
        items = response.get('Items', [])
        
        for item in items:
            try:
                # Validate item has required keys
                if 'bet_date' not in item or 'bet_id' not in item:
                    print(f"  ⚠ Skipping item without bet_date/bet_id: {item}")
                    items_skipped += 1
                    continue
                
                # Write to target
                target_table.put_item(Item=item)
                items_migrated += 1
                
                if items_migrated % 100 == 0:
                    print(f"  → {items_migrated} items migrated...")
            
            except Exception as e:
                print(f"  ✗ Error migrating item {item.get('bet_id')}: {e}")
                items_skipped += 1
        
        # Check for pagination
        if 'LastEvaluatedKey' not in response:
            break
        kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
    
    print(f"[Migration] Complete! {items_migrated} migrated, {items_skipped} skipped")
    return items_migrated, items_skipped


def verify_migration():
    """Verify migrated data integrity."""
    db = boto3.resource('dynamodb', region_name=TARGET_REGION)
    table = db.Table(TARGET_TABLE)
    
    print("[Verification] Checking migrated data...")
    
    # Count total items
    response = table.scan(Select='COUNT')
    total_count = response['Count']
    
    # Sample check
    response = table.scan(Limit=10)
    sample_items = response.get('Items', [])
    
    print(f"  Total items in target: {total_count}")
    print(f"  Sample items: {len(sample_items)}")
    
    # Check for required fields
    required_fields = ['bet_date', 'bet_id', 'horse', 'course', 'odds']
    missing_fields = 0
    
    for item in sample_items:
        for field in required_fields:
            if field not in item:
                print(f"  ✗ Missing field '{field}' in {item.get('bet_id')}")
                missing_fields += 1
    
    if missing_fields == 0:
        print("[Verification] ✓ Data integrity check passed!")
        return True
    else:
        print(f"[Verification] ✗ Found {missing_fields} missing fields")
        return False


def rollback_migration():
    """Delete all items from target table (for testing only)."""
    print("[Rollback] WARNING: This will DELETE all items from target table!")
    response = input("Type 'yes' to confirm: ")
    
    if response.lower() != 'yes':
        print("Rollback cancelled")
        return
    
    db = boto3.resource('dynamodb', region_name=TARGET_REGION)
    table = db.Table(TARGET_TABLE)
    
    print("[Rollback] Deleting all items...")
    
    kwargs = {}
    deleted = 0
    
    while True:
        response = table.scan(ProjectionExpression='bet_date, bet_id', **kwargs)
        items = response.get('Items', [])
        
        for item in items:
            table.delete_item(Key={
                'bet_date': item['bet_date'],
                'bet_id': item['bet_id'],
            })
            deleted += 1
        
        if 'LastEvaluatedKey' not in response:
            break
        kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
    
    print(f"[Rollback] Deleted {deleted} items")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [migrate|verify|rollback]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'migrate':
        migrated, skipped = migrate_picks_data()
        verify_migration()
    elif command == 'verify':
        verify_migration()
    elif command == 'rollback':
        rollback_migration()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

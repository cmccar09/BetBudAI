"""
Create BetBudAI_ValidationLogs DynamoDB Table
=============================================
Stores validation results for race field completeness checks.
Ensures every race has all horses analyzed before picks are deployed.
"""

import sys
import boto3
from botocore.exceptions import ClientError

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

dynamodb = boto3.client('dynamodb', region_name='eu-west-1')

TABLE_NAME = 'BetBudAI_ValidationLogs'

def create_validation_table():
    """Create validation logs table with TTL enabled."""

    try:
        # Check if table exists
        try:
            dynamodb.describe_table(TableName=TABLE_NAME)
            print(f"[OK] Table {TABLE_NAME} already exists")
            return
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise

        # Create table
        print(f"Creating table {TABLE_NAME}...")

        response = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'validation_date', 'KeyType': 'HASH'},   # Partition key
                {'AttributeName': 'validation_id', 'KeyType': 'RANGE'}     # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'validation_date', 'AttributeType': 'S'},
                {'AttributeName': 'validation_id', 'AttributeType': 'S'},
            ],
            BillingMode='PAY_PER_REQUEST',  # On-demand pricing
            Tags=[
                {'Key': 'Project', 'Value': 'BetBudAI'},
                {'Key': 'Purpose', 'Value': 'Quality gate validation logs'},
            ]
        )

        print(f"[OK] Table {TABLE_NAME} created successfully")
        print(f"  ARN: {response['TableDescription']['TableArn']}")

        # Wait for table to be active
        print("  Waiting for table to be active...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)

        # Enable TTL
        print("  Enabling TTL on 'ttl' attribute...")
        dynamodb.update_time_to_live(
            TableName=TABLE_NAME,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'ttl'
            }
        )

        print(f"[OK] TTL enabled - items will auto-expire after their TTL timestamp")
        print(f"\n[SUCCESS] Table {TABLE_NAME} is ready!")

    except Exception as e:
        print(f"[ERROR] Error creating table: {e}")
        raise


if __name__ == '__main__':
    create_validation_table()

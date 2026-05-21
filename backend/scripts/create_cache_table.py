"""
Create BetBudAICache DynamoDB table for storing pre-calculated data.
Run once to create the table.
"""

import boto3

dynamodb = boto3.client('dynamodb', region_name='eu-west-1')

def create_cache_table():
    """Create the cache table with TTL enabled."""
    try:
        response = dynamodb.create_table(
            TableName='BetBudAICache',
            KeySchema=[
                {
                    'AttributeName': 'cache_key',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'cache_key',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',  # On-demand pricing
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'BetBudAI'
                },
                {
                    'Key': 'Purpose',
                    'Value': 'Performance cache for expensive calculations'
                }
            ]
        )

        print(f"[OK] Table creation initiated: {response['TableDescription']['TableName']}")
        print(f"  Status: {response['TableDescription']['TableStatus']}")
        print(f"  ARN: {response['TableDescription']['TableArn']}")

        # Wait for table to be created
        print("\nWaiting for table to be active...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName='BetBudAICache')
        print("[OK] Table is now ACTIVE")

        # Enable TTL for automatic expiration
        print("\nEnabling TTL on 'ttl' attribute...")
        dynamodb.update_time_to_live(
            TableName='BetBudAICache',
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'ttl'
            }
        )
        print("[OK] TTL enabled - items will auto-expire based on 'ttl' field")

        return True

    except dynamodb.exceptions.ResourceInUseException:
        print("[WARNING] Table 'BetBudAICache' already exists")
        return False
    except Exception as e:
        print(f"[ERROR] Error creating table: {str(e)}")
        return False


if __name__ == '__main__':
    print("Creating BetBudAICache table...\n")
    create_cache_table()
    print("\n" + "="*60)
    print("Cache table setup complete!")
    print("="*60)

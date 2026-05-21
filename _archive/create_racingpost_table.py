"""
CREATE RACINGPOST DYNAMODB TABLE
Run this once to create the RacingPostRaces table
"""

import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')

def create_racingpost_table():
    """Create RacingPostRaces table with proper schema"""
    
    try:
        table = dynamodb.create_table(
            TableName='RacingPostRaces',
            KeySchema=[
                {
                    'AttributeName': 'raceKey',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'scrapeTime',
                    'KeyType': 'RANGE'  # Sort key (allows multiple scrapes of same race)
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'raceKey',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'scrapeTime',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'raceDate',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'DateIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'raceDate',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        # Wait for table to be created
        print("Creating table RacingPostRaces...")
        table.meta.client.get_waiter('table_exists').wait(TableName='RacingPostRaces')
        print("✓ Table created successfully!")
        
        print("\nTable details:")
        print(f"  Name: {table.table_name}")
        print(f"  Status: {table.table_status}")
        print(f"  Item count: {table.item_count}")
        
        return True
    
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print("Table 'RacingPostRaces' already exists")
        return True
    
    except Exception as e:
        print(f"Error creating table: {e}")
        return False

if __name__ == '__main__':
    success = create_racingpost_table()
    
    if success:
        print("\n✓ Ready to start scraping!")
        print("\nRun: python scheduled_racingpost_scraper.py")

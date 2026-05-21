"""
CHELTENHAM FESTIVAL 2026 DATABASE SCHEMA
Create dedicated table for Cheltenham Festival research and betting
Tuesday 10 - Friday 13 March 2026
"""

import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')

def create_cheltenham_festival_table():
    """Create CheltenhamFestival2026 table for dedicated festival tracking"""
    
    try:
        table = dynamodb.create_table(
            TableName='CheltenhamFestival2026',
            KeySchema=[
                {
                    'AttributeName': 'raceId',  # {day}_{raceName}
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'horseId',  # {horseName}_{timestamp}
                    'KeyType': 'RANGE'  # Sort key (allows multiple updates per horse)
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'raceId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'horseId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'festivalDay',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'confidenceRank',
                    'AttributeType': 'N'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'DayIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'festivalDay',
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
                },
                {
                    'IndexName': 'ConfidenceIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'raceId',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'confidenceRank',
                            'KeyType': 'RANGE'
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
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        
        # Wait for table to be created
        print("Creating table CheltenhamFestival2026...")
        table.meta.client.get_waiter('table_exists').wait(TableName='CheltenhamFestival2026')
        print("✓ Table created successfully!")
        
        print("\nTable details:")
        print(f"  Name: {table.table_name}")
        print(f"  Status: {table.table_status}")
        print(f"  Indexes: DayIndex, ConfidenceIndex")
        
        return True
    
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print("Table 'CheltenhamFestival2026' already exists")
        return True
    
    except Exception as e:
        print(f"Error creating table: {e}")
        return False


def initialize_cheltenham_races():
    """Initialize all known Cheltenham Festival races with placeholders"""
    
    table = dynamodb.Table('CheltenhamFestival2026')
    
    # Cheltenham Festival 2026 Race Schedule
    # Based on typical Cheltenham Festival structure
    cheltenham_races = {
        'Tuesday_10_March': [
            {'time': '13:30', 'name': 'Supreme Novices Hurdle', 'grade': 'Grade 1', 'distance': '2m 87y'},
            {'time': '14:10', 'name': 'Arkle Challenge Trophy', 'grade': 'Grade 1', 'distance': '2m'},
            {'time': '14:50', 'name': 'Ultima Handicap Chase', 'grade': 'Grade 3', 'distance': '3m 1f'},
            {'time': '15:30', 'name': 'Champion Hurdle', 'grade': 'Grade 1', 'distance': '2m 87y'},
            {'time': '16:10', 'name': 'Mares Hurdle', 'grade': 'Grade 1', 'distance': '2m 4f'},
            {'time': '16:50', 'name': 'National Hunt Chase', 'grade': 'Amateur', 'distance': '4m'},
            {'time': '17:30', 'name': 'Champion Bumper', 'grade': 'Grade 1', 'distance': '2m 87y'}
        ],
        'Wednesday_11_March': [
            {'time': '13:30', 'name': 'Ballymore Novices Hurdle', 'grade': 'Grade 1', 'distance': '2m 5f'},
            {'time': '14:10', 'name': 'Brown Advisory Novices Chase', 'grade': 'Grade 1', 'distance': '3m'},
            {'time': '14:50', 'name': 'Coral Cup', 'grade': 'Handicap', 'distance': '2m 5f'},
            {'time': '15:30', 'name': 'Queen Mother Champion Chase', 'grade': 'Grade 1', 'distance': '2m'},
            {'time': '16:10', 'name': 'Cross Country Chase', 'grade': 'Grade 3', 'distance': '3m 6f'},
            {'time': '16:50', 'name': 'Grand Annual Chase', 'grade': 'Handicap', 'distance': '2m'},
            {'time': '17:30', 'name': 'Champion Bumper (NH Flat Race)', 'grade': 'Grade 1', 'distance': '2m 87y'}
        ],
        'Thursday_12_March': [
            {'time': '13:30', 'name': 'Turners Novices Chase', 'grade': 'Grade 1', 'distance': '2m'},
            {'time': '14:10', 'name': 'Pertemps Network Final', 'grade': 'Handicap', 'distance': '3m'},
            {'time': '14:50', 'name': 'Ryanair Chase', 'grade': 'Grade 1', 'distance': '2m 5f'},
            {'time': '15:30', 'name': 'Stayers Hurdle', 'grade': 'Grade 1', 'distance': '3m'},
            {'time': '16:10', 'name': 'Plate Handicap Chase', 'grade': 'Handicap', 'distance': '2m 4f'},
            {'time': '16:50', 'name': 'Mares Chase', 'grade': 'Grade 2', 'distance': '2m 4f'},
            {'time': '17:30', 'name': 'Fulke Walwyn Kim Muir', 'grade': 'Handicap', 'distance': '3m 2f'}
        ],
        'Friday_13_March': [
            {'time': '13:30', 'name': 'Triumph Hurdle', 'grade': 'Grade 1', 'distance': '2m 1f'},
            {'time': '14:10', 'name': 'County Handicap Hurdle', 'grade': 'Handicap', 'distance': '2m 1f'},
            {'time': '14:50', 'name': 'Albert Bartlett Novices Hurdle', 'grade': 'Grade 1', 'distance': '3m'},
            {'time': '15:30', 'name': 'Cheltenham Gold Cup', 'grade': 'Grade 1', 'distance': '3m 2f'},
            {'time': '16:10', 'name': 'St James\'s Place Foxhunter', 'grade': 'Amateur', 'distance': '2m 5f'},
            {'time': '16:50', 'name': 'Martin Pipe Conditional', 'grade': 'Handicap', 'distance': '2m 4f'},
            {'time': '17:30', 'name': 'Grand Annual Chase', 'grade': 'Handicap', 'distance': '2m'}
        ]
    }
    
    print("\nInitializing Cheltenham Festival 2026 races...")
    
    for day, races in cheltenham_races.items():
        day_name = day.replace('_', ' ')
        print(f"\n{day_name}:")
        
        for race in races:
            race_id = f"{day}_{race['name'].replace(' ', '_')}"
            
            # Create race entry
            item = {
                'raceId': race_id,
                'horseId': 'RACE_INFO',
                'festivalDay': day,
                'raceTime': race['time'],
                'raceName': race['name'],
                'raceGrade': race['grade'],
                'raceDistance': race['distance'],
                'raceDate': day.split('_')[1] + '_' + day.split('_')[2] + '_March_2026',
                'status': 'UPCOMING',
                'lastUpdated': datetime.now().isoformat(),
                'researchNotes': [],
                'totalHorses': 0,
                'confidenceRank': 0
            }
            
            table.put_item(Item=item)
            print(f"  ✓ {race['time']} - {race['name']} ({race['grade']})")
    
    print("\n✓ All Cheltenham Festival races initialized!")
    return True


if __name__ == '__main__':
    print("="*80)
    print("CHELTENHAM FESTIVAL 2026 - DATABASE SETUP")
    print("Tuesday 10 - Friday 13 March 2026")
    print("="*80)
    
    success = create_cheltenham_festival_table()
    
    if success:
        print("\n" + "="*80)
        initialize_cheltenham_races()
        print("\n" + "="*80)
        print("\n✓ Cheltenham Festival 2026 database ready!")
        print("\nNext steps:")
        print("  1. Run cheltenham_festival_scraper.py to populate horse data")
        print("  2. Access via cheltenham_festival.html")
        print("="*80)

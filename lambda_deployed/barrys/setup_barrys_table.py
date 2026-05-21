"""
setup_barrys_table.py
Creates BarrysCompetition DynamoDB table and seeds initial competition structure
"""
import boto3
from botocore.exceptions import ClientError
from barrys_config import DYNAMODB_TABLE, DYNAMODB_REGION, ENTRIES, FESTIVAL_RACES, COMPETITION_NAME, PRIZE
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION)
client = boto3.client('dynamodb', region_name=DYNAMODB_REGION)


def create_table():
    """Create the DynamoDB table if it doesn't exist"""
    try:
        table = dynamodb.create_table(
            TableName=DYNAMODB_TABLE,
            KeySchema=[
                {'AttributeName': 'entry', 'KeyType': 'HASH'},
                {'AttributeName': 'race_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'entry', 'AttributeType': 'S'},
                {'AttributeName': 'race_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        print(f"[OK] Table '{DYNAMODB_TABLE}' created successfully")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"[OK] Table '{DYNAMODB_TABLE}' already exists")
            return dynamodb.Table(DYNAMODB_TABLE)
        raise


def seed_picks_skeleton():
    """Create empty pick slots for all entries and all races"""
    table = dynamodb.Table(DYNAMODB_TABLE)
    seeded = 0

    for entry_name, entry_info in ENTRIES.items():
        for race_key, race_info in FESTIVAL_RACES.items():
            race_date = {1: "2026-03-10", 2: "2026-03-11", 3: "2026-03-12", 4: "2026-03-13"}[race_info["day"]]
            race_id = f"{race_date}_{race_key}"

            try:
                # Check if already exists
                existing = table.get_item(Key={'entry': entry_name, 'race_id': race_id})
                if 'Item' in existing:
                    continue

                table.put_item(Item={
                    'entry': entry_name,
                    'race_id': race_id,
                    'race_key': race_key,
                    'race_name': race_info['name'],
                    'race_date': race_date,
                    'race_time': race_info['time'],
                    'day': race_info['day'],
                    'grade': race_info['grade'],
                    'strategy': entry_info['strategy'],
                    'horse': 'TBC',
                    'odds': None,
                    'points': 0,
                    'result': 'pending',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
                seeded += 1
            except Exception as e:
                print(f"  [ERROR] {entry_name} / {race_key}: {e}")

    print(f"[OK] Seeded {seeded} pick slots across {len(ENTRIES)} entries x {len(FESTIVAL_RACES)} races")


def show_summary():
    """Display competition overview"""
    print(f"""
{'='*70}
{COMPETITION_NAME.upper()}
Prize: GBP {PRIZE:,}
Festival: 10-13 March 2026 | 28 Races | 4 Days
{'='*70}
Entries:
""")
    for entry, info in ENTRIES.items():
        print(f"  [{entry}]")
        print(f"    Strategy : {info['strategy'].upper()}")
        print(f"    Approach : {info['description']}")
    print(f"""
Points: 1st=10pts | 2nd=5pts | 3rd=3pts | Unplaced=0pts
Max possible: 28 races x 10pts = 280pts
{'='*70}
""")


if __name__ == '__main__':
    print(f"\nSetting up Barry's Competition...\n")
    table = create_table()
    seed_picks_skeleton()
    show_summary()
    print("Done. Run generate_picks.py next to populate selections.")

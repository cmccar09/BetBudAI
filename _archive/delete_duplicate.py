import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

# Delete the bad duplicate entry
table.delete_item(
    Key={
        'bet_date': '2026-02-10',
        'bet_id': '2026-02-10T133500.000Z_Ayr_The_Coffey_Boy'
    }
)

print("✓ Deleted duplicate entry for The Coffey Boy")

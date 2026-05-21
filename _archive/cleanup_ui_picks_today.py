import boto3
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Get all today's UI picks
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

ui_picks = [i for i in response['Items'] if i.get('show_in_ui') == True]

print(f"\nFound {len(ui_picks)} picks with show_in_ui=True\n")

# The 6 latest picks we want to keep (from the most recent run)
keep_horses = [
    'Thank You Maam',
    'Courageous Strike', 
    'Folly Master',
    'Haarar',
    'Jaitroplaclasse',
    'Secret Road'
]

print("Keeping these 6 picks visible on UI:")
for h in keep_horses:
    print(f"  ✓ {h}")

print(f"\nHiding {len(ui_picks) - 6} old picks from UI (keeping for learning):\n")

# Hide all others from UI
for pick in ui_picks:
    horse = pick.get('horse', '')
    
    if horse not in keep_horses:
        table.update_item(
            Key={
                'bet_date': pick['bet_date'],
                'bet_id': pick['bet_id']
            },
            UpdateExpression='SET show_in_ui = :val',
            ExpressionAttributeValues={':val': False}
        )
        print(f"  ✗ Hidden: {horse} (kept in DB for learning)")

print(f"\n✓ Done! UI will now show only 6 picks, all others used for learning only\n")

import boto3
from decimal import Decimal

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = '2026-02-10'

# Get all UI picks for today
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

ui_picks = [i for i in response['Items'] if i.get('show_in_ui')]

print(f"Adding stake and odds to {len(ui_picks)} UI picks")

for pick in ui_picks:
    horse = pick.get('horse')
    
    # Get odds - prefer starting_price if available, otherwise use odds
    odds_value = pick.get('starting_price') or pick.get('odds') or Decimal('0')
    
    # Set default stake of 2.0 if not set
    stake_value = pick.get('stake') or Decimal('2.0')
    
    # Update the pick
    table.update_item(
        Key={
            'bet_date': today,
            'bet_id': pick['bet_id']
        },
        UpdateExpression='SET stake = :s, odds = :o',
        ExpressionAttributeValues={
            ':s': stake_value,
            ':o': odds_value
        }
    )
    
    print(f"✓ {horse:30} stake={float(stake_value)}, odds={float(odds_value)}")

print("\nDone! All UI picks now have stake and odds set.")

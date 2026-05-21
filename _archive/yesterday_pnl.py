import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(yesterday)
)

picks = response['Items']
print(f"\n{'='*100}")
print(f"YESTERDAY'S RESULTS ({yesterday}): {len(picks)} BETS")
print(f"{'='*100}\n")

wins = 0
losses = 0
places = 0
no_outcome = 0
total_staked = 0
total_returns = 0

for i, pick in enumerate(picks, 1):
    horse = pick.get('horse', 'Unknown')
    venue = pick.get('course', 'Unknown')
    outcome = pick.get('outcome', None)
    bet_type = pick.get('bet_type', 'N/A')
    odds = float(pick.get('odds', 0))
    stake = float(pick.get('stake', 0))
    conf = pick.get('combined_confidence', 'N/A')
    
    total_staked += stake
    
    # Calculate returns
    returns = 0
    if outcome == 'win':
        wins += 1
        returns = stake * odds
        status_symbol = "WIN"
    elif outcome == 'place':
        places += 1
        ew_fraction = float(pick.get('ew_fraction', 0.2))
        returns = stake * (1 + (odds - 1) * ew_fraction)
        status_symbol = "PLACE"
    elif outcome == 'loss':
        losses += 1
        returns = 0
        status_symbol = "LOST"
    else:
        no_outcome += 1
        status_symbol = "PENDING"
    
    total_returns += returns
    profit = returns - stake
    
    print(f"{i:2}. {horse:25} @ {venue:20}")
    print(f"    Status: {status_symbol:10} | {bet_type:3} @ {odds:5.1f}/1 | Conf: {conf}%")
    print(f"    Stake: £{stake:6.2f} | Returns: £{returns:6.2f} | P/L: £{profit:+7.2f}")
    print()

print(f"{'='*100}")
print(f"\nSUMMARY:")
print(f"  Total Bets:    {len(picks)}")
print(f"  Wins:          {wins}")
print(f"  Places:        {places}")
print(f"  Losses:        {losses}")
print(f"  No Outcome:    {no_outcome}")
print(f"\n  Total Staked:  £{total_staked:.2f}")
print(f"  Total Returns: £{total_returns:.2f}")
print(f"  Profit/Loss:   £{total_returns - total_staked:+.2f}")
if total_staked > 0:
    roi_pct = ((total_returns - total_staked) / total_staked) * 100
    print(f"  ROI:           {roi_pct:+.1f}%")
print(f"\n{'='*100}\n")

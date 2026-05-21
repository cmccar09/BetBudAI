import boto3
import json
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Query today's picks
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-05-20'}
)

items = response['Items']
print(f"\n{'='*70}")
print(f"BetBudAI Results Summary - May 20, 2026")
print(f"{'='*70}\n")

total_picks = 0
wins = 0
places = 0
losses = 0
pending = 0
total_stake = 0
total_return = 0

results_detail = []

for item in items:
    horse = item.get('horse_name', 'Unknown')
    course = item.get('course', 'Unknown')
    race_time = item.get('race_time', 'Unknown')
    odds = float(item.get('odds', 0))
    result = item.get('actual_result', 'PENDING')
    score = item.get('comprehensive_score', 0)

    total_picks += 1
    stake = 1.0  # £1 per pick
    total_stake += stake

    returns = 0
    if result == 'WIN':
        wins += 1
        returns = stake * odds
        total_return += returns
        status = f"[WIN] at {odds:.1f}"
    elif result == 'PLACED':
        places += 1
        place_return = stake * (1 + (odds - 1) * 0.25)  # EW place terms
        returns = place_return
        total_return += returns
        status = f"[PLACE] at {odds:.1f}"
    elif result == 'LOSS':
        losses += 1
        status = f"[LOSS]"
    else:
        pending += 1
        status = f"[PENDING]"

    results_detail.append({
        'horse': horse,
        'course': course,
        'time': race_time,
        'odds': odds,
        'result': result,
        'score': score,
        'status': status,
        'returns': returns
    })

# Sort by time
results_detail.sort(key=lambda x: x['time'])

# Print detailed results
print(f"{'Horse':<25} {'Course':<15} {'Time':<8} {'Odds':<6} {'Result':<15} {'Returns':<10}")
print(f"{'-'*90}")

for r in results_detail:
    print(f"{r['horse']:<25} {r['course']:<15} {r['time']:<8} {r['odds']:<6.1f} {r['status']:<15} GBP{r['returns']:<9.2f}")

# Calculate ROI (only on settled bets)
settled_picks = wins + places + losses
settled_stake = settled_picks * 1.0

if settled_stake > 0:
    profit = total_return - settled_stake
    roi_pct = (profit / settled_stake * 100)
    win_rate = (wins / settled_picks * 100)
    place_rate = ((wins + places) / settled_picks * 100)
else:
    profit = 0
    roi_pct = 0
    win_rate = 0
    place_rate = 0

print(f"\n{'='*70}")
print(f"PERFORMANCE SUMMARY")
print(f"{'='*70}")
print(f"Total Picks:        {total_picks}")
print(f"Settled Picks:      {settled_picks}")
print(f"Pending:            {pending}")
print(f"Wins:               {wins} ({win_rate:.1f}%)")
print(f"Places:             {places}")
print(f"Losses:             {losses}")
print(f"Win + Place Rate:   {place_rate:.1f}%")
print(f"\nTotal Stake:        GBP{settled_stake:.2f}")
print(f"Total Returns:      GBP{total_return:.2f}")
print(f"Profit/Loss:        GBP{profit:+.2f}")
print(f"ROI:                {roi_pct:+.1f}%")
print(f"{'='*70}\n")

# Feature highlight
if wins > 0:
    winners = [r for r in results_detail if r['result'] == 'WIN']
    print(f"WINNERS TODAY:")
    for w in winners:
        print(f"   {w['horse']} ({w['course']} {w['time']}) - {w['odds']:.1f} - Returns: GBP{w['returns']:.2f}")
    print()

# Save to file
with open('today_roi_report.txt', 'w') as f:
    f.write(f"BetBudAI ROI Report - May 20, 2026\n")
    f.write(f"{'='*70}\n\n")
    f.write(f"Total Picks: {total_picks}\n")
    f.write(f"Settled: {settled_picks} | Pending: {pending}\n")
    f.write(f"Wins: {wins} ({win_rate:.1f}%) | Places: {places} | Losses: {losses}\n\n")
    f.write(f"Stake: GBP{settled_stake:.2f}\n")
    f.write(f"Returns: GBP{total_return:.2f}\n")
    f.write(f"Profit: GBP{profit:+.2f}\n")
    f.write(f"ROI: {roi_pct:+.1f}%\n\n")
    if wins > 0:
        f.write("WINNERS:\n")
        for w in winners:
            f.write(f"  - {w['horse']} ({w['course']}) at {w['odds']:.1f}\n")

print("Report saved to: today_roi_report.txt")

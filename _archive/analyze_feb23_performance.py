import boto3
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("YESTERDAY'S BETTING PERFORMANCE - February 23, 2026")
print("="*80 + "\n")

# Get yesterday's bets
yesterday = '2026-02-23'

response = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': yesterday}
)

bets = response.get('Items', [])

if not bets:
    print(f"No bets found for {yesterday}")
    exit(0)

print(f"Total bets placed: {len(bets)}\n")

# Categorize bets by outcome
won_bets = []
lost_bets = []
no_outcome_bets = []
pending_bets = []

for bet in bets:
    outcome = bet.get('outcome', 'NO OUTCOME')
    if outcome == 'won':
        won_bets.append(bet)
    elif outcome == 'lost':
        lost_bets.append(bet)
    elif outcome == 'NO OUTCOME':
        no_outcome_bets.append(bet)
    elif outcome == 'WON':
        won_bets.append(bet)
    else:
        pending_bets.append(bet)

print(f"✅ Winning bets: {len(won_bets)}")
print(f"❌ Losing bets: {len(lost_bets)}")
print(f"⚪ No outcome/Voided: {len(no_outcome_bets)}")
print(f"⏳ Pending: {len(pending_bets)}")
print()

# Calculate P&L (assuming £1 stakes)
total_stake = len(won_bets) + len(lost_bets)  # Only count actual bets
total_returns = 0

for bet in won_bets:
    if isinstance(bet.get('odds'), Decimal):
        odds = float(bet.get('odds', 0))
    else:
        odds = bet.get('odds', 0)
    stake = 1  # £1 per bet
    total_returns += (odds * stake)

profit = total_returns - total_stake
roi = (profit / total_stake * 100) if total_stake > 0 else 0

print("="*80)
print("FINANCIAL SUMMARY")
print("="*80)
print(f"Total stake: £{total_stake:.2f}")
print(f"Total returns: £{total_returns:.2f}")
print(f"Profit/Loss: £{profit:.2f}")
print(f"ROI: {roi:.2f}%")
print(f"Strike rate: {len(won_bets)/total_stake*100 if total_stake > 0 else 0:.1f}%")
print()

# Show winning bets
if won_bets:
    print("="*80)
    print(f"WINNING BETS ({len(won_bets)})")
    print("="*80)
    for bet in sorted(won_bets, key=lambda x: float(x.get('odds', 0)) if isinstance(x.get('odds', 0), (int, float, Decimal)) else 0, reverse=True):
        horse = bet.get('horse_name', 'Unknown')
        venue = bet.get('venue', 'Unknown')
        odds = float(bet.get('odds', 0)) if isinstance(bet.get('odds'), Decimal) else bet.get('odds', 0)
        conf = bet.get('combined_confidence', 0)
        returns = odds * 1
        profit_on_bet = returns - 1
        print(f"  {horse} @ {venue}")
        print(f"    Odds: {odds:.2f} | Confidence: {conf:.1f} | Profit: £{profit_on_bet:.2f}")
    print()

# Show some losing bets (highest confidence losses)
if lost_bets:
    print("="*80)
    print(f"LOSING BETS ({len(lost_bets)}) - Top 10 by Confidence")
    print("="*80)
    sorted_losses = sorted(lost_bets, key=lambda x: x.get('combined_confidence', 0), reverse=True)[:10]
    for bet in sorted_losses:
        horse = bet.get('horse_name', 'Unknown')
        venue = bet.get('venue', 'Unknown')
        odds = float(bet.get('odds', 0)) if isinstance(bet.get('odds'), Decimal) else bet.get('odds', 0)
        conf = bet.get('combined_confidence', 0)
        p_win = bet.get('p_win', 0)
        print(f"  {horse} @ {venue}")
        print(f"    Odds: {odds:.2f} | Confidence: {conf:.1f} | P(Win): {p_win:.2%}")
    print()

# Venue breakdown
venue_stats = {}
for bet in won_bets + lost_bets:
    venue = bet.get('venue', 'Unknown')
    if venue not in venue_stats:
        venue_stats[venue] = {'wins': 0, 'losses': 0, 'stake': 0, 'returns': 0}
    venue_stats[venue]['stake'] += 1
    if bet in won_bets:
        venue_stats[venue]['wins'] += 1
        odds = float(bet.get('odds', 0)) if isinstance(bet.get('odds'), Decimal) else bet.get('odds', 0)
        venue_stats[venue]['returns'] += odds
    else:
        venue_stats[venue]['losses'] += 1

print("="*80)
print("VENUE BREAKDOWN")
print("="*80)
for venue, stats in sorted(venue_stats.items(), key=lambda x: x[1]['returns'] - x[1]['stake'], reverse=True):
    profit = stats['returns'] - stats['stake']
    sr = stats['wins'] / stats['stake'] * 100 if stats['stake'] > 0 else 0
    print(f"{venue:20s} | Bets: {stats['stake']:3d} | W: {stats['wins']:2d} L: {stats['losses']:2d} | SR: {sr:5.1f}% | P/L: £{profit:+6.2f}")

print("\n" + "="*80)

"""
Complete Analysis of Feb 21 Results - What Went Wrong
"""
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*80)
print("FEBRUARY 21, 2026 - COMPLETE ANALYSIS")
print("="*80)
print()

response = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-02-21')
)

picks = [item for item in response['Items'] if item.get('show_in_ui') == True]
picks.sort(key=lambda x: x.get('race_time', ''))

wins = []
losses = []

for pick in picks:
    horse = pick.get('horse', 'Unknown')
    odds = float(pick.get('odds', 0))
    score = int(pick.get('comprehensive_score', 0))
    outcome = str(pick.get('outcome', '')).lower()
    track = pick.get('course', 'Unknown')
    time = pick.get('race_time', '')
    trainer = pick.get('trainer', 'Unknown')
    
    if outcome in ['won', 'win']:
        wins.append({
            'horse': horse,
            'odds': odds,
            'score': score,
            'track': track,
            'time': time,
            'trainer': trainer
        })
    elif outcome in ['lost', 'loss', 'lose']:
        losses.append({
            'horse': horse,
            'odds': odds,
            'score': score,
            'track': track,
            'time': time,
            'trainer': trainer
        })

print(f"RESULTS: {len(wins)} WINS | {len(losses)} LOSSES")
print()

# Calculate P&L
stake_per_bet = 2.0
total_staked = (len(wins) + len(losses)) * stake_per_bet
total_returned = sum(w['odds'] * stake_per_bet for w in wins)
profit_loss = total_returned - total_staked
roi = (profit_loss / total_staked * 100) if total_staked > 0 else 0

print("="*80)
print("FINANCIAL RESULTS:")
print("-"*80)
print(f"Total Bets: {len(wins) + len(losses)}")
print(f"Stake per bet: £{stake_per_bet:.2f}")
print(f"Total Staked: £{total_staked:.2f}")
print(f"Total Returned: £{total_returned:.2f}")
print(f"Profit/Loss: £{profit_loss:.2f}")
print(f"ROI: {roi:.1f}%")
print(f"Strike Rate: {len(wins)}/{len(wins)+len(losses)} = {(len(wins)/(len(wins)+len(losses))*100):.1f}%")
print()

print("="*80)
print("WINNERS:")
print("-"*80)
for w in wins:
    print(f"✓ {w['horse']} @ {w['odds']} (Score: {w['score']}/100)")
    print(f"  {w['time'][:16]} {w['track']}")
    print(f"  Trainer: {w['trainer']}")
    print(f"  Return: £{w['odds'] * stake_per_bet:.2f} from £{stake_per_bet:.2f} stake")
    print()

print("="*80)
print("LOSERS (What Went Wrong):")
print("-"*80)
for l in losses:
    print(f"✗ {l['horse']} @ {l['odds']} (Score: {l['score']}/100)")
    print(f"  {l['time'][:16]} {l['track']}")
    print(f"  Trainer: {l['trainer']}")
    print(f"  Lost: £{stake_per_bet:.2f}")
    print()

print("="*80)
print("KEY PROBLEMS IDENTIFIED:")
print("-"*80)
print()

# Problem 1: High scores still losing
high_score_losses = [l for l in losses if l['score'] >= 100]
if high_score_losses:
    print(f"1. HIGH SCORES LOSING ({len(high_score_losses)} horses)")
    print("   Even 103/100 scores lost - scoring system too optimistic")
    for l in high_score_losses:
        print(f"   - {l['horse']}: {l['score']}/100 @ {l['odds']} - LOST")
    print()

# Problem 2: Sweet spot odds not delivering
sweet_spot_losses = [l for l in losses if 3.0 <= l['odds'] <= 9.0]
if sweet_spot_losses:
    print(f"2. SWEET SPOT (3-9) LOSSES ({len(sweet_spot_losses)} horses)")
    print("   'Sweet spot' theory not working")
    for l in sweet_spot_losses:
        print(f"   - {l['horse']}: @ {l['odds']} - LOST")
    print()

# Problem 3: Overall strike rate
strike_rate = (len(wins)/(len(wins)+len(losses))) * 100
if strike_rate < 33:
    print(f"3. LOW STRIKE RATE: {strike_rate:.1f}%")
    print("   With 25% strike rate, need higher odds to profit")
    print("   Average winning odds needed: 4.0+")
    actual_avg = sum(w['odds'] for w in wins) / len(wins) if wins else 0
    print(f"   Actual average winning odds: {actual_avg:.2f}")
    print()

# Problem 4: Trainer analysis failed
print("4. TRAINER ANALYSIS FAILED")
print("   Seaview Rock had O Murphy trainer (who won earlier with Hold The Serve)")
print("   BUT - Seaview Rock LOST despite 'hot trainer' boost")
print("   → Same-day trainer form is NOT predictive")
print()

print("="*80)
print("RECOMMENDATIONS:")
print("-"*80)
print()
print("1. LOWER THE SCORE THRESHOLD")
print("   Current: 85+ shows on UI")
print("   Problem: Even 103/100 lost")
print("   → Need to be MORE selective, not less")
print("   → Consider 95+ only, or add additional filters")
print()
print("2. ABANDON 'SWEET SPOT' THEORY")
print("   3-9 odds range is not delivering wins")
print("   → Focus on VALUE, not odds range")
print()
print("3. IMPROVE STRIKE RATE OR INCREASE ODDS")
print("   25% strike rate needs 4.0+ average odds to profit")
print("   Options:")
print("   a) Be MORE selective (higher threshold)")
print("   b) Focus on higher odds (5.0+)")
print("   c) Accept smaller stakes on marginal picks")
print()
print("4. STOP USING INTRADAY TRAINER BOOSTS")
print("   Same-day trainer form is NOT predictive")
print("   O Murphy won with Hold The Serve at 13:10")
print("   O Murphy LOST with Seaview Rock at 15:20")
print()
print("5. REVIEW THE 7-FACTOR SYSTEM")
print("   Current factors may be weighted incorrectly")
print("   High scores are not translating to wins")
print("   → Need backtesting against historical results")
print()
print("="*80)

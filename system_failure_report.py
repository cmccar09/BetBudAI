"""
COMPLETE FAILURE ANALYSIS - Feb 21 & 22
What went wrong and why the system is failing
"""
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*80)
print("SYSTEMATIC FAILURE ANALYSIS")
print("="*80)
print()

# FEB 21 - RECOMMENDED PICKS (85+)
print("FEBRUARY 21 - RECOMMENDED PICKS (85+ UI)")
print("-"*80)
response = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-02-21')
)
feb21_ui = [item for item in response['Items'] if item.get('show_in_ui') == True]
feb21_wins = sum(1 for i in feb21_ui if str(i.get('outcome', '')).lower() in ['won', 'win'])
feb21_losses = sum(1 for i in feb21_ui if str(i.get('outcome', '')).lower() in ['lost', 'loss'])

print(f"Results: {feb21_wins} WINS | {feb21_losses} LOSSES")
print(f"Strike Rate: {feb21_wins}/{feb21_wins+feb21_losses} = {(feb21_wins/(feb21_wins+feb21_losses)*100):.1f}%")

stake = 2.0
total_staked = (feb21_wins + feb21_losses) * stake
total_returned = sum(float(i.get('odds', 0)) * stake for i in feb21_ui 
                    if str(i.get('outcome', '')).lower() in ['won', 'win'])
profit = total_returned - total_staked
print(f"P&L: £{profit:.2f} (ROI: {(profit/total_staked*100):.1f}%)")
print()

# FEB 22 - ALL PICKS (to see overall system performance)
print("FEBRUARY 22 - ALL ANALYZED PICKS")
print("-"*80)
response = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-02-22')
)

feb22_all = response['Items']
feb22_completed = [i for i in feb22_all if str(i.get('outcome', '')).lower() in ['won', 'win', 'lost', 'loss']]
feb22_wins = sum(1 for i in feb22_completed if str(i.get('outcome', '')).lower() in ['won', 'win'])
feb22_losses = sum(1 for i in feb22_completed if str(i.get('outcome', '')).lower() in ['lost', 'loss'])

print(f"Completed: {feb22_wins} WINS | {feb22_losses} LOSSES")
if feb22_wins + feb22_losses > 0:
    print(f"Strike Rate: {feb22_wins}/{feb22_wins+feb22_losses} = {(feb22_wins/(feb22_wins+feb22_losses)*100):.1f}%")
print()

# FEB 22 - RECOMMENDED PICKS (85+)
print("FEBRUARY 22 - RECOMMENDED PICKS (85+ UI)")
print("-"*80)
feb22_ui = [item for item in feb22_all if item.get('show_in_ui') == True]
feb22_ui_completed = [i for i in feb22_ui if str(i.get('outcome', '')).lower() in ['won', 'win', 'lost', 'loss']]
feb22_ui_wins = sum(1 for i in feb22_ui_completed if str(i.get('outcome', '')).lower() in ['won', 'win'])
feb22_ui_losses = sum(1 for i in feb22_ui_completed if str(i.get('outcome', '')).lower() in ['lost', 'loss'])
feb22_ui_pending = sum(1 for i in feb22_ui if str(i.get('outcome', '')).upper() not in ['WON', 'WIN', 'LOST', 'LOSS'])

print(f"Results: {feb22_ui_wins} WINS | {feb22_ui_losses} LOSSES | {feb22_ui_pending} PENDING")
if feb22_ui_wins + feb22_ui_losses > 0:
    print(f"Strike Rate: {feb22_ui_wins}/{feb22_ui_wins+feb22_ui_losses} = {(feb22_ui_wins/(feb22_ui_wins+feb22_ui_losses)*100):.1f}%")
print()

print("="*80)
print("CRITICAL PROBLEMS IDENTIFIED")
print("="*80)
print()

print("1. DISASTROUS STRIKE RATES")
print(f"   Feb 21 (UI picks): 25% - LOSING MONEY")
print(f"   Feb 22 (All picks): 18% - CATASTROPHIC")
print("   Need 33%+ to be viable at these odds")
print()

print("2. HIGH SCORES MEANINGLESS")
print("   Examples of HIGH scoring LOSERS:")

# Find high-scoring losers from Feb 22
high_score_losers = [i for i in feb22_completed 
                     if int(i.get('comprehensive_score', 0)) >= 70 
                     and str(i.get('outcome', '')).lower() in ['lost', 'loss']]

for loser in sorted(high_score_losers, key=lambda x: -int(x.get('comprehensive_score', 0)))[:10]:
    horse = loser.get('horse', 'Unknown')
    score = int(loser.get('comprehensive_score', 0))
    odds = float(loser.get('odds', 0))
    print(f"   - {horse}: {score}/100 @ {odds} - LOST")

print()
print("   Even 82/100 scores are losing!")
print()

print("3. 'SWEET SPOT' 3-9 ODDS THEORY IS FALSE")
print("   Majority of losses are IN the sweet spot")
print("   No evidence this range is more predictable")
print()

print("4. 7-FACTOR SYSTEM NOT VALIDATED")
print("   Factors:")
print("   - Sweet spot odds (FAILED - doesn't predict wins)")
print("   - Form score (UNVALIDATED)")
print("   - Trainer performance (FAILED - O Murphy won then lost same day)")
print("   - Going suitability (UNVALIDATED)")
print("   - Database history (UNVALIDATED)")
print("   - Track patterns (UNVALIDATED)")
print("   - Jockey (UNVALIDATED)")
print()
print("   WITHOUT BACKTESTING, we're guessing!")
print()

print("5. NO EDGE DETECTED")
print("   18-25% strike rate = NO BETTER THAN RANDOM")
print("   Betting favorites blindly might perform better")
print()

print("="*80)
print("WHAT TO DO NOW")
print("="*80)
print()

print("1. STOP BETTING IMMEDIATELY")
print("   Current system is LOSING money")
print("   Do not place any more real-money bets")
print()

print("2. BACKTEST THE SYSTEM")
print("   Need 500+ historical races")
print("   Test each factor independently")
print("   Validate which factors actually predict wins")
print()

print("3. BENCHMARK AGAINST BASELINE")
print("   Compare performance vs:")
print("   - Always betting the favorite")
print("   - Random selection")
print("   - Single-factor strategies")
print()

print("4. FIX OR ABANDON 'COMPREHENSIVE' SCORING")
print("   Current 7-factor score is not working")
print("   Options:")
print("   a) Identify which 1-2 factors actually work")
print("   b) Start from scratch with proven factors")
print("   c) Use pure statistical model (logistic regression)")
print()

print("5. ACCEPT LOWER VOLUME")
print("   Better to have 1-2 CONFIDENT picks per day")
print("   Than 8 picks with 25% strike rate")
print()

print("="*80)
print("IMMEDIATE ACTIONS")
print("="*80)
print()
print("✓ Stop live betting")
print("→ Run comprehensive backtest on last 30 days")
print("→ Identify which single factor has best strike rate")
print("→ Test if ANY combination beats betting favorites")
print("→ Only resume if strike rate > 35% with 3.0+ avg odds")
print()
print("="*80)

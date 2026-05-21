"""
Verify today's picks meet all ROI improvement criteria
"""
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': today}
)

ui_picks = [i for i in response.get('Items', []) if i.get('show_in_ui') == True]

print(f"\n{'='*80}")
print(f"ROI CRITERIA VERIFICATION - {today}")
print(f"{'='*80}\n")

print(f"Total UI picks: {len(ui_picks)}\n")

passed = []
failed = []

for pick in sorted(ui_picks, key=lambda x: x.get('combined_confidence', 0), reverse=True):
    horse = pick.get('horse', 'Unknown')
    conf = pick.get('combined_confidence', 0)
    odds = float(pick.get('odds', 0)) if isinstance(pick.get('odds'), Decimal) else pick.get('odds', 0)
    venue = pick.get('venue', 'Unknown')
    race_time = pick.get('race_time', '')[:16]
    
    # Check all criteria
    issues = []
    
    # 1. Confidence >= 80
    if conf < 80:
        issues.append(f"Conf {conf} < 80")
    
    # 2. Odds range 2.0-12.0
    if odds < 2.0:
        issues.append(f"Odds {odds:.2f} < 2.0 (too short)")
    elif odds > 12.0:
        issues.append(f"Odds {odds:.2f} > 12.0 (too long)")
    
    # 3. Value check (10% edge required)
    implied_prob = (1 / float(odds) * 100) if odds > 0 else 0
    our_prob = float(conf)
    edge = our_prob - implied_prob
    
    if edge < 10:
        issues.append(f"Edge {edge:.1f}% < 10% (no value)")
    
    # Calculate stake multiplier
    if conf >= 90:
        stake_mult = "2.0x"
    elif conf >= 85:
        stake_mult = "1.5x"
    elif conf >= 80:
        stake_mult = "1.0x"
    else:
        stake_mult = "0.5x"
    
    status = "✅ PASS" if not issues else "❌ FAIL"
    
    if not issues:
        passed.append(pick)
        print(f"{status} | {conf:5.1f} | {horse:25s} @ {venue:15s}")
        print(f"       Odds: {odds:6.2f} | Implied: {implied_prob:5.1f}% | Edge: {edge:+5.1f}% | Stake: {stake_mult}")
        print(f"       Time: {race_time}")
    else:
        failed.append((pick, issues))
        print(f"{status} | {conf:5.1f} | {horse:25s} @ {venue:15s}")
        print(f"       Issues: {', '.join(issues)}")
    
    print()

print(f"{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")
print(f"✅ Passed all filters: {len(passed)}")
print(f"❌ Failed filters: {len(failed)}")

if failed:
    print(f"\nFailed picks need to be removed from UI:")
    for pick, issues in failed:
        horse = pick.get('horse', 'Unknown')
        print(f"  - {horse}: {', '.join(issues)}")

print(f"\n{'='*80}")
print(f"RECOMMENDED BETS FOR TODAY")
print(f"{'='*80}")

if passed:
    total_units = 0
    for pick in sorted(passed, key=lambda x: x.get('combined_confidence', 0), reverse=True):
        horse = pick.get('horse', 'Unknown')
        conf = pick.get('combined_confidence', 0)
        odds = float(pick.get('odds', 0)) if isinstance(pick.get('odds'), Decimal) else pick.get('odds', 0)
        
        # Calculate stake
        if conf >= 90:
            units = 2.0
        elif conf >= 85:
            units = 1.5
        elif conf >= 80:
            units = 1.0
        else:
            units = 0.5
        
        total_units += units
        stakes = f"£{units * 2:.2f}" if units else "0"
        
        print(f"{horse:25s} | Conf: {conf:5.1f} | Odds: {odds:6.2f} | Stake: {stakes} ({units}u)")
    
    print(f"\nTotal exposure: {total_units} units = £{total_units * 2:.2f}")
else:
    print("No picks meet all criteria")

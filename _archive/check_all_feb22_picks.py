"""
Check ALL Feb 22 picks (not just show_in_ui)
"""
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource ('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*80)
print("FEBRUARY 22, 2026 - ALL PICKS (INCLUDING NON-UI)")
print("="*80)
print()

response = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-02-22')
)

all_picks = response['Items']
all_picks.sort(key=lambda x: x.get('race_time', ''))

print(f"Total Picks in Database: {len(all_picks)}")
print()

wins = 0
losses = 0
pending = 0

for i, pick in enumerate(all_picks, 1):
    horse = pick.get('horse', 'Unknown')
    odds = float(pick.get('odds', 0))
    score = int(pick.get('comprehensive_score', 0))
    outcome = str(pick.get('outcome', 'PENDING')).lower()
    track = pick.get('course', 'Unknown')
    time = pick.get('race_time', '')[:16]
    show_ui = pick.get('show_in_ui', False)
    
    if outcome in ['won', 'win']:
        status = "✓ WON"
        wins += 1
    elif outcome in ['lost', 'loss', 'lose']:
        status = "✗ LOST"
        losses += 1
    else:
        status = "⏳ PENDING"
        pending += 1
    
    ui_marker = "[UI]" if show_ui else "    "
    
    print(f"{ui_marker} {i}. {horse} @ {odds} (Score: {score}/100)")
    print(f"     {time} {track} - {status}")
    print()

print("="*80)
print(f"SUMMARY: {wins} Wins | {losses} Losses | {pending} Pending")
print("="*80)

if losses > 0:
    print()
    print(f"❌ {losses} HORSES LOST")
    print()
    print("LOSERS:")
    for pick in all_picks:
        outcome = str(pick.get('outcome', '')).lower()
        if outcome in ['lost', 'loss', 'lose']:
            horse = pick.get('horse', 'Unknown')
            score = int(pick.get('comprehensive_score', 0))
            odds = float(pick.get('odds', 0))
            print(f"  • {horse} @ {odds} (Score: {score}/100)")

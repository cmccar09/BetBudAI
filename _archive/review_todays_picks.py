"""
Review Today's Picks - Ground Conditions Analysis
"""
import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

ui_picks = [i for i in response['Items'] if i.get('show_in_ui') == True]

print("\n" + "="*100)
print("TODAY'S PICKS REVIEW - Ground Conditions Needed")
print("="*100 + "\n")

# Group by track
tracks = {}
for pick in ui_picks:
    track = pick.get('course', 'Unknown')
    if track not in tracks:
        tracks[track] = []
    tracks[track].append(pick)

for track in sorted(tracks.keys()):
    picks = tracks[track]
    print(f"\n{track.upper()} ({len(picks)} picks)")
    print("-" * 80)
    
    # Wolverhampton is all-weather (polytrack)
    if 'Wolverhampton' in track:
        print("  🏟️  ALL-WEATHER (Polytrack) - Ground conditions less critical")
    else:
        print("  🌧️  TURF TRACK - Ground conditions CRITICAL")
        print("  ⚠️  Need to check: Heavy/Soft favors stamina, Good/Firm favors speed")
    
    print()
    for pick in sorted(picks, key=lambda x: x.get('race_time', '')):
        horse = pick.get('horse', 'Unknown')
        score = pick.get('confidence', 0)
        odds = pick.get('odds', 0)
        form = pick.get('form', '')
        race_time = pick.get('race_time', '')[:16]
        
        print(f"  {race_time:18} {horse:25} Score: {score:2} Odds: {odds:4.1f} Form: {form[:10]}")

print("\n" + "="*100)
print("RECOMMENDATIONS:")
print("="*100)
print("""
1. Wolverhampton picks (5) - Safe, all-weather track with consistent surface
   ✓ Secret Road, Dyrholaey, Towerlands, Far Too Fizzy, Thanh Nam

2. Turf tracks need ground condition analysis:
   - Carlisle (4 picks) - Check going, winter NH track often soft/heavy
   - Taunton (6 picks) - Check going, NH track often testing ground
   - Fairyhouse (1 pick) - Check going, Irish track

3. Action Items:
   - Fetch ground conditions from Betfair/Racing Post
   - Add ground preference to horse profiles (does horse prefer soft/heavy?)
   - Adjust scores: +10 for preferred ground, -15 for unsuitable ground
   - Check recent form on similar ground conditions
""")

print("="*100 + "\n")

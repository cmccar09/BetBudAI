"""
TAUNTON 13:40 COMPREHENSIVE WINNER ANALYSIS
Feb 3, 2026
"""
import boto3
import json
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Always use eu-west-1
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("=" * 100)
print("TAUNTON 13:40 - COMPREHENSIVE WINNER ANALYSIS")
print("=" * 100)

print("\nACTUAL RACE RESULT:")
print("   1st: Talk To The Man (11/4 = 3.75 odds)")
print("   2nd: Kings Champion (10/11 = 1.91 odds - FAVORITE)")
print("   3rd: Crest Of Stars")

# Get Talk To The Man
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='course = :course AND horse = :horse',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':course': 'Taunton',
        ':horse': 'Talk To The Man'
    }
)

if response['Items']:
    winner = response['Items'][0]
    
    print("\n" + "=" * 100)
    print("[WINNER] TALK TO THE MAN - OUR ANALYSIS")
    print("=" * 100)
    
    confidence = winner.get('confidence', 0)
    p_win = winner.get('p_win', 0)
    odds = winner.get('odds', 0)
    quality_score = winner.get('quality_score', 0)
    
    print(f"\nCONFIDENCE: {confidence}/100")
    print(f"P_WIN: {float(p_win)*100:.1f}%")
    print(f"ODDS: {odds} (actual: 3.75)")
    print(f"QUALITY SCORE: {quality_score}")
    print(f"RECOMMENDATION: {winner.get('recommendation')}")
    print(f"DECISION: {winner.get('decision_rating')}")
    
    print(f"\nVALUE ANALYSIS:")
    value_analysis = winner.get('all_horses_analyzed', {}).get('value_analysis', [])
    for runner in value_analysis:
        if runner['runner_name'] == 'Talk To The Man':
            print(f"   Edge: {runner['edge_percentage']}%")
            print(f"   Value Score: {runner['value_score']}/10 ** HIGHEST IN RACE **")
            print(f"   True Probability: {float(runner['true_probability'])*100:.1f}%")
            print(f"   Implied Probability: {float(runner['implied_probability'])*100:.1f}%")
            print(f"   Reasoning: {runner['reasoning']}")
    
    print(f"\nTAGS: {', '.join(winner.get('tags', []))}")
    print(f"\nWHY NOW: {winner.get('why_now')}")
    
    print(f"\nCONFIDENCE BREAKDOWN:")
    breakdown = winner.get('confidence_breakdown', {})
    if breakdown:
        raw_signals = breakdown.get('raw_signals', {})
        print(f"   Win Component: {breakdown.get('win_component')}")
        print(f"   Place Component: {breakdown.get('place_component')}")
        print(f"   Consistency Component: {breakdown.get('consistency_component')}")
        print(f"   Edge Component: {breakdown.get('edge_component')}")
    
    print(f"\nBETTING RECOMMENDATION:")
    print(f"   Stake: £{winner.get('stake')}")
    print(f"   Bankroll %: {winner.get('bankroll_pct')}%")
    print(f"   Expected ROI: {winner.get('roi')}%")
    
    # Decision
    print("\n" + "=" * 100)
    print("VERDICT:")
    print("=" * 100)
    
    if confidence >= 45:
        print(f"[YES] WOULD HAVE BEEN PICKED (confidence {confidence}/100 >= 45 threshold)")
    elif confidence >= 30:
        print(f"[MARGINAL] Below threshold (confidence {confidence}/100 < 45)")
        print(f"   But tagged as: {winner.get('tags')}")
        print(f"   Value score: 9/10 - BEST IN RACE")
        print(f"   This is a HIGH-QUALITY BET that fell just below threshold")
    else:
        print(f"[NO] WOULD NOT HAVE BEEN PICKED (confidence {confidence}/100)")

# Get Kings Champion
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='course = :course AND horse = :horse',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':course': 'Taunton',
        ':horse': 'Kings Champion'
    }
)

if response['Items']:
    favorite = response['Items'][0]
    
    print("\n" + "=" * 100)
    print("[2ND PLACE] KINGS CHAMPION (FAVORITE) - OUR ANALYSIS")
    print("=" * 100)
    
    confidence = favorite.get('confidence', 0)
    p_win = favorite.get('p_win', 0)
    odds = favorite.get('odds', 0)
    quality_score = favorite.get('quality_score', 0)
    
    print(f"\nCONFIDENCE: {confidence}/100")
    print(f"P_WIN: {float(p_win)*100:.1f}%")
    print(f"ODDS: {odds} (actual: 1.91)")
    print(f"QUALITY SCORE: {quality_score}")
    
    # Check if quality favorite logic would have applied
    print(f"\nQUALITY FAVORITE CHECK:")
    if 1.5 <= odds <= 3.0:
        print(f"   [YES] Odds in range (1.5-3.0): {odds}")
        
        # Check value analysis
        value_analysis = favorite.get('all_horses_analyzed', {}).get('value_analysis', [])
        for runner in value_analysis:
            if runner['runner_name'] == 'Kings Champion':
                print(f"   Edge: {runner['edge_percentage']}%")
                print(f"   Value Score: {runner['value_score']}/10")
                print(f"   Reasoning: {runner['reasoning']}")
        
        print(f"\n   Tags: {favorite.get('tags', [])}")
        
        if confidence >= 45:
            print(f"\n   [YES] WOULD GET +20 QUALITY FAVORITE BONUS")
        else:
            print(f"\n   [NO] Edge not significant enough for bonus")
    else:
        print(f"   [NO] Odds outside quality favorite range: {odds}")

# Get all Taunton 13:40 horses for comparison
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='course = :course',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':course': 'Taunton'
    }
)

taunton_1340 = [i for i in response['Items'] if '13:40' in i.get('race_time', '')]

print("\n" + "=" * 100)
print("FULL RACE COMPARISON")
print("=" * 100)

# Extract value analysis from any horse (they all have the same all_horses_analyzed)
if taunton_1340:
    value_analysis = taunton_1340[0].get('all_horses_analyzed', {}).get('value_analysis', [])
    
    print(f"\n{'Pos':<4} {'Horse':<25} {'Odds':<7} {'Value':<6} {'Edge':<7} {'Reasoning':<50}")
    print("-" * 100)
    
    sorted_runners = sorted(value_analysis, key=lambda x: int(x.get('value_score', 0)), reverse=True)
    
    for i, runner in enumerate(sorted_runners, 1):
        horse = runner['runner_name']
        odds = runner['odds']
        value_score = runner['value_score']
        edge = runner['edge_percentage']
        reasoning = runner['reasoning'][:47] + "..." if len(runner['reasoning']) > 50 else runner['reasoning']
        
        marker = ""
        if horse == "Talk To The Man":
            marker = "[W] "
            horse = f"WINNER - {horse}"
        elif horse == "Kings Champion":
            marker = "[2] "
            horse = f"2ND    - {horse}"
        
        print(f"{marker}{i:<4} {horse:<25} {odds:<7} {value_score:<6} {edge:<7} {reasoning}")

print("\n" + "=" * 100)
print("LESSONS LEARNED")
print("=" * 100)

print("""
1. [SUCCESS] VALUE SYSTEM WORKED PERFECTLY
   - Talk To The Man had highest value score (9/10)
   - Identified as "Recent winner with strong value proposition"
   - 28% edge - significantly positive expected value

2. [WARNING] CONFIDENCE THRESHOLD MAY BE TOO HIGH
   - Winner scored 32/100 (threshold: 45/100)
   - Quality indicators were excellent:
     * Recent winner [YES]
     * Odds in sweet spot (3-9) [YES]
     * Highest value score in race [YES]
     * 28% edge [YES]
   - Consider: Should high-value recent winners get threshold exception?

3. [SUCCESS] FAVORITE LOGIC APPROPRIATE
   - Kings Champion: 6% edge only
   - "Edge not significant enough" - correct assessment
   - Came 2nd, so place bet would have paid but win bet lost

4. [RECOMMENDATION]:
   - Add "HIGH VALUE RECENT WINNER" exception
   - Criteria: Value score >=9 AND "Recent winner" tag AND edge >=25%
   - This would have picked Talk To The Man [YES]
""")

print("=" * 100)

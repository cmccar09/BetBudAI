"""
Yesterday's Results Report - Comprehensive Summary
"""

from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key
from collections import defaultdict

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

def get_score(pick):
    conf = pick.get('confidence', 0)
    if isinstance(conf, (int, float)):
        return float(conf)
    if str(conf).upper() == 'HIGH':
        return 75
    if str(conf).upper() == 'MEDIUM':
        return 60
    if str(conf).upper() == 'LOW':
        return 45
    try:
        return float(conf)
    except:
        return 0

print(f"\n{'='*100}")
print(f"YESTERDAY'S FINAL RESULTS - {yesterday}")
print(f"ACTUAL BETTING PICKS ONLY (Learning picks excluded)")
print(f"{'='*100}\n")

response = table.query(KeyConditionExpression=Key('bet_date').eq(yesterday))
all_picks = response['Items']

# Filter to only actual betting picks (60+ confidence or marked as recommended)
def is_betting_pick(pick):
    # Check if it has a stake assigned (actual bet)
    if pick.get('stake') and float(pick.get('stake', 0)) > 0:
        return True
    # Or if it's comprehensive analysis with 60+ confidence
    if pick.get('analysis_method') in ['COMPREHENSIVE', 'COMPREHENSIVE_V2']:
        score = get_score(pick)
        return score >= 60
    return False

picks = [p for p in all_picks if is_betting_pick(p)]

wins = [p for p in picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON']]
losses = [p for p in picks if str(p.get('outcome', '')).upper() in ['LOSS', 'LOST']]
pending = [p for p in picks if str(p.get('outcome', '')).upper() in ['PENDING', '']]

learning_only = len(all_picks) - len(picks)

total_profit = sum(float(p.get('profit', 0)) for p in wins + losses)

print(f"📊 OVERALL PERFORMANCE:")
print(f"{'='*100}")
print(f"Betting Picks: {len(picks)} (Learning-only: {learning_only})")
print(f"Wins: {len(wins)} | Losses: {len(losses)} | Pending: {len(pending)}")
print(f"Strike Rate: {len(wins)/(len(wins)+len(losses))*100:.1f}%")
print(f"Total Profit: £{total_profit:.2f}")
print(f"{'='*100}\n")

comprehensive_picks = [p for p in picks if p.get('analysis_method') in ['COMPREHENSIVE', 'COMPREHENSIVE_V2']]
comp_wins = [p for p in comprehensive_picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON']]
comp_losses = [p for p in comprehensive_picks if str(p.get('outcome', '')).upper() in ['LOSS', 'LOST']]

if comprehensive_picks:
    print(f"🎯 COMPREHENSIVE ANALYSIS PICKS:")
    print(f"{'='*100}")
    print(f"Total: {len(comprehensive_picks)} | Wins: {len(comp_wins)} | Losses: {len(comp_losses)}")
    if len(comprehensive_picks) > 0:
        print(f"Strike Rate: {len(comp_wins)/len(comprehensive_picks)*100:.1f}%")
    
    def get_score(pick):
        conf = pick.get('confidence', 0)
        if isinstance(conf, (int, float)):
            return float(conf)
        if str(conf).upper() == 'HIGH':
            return 75
        if str(conf).upper() == 'MEDIUM':
            return 60
        if str(conf).upper() == 'LOW':
            return 45
        try:
            return float(conf)
        except:
            return 0
    
    if comp_wins:
        print(f"\n✅ WINNERS:")
        for w in sorted(comp_wins, key=get_score, reverse=True):
            horse = w.get('horse') or w.get('horse_name', 'Unknown')
            score = get_score(w)
            course = w.get('course') or w.get('course_name', '')
            trainer = w.get('trainer', '')
            profit = float(w.get('profit', 0))
            print(f"  {horse:25s} {score:3.0f}pts @ {course:15s} - {trainer[:25]:25s} Profit: £{profit:.2f}")
    
    print(f"{'='*100}\n")

# Elite trainers
elite_trainers = ['Mullins', 'Elliott', 'Henderson', 'Nicholls', 'de Bromhead', 'Skelton', 'Murphy']
elite_picks = [p for p in picks if any(elite in p.get('trainer', '') for elite in elite_trainers)]
elite_wins = [p for p in elite_picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON']]
if elite_picks:
    elite_sr = len(elite_wins)/len(elite_picks)*100
    print(f"⭐ ELITE CONNECTIONS: {elite_sr:.1f}% strike rate ({len(elite_wins)}/{len(elite_picks)})")

def get_score(pick):
    conf = pick.get('confidence', 0)
    if isinstance(conf, (int, float)):
        return float(conf)
    if str(conf).upper() == 'HIGH':
        return 75
    if str(conf).upper() == 'MEDIUM':
        return 60
    if str(conf).upper() == 'LOW':
        return 45
    try:
        return float(conf)
    except:
        return 0

high_conf = [p for p in picks if get_score(p) >= 75]
high_conf_wins = [p for p in high_conf if str(p.get('outcome', '')).upper() in ['WIN', 'WON']]
if high_conf:
    high_sr = len(high_conf_wins)/len(high_conf)*100
    print(f"🎯 HIGH CONFIDENCE (75+): {high_sr:.1f}% strike rate ({len(high_conf_wins)}/{len(high_conf)})")

print(f"\n{'='*100}\n")

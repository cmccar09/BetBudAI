"""
Today's Results Report - Live Updates
"""

from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

def get_score(pick):
    conf = pick.get('confidence', 0)
    if isinstance(conf, (int, float)):
        return float(conf)
    if isinstance(conf, Decimal):
        return float(conf)
    if str(conf).upper() == 'VERY_HIGH':
        return 90
    if str(conf).upper() == 'HIGH':
        return 80
    if str(conf).upper() == 'MEDIUM':
        return 65
    if str(conf).upper() == 'LOW':
        return 45
    try:
        return float(conf)
    except:
        return 0

def is_betting_pick(pick):
    # Check if it has a stake assigned (actual bet)
    if pick.get('stake') and float(pick.get('stake', 0)) > 0:
        return True
    # Or if it's comprehensive analysis with 60+ confidence
    if pick.get('analysis_method') in ['COMPREHENSIVE', 'COMPREHENSIVE_V2']:
        score = get_score(pick)
        return score >= 60
    return False

print(f"\n{'='*100}")
print(f"TODAY'S RESULTS - {today}")
print(f"BETTING PICKS ONLY (Learning picks excluded)")
print(f"{'='*100}\n")

response = table.query(KeyConditionExpression=Key('bet_date').eq(today))
all_picks = response['Items']

picks = [p for p in all_picks if is_betting_pick(p)]

wins = [p for p in picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON']]
losses = [p for p in picks if str(p.get('outcome', '')).upper() in ['LOSS', 'LOST']]
pending = [p for p in picks if str(p.get('outcome', '')).upper() in ['PENDING', '']]

learning_only = len(all_picks) - len(picks)
total_profit = sum(float(p.get('profit', 0)) for p in wins + losses)

print(f"OVERALL PERFORMANCE:")
print(f"{'='*100}")
print(f"Betting Picks: {len(picks)} (Learning-only: {learning_only})")
print(f"Results In: {len(wins) + len(losses)} | Pending: {len(pending)}")
print(f"Wins: {len(wins)} | Losses: {len(losses)}")
if len(wins) + len(losses) > 0:
    print(f"Strike Rate: {len(wins)/(len(wins)+len(losses))*100:.1f}%")
print(f"Total Profit/Loss: GBP {total_profit:.2f}")
print(f"{'='*100}\n")

if losses:
    print(f"LOSSES:")
    print(f"{'='*100}")
    for loss in sorted(losses, key=get_score, reverse=True):
        horse = loss.get('horse') or loss.get('horse_name', 'Unknown')
        score = get_score(loss)
        course = loss.get('course') or loss.get('course_name', '')
        time = loss.get('race_time', '')[:16]
        trainer = loss.get('trainer', '')
        position = loss.get('finishing_position', 'DNF')
        print(f"  {time} {course:15s} - {horse:25s} {score:3.0f}pts - {position:5s} - {trainer[:30]}")
    print(f"{'='*100}\n")

if wins:
    print(f"WINS:")
    print(f"{'='*100}")
    for win in sorted(wins, key=get_score, reverse=True):
        horse = win.get('horse') or win.get('horse_name', 'Unknown')
        score = get_score(win)
        course = win.get('course') or win.get('course_name', '')
        time = win.get('race_time', '')[:16]
        trainer = win.get('trainer', '')
        profit = float(win.get('profit', 0))
        print(f"  {time} {course:15s} - {horse:25s} {score:3.0f}pts - Profit: GBP {profit:.2f} - {trainer[:30]}")
    print(f"{'='*100}\n")

if pending:
    print(f"PENDING RACES ({len(pending)}):")
    print(f"{'='*100}")
    
    # Group by confidence level
    very_high = [p for p in pending if get_score(p) >= 90]
    high = [p for p in pending if 80 <= get_score(p) < 90]
    medium = [p for p in pending if 60 <= get_score(p) < 80]
    
    if very_high:
        print(f"\nVERY HIGH CONFIDENCE (90+):")
        for p in sorted(very_high, key=get_score, reverse=True):
            horse = p.get('horse') or p.get('horse_name', 'Unknown')
            score = get_score(p)
            course = p.get('course') or p.get('course_name', '')
            time = p.get('race_time', '')[:16]
            odds = p.get('odds', 0)
            print(f"  {time} {course:15s} - {horse:25s} {score:3.0f}pts @ {odds}")
    
    if high:
        print(f"\nHIGH CONFIDENCE (80-89):")
        for p in sorted(high, key=get_score, reverse=True):
            horse = p.get('horse') or p.get('horse_name', 'Unknown')
            score = get_score(p)
            course = p.get('course') or p.get('course_name', '')
            time = p.get('race_time', '')[:16]
            odds = p.get('odds', 0)
            print(f"  {time} {course:15s} - {horse:25s} {score:3.0f}pts @ {odds}")
    
    if medium:
        print(f"\nMEDIUM CONFIDENCE (60-79):")
        for p in sorted(medium, key=get_score, reverse=True):
            horse = p.get('horse') or p.get('horse_name', 'Unknown')
            score = get_score(p)
            course = p.get('course') or p.get('course_name', '')
            time = p.get('race_time', '')[:16]
            odds = p.get('odds', 0)
            print(f"  {time} {course:15s} - {horse:25s} {score:3.0f}pts @ {odds}")
    
    print(f"{'='*100}\n")

# Performance by confidence tier
high_conf = [p for p in picks if get_score(p) >= 75]
high_conf_wins = [p for p in high_conf if str(p.get('outcome', '')).upper() in ['WIN', 'WON']]
high_conf_results = [p for p in high_conf if str(p.get('outcome', '')).upper() in ['WIN', 'WON', 'LOSS', 'LOST']]

if high_conf_results:
    print(f"HIGH CONFIDENCE (75+): {len(high_conf_wins)}/{len(high_conf_results)} = {len(high_conf_wins)/len(high_conf_results)*100:.1f}%")

# Elite trainers
elite_trainers = ['Mullins', 'Elliott', 'Henderson', 'Nicholls', 'de Bromhead', 'Skelton', 'Murphy']
elite_picks = [p for p in picks if any(elite in str(p.get('trainer', '')) for elite in elite_trainers)]
elite_results = [p for p in elite_picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON', 'LOSS', 'LOST']]
elite_wins = [p for p in elite_picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON']]
if elite_results:
    print(f"ELITE CONNECTIONS: {len(elite_wins)}/{len(elite_results)} = {len(elite_wins)/len(elite_results)*100:.1f}%")

print(f"\n{'='*100}\n")

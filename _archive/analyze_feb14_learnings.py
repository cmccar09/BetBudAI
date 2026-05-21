"""
Analyze Feb 14, 2026 results to identify what worked and lock in successful patterns
"""
from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key
from collections import defaultdict
import statistics
from decimal import Decimal

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# Get yesterday's results
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
response = table.query(KeyConditionExpression=Key('bet_date').eq(yesterday))
picks = response['Items']

print(f"\n{'='*80}")
print(f"LEARNING ANALYSIS - {yesterday}")
print(f"{'='*80}\n")

# Categorize by outcome
wins = [p for p in picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON']]
losses = [p for p in picks if str(p.get('outcome', '')).upper() in ['LOSS', 'LOST']]

# Filter out entries without confidence scores - handle both Decimal and string types
def get_numeric_confidence(p):
    conf = p.get('confidence')
    if conf is None:
        return 0
    try:
        return float(conf)
    except (ValueError, TypeError):
        return 0

wins = [w for w in wins if get_numeric_confidence(w) > 0]
losses = [l for l in losses if get_numeric_confidence(l) > 0]

print(f"Analyzed: {len(wins)} wins, {len(losses)} losses")
print(f"Strike Rate: {len(wins)/(len(wins)+len(losses))*100:.1f}%\n")

# Score distribution analysis
win_scores = [float(w.get('confidence', 0)) for w in wins]
loss_scores = [float(l.get('confidence', 0)) for l in losses]

if win_scores:
    print("SCORE DISTRIBUTION:")
    print(f"  Winning picks - Avg: {statistics.mean(win_scores):.1f}, Range: {min(win_scores):.0f}-{max(win_scores):.0f}")
    print(f"  Losing picks  - Avg: {statistics.mean(loss_scores):.1f}, Range: {min(loss_scores):.0f}-{max(loss_scores):.0f}")
    print()

# Confidence tier performance
def get_confidence(score):
    if score >= 75: return "EXCELLENT"
    elif score >= 60: return "GOOD"
    elif score >= 45: return "FAIR"
    else: return "POOR"

confidence_performance = defaultdict(lambda: {'wins': 0, 'losses': 0})
for w in wins:
    conf = get_confidence(float(w.get('confidence', 0)))
    confidence_performance[conf]['wins'] += 1
for l in losses:
    conf = get_confidence(float(l.get('confidence', 0)))
    confidence_performance[conf]['losses'] += 1

print("CONFIDENCE TIER PERFORMANCE:")
for tier in ['EXCELLENT', 'GOOD', 'FAIR', 'POOR']:
    w = confidence_performance[tier]['wins']
    l = confidence_performance[tier]['losses']
    total = w + l
    if total > 0:
        sr = w/total*100
        print(f"  {tier:10s} ({w:2d}W/{l:2d}L): {sr:5.1f}% strike rate")
print()

# Odds range analysis
win_odds = [float(w.get('odds', 0)) for w in wins if w.get('odds', 0) > 0]
loss_odds = [float(l.get('odds', 0)) for l in losses if l.get('odds', 0) > 0]

if win_odds:
    print("ODDS ANALYSIS:")
    print(f"  Winning picks - Avg odds: {statistics.mean(win_odds):.2f}")
    print(f"  Losing picks  - Avg odds: {statistics.mean(loss_odds):.2f}")
    
    # Favorites vs longer odds
    fav_wins = len([o for o in win_odds if o <= 3.5])
    fav_losses = len([o for o in loss_odds if o <= 3.5])
    long_wins = len([o for o in win_odds if o > 3.5])
    long_losses = len([o for o in loss_odds if o > 3.5])
    
    print(f"\n  Favorites (<=3.5): {fav_wins}W/{fav_losses}L = {fav_wins/(fav_wins+fav_losses)*100:.1f}%")
    print(f"  Longer odds (>3.5): {long_wins}W/{long_losses}L = {long_wins/(long_wins+long_losses)*100:.1f}%")
print()

# Race type analysis
race_types = defaultdict(lambda: {'wins': 0, 'losses': 0})
for w in wins:
    rtype = w.get('race_type', 'Unknown')
    race_types[rtype]['wins'] += 1
for l in losses:
    rtype = l.get('race_type', 'Unknown')
    race_types[rtype]['losses'] += 1

print("RACE TYPE PERFORMANCE:")
for rtype, results in sorted(race_types.items(), key=lambda x: x[1]['wins'], reverse=True):
    w = results['wins']
    l = results['losses']
    total = w + l
    if total > 0:
        print(f"  {rtype:20s}: {w}W/{l}L ({w/total*100:.1f}%)")
print()

# Top performers - horses that won
print("TOP WINNING PICKS:")
top_wins = sorted(wins, key=lambda x: float(x.get('confidence', 0)), reverse=True)[:10]
for w in top_wins:
    score = w.get('confidence', 0)
    odds = w.get('odds', 0)
    profit = w.get('profit', 0)
    horse = w.get('horse_name') or w.get('horse', 'Unknown')
    course = w.get('course_name') or w.get('course', '')
    print(f"  {horse:25s} @ {course:12s} Score: {score:3.0f} Odds: {odds:.1f} Profit: £{profit:.2f}")
print()

# High scorers that lost (identify weaknesses)
print("HIGH-SCORING LOSSES (Score >= 75):")
high_losses = [l for l in losses if float(l.get('confidence', 0)) >= 75]
for l in sorted(high_losses, key=lambda x: float(x.get('confidence', 0)), reverse=True):
    score = l.get('confidence', 0)
    odds = l.get('odds', 0)
    notes = l.get('race_notes', '') or l.get('validation_notes', '')
    horse = l.get('horse_name') or l.get('horse', 'Unknown')
    course = l.get('course_name') or l.get('course', '')
    print(f"  {horse:25s} @ {course:12s} Score: {score:3.0f} Odds: {odds:.1f} {notes}")
print()

# KEY LEARNINGS
print("="*80)
print("KEY LEARNINGS TO LOCK IN:")
print("="*80)

# Calculate optimal score threshold
all_picks_sorted = sorted(wins + losses, key=lambda x: float(x.get('confidence', 0)), reverse=True)
best_threshold = 0
best_roi = 0
for threshold in range(50, 90, 5):
    filtered = [p for p in all_picks_sorted if float(p.get('confidence', 0)) >= threshold]
best_threshold = 0
best_roi = 0
for threshold in range(50, 90, 5):
    filtered = [p for p in all_picks_sorted if float(p.get('score', 0)) >= threshold]
    if len(filtered) > 5:
        filt_wins = [p for p in filtered if str(p.get('outcome', '')).upper() in ['WIN', 'WON']]
        filt_losses = [p for p in filtered if str(p.get('outcome', '')).upper() in ['LOSS', 'LOST']]
        profit = sum(float(p.get('profit', 0)) for p in filt_wins + filt_losses)
        stake = len(filtered) * 5
        roi = (profit / stake * 100) if stake > 0 else 0
        sr = len(filt_wins)/len(filtered)*100 if filtered else 0
        if roi > best_roi:
            best_roi = roi
            best_threshold = threshold
        print(f"{threshold}+ threshold: {len(filt_wins)}W/{len(filt_losses)}L ({sr:.1f}%) - ROI: {roi:.1f}%")

print(f"\n✓ OPTIMAL SCORE THRESHOLD: {best_threshold}+ (ROI: {best_roi:.1f}%)")

# Confidence tier recommendation
excellent_wins = confidence_performance['EXCELLENT']['wins']
excellent_losses = confidence_performance['EXCELLENT']['losses']
excellent_total = excellent_wins + excellent_losses
if excellent_total > 0:
    excellent_sr = excellent_wins/excellent_total*100
    print(f"✓ EXCELLENT tier (75+): {excellent_sr:.1f}% strike rate - STRONG PREDICTOR")

good_wins = confidence_performance['GOOD']['wins']
good_losses = confidence_performance['GOOD']['losses']
good_total = good_wins + good_losses
if good_total > 0:
    good_sr = good_wins/good_total*100
    print(f"✓ GOOD tier (60-74): {good_sr:.1f}% strike rate - RELIABLE")

# Favorite performance
if fav_wins + fav_losses > 0:
    fav_sr = fav_wins/(fav_wins+fav_losses)*100
    print(f"✓ Favorites (<=3.5 odds): {fav_sr:.1f}% strike rate - favorite_correction={12 if fav_sr < 50 else 15}")

print(f"\n✓ Average winning score: {statistics.mean(win_scores):.1f}")
print(f"✓ Average losing score: {statistics.mean(loss_scores):.1f}")
print(f"✓ Score differential: {statistics.mean(win_scores) - statistics.mean(loss_scores):.1f} points")
print(f"\n{'='*80}\n")

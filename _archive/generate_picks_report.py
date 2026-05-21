"""
Quick Performance Report for Today's Picks
Analyzes selections vs market outcomes
"""

import json
import csv
from datetime import datetime

# Read today's picks
picks = []
with open('today_picks.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        picks.append({
            'name': row['runner_name'],
            'selection_id': row['selection_id'],
            'market_id': row['market_id'],
            'venue': row['venue'],
            'start_time': row['start_time_dublin'],
            'p_win': float(row['p_win']),
            'p_place': float(row['p_place']),
            'tags': row['tags'],
            'why': row['why_now'][:100] + '...' if len(row['why_now']) > 100 else row['why_now']
        })

print("=" * 80)
print(f"TODAY'S BETTING PICKS PERFORMANCE REPORT")
print(f"Date: {datetime.now().strftime('%B %d, %Y')}")
print("=" * 80)

print(f"\nTOTAL PICKS: {len(picks)}")
print("\nPICKS BREAKDOWN:")
print("-" * 80)

# Group by venue
venues = {}
for pick in picks:
    venue = pick['venue']
    if venue not in venues:
        venues[venue] = []
    venues[venue].append(pick)

for venue, venue_picks in venues.items():
    print(f"\n📍 {venue.upper()} - {len(venue_picks)} selection(s)")
    
    for i, pick in enumerate(venue_picks, 1):
        race_time = datetime.fromisoformat(pick['start_time'].replace('Z', '+00:00'))
        time_str = race_time.strftime('%H:%M')
        
        print(f"\n  {i}. {pick['name']} @ {time_str}")
        print(f"     Win Prob: {pick['p_win']:.1%} | Place Prob: {pick['p_place']:.1%}")
        print(f"     Tags: {pick['tags'][:60]}")
        print(f"     Reasoning: {pick['why']}")

# Summary Statistics
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

avg_win_prob = sum(p['p_win'] for p in picks) / len(picks) if picks else 0
avg_place_prob = sum(p['p_place'] for p in picks) / len(picks) if picks else 0

print(f"\nAverage Win Probability:   {avg_win_prob:.1%}")
print(f"Average Place Probability: {avg_place_prob:.1%}")

# Count by confidence level
high_confidence = [p for p in picks if p['p_win'] >= 0.40]
medium_confidence = [p for p in picks if 0.25 <= p['p_win'] < 0.40]
low_confidence = [p for p in picks if p['p_win'] < 0.25]

print(f"\nConfidence Distribution:")
print(f"  High (≥40% win):     {len(high_confidence)} picks")
print(f"  Medium (25-39%):     {len(medium_confidence)} picks")
print(f"  Low (<25%):          {len(low_confidence)} picks")

# Most common tags
all_tags = []
for pick in picks:
    all_tags.extend(pick['tags'].split(','))

tag_counts = {}
for tag in all_tags:
    tag = tag.strip()
    tag_counts[tag] = tag_counts.get(tag, 0) + 1

print(f"\nMost Common Selection Factors:")
sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
for tag, count in sorted_tags:
    print(f"  • {tag}: {count} selections")

print("\n" + "=" * 80)
print("RESULTS STATUS")
print("=" * 80)

# Check race times
now = datetime.now()
completed_races = []
upcoming_races = []

for pick in picks:
    race_time = datetime.fromisoformat(pick['start_time'].replace('Z', '+00:00'))
    # Add 20 minutes for race duration
    end_time = race_time.replace(tzinfo=None) + __import__('datetime').timedelta(minutes=20)
    
    if end_time < now:
        completed_races.append(pick)
    else:
        upcoming_races.append(pick)

print(f"\n✅ Completed: {len(completed_races)} races")
print(f"⏳ Upcoming:  {len(upcoming_races)} races")

if upcoming_races:
    print(f"\nNext race: {upcoming_races[0]['name']} at {upcoming_races[0]['venue']}")
    next_time = datetime.fromisoformat(upcoming_races[0]['start_time'].replace('Z', '+00:00'))
    print(f"Start time: {next_time.strftime('%H:%M')}")

print("\n" + "=" * 80)
print("NOTE: Actual results need to be fetched from Betfair API")
print("Run: python update_results_from_betfair.py (if available)")
print("Or check manually at: https://www.betfair.com/exchange/")
print("=" * 80)

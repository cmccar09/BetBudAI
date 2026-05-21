"""
INTRADAY LEARNING SYSTEM
Monitor earlier races today and apply learnings to upcoming picks

This script:
1. Fetches results from races that have finished today
2. Identifies patterns (trainer/going/odds performance)
3. Updates pick confidence for remaining races
4. Saves insights for real-time adjustment

Run this BEFORE making final picks for late races
"""

import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

def get_todays_results():
    """Get results from races that finished earlier today"""
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
    )
    
    items = resp.get('Items', [])
    
    # Filter to only races that have results
    finished_races = [i for i in items if i.get('outcome') in ['WON', 'LOST', 'PLACED']]
    
    return finished_races

def analyze_trainer_performance_today(results):
    """See which trainers are winning/losing today"""
    trainer_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
    
    for result in results:
        trainer = result.get('trainer', 'Unknown')
        outcome = result.get('outcome')
        
        trainer_stats[trainer]['total'] += 1
        if outcome == 'WON':
            trainer_stats[trainer]['wins'] += 1
        elif outcome == 'LOST':
            trainer_stats[trainer]['losses'] += 1
    
    # Calculate win rates
    hot_trainers = []
    cold_trainers = []
    
    for trainer, stats in trainer_stats.items():
        if stats['total'] >= 2:  # At least 2 races
            win_rate = stats['wins'] / stats['total']
            stats['win_rate'] = win_rate
            
            if win_rate >= 0.5:
                hot_trainers.append((trainer, stats))
            elif win_rate == 0:
                cold_trainers.append((trainer, stats))
    
    return hot_trainers, cold_trainers, trainer_stats

def analyze_going_performance_today(results):
    """See if certain going conditions favor different odds ranges"""
    going_stats = defaultdict(lambda: {'heavy': [], 'soft': [], 'good': [], 'firm': []})
    
    for result in results:
        course = result.get('course', '')
        outcome = result.get('outcome')
        odds = float(result.get('odds', 0))
        
        # Infer going from our weather system
        # For now, track by outcome and odds
        if outcome == 'WON':
            going_stats[course]['wins'].append(odds)
    
    return going_stats

def analyze_odds_range_performance(results):
    """See which odds ranges are hitting today"""
    odds_performance = {
        'favorites_2-3': {'wins': 0, 'total': 0},
        'sweet_spot_3-9': {'wins': 0, 'total': 0},
        'outsiders_9-15': {'wins': 0, 'total': 0},
        'longshots_15+': {'wins': 0, 'total': 0}
    }
    
    for result in results:
        outcome = result.get('outcome')
        odds = float(result.get('odds', 0))
        
        if 2 <= odds < 3:
            category = 'favorites_2-3'
        elif 3 <= odds < 9:
            category = 'sweet_spot_3-9'
        elif 9 <= odds < 15:
            category = 'outsiders_9-15'
        else:
            category = 'longshots_15+'
        
        odds_performance[category]['total'] += 1
        if outcome == 'WON':
            odds_performance[category]['wins'] += 1
    
    # Calculate win rates
    for category, stats in odds_performance.items():
        if stats['total'] > 0:
            stats['win_rate'] = stats['wins'] / stats['total']
        else:
            stats['win_rate'] = 0
    
    return odds_performance

def get_track_patterns_today(results):
    """Identify which tracks have specific patterns emerging"""
    track_winners = defaultdict(list)
    
    for result in results:
        if result.get('outcome') == 'WON':
            course = result.get('course', '')
            horse = result.get('horse', '')
            odds = float(result.get('odds', 0))
            trainer = result.get('trainer', '')
            score = float(result.get('comprehensive_score', 0))
            
            track_winners[course].append({
                'horse': horse,
                'odds': odds,
                'trainer': trainer,
                'score': score
            })
    
    return track_winners

def generate_insights(results):
    """Generate actionable insights from today's results"""
    insights = {
        'timestamp': datetime.now().isoformat(),
        'races_analyzed': len(results),
        'learnings': []
    }
    
    # Trainer performance
    hot_trainers, cold_trainers, trainer_stats = analyze_trainer_performance_today(results)
    
    if hot_trainers:
        insights['learnings'].append({
            'type': 'HOT_TRAINERS',
            'data': hot_trainers,
            'action': 'BOOST picks from these trainers in remaining races'
        })
    
    if cold_trainers:
        insights['learnings'].append({
            'type': 'COLD_TRAINERS',
            'data': cold_trainers,
            'action': 'REDUCE confidence in picks from these trainers'
        })
    
    # Odds range performance
    odds_perf = analyze_odds_range_performance(results)
    
    best_odds_range = max(odds_perf.items(), key=lambda x: x[1]['win_rate'])
    if best_odds_range[1]['total'] >= 3:  # At least 3 races
        insights['learnings'].append({
            'type': 'WINNING_ODDS_RANGE',
            'data': best_odds_range,
            'action': f"Focus on {best_odds_range[0]} - {best_odds_range[1]['win_rate']*100:.0f}% win rate today"
        })
    
    # Track patterns
    track_winners = get_track_patterns_today(results)
    
    for track, winners in track_winners.items():
        if len(winners) >= 2:
            avg_odds = sum(w['odds'] for w in winners) / len(winners)
            insights['learnings'].append({
                'type': 'TRACK_PATTERN',
                'track': track,
                'winners': len(winners),
                'avg_odds': round(avg_odds, 1),
                'action': f"{track}: Average winner odds {avg_odds:.1f}"
            })
    
    return insights

def save_insights(insights):
    """Save insights to file for use by workflow"""
    with open('intraday_learnings.json', 'w') as f:
        json.dump(insights, f, indent=2, default=str)
    
    print(f"✓ Saved insights to intraday_learnings.json")

def display_insights(insights):
    """Display insights in readable format"""
    print("\n" + "="*80)
    print("INTRADAY LEARNING SYSTEM - Today's Race Analysis")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Races analyzed: {insights['races_analyzed']}")
    print()
    
    if not insights['learnings']:
        print("⚠️  Not enough race results yet to generate insights")
        print("   Check back after more races have finished")
        return
    
    for learning in insights['learnings']:
        learning_type = learning['type']
        
        if learning_type == 'HOT_TRAINERS':
            print("🔥 HOT TRAINERS TODAY:")
            for trainer, stats in learning['data']:
                win_rate = stats['win_rate'] * 100
                print(f"   ✓ {trainer}: {stats['wins']}/{stats['total']} wins ({win_rate:.0f}%)")
            print(f"   → {learning['action']}\n")
        
        elif learning_type == 'COLD_TRAINERS':
            print("❄️  COLD TRAINERS TODAY:")
            for trainer, stats in learning['data']:
                print(f"   ✗ {trainer}: {stats['losses']}/{stats['total']} losses")
            print(f"   → {learning['action']}\n")
        
        elif learning_type == 'WINNING_ODDS_RANGE':
            category, stats = learning['data']
            win_rate = stats['win_rate'] * 100
            print(f"💰 WINNING ODDS RANGE:")
            print(f"   {category}: {stats['wins']}/{stats['total']} wins ({win_rate:.0f}%)")
            print(f"   → {learning['action']}\n")
        
        elif learning_type == 'TRACK_PATTERN':
            track = learning['track']
            winners = learning['winners']
            avg_odds = learning['avg_odds']
            print(f"📍 {track} PATTERN:")
            print(f"   {winners} winners today, average odds: {avg_odds}")
            print(f"   → {learning['action']}\n")
    
    print("="*80)
    print("Use these insights to adjust confidence in remaining picks")
    print("="*80 + "\n")

def main():
    """Run intraday learning analysis"""
    print("Fetching today's race results...")
    results = get_todays_results()
    
    if not results:
        print("No race results available yet today")
        return
    
    print(f"Found {len(results)} finished races\n")
    
    # Generate insights
    insights = generate_insights(results)
    
    # Display
    display_insights(insights)
    
    # Save for workflow
    save_insights(insights)
    
    return insights

if __name__ == "__main__":
    main()

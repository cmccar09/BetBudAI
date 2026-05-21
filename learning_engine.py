#!/usr/bin/env python3
"""
Learning Engine - Analyzes past performance and continuously improves betting strategy
Feeds insights back into prompt.txt to improve future selections
"""

import os
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import boto3
from decimal import Decimal

def load_historical_results(days_back=7):
    """Load all results from last N days (default: 7 for weekly analysis)"""
    history_dir = Path("./history")
    results = []
    
    for i in range(days_back):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        results_file = history_dir / f"results_{date}.json"
        selections_file = list(history_dir.glob(f"selections_{date}*.csv"))
        
        if results_file.exists() and selections_file:
            with open(results_file, 'r') as f:
                race_results = json.load(f)
            
            # Load selections
            with open(selections_file[0], 'r') as f:
                reader = csv.DictReader(f)
                selections = list(reader)
            
            # Match selections with results
            for selection in selections:
                selection_id = selection.get('selection_id', '')
                
                # Find matching result
                for result in race_results:
                    if str(result.get('selection_id', '')) == str(selection_id):
                        results.append({
                            'date': date,
                            'selection': selection,
                            'result': result
                        })
                        break
    
    return results

def analyze_performance_patterns(results):
    """Analyze what works and what doesn't"""
    
    analysis = {
        'by_ground': defaultdict(lambda: {'wins': 0, 'total': 0, 'roi': 0}),
        'by_odds_range': defaultdict(lambda: {'wins': 0, 'total': 0, 'roi': 0}),
        'by_course': defaultdict(lambda: {'wins': 0, 'total': 0, 'roi': 0}),
        'by_bet_type': defaultdict(lambda: {'wins': 0, 'total': 0, 'places': 0, 'roi': 0}),
        'by_trainer_jockey': defaultdict(lambda: {'wins': 0, 'total': 0}),
        'mistakes': [],
        'successes': []
    }
    
    for record in results:
        selection = record['selection']
        result = record['result']
        
        horse = selection.get('runner_name', '')
        venue = selection.get('venue', '')
        odds = float(selection.get('odds', 0))
        bet_type = selection.get('bet_type', 'WIN')
        tags = selection.get('tags', '')
        why_now = selection.get('why_now', '')
        
        is_winner = result.get('is_winner', False)
        is_placed = result.get('is_placed', False)
        
        # Categorize odds
        if odds <= 3.0:
            odds_range = 'favorite'
        elif odds <= 6.0:
            odds_range = 'mid_price'
        elif odds <= 12.0:
            odds_range = 'outsider'
        else:
            odds_range = 'longshot'
        
        # Track by odds range
        analysis['by_odds_range'][odds_range]['total'] += 1
        if is_winner:
            analysis['by_odds_range'][odds_range]['wins'] += 1
            analysis['by_odds_range'][odds_range]['roi'] += (odds - 1)
        else:
            analysis['by_odds_range'][odds_range]['roi'] -= 1
        
        # Track by bet type
        analysis['by_bet_type'][bet_type]['total'] += 1
        if is_winner:
            analysis['by_bet_type'][bet_type]['wins'] += 1
        if is_placed:
            analysis['by_bet_type'][bet_type]['places'] += 1
        
        # Track by venue
        analysis['by_course'][venue]['total'] += 1
        if is_winner:
            analysis['by_course'][venue]['wins'] += 1
        
        # Identify mistakes (high confidence losers)
        confidence = float(selection.get('confidence', 0))
        if confidence > 70 and not is_winner:
            analysis['mistakes'].append({
                'horse': horse,
                'venue': venue,
                'confidence': confidence,
                'odds': odds,
                'why_failed': why_now,
                'tags': tags,
                'date': record['date']
            })
        
        # Identify successes (winners at good prices)
        if is_winner and odds >= 3.0:
            analysis['successes'].append({
                'horse': horse,
                'venue': venue,
                'odds': odds,
                'why_won': why_now,
                'tags': tags,
                'date': record['date']
            })
    
    return analysis

def generate_learning_insights(analysis, min_sample_size=20):
    """Generate actionable insights from performance analysis
    
    Args:
        analysis: Performance data from analyze_performance_patterns
        min_sample_size: Minimum number of bets required before making recommendations (default: 20)
    """
    
    insights = []
    
    # Odds range performance (only if sufficient sample size)
    print("\n=== ODDS RANGE ANALYSIS ===")
    for odds_range, stats in sorted(analysis['by_odds_range'].items()):
        if stats['total'] > 0:
            win_rate = (stats['wins'] / stats['total']) * 100
            roi = (stats['roi'] / stats['total']) * 100
            print(f"{odds_range}: {stats['wins']}/{stats['total']} wins ({win_rate:.1f}%) ROI: {roi:+.1f}%")
            
            # Only generate insights if we have enough data (min 20 bets)
            if stats['total'] >= min_sample_size:
                if roi < -50:
                    insights.append(f"AVOID {odds_range} selections - losing {-roi:.0f}% ROI (n={stats['total']})")
                elif roi > 20:
                    insights.append(f"FOCUS on {odds_range} selections - strong {roi:.0f}% ROI (n={stats['total']})")
    
    # Bet type performance (only with sufficient sample)
    print("\n=== BET TYPE ANALYSIS ===")
    for bet_type, stats in analysis['by_bet_type'].items():
        if stats['total'] > 0:
            win_rate = (stats['wins'] / stats['total']) * 100
            place_rate = (stats['places'] / stats['total']) * 100
            print(f"{bet_type}: {stats['wins']} wins, {stats['places']} places from {stats['total']} bets")
            print(f"  Win rate: {win_rate:.1f}%, Place rate: {place_rate:.1f}%")
            
            # Only flag issues if we have minimum 15 bets of this type
            if stats['total'] >= 15:
                if bet_type == 'EW' and place_rate < 40:
                    insights.append(f"Each-way place rate too low ({place_rate:.0f}%) - tighten EW criteria (n={stats['total']})")
                elif bet_type == 'WIN' and win_rate < 20:
                    insights.append(f"WIN bet strike rate too low ({win_rate:.0f}%) - need stronger fancies (n={stats['total']})")
    
    # Course performance (need at least 5 bets at a venue)
    print("\n=== COURSE PERFORMANCE ===")
    best_courses = []
    worst_courses = []
    for course, stats in sorted(analysis['by_course'].items(), key=lambda x: x[1]['wins'], reverse=True):
        if stats['total'] >= 5:  # Require minimum 5 bets at venue before judging
            win_rate = (stats['wins'] / stats['total']) * 100
            if win_rate >= 40:
                best_courses.append(f"{course} ({stats['total']} bets)")
            elif win_rate < 15 and stats['total'] >= 8:  # Need 8+ bets to declare venue "bad"
                worst_courses.append(f"{course} ({stats['total']} bets)")
    
    if best_courses:
        print(f"Best courses: {', '.join(best_courses[:5])}")
        insights.append(f"Prioritize selections at: {', '.join([c.split(' ')[0] for c in best_courses[:3]])}")
    
    if worst_courses:
        print(f"Worst courses: {', '.join(worst_courses[:5])}")
        insights.append(f"Be cautious at: {', '.join([c.split(' ')[0] for c in worst_courses[:3]])}")
    
    # Common mistakes
    print("\n=== TOP MISTAKES (High confidence losers) ===")
    for i, mistake in enumerate(analysis['mistakes'][:5], 1):
        print(f"{i}. {mistake['horse']} at {mistake['venue']} ({mistake['confidence']}% conf, {mistake['odds']} odds)")
        print(f"   Tags: {mistake['tags']}")
        
        # Identify common patterns in mistakes
        tags_list = mistake['tags'] if isinstance(mistake['tags'], list) else [mistake['tags']]
        if 'BELOW_THRESHOLD' in tags_list or 'BELOW_THRESHOLD' in str(mistake['tags']):
            insights.append("Too many BELOW_THRESHOLD selections failing - raise minimum ROI requirement")
        if 'MULTI_RUNNER_STABLE' in tags_list or 'MULTI_RUNNER_STABLE' in str(mistake['tags']):
            insights.append("Multi-runner stable picks underperforming - avoid unless clear signals")
    
    # Success patterns
    print("\n=== TOP SUCCESSES (Winners at good prices) ===")
    success_tags = defaultdict(int)
    for i, success in enumerate(analysis['successes'][:5], 1):
        print(f"{i}. {success['horse']} at {success['venue']} ({success['odds']} odds)")
        print(f"   Tags: {success['tags']}")
        
        # Count successful tag combinations
        tags_list = success['tags'] if isinstance(success['tags'], list) else success['tags'].split(',')
        for tag in tags_list:
            tag = tag.strip()
            if tag:
                success_tags[tag] += 1
    
    # Identify winning patterns
    if success_tags:
        top_tags = sorted(success_tags.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"\nMost successful tags: {', '.join([t[0] for t in top_tags])}")
        insights.append(f"Winning pattern: prioritize {top_tags[0][0]} selections")
    
    return insights

def update_prompt_with_learnings(insights):
    """Update prompt.txt with learned insights"""
    
    prompt_file = Path("./prompt.txt")
    
    # Read current prompt
    with open(prompt_file, 'r', encoding='utf-8', errors='ignore') as f:
        prompt = f.read()
    
    # Create learning section
    learning_section = f"""

=== LEARNED INSIGHTS (Updated {datetime.now().strftime('%Y-%m-%d')}) ===

Based on analysis of last 7 days performance (weekly learning cycle):

"""
    
    for insight in insights:
        learning_section += f"• {insight}\n"
    
    learning_section += """
Apply these learnings when making selections. Continuously adapt strategy based on what works.

"""
    
    # Remove old learning section if exists
    if "=== LEARNED INSIGHTS" in prompt:
        start = prompt.find("=== LEARNED INSIGHTS")
        end = prompt.find("=== ", start + 20)
        if end > start:
            prompt = prompt[:start] + prompt[end:]
    
    # Add new learning section before final output format
    if "=== CSV OUTPUT FORMAT ===" in prompt:
        insert_point = prompt.find("=== CSV OUTPUT FORMAT ===")
        prompt = prompt[:insert_point] + learning_section + prompt[insert_point:]
    else:
        # Append to end
        prompt += learning_section
    
    # Write updated prompt
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    print(f"\n✓ Updated prompt.txt with {len(insights)} new insights")

def calculate_optimal_stakes(bankroll=1000.0, target_weekly_return=0.50):
    """Calculate stake recommendations using Kelly Criterion (fractional)"""
    
    # Kelly fraction (0.25 = quarter Kelly for safety)
    kelly_fraction = 0.25
    
    # Weekly target means we need cumulative growth
    # 50% per week is extremely aggressive but we'll optimize for it
    
    stakes = {
        'bankroll': bankroll,
        'target_weekly': target_weekly_return,
        'max_single_bet': bankroll * 0.05,  # Never risk more than 5% on one bet
        'recommendations': {}
    }
    
    return stakes

def calculate_bet_stake(odds, p_win, bankroll=1000.0, bet_type='WIN', p_place=None, ew_fraction=0.2):
    """Calculate optimal stake for a bet using fractional Kelly"""
    
    # Kelly Criterion: f = (bp - q) / b
    # f = fraction of bankroll to bet
    # b = odds - 1 (decimal odds minus stake)
    # p = probability of winning
    # q = probability of losing (1 - p)
    
    kelly_fraction = 0.25  # Use quarter Kelly for safety
    max_stake_pct = 0.05  # Never more than 5% of bankroll
    
    if bet_type == 'WIN':
        b = odds - 1
        q = 1 - p_win
        
        # Kelly formula
        kelly_full = (b * p_win - q) / b
        
        if kelly_full <= 0:
            return 0  # No positive edge, don't bet
        
        # Apply fractional Kelly
        kelly = kelly_full * kelly_fraction
        
        # Convert to stake
        stake = min(kelly * bankroll, max_stake_pct * bankroll)
        
    elif bet_type == 'EW':
        # Each-way is more complex - split into win and place components
        if not p_place:
            p_place = p_win * 2.5  # Rough estimate if not provided
        
        # Win component
        b_win = odds - 1
        kelly_win = ((b_win * p_win - (1 - p_win)) / b_win) if b_win > 0 else 0
        
        # Place component (at fractional odds)
        place_odds = 1 + (odds - 1) * ew_fraction
        b_place = place_odds - 1
        kelly_place = ((b_place * p_place - (1 - p_place)) / b_place) if b_place > 0 else 0
        
        # Combined Kelly (average of both components)
        kelly_combined = (kelly_win + kelly_place) / 2
        
        if kelly_combined <= 0:
            return 0
        
        # Apply fractional Kelly
        kelly = kelly_combined * kelly_fraction
        stake = min(kelly * bankroll, max_stake_pct * bankroll)
    
    else:
        stake = 0
    
    # Minimum stake of €2, round to nearest €0.50
    if stake < 2:
        stake = 2
    else:
        stake = round(stake * 2) / 2  # Round to nearest 0.50
    
    return round(stake, 2)

def main():
    """Run daily learning cycle"""
    
    print("="*60)
    print("LEARNING ENGINE - Analyzing Past Performance")
    print("="*60)
    
    # Load historical results
    print("\nLoading results from last 30 days...")
    results = load_historical_results(days_back=30)
    print(f"Found {len(results)} bet outcomes")
    
    if len(results) < 5:
        print("Not enough data yet for meaningful analysis")
        return
    
    # Analyze performance
    print("\nAnalyzing performance patterns...")
    analysis = analyze_performance_patterns(results)
    
    # Generate insights
    print("\nGenerating insights...")
    insights = generate_learning_insights(analysis)
    
    # Update prompt with learnings
    if insights:
        print("\nUpdating strategy with learnings...")
        update_prompt_with_learnings(insights)
        print("\n✓ Learning cycle complete!")
    else:
        print("\nNo significant insights yet - need more data")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

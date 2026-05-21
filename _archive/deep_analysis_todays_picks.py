#!/usr/bin/env python3
"""
Deep analysis of today's betting picks - verify quality and get next best horses
"""

import boto3
from decimal import Decimal
from datetime import datetime
import json

def get_todays_picks():
    """Get all picks for today"""
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    today = '2026-02-07'
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
    )
    
    return response.get('Items', [])

def analyze_pick(pick):
    """Detailed analysis of a single pick"""
    horse = pick.get('horse', 'Unknown')
    course = pick.get('course', 'Unknown')
    race_time = pick.get('race_time', '')
    score = float(pick.get('comprehensive_score', 0))
    
    print(f"\n{'='*80}")
    print(f"🐴 {horse} @ {course}")
    print(f"   Race Time: {race_time}")
    print(f"   Comprehensive Score: {score:.0f}/100")
    print(f"   Recommended: {pick.get('recommended_bet', False)}")
    print(f"   Confidence Tier: {pick.get('confidence_tier', 'N/A')}")
    print(f"\n   Score Breakdown:")
    
    # Component scores
    components = [
        ('Form', 'form_score', 25),
        ('Class', 'class_score', 15),
        ('Weight', 'weight_score', 10),
        ('Jockey', 'jockey_score', 10),
        ('Trainer', 'trainer_score', 10),
        ('Distance', 'distance_score', 10),
        ('Track', 'track_score', 10),
        ('Pace', 'pace_score', 5),
        ('Value', 'value_score', 5),
        ('Recent Perf', 'recent_performance_score', 10),
    ]
    
    total_possible = sum(c[2] for c in components)
    total_actual = 0
    
    for name, key, max_val in components:
        val = float(pick.get(key, 0))
        total_actual += val
        pct = (val/max_val*100) if max_val > 0 else 0
        bar = '█' * int(pct/10) + '░' * (10 - int(pct/10))
        print(f"   {name:15} {val:5.1f}/{max_val:2} {bar} {pct:5.1f}%")
    
    print(f"\n   Total Component Score: {total_actual:.1f}/{total_possible}")
    
    # Additional factors
    print(f"\n   Additional Factors:")
    print(f"   Odds: {pick.get('odds', 'N/A')}")
    print(f"   Distance: {pick.get('distance', 'N/A')}")
    print(f"   Going: {pick.get('going', 'N/A')}")
    print(f"   Race Type: {pick.get('race_type', 'N/A')}")
    print(f"   Jockey: {pick.get('jockey', 'N/A')}")
    print(f"   Trainer: {pick.get('trainer', 'N/A')}")
    
    # Quality assessment
    print(f"\n   Quality Assessment:")
    if score >= 110:
        print(f"   ⭐⭐⭐ EXCEPTIONAL - Very strong pick")
    elif score >= 95:
        print(f"   ⭐⭐ STRONG - Good betting opportunity")
    elif score >= 85:
        print(f"   ⭐ SOLID - Worth considering")
    elif score >= 75:
        print(f"   ⚠️  MODERATE - Marginal pick")
    else:
        print(f"   ❌ WEAK - Questionable selection")
    
    return score

def get_next_best_in_race(all_items, race_course, race_time, exclude_horse):
    """Find the next best horse in the same race"""
    same_race = [
        item for item in all_items
        if item.get('course') == race_course 
        and item.get('race_time') == race_time
        and item.get('horse') != exclude_horse
    ]
    
    if not same_race:
        return None
    
    # Sort by score
    same_race.sort(key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)
    
    return same_race[0] if same_race else None

def main():
    print("="*80)
    print("DEEP ANALYSIS OF TODAY'S BETTING PICKS")
    print("Date: 2026-02-07")
    print("="*80)
    
    # Get all items
    all_items = get_todays_picks()
    
    # Get recommended picks
    recommended = [item for item in all_items if item.get('recommended_bet')]
    ui_picks = [item for item in all_items if item.get('show_in_ui')]
    
    print(f"\n📊 OVERVIEW:")
    print(f"   Total horses analyzed: {len(all_items)}")
    print(f"   Recommended bets: {len(recommended)}")
    print(f"   UI picks shown: {len(ui_picks)}")
    
    # Sort recommended by score
    recommended.sort(key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)
    
    print(f"\n\n{'='*80}")
    print(f"DETAILED ANALYSIS OF TOP RECOMMENDED BETS")
    print(f"{'='*80}")
    
    # Analyze each recommended bet
    for i, pick in enumerate(recommended[:10], 1):
        print(f"\n\n{'#'*80}")
        print(f"PICK #{i}")
        score = analyze_pick(pick)
        
        # Find next best in same race
        next_best = get_next_best_in_race(
            all_items,
            pick.get('course'),
            pick.get('race_time'),
            pick.get('horse')
        )
        
        if next_best:
            next_score = float(next_best.get('comprehensive_score', 0))
            print(f"\n   🔍 NEXT BEST IN RACE:")
            print(f"      Horse: {next_best.get('horse')}")
            print(f"      Score: {next_score:.0f}/100")
            print(f"      Gap: {score - next_score:.0f} points ({((score-next_score)/score*100):.1f}% advantage)")
            print(f"      Odds: {next_best.get('odds', 'N/A')}")
            
            # Comparison analysis
            if score - next_score > 20:
                print(f"      ✅ DOMINANT - Clear favorite in the race")
            elif score - next_score > 10:
                print(f"      ⚡ STRONG EDGE - Good advantage over field")
            elif score - next_score > 5:
                print(f"      ⚠️  MARGINAL - Close competition")
            else:
                print(f"      🚨 VERY CLOSE - Minimal edge, risky bet")
        else:
            print(f"\n   ℹ️  No other horses found in this race")
    
    print(f"\n\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    
    # Summary statistics
    scores = [float(p.get('comprehensive_score', 0)) for p in recommended]
    if scores:
        print(f"\nRecommended Bet Scores:")
        print(f"   Highest: {max(scores):.0f}")
        print(f"   Average: {sum(scores)/len(scores):.0f}")
        print(f"   Lowest: {min(scores):.0f}")
        
        # Tier breakdown
        exceptional = len([s for s in scores if s >= 110])
        strong = len([s for s in scores if 95 <= s < 110])
        solid = len([s for s in scores if 85 <= s < 95])
        moderate = len([s for s in scores if 75 <= s < 85])
        weak = len([s for s in scores if s < 75])
        
        print(f"\nQuality Tiers:")
        print(f"   ⭐⭐⭐ Exceptional (110+): {exceptional}")
        print(f"   ⭐⭐ Strong (95-109): {strong}")
        print(f"   ⭐ Solid (85-94): {solid}")
        print(f"   ⚠️  Moderate (75-84): {moderate}")
        print(f"   ❌ Weak (<75): {weak}")
        
        print(f"\n💡 RECOMMENDATION:")
        if exceptional >= 2:
            print(f"   Focus on the {exceptional} exceptional picks - these have the best chance")
        elif strong >= 3:
            print(f"   Good selection of strong picks - spread bets across top performers")
        else:
            print(f"   Limited high-confidence picks today - be selective and cautious")

if __name__ == '__main__':
    main()

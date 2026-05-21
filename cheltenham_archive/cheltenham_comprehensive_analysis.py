"""
Cheltenham Festival Comprehensive Analysis
Analyzes ALL races but recommends ONLY high-confidence picks (75+)

Usage:
    python cheltenham_comprehensive_analysis.py --day 1
    python cheltenham_comprehensive_analysis.py --all
"""

import sys
import argparse
from datetime import datetime
from comprehensive_pick_logic import (
    analyze_horse_comprehensive,
    DEFAULT_WEIGHTS,
    get_confidence_tier
)

# Cheltenham-specific bonuses (added to validated weights)
CHELTENHAM_BONUSES = {
    'festival_winner_history': 15,      # Previous Cheltenham winner
    'festival_placed_history': 8,       # Previous Cheltenham 2nd/3rd
    'course_winner': 10,                # Won at Cheltenham before
    'graded_winner_this_season': 12,   # Grade 1/2 win this season
    'irish_raider_elite': 8,            # Mullins/Elliott at Festival
    'champion_jockey': 5,               # Walsh/Townend/Blackmore
    'grade1_championship': 10,          # Supreme, Champion, Gold Cup, etc.
    'grade1_novice': 5,                 # Novice Grade 1s
    'handicap_penalty': -5,             # Handicaps less predictable
}

# Elite Festival trainers (proven Festival winners)
FESTIVAL_ELITE_TRAINERS = [
    'W. P. Mullins', 'Willie Mullins',
    'Gordon Elliott', 'G. Elliott',
    'Nicky Henderson', 'N. Henderson',
    'Paul Nicholls', 'P. Nicholls',
    'Henry de Bromhead', 'H. de Bromhead',
    'Dan Skelton', 'D. Skelton'
]

# Champion jockeys
CHAMPION_JOCKEYS = [
    'P. Townend', 'Paul Townend',
    'R. Walsh', 'Ruby Walsh',
    'R. Blackmore', 'Rachael Blackmore',
    'J. W. Kennedy', 'Jack Kennedy',
    'D. Russell', 'Davy Russell',
    'N. de Boinville', 'Nico de Boinville',
    'H. Cobden', 'Harry Cobden'
]

def apply_cheltenham_bonuses(horse_data, race_data, base_score):
    """
    Apply Cheltenham-specific bonuses to base comprehensive score
    
    Args:
        horse_data: Dictionary with horse information
        race_data: Dictionary with race information
        base_score: Score from comprehensive_pick_logic
        
    Returns:
        Enhanced score with Cheltenham bonuses
    """
    bonus_breakdown = {}
    total_bonus = 0
    
    # Festival winner history
    if horse_data.get('cheltenham_wins', 0) > 0:
        bonus = CHELTENHAM_BONUSES['festival_winner_history']
        bonus_breakdown['Previous Festival Winner'] = bonus
        total_bonus += bonus
    
    # Festival placed history
    elif horse_data.get('cheltenham_places', 0) > 0:
        bonus = CHELTENHAM_BONUSES['festival_placed_history']
        bonus_breakdown['Previous Festival Place'] = bonus
        total_bonus += bonus
    
    # Course winner (any Cheltenham win, not just Festival)
    if horse_data.get('cheltenham_course_wins', 0) > 0:
        bonus = CHELTENHAM_BONUSES['course_winner']
        bonus_breakdown['Cheltenham Course Winner'] = bonus
        total_bonus += bonus
    
    # Graded winner this season
    if horse_data.get('grade1_wins_this_season', 0) > 0 or horse_data.get('grade2_wins_this_season', 0) > 0:
        bonus = CHELTENHAM_BONUSES['graded_winner_this_season']
        bonus_breakdown['Graded Winner This Season'] = bonus
        total_bonus += bonus
    
    # Elite Irish raider bonus
    trainer = horse_data.get('trainer', '')
    if trainer in FESTIVAL_ELITE_TRAINERS and ('Mullins' in trainer or 'Elliott' in trainer):
        bonus = CHELTENHAM_BONUSES['irish_raider_elite']
        bonus_breakdown['Elite Irish Raider'] = bonus
        total_bonus += bonus
    
    # Champion jockey
    jockey = horse_data.get('jockey', '')
    if jockey in CHAMPION_JOCKEYS:
        bonus = CHELTENHAM_BONUSES['champion_jockey']
        bonus_breakdown['Champion Jockey'] = bonus
        total_bonus += bonus
    
    # Race type bonuses
    race_name = race_data.get('name', '').lower()
    race_type = race_data.get('type', '').lower()
    
    # Grade 1 Championships (the big ones)
    championship_races = [
        'supreme novices', 'arkle', 'champion hurdle', 'mares hurdle',
        'queen mother champion chase', 'champion chase', 'cheltenham gold cup',
        'gold cup', 'stayers hurdle', 'triumph hurdle', 'champion bumper'
    ]
    
    if any(name in race_name for name in championship_races):
        bonus = CHELTENHAM_BONUSES['grade1_championship']
        bonus_breakdown['Grade 1 Championship'] = bonus
        total_bonus += bonus
    
    # Grade 1 Novices
    elif 'grade 1' in race_type and ('novice' in race_name or 'novice' in race_type):
        bonus = CHELTENHAM_BONUSES['grade1_novice']
        bonus_breakdown['Grade 1 Novice'] = bonus
        total_bonus += bonus
    
    # Handicap penalty
    if 'handicap' in race_name or 'handicap' in race_type:
        penalty = CHELTENHAM_BONUSES['handicap_penalty']
        bonus_breakdown['Handicap Penalty'] = penalty
        total_bonus += penalty
    
    enhanced_score = base_score + total_bonus
    
    return enhanced_score, bonus_breakdown

def analyze_cheltenham_race(race_data, verbose=True):
    """
    Analyze a single Cheltenham race
    
    Returns:
        - All horses analyzed (for opinions)
        - Betting recommendations (75+ only)
        - Watch list (60-74)
        - Learning data (sub-60)
    """
    results = {
        'betting_picks': [],    # 75+ confidence
        'watch_list': [],       # 60-74 confidence
        'learning_data': [],    # < 60 confidence
    }
    
    race_name = race_data.get('name', 'Unknown Race')
    race_time = race_data.get('time', '')
    runners = race_data.get('runners', [])
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"CHELTENHAM FESTIVAL - {race_name}")
        print(f"Time: {race_time} | Runners: {len(runners)}")
        print(f"{'='*80}\n")
    
    for horse in runners:
        # Get base comprehensive score (our validated logic)
        base_score, reasoning, breakdown = analyze_horse_comprehensive(
            horse, 
            race_data, 
            DEFAULT_WEIGHTS
        )
        
        # Apply Cheltenham-specific bonuses
        enhanced_score, cheltenham_bonuses = apply_cheltenham_bonuses(
            horse, 
            race_data, 
            base_score
        )
        
        # Get confidence tier
        tier = get_confidence_tier(enhanced_score)
        
        # Package result
        result = {
            'horse_name': horse.get('name', 'Unknown'),
            'base_score': base_score,
            'cheltenham_bonuses': cheltenham_bonuses,
            'final_score': enhanced_score,
            'confidence_tier': tier,
            'odds': horse.get('odds', 0),
            'trainer': horse.get('trainer', ''),
            'jockey': horse.get('jockey', ''),
            'reasoning': reasoning,
            'breakdown': breakdown
        }
        
        # Categorize
        if enhanced_score >= 75:
            results['betting_picks'].append(result)
        elif enhanced_score >= 60:
            results['watch_list'].append(result)
        else:
            results['learning_data'].append(result)
    
    # Sort each category by score
    for category in results.values():
        category.sort(key=lambda x: x['final_score'], reverse=True)
    
    if verbose:
        print_race_analysis(race_name, results)
    
    return results

def print_race_analysis(race_name, results):
    """Print formatted analysis for a race"""
    
    print(f"\n🎯 BETTING RECOMMENDATIONS (75+ confidence)")
    print(f"{'='*80}")
    if results['betting_picks']:
        for pick in results['betting_picks']:
            print(f"\n✅ BET THIS: {pick['horse_name']} @ {pick['odds']}")
            print(f"   Score: {pick['final_score']:.0f} pts ({pick['confidence_tier']})")
            print(f"   Base: {pick['base_score']:.0f} | Cheltenham Bonus: {pick['final_score'] - pick['base_score']:.0f}")
            print(f"   Trainer: {pick['trainer']} | Jockey: {pick['jockey']}")
            print(f"   Reasoning: {pick['reasoning'][:100]}...")
            if pick['cheltenham_bonuses']:
                print(f"   Festival Factors: {', '.join([f'{k} (+{v})' for k,v in pick['cheltenham_bonuses'].items()])}")
    else:
        print("   ❌ NO BETTING PICKS - No horses reached 75+ confidence threshold")
        print("   Recommendation: SKIP this race or wait for odds changes")
    
    print(f"\n\n👀 WATCH LIST (60-74 confidence)")
    print(f"{'='*80}")
    if results['watch_list']:
        for pick in results['watch_list'][:3]:  # Top 3
            print(f"   {pick['horse_name']:25s} {pick['final_score']:3.0f}pts @ {pick['odds']} - {pick['trainer']}")
    else:
        print("   No horses in watch range")
    
    print(f"\n\n📊 OPINION ON ALL ({len(results['learning_data'])} other runners analyzed)")
    print(f"{'='*80}")
    print(f"   (Full analysis available for learning - not recommended for betting)")
    
    print(f"\n{'='*80}\n")

def generate_daily_report(day_number):
    """Generate full report for a Festival day"""
    
    # This would load actual race data from API/scraper
    # For now, showing the structure
    
    print(f"\n{'#'*80}")
    print(f"CHELTENHAM FESTIVAL 2026 - DAY {day_number} COMPREHENSIVE REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}\n")
    
    print("STRATEGY:")
    print("  ✅ Every race analyzed with validated comprehensive logic")
    print("  ✅ Cheltenham-specific bonuses applied (Festival history, elite raiders)")
    print("  🎯 ONLY bet on 75+ confidence picks")
    print("  👀 Watch list for 60-74 picks (smaller stakes)")
    print("  📊 Learning data collected on all others\n")
    
    # Example races for Day 1
    day_1_races = [
        {'name': 'Supreme Novices Hurdle', 'type': 'Grade 1 Novice Hurdle', 'time': '13:30'},
        {'name': 'Arkle Challenge Trophy', 'type': 'Grade 1 Chase', 'time': '14:10'},
        {'name': 'Ultima Handicap Chase', 'type': 'Handicap Chase', 'time': '14:50'},
        {'name': 'Champion Hurdle', 'type': 'Grade 1 Hurdle', 'time': '15:30'},
        {'name': 'Mares Hurdle', 'type': 'Grade 1 Hurdle', 'time': '16:10'},
        {'name': 'National Hunt Chase', 'type': 'Amateur Chase', 'time': '16:50'},
        {'name': 'Boodles Fred Winter', 'type': 'Handicap Hurdle', 'time': '17:30'},
    ]
    
    print(f"DAY {day_number} RACES: {len(day_1_races)}")
    for race in day_1_races:
        print(f"  - {race['time']} {race['name']} ({race['type']})")
    
    print(f"\n{'='*80}")
    print("To get full analysis, run with actual race data loaded")
    print(f"{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(description='Cheltenham Festival Analysis')
    parser.add_argument('--day', type=int, help='Festival day (1-4)')
    parser.add_argument('--all', action='store_true', help='Analyze all 4 days')
    parser.add_argument('--race', type=str, help='Specific race name')
    
    args = parser.parse_args()
    
    if args.day:
        generate_daily_report(args.day)
    elif args.all:
        for day in range(1, 5):
            generate_daily_report(day)
    else:
        print("Cheltenham Festival Comprehensive Analysis")
        print("\nUsage:")
        print("  python cheltenham_comprehensive_analysis.py --day 1")
        print("  python cheltenham_comprehensive_analysis.py --all")
        print("\nThis tool:")
        print("  ✅ Analyzes EVERY race at Cheltenham Festival")
        print("  ✅ Applies validated Feb 14 logic + Festival bonuses")
        print("  ✅ Recommends ONLY 75+ confidence picks for betting")
        print("  ✅ Provides watch list (60-74) and learning data")
        print("  ✅ Expected: 10-15 betting picks across 4 days")

if __name__ == '__main__':
    main()

"""
Comprehensive Analysis & Historical Learning System
Analyzes all today's races, stores picks, then refines logic based on ALL historical data
"""

import subprocess
import json
from datetime import datetime
from decimal import Decimal
import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def run_command(description, command):
    """Run a command and return success status"""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"\n⚠ WARNING: {description} returned code {result.returncode}")
            print(result.stderr)
            return False
        
        print(f"\n✓ {description} completed")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def analyze_todays_races():
    """Fetch and analyze all today's races"""
    print("\n" + "="*80)
    print("STEP 1: FETCH AND ANALYZE TODAY'S RACES")
    print("="*80)
    
    # Fetch races
    run_command("Fetching today's races from Betfair", "python betfair_odds_fetcher.py")
    
    # Check what we got
    try:
        with open('response_horses.json', 'r') as f:
            data = json.load(f)
        races = data.get('races', [])
        print(f"\n✓ Found {len(races)} races")
        
        # Show summary
        venues = {}
        for race in races:
            venue = race.get('venue', 'Unknown')
            venues[venue] = venues.get(venue, 0) + 1
        
        print("\nVenues:")
        for venue, count in sorted(venues.items()):
            print(f"  {venue}: {count} races")
        
    except Exception as e:
        print(f"❌ Could not read race data: {e}")
        return False
    
    # Analyze all races with comprehensive logic
    print("\n" + "="*80)
    print("Analyzing all races with comprehensive scoring...")
    print("="*80)
    
    run_command("Running comprehensive analysis", "python analyze_all_races_comprehensive.py")
    
    return True


def store_all_races_for_learning():
    """Store ALL horses from all races for comprehensive learning"""
    print("\n" + "="*80)
    print("STEP 2: STORE ALL RACES FOR LEARNING")
    print("="*80)
    
    run_command("Storing all horses for learning", "python complete_race_learning.py store")
    
    return True


def analyze_historical_performance():
    """Analyze ALL historical data to find best overall logic"""
    print("\n" + "="*80)
    print("STEP 3: COMPREHENSIVE HISTORICAL ANALYSIS")
    print("="*80)
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get all historical picks with outcomes
    print("Querying all historical picks...")
    
    all_picks = []
    last_evaluated_key = None
    
    # Scan all dates
    while True:
        if last_evaluated_key:
            response = table.scan(
                FilterExpression='attribute_exists(outcome) AND attribute_exists(comprehensive_score)',
                ExclusiveStartKey=last_evaluated_key,
                Limit=1000
            )
        else:
            response = table.scan(
                FilterExpression='attribute_exists(outcome) AND attribute_exists(comprehensive_score)',
                Limit=1000
            )
        
        items = response.get('Items', [])
        all_picks.extend(items)
        
        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break
        
        print(f"  Retrieved {len(all_picks)} picks so far...")
    
    print(f"\n✓ Found {len(all_picks)} historical picks with outcomes")
    
    if len(all_picks) < 10:
        print("⚠ Not enough historical data for comprehensive analysis")
        print("  Need at least 10 picks with outcomes")
        return False
    
    # Analyze by various criteria
    print("\n" + "="*80)
    print("ANALYZING HISTORICAL PATTERNS")
    print("="*80)
    
    # Group by different factors
    by_odds_range = {
        '2-3': [], '3-4': [], '4-5': [], '5-6': [], '6-7': [], '7-8': [], '8-9': [], '9+': []
    }
    by_score_range = {
        '60-69': [], '70-79': [], '80-89': [], '90-100': []
    }
    by_form_quality = {
        'excellent': [],  # 1 in last 3 races
        'good': [],       # 2 or 3 in last 3
        'moderate': [],   # 4-6 in last 3
        'poor': []        # 7+ or no recent placings
    }
    
    for pick in all_picks:
        odds = float(pick.get('odds', 0))
        score = float(pick.get('comprehensive_score', 0))
        form = str(pick.get('form', ''))
        outcome = pick.get('outcome', '')
        
        # By odds
        if 2 <= odds < 3:
            by_odds_range['2-3'].append(pick)
        elif 3 <= odds < 4:
            by_odds_range['3-4'].append(pick)
        elif 4 <= odds < 5:
            by_odds_range['4-5'].append(pick)
        elif 5 <= odds < 6:
            by_odds_range['5-6'].append(pick)
        elif 6 <= odds < 7:
            by_odds_range['6-7'].append(pick)
        elif 7 <= odds < 8:
            by_odds_range['7-8'].append(pick)
        elif 8 <= odds < 9:
            by_odds_range['8-9'].append(pick)
        else:
            by_odds_range['9+'].append(pick)
        
        # By score
        if 60 <= score < 70:
            by_score_range['60-69'].append(pick)
        elif 70 <= score < 80:
            by_score_range['70-79'].append(pick)
        elif 80 <= score < 90:
            by_score_range['80-89'].append(pick)
        elif score >= 90:
            by_score_range['90-100'].append(pick)
        
        # By form
        if '1' in form[:3]:
            by_form_quality['excellent'].append(pick)
        elif '2' in form[:3] or '3' in form[:3]:
            by_form_quality['good'].append(pick)
        elif any(c in form[:3] for c in ['4', '5', '6']):
            by_form_quality['moderate'].append(pick)
        else:
            by_form_quality['poor'].append(pick)
    
    # Calculate win rates
    print("\nWIN RATES BY ODDS RANGE:")
    print("-" * 60)
    best_odds_range = None
    best_odds_rate = 0
    
    for odds_range, picks in sorted(by_odds_range.items()):
        if not picks:
            continue
        wins = sum(1 for p in picks if p.get('outcome') == 'win')
        win_rate = (wins / len(picks)) * 100
        roi_estimate = (win_rate / 100) * float(odds_range.split('-')[0] if '-' in odds_range else odds_range.replace('+', '')) - 1
        
        print(f"  {odds_range:6} odds: {len(picks):3} picks, {wins:3} wins ({win_rate:5.1f}%) - Estimated ROI: {roi_estimate*100:+6.1f}%")
        
        if win_rate > best_odds_rate and len(picks) >= 5:
            best_odds_rate = win_rate
            best_odds_range = odds_range
    
    print(f"\n  ⭐ BEST: {best_odds_range} range with {best_odds_rate:.1f}% win rate")
    
    print("\nWIN RATES BY COMPREHENSIVE SCORE:")
    print("-" * 60)
    best_score_range = None
    best_score_rate = 0
    
    for score_range, picks in sorted(by_score_range.items()):
        if not picks:
            continue
        wins = sum(1 for p in picks if p.get('outcome') == 'win')
        win_rate = (wins / len(picks)) * 100
        
        print(f"  Score {score_range}: {len(picks):3} picks, {wins:3} wins ({win_rate:5.1f}%)")
        
        if win_rate > best_score_rate and len(picks) >= 5:
            best_score_rate = win_rate
            best_score_range = score_range
    
    print(f"\n  ⭐ BEST: Score {best_score_range} with {best_score_rate:.1f}% win rate")
    
    print("\nWIN RATES BY FORM QUALITY:")
    print("-" * 60)
    
    for form_cat, picks in sorted(by_form_quality.items()):
        if not picks:
            continue
        wins = sum(1 for p in picks if p.get('outcome') == 'win')
        win_rate = (wins / len(picks)) * 100
        
        print(f"  {form_cat:10}: {len(picks):3} picks, {wins:3} wins ({win_rate:5.1f}%)")
    
    # Overall statistics
    print("\n" + "="*80)
    print("OVERALL PERFORMANCE")
    print("="*80)
    
    total_wins = sum(1 for p in all_picks if p.get('outcome') == 'win')
    total_places = sum(1 for p in all_picks if p.get('outcome') == 'placed')
    total_losses = sum(1 for p in all_picks if p.get('outcome') == 'loss')
    
    overall_win_rate = (total_wins / len(all_picks)) * 100
    place_rate = (total_places / len(all_picks)) * 100
    
    print(f"\nTotal historical picks: {len(all_picks)}")
    print(f"  Wins: {total_wins} ({overall_win_rate:.1f}%)")
    print(f"  Places: {total_places} ({place_rate:.1f}%)")
    print(f"  Losses: {total_losses}")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS FOR LOGIC OPTIMIZATION")
    print("="*80)
    
    print(f"\n1. OPTIMAL ODDS RANGE: {best_odds_range}")
    print(f"   - Achieves {best_odds_rate:.1f}% win rate")
    print(f"   - Adjust sweet_spot weight if needed")
    
    print(f"\n2. MINIMUM SCORE THRESHOLD: {best_score_range}")
    print(f"   - Achieves {best_score_rate:.1f}% win rate")
    print(f"   - Consider raising minimum from 75 to {score_range.split('-')[0]}")
    
    form_analysis = []
    for form_cat, picks in by_form_quality.items():
        if picks:
            wins = sum(1 for p in picks if p.get('outcome') == 'win')
            rate = (wins / len(picks)) * 100
            form_analysis.append((form_cat, rate, len(picks)))
    
    form_analysis.sort(key=lambda x: x[1], reverse=True)
    best_form = form_analysis[0] if form_analysis else None
    
    if best_form:
        print(f"\n3. FORM IMPORTANCE: {best_form[0].upper()} form performs best ({best_form[1]:.1f}%)")
        if best_form[0] == 'poor':
            print("   - Consider REDUCING recent_win weight")
        elif best_form[0] == 'excellent':
            print("   - Consider INCREASING recent_win weight")
    
    # Store insights
    learning_record = {
        'bet_id': f'HISTORICAL_ANALYSIS_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'bet_date': today,
        'learning_type': 'COMPREHENSIVE_HISTORICAL',
        'total_picks_analyzed': len(all_picks),
        'overall_win_rate': Decimal(str(overall_win_rate)),
        'best_odds_range': best_odds_range,
        'best_odds_win_rate': Decimal(str(best_odds_rate)),
        'best_score_range': best_score_range,
        'best_score_win_rate': Decimal(str(best_score_rate)),
        'recommendations': {
            'optimal_odds': best_odds_range,
            'minimum_score': best_score_range,
            'form_priority': best_form[0] if best_form else 'unknown'
        },
        'analyzed_at': datetime.now().isoformat()
    }
    
    table.put_item(Item=learning_record)
    print(f"\n✓ Historical analysis saved to DynamoDB")
    
    return True


def main():
    """Run complete analysis and learning workflow"""
    
    print("\n" + "="*80)
    print("COMPREHENSIVE ANALYSIS & HISTORICAL LEARNING")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Step 1: Analyze today's races
    print("\n📊 Analyzing all today's meetings:")
    print("   - Carlisle (7 races)")
    print("   - Fairyhouse (7 races)")
    print("   - Taunton (7 races)")
    print("   - Wolverhampton (7 races)")
    
    if not analyze_todays_races():
        print("\n❌ Failed to analyze today's races")
        return
    
    # Step 2: Store all races for learning
    if not store_all_races_for_learning():
        print("\n❌ Failed to store races for learning")
        return
    
    # Step 3: Comprehensive historical analysis
    if not analyze_historical_performance():
        print("\n❌ Failed to analyze historical performance")
        return
    
    # Summary
    print("\n" + "="*80)
    print("WORKFLOW COMPLETE")
    print("="*80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✓ All races analyzed")
    print("✓ All horses stored for learning")
    print("✓ Historical patterns identified")
    print("✓ Recommendations generated")
    print("\nNext: Review recommendations and adjust weights in auto_adjust_weights.py")
    print("="*80)


if __name__ == "__main__":
    main()

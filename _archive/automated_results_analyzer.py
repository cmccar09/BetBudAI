"""
Automated Results Analyzer
Fetches results and automatically compares with pre-race analysis
"""

import json
import boto3
from datetime import datetime
from decimal import Decimal
import subprocess
import time

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

def fetch_and_process_all_results():
    """Fetch results and process all completed races"""
    
    print(f"\n{'='*80}")
    print(f"AUTOMATED RESULTS ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*80}\n")
    
    # Step 1: Fetch results from Betfair
    print("Fetching race results from Betfair...")
    try:
        result = subprocess.run(
            ['python', 'betfair_results_fetcher_v2.py'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print("   INFO: No new results available yet")
            return 0
        
        print("   Results fetched successfully")
    except Exception as e:
        print(f"   ERROR fetching results: {str(e)}")
        return 0
    
    # Step 2: Load results data
    try:
        with open('race_results.json', 'r') as f:
            results_data = json.load(f)
    except FileNotFoundError:
        print("   ℹ️  No results file found")
        return 0
    
    # Step 3: Process each completed race
    races_processed = 0
    learnings_created = 0
    
    for race_result in results_data.get('results', []):
        market_id = race_result.get('marketId')
        venue = race_result.get('venue', 'Unknown')
        race_time = race_result.get('startTime', 'Unknown')
        
        # Get winner info
        runners = race_result.get('runners', [])
        winner = next((r for r in runners if r.get('status') == 'WINNER'), None)
        
        if not winner:
            continue
        
        winner_name = winner.get('runnerName', 'Unknown')
        
        # Query our pre-race analysis
        response = table.scan(
            FilterExpression='market_id = :mid AND analysis_type = :type',
            ExpressionAttributeValues={
                ':mid': market_id,
                ':type': 'PRE_RACE_COMPLETE'
            }
        )
        
        analyses = response.get('Items', [])
        
        if not analyses:
            print(f"   ⚠️  No pre-race analysis for {venue} {race_time}")
            continue
        
        # Find winner in our analysis
        winner_analysis = None
        for a in analyses:
            if a['horse'].lower() == winner_name.lower():
                winner_analysis = a
                break
        
        if not winner_analysis:
            print(f"   ⚠️  Winner {winner_name} not in our analysis")
            continue
        
        # Create learning entry
        learning = analyze_race_result(
            venue,
            race_time,
            market_id,
            winner_name,
            winner_analysis,
            analyses,
            runners
        )
        
        if learning:
            table.put_item(Item=learning)
            learnings_created += 1
            print(f"   ✓ {venue} {race_time[:5]}: {winner_name} ({winner_analysis['odds']} odds)")
        
        races_processed += 1
    
    print(f"\n{'='*80}")
    print(f"RESULTS SUMMARY")
    print(f"   Races processed: {races_processed}")
    print(f"   Learnings created: {learnings_created}")
    print(f"{'='*80}\n")
    
    return learnings_created

def analyze_race_result(venue, race_time, market_id, winner_name, winner_analysis, all_analyses, race_runners):
    """Analyze a single race result"""
    
    # Calculate winner's position in betting
    sorted_by_odds = sorted(all_analyses, key=lambda x: float(x['odds']) if x['odds'] else 999)
    winner_position = 0
    for idx, horse in enumerate(sorted_by_odds, 1):
        if horse['horse'] == winner_name:
            winner_position = idx
            break
    
    # Extract insights
    insights = []
    
    # Form analysis
    winner_form = winner_analysis.get('form', '')
    if winner_form and winner_form != 'Unknown':
        if winner_form and len(winner_form) > 0 and winner_form[0] == '1':
            insights.append('Winner won last race (LTO winner)')
        if '1' in winner_form[:3]:
            insights.append('Winner had win in last 3 runs')
        win_count = winner_form.count('1')
        if win_count >= 2:
            insights.append(f'Winner had {win_count} recent wins in form')
    
    # Odds analysis
    winner_odds = float(winner_analysis['odds']) if winner_analysis['odds'] else 0
    if winner_odds >= 3.0 and winner_odds <= 9.0:
        insights.append('Winner in SWEET SPOT odds (3.0-9.0)')
        odds_category = 'SWEET_SPOT'
    elif winner_odds < 3.0:
        insights.append(f'Winner was favorite/short-priced ({winner_odds} odds)')
        odds_category = 'FAVORITE'
    elif winner_odds > 15.0:
        insights.append(f'Winner was LONGSHOT ({winner_odds} odds)')
        odds_category = 'LONGSHOT'
    else:
        insights.append(f'Winner outside sweet spot ({winner_odds} odds)')
        odds_category = 'NEAR_SWEET_SPOT'
    
    # Position analysis
    if winner_position == 1:
        insights.append('Favorite won')
    elif winner_position <= 3:
        insights.append(f'{winner_position}rd favorite won')
    else:
        insights.append(f'{winner_position}th in betting won (upset)')
    
    # Get placed horses
    placed_horses = []
    for runner in race_runners:
        if runner.get('status') in ['PLACED', 'WINNER']:
            for a in all_analyses:
                if a['horse'].lower() == runner.get('runnerName', '').lower():
                    placed_horses.append({
                        'name': a['horse'],
                        'odds': a['odds'],
                        'form': a.get('form', 'Unknown'),
                        'status': runner.get('status')
                    })
                    break
    
    # Create learning entry
    learning = {
        'bet_id': f'RESULT_{market_id}_{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'bet_date': datetime.now().strftime('%Y-%m-%d'),
        'learning_type': 'RACE_RESULT_ANALYSIS',
        'venue': venue,
        'race_time': race_time,
        'market_id': market_id,
        
        # Winner details
        'winner': winner_name,
        'winner_odds': Decimal(str(winner_odds)),
        'winner_odds_category': odds_category,
        'winner_form': winner_analysis.get('form', 'Unknown'),
        'winner_trainer': winner_analysis.get('trainer', 'Unknown'),
        'winner_position_in_betting': winner_position,
        'favorite_won': (winner_position == 1),
        
        # Race details
        'total_runners': len(all_analyses),
        'insights': insights,
        'placed_horses': placed_horses,
        
        # Metadata
        'analyzed_at': datetime.now().isoformat(),
        'analysis_purpose': 'CONTINUOUS_LEARNING'
    }
    
    return learning

def generate_pattern_summary():
    """Generate summary of recent patterns"""
    
    print(f"\n{'='*80}")
    print(f"PATTERN ANALYSIS SUMMARY")
    print(f"{'='*80}\n")
    
    # Query recent learnings (last 24 hours)
    from datetime import timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    response = table.scan(
        FilterExpression='learning_type = :type AND (bet_date = :today OR bet_date = :yesterday)',
        ExpressionAttributeValues={
            ':type': 'RACE_RESULT_ANALYSIS',
            ':today': today,
            ':yesterday': yesterday
        }
    )
    
    results = response.get('Items', [])
    
    if not results:
        print("   ℹ️  No results to analyze yet")
        return
    
    # Calculate statistics
    total = len(results)
    sweet_spot_wins = sum(1 for r in results if r.get('winner_odds_category') == 'SWEET_SPOT')
    favorite_wins = sum(1 for r in results if r.get('favorite_won', False))
    longshot_wins = sum(1 for r in results if r.get('winner_odds_category') == 'LONGSHOT')
    lto_winners = sum(1 for r in results if any('LTO winner' in i for i in r.get('insights', [])))
    
    print(f"📊 Results from last 24 hours: {total} races\n")
    print(f"   Sweet Spot (3-9 odds):  {sweet_spot_wins:3d} wins ({100*sweet_spot_wins/total:5.1f}%)")
    print(f"   Favorites won:          {favorite_wins:3d} wins ({100*favorite_wins/total:5.1f}%)")
    print(f"   Longshots (15+ odds):   {longshot_wins:3d} wins ({100*longshot_wins/total:5.1f}%)")
    print(f"   LTO winners:            {lto_winners:3d} wins ({100*lto_winners/total:5.1f}%)")
    
    print(f"\n{'='*80}\n")
    
    # Save pattern summary
    pattern_summary = {
        'bet_id': f'PATTERN_SUMMARY_{datetime.now().strftime("%Y%m%d")}',
        'bet_date': datetime.now().strftime('%Y-%m-%d'),
        'learning_type': 'PATTERN_ANALYSIS',
        'total_races': total,
        'sweet_spot_wins': sweet_spot_wins,
        'sweet_spot_pct': Decimal(str(100*sweet_spot_wins/total)),
        'favorite_wins': favorite_wins,
        'favorite_pct': Decimal(str(100*favorite_wins/total)),
        'longshot_wins': longshot_wins,
        'lto_winners': lto_winners,
        'lto_pct': Decimal(str(100*lto_winners/total)),
        'analyzed_at': datetime.now().isoformat()
    }
    
    table.put_item(Item=pattern_summary)
    
    return pattern_summary

def main():
    """Main execution"""
    learnings = fetch_and_process_all_results()
    
    if learnings > 0:
        print("\n📊 Generating pattern analysis...")
        generate_pattern_summary()
    
    return learnings

if __name__ == "__main__":
    main()

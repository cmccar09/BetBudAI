"""
COORDINATED MASTER WORKFLOW
Continuously learn and improve throughout the day

SCHEDULE (Automated via Task Scheduler):
- 11:00am-7:00pm: Background learning (every 30min)
- 12:00pm-8:00pm: Racing Post scraper (every 30min)  
- 1:00pm-9:00pm: Results matching & learning (every hour)

CONTINUOUS LEARNING LOOP:
1. Analyze ALL races -> Learn patterns
2. Match results as they come in -> Update weights
3. Apply learnings to next race predictions
4. Only show high-confidence picks on UI

DUAL-TRACK SYSTEM:
- Learning Track: Analyze 100% of horses (show_in_ui=False)
- UI Track: Show only validated high-confidence picks (show_in_ui=True)
"""

import subprocess
import time
from datetime import datetime
import boto3
from decimal import Decimal
from track_daily_insights import add_race_insight, print_track_insights

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
bets_table = dynamodb.Table('SureBetBets')
racingpost_table = dynamodb.Table('RacingPostRaces')


def step1_analyze_all_races():
    """
    LEARNING: Analyze ALL horses in ALL races
    - Saves to database with show_in_ui=False (learning) and show_in_ui=True (UI picks 85+)
    - Uses strict 85+ threshold for UI promotion
    - 100% race coverage tracking
    """
    print("\n" + "="*80)
    print("STEP 1: COMPREHENSIVE ANALYSIS (Learning + UI Picks)")
    print("="*80)
    print("Analyzing every horse with 7-factor scoring...")
    print("Learning: ALL horses | UI: Only 85+ (Sure Thing)")
    
    try:
        result = subprocess.run(
            ['python', 'complete_daily_analysis.py'],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        # Show summary
        lines = result.stdout.split('\n')
        for line in lines:
            if 'analyzed' in line.lower() or 'Total' in line or 'saved' in line.lower():
                print(f"  {line}")
        
        if result.returncode == 0:
            print("✓ All races analyzed and saved for learning")
            
            # Save top tips for all races (for end-of-day report)
            try:
                print("\nSaving top tips for performance tracking...")
                tips_result = subprocess.run(
                    ['python', 'save_all_race_tips.py'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if tips_result.returncode == 0:
                    print("✓ Tips saved for daily performance report")
                else:
                    print("  (Tips save had issues - non-critical)")
            except Exception as e:
                print(f"  (Could not save tips: {e})")
            
            return True
        else:
            print(f"⚠️ Analysis had issues: {result.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ Error in analysis: {e}")
        return False


def step2_match_racingpost_results():
    """
    RESULTS: Match Racing Post results with our picks
    - Updates picks with win/loss outcomes
    - Provides real race results for learning
    """
    print("\n" + "="*80)
    print("STEP 2: MATCH RACING POST RESULTS")
    print("="*80)
    print("Matching completed races with our predictions...")
    
    try:
        # Check if we have Racing Post data
        today = datetime.now().strftime('%Y-%m-%d')
        response = racingpost_table.query(
            IndexName='DateIndex',
            KeyConditionExpression='raceDate = :date',
            ExpressionAttributeValues={':date': today}
        )
        
        races = response.get('Items', [])
        races_with_results = [r for r in races if r.get('hasResults', False)]
        
        print(f"Racing Post races today: {len(races)}")
        print(f"Races with results: {len(races_with_results)}")
        
        if len(races_with_results) == 0:
            print("⚠️ No results available yet - skipping matching")
            return False
        
        # Run matching
        result = subprocess.run(
            ['python', 'match_racingpost_to_betfair.py'],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✓ Results matched successfully")
            return True
        else:
            print(f"⚠️ Matching had issues")
            return False
            
    except Exception as e:
        print(f"✗ Error in matching: {e}")
        return False


def step3_learn_from_results():
    """
    LEARNING: Adjust weights based on what actually won
    - Analyzes win/loss patterns
    - Updates scoring weights
    - Improves future predictions
    - Captures track-specific insights for same-day learning
    """
    print("\n" + "="*80)
    print("STEP 3: LEARN FROM RESULTS")
    print("="*80)
    print("Adjusting weights based on actual outcomes...")
    
    try:
        # First, capture track-specific insights from today's winners
        print("\nCapturing track-specific insights...")
        capture_track_insights()
        
        # Then adjust global weights
        result = subprocess.run(
            ['python', 'auto_adjust_weights.py'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Show key learning insights
        lines = result.stdout.split('\n')
        for line in lines:
            if 'Weight' in line or 'adjusted' in line.lower() or 'Winners' in line:
                print(f"  {line}")
        
        if result.returncode == 0:
            print("✓ Weights adjusted based on results")
            return True
        else:
            print(f"⚠️ Learning had issues")
            return False
            
    except Exception as e:
        print(f"✗ Error in learning: {e}")
        return False


def step4_generate_ui_picks():
    """
    UI PICKS: Report current UI pick status.
    NOTE: All UI picks are managed by comprehensive_workflow.py via add_pick_to_ui().
    This step no longer promotes learning data to the UI — that caused pollution
    from skipped-race runners and low-confidence candidates appearing in results.
    """
    print("\n" + "="*80)
    print("STEP 4: UI PICKS STATUS")
    print("="*80)
    print("UI picks are set exclusively by comprehensive_workflow (add_pick_to_ui).")
    print("No promotion from learning data to prevent skipped-race contamination.")
    
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        response = bets_table.query(
            KeyConditionExpression='bet_date = :date',
            ExpressionAttributeValues={':date': today}
        )
        
        items = response.get('Items', [])
        current_ui = [i for i in items if i.get('show_in_ui') == True]
        learning_data = [i for i in items if not i.get('show_in_ui')]
        
        print(f"Total analyzed: {len(items)}")
        print(f"UI picks (set by comprehensive_workflow): {len(current_ui)}")
        print(f"Learning data: {len(learning_data)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking UI picks status: {e}")
        return False


def check_system_status():
    """Quick health check of the learning system"""
    print("\n" + "="*80)
    print("SYSTEM STATUS")
    print("="*80)
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Check bets table
        response = bets_table.query(
            KeyConditionExpression='bet_date = :date',
            ExpressionAttributeValues={':date': today}
        )
        items = response.get('Items', [])
        ui_picks = [i for i in items if i.get('show_in_ui') == True]
        learning = [i for i in items if not i.get('show_in_ui')]
        
        print(f"Bets analyzed today: {len(items)}")
        print(f"  UI picks: {len(ui_picks)}")
        print(f"  Learning data: {len(learning)}")
        
        # Check Racing Post table
        rp_response = racingpost_table.query(
            IndexName='DateIndex',
            KeyConditionExpression='raceDate = :date',
            ExpressionAttributeValues={':date': today}
        )
        rp_races = rp_response.get('Items', [])
        rp_results = [r for r in rp_races if r.get('hasResults', False)]
        
        print(f"\nRacing Post scrapes: {len(rp_races)}")
        print(f"  With results: {len(rp_results)}")
        
        print("\n✓ System operational")
        return True
        
    except Exception as e:
        print(f"✗ Status check failed: {e}")
        return False


def capture_track_insights():
    """
    Capture insights from today's race winners at each track
    Learn what factors are working today at each venue
    """
    try:
        # Get all horses with outcomes from today
        response = bets_table.scan()
        items = response.get('Items', [])
        
        # Group winners by track
        track_winners = {}
        
        for item in items:
            if item.get('outcome') == 'WON':
                course = item.get('course', '')
                race_time = item.get('race_time', '')
                
                if course and race_time:
                    if course not in track_winners:
                        track_winners[course] = []
                    
                    # Get the breakdown from database
                    breakdown = {}
                    for key in ['sweet_spot', 'optimal_odds', 'recent_win', 'total_wins', 
                               'consistency', 'course_bonus', 'database_history', 'going_suitability']:
                        if key in item:
                            breakdown[key] = int(item[key])
                    
                    track_winners[course].append({
                        'winner_data': item,
                        'breakdown': breakdown,
                        'race_time': race_time
                    })
        
        # Add insights for each track's winners
        insights_added = 0
        for course, winners in track_winners.items():
            for winner_info in winners:
                add_race_insight(
                    course=course,
                    race_time=winner_info['race_time'],
                    winner_data=winner_info['winner_data'],
                    breakdown=winner_info['breakdown']
                )
                insights_added += 1
        
        if insights_added > 0:
            print(f"✓ Captured insights from {insights_added} winners across {len(track_winners)} tracks")
            
            # Show insights for each track
            for course in track_winners.keys():
                print_track_insights(course)
        else:
            print("  No winner insights to capture yet")
        
        return True
        
    except Exception as e:
        print(f"  Warning: Could not capture track insights: {e}")
        return False


def main():
    """Run complete coordinated workflow"""
    print("\n" + "="*100)
    print("COORDINATED LEARNING WORKFLOW")
    print("="*100)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis workflow:")
    print("  1. Analyzes ALL races for learning")
    print("  2. Matches Racing Post results with predictions")
    print("  3. Learns from outcomes and adjusts weights")
    print("  4. Captures track-specific patterns for same-day learning")
    print("  5. Promotes high-confidence picks to UI")
    print("="*100)
    
    # System health check
    check_system_status()
    
    # Step 1: Analyze all races
    analyzed = step1_analyze_all_races()
    
    if not analyzed:
        print("\n⚠️ Analysis step failed - continuing anyway")
    
    # Step 2: Match results
    matched = step2_match_racingpost_results()
    
    if not matched:
        print("\n⚠️ No results to match yet - skipping learning")
    else:
        # Step 3: Learn from results (only if we have matches)
        learned = step3_learn_from_results()
        
        if learned:
            print("\n✓ Learning complete - weights updated")
    
    # Step 4: Generate UI picks (always run)
    step4_generate_ui_picks()
    
    print("\n" + "="*100)
    print("WORKFLOW COMPLETE")
    print("="*100)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nNext steps:")
    print("  - Check UI for updated high-confidence picks")
    print("  - Monitor learning progress in logs")
    print("  - Racing Post scraper will provide more results")
    print("  - Track insights improve predictions throughout the day")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()

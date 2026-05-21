"""
Daily Performance Report
Compares AI tips vs actual race results
Runs at 7pm to show how well predictions performed
"""
import boto3
import json
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
bets_table = dynamodb.Table('SureBetBets')
results_table = dynamodb.Table('RacingPostRaces')

def get_race_result(course, time):
    """Get actual race result from Racing Post table"""
    try:
        # Search for race result
        response = results_table.scan(
            FilterExpression='contains(course, :course) AND contains(race_time, :time)',
            ExpressionAttributeValues={
                ':course': course,
                ':time': time
            }
        )
        
        items = response.get('Items', [])
        if items:
            # Find the winner
            for item in items:
                if item.get('position') == '1' or item.get('actual_position') == 1:
                    return {
                        'winner': item.get('horse', item.get('runner_name', 'Unknown')),
                        'odds': item.get('odds', item.get('sp', 'N/A')),
                        'found': True
                    }
        
        # Alternative: check our bets table for outcomes
        response = bets_table.scan(
            FilterExpression='contains(course, :course) AND contains(race_time, :time)',
            ExpressionAttributeValues={
                ':course': course,
                ':time': time
            }
        )
        
        for item in response.get('Items', []):
            if item.get('outcome') == 'WON':
                return {
                    'winner': item.get('horse', 'Unknown'),
                    'odds': item.get('odds', 'N/A'),
                    'found': True
                }
        
        return {'winner': None, 'found': False}
        
    except Exception as e:
        print(f"Error getting result for {course} {time}: {e}")
        return {'winner': None, 'found': False}

def generate_performance_report():
    """Generate end-of-day performance report"""
    
    today = datetime.now().strftime('%Y-%m-%d')
    tips_file = f'daily_tips_{today}.json'
    
    if not os.path.exists(tips_file):
        print(f"No tips file found for today ({tips_file})")
        print("Run save_all_race_tips.py first to generate tips")
        return
    
    # Load tips
    with open(tips_file, 'r') as f:
        tips_data = json.load(f)
    
    tips = tips_data['tips']
    
    # Compare with results
    results = []
    wins = 0
    places = 0  # Top 3
    races_completed = 0
    total_stake = 0
    total_return = 0
    
    print("\n" + "="*100)
    print(f"DAILY PERFORMANCE REPORT - {today}")
    print("="*100)
    print(f"Generated: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Tips saved: {tips_data['generated_at']}")
    print(f"Total races: {len(tips)}")
    print("="*100)
    
    for tip in tips:
        course = tip['course']
        time = tip['time']
        my_tip = tip['tip']
        my_score = tip['score']
        my_odds = tip['odds']
        
        result = get_race_result(course, time)
        
        if result['found']:
            races_completed += 1
            actual_winner = result['winner']
            
            # Check if we got it right
            is_win = (my_tip.lower() == actual_winner.lower())
            
            # Calculate hypothetical returns (£10 stake)
            stake = 10
            total_stake += stake
            
            if is_win:
                wins += 1
                win_return = stake * my_odds
                total_return += win_return
                outcome = f"✓ WIN  (Return: £{win_return:.2f})"
            else:
                outcome = f"✗ LOST"
            
            results.append({
                'course': course,
                'time': time,
                'my_tip': my_tip,
                'score': my_score,
                'odds': my_odds,
                'actual_winner': actual_winner,
                'is_win': is_win,
                'outcome': outcome
            })
            
            print(f"\n{time} {course}")
            print(f"  My Tip: {my_tip} ({my_score:.0f}/100 @{my_odds})")
            print(f"  Winner: {actual_winner}")
            print(f"  Result: {outcome}")
        else:
            results.append({
                'course': course,
                'time': time,
                'my_tip': my_tip,
                'score': my_score,
                'odds': my_odds,
                'actual_winner': 'PENDING',
                'is_win': None,
                'outcome': 'Race not finished or result not captured'
            })
    
    # Summary statistics
    print("\n" + "="*100)
    print("PERFORMANCE SUMMARY")
    print("="*100)
    
    if races_completed > 0:
        win_rate = (wins / races_completed) * 100
        profit_loss = total_return - total_stake
        roi = (profit_loss / total_stake) * 100 if total_stake > 0 else 0
        
        print(f"\nRaces Completed: {races_completed}/{len(tips)}")
        print(f"Winners Predicted: {wins}/{races_completed} ({win_rate:.1f}%)")
        print(f"\nHypothetical Performance (£10 stakes):")
        print(f"  Total Staked:  £{total_stake:.2f}")
        print(f"  Total Returns: £{total_return:.2f}")
        print(f"  Profit/Loss:   £{profit_loss:+.2f}")
        print(f"  ROI:          {roi:+.1f}%")
        
        # Grade the performance
        print(f"\nPerformance Grade:")
        if win_rate >= 35:
            grade = "EXCELLENT - Exceeding target (35%+)"
        elif win_rate >= 25:
            grade = "GOOD - On target (25-35%)"
        elif win_rate >= 15:
            grade = "FAIR - Below target (15-25%)"
        else:
            grade = "POOR - Needs improvement (<15%)"
        print(f"  {grade}")
        
        if roi > 0:
            print(f"  Profitable on the day!")
        
    else:
        print("\nNo completed races to analyze yet")
        print(f"Pending: {len(tips) - races_completed} races")
    
    print("\n" + "="*100)
    
    # Save report
    report_file = f'performance_report_{today}.json'
    report_data = {
        'date': today,
        'generated_at': datetime.now().isoformat(),
        'total_races': len(tips),
        'completed_races': races_completed,
        'wins': wins,
        'win_rate': (wins / races_completed * 100) if races_completed > 0 else 0,
        'total_stake': total_stake,
        'total_return': total_return,
        'profit_loss': total_return - total_stake,
        'roi': ((total_return - total_stake) / total_stake * 100) if total_stake > 0 else 0,
        'results': results
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"Report saved to: {report_file}\n")
    
    return report_data

if __name__ == '__main__':
    generate_performance_report()

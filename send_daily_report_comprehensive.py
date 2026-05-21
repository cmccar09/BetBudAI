"""
Comprehensive Daily Report Email
Sends daily email with:
- Race results with outcomes
- Win rate and ROI calculations
- Learning insights from the day
- Performance by course, odds range, etc.
"""
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
bets_table = dynamodb.Table('SureBetBets')
ses = boto3.client('ses', region_name='eu-west-1')

# Email configuration
FROM_EMAIL = 'directorai@futuregenai.com'
TO_EMAIL = 'charles.mccarthy@gmail.com'

def get_yesterday_results():
    """Get yesterday's picks with results (System A only - actual bets with scores)"""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    response = bets_table.scan(
        FilterExpression='#d = :date OR bet_date = :date',
        ExpressionAttributeNames={'#d': 'date'},
        ExpressionAttributeValues={':date': yesterday}
    )
    
    all_picks = response.get('Items', [])
    
    # Filter to System A only: picks with stake <= 10 (excludes learning_workflow picks)
    # System A = Comprehensive scoring system with £5-6 stakes
    # System B = Learning workflow with £12-30 stakes (data collection only)
    system_a_picks = [
        pick for pick in all_picks 
        if float(pick.get('stake', 0)) <= 10
    ]
    
    return system_a_picks, yesterday

def calculate_stats(picks):
    """Calculate performance statistics"""
    stats = {
        'total_picks': len(picks),
        'wins': 0,
        'losses': 0,
        'pending': 0,
        'total_stake': 0,
        'total_profit': 0,
        'win_rate': 0,
        'roi': 0,
        'by_course': defaultdict(lambda: {'wins': 0, 'total': 0, 'profit': 0}),
        'by_odds_range': defaultdict(lambda: {'wins': 0, 'total': 0, 'profit': 0}),
        'high_confidence': {'wins': 0, 'total': 0, 'profit': 0},
        'elite_trainers': {'wins': 0, 'total': 0, 'profit': 0}
    }
    
    for pick in picks:
        outcome = pick.get('outcome', '').upper()
        stake = float(pick.get('stake', 5))
        profit = float(pick.get('profit', 0))
        odds = float(pick.get('odds', 0))
        course = pick.get('course', 'Unknown')
        score = float(pick.get('comprehensive_score', pick.get('combined_score', 0)))
        trainer = pick.get('trainer', '')
        
        stats['total_stake'] += stake
        stats['total_profit'] += profit
        
        if outcome in ['WIN', 'WINNER']:
            stats['wins'] += 1
            stats['by_course'][course]['wins'] += 1
            
            # Odds range
            if odds < 3.0:
                range_key = '1.5-3.0 (Favorites)'
            elif odds <= 5.0:
                range_key = '3.0-5.0 (Sweet Spot)'
            elif odds <= 9.0:
                range_key = '5.0-9.0 (Value)'
            else:
                range_key = '9.0+ (Longshots)'
            stats['by_odds_range'][range_key]['wins'] += 1
            stats['by_odds_range'][range_key]['total'] += 1
            stats['by_odds_range'][range_key]['profit'] += profit
            
            # High confidence tracking
            if score >= 75:
                stats['high_confidence']['wins'] += 1
                stats['high_confidence']['profit'] += profit
            
            # Elite trainer tracking
            if any(elite in trainer for elite in ['Mullins', 'Elliott', 'Henderson', 'Nicholls', 'Skelton']):
                stats['elite_trainers']['wins'] += 1
                stats['elite_trainers']['profit'] += profit
                
        elif outcome in ['LOSS', 'LOSER']:
            stats['losses'] += 1
            
            # Track losses by odds range
            if odds < 3.0:
                range_key = '1.5-3.0 (Favorites)'
            elif odds <= 5.0:
                range_key = '3.0-5.0 (Sweet Spot)'
            elif odds <= 9.0:
                range_key = '5.0-9.0 (Value)'
            else:
                range_key = '9.0+ (Longshots)'
            stats['by_odds_range'][range_key]['total'] += 1
            stats['by_odds_range'][range_key]['profit'] += profit
            
            if score >= 75:
                stats['high_confidence']['total'] += 1
                stats['high_confidence']['profit'] += profit
                
            if any(elite in trainer for elite in ['Mullins', 'Elliott', 'Henderson', 'Nicholls', 'Skelton']):
                stats['elite_trainers']['total'] += 1
                stats['elite_trainers']['profit'] += profit
        else:
            stats['pending'] += 1
        
        stats['by_course'][course]['total'] += 1
        stats['by_course'][course]['profit'] += profit
    
    # Calculate rates
    completed = stats['wins'] + stats['losses']
    if completed > 0:
        stats['win_rate'] = (stats['wins'] / completed) * 100
    
    if stats['total_stake'] > 0:
        stats['roi'] = (stats['total_profit'] / stats['total_stake']) * 100
    
    # Calculate high confidence stats
    if stats['high_confidence']['total'] > 0:
        stats['high_confidence']['win_rate'] = (stats['high_confidence']['wins'] / stats['high_confidence']['total']) * 100
    
    # Calculate elite trainer stats
    if stats['elite_trainers']['total'] > 0:
        stats['elite_trainers']['win_rate'] = (stats['elite_trainers']['wins'] / stats['elite_trainers']['total']) * 100
    
    return stats

def generate_learning_insights(picks, stats):
    """Generate learning insights from the day's results"""
    insights = {
        'strengths': [],
        'weaknesses': [],
        'patterns': [],
        'recommendations': []
    }
    
    # Analyze what worked
    if stats['win_rate'] >= 40:
        insights['strengths'].append(f"Strong overall win rate of {stats['win_rate']:.1f}% (target: 35%+)")
    
    if stats['roi'] >= 15:
        insights['strengths'].append(f"Excellent ROI of {stats['roi']:.1f}% (target: 15%+)")
    elif stats['roi'] >= 10:
        insights['strengths'].append(f"Good ROI of {stats['roi']:.1f}% (target: 10%+)")
    
    # Check high confidence performance
    if stats['high_confidence']['total'] > 0:
        hc_rate = stats['high_confidence']['win_rate']
        if hc_rate >= 50:
            insights['strengths'].append(f"High confidence picks (75+) performing excellently: {hc_rate:.1f}% win rate")
        elif hc_rate < 35:
            insights['weaknesses'].append(f"High confidence picks underperforming: only {hc_rate:.1f}% win rate")
    
    # Check elite trainer performance
    if stats['elite_trainers']['total'] > 0:
        et_rate = stats['elite_trainers']['win_rate']
        if et_rate >= 40:
            insights['strengths'].append(f"Elite trainers delivering: {et_rate:.1f}% win rate")
        elif et_rate < 30:
            insights['weaknesses'].append(f"Elite trainers underperforming: {et_rate:.1f}% win rate")
    
    # Analyze by odds range
    for range_name, range_stats in stats['by_odds_range'].items():
        if range_stats['total'] >= 3:  # Only report if enough samples
            range_rate = (range_stats['wins'] / range_stats['total']) * 100
            if range_rate >= 40:
                insights['patterns'].append(f"{range_name} performing well: {range_rate:.1f}% win rate ({range_stats['wins']}/{range_stats['total']})")
            elif range_rate < 20:
                insights['patterns'].append(f"{range_name} struggling: {range_rate:.1f}% win rate ({range_stats['wins']}/{range_stats['total']})")
    
    # Best courses
    best_courses = [(course, data) for course, data in stats['by_course'].items() 
                    if data['total'] >= 2 and data['wins'] > 0]
    best_courses.sort(key=lambda x: (x[1]['wins'] / x[1]['total']), reverse=True)
    if best_courses:
        course, data = best_courses[0]
        rate = (data['wins'] / data['total']) * 100
        insights['patterns'].append(f"{course} top course: {rate:.1f}% win rate ({data['wins']}/{data['total']})")
    
    # Generate recommendations
    if stats['win_rate'] < 30:
        insights['recommendations'].append("Consider raising score threshold - current selections may be too aggressive")
    
    if stats['roi'] < 0:
        insights['recommendations'].append("Negative ROI - focus on odds sweet spots (3.0-7.0) and elite trainers")
    
    if stats['high_confidence']['total'] > 0 and stats['high_confidence']['win_rate'] < 40:
        insights['recommendations'].append("High confidence picks not converting - review scoring factors")
    
    if not insights['recommendations']:
        if stats['win_rate'] >= 35 and stats['roi'] >= 10:
            insights['recommendations'].append("System performing well - maintain current strategy")
        else:
            insights['recommendations'].append("Continue gathering data to identify patterns")
    
    return insights

def generate_html_email(picks, date, stats, insights):
    """Generate HTML email content"""
    
    # Status color based on performance
    if stats['roi'] >= 15:
        status_color = '#27ae60'  # Green
        status_text = 'EXCELLENT'
    elif stats['roi'] >= 10:
        status_color = '#f39c12'  # Orange
        status_text = 'GOOD'
    elif stats['roi'] >= 0:
        status_color = '#3498db'  # Blue
        status_text = 'POSITIVE'
    else:
        status_color = '#e74c3c'  # Red
        status_text = 'NEGATIVE'
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; }}
            .header .date {{ font-size: 16px; opacity: 0.9; margin-top: 5px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; padding: 20px; background-color: #f8f9fa; }}
            .stat-card {{ background-color: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .stat-value {{ font-size: 32px; font-weight: bold; color: {status_color}; }}
            .stat-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
            .section {{ padding: 25px; }}
            .section-title {{ font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 15px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
            .race-card {{ background-color: #f8f9fa; padding: 15px; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid #667eea; }}
            .race-win {{ border-left-color: #27ae60; }}
            .race-loss {{ border-left-color: #e74c3c; }}
            .race-pending {{ border-left-color: #95a5a6; }}
            .race-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
            .race-horse {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
            .race-outcome {{ font-size: 14px; padding: 5px 12px; border-radius: 20px; font-weight: bold; }}
            .outcome-win {{ background-color: #27ae60; color: white; }}
            .outcome-loss {{ background-color: #e74c3c; color: white; }}
            .outcome-pending {{ background-color: #95a5a6; color: white; }}
            .race-details {{ font-size: 14px; color: #666; }}
            .race-profit {{ font-size: 16px; font-weight: bold; margin-top: 10px; }}
            .profit-positive {{ color: #27ae60; }}
            .profit-negative {{ color: #e74c3c; }}
            .insight-box {{ background-color: #f8f9fa; padding: 15px; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid #3498db; }}
            .insight-strength {{ border-left-color: #27ae60; }}
            .insight-weakness {{ border-left-color: #e74c3c; }}
            .insight-pattern {{ border-left-color: #f39c12; }}
            .insight-recommendation {{ border-left-color: #9b59b6; }}
            .footer {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏇 SureBet Daily Report</h1>
                <div class="date">{date} | Status: {status_text}</div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{stats['win_rate']:.1f}%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats['roi']:.1f}%</div>
                    <div class="stat-label">ROI</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats['wins']}/{stats['total_picks']}</div>
                    <div class="stat-label">Wins / Total</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" class="{'profit-positive' if stats['total_profit'] >= 0 else 'profit-negative'}">
                        {'£' if stats['total_profit'] >= 0 else '-£'}{abs(stats['total_profit']):.2f}
                    </div>
                    <div class="stat-label">Profit/Loss</div>
                </div>
            </div>
    """
    
    # Race results section
    if picks:
        html += """
            <div class="section">
                <div class="section-title">📊 Race Results</div>
        """
        
        for pick in sorted(picks, key=lambda x: x.get('race_time', '')):
            horse = pick.get('horse', 'Unknown')
            course = pick.get('course', 'Unknown')
            race_time = pick.get('race_time', '')
            if 'T' in str(race_time):
                race_time = race_time.split('T')[1][:5]
            
            odds = pick.get('odds', 'N/A')
            score = pick.get('comprehensive_score', pick.get('combined_score', 'N/A'))
            outcome = pick.get('outcome', 'PENDING').upper()
            profit = float(pick.get('profit', 0))
            stake = float(pick.get('stake', 5))
            trainer = pick.get('trainer', 'Unknown')
            finishing_pos = pick.get('finishing_position', '-')
            
            # Determine card class and outcome badge
            if outcome in ['WIN', 'WINNER']:
                card_class = 'race-win'
                outcome_class = 'outcome-win'
                outcome_text = f'✓ WON (Finished: 1st)'
            elif outcome in ['LOSS', 'LOSER']:
                card_class = 'race-loss'
                outcome_class = 'outcome-loss'
                outcome_text = f'✗ LOST (Finished: {finishing_pos})'
            else:
                card_class = 'race-pending'
                outcome_class = 'outcome-pending'
                outcome_text = '⏳ PENDING'
            
            profit_class = 'profit-positive' if profit >= 0 else 'profit-negative'
            profit_text = f"{'Profit' if profit >= 0 else 'Loss'}: {'£' if profit >= 0 else '-£'}{abs(profit):.2f} (Stake: £{stake:.2f})"
            
            html += f"""
                <div class="race-card {card_class}">
                    <div class="race-header">
                        <div class="race-horse">{horse}</div>
                        <div class="race-outcome {outcome_class}">{outcome_text}</div>
                    </div>
                    <div class="race-details">
                        📍 {course} | ⏰ {race_time} | 💰 {odds} | 📊 Score: {score} | 👨‍🏫 {trainer}
                    </div>
                    <div class="race-profit {profit_class}">{profit_text}</div>
                </div>
            """
        
        html += "</div>"
    
    # Learning insights section
    html += """
        <div class="section">
            <div class="section-title">🧠 Learning Insights</div>
    """
    
    if insights['strengths']:
        html += '<h3 style="color: #27ae60; font-size: 16px; margin-top: 20px;">✓ Strengths</h3>'
        for strength in insights['strengths']:
            html += f'<div class="insight-box insight-strength">{strength}</div>'
    
    if insights['weaknesses']:
        html += '<h3 style="color: #e74c3c; font-size: 16px; margin-top: 20px;">✗ Weaknesses</h3>'
        for weakness in insights['weaknesses']:
            html += f'<div class="insight-box insight-weakness">{weakness}</div>'
    
    if insights['patterns']:
        html += '<h3 style="color: #f39c12; font-size: 16px; margin-top: 20px;">📈 Patterns Identified</h3>'
        for pattern in insights['patterns']:
            html += f'<div class="insight-box insight-pattern">{pattern}</div>'
    
    if insights['recommendations']:
        html += '<h3 style="color: #9b59b6; font-size: 16px; margin-top: 20px;">💡 Recommendations</h3>'
        for rec in insights['recommendations']:
            html += f'<div class="insight-box insight-recommendation">{rec}</div>'
    
    html += """
            </div>
            
            <div class="footer">
                <p>Automated Daily Report from SureBet AI System</p>
                <p>View full dashboard: <a href="https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/yesterday" style="color: #3498db;">API</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_text_email(picks, date, stats, insights):
    """Generate plain text email content"""
    
    text = f"""
================================================================================
SUREBET DAILY REPORT - {date}
================================================================================

PERFORMANCE SUMMARY
-------------------
Win Rate: {stats['win_rate']:.1f}%
ROI: {stats['roi']:.1f}%
Wins: {stats['wins']} / {stats['total_picks']}
Profit/Loss: {'£' if stats['total_profit'] >= 0 else '-£'}{abs(stats['total_profit']):.2f}
Total Stake: £{stats['total_stake']:.2f}

================================================================================
RACE RESULTS
================================================================================
"""
    
    for pick in sorted(picks, key=lambda x: x.get('race_time', '')):
        horse = pick.get('horse', 'Unknown')
        course = pick.get('course', 'Unknown')
        odds = pick.get('odds', 'N/A')
        outcome = pick.get('outcome', 'PENDING').upper()
        profit = float(pick.get('profit', 0))
        finishing_pos = pick.get('finishing_position', '-')
        
        if outcome in ['WIN', 'WINNER']:
            result = f"WON (1st)"
        elif outcome in ['LOSS', 'LOSER']:
            result = f"LOST ({finishing_pos})"
        else:
            result = "PENDING"
        
        text += f"\n{horse} @ {course}\n"
        text += f"  Odds: {odds} | Outcome: {result}\n"
        text += f"  Profit: {'£' if profit >= 0 else '-£'}{abs(profit):.2f}\n"
    
    text += f"""
================================================================================
LEARNING INSIGHTS
================================================================================
"""
    
    if insights['strengths']:
        text += "\nSTRENGTHS:\n"
        for strength in insights['strengths']:
            text += f"  ✓ {strength}\n"
    
    if insights['weaknesses']:
        text += "\nWEAKNESSES:\n"
        for weakness in insights['weaknesses']:
            text += f"  ✗ {weakness}\n"
    
    if insights['patterns']:
        text += "\nPATTERNS:\n"
        for pattern in insights['patterns']:
            text += f"  • {pattern}\n"
    
    if insights['recommendations']:
        text += "\nRECOMMENDATIONS:\n"
        for rec in insights['recommendations']:
            text += f"  → {rec}\n"
    
    text += "\n" + "="*80 + "\n"
    
    return text

def send_email(subject, html_body, text_body):
    """Send email via AWS SES"""
    try:
        response = ses.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [TO_EMAIL]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': text_body},
                    'Html': {'Data': html_body}
                }
            }
        )
        print(f"✓ Email sent! Message ID: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        print("\nEmail preview (text version):")
        print(text_body)
        return False

def main():
    """Main function"""
    print("Generating comprehensive daily report...")
    print("="*70)
    
    # Get data
    picks, date = get_yesterday_results()
    
    if not picks:
        print(f"No picks found for {date}")
        print("This is expected if workflows weren't running that day")
        return
    
    print(f"Found {len(picks)} picks for {date}")
    
    # Calculate stats
    stats = calculate_stats(picks)
    print(f"Win Rate: {stats['win_rate']:.1f}%")
    print(f"ROI: {stats['roi']:.1f}%")
    print(f"Profit: £{stats['total_profit']:.2f}")
    
    # Generate insights
    insights = generate_learning_insights(picks, stats)
    print(f"\nInsights: {len(insights['strengths'])} strengths, {len(insights['weaknesses'])} weaknesses")
    
    # Generate email
    subject = f"SureBet Daily Report - {date} | Win Rate: {stats['win_rate']:.1f}% | ROI: {stats['roi']:.1f}%"
    html_body = generate_html_email(picks, date, stats, insights)
    text_body = generate_text_email(picks, date, stats, insights)
    
    # Send email
    success = send_email(subject, html_body, text_body)
    
    if success:
        print("\n✓ Daily report sent successfully!")
    else:
        print("\n✗ Failed to send email (see preview above)")
        
        # Save to file as backup
        with open(f'daily_report_{date}.html', 'w', encoding='utf-8') as f:
            f.write(html_body)
        print(f"✓ Report saved to: daily_report_{date}.html")

if __name__ == "__main__":
    main()

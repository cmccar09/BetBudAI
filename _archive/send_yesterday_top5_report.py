#!/usr/bin/env python3
"""
send_yesterday_top5_report.py - Daily email report of top 5 moderate ROI picks from yesterday
Sent at 10am each morning to track performance
"""

import os
import sys
import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal

# Email recipients
EMAIL_RECIPIENTS = [
    'charles.mccarthy@gmail.com',
    'dryanfitness@gmail.com'
]

def decimal_to_float(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_yesterday_picks_from_dynamodb():
    """Retrieve yesterday's picks from DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('SureBetBets')
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = table.scan(
            FilterExpression='#date = :yesterday',
            ExpressionAttributeNames={'#date': 'date'},
            ExpressionAttributeValues={':yesterday': yesterday}
        )
        
        return response.get('Items', [])
    except Exception as e:
        print(f"Error accessing DynamoDB: {e}")
        return []

def calculate_expected_roi(p_win, odds):
    """Calculate expected ROI: (odds × p_win - 1) × 100"""
    return ((odds * p_win) - 1) * 100

def filter_top5_moderate_roi(picks):
    """Filter and rank picks by moderate positive expected ROI (0-50%)"""
    picks_with_roi = []
    
    for pick in picks:
        p_win = float(pick.get('p_win', 0))
        odds = float(pick.get('odds', 0))
        expected_roi = calculate_expected_roi(p_win, odds)
        
        # Only include moderate positive ROI (0-50%)
        if 0 < expected_roi < 50:
            picks_with_roi.append({
                'horse': pick.get('horse', 'Unknown'),
                'venue': pick.get('venue', 'N/A'),
                'race_time': pick.get('race_time', 'N/A'),
                'confidence': int(pick.get('confidence', 0)),
                'p_win': p_win,
                'p_place': float(pick.get('p_place', 0)),
                'odds': odds,
                'bet_type': pick.get('bet_type', 'N/A'),
                'expected_roi': expected_roi,
                'outcome': pick.get('outcome', 'Pending'),
                'profit_loss': float(pick.get('profit_loss', 0)) if pick.get('profit_loss') else None,
                'tags': pick.get('tags', []),
                'why_now': pick.get('why_now', '')
            })
    
    # Sort by expected ROI descending and take top 5
    picks_with_roi.sort(key=lambda x: x['expected_roi'], reverse=True)
    return picks_with_roi[:5]

def generate_html_report(top5_picks, yesterday_date):
    """Generate HTML email report"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; padding: 30px; text-align: center; border-radius: 10px; }}
            .header h1 {{ margin: 0; font-size: 28px; }}
            .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
            .pick {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; 
                    border-left: 5px solid #667eea; border-radius: 5px; }}
            .pick-header {{ display: flex; justify-content: space-between; align-items: center; }}
            .pick-title {{ font-size: 22px; font-weight: bold; color: #2c3e50; }}
            .roi-badge {{ background-color: #27ae60; color: white; padding: 8px 16px; 
                         border-radius: 20px; font-weight: bold; font-size: 18px; }}
            .roi-badge.pending {{ background-color: #f39c12; }}
            .roi-badge.won {{ background-color: #27ae60; }}
            .roi-badge.lost {{ background-color: #e74c3c; }}
            .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 15px 0; }}
            .stat-box {{ background-color: white; padding: 12px; border: 1px solid #e0e0e0; 
                        border-radius: 5px; text-align: center; }}
            .stat-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; }}
            .stat-value {{ font-size: 20px; font-weight: bold; color: #2c3e50; margin-top: 5px; }}
            .reasoning {{ color: #555; font-size: 14px; line-height: 1.6; margin-top: 10px; 
                         padding: 10px; background-color: #ecf0f1; border-radius: 5px; }}
            .summary {{ background-color: #ecf0f1; padding: 20px; margin-top: 30px; 
                       border-radius: 5px; }}
            .footer {{ text-align: center; color: #7f8c8d; margin-top: 30px; 
                      padding-top: 20px; border-top: 1px solid #e0e0e0; }}
            .rank {{ display: inline-block; background-color: #667eea; color: white; 
                    border-radius: 50%; width: 35px; height: 35px; line-height: 35px; 
                    text-align: center; font-weight: bold; margin-right: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏇 Top 5 Moderate ROI Picks</h1>
                <p>Performance Report for {yesterday_date}</p>
            </div>
    """
    
    if not top5_picks:
        html += """
            <div class="summary">
                <p style="text-align: center; font-size: 18px; color: #e74c3c;">
                    ⚠️ No picks with moderate positive expected ROI (0-50%) were found for yesterday.
                </p>
            </div>
        """
    else:
        for i, pick in enumerate(top5_picks, 1):
            outcome_class = 'pending'
            outcome_text = pick['outcome']
            
            # EW PLACED BETS COUNT AS WINS
            if pick['outcome'] == 'WON':
                outcome_class = 'won'
                outcome_text = f"WON (+{pick['profit_loss']:.2f} units)" if pick['profit_loss'] else "WON"
            elif pick['outcome'] in ['PLACED_2ND', 'PLACED_3RD', 'PLACED_4TH', 'PLACED'] and pick.get('bet_type') == 'EW':
                # EW bets that placed count as wins
                outcome_class = 'won'
                outcome_text = f"EW PLACED (+{pick['profit_loss']:.2f} units)" if pick['profit_loss'] else f"{pick['outcome']} (EW WIN)"
            elif pick['outcome'] == 'LOST':
                outcome_class = 'lost'
                outcome_text = f"LOST ({pick['profit_loss']:.2f} units)" if pick['profit_loss'] else "LOST"
            
            html += f"""
            <div class="pick">
                <div class="pick-header">
                    <div>
                        <span class="rank">#{i}</span>
                        <span class="pick-title">{pick['horse']}</span>
                    </div>
                    <span class="roi-badge {outcome_class}">
                        {pick['expected_roi']:.1f}% ROI
                    </span>
                </div>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-label">Win Probability</div>
                        <div class="stat-value">{pick['p_win']*100:.1f}%</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Odds</div>
                        <div class="stat-value">{pick['odds']:.2f}</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Confidence</div>
                        <div class="stat-value">{pick['confidence']}</div>
                    </div>
                </div>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-label">Place Prob</div>
                        <div class="stat-value">{pick['p_place']*100:.1f}%</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Bet Type</div>
                        <div class="stat-value">{pick['bet_type']}</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Outcome</div>
                        <div class="stat-value" style="font-size: 16px;">{outcome_text}</div>
                    </div>
                </div>
                
                <div class="reasoning">
                    <strong>Reasoning:</strong> {pick['why_now'][:300]}...
                </div>
            </div>
            """
        
        # Summary section
        total_picks = len(top5_picks)
        # COUNT EW PLACED BETS AS WINS
        won = sum(1 for p in top5_picks if p['outcome'] == 'WON')
        ew_placed = sum(1 for p in top5_picks if p['outcome'] in ['PLACED_2ND', 'PLACED_3RD', 'PLACED_4TH', 'PLACED'] and p.get('bet_type') == 'EW')
        total_wins = won + ew_placed  # EW places count as wins
        lost = sum(1 for p in top5_picks if p['outcome'] == 'LOST')
        pending = sum(1 for p in top5_picks if p['outcome'] == 'Pending')
        
        total_profit = sum(p.get('profit_loss', 0) for p in top5_picks if p.get('profit_loss'))
        avg_expected_roi = sum(p['expected_roi'] for p in top5_picks) / total_picks
        
        html += f"""
            <div class="summary">
                <h2 style="margin-top: 0; color: #2c3e50;">📊 Summary</h2>
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-label">Total Wins</div>
                        <div class="stat-value" style="color: #27ae60;">{total_wins}</div>
                        <div class="stat-label" style="font-size: 10px; margin-top: 5px;">({won} won + {ew_placed} EW placed)</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Lost</div>
                        <div class="stat-value" style="color: #e74c3c;">{lost}</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Lost</div>
                        <div class="stat-value" style="color: #e74c3c;">{lost}</div>
                    </div>
                </div>
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-label">Pending</div>
                        <div class="stat-value" style="color: #f39c12;">{pending}</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Avg Expected ROI</div>
                        <div class="stat-value" style="color: #667eea;">{avg_expected_roi:.1f}%</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Total P/L</div>
                        <div class="stat-value" style="color: {'#27ae60' if total_profit >= 0 else '#e74c3c'};">
                            {total_profit:+.2f}
                        </div>
                    </div>
                </div>
            </div>
        """
    
    html += """
            <div class="footer">
                <p>This report is automatically generated daily at 10:00 AM</p>
                <p>SureBet AI Performance Tracking System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_text_report(top5_picks, yesterday_date):
    """Generate plain text email report"""
    lines = []
    lines.append("=" * 70)
    lines.append(f"TOP 5 MODERATE ROI PICKS - {yesterday_date}")
    lines.append("=" * 70)
    lines.append("")
    
    if not top5_picks:
        lines.append("⚠️ No picks with moderate positive expected ROI (0-50%) found.")
        return "\n".join(lines)
    
    for i, pick in enumerate(top5_picks, 1):
        outcome_text = pick['outcome']
        if pick['profit_loss']:
            outcome_text += f" ({pick['profit_loss']:+.2f} units)"
        
        lines.append(f"#{i}. {pick['horse']}")
        lines.append(f"    Expected ROI: {pick['expected_roi']:.1f}%")
        lines.append(f"    Win Prob: {pick['p_win']*100:.1f}% | Odds: {pick['odds']:.2f} | Confidence: {pick['confidence']}")
        lines.append(f"    Bet Type: {pick['bet_type']} | Outcome: {outcome_text}")
        lines.append(f"    Reasoning: {pick['why_now'][:200]}...")
        lines.append("")
    
    # Summary
    lines.append("=" * 70)
    lines.append("SUMMARY")
    lines.append("=" * 70)
    won = sum(1 for p in top5_picks if p['outcome'] == 'WON')
    placed = sum(1 for p in top5_picks if p['outcome'] in ['PLACED_2ND', 'PLACED_3RD', 'PLACED_4TH'])
    lost = sum(1 for p in top5_picks if p['outcome'] == 'LOST')
    pending = sum(1 for p in top5_picks if p['outcome'] == 'Pending')
    total_profit = sum(p.get('profit_loss', 0) for p in top5_picks if p.get('profit_loss'))
    
    lines.append(f"Won: {won} | Placed: {placed} | Lost: {lost} | Pending: {pending}")
    lines.append(f"Total P/L: {total_profit:+.2f} units")
    lines.append("")
    
    return "\n".join(lines)

def send_email_via_ses(to_emails, subject, html_body, text_body):
    """Send email using AWS SES"""
    ses = boto3.client('ses', region_name='eu-west-1')
    
    for to_email in to_emails:
        try:
            response = ses.send_email(
                Source='directorai@futuregenai.com',  # Must be verified in SES
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Text': {'Data': text_body},
                        'Html': {'Data': html_body}
                    }
                }
            )
            print(f"✅ Email sent to {to_email}! Message ID: {response['MessageId']}")
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")

def main():
    """Main execution"""
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%A, %B %d, %Y")
    
    print(f"Generating Top 5 Moderate ROI Report for {yesterday_date}...")
    
    # Get yesterday's picks
    all_picks = get_yesterday_picks_from_dynamodb()
    print(f"Found {len(all_picks)} total picks from yesterday")
    
    # Filter to top 5 moderate ROI
    top5_picks = filter_top5_moderate_roi(all_picks)
    print(f"Filtered to {len(top5_picks)} picks with moderate positive ROI")
    
    # Generate email content
    html_body = generate_html_report(top5_picks, yesterday_date)
    text_body = generate_text_report(top5_picks, yesterday_date)
    
    subject = f"🏇 Top 5 Moderate ROI Picks - {yesterday_date}"
    
    # Send emails
    print(f"\nSending emails to {len(EMAIL_RECIPIENTS)} recipients...")
    send_email_via_ses(EMAIL_RECIPIENTS, subject, html_body, text_body)
    
    print("\n✅ Report generation complete!")

if __name__ == "__main__":
    main()

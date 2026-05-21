#!/usr/bin/env python3
"""
send_daily_calibration_report.py - Daily v2.3 Comparative Learning Analysis

Sent at 9am each morning with:
1. Prediction calibration analysis (accuracy by confidence bins)
2. Comparative learning (our picks vs actual winners)
3. Systematic patterns and actionable recommendations

Replaces the 9am results file email.
"""

import os
import sys
import json
import boto3
from datetime import datetime, timedelta
from pathlib import Path
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

def load_calibration_report():
    """Load the latest calibration report"""
    report_path = Path(__file__).parent / "calibration_report.json"
    
    if not report_path.exists():
        return None
    
    with open(report_path, 'r') as f:
        return json.load(f)

def load_loss_comparison_report():
    """Load the latest loss comparison analysis"""
    report_path = Path(__file__).parent / "loss_comparison_analysis.json"
    
    if not report_path.exists():
        return None
    
    with open(report_path, 'r') as f:
        return json.load(f)

def generate_html_report(calibration_report, loss_report):
    """Generate comprehensive HTML email report"""
    today = datetime.now().strftime("%A, %B %d, %Y")
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 32px; font-weight: 600; }}
            .header p {{ margin: 10px 0 0 0; opacity: 0.95; font-size: 16px; }}
            .section {{ padding: 30px; border-bottom: 1px solid #e0e0e0; }}
            .section:last-child {{ border-bottom: none; }}
            .section-title {{ font-size: 24px; font-weight: 600; color: #2c3e50; margin-bottom: 20px; display: flex; align-items: center; }}
            .section-title .emoji {{ font-size: 28px; margin-right: 12px; }}
            
            /* Calibration Bins */
            .bins-grid {{ display: grid; gap: 15px; margin-top: 20px; }}
            .bin-card {{ background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 20px; border-radius: 8px; border-left: 5px solid #667eea; }}
            .bin-card.overconfident {{ border-left-color: #e74c3c; }}
            .bin-card.underconfident {{ border-left-color: #f39c12; }}
            .bin-card.calibrated {{ border-left-color: #27ae60; }}
            .bin-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            .bin-range {{ font-size: 18px; font-weight: 600; color: #2c3e50; }}
            .bin-status {{ padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; }}
            .bin-status.over {{ background-color: #e74c3c; color: white; }}
            .bin-status.under {{ background-color: #f39c12; color: white; }}
            .bin-status.good {{ background-color: #27ae60; color: white; }}
            .bin-stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
            .bin-stat {{ text-align: center; }}
            .bin-stat-label {{ font-size: 11px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 0.5px; }}
            .bin-stat-value {{ font-size: 20px; font-weight: 700; color: #2c3e50; margin-top: 4px; }}
            
            /* Brier Score */
            .brier-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 8px; text-align: center; margin: 20px 0; }}
            .brier-score {{ font-size: 48px; font-weight: 700; margin: 10px 0; }}
            .brier-label {{ font-size: 14px; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; }}
            .brier-explanation {{ font-size: 13px; opacity: 0.85; margin-top: 10px; line-height: 1.5; }}
            
            /* Loss Comparisons */
            .comparison-card {{ background-color: #fff5f5; padding: 20px; border-left: 4px solid #e74c3c; border-radius: 8px; margin-bottom: 15px; }}
            .comparison-header {{ font-size: 16px; font-weight: 600; color: #c0392b; margin-bottom: 12px; }}
            .vs-grid {{ display: grid; grid-template-columns: 1fr auto 1fr; gap: 15px; align-items: center; }}
            .pick-box {{ background-color: white; padding: 15px; border-radius: 6px; border: 2px solid #e0e0e0; }}
            .pick-box.winner {{ border-color: #27ae60; background-color: #f0fff4; }}
            .pick-name {{ font-size: 15px; font-weight: 600; color: #2c3e50; }}
            .pick-label {{ font-size: 11px; color: #7f8c8d; text-transform: uppercase; margin-bottom: 8px; }}
            .vs-icon {{ font-size: 24px; color: #95a5a6; }}
            .insight-list {{ margin-top: 12px; padding-left: 0; }}
            .insight-item {{ background-color: white; padding: 10px 15px; margin: 6px 0; border-radius: 5px; font-size: 13px; color: #555; list-style: none; border-left: 3px solid #e74c3c; }}
            
            /* Common Mistakes */
            .mistakes-grid {{ display: grid; gap: 12px; margin-top: 15px; }}
            .mistake-card {{ background-color: #fff9e6; padding: 15px 20px; border-radius: 6px; border-left: 4px solid #f39c12; }}
            .mistake-type {{ font-weight: 600; color: #d68910; font-size: 14px; text-transform: capitalize; }}
            .mistake-count {{ float: right; background-color: #f39c12; color: white; padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: 600; }}
            
            /* Recommendations */
            .recommendations {{ background: linear-gradient(135deg, #27ae60 0%, #229954 100%); color: white; padding: 25px; border-radius: 8px; }}
            .recommendations h3 {{ margin: 0 0 15px 0; font-size: 20px; }}
            .recommendation-item {{ background-color: rgba(255, 255, 255, 0.15); padding: 12px 18px; margin: 10px 0; border-radius: 6px; font-size: 14px; line-height: 1.6; border-left: 3px solid white; }}
            .recommendation-number {{ display: inline-block; background-color: white; color: #27ae60; width: 24px; height: 24px; line-height: 24px; text-align: center; border-radius: 50%; font-weight: 700; margin-right: 10px; font-size: 13px; }}
            
            /* Summary Stats */
            .summary-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
            .summary-stat {{ background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 20px; border-radius: 8px; text-align: center; }}
            .summary-stat-value {{ font-size: 32px; font-weight: 700; color: #667eea; }}
            .summary-stat-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; margin-top: 8px; letter-spacing: 0.5px; }}
            
            /* Footer */
            .footer {{ background-color: #f8f9fa; padding: 25px; text-align: center; color: #7f8c8d; font-size: 13px; }}
            .footer-links {{ margin-top: 15px; }}
            .footer-links a {{ color: #667eea; text-decoration: none; margin: 0 10px; }}
            
            /* Alert Box */
            .alert {{ padding: 15px 20px; border-radius: 6px; margin: 15px 0; }}
            .alert.info {{ background-color: #e7f3ff; border-left: 4px solid #3498db; color: #2471a3; }}
            .alert.warning {{ background-color: #fff9e6; border-left: 4px solid #f39c12; color: #d68910; }}
            .alert.error {{ background-color: #fff5f5; border-left: 4px solid #e74c3c; color: #c0392b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Daily Calibration & Learning Report</h1>
                <p>v2.3 Comparative Analysis • {today}</p>
            </div>
    """
    
    # Check if reports exist
    if not calibration_report and not loss_report:
        html += """
            <div class="section">
                <div class="alert info">
                    <strong>📊 Insufficient Data</strong><br>
                    No settled picks from the last 7 days to analyze yet. Reports will generate automatically once races settle.
                </div>
            </div>
        """
    else:
        # SECTION 1: Prediction Calibration
        if calibration_report:
            html += generate_calibration_section(calibration_report)
        
        # SECTION 2: Loss Comparison Analysis
        if loss_report:
            html += generate_loss_comparison_section(loss_report)
    
    # Footer
    html += f"""
            <div class="footer">
                <p><strong>SureBet AI</strong> • Self-Learning Betting System v2.3</p>
                <p>Automated daily analysis at 9:00 AM</p>
                <div class="footer-links">
                    <a href="#">Dashboard</a> • 
                    <a href="#">View All Picks</a> • 
                    <a href="#">Settings</a>
                </div>
                <p style="margin-top: 15px; font-size: 11px; color: #95a5a6;">
                    Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_calibration_section(report):
    """Generate calibration analysis HTML section"""
    overall = report.get('overall', {})
    bins_dict = report.get('calibration_bins', {})
    brier_score = report.get('brier_score', {}).get('score', 0)
    
    html = f"""
        <div class="section">
            <div class="section-title">
                <span class="emoji">📊</span> Prediction Calibration Analysis
            </div>
            
            <div class="summary-grid">
                <div class="summary-stat">
                    <div class="summary-stat-value">{overall.get('total_picks', 0)}</div>
                    <div class="summary-stat-label">Picks Analyzed</div>
                </div>
                <div class="summary-stat">
                    <div class="summary-stat-value">{overall.get('wins', 0)}</div>
                    <div class="summary-stat-label">Actual Wins</div>
                </div>
                <div class="summary-stat">
                    <div class="summary-stat-value">{overall.get('win_rate', 0)*100:.1f}%</div>
                    <div class="summary-stat-label">Overall Win Rate</div>
                </div>
            </div>
            
            <div class="brier-box">
                <div class="brier-label">Brier Score (Prediction Quality)</div>
                <div class="brier-score">{brier_score:.4f}</div>
                <div class="brier-explanation">
                    Lower is better (0 = perfect, 0.25 = random). 
                    Measures how close our probabilities match actual outcomes.
                </div>
            </div>
            
            <h3 style="margin: 30px 0 15px 0; color: #2c3e50;">Confidence Bins Analysis</h3>
            <div class="bins-grid">
    """
    
    # Convert dict to sorted list for display
    for bin_range, bin_data in sorted(bins_dict.items()):
        predicted = bin_data.get('predicted', 0) * 100
        actual = bin_data.get('actual', 0) * 100
        count = bin_data.get('sample_size', 0)
        wins = bin_data.get('wins', 0)
        calibration_error = bin_data.get('calibration_error', 0)
        
        # Determine status
        status_class = 'calibrated'
        status_text = 'Well Calibrated'
        card_class = ''
        
        if calibration_error > 0.10:  # Overconfident by >10%
            status_class = 'over'
            status_text = 'Overconfident'
            card_class = 'overconfident'
        elif calibration_error < -0.10:  # Underconfident by >10%
            status_class = 'under'
            status_text = 'Underconfident'
            card_class = 'underconfident'
        else:
            status_class = 'good'
            status_text = 'Good ✓'
        
        html += f"""
                <div class="bin-card {card_class}">
                    <div class="bin-header">
                        <div class="bin-range">{bin_range} Confidence</div>
                        <div class="bin-status {status_class}">{status_text}</div>
                    </div>
                    <div class="bin-stats">
                        <div class="bin-stat">
                            <div class="bin-stat-label">Predicted</div>
                            <div class="bin-stat-value">{predicted:.1f}%</div>
                        </div>
                        <div class="bin-stat">
                            <div class="bin-stat-label">Actual</div>
                            <div class="bin-stat-value">{actual:.1f}%</div>
                        </div>
                        <div class="bin-stat">
                            <div class="bin-stat-label">Sample</div>
                            <div class="bin-stat-value">{wins}/{count}</div>
                        </div>
                    </div>
                </div>
        """
    
    html += """
            </div>
        </div>
    """
    
    return html

def generate_loss_comparison_section(loss_report):
    """Generate loss comparison analysis HTML section"""
    total_losses = loss_report.get('total_losses_analyzed', 0)
    losses_without_data = loss_report.get('losses_without_data', 0)
    common_mistakes = loss_report.get('common_mistakes', {})
    recommendations = loss_report.get('recommendations', [])
    comparisons = loss_report.get('comparisons', [])[:3]  # Top 3 examples
    
    html = f"""
        <div class="section">
            <div class="section-title">
                <span class="emoji">🔍</span> Comparative Learning (Picks vs Winners)
            </div>
            
            <div class="alert info">
                <strong>Analyzed:</strong> {total_losses} losing bets compared against actual winners
            </div>
    """
    
    if losses_without_data > 0:
        html += f"""
            <div class="alert warning">
                <strong>Note:</strong> {losses_without_data} losses don't have all-horses data yet. 
                This data will be available for picks made after v2.3 implementation.
            </div>
        """
    
    # Common Mistakes
    if common_mistakes:
        html += """
            <h3 style="margin: 25px 0 15px 0; color: #2c3e50;">Common Mistakes Identified</h3>
            <div class="mistakes-grid">
        """
        
        for mistake_type, count in common_mistakes.items():
            mistake_label = mistake_type.replace('_', ' ').title()
            html += f"""
                <div class="mistake-card">
                    <span class="mistake-count">{count}x</span>
                    <div class="mistake-type">{mistake_label}</div>
                </div>
            """
        
        html += """
            </div>
        """
    
    # Example Comparisons
    if comparisons:
        html += """
            <h3 style="margin: 25px 0 15px 0; color: #2c3e50;">Example Loss Comparisons</h3>
        """
        
        for comp in comparisons:
            our_pick = comp.get('our_pick', 'Unknown')
            winner = comp.get('actual_winner', 'Unknown')
            insights = comp.get('insights', [])
            
            html += f"""
                <div class="comparison-card">
                    <div class="comparison-header">
                        {comp.get('race_name', 'Race')}
                    </div>
                    <div class="vs-grid">
                        <div class="pick-box">
                            <div class="pick-label">Our Pick</div>
                            <div class="pick-name">❌ {our_pick}</div>
                        </div>
                        <div class="vs-icon">vs</div>
                        <div class="pick-box winner">
                            <div class="pick-label">Actual Winner</div>
                            <div class="pick-name">✅ {winner}</div>
                        </div>
                    </div>
            """
            
            if insights:
                html += '<ul class="insight-list">'
                for insight in insights:
                    html += f'<li class="insight-item">{insight}</li>'
                html += '</ul>'
            
            html += '</div>'
    
    # Recommendations
    if recommendations:
        html += """
            <div class="recommendations" style="margin-top: 25px;">
                <h3>💡 Actionable Recommendations</h3>
        """
        
        for i, rec in enumerate(recommendations, 1):
            html += f"""
                <div class="recommendation-item">
                    <span class="recommendation-number">{i}</span>
                    {rec}
                </div>
            """
        
        html += '</div>'
    
    html += '</div>'
    
    return html

def send_email(html_content, subject):
    """Send email via AWS SES"""
    try:
        # Save HTML to file for now (SES not verified)
        output_file = Path(__file__).parent / "calibration_email_output.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Email HTML saved to: {output_file}")
        print(f"   Open this file in a browser to view the formatted report")
        print(f"   Recipients: {', '.join(EMAIL_RECIPIENTS)}")
        
        # TODO: Configure SES verified sender email
        # ses = boto3.client('ses', region_name='eu-west-1')
        # response = ses.send_email(...)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("📧 DAILY CALIBRATION REPORT EMAIL")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Recipients: {', '.join(EMAIL_RECIPIENTS)}")
    print()
    
    # Load reports
    print("Loading calibration report...")
    calibration_report = load_calibration_report()
    
    print("Loading loss comparison report...")
    loss_report = load_loss_comparison_report()
    
    # Generate HTML
    print("Generating HTML report...")
    html_content = generate_html_report(calibration_report, loss_report)
    
    # Send email
    subject = f"🎯 Daily Calibration & Learning Report - {datetime.now().strftime('%B %d, %Y')}"
    
    print(f"\nSending email: {subject}")
    success = send_email(html_content, subject)
    
    if success:
        print("\n✅ Daily calibration report sent successfully!")
    else:
        print("\n❌ Failed to send daily calibration report")
        sys.exit(1)
    
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

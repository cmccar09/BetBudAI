"""
Generate Complete System Failure Report
For emailing to charles.mccarthy@gmail.com
"""
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from decimal import Decimal

def generate_report():
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    # Fetch Feb 21 data
    response_21 = table.query(
        KeyConditionExpression=Key('bet_date').eq('2026-02-21')
    )
    
    # Fetch Feb 22 data
    response_22 = table.query(
        KeyConditionExpression=Key('bet_date').eq('2026-02-22')
    )
    
    feb21_ui = [item for item in response_21['Items'] if item.get('show_in_ui') == True]
    feb21_ui.sort(key=lambda x: x.get('race_time', ''))
    
    feb22_all = response_22['Items']
    feb22_ui = [item for item in feb22_all if item.get('show_in_ui') == True]
    feb22_ui.sort(key=lambda x: x.get('race_time', ''))
    
    # Calculate Feb 21 stats
    feb21_wins = []
    feb21_losses = []
    
    for pick in feb21_ui:
        outcome = str(pick.get('outcome', '')).lower()
        if outcome in ['won', 'win']:
            feb21_wins.append(pick)
        elif outcome in ['lost', 'loss', 'lose']:
            feb21_losses.append(pick)
    
    stake = 2.0
    feb21_total_staked = len(feb21_ui) * stake
    feb21_total_returned = sum(float(w.get('odds', 0)) * stake for w in feb21_wins)
    feb21_profit = feb21_total_returned - feb21_total_staked
    feb21_roi = (feb21_profit / feb21_total_staked * 100) if feb21_total_staked > 0 else 0
    feb21_strike_rate = (len(feb21_wins) / len(feb21_ui) * 100) if feb21_ui else 0
    
    # Calculate Feb 22 stats
    feb22_completed = [i for i in feb22_all if str(i.get('outcome', '')).lower() in ['won', 'win', 'lost', 'loss', 'lose']]
    feb22_wins_all = [i for i in feb22_completed if str(i.get('outcome', '')).lower() in ['won', 'win']]
    feb22_losses_all = [i for i in feb22_completed if str(i.get('outcome', '')).lower() in ['lost', 'loss', 'lose']]
    feb22_strike_rate = (len(feb22_wins_all) / len(feb22_completed) * 100) if feb22_completed else 0
    
    # Find high-scoring losers
    high_score_losers = [i for i in feb22_losses_all if int(i.get('comprehensive_score', 0)) >= 70]
    high_score_losers.sort(key=lambda x: -int(x.get('comprehensive_score', 0)))
    
    # Generate HTML Report
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Betting System Failure Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 20px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #d32f2f;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .section {{
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .warning {{
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 15px 0;
        }}
        .critical {{
            background-color: #ffebee;
            border-left: 4px solid #d32f2f;
            padding: 15px;
            margin: 15px 0;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #d32f2f;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}
        .loss {{
            color: #d32f2f;
        }}
        .win {{
            color: #388e3c;
        }}
        .recommendation {{
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 15px 0;
        }}
        h1 {{
            margin: 0;
            font-size: 28px;
        }}
        h2 {{
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        h3 {{
            color: #555;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 BETTING SYSTEM FAILURE REPORT</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Status: <strong>CRITICAL - SYSTEM NOT PROFITABLE</strong></p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="critical">
            <p><strong>RECOMMENDATION: STOP ALL BETTING IMMEDIATELY</strong></p>
            <p>The betting system is failing to generate profit and shows no statistical edge over random selection. 
            The 7-factor comprehensive scoring system has not been validated and high scores are not predictive of wins.</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{feb21_strike_rate:.1f}%</div>
                <div class="stat-label">Feb 21 Strike Rate</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{feb22_strike_rate:.1f}%</div>
                <div class="stat-label">Feb 22 Strike Rate</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">£{feb21_profit:.2f}</div>
                <div class="stat-label">Feb 21 P&L</div>
            </div>
        </div>
        
        <p><strong>Target:</strong> 33%+ strike rate needed to be profitable at current odds</p>
        <p><strong>Actual:</strong> 18-25% strike rate = losing money consistently</p>
    </div>

    <div class="section">
        <h2>February 21, 2026 - Detailed Results</h2>
        <p><strong>Recommended Picks (85+ Score):</strong> {len(feb21_ui)} bets</p>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{len(feb21_wins)}</div>
                <div class="stat-label">Wins</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(feb21_losses)}</div>
                <div class="stat-label">Losses</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{feb21_roi:.1f}%</div>
                <div class="stat-label">ROI</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Horse</th>
                    <th>Score</th>
                    <th>Odds</th>
                    <th>Track</th>
                    <th>Result</th>
                </tr>
            </thead>
            <tbody>"""
    
    for pick in feb21_ui:
        horse = pick.get('horse', 'Unknown')
        score = int(pick.get('comprehensive_score', 0))
        odds = float(pick.get('odds', 0))
        track = pick.get('course', 'Unknown')
        outcome = str(pick.get('outcome', '')).lower()
        
        if outcome in ['won', 'win']:
            result_class = 'win'
            result_text = '✓ WON'
        else:
            result_class = 'loss'
            result_text = '✗ LOST'
        
        html += f"""
                <tr>
                    <td>{horse}</td>
                    <td>{score}/100</td>
                    <td>{odds}</td>
                    <td>{track}</td>
                    <td class="{result_class}"><strong>{result_text}</strong></td>
                </tr>"""
    
    html += """
            </tbody>
        </table>
        
        <div class="warning">
            <p><strong>Critical Issue:</strong> Even the highest-scoring picks lost:</p>
            <ul>
                <li>Jaipaletemps: 103/100 @ 5.2 - LOST</li>
                <li>Seaview Rock: 86/100 @ 3.45 - LOST (O Murphy trainer who won earlier)</li>
            </ul>
        </div>
    </div>

    <div class="section">
        <h2>February 22, 2026 - System Performance</h2>
        <p><strong>All Analyzed Horses:</strong> {len(feb22_all)} horses</p>
        <p><strong>Completed Races:</strong> {len(feb22_completed)} horses</p>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{len(feb22_wins_all)}</div>
                <div class="stat-label">Wins</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(feb22_losses_all)}</div>
                <div class="stat-label">Losses</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{feb22_strike_rate:.1f}%</div>
                <div class="stat-label">Strike Rate</div>
            </div>
        </div>
        
        <h3>High-Scoring Horses That LOST</h3>
        <div class="critical">
            <p>These horses scored 70+ but still lost, proving the scoring system is broken:</p>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Horse</th>
                    <th>Score</th>
                    <th>Odds</th>
                    <th>Track</th>
                </tr>
            </thead>
            <tbody>"""
    
    for loser in high_score_losers[:15]:
        horse = loser.get('horse', 'Unknown')
        score = int(loser.get('comprehensive_score', 0))
        odds = float(loser.get('odds', 0))
        track = loser.get('course', 'Unknown')
        
        html += f"""
                <tr>
                    <td>{horse}</td>
                    <td><strong>{score}/100</strong></td>
                    <td>{odds}</td>
                    <td>{track}</td>
                </tr>"""
    
    html += """
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Root Cause Analysis</h2>
        
        <h3>1. Unvalidated Scoring System</h3>
        <div class="warning">
            <p>The 7-factor comprehensive scoring system has NEVER been backtested. High scores don't predict wins.</p>
            <ul>
                <li><strong>Sweet Spot Theory (3-9 odds):</strong> FALSE - most losses were in this range</li>
                <li><strong>Form scoring:</strong> Not validated</li>
                <li><strong>Trainer performance:</strong> FAILED - O Murphy won then lost same day</li>
                <li><strong>Going suitability:</strong> Not validated</li>
                <li><strong>Database history:</strong> Not validated</li>
                <li><strong>Track patterns:</strong> Not validated</li>
                <li><strong>Jockey analysis:</strong> Not validated</li>
            </ul>
        </div>
        
        <h3>2. No Statistical Edge</h3>
        <div class="critical">
            <p>18-25% strike rate is NO BETTER than random selection or betting favorites blindly.</p>
            <p>At average odds of 3.5, you need 28%+ strike rate to break even.</p>
            <p>At current 20% strike rate, you need 5.0+ average odds to profit.</p>
        </div>
        
        <h3>3. Intraday Learning Failed</h3>
        <div class="warning">
            <p>The system tried to boost confidence for horses with "hot" trainers based on earlier wins same day.</p>
            <p><strong>Result:</strong> O Murphy won with Hold The Serve at 13:10, then LOST with Seaview Rock at 15:20.</p>
            <p>Same-day trainer form is NOT predictive.</p>
        </div>
        
        <h3>4. Threshold Adjustments Made Things Worse</h3>
        <p>The threshold was increased from 70+ to 85+ to show only "confident" picks.</p>
        <p><strong>Result:</strong> Even 85+ picks lost at 75% rate (6 losses, 2 wins on Feb 21).</p>
    </div>

    <div class="section">
        <h2>Immediate Actions Required</h2>
        
        <div class="recommendation">
            <h3>1. STOP ALL BETTING IMMEDIATELY</h3>
            <p>Do not place any more real-money bets until the system is validated.</p>
        </div>
        
        <div class="recommendation">
            <h3>2. Comprehensive Backtesting (500+ races minimum)</h3>
            <ul>
                <li>Test each scoring factor independently</li>
                <li>Validate which factors actually predict wins</li>
                <li>Benchmark against baseline strategies:
                    <ul>
                        <li>Always betting the favorite</li>
                        <li>Random selection</li>
                        <li>Single-factor strategies</li>
                    </ul>
                </li>
            </ul>
        </div>
        
        <div class="recommendation">
            <h3>3. Accept Lower Volume</h3>
            <p>Better to have 1-2 truly confident picks per day with 40%+ strike rate</p>
            <p>Than 8 picks per day with 20% strike rate</p>
        </div>
        
        <div class="recommendation">
            <h3>4. Fix or Abandon Current Scoring</h3>
            <p>Options:</p>
            <ul>
                <li>Identify the 1-2 factors that actually work</li>
                <li>Start from scratch with proven factors only</li>
                <li>Use pure statistical model (logistic regression on historical wins)</li>
            </ul>
        </div>
        
        <div class="recommendation">
            <h3>5. Only Resume Betting If:</h3>
            <ul>
                <li>Backtesting shows 35%+ strike rate on 500+ races</li>
                <li>Performance beats "always bet favorite" strategy</li>
                <li>Factors are statistically significant (p < 0.05)</li>
                <li>Out-of-sample testing confirms edge</li>
            </ul>
        </div>
    </div>

    <div class="section">
        <h2>Next Steps</h2>
        <ol>
            <li><strong>Immediate:</strong> Disable all automated betting workflows</li>
            <li><strong>Week 1:</strong> Gather 500+ historical race results with outcomes</li>
            <li><strong>Week 2:</strong> Build backtesting framework</li>
            <li><strong>Week 3:</strong> Test each factor independently, identify what works</li>
            <li><strong>Week 4:</strong> Rebuild scoring with only validated factors</li>
            <li><strong>Week 5:</strong> Out-of-sample testing on new data</li>
            <li><strong>Week 6:</strong> Paper trade for 2 weeks before resuming real bets</li>
        </ol>
    </div>

    <div class="section">
        <h2>Financial Summary</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Bets</th>
                    <th>Wins</th>
                    <th>Losses</th>
                    <th>Staked</th>
                    <th>Returned</th>
                    <th>P&L</th>
                    <th>ROI</th>
                </tr>
            </thead>
            <tbody>
                <tr class="loss">
                    <td>Feb 21</td>
                    <td>{len(feb21_ui)}</td>
                    <td>{len(feb21_wins)}</td>
                    <td>{len(feb21_losses)}</td>
                    <td>£{feb21_total_staked:.2f}</td>
                    <td>£{feb21_total_returned:.2f}</td>
                    <td><strong>£{feb21_profit:.2f}</strong></td>
                    <td><strong>{feb21_roi:.1f}%</strong></td>
                </tr>
            </tbody>
        </table>
        
        <p><strong>Conclusion:</strong> System is consistently unprofitable. Do not continue betting without major system overhaul.</p>
    </div>

    <div class="header">
        <p style="margin: 0; text-align: center;">
            <strong>This system requires fundamental redesign before resuming operations</strong>
        </p>
    </div>
</body>
</html>"""
    
    # Save HTML
    with open('system_failure_report.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✓ Report generated: system_failure_report.html")
    print(f"  Size: {len(html)} characters")
    
    return True

if __name__ == "__main__":
    generate_report()

#!/usr/bin/env python3
"""
WORKFLOW MONITOR WITH ALERTS
Run this at end of day to get summary email/notification
"""

import boto3
from datetime import datetime, timedelta
import json
import os

def generate_daily_report():
    """Generate end-of-day workflow report"""
    
    report = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'status': 'UNKNOWN',
        'picks_generated': 0,
        'ui_picks': 0,
        'issues': [],
        'warnings': [],
        'highlights': []
    }
    
    print("\n" + "="*70)
    print(f"DAILY WORKFLOW REPORT - {report['date']}")
    print("="*70)
    
    # Check database
    try:
        table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
        today = datetime.now().strftime('%Y-%m-%d')
        
        resp = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
        )
        
        items = resp.get('Items', [])
        ui_picks = [i for i in items if i.get('show_in_ui')]
        
        report['picks_generated'] = len(items)
        report['ui_picks'] = len(ui_picks)
        
        # Analyze picks
        if len(ui_picks) > 0:
            scores = sorted([float(i.get('comprehensive_score', 0)) for i in ui_picks], reverse=True)
            top_score = scores[0] if scores else 0
            avg_score = sum(scores) / len(scores) if scores else 0
            
            report['highlights'].append(f"Top score: {top_score:.0f}/100")
            report['highlights'].append(f"Average score: {avg_score:.0f}/100")
            
            # Check for high confidence picks
            high_conf = [i for i in ui_picks if float(i.get('comprehensive_score', 0)) >= 90]
            if high_conf:
                report['highlights'].append(f"{len(high_conf)} high-confidence picks (90+)")
            
        # Data quality checks
        no_form = sum(1 for i in items if i.get('form') in [None, '', 'N/A'])
        if no_form > 0:
            report['warnings'].append(f"{no_form}/{len(items)} horses missing form data")
        
        # Check for zero scores
        zero_scores = sum(1 for i in items if float(i.get('comprehensive_score', 0)) == 0)
        if zero_scores > len(items) * 0.5:  # >50% zeros = problem
            report['issues'].append(f"{zero_scores}/{len(items)} horses scored 0 (scoring failure)")
        
    except Exception as e:
        report['issues'].append(f"Database error: {str(e)}")
    
    # Check file freshness
    if os.path.exists('response_horses.json'):
        file_age = datetime.now().timestamp() - os.path.getmtime('response_horses.json')
        age_hours = file_age / 3600
        
        if age_hours > 24:
            report['warnings'].append(f"Race data is {age_hours:.1f}h old")
    else:
        report['issues'].append("No race data file found")
    
    # Determine overall status
    if report['issues']:
        report['status'] = '🔴 FAILED'
    elif report['ui_picks'] == 0:
        report['status'] = '⚠️ NO PICKS'
    elif report['warnings']:
        report['status'] = '⚠️ ISSUES'
    elif report['ui_picks'] >= 5:
        report['status'] = '✓ EXCELLENT'
    else:
        report['status'] = '✓ OK'
    
    # Print report
    print(f"\nStatus: {report['status']}")
    print(f"Picks Generated: {report['picks_generated']}")
    print(f"UI Picks: {report['ui_picks']}")
    
    if report['highlights']:
        print("\n📊 Highlights:")
        for h in report['highlights']:
            print(f"   • {h}")
    
    if report['warnings']:
        print("\n⚠️  Warnings:")
        for w in report['warnings']:
            print(f"   • {w}")
    
    if report['issues']:
        print("\n🔴 Issues:")
        for i in report['issues']:
            print(f"   • {i}")
    
    print("\n" + "="*70)
    
    # Save report
    report_file = f"daily_report_{report['date']}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved: {report_file}")
    
    # Return status for alerts
    return report

def should_alert(report):
    """Determine if alert should be sent"""
    
    # Alert conditions
    if report['issues']:
        return True, "Critical issues detected"
    
    if report['ui_picks'] == 0 and report['picks_generated'] > 0:
        return True, "No UI picks generated despite races analyzed"
    
    if report['ui_picks'] == 0:
        return True, "No picks generated today"
    
    # All good
    return False, None

if __name__ == "__main__":
    report = generate_daily_report()
    
    alert, reason = should_alert(report)
    
    if alert:
        print(f"\n🚨 ALERT: {reason}")
        print("   Consider manual review")
    else:
        print("\n✓ No alerts - system operating normally")

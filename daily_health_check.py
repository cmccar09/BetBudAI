#!/usr/bin/env python3
"""
DAILY HEALTH CHECK
Runs automated checks to prevent workflow failures
Alerts if anything is broken

Run this BEFORE the main workflow to catch issues early
"""

import boto3
from datetime import datetime
import json
import os

def health_check():
    """Comprehensive health check"""
    
    issues = []
    warnings = []
    
    print("\n" + "="*70)
    print("DAILY HEALTH CHECK")
    print("="*70)
    
    # 1. Check if response_horses.json exists and is recent
    print("\n1. Checking race data file...")
    if os.path.exists('response_horses.json'):
        file_age = datetime.now().timestamp() - os.path.getmtime('response_horses.json')
        age_hours = file_age / 3600
        
        if age_hours < 24:
            print(f"   ✓ response_horses.json exists ({age_hours:.1f}h old)")
            
            # Check if it has form data
            with open('response_horses.json', 'r') as f:
                data = json.load(f)
                races = data.get('races', [])
                
                if races:
                    sample_race = races[0]
                    sample_runner = sample_race.get('runners', [{}])[0]
                    has_form = sample_runner.get('form') not in [None, '', 'N/A']
                    
                    if has_form:
                        print(f"   ✓ Form data present in race data")
                    else:
                        issues.append("CRITICAL: No form data in response_horses.json")
                        print(f"   ✗ No form data found!")
                else:
                    warnings.append("response_horses.json has no races")
        else:
            warnings.append(f"response_horses.json is old ({age_hours:.1f}h)")
    else:
        issues.append("CRITICAL: response_horses.json not found")
        print("   ✗ File not found")
    
    # 2. Check database for today's picks
    print("\n2. Checking database picks...")
    try:
        table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
        today = datetime.now().strftime('%Y-%m-%d')
        
        resp = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
        )
        
        items = resp.get('Items', [])
        ui_picks = [i for i in items if i.get('show_in_ui')]
        
        print(f"   Total horses: {len(items)}")
        print(f"   UI picks: {len(ui_picks)}")
        
        if len(items) > 0 and len(ui_picks) == 0:
            issues.append("CRITICAL: Horses analyzed but 0 UI picks (all scored too low)")
        
        # Check for form data in database
        no_form_count = sum(1 for i in items if i.get('form') in [None, '', 'N/A'])
        if no_form_count > 0:
            issues.append(f"CRITICAL: {no_form_count}/{len(items)} horses have no form data")
            print(f"   ✗ {no_form_count} horses without form data")
        else:
            print(f"   ✓ All horses have form data")
        
        # Check score fields
        score_mismatches = 0
        coverage_mismatches = 0
        for item in ui_picks:
            comp_score = item.get('comprehensive_score')
            comb_conf = item.get('combined_confidence')
            
            if comp_score and (not comb_conf or float(comb_conf) == 0):
                score_mismatches += 1
            
            # Check coverage field consistency (prevent UI showing 0%)
            coverage = item.get('coverage')
            data_coverage = item.get('data_coverage')
            race_coverage = item.get('race_coverage_pct')
            
            # All three should have the same value
            if coverage and (not data_coverage or not race_coverage):
                coverage_mismatches += 1
        
        if score_mismatches > 0:
            warnings.append(f"{score_mismatches} picks have score mismatches")
            print(f"   ⚠ {score_mismatches} score field mismatches")
        else:
            print(f"   ✓ All scores synchronized")
        
        if coverage_mismatches > 0:
            warnings.append(f"{coverage_mismatches} picks have coverage field mismatches")
            print(f"   ⚠ {coverage_mismatches} coverage field mismatches (UI may show 0%)")
        else:
            print(f"   ✓ All coverage fields synchronized")
            
    except Exception as e:
        issues.append(f"Database error: {str(e)}")
        print(f"   ✗ Error: {e}")
    
    # 3. Check scheduled task
    print("\n3. Checking scheduled task...")
    import subprocess
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-ScheduledTask -TaskName "RacingPostScraper" | Select-Object State'],
            capture_output=True,
            text=True
        )
        
        if 'Ready' in result.stdout:
            print("   ✓ Scheduled task is active")
        else:
            warnings.append("Scheduled task may not be ready")
            
    except Exception as e:
        warnings.append(f"Could not check scheduled task: {e}")
    
    # 4. Check comprehensive_workflow.py exists
    print("\n4. Checking workflow files...")
    required_files = [
        'comprehensive_workflow.py',
        'comprehensive_pick_logic.py',
        'betfair_odds_fetcher.py',
        'fetch_hourly_results.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✓ {file}")
        else:
            issues.append(f"CRITICAL: Missing {file}")
            print(f"   ✗ {file} not found")
    
    # 5. Check results are being captured (learning workflow health)
    print("\n5. Checking learning workflow...")
    try:
        # Check if results are being captured
        from datetime import timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        resp = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(yesterday)
        )
        yesterday_picks = resp.get('Items', [])
        
        if yesterday_picks:
            with_results = [p for p in yesterday_picks if p.get('outcome') not in [None, 'pending']]
            results_pct = (len(with_results) / len(yesterday_picks) * 100) if yesterday_picks else 0
            
            print(f"   Yesterday: {len(with_results)}/{len(yesterday_picks)} picks have results ({results_pct:.0f}%)")
            
            if results_pct < 50 and len(yesterday_picks) > 3:
                warnings.append(f"Only {results_pct:.0f}% of yesterday's picks have results - learning may be slow")
            elif results_pct >= 80:
                print(f"   ✓ Results capture working well")
            
            # Check if learning happened recently
            if os.path.exists('learning_summary.py'):
                learning_mod_time = os.path.getmtime('learning_summary.py')
                hours_since_learning = (datetime.now().timestamp() - learning_mod_time) / 3600
                
                if hours_since_learning < 24:
                    print(f"   ✓ Learning ran recently ({hours_since_learning:.1f}h ago)")
                else:
                    warnings.append(f"Learning hasn't run in {hours_since_learning:.1f}h")
        else:
            print(f"   No picks from yesterday to check")
            
    except Exception as e:
        warnings.append(f"Could not check learning workflow: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if issues:
        print(f"\n🔴 CRITICAL ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"   ✗ {issue}")
        print("\n⚠️  WORKFLOW WILL LIKELY FAIL - FIX THESE FIRST!")
        return False
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   ⚠ {warning}")
    
    if not issues and not warnings:
        print("\n✓ ALL CHECKS PASSED - System ready!")
        return True
    
    if not issues:
        print("\n✓ No critical issues - System should work")
        return True
    
    return False

if __name__ == "__main__":
    success = health_check()
    exit(0 if success else 1)

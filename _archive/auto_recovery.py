#!/usr/bin/env python3
"""
AUTO-RECOVERY SYSTEM
Attempts to fix common workflow failures automatically

Run this if daily_health_check.py reports issues
"""

import os
import subprocess
import json
from datetime import datetime
import boto3

def attempt_recovery():
    """Try to fix common issues"""
    
    print("\n" + "="*70)
    print("AUTO-RECOVERY SYSTEM")
    print("="*70)
    
    fixed = []
    failed = []
    
    # 1. Check if response_horses.json is missing or old
    print("\n1. Checking race data...")
    if not os.path.exists('response_horses.json') or is_file_old('response_horses.json', hours=6):
        print("   Fetching fresh race data...")
        try:
            result = subprocess.run(['python', 'betfair_odds_fetcher.py'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                fixed.append("Fetched fresh race data from Betfair")
                print("   ✓ Fresh data fetched")
            else:
                failed.append("Could not fetch Betfair data")
                print(f"   ✗ Failed: {result.stderr[:100]}")
        except Exception as e:
            failed.append(f"Betfair fetch error: {e}")
            print(f"   ✗ Error: {e}")
    else:
        print("   ✓ Race data is current")
    
    # 2. Fix score mismatches in database
    print("\n2. Fixing score mismatches...")
    try:
        table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
        today = datetime.now().strftime('%Y-%m-%d')
        
        resp = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
        )
        
        items = resp.get('Items', [])
        ui_picks = [i for i in items if i.get('show_in_ui')]
        
        score_fixed = 0
        coverage_fixed = 0
        
        for item in ui_picks:
            update_expr = []
            update_vals = {}
            
            # Fix score mismatch
            comp_score = item.get('comprehensive_score')
            comb_conf = item.get('combined_confidence', 0)
            
            if comp_score and (not comb_conf or float(comb_conf) == 0):
                update_expr.append('combined_confidence = :score')
                update_vals[':score'] = comp_score
                score_fixed += 1
            
            # Fix coverage field mismatches (prevent UI showing 0%)
            coverage = item.get('coverage')
            data_coverage = item.get('data_coverage')
            race_coverage = item.get('race_coverage_pct')
            
            if coverage and (not data_coverage or not race_coverage):
                if not data_coverage:
                    update_expr.append('data_coverage = :cov')
                if not race_coverage:
                    update_expr.append('race_coverage_pct = :cov')
                update_vals[':cov'] = coverage
                coverage_fixed += 1
            
            # Apply updates if needed
            if update_expr:
                table.update_item(
                    Key={'bet_date': item['bet_date'], 'bet_id': item['bet_id']},
                    UpdateExpression='SET ' + ', '.join(update_expr),
                    ExpressionAttributeValues=update_vals
                )
        
        if score_fixed > 0:
            fixed.append(f"Synchronized {score_fixed} score mismatches")
            print(f"   ✓ Fixed {score_fixed} score mismatches")
        
        if coverage_fixed > 0:
            fixed.append(f"Synchronized {coverage_fixed} coverage field mismatches")
            print(f"   ✓ Fixed {coverage_fixed} coverage mismatches")
        
        if score_fixed == 0 and coverage_fixed == 0:
            print("   ✓ No field mismatches found")
            
    except Exception as e:
        failed.append(f"Score sync error: {e}")
        print(f"   ✗ Error: {e}")
    
    # 3. Clear old data if needed
    print("\n3. Checking for stale data...")
    try:
        # Remove picks older than 2 days
        old_dates = [(datetime.now().date() - timedelta(days=i)).strftime('%Y-%m-%d') 
                     for i in range(2, 30)]
        
        deleted = 0
        for old_date in old_dates[:5]:  # Only check last 5 days beyond 2 days ago
            resp = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(old_date)
            )
            items = resp.get('Items', [])
            
            for item in items:
                if not item.get('outcome'):  # Only delete if no result recorded
                    table.delete_item(
                        Key={'bet_date': item['bet_date'], 'bet_id': item['bet_id']}
                    )
                    deleted += 1
        
        if deleted > 0:
            fixed.append(f"Cleaned {deleted} old unresolved picks")
            print(f"   ✓ Removed {deleted} old items")
        else:
            print("   ✓ No stale data to clean")
            
    except Exception as e:
        # Non-critical, just log
        print(f"   ⚠ Could not clean old data: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("RECOVERY SUMMARY")
    print("="*70)
    
    if fixed:
        print(f"\n✓ FIXED ({len(fixed)}):")
        for fix in fixed:
            print(f"   ✓ {fix}")
    
    if failed:
        print(f"\n✗ FAILED ({len(failed)}):")
        for fail in failed:
            print(f"   ✗ {fail}")
    
    if not failed:
        print("\n✓ All recovery actions succeeded!")
        print("  Run comprehensive_workflow.py now")
        return True
    else:
        print("\n⚠️  Some issues remain - manual intervention needed")
        return False

def is_file_old(filepath, hours=6):
    """Check if file is older than specified hours"""
    if not os.path.exists(filepath):
        return True
    file_age = datetime.now().timestamp() - os.path.getmtime(filepath)
    return (file_age / 3600) > hours

if __name__ == "__main__":
    from datetime import timedelta
    success = attempt_recovery()
    exit(0 if success else 1)

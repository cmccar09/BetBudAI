"""
Data Quality Monitor
Check for missing runners and data completeness issues
"""
import json
import boto3
from datetime import datetime
from decimal import Decimal

def check_data_quality():
    """
    Check for data quality issues:
    1. Missing runners (expected vs captured)
    2. Winner not in our data
    3. Odds anomalies
    """
    
    issues = []
    
    print("\n" + "="*80)
    print("DATA QUALITY CHECK")
    print("="*80 + "\n")
    
    try:
        # Load race data
        with open('response_horses.json', 'r') as f:
            data = json.load(f)
        
        races = data.get('races', [])
        total_races = len(races)
        
        print(f"Checking {total_races} races for data quality issues...\n")
        
        # Check each race
        for race in races:
            venue = race.get('venue', 'Unknown')
            start_time = race.get('start_time', 'Unknown')
            market_name = race.get('market_name', 'Unknown')
            runners = race.get('runners', [])
            runner_count = len(runners)
            
            race_key = f"{venue} {start_time[:16]}"
            
            # Issue 1: Very few runners (possible incomplete data)
            if runner_count < 4 and 'chase' not in market_name.lower():
                issues.append({
                    'type': 'LOW_RUNNER_COUNT',
                    'race': race_key,
                    'market': market_name,
                    'runners': runner_count,
                    'severity': 'WARNING',
                    'message': f'Only {runner_count} runners captured (suspicious for {market_name})'
                })
            
            # Issue 2: Missing status field (API data quality)
            missing_status = sum(1 for r in runners if r.get('status') is None)
            if missing_status == runner_count:
                issues.append({
                    'type': 'MISSING_STATUS_FIELD',
                    'race': race_key,
                    'market': market_name,
                    'runners': runner_count,
                    'severity': 'INFO',
                    'message': 'All runners missing status field (API limitation)'
                })
            
            # Issue 3: Odds anomalies (all horses very high odds = incomplete market)
            avg_odds = sum(r.get('odds', 0) for r in runners) / max(runner_count, 1)
            if avg_odds > 50 and runner_count > 5:
                issues.append({
                    'type': 'HIGH_AVERAGE_ODDS',
                    'race': race_key,
                    'market': market_name,
                    'avg_odds': avg_odds,
                    'severity': 'WARNING',
                    'message': f'Average odds {avg_odds:.1f} suspiciously high (incomplete market?)'
                })
            
            # Issue 4: Missing form data
            no_form = sum(1 for r in runners if not r.get('form'))
            if no_form > runner_count * 0.5:
                issues.append({
                    'type': 'MISSING_FORM_DATA',
                    'race': race_key,
                    'market': market_name,
                    'affected': no_form,
                    'total': runner_count,
                    'severity': 'INFO',
                    'message': f'{no_form}/{runner_count} horses missing form data'
                })
        
        # Report issues
        if issues:
            print(f"Found {len(issues)} data quality issues:\n")
            
            # Group by severity
            critical = [i for i in issues if i['severity'] == 'CRITICAL']
            warnings = [i for i in issues if i['severity'] == 'WARNING']
            info = [i for i in issues if i['severity'] == 'INFO']
            
            if critical:
                print(f"🔴 CRITICAL ISSUES ({len(critical)}):")
                for issue in critical:
                    print(f"   {issue['race']}: {issue['message']}")
                print()
            
            if warnings:
                print(f"⚠️  WARNINGS ({len(warnings)}):")
                for issue in warnings:
                    print(f"   {issue['race']}: {issue['message']}")
                print()
            
            if info:
                print(f"ℹ️  INFO ({len(info)}):")
                for issue in info[:5]:  # Show first 5
                    print(f"   {issue['race']}: {issue['message']}")
                if len(info) > 5:
                    print(f"   ... and {len(info)-5} more")
                print()
            
            # Save to file
            timestamp = datetime.now().isoformat()
            quality_report = {
                'timestamp': timestamp,
                'total_races': total_races,
                'issues_found': len(issues),
                'issues': issues
            }
            
            try:
                with open('data_quality_issues.json', 'w') as f:
                    json.dump(quality_report, f, indent=2, default=str)
                print(f"✓ Saved report to data_quality_issues.json")
            except Exception as e:
                print(f"❌ Error saving report: {e}")
        
        else:
            print("✓ No data quality issues detected")
        
        return issues
        
    except FileNotFoundError:
        print("❌ response_horses.json not found - cannot check data quality")
        return []
    except Exception as e:
        print(f"❌ Error during quality check: {e}")
        import traceback
        traceback.print_exc()
        return []


def check_winner_coverage(race_results):
    """
    Check if winners are in our captured data
    
    Args:
        race_results: List of results from betfair_results_fetcher
    """
    print("\n" + "="*80)
    print("WINNER COVERAGE CHECK")
    print("="*80 + "\n")
    
    try:
        with open('response_horses.json', 'r') as f:
            data = json.load(f)
        
        races = data.get('races', [])
        coverage_issues = []
        
        for result in race_results:
            winner_name = result.get('winner')
            venue = result.get('venue')
            race_time = result.get('race_time')
            
            if not winner_name:
                continue
            
            # Find matching race in our data
            matching_race = None
            for race in races:
                if venue in race.get('venue', '') and race_time[:10] in race.get('start_time', ''):
                    matching_race = race
                    break
            
            if matching_race:
                runners = matching_race.get('runners', [])
                winner_found = any(winner_name.lower() in r.get('name', '').lower() for r in runners)
                
                if not winner_found:
                    coverage_issues.append({
                        'race': f"{venue} {race_time}",
                        'winner': winner_name,
                        'runners_captured': len(runners),
                        'message': f'Winner "{winner_name}" not in captured data'
                    })
        
        if coverage_issues:
            print(f"🔴 WINNER COVERAGE ISSUES ({len(coverage_issues)}):\n")
            for issue in coverage_issues:
                print(f"   {issue['race']}")
                print(f"      Winner: {issue['winner']}")
                print(f"      We had: {issue['runners_captured']} runners")
                print(f"      ⚠️  {issue['message']}\n")
            
            return coverage_issues
        else:
            print("✓ All winners found in captured data")
            return []
            
    except Exception as e:
        print(f"❌ Error checking winner coverage: {e}")
        return []


if __name__ == "__main__":
    print("\n" + "="*80)
    print("RUNNING DATA QUALITY CHECKS")
    print("="*80)
    
    # Check general data quality
    issues = check_data_quality()
    
    print(f"\n{'='*80}")
    print(f"SUMMARY: {len(issues)} issues found")
    print(f"{'='*80}\n")

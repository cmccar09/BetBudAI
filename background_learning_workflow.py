"""
WORKFLOW 1: Background Learning System
Runs 11am-7pm on 30min cycles
Analyzes ALL races, stores ALL horses, learns from winners

Confidence Scoring (4-tier system applied to all horses):
- EXCELLENT (75+): Green - 2.0x stake
- GOOD (60-74): Light amber - 1.5x stake
- FAIR (45-59): Dark amber - 1.0x stake
- POOR (<45): Red - 0.5x stake

CRITICAL COVERAGE RULES:
- ALL horses must be analyzed (target 100% coverage)
- Minimum 90% required - below this = race REJECTED
- Everything saved to database with show_in_ui=False
- Only fully analyzed races (>=90% coverage) can appear on UI
"""

import subprocess
import time
from datetime import datetime, timedelta
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')


def is_within_trading_hours():
    """Check if current time is between 11am and 7pm"""
    now = datetime.now()
    start_hour = 11
    end_hour = 19  # 7pm
    
    return start_hour <= now.hour < end_hour


def check_data_quality():
    """Check data quality before processing"""
    print("\n" + "="*80)
    print("DATA QUALITY CHECK")
    print("="*80)
    
    result = subprocess.run(
        ['python', 'data_quality_monitor.py'],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    # Show critical issues and warnings
    lines = result.stdout.split('\n')
    for line in lines:
        if '🔴' in line or '⚠️' in line or 'CRITICAL' in line or 'WARNING' in line:
            print(line)
    
    return True  # Continue even if issues found (for learning)


def store_all_races_for_learning():
    """Store ALL horses from ALL races - LEARNING data + 85+ UI picks"""
    print("\n" + "="*80)
    print("COMPREHENSIVE DAILY ANALYSIS - 7-Factor Scoring")
    print("="*80)
    
    # Use complete_daily_analysis.py for 100% coverage + strict 85+ threshold
    result = subprocess.run(
        ['python', 'complete_daily_analysis.py'],
        capture_output=True,
        text=True,
        timeout=600
    )
    
    # Show summary
    lines = result.stdout.split('\n')
    for line in lines:
        if 'Total picks:' in line or 'Background analysis:' in line or 'analyzed' in line.lower():
            print(line)
    
    return result.returncode == 0


def analyze_winners_and_learn():
    """Compare stored horses with actual winners via BettingPicksAPI Lambda"""
    print("\n" + "="*80)
    print("ANALYZING WINNERS - Learning Patterns (via Lambda)")
    print("="*80)

    import json
    lam = boto3.client('lambda', region_name='eu-west-1')
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        resp = lam.invoke(
            FunctionName='BettingPicksAPI',
            Payload=json.dumps({
                'rawPath': '/api/learning/apply',
                'requestContext': {'http': {'method': 'POST'}},
                'headers': {'content-type': 'application/json'},
                'body': json.dumps({'date': today}),
            })
        )
        body = json.loads(resp['Payload'].read())
        result_body = json.loads(body.get('body', '{}'))
        status = body.get('statusCode', 0)
        print(f"  Lambda status: {status}")
        print(f"  Result: {result_body}")
        return status == 200
    except Exception as e:
        print(f"  ⚠ Lambda call failed: {e}")
        return False


def fetch_latest_results():
    """Fetch results from API (today + yesterday for comparison)"""
    print("\n" + "="*80)
    print("FETCHING RESULTS FROM API")
    print("="*80)
    
    result = subprocess.run(
        ['python', 'fetch_api_results.py'],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    print(result.stdout)
    return result.returncode == 0


def auto_adjust_logic():
    """Auto-adjust scoring weights based on what's actually winning"""
    print("\n" + "="*80)
    print("AUTO-ADJUSTING SCORING LOGIC")
    print("="*80)
    
    result = subprocess.run(
        ['python', 'auto_adjust_weights.py'],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    print(result.stdout)
    return result.returncode == 0


def log_learning_cycle(cycle_num, stored_count, learned_count, adjusted):
    """Log this learning cycle to database"""
    today = datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.now().isoformat()
    
    record = {
        'bet_id': f'LEARNING_CYCLE_{timestamp.replace(":", "").replace("-", "").replace(".", "_")}',
        'bet_date': today,
        'learning_type': 'BACKGROUND_CYCLE',
        'cycle_number': cycle_num,
        'horses_stored': stored_count,
        'winners_analyzed': learned_count,
        'logic_adjusted': adjusted,
        'timestamp': timestamp,
        'show_in_ui': False,
        'is_learning_pick': True
    }
    
    table.put_item(Item=record)
    print(f"\n✓ Learning cycle #{cycle_num} logged to database")


def run_background_learning():
    """Main background learning loop - 11am to 7pm, every 30 minutes"""
    
    print("\n" + "="*80)
    print("BACKGROUND LEARNING SYSTEM STARTED")
    print("Trading Hours: 11:00 AM - 7:00 PM")
    print("Cycle Frequency: Every 30 minutes")
    print("Purpose: Learn from ALL races, improve logic")
    print("UI Visibility: NONE (all data stored in database only)")
    print("="*80)
    
    cycle_count = 0
    
    while True:
        if not is_within_trading_hours():
            now = datetime.now()
            if now.hour < 11:
                wait_until = now.replace(hour=11, minute=0, second=0, microsecond=0)
                wait_seconds = (wait_until - now).total_seconds()
                print(f"\n⏰ Before trading hours. Waiting until 11:00 AM ({wait_seconds//60:.0f} minutes)")
                time.sleep(min(wait_seconds, 1800))  # Sleep max 30 min at a time
                continue
            else:
                print(f"\n🌙 Trading hours ended (7:00 PM). Stopping for today.")
                break
        
        cycle_count += 1
        print(f"\n{'='*80}")
        print(f"LEARNING CYCLE #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        try:
            # Step 1: Fetch latest race data
            print("\n[1/6] Fetching latest race data...")
            subprocess.run(['python', 'betfair_odds_fetcher.py'], timeout=300)
            
            # Step 1.5: Check data quality
            check_data_quality()
            
            # Step 2: ANALYZE ALL horses from ALL races (100% coverage)
            print("\n[2/6] Analyzing ALL horses in ALL races...")
            stored = store_all_races_for_learning()
            
            # Step 2.5: Calculate confidence scores for all horses
            print("\n[2.5/6] Calculating confidence scores...")
            result_conf = subprocess.run(
                ['python', 'calculate_all_confidence_scores.py'],
                capture_output=True,
                text=True,
                timeout=300
            )
            conf_lines = result_conf.stdout.split('\n')
            for line in conf_lines:
                if 'Horses scored:' in line:
                    print(f"  {line}")
            
            # Step 3: Fetch results for completed races
            print("\n[3/6] Fetching results...")
            fetch_latest_results()
            
            # Step 4: Analyze winners - learn WHY they won
            print("\n[4/6] Analyzing winners and learning patterns...")
            learned = analyze_winners_and_learn()
            
            # Step 5: Auto-adjust scoring logic based on learnings
            print("\n[5/6] Auto-adjusting scoring weights...")
            adjusted = auto_adjust_logic()
            
            # Step 6: Log this cycle
            log_learning_cycle(cycle_count, 0, 0, adjusted)
            
            # Wait 30 minutes
            next_run = datetime.now() + timedelta(minutes=30)
            print(f"\n⏳ Learning cycle complete. Next run at {next_run.strftime('%H:%M:%S')}")
            print(f"   Sleeping for 30 minutes...")
            time.sleep(1800)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Learning system stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error in learning cycle: {str(e)}")
            import traceback
            traceback.print_exc()
            print("\n⏳ Waiting 5 minutes before retry...")
            time.sleep(300)
    
    print("\n" + "="*80)
    print("BACKGROUND LEARNING SYSTEM STOPPED")
    print(f"Total cycles completed: {cycle_count}")
    print("="*80)


if __name__ == "__main__":
    run_background_learning()

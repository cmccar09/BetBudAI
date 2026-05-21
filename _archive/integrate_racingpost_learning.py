"""
Racing Post Learning Integration
Runs after scraper to match results with Betfair picks and trigger learning
Schedule: Run this every hour from 1pm-9pm (after scraper runs)
"""

import subprocess
import sys
from datetime import datetime
import boto3
from decimal import Decimal

def match_racingpost_results():
    """Match Racing Post results with Betfair picks"""
    print("\n" + "="*80)
    print("MATCHING RACING POST RESULTS WITH BETFAIR PICKS")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        result = subprocess.run(
            ['python', 'match_racingpost_to_betfair.py'],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"⚠️ Matching had errors: {result.stderr}")
            return False
        
        # Parse output to see how many picks were updated
        lines = result.stdout.split('\n')
        for line in lines:
            if 'Updated' in line or 'picks matched' in line:
                print(f"✓ {line}")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("⚠️ Matching timed out after 3 minutes")
        return False
    except Exception as e:
        print(f"✗ Error during matching: {e}")
        return False


def trigger_learning():
    """Trigger learning from newly matched results"""
    print("\n" + "="*80)
    print("TRIGGERING LEARNING FROM MATCHED RESULTS")
    print("="*80)
    
    try:
        result = subprocess.run(
            ['python', 'auto_adjust_weights.py'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"⚠️ Learning had errors: {result.stderr}")
            return False
        
        print("✓ Learning completed")
        return True
        
    except subprocess.TimeoutExpired:
        print("⚠️ Learning timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"✗ Error during learning: {e}")
        return False


def check_racingpost_data():
    """Check if we have recent Racing Post data"""
    print("\n" + "="*80)
    print("CHECKING RACING POST DATA")
    print("="*80)
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('RacingPostRaces')
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Query today's races
        response = table.query(
            IndexName='DateIndex',
            KeyConditionExpression='raceDate = :date',
            ExpressionAttributeValues={':date': today}
        )
        
        races = response.get('Items', [])
        races_with_results = [r for r in races if r.get('hasResults', False)]
        
        print(f"Total races in RacingPost table today: {len(races)}")
        print(f"Races with results: {len(races_with_results)}")
        
        if len(races_with_results) > 0:
            print(f"✓ Racing Post scraper is working")
            return True
        else:
            print(f"⚠️ No results yet (scraper may not have run)")
            return False
        
    except Exception as e:
        print(f"✗ Error checking Racing Post data: {e}")
        return False


def main():
    """Main workflow: Check data -> Match results -> Learn"""
    print("\n" + "="*80)
    print("RACING POST LEARNING INTEGRATION")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check if we have Racing Post data
    has_data = check_racingpost_data()
    
    if not has_data:
        print("\n⚠️ No Racing Post data available yet - skipping for now")
        return
    
    # Step 2: Match Racing Post results with Betfair picks
    matched = match_racingpost_results()
    
    if not matched:
        print("\n⚠️ Matching failed - skipping learning")
        return
    
    # Step 3: Trigger learning from matched results
    learned = trigger_learning()
    
    if learned:
        print("\n" + "="*80)
        print("✓ RACING POST LEARNING COMPLETE")
        print("="*80)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("\n⚠️ Learning failed - check logs")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

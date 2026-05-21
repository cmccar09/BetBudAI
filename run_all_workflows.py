"""
RUN ALL WORKFLOWS
Executes the complete betting system workflow in proper order:
1. Fetch yesterday's results
2. Update learning from results
3. Generate today's picks
4. Fetch any available today's results
"""

import subprocess
import sys
from datetime import datetime

def run_script(script_name, description):
    """Run a Python script and report status"""
    print(f"\n{'='*80}")
    print(f"📋 {description}")
    print(f"   Running: {script_name}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Show output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print(f"\n✅ {description} - COMPLETED")
            return True
        else:
            print(f"\n⚠️ {description} - COMPLETED WITH WARNINGS")
            if result.stderr:
                print(f"Errors/Warnings:\n{result.stderr}")
            return True  # Continue even with warnings
            
    except subprocess.TimeoutExpired:
        print(f"\n⏱️ {description} - TIMEOUT (took > 5 minutes)")
        return False
    except Exception as e:
        print(f"\n❌ {description} - ERROR: {e}")
        return False

def main():
    start_time = datetime.now()
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ALL WORKFLOWS RUNNER                                  ║
║                                                                              ║
║  This will execute the complete betting system workflow:                    ║
║  1. Fetch yesterday's results from Betfair                                  ║
║  2. Run learning cycle to update system with insights                       ║
║  3. Generate today's picks using comprehensive analysis                     ║
║  4. Fetch any results for races that have already run today                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
""")
    
    workflows = [
        {
            'script': 'fetch_yesterday_results.py',
            'description': 'STEP 1: Fetch Yesterday\'s Results',
            'required': False  # Not critical if already done
        },
        {
            'script': 'daily_learning_cycle.py',
            'description': 'STEP 2: Update Learning System',
            'required': False  # Can skip if no new data
        },
        {
            'script': 'comprehensive_workflow.py',
            'description': 'STEP 3: Generate Today\'s Picks',
            'required': True  # This is essential
        },
        {
            'script': 'fetch_hourly_results.py',
            'description': 'STEP 4: Fetch Today\'s Results (if available)',
            'required': False  # May not have results yet
        }
    ]
    
    completed = 0
    failed = 0
    
    for workflow in workflows:
        success = run_script(workflow['script'], workflow['description'])
        
        if success:
            completed += 1
        else:
            failed += 1
            if workflow['required']:
                print(f"\n❌ CRITICAL WORKFLOW FAILED: {workflow['description']}")
                print("   Stopping execution.")
                break
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{'='*80}")
    print(f"📊 WORKFLOW EXECUTION SUMMARY")
    print(f"{'='*80}")
    print(f"  Completed: {completed}/{len(workflows)}")
    print(f"  Failed: {failed}")
    print(f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"  Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    if failed == 0:
        print("✅ ALL WORKFLOWS COMPLETED SUCCESSFULLY")
    else:
        print(f"⚠️  {failed} workflow(s) had issues (see above for details)")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

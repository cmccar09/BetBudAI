"""
MASTER BACKTESTING WORKFLOW
Runs complete backtesting suite in correct order
"""
import subprocess
import sys
from datetime import datetime

print("="*80)
print("COMPREHENSIVE BACKTESTING WORKFLOW")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print()

steps = [
    {
        'name': 'Extract Historical Data',
        'script': 'extract_historical_data.py',
        'description': 'Gather all completed races from database'
    },
    {
        'name': 'Test Individual Factors',
        'script': 'backtest_individual_factors.py',
        'description': 'Test each scoring factor independently'
    },
    {
        'name': 'Benchmark Baseline Strategies',
        'script': 'backtest_baseline_strategies.py',
        'description': 'Compare against simple strategies (favorite, random, etc.)'
    },
    {
        'name': 'Comprehensive Analysis',
        'script': 'backtest_comprehensive_analysis.py',
        'description': 'Final analysis and recommendations'
    }
]

failed = False

for i, step in enumerate(steps, 1):
    print(f"\n{'='*80}")
    print(f"STEP {i}/{len(steps)}: {step['name']}")
    print(f"Description: {step['description']}")
    print('='*80)
    print()
    
    try:
        result = subprocess.run(
            [sys.executable, step['script']],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"\n❌ STEP {i} FAILED")
            print("Error output:")
            print(result.stderr)
            failed = True
            break
        else:
            print(f"\n✓ STEP {i} COMPLETED SUCCESSFULLY")
    
    except subprocess.TimeoutExpired:
        print(f"\n❌ STEP {i} TIMED OUT (>120 seconds)")
        failed = True
        break
    except Exception as e:
        print(f"\n❌ STEP {i} ERROR: {e}")
        failed = True
        break

print("\n" + "="*80)
if failed:
    print("BACKTESTING FAILED")
    print("="*80)
    print("\nSome steps did not complete successfully.")
    print("Review error messages above.")
else:
    print("BACKTESTING COMPLETE")
    print("="*80)
    print()
    print("✓ All steps completed successfully")
    print()
    print("RESULTS SUMMARY:")
    print("  • backtest_dataset.json - Raw historical data")
    print("  • individual_factor_results.json - Single factor performance")
    print("  • baseline_comparison.json - Strategy comparison")
    print("  • comprehensive_backtest_report.json - Final recommendations")
    print()
    print("NEXT STEPS:")
    print("  1. Review comprehensive_backtest_report.json")
    print("  2. Read recommendations section carefully")
    print("  3. Implement top priority recommendation")
    print()
    print("To view report:")
    print("  python -c \"import json; print(json.dumps(json.load(open('comprehensive_backtest_report.json')), indent=2))\"")

print("\n" + "="*80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

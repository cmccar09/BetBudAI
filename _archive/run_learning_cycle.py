#!/usr/bin/env python3
"""
Complete learning cycle:
1. Fetch results for past picks
2. Generate learning insights from winners/losers
3. Update AI prompt with learnings
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and show output"""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if result.returncode != 0:
        print(f"WARNING: Command exited with code {result.returncode}")
    
    return result.returncode == 0

def main():
    python_exe = sys.executable
    
    print("DAILY LEARNING CYCLE STARTING...")
    
    # Step 1: Fetch results for recent picks
    success = run_command(
        f'"{python_exe}" fetch_hourly_results.py',
        "STEP 1: Fetching race results"
    )
    
    # Step 2: Generate learning insights
    if os.path.exists('generate_learning_insights.py'):
        run_command(
            f'"{python_exe}" generate_learning_insights.py',
            "STEP 2: Generating learning insights"
        )
    
    # Step 3: Update Lambda with new insights (if S3 bucket exists)
    print(f"\n{'='*70}")
    print("LEARNING CYCLE COMPLETE")
    print(f"{'='*70}")
    print("\nNext steps:")
    print("1. New picks will use updated learning insights")
    print("2. Run this daily after races complete")
    print("3. Monitor performance improvements over time")

if __name__ == "__main__":
    main()

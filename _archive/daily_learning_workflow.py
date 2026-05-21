#!/usr/bin/env python3
"""
daily_learning_workflow.py - Automated daily learning loop
1. Fetch yesterday's race results
2. Evaluate performance vs predictions
3. Update prompt with learned adjustments
4. Generate today's selections with updated logic
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime, timedelta
from pathlib import Path

def run_command(cmd: str, description: str):
    """Run shell command with error handling"""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    print(f"Running: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ ERROR: {description} failed with code {result.returncode}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Automated daily learning workflow")
    parser.add_argument("--date", type=str, default="", help="Date to evaluate (YYYY-MM-DD, default: yesterday)")
    parser.add_argument("--apply_updates", action="store_true", help="Actually update prompt.txt (default: dry run)")
    parser.add_argument("--skip_results", action="store_true", help="Skip fetching results (use existing)")
    parser.add_argument("--skip_evaluation", action="store_true", help="Skip evaluation (just run selections)")
    parser.add_argument("--run_today", action="store_true", help="Generate selections for today after learning")
    
    args = parser.parse_args()
    
    # Determine date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        target_date = datetime.now() - timedelta(days=1)
    
    date_str = target_date.strftime("%Y-%m-%d")
    date_slug = target_date.strftime("%Y%m%d")
    
    print(f"""
{'='*60}
DAILY LEARNING WORKFLOW
{'='*60}
Evaluation Date: {date_str}
Apply Updates: {args.apply_updates}
{'='*60}
""")
    
    # File paths
    selections_file = f"./history/selections_{date_slug}.csv"
    results_file = f"./history/results_{date_slug}.json"
    report_file = f"./history/performance_{date_slug}.md"
    
    # Create history directory
    os.makedirs("./history", exist_ok=True)
    
    # STEP 1: Fetch results (if not skipped)
    if not args.skip_results:
        if not os.path.exists(selections_file):
            print(f"⚠️  WARNING: No selections file found for {date_str}")
            print(f"    Looking for: {selections_file}")
            print("    Skipping result fetch. Run workflow after making selections first.")
        else:
            cmd = f"python fetch_race_results.py --date {date_str} --selections {selections_file} --out {results_file}"
            if not run_command(cmd, f"Fetch results for {date_str}"):
                sys.exit(1)
    else:
        print(f"\n⏭️  Skipping result fetch (--skip_results)")
    
    # STEP 2: Evaluate performance (if not skipped)
    if not args.skip_evaluation:
        if not os.path.exists(selections_file):
            print(f"\n⚠️  No selections file found: {selections_file}")
            print("    Skipping evaluation")
        elif not os.path.exists(results_file):
            print(f"\n⚠️  No results file found: {results_file}")
            print("    Skipping evaluation")
        else:
            apply_flag = "--apply" if args.apply_updates else ""
            cmd = f"python evaluate_performance.py --selections {selections_file} --results {results_file} --report {report_file} {apply_flag}"
            if not run_command(cmd, f"Evaluate performance for {date_str}"):
                sys.exit(1)
            
            # STEP 2a: Auto-adjust weights based on results
            cmd = "python auto_adjust_weights.py"
            if not run_command(cmd, "Auto-adjust scoring weights based on results"):
                print("⚠️  Weight adjustment failed but continuing...")
    else:
        print(f"\n⏭️  Skipping evaluation (--skip_evaluation)")
    
    # STEP 3: Generate today's selections with updated prompt (if requested)
    if args.run_today:
        today_slug = datetime.now().strftime("%Y%m%d")
        today_selections = f"./history/selections_{today_slug}.csv"
        
        # Generate selections and save to DynamoDB
        cmd = f"python run_prompt_with_betfair.py --use_saved_prompt --auto --once --out_csv {today_selections} --save_to_dynamodb"
        if not run_command(cmd, "Generate today's selections with updated logic"):
            sys.exit(1)
        
        print(f"\n✓ Today's selections saved to: {today_selections}")
        print(f"✓ Selections stored in DynamoDB (visible in React app)")
    
    # Summary
    print(f"""
{'='*60}
WORKFLOW COMPLETE
{'='*60}
Files generated:
  - Results: {results_file}
  - Report:  {report_file}
  - Prompt:  {'UPDATED' if args.apply_updates else 'NOT UPDATED (dry run)'}
{'='*60}

Next steps:
  1. Review report: {report_file}
  2. Run with --apply_updates to actually update prompt.txt
  3. Run with --run_today to generate selections with learned logic
  
Full learning loop:
  python daily_learning_workflow.py --apply_updates --run_today
{'='*60}
""")

if __name__ == "__main__":
    main()

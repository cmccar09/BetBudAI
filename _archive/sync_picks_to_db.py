#!/usr/bin/env python3
"""
Quick command to save today's selections to DynamoDB for React app
"""

import os
import sys
import glob
import subprocess
from datetime import datetime

def find_latest_selections():
    """Find the most recent selections CSV"""
    patterns = [
        f"./history/selections_{datetime.now().strftime('%Y%m%d')}.csv",
        "./top5.csv",
        "./my_probs.csv",
        "./history/selections_*.csv"
    ]
    
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[-1]
    return None

def main():
    print("="*60)
    print("Save Today's Picks to Database")
    print("="*60)
    
    # Find selections file
    selections_file = find_latest_selections()
    
    if not selections_file:
        print("\n❌ ERROR: No selections file found")
        print("\nRun this first to generate selections:")
        print("  python run_prompt_with_betfair.py --use_saved_prompt --auto --once")
        sys.exit(1)
    
    print(f"\n📁 Found selections: {selections_file}")
    
    # Save to DynamoDB
    cmd = f'python save_selections_to_dynamodb.py --selections "{selections_file}" --min_roi 0.0'
    
    print(f"\n🚀 Saving to DynamoDB...")
    print(f"Command: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print("\n✅ SUCCESS! Picks are now in DynamoDB")
        print("🌐 Your React app should show them now")
    else:
        print(f"\n❌ ERROR: Failed with exit code {result.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()

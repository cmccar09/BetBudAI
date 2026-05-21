"""
MASTER CONTROL: Run Both Workflows Simultaneously
Starts both background learning and value betting systems at 11am
"""

import subprocess
import sys
from datetime import datetime


def start_both_workflows():
    """Start both workflows in separate processes"""
    
    print("\n" + "="*80)
    print("DUAL WORKFLOW SYSTEM STARTING")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Starting 2 parallel workflows:")
    print()
    print("1️⃣  BACKGROUND LEARNING (11am-7pm, 30min cycles)")
    print("   → Stores ALL horses from ALL races")
    print("   → Analyzes why winners won")
    print("   → Auto-adjusts scoring logic")
    print("   → Everything saved to database (show_in_ui=False)")
    print()
    print("2️⃣  VALUE BETTING (11am-7pm, 30min cycles)")
    print("   → Finds high-confidence value bets")
    print("   → Uses optimized/learned logic")
    print("   → Only score >= 75 appear on UI (show_in_ui=True)")
    print()
    print("="*80)
    print()
    
    # Start background learning in new terminal
    print("Starting Background Learning System...")
    learning_process = subprocess.Popen(
        ['powershell', '-Command', 
         'Start-Process', 'powershell', 
         '-ArgumentList', '"-NoExit -Command python background_learning_workflow.py"',
         '-WindowStyle', 'Normal'],
        cwd=r'C:\Users\charl\OneDrive\futuregenAI\Betting'
    )
    
    print("✓ Background Learning started in new terminal")
    print()
    
    # Start value betting in new terminal  
    print("Starting Value Betting System...")
    betting_process = subprocess.Popen(
        ['powershell', '-Command',
         'Start-Process', 'powershell',
         '-ArgumentList', '"-NoExit -Command python value_betting_workflow.py"',
         '-WindowStyle', 'Normal'],
        cwd=r'C:\Users\charl\OneDrive\futuregenAI\Betting'
    )
    
    print("✓ Value Betting started in new terminal")
    print()
    
    print("="*80)
    print("BOTH WORKFLOWS ARE NOW RUNNING")
    print("="*80)
    print()
    print("What's happening:")
    print("  • Background Learning: Analyzing ALL races, learning patterns")
    print("  • Value Betting: Finding high-confidence picks for UI")
    print()
    print("To stop:")
    print("  • Close the PowerShell windows")
    print("  • Or press Ctrl+C in each window")
    print()
    print("Check the UI to see validated picks (GOOD 55+ or EXCELLENT 70+)")
    print("Check DynamoDB to see learning analysis (show_in_ui=False)")
    print("="*80)


if __name__ == "__main__":
    start_both_workflows()

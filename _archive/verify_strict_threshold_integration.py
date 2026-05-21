"""
Verify Strict Threshold System Integration
Checks that all workflows are using updated configuration
"""
import os
import re

def check_file_uses_correct_script(filepath, correct_script, old_script):
    """Check if a file uses the correct analysis script"""
    if not os.path.exists(filepath):
        return None, "File not found"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    uses_correct = correct_script in content
    uses_old = old_script in content
    
    if uses_correct and not uses_old:
        return True, "Using complete_daily_analysis.py"
    elif uses_old and not uses_correct:
        return False, f"Still using {old_script}"
    elif uses_correct and uses_old:
        return None, "Uses both (may need cleanup)"
    else:
        return None, "Doesn't use either script"

def check_threshold_value(filepath):
    """Check if file has correct 85+ threshold"""
    if not os.path.exists(filepath):
        return None, "File not found"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for threshold patterns
    threshold_85 = re.search(r'>=\s*85', content)
    threshold_70 = re.search(r'>=\s*70', content) and not re.search(r'70-84|70\+.*dodgy', content.lower())
    
    if threshold_85:
        return True, "Using 85+ threshold"
    elif threshold_70:
        return False, "Still using old 70+ threshold"
    else:
        return None, "No explicit threshold check found"

print("="*80)
print("STRICT THRESHOLD SYSTEM - INTEGRATION VERIFICATION")
print("="*80)

# Files to check
workflow_files = [
    'coordinated_learning_workflow.py',
    'daily_automated_workflow.py',
    'background_learning_workflow.py',
    'value_betting_workflow.py',
    'complete_daily_analysis.py'
]

print("\n1. Checking workflow scripts use complete_daily_analysis.py...")
print("-" * 80)

for filename in workflow_files:
    status, message = check_file_uses_correct_script(
        filename,
        'complete_daily_analysis.py',
        'analyze_all_races_comprehensive.py'
    )
    
    symbol = "✓" if status is True else ("✗" if status is False else "⚠")
    color = "green" if status is True else ("red" if status is False else "yellow")
    
    print(f"{symbol} {filename:45} - {message}")

print("\n2. Checking threshold configuration (85+)...")
print("-" * 80)

threshold_files = [
    'complete_daily_analysis.py',
    'coordinated_learning_workflow.py'
]

for filename in threshold_files:
    status, message = check_threshold_value(filename)
    
    symbol = "✓" if status is True else ("✗" if status is False else "⚠")
    
    print(f"{symbol} {filename:45} - {message}")

print("\n3. Checking coverage tracking in complete_daily_analysis.py...")
print("-" * 80)

if os.path.exists('complete_daily_analysis.py'):
    with open('complete_daily_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_coverage_pct = 'race_coverage_pct' in content
    has_analyzed_count = 'race_analyzed_count' in content
    has_total_count = 'race_total_count' in content
    
    if has_coverage_pct and has_analyzed_count and has_total_count:
        print("✓ All coverage fields present (race_coverage_pct, race_analyzed_count, race_total_count)")
    else:
        missing = []
        if not has_coverage_pct: missing.append('race_coverage_pct')
        if not has_analyzed_count: missing.append('race_analyzed_count')
        if not has_total_count: missing.append('race_total_count')
        print(f"✗ Missing coverage fields: {', '.join(missing)}")
else:
    print("✗ complete_daily_analysis.py not found")

print("\n4. Checking risk descriptions...")
print("-" * 80)

if os.path.exists('complete_daily_analysis.py'):
    with open('complete_daily_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    descriptions = [
        ('Sure Thing', '85+ EXCELLENT grade'),
        ('Reasonable but Dodgy', '70-84 GOOD grade'),
        ('Very Risky', '55-69 FAIR grade'),
        ('Will Likely Lose', '<55 POOR grade')
    ]
    
    all_present = True
    for desc, context in descriptions:
        if desc in content:
            print(f"✓ '{desc}' - {context}")
        else:
            print(f"✗ Missing: '{desc}'")
            all_present = False
else:
    print("✗ complete_daily_analysis.py not found")

print("\n5. Scheduled tasks status...")
print("-" * 80)

import subprocess
try:
    result = subprocess.run(
        ['powershell', '-Command', 
         "Get-ScheduledTask -TaskName 'CoordinatedLearning','RacingPostScraper' -ErrorAction SilentlyContinue | Select-Object TaskName,State"],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode == 0 and result.stdout:
        print(result.stdout)
    else:
        print("⚠ Could not query scheduled tasks (may need admin)")
except Exception as e:
    print(f"⚠ Could not check scheduled tasks: {e}")

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print("\nNext steps:")
print("1. Review any ✗ or ⚠ items above")
print("2. Run: python complete_daily_analysis.py")
print("3. Verify with: python show_todays_ui_picks.py")
print("4. Check coverage shows 100% for all picks")
print("5. Confirm only 85+ scores shown as UI picks")

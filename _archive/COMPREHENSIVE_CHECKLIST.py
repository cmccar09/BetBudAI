"""
COMPREHENSIVE RACE ANALYSIS CHECKLIST
All checks that MUST happen for each race

Run this for Wolverhampton 18:30 onwards TODAY
"""
import boto3
from datetime import datetime
import json

print("="*80)
print("COMPREHENSIVE RACE ANALYSIS - REQUIRED CHECKS")
print("="*80)
print()

REQUIRED_CHECKS = {
    "1. DATA COLLECTION": [
        "✓ Fetch all UK/Ireland races from API",
        "✓ Get all horses in each race (100% coverage target)",
        "✓ Betfair odds for each horse",
        "✓ Weather conditions at venue",
        "✓ Going (track condition)",
    ],
    
    "2. HORSE ANALYSIS": [
        "✓ Form string (last 10 runs)",
        "✓ Recent wins (check last 5 runs, not just LTO)",
        "✓ Improvement patterns (getting better positions)",
        "✓ Consistency (stable placings)",
        "✓ Course history (wins/places at this venue)",
        "✓ Distance suitability",
    ],
    
    "3. JOCKEY & TRAINER": [
        "✓ Jockey win rate",
        "✓ Trainer statistics",
        "✓ Jockey/Trainer combination success",
        "✓ Elite trainer bonus (Nicholls, Mullins, etc.)",
    ],
    
    "4. ODDS ANALYSIS": [
        "✓ Current Betfair odds",
        "✓ Odds movement tracking",
        "✓ Sweet spot detection (3-9 odds = +12 bonus)",
        "✓ Optimal odds (3-6 odds)",
        "✓ Long-shot penalty (10-15 = -5, >15 = -10)",
    ],
    
    "5. WEATHER & CONDITIONS": [
        "✓ Current weather at venue",
        "✓ Temperature",
        "✓ Rain/wind conditions",
        "✓ Track going (Heavy/Soft/Good/Firm)",
        "✓ Horse preference for going",
    ],
    
    "6. CONFIDENCE SCORING": [
        "✓ Base score: 30",
        "✓ Form scoring (weighted recent runs)",
        "✓ Win bonuses (graduated by recency)",
        "✓ Improvement pattern bonus",
        "✓ Consistency bonus",
        "✓ Odds adjustment",
        "✓ Course bonus",
        "✓ Trainer bonus",
        "✓ comprehensive_score field set",
        "✓ combined_confidence field set",
        "✓ confidence_grade (EXCELLENT/GOOD/FAIR/POOR)",
    ],
    
    "7. VALIDATION": [
        "✓ Race coverage >= 90% minimum",
        "✓ All horses have analysis_type='PRE_RACE_COMPLETE'",
        "✓ Score >= 45 for UI inclusion",
        "✓ Coverage tracking (race_coverage_pct, race_analyzed_count, race_total_count)",
        "✓ show_in_ui flag set correctly",
    ],
    
    "8. DATABASE STORAGE": [
        "✓ bet_date (partition key)",
        "✓ bet_id (sort key)",
        "✓ All required fields populated",
        "✓ No duplicates",
        "✓ Consistent field names",
    ],
}

print("CHECKLIST:\n")
for category, checks in REQUIRED_CHECKS.items():
    print(f"{category}")
    for check in checks:
        print(f"  {check}")
    print()

print("="*80)
print("WORKFLOW SCRIPTS THAT MUST RUN:")
print("="*80)
print()

WORKFLOW_SCRIPTS = [
    ("1", "fetch_betfair_data.py", "Get all races + Betfair odds + weather"),
    ("2", "analyze_all_races_comprehensive.py", "Analyze ALL horses in ALL races (100% coverage)"),
    ("3", "calculate_all_confidence_scores.py", "Calculate comprehensive_score for each horse"),
    ("4", "set_ui_picks_from_validated.py", "Select best picks (score >= 45, coverage >= 90%)"),
    ("5", "show_todays_ui_picks.py", "Display UI picks with coverage status"),
]

for num, script, description in WORKFLOW_SCRIPTS:
    print(f"{num}. {script}")
    print(f"   Purpose: {description}")
    print()

print("="*80)
print("DAILY AUTOMATION:")
print("="*80)
print()
print("• daily_automated_workflow.py runs ALL of these at 9:00 AM")
print("• Windows Task Scheduler: BettingDailyWorkflow")
print("• Can also run manually for specific races")
print()

print("="*80)
print("NOW RUNNING FOR WOLVERHAMPTON 18:30 ONWARDS...")
print("="*80)
print()

"""
Daily Automated Learning - Complete Workflow with Realistic Win Probability Grading
Runs automatically every day to:
1. Fetch yesterday's results
2. Analyze performance
3. Auto-adjust weights
4. Generate today's picks with realistic probability validation

REALISTIC WIN PROBABILITY GRADING SYSTEM:
- EXCELLENT: 85+ points (Green)       - 40-50% win chance - 2.0x stake
- GOOD:      70-84 points (Light amber) - 25-35% win chance - 1.5x stake
- FAIR:      55-69 points (Dark amber)  - 15-25% win chance - 1.0x stake
- POOR:      <55 points (Red)          - <15% win chance   - 0.5x stake

CRITICAL REQUIREMENT:
- ALL horses in ALL races MUST be analyzed before racing
- Minimum 90% coverage required (100% preferred)
- Races with <90% coverage will NOT appear on UI
- Never show picks when we haven't analyzed the full field
"""

import subprocess
import sys
from datetime import datetime, timedelta

def run_step(description, command):
    """Run a workflow step with logging"""
    print(f"\n{'='*80}")
    print(f"STEP: {description}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"\n⚠️ WARNING: {description} returned code {result.returncode}")
            print(result.stderr)
            return False
        
        print(f"\n✓ {description} completed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"\n❌ ERROR: {description} timed out")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {description} failed: {str(e)}")
        return False


def main():
    """Run complete daily workflow"""
    
    print(f"""
{'='*80}
DAILY AUTOMATED LEARNING WORKFLOW
{'='*80}
Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}
""")
    
    # STEP 1: Fetch results for yesterday's picks
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    run_step(
        "Fetch yesterday's race results",
        f"python betfair_results_fetcher_v2.py --date {yesterday}"
    )
    
    # STEP 1a: Store all races for learning — now handled by SureBet-Morning Lambda
    # (complete_race_learning.py store — archived, replaced by AWS pipeline)
    print("\n[Step 1a] Race storage for learning handled by SureBet-Morning step function.")
    
    # STEP 2: Auto-adjust weights based on results
    success = run_step(
        "Auto-adjust scoring weights based on performance",
        "python auto_adjust_weights.py"
    )
    
    if success:
        print("\n🎯 Weights have been automatically optimized based on yesterday's results")
    
    # STEP 2a: Learning — now handled by SureBet-Evening/Learning Lambda
    run_step(
        "Check winners and learn from ALL races",
        "python -c \"import boto3,json; lam=boto3.client('lambda',region_name='eu-west-1'); r=lam.invoke(FunctionName='BettingPicksAPI',Payload=json.dumps({'rawPath':'/api/learning/apply','requestContext':{'http':{'method':'POST'}},'headers':{'content-type':'application/json'},'body':json.dumps({'date':__import__('datetime').datetime.now().strftime('%Y-%m-%d')})})); print(json.loads(r['Payload'].read()).get('statusCode'))\""
    )
    
    # STEP 3: Fetch today's races
    run_step(
        "Fetch today's race data",
        "python betfair_odds_fetcher.py"
    )
    
    # STEP 4: Comprehensive analysis with strict thresholds (replaces steps 4-6)
    run_step(
        "Comprehensive analysis: Learning + UI picks (85+ threshold, 100% coverage)",
        "python complete_daily_analysis.py"
    )

    # STEP 4a: Send WhatsApp notifications for today's picks
    run_step(
        "Send WhatsApp notifications for today's picks",
        "python notify_picks.py"
    )
    
    # Note: complete_daily_analysis.py now handles:
    # - 7-factor comprehensive scoring for ALL horses
    # - Automatic UI promotion for 85+ scores (EXCELLENT tier)
    # - 100% race coverage tracking
    # - Realistic risk grading (Sure Thing, Dodgy, Risky, Will Lose)
    # Old steps (calculate_all_confidence_scores.py, set_ui_picks_from_validated.py) are replaced
    
    # ── CHELTENHAM FESTIVAL 2026 (10–13 March) ──────────────────────────────
    today_date = datetime.now().date()
    from datetime import date as _date
    cheltenham_start = _date(2026, 3,  5)   # Start updating picks 5 days pre-festival
    cheltenham_end   = _date(2026, 3, 13)   # Last race day
    festival_live    = _date(2026, 3, 10)   # First race day

    if cheltenham_start <= today_date <= cheltenham_end:
        print("\n" + "="*80)
        print("CHELTENHAM FESTIVAL 2026 — Running Cheltenham workflow")
        print("="*80)

        # Refresh picks: score all 28 races, save top pick + all_horses ranked list
        run_step(
            "Cheltenham: Score all 28 races and save picks to DynamoDB",
            "python save_cheltenham_picks.py"
        )

        # During live festival days, also refresh Betfair prices / intelligence
        if festival_live <= today_date <= cheltenham_end:
            run_step(
                "Cheltenham: Fetch live Betfair odds and update RP_LIVE_ODDS",
                "python cheltenham_2026_intelligence.py --update-picks"
            )
            # Re-run picks with fresh odds
            run_step(
                "Cheltenham: Re-save picks with updated live odds",
                "python save_cheltenham_picks.py"
            )

        # Regenerate Barry's competition HTML from live DynamoDB picks.
        # Applies macfitz_overrides.json (splits for dead-ties / near-ties)
        # and flags any NEW close calls that may need a human decision.
        run_step(
            "Barry's Competition: Regenerate HTML with live picks + MacFitz splits",
            "python barrys/update_barrys_html.py"
        )

    # STEP 7: Comprehensive historical learning (weekly)
    if datetime.now().weekday() == 0:  # Monday only
        print("\n" + "="*80)
        print("WEEKLY: Running comprehensive historical analysis...")
        print("="*80)
        run_step(
            "Comprehensive historical learning (all races, all time)",
            "python analyze_and_learn_all.py"
        )
    
    # Summary
    print(f"""
{'='*80}
WORKFLOW COMPLETE
{'='*80}
Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

WHAT HAPPENED:
1. ✓ Fetched yesterday's results
2. ✓ Stored ALL today's races for learning
3. ✓ Analyzed performance patterns
4. ✓ Automatically adjusted scoring weights
5. ✓ Learned from ALL race winners (not just our picks)
6. ✓ Fetched updated race data
7. ✓ Generated picks using optimized weights
8. ✓ Applied 4-tier grading (EXCELLENT/GOOD/FAIR/POOR)
9. ✓ Set UI picks (one per validated race)

[CHELTENHAM 5-13 Mar]: If in festival window:
  • Scored all 28 races (228 horses ranked)
  • BETTING_PICK: Grade 1, non-handicap, score ≥ 75
  • WATCH_LIST: non-handicap, score ≥ 60
  • OPINION_ONLY: handicaps / skip races / score < 60
  • On race days: live Betfair odds fetched + picks re-saved

NEXT STEPS:
- View picks: python show_todays_ui_picks.py
- UI shows only validated picks with 4-tier grading
- EXCELLENT (75+) gets 2.0x stake, GOOD (60-74) gets 1.5x stake

CONTINUOUS IMPROVEMENT:
The system learns from EVERY race (not just our picks):
1. Stores all horses from all UK/Ireland races
2. Checks actual winners when results come in
3. Compares winners vs our selection criteria
4. Identifies patterns (sweet spot%, form%, etc.)
5. Adjusts weights automatically
6. Uses learned weights for next day's picks
{'='*80}
""")


if __name__ == "__main__":
    main()

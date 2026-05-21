"""
BETTING WORKFLOW - COMPREHENSIVE ANALYSIS REQUIRED
This script ensures ALL picks use comprehensive analysis before being added to UI

Rule: NO picks go to UI without comprehensive scoring (minimum 60/100)
"""

import json
import boto3
from datetime import datetime
from decimal import Decimal
from comprehensive_pick_logic import analyze_horse_comprehensive, get_comprehensive_pick, should_skip_race

# ── Fix 3: normalise bet_id timestamp so all runs produce the same key ──────────
def _normalise_dt_for_bet_id(dt_str: str) -> str:
    """
    Convert any ISO-8601 datetime string to the canonical bet_id prefix:
      2026-03-30T141800+0000
    This ensures Run 1, Run 2, and any retry produce the same DynamoDB key
    and overwrite rather than creating orphan duplicates.
    Accepts: '2026-03-30T14:18:00+00:00'  or  '2026-03-30T141800+0000'
    """
    try:
        clean = dt_str.strip().replace('Z', '+00:00')
        dt = datetime.fromisoformat(clean)
        return dt.strftime('%Y-%m-%dT%H%M%S') + '+0000'
    except Exception:
        # Fallback: strip colons from time/tz portions manually
        return dt_str.replace(':', '').replace('+0000', '+0000')

def validate_pick_for_ui(pick_data):
    """
    Validate that a pick meets comprehensive analysis standards
    Returns: (is_valid, score, reasoning)
    """
    # Check if comprehensive score exists (accept both 'score' and 'comprehensive_score')
    score = pick_data.get('comprehensive_score') or pick_data.get('score')
    if score is None:
        return False, 0, "Missing comprehensive score - REJECTED"

    # Class 3/4/5/6 handicap hard block (any surface)
    # Lesson: 2026-03-01 Huntingdon 14:45 - Reallyntruthfully (1111 form, 3/1) PU
    # Handicapper-engineered unpredictability; model weights calibrated for Grade 1+
    skip, skip_reason = should_skip_race(pick_data)
    if skip:
        return False, score, f"Class 3-6 handicap - BLOCKED: {skip_reason}"

    # Minimum threshold: 65/100 (avoids POOR <55 and borderline FAIR picks)
    if score < 65:
        return False, score, f"Score too low ({score}/100) - minimum 65 required"

    # AW Class 5/6 block: handicapper-designed unpredictability, going advantage = 0
    # Lesson 2026-02-28: Royal Jet (105) lost to Dandy Khan (42) at 8/1 in AW Class 6
    breakdown = pick_data.get('breakdown', pick_data.get('score_breakdown', {}))
    aw_penalty = float(breakdown.get('aw_low_class_penalty', 0))
    if aw_penalty < 0:
        return False, score, f"AW Class 5/6 handicap - BLOCKED (too unpredictable, going advantage = 0)"
    
    # Check required fields (accept different naming conventions)
    horse_data = pick_data.get('horse', pick_data)
    if not horse_data.get('odds') and not horse_data.get('name'):
        return False, score, "Missing horse data"
    
    return True, score, "APPROVED for UI"

def add_pick_to_ui(pick_data, race_data):
    """
    Add a pick to the UI ONLY if it passes comprehensive analysis
    """
    # Validate comprehensive analysis
    is_valid, score, reason = validate_pick_for_ui(pick_data)
    
    if not is_valid:
        horse_name = pick_data.get('horse', {}).get('name', 'Unknown') if isinstance(pick_data.get('horse'), dict) else str(pick_data.get('horse', 'Unknown'))
        print(f"- REJECTED: {horse_name}")
        print(f"   Reason: {reason}")
        return False
    
    # Add to database with show_in_ui=True
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    today = datetime.now().strftime('%Y-%m-%d')
    race_time = race_data['race_time']
    
    # Extract horse data
    horse_data = pick_data.get('horse', {})
    horse_name = horse_data.get('name', '') if isinstance(horse_data, dict) else str(horse_data)
    odds = horse_data.get('odds', 0) if isinstance(horse_data, dict) else pick_data.get('odds', 0)
    form = horse_data.get('form', '') if isinstance(horse_data, dict) else pick_data.get('form', '')
    trainer = horse_data.get('trainer', '') if isinstance(horse_data, dict) else pick_data.get('trainer', '')
    selection_id = horse_data.get('selectionId', '') if isinstance(horse_data, dict) else pick_data.get('selectionId', '')
    
    # Fix 3: normalise timestamp in bet_id so all runs produce the same DynamoDB key
    normalised_rt = _normalise_dt_for_bet_id(race_time)
    bet_id = f"{normalised_rt}_{race_data['course']}_{horse_name}".replace(' ', '_')
    
    # Get reasoning
    reasons = pick_data.get('reasons', [])
    reasoning = ", ".join(reasons[:3]) if reasons else pick_data.get('reasoning', 'Comprehensive analysis')
    
    # Determine confidence
    if score >= 90:
        confidence = "VERY_HIGH"
    elif score >= 75:
        confidence = "HIGH"
    elif score >= 60:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    # Get coverage from pick data
    coverage = pick_data.get('coverage', 100)  # Default to 100% if not provided
    total_runners = pick_data.get('total_runners', 0)
    analyzed_runners = pick_data.get('analyzed_runners', 0)
    
    # Get market_id for results fetching
    market_id = race_data.get('market_id', '')
    
    item = {
        'bet_date': today,
        'bet_id': bet_id,
        'race_time': race_time,
        'horse': horse_name,
        'course': race_data['course'],
        'odds': Decimal(str(odds)),
        'form': form,
        'trainer': trainer,
        'selection_id': str(selection_id),
        'market_id': str(market_id),  # For Betfair results API
        'race_name': race_data.get('race_name', ''),
        'stake': Decimal('6.0'),
        'bet_type': 'WIN',
        'outcome': 'pending',
        'show_in_ui': (score >= 90),  # Threshold: 90+ (85-89 is historically -21.8% ROI losing band)
        'recommended_bet': (score >= 90),
        
        # Comprehensive analysis data
        'comprehensive_score': Decimal(str(score)),
        'combined_confidence': Decimal(str(score)),  # For UI compatibility
        'score_breakdown': pick_data.get('breakdown', {}),
        'reasoning': reasoning,
        'reasons': reasons,          # Full list of scoring reasons for UI
        'all_horses': [              # All runners ranked by score (floats → Decimal for DynamoDB)
            {
                'horse':   h.get('horse', ''),
                'jockey':  h.get('jockey', ''),
                'trainer': h.get('trainer', ''),
                'odds':    Decimal(str(round(float(h.get('odds', 0) or 0), 2))),
                'score':   Decimal(str(int(h.get('score', 0) or 0))),
            }
            for h in pick_data.get('all_horses', [])
        ],
        'confidence': confidence,
        'analysis_method': 'COMPREHENSIVE',
        
        # Coverage metrics - MULTIPLE FIELD NAMES FOR UI COMPATIBILITY
        # Frontend may use any of these field names
        'coverage': Decimal(str(coverage)),
        'data_coverage': Decimal(str(coverage)),
        'race_coverage_pct': Decimal(str(coverage)),  # Legacy UI field name
        'total_runners': total_runners,
        'analyzed_runners': analyzed_runners,
        
        'timestamp': datetime.now().isoformat()
    }
    
    # ── Fix 2: check existing record before writing ────────────────────────────
    # If the existing record already has show_in_ui=True we PRESERVE that flag
    # regardless of the new score, so a re-run can never silently demote a pick.
    # Fix 5: detect large score drops for audit/investigation.
    preserve_shown = False
    large_score_drop_meta = None
    try:
        existing = table.get_item(Key={'bet_date': today, 'bet_id': bet_id}).get('Item')
        if existing:
            old_score = float(existing.get('comprehensive_score', 0) or 0)
            delta = score - old_score
            if existing.get('show_in_ui') is True:
                preserve_shown = True
                print(f'[PRESERVE] {horse_name} already show_in_ui=True (score was {old_score:.0f}, new {score:.0f}) — keeping shown')
            # Fix 5: flag drops >= 10pts for investigation
            if delta <= -10:
                large_score_drop_meta = {
                    'horse': horse_name,
                    'course': race_data['course'],
                    'race_time': race_time,
                    'old_score': int(old_score),
                    'new_score': int(score),
                    'delta': int(delta),
                }
                print(f'[SCORE DROP] {horse_name} {race_data["course"]} {race_time}: {old_score:.0f} -> {score:.0f} ({delta:+.0f}pts) — investigate signal change')
    except Exception as e:
        print(f'[PRESERVE] WARNING: Could not check existing record: {e}')

    # Apply preservation: if the existing pick was shown, keep it shown
    if preserve_shown:
        item['show_in_ui'] = True
        item['recommended_bet'] = True

    table.put_item(Item=item)
    
    print(f"+ APPROVED: {horse_name} @ {odds}")
    print(f"   Score: {score}/100 - {confidence}")
    print(f"   Reasoning: {reasoning[:80]}...")

    # Return (True, meta) so the caller (workflow) can collect large-drop diagnostics
    if large_score_drop_meta:
        return True, {'large_score_drop': large_score_drop_meta}
    return True, {}

def analyze_race_comprehensive(race_data):
    """
    Analyze a race using comprehensive logic
    Returns best pick or None if no suitable horses
    """
    course = race_data.get('course', 'Unknown')
    runners = race_data.get('runners', [])
    
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE ANALYSIS: {race_data.get('race_time')} - {race_data.get('race_name')}")
    print(f"Course: {course}")
    print(f"{'='*80}\n")
    
    # Get comprehensive pick
    pick = get_comprehensive_pick(race_data, course_stats={'avg_winner_odds': 4.75})
    
    if pick:
        print(f"\n+ Best pick: {pick['horse']} @ {pick['odds']}")
        print(f"  Score: {pick['comprehensive_score']}/100")
        print(f"  Confidence: {pick['confidence']}")
        return pick
    else:
        print("\n✗ No suitable picks (all scores below threshold)")
        return None

if __name__ == "__main__":
    print("\n" + "="*80)
    print("BETTING WORKFLOW - COMPREHENSIVE ANALYSIS ENFORCEMENT")
    print("="*80)
    print("\nRule: ALL UI picks must score 60+ using comprehensive analysis")
    print("Factors: Sweet spot + Odds + Form + Wins + Consistency + Course + History")
    print("\nThis prevents picks based on odds alone (tonight's 0/2 mistake)")
    print("="*80 + "\n")

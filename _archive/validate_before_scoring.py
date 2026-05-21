#!/usr/bin/env python3
"""
VALIDATION LAYER
Add this to any scoring function to prevent 0-score failures
"""

def validate_horse_data(horse, race_context="Unknown"):
    """
    Validate horse has minimum required data before scoring
    Returns (is_valid, error_message)
    """
    
    errors = []
    warnings = []
    
    # Critical checks (will cause 0 score if missing)
    if not horse.get('name'):
        errors.append("No horse name")
    
    if not horse.get('odds') or float(horse.get('odds', 0)) == 0:
        errors.append("No odds data")
    
    form = horse.get('form')
    if not form or form == 'N/A' or form == '':
        errors.append("No form data")
    
    # Warnings (non-critical but affects quality)
    if not horse.get('trainer'):
        warnings.append("No trainer data")
    
    if not horse.get('jockey'):
        warnings.append("No jockey data")
    
    if errors:
        error_msg = f"[{race_context}] {horse.get('name', 'Unknown')}: " + ", ".join(errors)
        return False, error_msg
    
    if warnings:
        warning_msg = f"[{race_context}] {horse.get('name', 'Unknown')}: " + ", ".join(warnings)
        return True, warning_msg
    
    return True, None


def validate_race_data(race):
    """
    Validate race has minimum data before analysis
    Returns (is_valid, error_message, coverage_pct)
    """
    
    runners = race.get('runners', [])
    venue = race.get('venue', 'Unknown')
    race_time = race.get('start_time', 'Unknown')
    
    if not runners:
        return False, f"{venue} {race_time}: No runners data", 0
    
    # Check data coverage
    valid_runners = 0
    for runner in runners:
        is_valid, _ = validate_horse_data(runner, f"{venue} {race_time}")
        if is_valid:
            valid_runners += 1
    
    coverage = (valid_runners / len(runners)) * 100
    
    # CRITICAL: Require 90% coverage minimum
    # Lesson from Carlisle 15:35: 9% coverage = system failure
    if coverage < 90:
        return False, f"{venue} {race_time}: Only {coverage:.0f}% coverage ({valid_runners}/{len(runners)} runners)", coverage
    
    return True, None, coverage


def safe_score_horse(horse, scoring_function, race_context="Unknown"):
    """
    Wrapper around any scoring function that validates data first
    Usage: score = safe_score_horse(horse, your_scoring_function, "Venue Time")
    """
    
    # Validate first
    is_valid, error_msg = validate_horse_data(horse, race_context)
    
    if not is_valid:
        print(f"  ⚠ Skipping: {error_msg}")
        return 0, ["Insufficient data"]
    
    # Data is valid, proceed with scoring
    try:
        return scoring_function(horse)
    except Exception as e:
        print(f"  ✗ Scoring error for {horse.get('name')}: {e}")
        return 0, [f"Scoring error: {str(e)[:50]}"]


# Example usage in comprehensive_pick_logic.py:
"""
from validate_before_scoring import safe_score_horse, validate_race_data

def analyze_race(race):
    # Validate race data first
    is_valid, error, coverage = validate_race_data(race)
    
    if not is_valid:
        print(f"  ✗ SKIPPING RACE: {error}")
        return None
    
    print(f"  ✓ Coverage: {coverage:.0f}%")
    
    # Score each horse safely
    for runner in race['runners']:
        score, reasons = safe_score_horse(runner, score_horse_function, race['venue'])
        # ... rest of logic
"""

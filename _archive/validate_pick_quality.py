#!/usr/bin/env python3
"""
Validate pick quality before saving to database
Implements improved picking rules based on winner analysis
"""
import sys
import json
import argparse

def validate_pick(pick, race_type='horse'):
    """
    Validate a single pick based on quality rules
    Returns: (is_valid, reason)
    """
    confidence = float(pick.get('confidence', 0))
    has_enrichment = bool(pick.get('enrichment_data'))
    reasoning = pick.get('why_now', '').lower()
    combined_confidence = float(pick.get('combined_confidence', confidence))
    
    # Rule 1: Greyhounds with high confidence MUST have enrichment data
    if race_type == 'greyhound' and confidence >= 60:
        if not has_enrichment:
            return False, f"REJECTED: {confidence}% confidence but NO form data to validate"
    
    # Rule 2: Greyhounds without enrichment capped at 50% confidence
    if race_type == 'greyhound' and not has_enrichment:
        if confidence > 50:
            return False, f"REJECTED: {confidence}% confidence without form data (max 50% allowed)"
    
    # Rule 3: Combined confidence threshold for greyhounds
    if race_type == 'greyhound' and combined_confidence < 50:
        return False, f"REJECTED: Combined confidence {combined_confidence}% too low (min 50%)"
    
    # Rule 4: Shallow reasoning detection
    shallow_indicators = ['lowest odds', 'shortest odds', 'best odds']
    performance_indicators = ['form', 'win rate', 'recent performance', 'track record', 'trainer']
    
    has_shallow = any(indicator in reasoning for indicator in shallow_indicators)
    has_performance = any(indicator in reasoning for indicator in performance_indicators)
    
    if has_shallow and not has_performance and confidence >= 60:
        return False, f"REJECTED: Shallow reasoning (odds-only) for {confidence}% confidence pick"
    
    # Rule 5: Minimum combined confidence for any pick
    if combined_confidence < 35:
        return False, f"REJECTED: Combined confidence {combined_confidence}% below minimum threshold"
    
    # All rules passed
    return True, "VALID"

def main():
    parser = argparse.ArgumentParser(description='Validate pick quality')
    parser.add_argument('--picks-file', required=True, help='JSON file with picks')
    parser.add_argument('--race-type', default='horse', choices=['horse', 'greyhound'])
    parser.add_argument('--out', help='Output file for valid picks')
    
    args = parser.parse_args()
    
    # Load picks
    try:
        with open(args.picks_file, 'r') as f:
            picks = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not load picks file: {e}")
        sys.exit(1)
    
    if not isinstance(picks, list):
        picks = [picks]
    
    print("=" * 80)
    print("PICK QUALITY VALIDATION")
    print("=" * 80)
    print(f"Race type: {args.race_type}")
    print(f"Total picks to validate: {len(picks)}")
    print()
    
    valid_picks = []
    rejected_picks = []
    
    for i, pick in enumerate(picks, 1):
        horse = pick.get('horse', pick.get('name', 'Unknown'))
        confidence = pick.get('confidence', 0)
        
        is_valid, reason = validate_pick(pick, args.race_type)
        
        if is_valid:
            print(f"[{i}] {horse} - {confidence}% - {reason}")
            valid_picks.append(pick)
        else:
            print(f"[{i}] {horse} - {confidence}% - {reason}")
            rejected_picks.append({
                'pick': pick,
                'reason': reason
            })
    
    print()
    print("=" * 80)
    print(f"VALID: {len(valid_picks)}/{len(picks)} picks passed validation")
    print(f"REJECTED: {len(rejected_picks)}/{len(picks)} picks failed validation")
    print("=" * 80)
    
    if rejected_picks:
        print("\nRejection Summary:")
        for item in rejected_picks:
            horse = item['pick'].get('horse', item['pick'].get('name', 'Unknown'))
            print(f"  - {horse}: {item['reason']}")
    
    # Save valid picks if output specified
    if args.out and valid_picks:
        with open(args.out, 'w') as f:
            json.dump(valid_picks, f, indent=2)
        print(f"\nSaved {len(valid_picks)} valid picks to: {args.out}")
    
    # Exit with error if all picks rejected
    if len(valid_picks) == 0:
        print("\nWARNING: All picks rejected - no bets to place")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()

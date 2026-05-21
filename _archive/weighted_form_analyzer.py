"""
Enhanced Form Analyzer - Weights recent runs heavily
Based on Carlisle 14:00 lessons (Thank You Maam had 7th last run)
"""


def analyze_form_weighted(form_string):
    """
    Analyze form with heavy weighting on recent runs
    
    Weighting:
    - Last run: 50%
    - Second-last: 30%
    - Older runs: 20%
    
    Returns: (weighted_score, analysis_dict)
    """
    if not form_string:
        return 0, {'error': 'No form data'}
    
    # Clean form string (remove non-alphanumeric except -)
    form = ''.join(c for c in form_string if c.isalnum() or c in ['-', '/'])
    
    # Split by - or / to get individual runs
    runs = []
    for separator in ['-', '/']:
        if separator in form:
            runs = form.split(separator)
            break
    
    if not runs:
        # No separator, treat each character as a run
        runs = list(form)
    
    # Remove empty strings
    runs = [r for r in runs if r]
    
    if not runs:
        return 0, {'error': 'Could not parse form'}
    
    # Scoring for each position
    position_scores = {
        '1': 100,  # Win
        '2': 60,   # 2nd
        '3': 40,   # 3rd
        '4': 20,   # 4th
        '5': 10,   # 5th
        '6': 5,    # 6th
        '7': -10,  # 7th or worse = penalty
        '8': -15,
        '9': -20,
        '0': -30,  # Unplaced
        'P': -40,  # Pulled up
        'F': -40,  # Fell
        'U': -40,  # Unseated
    }
    
    # Calculate weighted score
    weights = [0.50, 0.30, 0.20]  # Last run, 2nd last, older
    
    total_score = 0
    run_details = []
    
    for i, run in enumerate(runs[:3]):  # Only look at last 3 runs
        weight = weights[i] if i < len(weights) else 0.20
        
        # Get score for this run
        run_score = 0
        for char in run:
            if char in position_scores:
                run_score = max(run_score, position_scores[char])
        
        weighted_contribution = run_score * weight
        total_score += weighted_contribution
        
        run_details.append({
            'position': i + 1,
            'result': run,
            'score': run_score,
            'weight': weight,
            'contribution': weighted_contribution
        })
    
    # Analyze patterns
    analysis = {
        'total_score': round(total_score, 1),
        'runs_analyzed': len(run_details),
        'run_details': run_details,
        'last_run': runs[0] if runs else None,
        'form_string': form_string
    }
    
    # Add warnings
    if runs and runs[0] in ['7', '8', '9', '0', 'P', 'F', 'U']:
        analysis['warning'] = f"Poor last run: {runs[0]}"
        analysis['penalty_applied'] = True
    
    # Check for LTO winner
    if runs and runs[0] == '1':
        analysis['lto_winner'] = True
        analysis['boost'] = "LTO winner - quality signal"
    
    # Consistency check
    wins_recent = sum(1 for r in runs[:3] if '1' in r)
    places_recent = sum(1 for r in runs[:3] if any(c in r for c in ['1', '2', '3']))
    
    analysis['recent_wins'] = wins_recent
    analysis['recent_places'] = places_recent
    
    if places_recent >= 2:
        analysis['consistency'] = 'Good'
    elif places_recent == 1:
        analysis['consistency'] = 'Moderate'
    else:
        analysis['consistency'] = 'Poor'
    
    return total_score, analysis


def get_form_adjustment_for_confidence(form_string):
    """
    Get confidence score adjustment based on weighted form analysis
    
    Returns: adjustment (-30 to +30 points)
    """
    score, analysis = analyze_form_weighted(form_string)
    
    # Convert weighted score (0-100) to confidence adjustment (-30 to +30)
    # 50 is neutral
    adjustment = (score - 50) * 0.6  # Scale to -30 to +30 range
    adjustment = max(-30, min(30, adjustment))  # Cap at -30/+30
    
    return round(adjustment), analysis


if __name__ == '__main__':
    print("="*100)
    print("WEIGHTED FORM ANALYSIS - Testing")
    print("="*100)
    
    # Test cases based on Carlisle 14:00
    test_forms = [
        ('21312-7', 'Thank You Maam - our losing pick'),
        ('1P-335F', 'First Confession - winner we missed'),
        ('157-734', 'Della Casa Lunga - 2nd place'),
        ('1-1-1', 'Perfect recent form'),
        ('7-8-9', 'Terrible recent form'),
        ('2-3-2', 'Consistent placer'),
        ('1', 'Single LTO winner'),
        ('P-P-0', 'Very poor form'),
    ]
    
    for form, description in test_forms:
        print(f"\n{'-'*100}")
        print(f"Form: {form} ({description})")
        print('-'*100)
        
        score, analysis = analyze_form_weighted(form)
        adjustment, _ = get_form_adjustment_for_confidence(form)
        
        print(f"\nWeighted Score: {score:.1f}/100")
        print(f"Confidence Adjustment: {adjustment:+d} points")
        
        print(f"\nRun Breakdown:")
        for run in analysis.get('run_details', []):
            print(f"  {run['position']}. {run['result']:<10} Score: {run['score']:>4} x {run['weight']:.0%} = {run['contribution']:+.1f}")
        
        print(f"\nAnalysis:")
        print(f"  Last run: {analysis.get('last_run', 'N/A')}")
        print(f"  Recent wins: {analysis.get('recent_wins', 0)}")
        print(f"  Recent places: {analysis.get('recent_places', 0)}")
        print(f"  Consistency: {analysis.get('consistency', 'Unknown')}")
        
        if 'warning' in analysis:
            print(f"  [WARNING] {analysis['warning']}")
        
        if 'boost' in analysis:
            print(f"  [BOOST] {analysis['boost']}")
        
        # Show how it would affect confidence
        base_conf = 45
        adjusted_conf = base_conf + adjustment
        print(f"\nImpact on Confidence:")
        print(f"  Base: {base_conf}/100")
        print(f"  Adjusted: {adjusted_conf}/100 ({adjustment:+d})")
    
    print(f"\n{'='*100}")

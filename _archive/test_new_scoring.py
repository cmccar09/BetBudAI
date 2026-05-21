"""
Test new scoring weights on Plumpton 14:15 race to see if they fix the problem
"""
import sys
sys.path.insert(0, '.')
from fix_component_scores import (
    calculate_form_score, calculate_trainer_score, calculate_recent_performance_score,
    calculate_class_score, calculate_value_score
)

print("="*80)
print("TESTING NEW SCORING WEIGHTS ON PLUMPTON 14:15")
print("="*80)

horses = [
    {
        'name': 'Ferret Jeeter (WINNER)',
        'form': '69/1F13',
        'trainer': 'A J Honeyball',
        'odds': 5.0
    },
    {
        'name': 'Pachacuti (OUR PICK - 5th)',
        'form': '20-P3P2',
        'trainer': 'D Pipe',
        'odds': 3.15
    },
    {
        'name': 'Madajovy (2nd)',
        'form': '4P6572',
        'trainer': 'Dan Skelton',
        'odds': 5.5
    }
]

print("\nNEW SCORES with learning applied:\n")

for horse in horses:
    form_score = calculate_form_score(horse['form'])
    class_score = calculate_class_score(horse['odds'])
    trainer_score = calculate_trainer_score(horse['trainer'])
    value_score = calculate_value_score(horse['odds'])
    recent_perf = calculate_recent_performance_score(horse['form'])
    
    # Base scores (jockey, weight, distance, track, pace)
    base = 30  # Approximate
    
    total = form_score + class_score + trainer_score + value_score + recent_perf + base
    
    print(f"{horse['name']}")
    print(f"  Form: {horse['form']}")
    print(f"  Scores:")
    print(f"    Form: {form_score}/25 (was more important)")
    print(f"    Class: {class_score}/15")
    print(f"    Trainer: {trainer_score}/5 (was 10)")
    print(f"    Value: {value_score}/5")
    print(f"    Recent Perf: {recent_perf}/15 (was 10)")
    print(f"    Base scores: ~{base}/35")
    print(f"  TOTAL: {total}/100")
    print()

print("="*80)
print("ANALYSIS")
print("="*80)
print("\nExpected improvements:")
print("  - Ferret Jeeter (winner) should score HIGHER")
print("  - Pachacuti should score LOWER (pull-ups penalized)")
print("  - Recent wins matter more than trainer reputation")

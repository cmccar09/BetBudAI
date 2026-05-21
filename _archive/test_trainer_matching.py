#!/usr/bin/env python3
"""Test trainer name matching"""

from comprehensive_pick_logic import analyze_horse_comprehensive

print("Testing different trainer name formats:\n")

tests = [
    ("Jonjo O'Neill Jr.", "Jockey name format"),
    ("Jonjo & A.J. O'Neill", "Exact from race data"),
    ("Jonjo Oneill", "Alternate spelling"),
    ("A.J. O'Neill", "Just A.J."),
    ("J O Neill", "Short form")
]

for trainer, label in tests:
    horse = {
        'name': 'Largy Go',
        'odds': 2.625,
        'trainer': trainer,
        'form': ''
    }
    
    score, breakdown, reasons = analyze_horse_comprehensive(horse, 'Test')
    trainer_bonus = breakdown.get('trainer_reputation', 0)
    
    print(f"{label:30} \"{trainer:25}\" -> {score}/100 (trainer: {trainer_bonus}pts)")

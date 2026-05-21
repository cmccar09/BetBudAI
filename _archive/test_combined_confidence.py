#!/usr/bin/env python3
"""
test_combined_confidence.py - Test the Combined Confidence Rating calculation
"""

import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from save_selections_to_dynamodb import calculate_combined_confidence

def test_scenarios():
    """Test various betting scenarios"""
    
    print("=" * 80)
    print("COMBINED CONFIDENCE RATING - TEST SCENARIOS")
    print("=" * 80)
    
    # Scenario 1: Premium Bet (Very High Confidence)
    print("\n📌 SCENARIO 1: Premium Bet (Multiple Strong Signals)")
    print("-" * 80)
    scenario1 = pd.Series({
        'p_win': 0.35,
        'p_place': 0.68,
        'odds': 4.0,
        'confidence': 75
    })
    conf, grade, color, explanation, breakdown = calculate_combined_confidence(scenario1)
    print(f"Input: Win={scenario1['p_win']:.0%}, Place={scenario1['p_place']:.0%}, Odds={scenario1['odds']}, Research Conf={scenario1['confidence']}")
    print(f"\n🎯 RESULT: {conf}/100 - {grade}")
    print(f"Explanation: {explanation}")
    print(f"\nBreakdown:")
    print(f"  Win Component:        {breakdown['win_component']:.1f} pts (35% × 40)")
    print(f"  Place Component:      {breakdown['place_component']:.1f} pts (68% × 20)")
    print(f"  Edge Component:       {breakdown['edge_component']:.1f} pts (Market edge validated)")
    print(f"  Consistency Component: {breakdown['consistency_component']:.1f} pts (Signals align)")
    
    # Scenario 2: Safe Bet (High Confidence, Moderate Value)
    print("\n\n📌 SCENARIO 2: Safe Bet (High Certainty, Lower Value)")
    print("-" * 80)
    scenario2 = pd.Series({
        'p_win': 0.28,
        'p_place': 0.62,
        'odds': 3.5,
        'confidence': 70
    })
    conf, grade, color, explanation, breakdown = calculate_combined_confidence(scenario2)
    print(f"Input: Win={scenario2['p_win']:.0%}, Place={scenario2['p_place']:.0%}, Odds={scenario2['odds']}, Research Conf={scenario2['confidence']}")
    print(f"\n🎯 RESULT: {conf}/100 - {grade}")
    print(f"Explanation: {explanation}")
    print(f"\nBreakdown:")
    print(f"  Win Component:        {breakdown['win_component']:.1f} pts")
    print(f"  Place Component:      {breakdown['place_component']:.1f} pts")
    print(f"  Edge Component:       {breakdown['edge_component']:.1f} pts")
    print(f"  Consistency Component: {breakdown['consistency_component']:.1f} pts")
    
    # Scenario 3: Value Gamble (Good Value, Moderate Confidence)
    print("\n\n📌 SCENARIO 3: Value Gamble (High Edge, Lower Probability)")
    print("-" * 80)
    scenario3 = pd.Series({
        'p_win': 0.18,
        'p_place': 0.45,
        'odds': 8.0,
        'confidence': 40
    })
    conf, grade, color, explanation, breakdown = calculate_combined_confidence(scenario3)
    print(f"Input: Win={scenario3['p_win']:.0%}, Place={scenario3['p_place']:.0%}, Odds={scenario3['odds']}, Research Conf={scenario3['confidence']}")
    print(f"\n🎯 RESULT: {conf}/100 - {grade}")
    print(f"Explanation: {explanation}")
    print(f"\nBreakdown:")
    print(f"  Win Component:        {breakdown['win_component']:.1f} pts")
    print(f"  Place Component:      {breakdown['place_component']:.1f} pts")
    print(f"  Edge Component:       {breakdown['edge_component']:.1f} pts")
    print(f"  Consistency Component: {breakdown['consistency_component']:.1f} pts")
    
    # Scenario 4: Skip Bet (Weak Signals)
    print("\n\n📌 SCENARIO 4: Skip Bet (Weak/Conflicting Signals)")
    print("-" * 80)
    scenario4 = pd.Series({
        'p_win': 0.12,
        'p_place': 0.35,
        'odds': 5.0,
        'confidence': 25
    })
    conf, grade, color, explanation, breakdown = calculate_combined_confidence(scenario4)
    print(f"Input: Win={scenario4['p_win']:.0%}, Place={scenario4['p_place']:.0%}, Odds={scenario4['odds']}, Research Conf={scenario4['confidence']}")
    print(f"\n🎯 RESULT: {conf}/100 - {grade}")
    print(f"Explanation: {explanation}")
    print(f"\nBreakdown:")
    print(f"  Win Component:        {breakdown['win_component']:.1f} pts")
    print(f"  Place Component:      {breakdown['place_component']:.1f} pts")
    print(f"  Edge Component:       {breakdown['edge_component']:.1f} pts")
    print(f"  Consistency Component: {breakdown['consistency_component']:.1f} pts")
    
    # Scenario 5: Strong Favorite (Low Odds, High Probability)
    print("\n\n📌 SCENARIO 5: Strong Favorite (High Probability, Low Odds)")
    print("-" * 80)
    scenario5 = pd.Series({
        'p_win': 0.42,
        'p_place': 0.78,
        'odds': 2.5,
        'confidence': 85
    })
    conf, grade, color, explanation, breakdown = calculate_combined_confidence(scenario5)
    print(f"Input: Win={scenario5['p_win']:.0%}, Place={scenario5['p_place']:.0%}, Odds={scenario5['odds']}, Research Conf={scenario5['confidence']}")
    print(f"\n🎯 RESULT: {conf}/100 - {grade}")
    print(f"Explanation: {explanation}")
    print(f"\nBreakdown:")
    print(f"  Win Component:        {breakdown['win_component']:.1f} pts")
    print(f"  Place Component:      {breakdown['place_component']:.1f} pts")
    print(f"  Edge Component:       {breakdown['edge_component']:.1f} pts")
    print(f"  Consistency Component: {breakdown['consistency_component']:.1f} pts")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\n✅ All scenarios calculated successfully!")
    print("\nKey Insights:")
    print("• Very High (70+): Premium bets with aligned signals")
    print("• High (50-69): Solid bets with good fundamentals")
    print("• Moderate (35-49): Mixed signals, reduce stakes")
    print("• Low (0-34): Skip these bets")

if __name__ == '__main__':
    test_scenarios()

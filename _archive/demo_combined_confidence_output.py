#!/usr/bin/env python3
"""
demo_combined_confidence_output.py - Show how the new system displays
"""

import json

# Sample bet with combined confidence (what the system will generate)
sample_bet = {
    "bet_id": "demo_001",
    "timestamp": "2026-01-05T14:30:00Z",
    "date": "2026-01-05",
    
    # Core bet info
    "race_time": "2026-01-05T14:30:00Z",
    "course": "Cheltenham",
    "horse": "Pink Socks",
    "bet_type": "WIN",
    
    # Probabilities and odds
    "odds": 4.0,
    "p_win": 0.35,
    "p_place": 0.68,
    
    # Analysis
    "why_now": "Strong recent form with 2 wins in last 3 runs. Course specialist with 3 previous wins at Cheltenham. Class drop of 5 rating points makes this a solid value opportunity.",
    "tags": "course_specialist,class_drop,recent_winner,strong_form",
    "confidence": 75,  # Old research confidence
    "roi": 29.3,
    "recommendation": "BACK",
    
    # Decision Rating (existing)
    "decision_rating": "DO IT",
    "decision_score": 75.3,
    "rating_color": "green",
    
    # Combined Confidence Rating (NEW!)
    "combined_confidence": 71.2,
    "confidence_grade": "VERY HIGH",
    "confidence_color": "green",
    "confidence_explanation": "Multiple strong signals align - high conviction bet",
    "confidence_breakdown": {
        "win_component": 14.0,
        "place_component": 13.6,
        "edge_component": 16.0,
        "consistency_component": 18.4,
        "raw_signals": {
            "p_win": 0.35,
            "p_place": 0.68,
            "market_edge": 0.10,
            "consistency_score": 0.92
        }
    }
}

print("=" * 80)
print("SAMPLE BET OUTPUT - WITH COMBINED CONFIDENCE RATING")
print("=" * 80)
print()
print(f"🏇 {sample_bet['horse']}")
print(f"📍 {sample_bet['course']} | 14:30")
print(f"💰 Odds: {sample_bet['odds']}/1")
print()
print("─" * 80)
print("RATINGS")
print("─" * 80)
print()
print(f"📊 Decision Rating: {sample_bet['decision_score']} - {sample_bet['decision_rating']}")
print(f"   → Tells you: Should you bet? (value/ROI indicator)")
print()
print(f"🎯 Combined Confidence: {sample_bet['combined_confidence']}/100 - {sample_bet['confidence_grade']}")
print(f"   → Tells you: How confident are we? (prediction strength)")
print(f"   → {sample_bet['confidence_explanation']}")
print()
print("   Component Breakdown:")
print(f"   • Win Probability:    {sample_bet['confidence_breakdown']['win_component']:.1f} pts (35% × 40)")
print(f"   • Place Probability:  {sample_bet['confidence_breakdown']['place_component']:.1f} pts (68% × 20)")
print(f"   • Market Edge:        {sample_bet['confidence_breakdown']['edge_component']:.1f} pts (10% overlay)")
print(f"   • Signal Consistency: {sample_bet['confidence_breakdown']['consistency_component']:.1f} pts (92% agreement)")
print()
print("─" * 80)
print("DECISION MATRIX")
print("─" * 80)
print()
print(f"Decision Rating: {sample_bet['decision_rating']} (70+)")
print(f"Combined Confidence: {sample_bet['confidence_grade']} (70+)")
print()
print("Matrix Result: 💎 PREMIUM BET")
print("Recommended Stake: €30 (full stake)")
print()
print("─" * 80)
print("ANALYSIS")
print("─" * 80)
print()
print(f"Why Now: {sample_bet['why_now']}")
print()
print(f"Tags: {sample_bet['tags']}")
print()
print("=" * 80)
print()

# Show JSON structure
print("JSON STRUCTURE (sent to DynamoDB):")
print("=" * 80)
print(json.dumps(sample_bet, indent=2))
print()
print("=" * 80)
print("✅ System Ready!")
print("=" * 80)
print()
print("Next workflow run will:")
print("  1. Calculate combined confidence for each bet")
print("  2. Save to DynamoDB with all new fields")
print("  3. Display in frontend with blue badge")
print("  4. Provide component breakdown for transparency")
print()
print("Use the decision matrix to guide your stakes!")

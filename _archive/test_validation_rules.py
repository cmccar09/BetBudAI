# Test improved picking rules
import json

# Simulate yesterday's two losing picks
test_picks = [
    {
        "horse": "Bower Aoibhin",
        "confidence": 75,
        "p_win": 0.75,
        "odds": 1.33,
        "why_now": "Perfect recent form and lowest odds suggest best chance",
        "race_type": "greyhound",
        "enrichment_data": None,  # NO FORM DATA
        "combined_confidence": 67.4
    },
    {
        "horse": "Not So Steady",
        "confidence": 71,
        "p_win": 0.71,
        "odds": 1.41,
        "why_now": "Shortest odds and best chance to win based on recent performance patterns",
        "race_type": "greyhound",
        "enrichment_data": None,  # NO FORM DATA
        "combined_confidence": 65.3
    },
    {
        "horse": "Test Dog With Data",
        "confidence": 72,
        "p_win": 0.68,
        "odds": 1.5,
        "why_now": "Excellent win rate of 28% in last 20 races, trainer form strong",
        "race_type": "greyhound",
        "enrichment_data": {"win_percentage": 28, "place_percentage": 55},
        "combined_confidence": 68
    }
]

print("=" * 80)
print("TESTING IMPROVED VALIDATION RULES")
print("=" * 80)

for i, pick in enumerate(test_picks, 1):
    horse = pick["horse"]
    conf = pick["confidence"]
    has_data = bool(pick["enrichment_data"])
    combined = pick["combined_confidence"]
    reasoning = pick["why_now"].lower()
    
    print(f"\n[{i}] {horse} - {conf}% confidence")
    print(f"    Has enrichment data: {has_data}")
    print(f"    Combined confidence: {combined}%")
    print(f"    Reasoning: {reasoning[:80]}")
    
    # Apply validation rules
    rejected = False
    reason = ""
    
    # Rule 1: High confidence requires data
    if conf >= 60 and not has_data:
        rejected = True
        reason = "High confidence without form data"
    
    # Rule 2: Max 50% without data
    if not has_data and conf > 50:
        rejected = True
        reason = "Confidence exceeds 50% without form data"
    
    # Rule 3: Combined confidence threshold
    if combined < 50:
        rejected = True
        reason = f"Combined confidence {combined}% < 50%"
    
    # Rule 4: Shallow reasoning
    shallow = any(x in reasoning for x in ['lowest odds', 'shortest odds'])
    performance = any(x in reasoning for x in ['win rate', 'form', 'trainer'])
    
    if shallow and not performance and conf >= 60:
        rejected = True
        reason = "Shallow reasoning (odds-only)"
    
    if rejected:
        print(f"    Result: REJECTED - {reason}")
    else:
        print(f"    Result: VALID - Passed all rules")

print("\n" + "=" * 80)
print("EXPECTED RESULTS:")
print("  [1] Bower Aoibhin - REJECTED (high conf without data)")
print("  [2] Not So Steady - REJECTED (high conf without data)")
print("  [3] Test Dog With Data - VALID (has form data)")
print("=" * 80)

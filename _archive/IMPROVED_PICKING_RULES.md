# IMPROVED PICKING RULES - Based on Winner Analysis
# Generated: 2026-01-12

## Critical Finding: High-Confidence Losses Without Data

### Problem
- 2 high-confidence greyhound picks (75%, 71%) both lost
- Neither had external form data (GBGB enrichment)
- AI was picking favorites based only on odds
- Combined confidence system correctly lowered scores, but not enough

### Root Cause
AI overconfidence when picking without external validation:
1. Bower Aoibhin: 75% confidence → 67.4% combined (still picked, but LOST)
2. Not So Steady: 71% confidence → 65.3% combined (still picked, but LOST)

Both reasonings were shallow:
- "Perfect recent form and lowest odds" (no actual form data!)
- "Shortest odds and best chance" (just following market favorite)

## NEW RULES

### Rule 1: Require External Data for High Confidence
```
IF race_type == 'greyhound' AND confidence >= 60%:
    REQUIRE enrichment_data is not None
    IF no enrichment_data:
        REJECT pick (do not save to database)
        LOG: "Rejected - no form data to validate high confidence"
```

### Rule 2: Lower Confidence When Missing Data
```
IF race_type == 'greyhound' AND enrichment_data is None:
    confidence = confidence * 0.5  # Cut confidence in half
    max_confidence = 50%  # Cap at 50% without data
```

### Rule 3: Stricter Combined Confidence Threshold
```
Current: combined_confidence < 35% → Tag as BELOW_THRESHOLD
New: combined_confidence < 50% → REJECT entirely for greyhounds
     combined_confidence >= 70% → Required for "BET" recommendation
```

### Rule 4: Validate AI Reasoning Quality
```
IF "lowest odds" or "shortest odds" appears in reasoning:
    AND no specific form/performance data mentioned:
        FLAG as "SHALLOW_REASONING"
        Reduce confidence by 20%
```

## Implementation Priority

### HIGH PRIORITY (Implement Today)
1. Add validation check in greyhound workflow:
   - Before saving pick, check if enrichment_data exists
   - Reject picks with confidence > 60% if no enrichment

2. Update combined_confidence calculation:
   - More heavily penalize missing external data
   - Greyhounds without form: max 50% confidence

### MEDIUM PRIORITY (This Week)
3. Add reasoning quality check:
   - Parse AI response for shallow reasoning patterns
   - Flag picks that rely only on odds without performance data

4. Create feedback loop:
   - After each loss, check if it was due to missing data
   - Auto-adjust confidence penalties based on outcomes

## Expected Impact

With these rules applied to yesterday's picks:
- Bower Aoibhin (75% → REJECTED, no form data)
- Not So Steady (71% → REJECTED, no form data)
- Result: 2 fewer losses, saved 2 betting units

## Validation

Test on last 5 days of picks:
1. How many high-confidence losses had no external data?
2. Would these rules have prevented those losses?
3. What is the new expected win rate with stricter rules?

## Next Steps

1. Update `scheduled_greyhound_workflow.ps1`:
   - Add enrichment validation before database save
   
2. Update `generate_combined_confidence.py`:
   - Increase penalty for missing enrichment data
   - Add reasoning quality scoring

3. Create `validate_pick_quality.py`:
   - Run before saving any pick
   - Reject low-quality picks automatically

4. Monitor for 7 days:
   - Track rejection rate
   - Measure win rate improvement
   - Adjust thresholds if needed

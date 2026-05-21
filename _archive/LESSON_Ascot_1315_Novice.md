# LESSON LEARNED: Ascot 13:15 Novice Hurdle (Feb 14, 2026)

## Race Details
- **Venue:** Ascot
- **Time:** 13:15
- **Type:** 2m3f Nov Hrd (Novice Hurdle)
- **Class:** 2
- **Going:** Good to Soft (Soft in places)
- **Runners:** 6

## What Happened
**MY PICK:** Starzand (Form: 1-123, Marked BF favorite) - **CAME 4TH (LAST)**
**ACTUAL WINNER:** Mondouiboy (Form: 2-61, Ben Pauling trainer)

## Analysis Failures

### ❌ What Went Wrong

1. **Over-reliance on Favorite Status**
   - Starzand was marked BF (Betfair favorite)
   - Auto-boosted by +20pts (favorite_correction)
   - Ignored race-specific context (novice hurdle)

2. **Ignored Recent Bounce-Back Pattern**
   - Mondouiboy: Form 2-61 looked bad at first glance
   - BUT: Last 3 runs show 2-6-1 pattern
   - Actually indicates: Good run → Issue/fall → Recovery
   - Ben Pauling (quality trainer) backing the recovery

3. **Novice Race Dynamics Underestimated**
   - "Nov Hrd" = Novice Hurdle (less predictable than handicaps)
   - Form is less reliable
   - Horses still learning, improving rapidly
   - Favorites fail more often

4. **Short Form = Risk (WRONG in Novices)**
   - Kildinan Prince (Form: 2) came 2nd
   - Very short form dismissed as "risky"
   - In novice races: Limited form = improving horse, not inexperienced

5. **Ground Conditions Not Weighted**
   - "Good to Soft (Soft in places)" may have suited Mondouiboy
   - Starzand might prefer better ground
   - Didn't check going suitability adequately

## ✅ Fixes Implemented

### 1. Reduced Favorite Bias
```python
'favorite_correction': 12,  # Was 20 - reduced by 40%
```
**Impact:** Favorites get +12pts instead of +20pts
**Reasoning:** Don't auto-trust market without race context

### 2. Novice Race Penalty
```python
'novice_race_penalty': 15,  # NEW
```
**Detection:** Checks for 'nov', 'novice', 'maiden' in race name
**Impact:** All horses in novice races lose 15pts
**Result:** Lower confidence scores, less likely to bet

### 3. Bounce-Back Pattern Detection
```python
'bounce_back_bonus': 12,  # NEW
```
**Pattern:** Last 3 runs like 2-6-1 or 3-7-2
**Logic:** [Good] → [Bad] → [Better] = recovering horse
**Impact:** Mondouiboy would get +12pts for 2-6-1 pattern

### 4. Short-Form Improvement Bonus (Novice Only)
```python
'short_form_improvement': 10,  # NEW
```
**Trigger:** Form length ≤3 chars AND has a place (2nd/3rd) AND novice race
**Impact:** Kildinan Prince (Form: 2) gets +10pts
**Reasoning:** In novices, limited form = still improving

## Scoring Comparison

### BEFORE FIXES:
```
Starzand:
  + Sweet spot: 12pts (odds 2.5)
  + Recent win: 25pts (form 1-123)
  + Favorite correction: 20pts (BF favorite)
  + Elite trainer: 25pts (Hobbs)
  = 82pts → WOULD BET ❌

Mondouiboy:
  + Sweet spot: 15pts (odds ~5.0)
  + No recent win: 0pts
  + Trainer: 25pts (Ben Pauling)
  + Consistency: 4pts (two 2nds)
  = 44pts → REJECTED ❌
```

### AFTER FIXES:
```
Starzand:
  + Sweet spot: 12pts
  + Recent win: 25pts
  + Favorite correction: 12pts (reduced from 20)
  + Elite trainer: 25pts
  - Novice penalty: -15pts (NEW)
  = 59pts → MEDIUM CONFIDENCE ⚠️

Mondouiboy:
  + Sweet spot: 20pts (odds in sweet spot)
  + Bounce-back: 12pts (2-6-1 pattern) (NEW)
  + Trainer: 25pts
  + Consistency: 4pts
  - Novice penalty: -15pts (NEW)
  = 46pts → LOW CONFIDENCE (but closer)
```

## Key Takeaways

1. **Novice races need lower confidence** - Applied -15pt penalty
2. **Favorites fail more in novices** - Reduced favorite bonus
3. **Bounce-back patterns matter** - 2-6-1 now gets +12pts
4. **Short form ≠ risky in novices** - Limited data might = improving
5. **Always check race type** - Handicaps ≠ Novices ≠ Maiden

## Impact on Future Picks

- Novice races will score 10-15pts lower overall
- Less likely to recommend betting on novice races
- Bounce-back horses get recognition
- Favorites don't get auto-trust
- Short-form horses in novices won't be auto-rejected

## Next Steps

1. ✅ Updated comprehensive_pick_logic.py with all 4 fixes
2. ⏳ Monitor next novice race performance
3. ⏳ Track if bounce-back pattern proves reliable
4. ⏳ Consider adding ground suitability checks (soft vs good vs heavy)

---

**Lesson Date:** February 14, 2026
**Applied By:** Comprehensive Pick Logic v2.1
**Status:** ACTIVE in all workflows

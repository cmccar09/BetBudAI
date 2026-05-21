# HIGH CONFIDENCE FILTER - UI QUALITY CONTROL

## Overview
The UI now displays ONLY the highest quality picks to maximize user confidence and results.

## Confidence Levels

Based on comprehensive analysis score (0-100 points):

- **90-100 pts: VERY HIGH** ⭐⭐⭐
  - All 7 factors align perfectly
  - Show on UI ✓
  - Maximum confidence

- **75-89 pts: HIGH** ⭐⭐
  - Strong across multiple factors
  - Show on UI ✓
  - High probability picks

- **60-74 pts: MEDIUM** ⭐
  - Meets minimum standards
  - Hidden from UI ✗
  - Learning data only

- **Below 60 pts: LOW**
  - Does not meet standards
  - Rejected completely ✗
  - Not added to database

## UI Filtering Rules

### 1. Confidence Filter
- **Minimum score: 75/100** (HIGH confidence)
- Only HIGH and VERY HIGH picks visible on UI
- MEDIUM picks (60-74) hidden but tracked for learning

### 2. Quantity Limit
- **Maximum: 10 picks per day**
- Sorted by comprehensive score (highest first)
- Best quality picks only

### 3. Additional Filters
- `show_in_ui = True` (set automatically for score >= 75)
- Future races only (race_time > now)
- No "Unknown" courses or horses
- Actual betting picks only (no learning data, analyses)

## Why This Matters

### Before (60+ minimum):
- UI showed ALL picks meeting minimum standards
- Mix of MEDIUM and HIGH quality
- Some picks only marginally above threshold
- User had to evaluate which picks were best

### After (75+ minimum):
- UI shows ONLY top-tier picks
- All picks are HIGH or VERY HIGH quality
- Maximum 10 per day ensures curation
- User sees pre-filtered best selections

## Example: Today's Picks

**Market House @ 5.9 - Score 93/100 (VERY HIGH)**
- Form: 112215- (excellent)
- Sweet spot: ✓ 30pts
- Optimal odds: 15pts
- Recent wins: 25pts (three 1sts)
- Total wins: 15pts
- Consistency: 8pts
- **Result: APPROVED - Show on UI**
- Outcome: LOSS (5th place) - unlucky but correctly identified as quality pick

**Crimson Rambler @ 4.0 - Score 47/100 (LOW)**
- Form: 0876- (terrible)
- Sweet spot: ✓ 30pts
- Optimal odds: 17pts
- Recent wins: 0pts (no wins)
- Total wins: 0pts
- Consistency: 0pts
- **Result: REJECTED - Not added to database**
- Would have prevented bad bet

**Hypothetical: Score 68/100 (MEDIUM)**
- Form: 3421- (decent)
- Sweet spot: ✓ 30pts
- Optimal odds: 10pts
- Recent wins: 25pts (one recent win)
- Total wins: 3pts
- **Result: Added to database but HIDDEN from UI**
- Tracked for learning, not shown to users

## Implementation

### Lambda Function (lambda_function.py)
```python
# Filter 1: show_in_ui=True only
# Filter 2: comprehensive_score >= 75 (HIGH confidence)
# Filter 3: race_time > now (future races)
# Filter 4: Sort by score descending, limit to 10
```

### API Server (api_server.py)
- Same filtering as Lambda
- Ensures consistency across environments

### Comprehensive Logic (comprehensive_pick_logic.py)
```python
# Confidence level assignment:
if score >= 90:
    confidence_level = "VERY_HIGH"
    show_in_ui = True
elif score >= 75:
    confidence_level = "HIGH"
    show_in_ui = True
elif score >= 60:
    confidence_level = "MEDIUM"
    show_in_ui = False  # Hidden from UI
else:
    # Not added to database at all
```

## Database Fields

New fields added to DynamoDB records:

- `confidence_level`: "VERY_HIGH" | "HIGH" | "MEDIUM" | "LOW"
- `comprehensive_score`: Decimal (0-100)
- `show_in_ui`: Boolean (True only if score >= 75)

## Benefits

1. **Quality Control**: Only best picks visible to users
2. **Reduced Noise**: Maximum 10 picks per day prevents overwhelm
3. **Learning Continuity**: MEDIUM picks still tracked for analysis
4. **User Confidence**: Every UI pick is HIGH quality minimum
5. **Better Results**: Focus on highest probability outcomes

## Monitoring

To check current filtering:
```python
python check_today_picks.py  # Shows UI visible picks (score >= 75)
python check_all_picks.py    # Shows all picks including hidden (score >= 60)
```

## Next Steps

1. Deploy updated Lambda function
2. Test with live race data
3. Monitor HIGH confidence pick performance
4. Adjust score threshold if needed (currently 75/100)
5. Consider dynamic threshold based on daily race quality

---

**Created:** 2026-02-02
**Status:** Active
**Threshold:** 75/100 (HIGH confidence minimum)
**Limit:** Maximum 10 picks per day

# Odds Sweet Spot Implementation (Jan 30, 2026)

## Problem Identified

Analysis of 70 bets (Jan 22-29) revealed **100% of longshot bets lost**:

| Odds Range | Bets | Wins | Win Rate | Result |
|------------|------|------|----------|--------|
| 2.0-8.0/1  | 35   | 10   | **28.6%** | ✅ PROFITABLE |
| 8.0-15.0/1 | 10   | 0    | **0%**    | ❌ TOTAL LOSS |
| 15-30/1    | 7    | 0    | **0%**    | ❌ TOTAL LOSS |
| 30+/1      | 15   | 0    | **0%**    | ❌ TOTAL LOSS |

**32 longshot bets = £0 return = Complete waste**

## Solution Implemented

### 1. Quality Filter Added
**File:** [save_selections_to_dynamodb.py](save_selections_to_dynamodb.py#L1008-L1013)

```python
# Rule 0: SWEET SPOT ODDS RANGE (2.0 to 8.0 only)
# Historical data shows: 2-8/1 = 28.6% win rate, 8+/1 = 0% win rate
if odds < 2.0 or odds > 8.0:
    print(f"REJECTED: {horse} - Odds {odds:.1f}/1 outside sweet spot (2.0-8.0/1 only)")
    validation_rejected += 1
    continue
```

### 2. AI Prompt Updated
**File:** [prompt.txt](prompt.txt)

Added mandatory odds guidance:
- **ONLY select horses with odds 2.0-8.0/1**
- Historical evidence showing 0% win rate on longshots
- Instructions to avoid being tempted by high odds

### 3. Expected Impact

**Before (Yesterday Jan 29):**
- 12 bets placed
- 0 wins from staked bets (Secret History won but had £0 stake)
- Heavy longshot exposure (11/1, 22/1, 55/1, 80/1 odds)

**After (With Filters):**
- Only horses in 2-8/1 range considered
- Expected win rate: ~28.6% (based on historical sweet spot)
- Eliminates 32 guaranteed-losing longshots

## How It Works

### Selection Process
1. Betfair fetches live odds
2. Claude analyzes races with odds sweet spot guidance
3. save_selections_to_dynamodb.py filters selections:
   - ✅ Odds 2.0-8.0/1: KEEP
   - ❌ Odds <2.0 or >8.0: REJECT
4. Only validated picks saved to database

### Why This Range?

**2.0/1 (3.0 decimal) to 8.0/1 (9.0 decimal)** represents:
- **Not favorites:** Avoid over-bet short-priced horses
- **Not outsiders:** Avoid rank no-hopers
- **Competitive horses:** Real chance based on form
- **Value odds:** Decent returns when winning

## Testing the Fix

Run workflow and check rejection messages:

```powershell
.\scheduled_workflow.ps1
```

You should see:
```
REJECTED: Blue Train - Odds 55.0/1 outside sweet spot (2.0-8.0/1 only)
REJECTED: Spring Serenade - Odds 80.0/1 outside sweet spot (2.0-8.0/1 only)
```

## Performance Metrics to Track

Monitor these after 1 week:

1. **Average odds of placed bets** - Should be 2-8/1 range
2. **Win rate** - Target 25-30% (vs current 8.3% yesterday)
3. **ROI** - Should turn positive with fewer wasted bets
4. **Rejection rate** - Expect 40-60% of AI picks filtered out

## Next Steps

1. ✅ **Implemented** - Odds filter in quality validation
2. ✅ **Updated** - AI prompt with sweet spot guidance
3. ⏳ **Testing** - Run next workflow (manual or scheduled)
4. ⏳ **Monitor** - Track performance over next 7 days
5. ⏳ **Adjust** - May tighten to 3-7/1 if data supports it

---

**Implementation Date:** 2026-01-30  
**Historical Basis:** 70 bets (Jan 22-29)  
**Files Modified:** 2 (save_selections_to_dynamodb.py, prompt.txt)

# Featured Meeting Discrepancy Analysis

**Date**: May 20, 2026  
**Featured Course**: Gowran Park  
**Issue**: User's featured meeting page shows different picks than what's in DynamoDB

---

## User's Featured Meeting Page Shows:

| Race | Pick | Odds | Result (per user) |
|------|------|------|-------------------|
| 17:10 | Gloriously Glam | 4/1 | WIN |
| 17:45 | Sanctijude | 9/4 | WIN |
| 18:20 | Rolltight | 11/8 | LOST |
| 18:50 | Ballymagreehan | 8/1 | LOST |
| 19:20 | Lady Mairen | EVS | LOST |

---

## What's Actually in DynamoDB:

### 17:10 Gowran Park
**Picks in database:**
- Ardad Steve (score: 16)
- Bassrah (score: 13)
- Boysofwallstreet (score: 1)
- Conciliate (score: 3)
- Easy Answer (score: 0)
- Peaceful Warrior (score: 8)
- Prince Kameo (score: -6)
- Rogue Imperial (score: 1)

**Gloriously Glam NOT in our picks!** 
- Yet we have a record of it winning (from earlier update)
- Bet ID: 2026-05-20_GOWRAN_17:10_56134859
- We manually added this winner earlier

### 17:45 Gowran Park
**No picks found in database for this time**
- Sanctijude not in our system

### 18:20 Gowran Park
**Picks in database:**
- Lady Mairen (score: 108) - Result: LOSS
- Marmeladova (score: 65) - Result: LOSS
- Sparan Nua (score: 32) - Result: LOSS
- Vauntingly (score: 18) - Result: LOSS

**Rolltight NOT in our picks!**
- User says we picked Rolltight (lost)
- But we actually picked Lady Mairen, Marmeladova, Sparan Nua, Vauntingly
- All correctly marked as LOSS (Rolltight won the race at 11/10f)

### 18:50 Gowran Park
**No picks found in database**
- Ballymagreehan not in our system
- (Ballymagreehan won at 4/1, not 8/1 as user stated)

### 19:20 Gowran Park
**No picks found in database for this exact time**
- Lady Mairen appears at 18:20, not 19:20
- This is a data error in user's featured meeting page

---

## Root Cause Analysis

### Problem 1: Featured Meeting Page Not Synced with DynamoDB
The user's featured meeting page is showing picks that don't exist in DynamoDB:
- Sanctijude (17:45) - not in database
- Rolltight (18:20) - not in database
- Ballymagreehan (18:50) - not in database

### Problem 2: Gloriously Glam Discrepancy
- We manually added Gloriously Glam as a winner earlier
- But it wasn't in our original picks
- Bet ID format: 2026-05-20_GOWRAN_17:10_56134859 (different from other bet IDs)

### Problem 3: Lady Mairen Time Confusion
- User shows Lady Mairen at 19:20
- Database shows Lady Mairen at 18:20
- These are likely the same pick with wrong time on featured page

### Problem 4: Early LOSS Marking
- 18:20 races were marked LOSS at 17:37 (before they ran)
- This suggests results were being fetched incorrectly
- Or the results system pulled wrong data

---

## What Actually Happened (Best Reconstruction)

### Actual Race Winners:
1. **17:10** - Gloriously Glam won at 9/2 (we added this manually)
2. **17:45** - Sanctijude won at 9/4 (not in our picks)
3. **18:20** - Rolltight won at 11/10f (not in our picks)
4. **18:50** - Ballymagreehan won at 4/1 (not in our picks)

### Our Actual Picks:
1. **17:10** - Multiple horses (Ardad Steve, Bassrah, etc.) - None won
   - Exception: Gloriously Glam was manually added as winner
2. **17:45** - NO PICKS (no data in database)
3. **18:20** - Lady Mairen, Marmeladova, Sparan Nua, Vauntingly - ALL LOST
4. **18:50** - NO PICKS (no data in database)
5. **19:20** - NO PICKS (no data in database)

---

## Critical Issues to Fix

### Issue 1: Featured Meeting Page Source
**Problem**: Featured meeting page is displaying picks that don't exist in DynamoDB

**Possible Causes**:
- Featured meeting page queries a different table/source
- Caching issue showing stale data
- Manual entry on featured page not synced with main database
- Frontend bug constructing featured picks incorrectly

**Fix**: Identify where featured meeting page gets its data

### Issue 2: Results Timing
**Problem**: Races marked LOSS before they ran (at 17:37 for 18:20 races)

**Possible Causes**:
- Results fetch job running too early
- Wrong race IDs being matched
- Time zone confusion
- Cached results from previous day

**Fix**: Check results fetch Lambda timing and race ID matching

### Issue 3: Gloriously Glam Manual Entry
**Problem**: We manually added a winner that wasn't in original picks

**Impact**: ROI calculations now include a winner we didn't actually pick

**Fix**: Verify if Gloriously Glam was actually in our original 08:30 picks

---

## ROI Impact

### If User's Featured Meeting Page is Correct:
- 5 picks total
- 2 winners (Gloriously Glam 5.0, Sanctijude 3.25)
- 3 losers
- Stake: £5.00
- Returns: £8.25
- Profit: +£3.25
- ROI: +65%

### If DynamoDB Data is Correct:
- Only Gloriously Glam verified as our pick and winner
- Lady Mairen, Marmeladova, Sparan Nua, Vauntingly all lost at 18:20
- Total: 5 picks, 1 winner, 4 losers
- Stake: £5.00
- Returns: £5.00 (from Gloriously Glam at 5.0)
- Profit: £0.00
- ROI: 0%

---

## Immediate Actions Required

1. **Verify Featured Meeting Data Source**
   - Where does the featured meeting page pull picks from?
   - Is it DynamoDB or another source?

2. **Check Morning Pipeline Logs**
   - What picks were generated at 08:30 for Gowran Park?
   - Was Sanctijude included?
   - Was Rolltight included?

3. **Fix Results Timing Bug**
   - Why were 18:20 races marked LOSS at 17:37?
   - Check results-fetch Lambda logs
   - Verify race ID matching logic

4. **Correct Featured Meeting Display**
   - Remove picks that don't exist in DynamoDB
   - Or add missing picks to DynamoDB if they were legitimate

5. **Recalculate Today's ROI**
   - Based on actual picks in DynamoDB
   - Not based on featured meeting page display

---

## Questions for User

1. Where does the featured meeting page get its data?
2. Were Sanctijude, Rolltight, and Ballymagreehan ever in the system?
3. Is the featured meeting page manually curated or auto-generated?
4. Should featured meeting picks be a subset of main picks or separate?

---

**Status**: Data integrity issue identified  
**Priority**: HIGH - affects user trust and ROI accuracy  
**Next Step**: Identify featured meeting page data source

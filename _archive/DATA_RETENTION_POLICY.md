# Data Retention Policy

## Overview
**CRITICAL:** Historical betting data is NEVER deleted from DynamoDB. This data is essential for AI learning and performance analysis.

## Why Keep Historical Data?

### 1. AI Learning System
The betting system uses historical results to:
- Analyze which strategies work (40% win rate on "Recent win" pattern)
- Calibrate probability predictions (currently 19.4% actual vs 21.7% predicted)
- Identify failing patterns and adjust selections
- Build confidence scoring models

**Deleting old data destroys the learning foundation.**

### 2. Performance Tracking
- Historical strike rates: 19.4% (Jan 3-29, 186 bets)
- Recent performance trends: Week-over-week comparisons
- ROI calculations require complete bet history
- Learning insights based on 186+ bets, not just last week

### 3. What Happened When Data Was Deleted

**Jan 22, 2026:** Cleanup script ran, deleting all bets before Jan 22
- **Lost:** 116 bets from Jan 3-21
- **Impact:** Learning system now has 70 bets instead of 186
- **Result:** Performance degraded from 19.4% to 17% win rate

## Current System Design

### UI Filtering (CORRECT APPROACH)
The API endpoints **automatically filter past races** without deleting data:

```python
# In lambda_api_picks.py - get_today_picks()
now = datetime.utcnow()
future_picks = []

for item in horse_items:
    race_time = datetime.fromisoformat(item['race_time'])
    if race_time > now:  # Only show upcoming races
        future_picks.append(item)
```

**Result:** Users see only upcoming races, but historical data remains in database.

### Endpoints Behavior
- `/api/picks/today` - Shows only FUTURE races (race_time > now)
- `/api/results/today` - Shows ALL today's races for P&L calculation
- `/api/picks/yesterday` - Shows previous day's races with outcomes

## Disabled Scripts

### ⛔ cleanup_old_picks.py
**Status:** DISABLED  
**Reason:** Deleted past races from database  
**Impact:** Destroyed 116 bets of learning history  
**Replacement:** API filtering by race_time

### ⛔ clear_old_data.ps1
**Status:** DISABLED  
**Reason:** Removed test data AND historical bets  
**Impact:** Lost all bets before Jan 22  
**Replacement:** API filtering by race_time

### ✅ cleanup_duplicate_races.py
**Status:** SAFE TO USE  
**Reason:** Only removes duplicate picks for same race  
**Impact:** Ensures 1 pick per race (quality control)

## Data Lifecycle

```
NEW BET
   ↓
SAVED TO DYNAMODB (bet_date, bet_id, race_time)
   ↓
SHOWN ON UI (if race_time > now)
   ↓
RACE COMPLETES
   ↓
HIDDEN FROM UI (race_time in past)
   ↓
RESULTS FETCHED (outcome: win/loss/place)
   ↓
LEARNING ANALYSIS (evaluate_performance.py)
   ↓
KEPT FOREVER (used for AI learning)
```

## Current Database Stats (Jan 30, 2026)

- **Total bets with results:** 70
- **Date range:** Jan 22-29 (8 days)
- **Data lost:** 116 bets from Jan 3-21
- **Learning insights:** Based on 186 bets (includes deleted data snapshot in learning_insights.json)

## Recommendations

### DO:
- ✅ Keep all historical betting data indefinitely
- ✅ Use API race_time filtering for UI display
- ✅ Run learning analysis on complete history
- ✅ Monitor database size (DynamoDB auto-scales)
- ✅ Export data monthly to S3 for backup

### DON'T:
- ❌ Delete old bets from DynamoDB
- ❌ Run cleanup_old_picks.py
- ❌ Run clear_old_data.ps1
- ❌ Filter historical data from learning analysis
- ❌ Set TTL (Time To Live) on DynamoDB items

## Database Cost Impact

**Current scale:**
- 70 bets = ~35KB of data
- 1000 bets/month × 12 months = 6MB/year
- DynamoDB free tier: 25GB storage

**Cost:** Effectively FREE for years of historical data.

## If Cleanup Is Needed

Only clean up:
1. **Test data** - Horses like "Golden Spirit", "Silver Thunder" (obvious test entries)
2. **Duplicate picks** - Use cleanup_duplicate_races.py (keeps best pick per race)
3. **Failed saves** - Bets with null/invalid required fields

**NEVER delete:**
- Bets with outcome data (win/loss/place)
- Bets older than X days "just because"
- Bets shown on UI before race time

## Restoring Lost Data

Unfortunately, the 116 deleted bets (Jan 3-21) cannot be recovered unless:
1. DynamoDB backups exist (check AWS console)
2. CSV exports in history/ folder contain the data
3. learning_insights.json aggregates can provide partial statistics

## Monitoring

Track these metrics weekly:
- Total bets in database
- Oldest bet date
- Learning insights sample size
- Win rate trends (should be based on full history)

---

**Last Updated:** Jan 30, 2026  
**Policy Owner:** System Administrator  
**Review Frequency:** Quarterly

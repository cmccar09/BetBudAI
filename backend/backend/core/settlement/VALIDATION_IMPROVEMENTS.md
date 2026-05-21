# Settlement Validation Improvements
**Date**: 2026-05-21  
**Issue**: Evocative Spark (15:10 Catterick) incorrectly marked as LOSS with phantom winner "The Tunguska Event"

## Root Cause
The settlement fetcher matched against the **WRONG RACE** - assigning results from a different race to Catterick 15:10. All 7 horses were marked finish_position=6 with the same phantom winner.

## Validation Enhancements Added

### 1. Winner Must Exist in Original Race Lineup
**Location**: `sl_results_fetcher.py:593-610`

Before accepting any result, validates that the winner exists in the `all_horses` field from the original race analysis.

```python
all_horses_in_race = pick.get('all_horses', [])
runner_names = [norm(h.get('horse', '')) for h in all_horses_in_race]
winner_normalized = norm(winner)

if runner_names and winner_normalized not in runner_names:
    print(f"[ERROR] Winner '{winner}' NOT in original race lineup")
    print(f"        Matched result may be from WRONG RACE - SKIPPING")
    continue
```

**Impact**: Prevents accepting results from different races entirely. Would have blocked the Tunguska Event error immediately.

---

### 2. Cross-Check Winner with Betfair Market
**Location**: `sl_results_fetcher.py:687-702`

When Betfair market data is available, cross-validates that the winner exists in the Betfair market runners.

```python
betfair_runners = [name for name, sp in bf_sp_map.items() if sp and sp > 0]
if betfair_runners:
    winner_in_betfair = any(norm(name) == winner_normalized for name in betfair_runners)
    if not winner_in_betfair:
        print(f"[WARN] Winner '{winner}' not found in Betfair market")
        print(f"       This may indicate wrong race matched")
    else:
        print(f"[✓] Winner '{winner}' confirmed in Betfair market")
```

**Impact**: Provides second-source validation. Even if Sporting Life data is wrong, Betfair cross-check flags the issue.

---

### 3. Post-Settlement Integrity Check
**Location**: `sl_results_fetcher.py:852-892`

After all picks are settled, scans for data anomalies:

**Check A**: All horses in same race have identical finish position (impossible)  
**Check B**: Multiple different winners recorded for same race (impossible)

```python
# Group by race (course + time)
for race_key, data in races_check.items():
    positions = data['positions']
    winners = data['winners']
    
    # All horses same position?
    if len(positions) > 1 and len(set(positions)) == 1:
        print(f"[ALERT] Data corruption detected")
        print(f"        All {len(horses)} horses marked as position {positions[0]}")
        anomalies_found = True
    
    # Multiple winners?
    if len(winners) > 1:
        print(f"[ALERT] Inconsistent winner data")
        print(f"        Multiple winners: {winners}")
        anomalies_found = True
```

**Impact**: Would have immediately detected the Catterick bug where all 7 horses showed position=6 and winner="The Tunguska Event".

---

### 4. Enhanced Audit Logging
**Location**: `sl_results_fetcher.py:347, 596`

Improved logs to trace race matching:

```python
# When result found:
race_id = (fr.get('race_reference') or {}).get('id', 'unknown')
print(f"[fast] {off_time} {course} → {winner} | Placed: {runners[:4]} | Race ID: {race_id}")

# When matched to pick:
print(f"[MATCH] {horse} @ {course} {actual_off} | Source: {matched_source} | Winner: {winner}")
```

**Impact**: Clear audit trail showing which race was matched and from which source (fast-results vs HTML fallback).

---

## Testing & Deployment

- **Deployed**: 2026-05-21 15:26 UTC to `surebet-sl-results` Lambda
- **Next Execution**: Automatic at next results fetch (30min schedule)
- **Validation Status**: All 4 checks will run on every settlement

## Prevention Summary

| Scenario | Prevention Mechanism |
|----------|---------------------|
| Wrong race matched | ✅ Check #1: Winner must be in original lineup |
| Different course/time | ✅ Check #1 + Enhanced logging |
| Parsing error | ✅ Check #3: Detect duplicate positions |
| Data corruption | ✅ Check #3: Post-settlement scan |
| Single source failure | ✅ Check #2: Betfair cross-validation |

## Manual Corrections Applied

- **Evocative Spark**: Updated to WIN, finish_position=1, profit=+18pts
- **Moostar**: Updated to 2nd, finish_position=2, profit=+3pts (each-way)

Both horses now correctly reflect the actual 15:10 Catterick result.

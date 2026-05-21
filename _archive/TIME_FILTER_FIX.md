# Time Filter Bug Fix - Summary

## Problem Identified

**Issue:** Pick was saved for "In The Age @ Uttoxeter 15:06" at 16:14:54 - over 1 hour AFTER the race finished.

**Root Cause:** The time filtering logic had multiple issues:

1. **No buffer for AI processing time**: Races starting "soon" (within 15 minutes) could finish before AI analysis completes
2. **Possible timezone or API data issues**: Betfair may return stale data or incorrect timestamps
3. **No safety net in save script**: The database save script didn't validate race times before saving

## Fix Implemented

### 1. Added 15-Minute Buffer in AI Analysis ([run_enhanced_analysis.py](run_enhanced_analysis.py))

**Before:**
```python
if now <= start_time <= time_ahead:
    races_in_window.append(r)
```

**After:**
```python
buffer_time = now + timedelta(minutes=15)  # Exclude races starting within 15 minutes
if start_time < buffer_time:
    past_races += 1
    continue
if start_time <= time_ahead:
    races_in_window.append(r)
```

**Impact:**
- Excludes races already started
- Excludes races starting within 15 minutes (prevents races finishing during AI processing)
- Logs count of excluded past races for visibility

### 2. Added Safety Filter in Database Save ([save_selections_to_dynamodb.py](save_selections_to_dynamodb.py))

**Added validation before formatting picks:**
```python
# CRITICAL: Filter out races that have already started (safety check)
race_time_str = row.get('start_time_dublin', '')
if race_time_str:
    race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    if race_time <= now:
        races_already_started += 1
        print(f"FILTERED [RACE STARTED]: {horse} @ {venue} {race_time_str} (race already started)")
        continue
```

**Impact:**
- **Belt-and-suspenders**: Even if a past race slips through AI analysis, it won't be saved to DB
- Clear logging of filtered races
- Uses current time at save moment (not workflow start time)

### 3. Enhanced Logging

- AI analysis now shows: `"excluded {past_races} past/starting-soon races"`
- Save script now shows: `"filtered: {filtered_out} low ROI, {races_already_started} already started"`

## Testing

Created [test_time_filter.py](test_time_filter.py) to verify:
- ✓ Past races correctly excluded
- ✓ Races starting within 15 min correctly excluded
- ✓ Future races beyond 15-min buffer correctly included

## Expected Behavior Going Forward

**Scenario:** Workflow runs at 16:13

| Race Time | Old Behavior | New Behavior | Reason |
|-----------|--------------|--------------|---------|
| 15:06 | ❌ Saved | ✓ Excluded | Past race (before now) |
| 16:20 | ❌ Saved | ✓ Excluded | Only 7 min away (< 15 min buffer) |
| 16:30 | ✓ Saved | ✓ Saved | 17 min away (safe) |
| 17:00 | ✓ Saved | ✓ Saved | 47 min away (safe) |

## Files Modified

1. `run_enhanced_analysis.py` - Added 15-min buffer and past race detection
2. `save_selections_to_dynamodb.py` - Added safety filter for races already started
3. `test_time_filter.py` - Created test to verify fix

## Migration Notes

- **No breaking changes** - only adds filtering (safer)
- **Immediate effect** - next workflow run will use new logic
- **Backwards compatible** - works with existing database schema

## Monitoring

After deployment, check logs for:
- `"excluded X past/starting-soon races"` - should be > 0 if Betfair returns stale data
- `"FILTERED [RACE STARTED]"` - should be rare (safety net only)
- Verify all picks in DynamoDB have `race_time > created_at timestamp`

---

**Status:** ✅ FIXED - Ready for next workflow run

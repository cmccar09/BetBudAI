# Fix Picks Count

> **Purpose:** Diagnose and fix the pick count displayed to users. The extended picks cap (2 weekday / 4 weekend) is enforced in three layers — pipeline, API, and frontend. All three must agree or users will see too many or too few picks.

## Usage

```
/fix-picks-count
```

---

## Current rules (as of 2026-07-20)

| Day | Main UI picks | Extended picks | Total max |
|---|---|---|---|
| Mon–Fri (weekday) | 2 | 2 | 4 |
| Sat–Sun (weekend) | 2 | 4 | 6 |

---

## Step 1 — Check what's currently showing

Pull today's picks from DynamoDB and count by pick_type:

```bash
TODAY=$(date +%Y-%m-%d)
aws dynamodb query --table-name SureBetBets \
  --key-condition-expression "bet_date = :d" \
  --expression-attribute-values "{\":d\":{\"S\":\"$TODAY\"}}" \
  --projection-expression "bet_id, pick_type, COMPREHENSIVE_SCORE, show_in_ui" \
  --region eu-west-1 \
  --output json | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d.get('Items', [])
ui    = [i for i in items if i.get('show_in_ui',{}).get('BOOL')]
ext   = [i for i in items if i.get('pick_type',{}).get('S') == 'extended']
print(f'Main UI picks:  {len(ui)}')
print(f'Extended picks: {len(ext)}')
print(f'Total:          {len(ui) + len(ext)}')
for i in ext:
    print('  EXT:', i.get('bet_id',{}).get('S','?'))
"
```

---

## Step 2 — Find where the cap is set

The cap lives in **three places** — all must match:

### A. Pipeline (source of truth — controls what gets stored)
**File:** `complete_daily_analysis.py`
**Line ~1127:**
```python
_MAX_EXT_PICKS = 4 if now_utc.weekday() >= 5 else 2
```
`weekday() >= 5` = Saturday (5) or Sunday (6).

### B. API endpoint (caps what gets returned from DynamoDB)
**File:** `backend/api/lambda_function.py`
**Function:** `get_extended_picks()` (~line 1664)
```python
_max_ext = 4 if _is_weekend else 2
...
extended = extended[:_max_ext]
```
This is the **immediate fix** — changing this caps picks for today's already-stored data without waiting for tomorrow's pipeline run.

### C. Frontend (final display cap)
**File:** `frontend/src/App.js`
Two places:

1. **Live Opportunities section** (~line 3045–3046):
```javascript
const isWeekend = [0, 6].includes(new Date().getDay());
const maxPicks = isWeekend ? 4 : 2;
```
Note: JS `getDay()` = 0 (Sunday) to 6 (Saturday). Weekend = 0 or 6.

2. **YesterdayResultsView extended merge** (~line 3248–3250):
```javascript
const _todayIsWeekend = [0, 6].includes(new Date().getDay());
const _maxExtToday = _todayIsWeekend ? 4 : 2;
const extendedToday = (extTodayData?.success ? extTodayData.picks || [] : [])
  .filter(p => !p.is_dropped)
  .slice(0, _maxExtToday)
  ...
```

---

## Step 3 — Fix and deploy

If the numbers are wrong, update all three layers to match the target caps, then:

```powershell
# Rebuild and deploy the analysis Lambda (if pipeline change)
.\scripts\build_analysis_lambda.ps1

# Deploy API Lambda (if API change)
.\scripts\deploy_api.ps1

# Build and deploy frontend (if frontend change)
cd frontend && npm run build && cd ..
npx wrangler pages deploy frontend/build --project-name betbudai --branch main
```

---

## Known gotchas

- **Pipeline change only affects tomorrow** — if today's run already stored 3 extended picks, the API cap (Step B) is the only way to fix the count for today without manually deleting DynamoDB items.
- **API returns `score` AND `comprehensive_score`** — both fields must be present in `get_extended_picks()` response. If `comprehensive_score` is missing, the rating badge (ELITE / STRONG / GOOD) won't show in the picks table.
- **JS getDay() vs Python weekday()** — JS Sunday = 0, Python Sunday = 6. Weekend checks differ: JS uses `[0, 6].includes(day)`, Python uses `weekday() >= 5`.
- **Main UI picks cap** is separate: `MAX_DAILY_UI_PICKS = 2` in `complete_daily_analysis.py` (~line 364). This controls the best-bet + second-best picks, not the extended pool.

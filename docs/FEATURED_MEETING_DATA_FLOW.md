# Featured Meeting Data Flow - Debugging Guide

**Created:** 2026-05-20  
**Purpose:** Document how featured meeting data flows through the system for easier debugging

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  DynamoDB: SureBetBets                                      │
│  ├─ Main System Picks: bet_id format varies                │
│  │  Example: 2026-05-20T172000+0000_Gowran_Park_Rolltight │
│  │  Fields: bet_date, bet_id, outcome, result, horse       │
│  │                                                           │
│  └─ Featured Picks: bet_id = YYYY-MM-DD_FEATURED_...       │
│     Example: 2026-05-20_FEATURED_GOWRAN_18:20_Rolltight    │
│     Fields: bet_date, bet_id, outcome, result, horse,       │
│             is_featured_meeting=True                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  AWS Lambda: betbudai-picks-api                            │
│  File: backend/api/lambda_function.py                      │
│  Function: get_punchestown_tomorrow_picks() (line 963)     │
│                                                              │
│  Endpoint: /api/picks/featured-meeting                      │
│  URL: https://mnybvagd5m.execute-api.eu-west-1.amazonaws...│
│                                                              │
│  Query: KeyConditionExpression='bet_date'=:date (line 1036)│
│  → Returns ALL picks for that date (main + featured)        │
│                                                              │
│  Outcome Mapping: _norm_outcome() function (line 1045)     │
│  ├─ Reads: row.get('outcome') or row.get('result')        │
│  └─ Returns: 'win', 'loss', 'placed', or 'pending'         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  React App: frontend/src/App.js                            │
│  Deployed: https://dev.d2cp2pfnzl7t60.amplifyapp.com       │
│                                                              │
│  Fetches: /api/picks/featured-meeting?date=YYYY-MM-DD      │
│  Displays: Win rate, ROI, pick outcomes                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Critical Data Fields

### DynamoDB Record Structure

**Primary Key:**
- `bet_date` (String): YYYY-MM-DD format
- `bet_id` (String): Unique identifier per bet

**Outcome Fields (CRITICAL - Multiple fields used!):**
- `outcome` (String): 'win', 'loss', 'placed' (lowercase) - **API reads this first**
- `result` (String): 'WIN', 'LOSS', 'PLACED' (uppercase) - **API fallback**
- `actual_result` (String): 'WIN', 'LOSS', 'PLACED' - Settlement system field

**Other Fields:**
- `horse` (String): Horse name
- `course` (String): Course name
- `race_time` (String): ISO 8601 timestamp
- `odds` / `decimal_odds` (Number): Betting odds
- `outcome_value` (Number): Returns if won, 0 if lost
- `is_featured_meeting` (Boolean): True for featured picks

---

## Common Issues & Solutions

### Issue 1: Featured Page Shows Wrong Results

**Symptom:** Featured meeting page displays incorrect win/loss outcomes

**Root Cause:** Multiple records for same horse (main system + featured picks)

**Example:**
```
# TWO records for Rolltight on 2026-05-20:
1. bet_id: 2026-05-20T172000+0000_Gowran_Park_Rolltight
   outcome: loss (WRONG - main system pick marked early)

2. bet_id: 2026-05-20_FEATURED_GOWRAN_18:20_Rolltight
   outcome: win (CORRECT - featured pick)
```

**Solution:** API queries ALL picks for the date. If a horse appears in both main system and featured picks, you must update BOTH records OR filter the API query.

**Fix Script:** `scripts/fix_main_system_outcomes.py`

---

### Issue 2: API Returns Stale Data

**Symptom:** DynamoDB has correct data but API returns old results

**Root Causes:**
1. Lambda function caching
2. Multiple Lambda instances running old code
3. API Gateway caching (disabled on this API)

**Solutions:**

1. **Update Lambda environment to force restart:**
   ```bash
   aws lambda update-function-configuration \
     --function-name betbudai-picks-api \
     --region eu-west-1 \
     --environment "Variables={CACHE_BUST=$(date +%s)}"
   ```

2. **Wait 5-10 seconds for Lambda cold start**

3. **Force refresh API call:**
   ```bash
   curl "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/featured-meeting?date=2026-05-20&course=Gowran+Park&force_refresh=true"
   ```

---

### Issue 3: Outcome Field Not Set

**Symptom:** API returns `outcome: 'pending'` or `outcome: null`

**Root Cause:** The `_norm_outcome()` function (line 1045) checks:
1. `row.get('outcome')` - **CHECK THIS FIRST**
2. `row.get('result')` - Fallback

**Solution:** Always set BOTH fields when updating results:

```python
table.update_item(
    Key={'bet_date': date, 'bet_id': bet_id},
    UpdateExpression='SET actual_result = :win, #out = :outcome, #res = :result',
    ExpressionAttributeNames={
        '#out': 'outcome',
        '#res': 'result'
    },
    ExpressionAttributeValues={
        ':win': 'WIN',
        ':outcome': 'win',    # lowercase for API
        ':result': 'WIN'      # uppercase for settlement
    }
)
```

---

## Debugging Checklist

When featured meeting results are wrong, follow these steps:

### 1. Check DynamoDB Records

```bash
# Find ALL records for a horse (may have duplicates!)
aws dynamodb query \
  --table-name SureBetBets \
  --key-condition-expression "bet_date = :date" \
  --expression-attribute-values '{":date":{"S":"2026-05-20"}}' \
  --region eu-west-1 \
  --query 'Items[?contains(bet_id.S, `Rolltight`)].[bet_id.S,outcome.S,result.S,is_featured_meeting.BOOL]'
```

**Expected Output:** Each horse should have ONE record with:
- `outcome: 'win'` (lowercase)
- `result: 'WIN'` (uppercase)
- `is_featured_meeting: true` (if featured pick)

### 2. Check API Response

```bash
curl -s "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/featured-meeting?date=2026-05-20&course=Gowran+Park" | python -m json.tool | grep -A 5 "Rolltight"
```

**Expected Output:** Should show `"outcome": "win"` for winners

### 3. Restart Lambda If Needed

```bash
# Force Lambda restart
aws lambda update-function-configuration \
  --function-name betbudai-picks-api \
  --region eu-west-1 \
  --environment "Variables={CACHE_BUST=$(date +%s)}"

# Wait 5 seconds
sleep 5

# Test again
curl "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/featured-meeting?date=2026-05-20&course=Gowran+Park"
```

### 4. Check Frontend

1. Open: https://dev.d2cp2pfnzl7t60.amplifyapp.com
2. Navigate to featured meeting page
3. Verify outcomes match API response
4. Check browser console for errors

---

## Key Files

### Backend
- **Lambda Function:** `backend/api/lambda_function.py`
  - Line 963: `get_punchestown_tomorrow_picks()` - main handler
  - Line 1036: DynamoDB query
  - Line 1045: `_norm_outcome()` - outcome mapping
  - Line 1256: Outcome assignment to runner

### Frontend
- **React App:** `frontend/src/App.js`
  - Featured meeting display logic (search for "Featured Meeting")
  - API calls to `/api/picks/featured-meeting`

### Scripts
- **Fix Outcomes:** `scripts/fix_main_system_outcomes.py`
- **Add Featured Winners:** `scripts/update_featured_results_corrected.py`
- **Force API Refresh:** `scripts/fix_featured_api_outcomes.py`

---

## AWS Resources

### Lambda Functions
- **betbudai-picks-api** (eu-west-1)
  - Runtime: Python 3.11
  - Handler: `backend/api/lambda_function.lambda_handler`
  - Endpoint: API Gateway `/api/picks/featured-meeting`

- **surebet-featured-meeting** (eu-west-1)
  - Runtime: Python 3.11
  - Handler: `sf_featured_meeting.lambda_handler`
  - Purpose: Generate featured meeting picks (NOT used for API responses)

### API Gateway
- **API ID:** e5na6ldp35
- **Name:** SureBet API EU
- **Stage:** prod
- **Base URL:** https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com
- **Caching:** Disabled

### DynamoDB
- **Table:** SureBetBets
- **Region:** eu-west-1
- **Primary Key:** bet_date (partition), bet_id (sort)

---

## Testing Commands

### Quick Test Featured Meeting API
```bash
curl -s "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/featured-meeting?date=2026-05-20&course=Gowran+Park" | \
python -c "import sys,json; d=json.load(sys.stdin); \
[print(f\"{r['time_user']} {r['runners'][0]['horse']:20s} {r['runners'][0].get('outcome','?')}\") \
for r in d['races'][:5]]"
```

### Check All Featured Picks in DynamoDB
```bash
aws dynamodb query \
  --table-name SureBetBets \
  --key-condition-expression "bet_date = :date" \
  --filter-expression "is_featured_meeting = :featured" \
  --expression-attribute-values '{":date":{"S":"2026-05-20"},":featured":{"BOOL":true}}' \
  --region eu-west-1 \
  --query 'Items[*].[bet_id.S,horse.S,outcome.S]'
```

### Update Single Outcome
```python
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

table.update_item(
    Key={
        'bet_date': '2026-05-20',
        'bet_id': '2026-05-20_FEATURED_GOWRAN_18:20_Rolltight'
    },
    UpdateExpression='SET #out = :win, #res = :win2',
    ExpressionAttributeNames={
        '#out': 'outcome',
        '#res': 'result'
    },
    ExpressionAttributeValues={
        ':win': 'win',
        ':win2': 'WIN'
    }
)
```

---

## Contact & Support

**File:** `docs/FEATURED_MEETING_DATA_FLOW.md`  
**Last Updated:** 2026-05-20  
**Maintainer:** Claude Sonnet 4.5

For issues:
1. Check this debugging guide first
2. Follow the debugging checklist
3. Review recent script execution logs
4. Check AWS CloudWatch logs for Lambda errors

---

## Change Log

### 2026-05-20 - Initial Creation
- Documented complete data flow
- Added debugging checklist
- Identified duplicate record issue (main + featured picks)
- Created fix scripts for outcome mismatches

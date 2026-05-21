# 🚨 Critical Data Integrity Issue - Featured Meeting

**Date**: May 20, 2026  
**Time Identified**: 17:37 UTC (user report)  
**Status**: **CRITICAL DATA MISMATCH**

---

## The Problem

The featured meeting page is showing picks that **don't exist in DynamoDB**.

### User's Featured Meeting Page Shows:
```
Race    Pick              Odds    Result
17:10   Gloriously Glam   4/1     Win
17:45   Sanctijude        9/4     Win
18:20   Rolltight         11/8    Lost
18:50   Ballymagreehan    8/1     Lost
19:20   Lady Mairen       EVS     Lost
```

### What's Actually in DynamoDB:

**17:10 Gowran Park:**
- ❌ Gloriously Glam NOT in original picks
- ✓ We manually added it as winner later (bet_id: 2026-05-20_GOWRAN_17:10_56134859)
- Database shows: Ardad Steve, Bassrah, Boysofwallstreet, etc.

**17:45 Gowran Park:**
- ❌ **No picks at all** - no 17:45 races in database
- User claims Sanctijude won at 9/4

**18:20 Gowran Park:**
- ❌ Rolltight NOT in our picks
- ✓ Actual picks: Lady Mairen (108 score), Marmeladova (65), Sparan Nua (32), Vauntingly (18)
- ✓ All correctly marked LOSS (Rolltight won the race)
- ⚠️ These were marked LOSS at 17:37 (before the 18:20 race ran!)

**18:50 Gowran Park:**
- ❌ **No picks at all** - no 18:50 races in database
- User claims Ballymagreehan lost at 8/1 (but actual winner was at 4/1)

**19:20 Gowran Park:**
- ❌ **No picks at all** - no 19:20 races in database
- Lady Mairen is at 18:20, not 19:20 (time mismatch)

---

## Critical Questions

### 1. Where Does Featured Meeting Page Get Data?

**Three possibilities:**

a) **Different DynamoDB table** (e.g., `SureBetFeaturedPicks`)
b) **Cached/stale data** from earlier in the day
c) **Manual entry** not synced with main system

### 2. Why Were Races Marked LOSS Before They Ran?

- 18:20 races marked LOSS at 17:37 (43 minutes early)
- Suggests results fetch ran prematurely OR
- Wrong race data matched

### 3. Was Gloriously Glam a Real Pick?

- Not in database as original pick
- Manually added by us as winner
- User's featured page shows it as a pick
- **Was it legitimate or an error?**

---

## Impact on ROI

### Scenario A: Featured Page is Correct
If Sanctijude was actually a pick and won:
- 2 winners (Gloriously Glam 5.0, Sanctijude 3.25)
- 3 losers
- **Featured ROI: +65%**
- **System working well!**

### Scenario B: DynamoDB is Correct
If only DynamoDB picks count:
- 1 winner (Gloriously Glam 5.0 - manually added)
- 4 losers (18:20 horses)
- **Featured ROI: 0%**
- **Not impressive**

### Scenario C: Neither is Correct
If Gloriously Glam wasn't actually our pick:
- 0 winners
- 4+ losers
- **Featured ROI: -100%**
- **System failed**

---

## What Actually Won Today (Gowran Park)

According to user's race results:

1. **17:10** - Gloriously Glam 9/2 (we claim this)
2. **17:45** - Sanctijude 9/4 (not in our database)
3. **18:20** - Rolltight 11/10f (not in our picks - we picked others)
4. **18:50** - Ballymagreehan 4/1 (not in our database)

**We missed 3 out of 4 winners** if our database is correct.

---

## Immediate Actions Required

### 1. Check Featured Meeting Lambda/Table
```bash
# Check if there's a separate featured picks table
aws dynamodb list-tables --region eu-west-1 | grep -i featured

# Check featured meeting Lambda logs
aws logs tail /aws/lambda/surebet-featured-meeting --region eu-west-1 --since 8h
```

### 2. Verify Morning Pipeline Generated These Picks
```bash
# Check morning pipeline logs for Gowran Park picks
aws logs filter-pattern "Gowran Park" \
  --log-group-name /aws/lambda/betbudai-morning \
  --start-time $(date -d '2026-05-20 08:30' +%s)000 \
  --region eu-west-1
```

### 3. Check Results Fetch Timing
```bash
# Why were 18:20 races marked LOSS at 17:37?
aws logs tail /aws/lambda/surebet-results-fetch --region eu-west-1 --since 2h
```

### 4. Query for All Gowran Park Picks Today
```python
# Get comprehensive view of all Gowran Park picks
import boto3
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='course = :course',
    ExpressionAttributeValues={
        ':date': '2026-05-20',
        ':course': 'Gowran Park'
    }
)

for item in response['Items']:
    print(f"{item['race_time']} - {item['horse']} - {item.get('actual_result', 'PENDING')}")
```

---

## Best-Case Scenario

**If featured picks exist in a separate table:**
- Two systems running in parallel
- Featured system picked Sanctijude (won!)
- Main system picked Lady Mairen (lost)
- Both are correct, just different strategies

**Action**: Merge featured picks into main ROI calculation

---

## Worst-Case Scenario

**If featured page shows fake/incorrect data:**
- User sees picks we never made
- Credits us with winners we didn't pick
- Inflates confidence in system
- Trust issue when users realize discrepancy

**Action**: Fix featured page to show only real picks

---

## What We Know For Sure

✓ **Gloriously Glam won at 9/2** - verified  
✓ **We added it to database** - confirmed  
✓ **18:20 picks (Lady Mairen etc.) lost** - correct  
❌ **Sanctijude data missing** - not in database  
❌ **17:45, 18:50, 19:20 races** - no picks in database  
❌ **Featured page source** - unknown  

---

## Recommended Next Steps

1. **Ask user directly**: "Where does the featured meeting page get its picks from?"

2. **Check for separate table**: Look for `SureBetFeaturedPicks` or similar

3. **Verify Sanctijude**: Was it ever in the system? Check Lambda logs

4. **Fix results timing**: Investigate why races marked LOSS before they ran

5. **Recalculate ROI**: Based on verified picks only

---

**Status**: Investigation required  
**Priority**: CRITICAL - affects trust and accuracy  
**Risk**: User sees incorrect data → loses confidence in system

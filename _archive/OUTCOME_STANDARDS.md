# Database Outcome Value Standards

## ⚠️ MANDATORY STANDARDS - READ BEFORE WRITING TO DATABASE

### Standard Outcome Values (ALWAYS USE THESE)

**Use ONLY these uppercase values when writing to the database:**

| Outcome | Value to Use | Description |
|---------|-------------|-------------|
| Win | `'WON'` | Bet won |
| Loss | `'LOST'` | Bet lost |
| Place | `'PLACED'` | Each-way bet placed but didn't win |
| Pending | `'PENDING'` | Race hasn't run or result not recorded |

### ❌ DO NOT USE (These cause UI bugs)

**NEVER use these lowercase or mixed-case variants:**
- ❌ `'win'`, `'won'` 
- ❌ `'loss'`, `'lose'`
- ❌ `'place'`, `'placed'`
- ❌ `'pending'`, `'pend'`

### How to Use

**Import the standard module:**
```python
from outcome_standards import (
    OUTCOME_WON, 
    OUTCOME_LOST, 
    OUTCOME_PLACED, 
    OUTCOME_PENDING,
    normalize_outcome
)
```

**When writing to DynamoDB:**
```python
# ✅ CORRECT
table.update_item(
    Key={'bet_date': date, 'bet_id': bet_id},
    UpdateExpression='SET outcome = :outcome',
    ExpressionAttributeValues={
        ':outcome': OUTCOME_WON  # or OUTCOME_LOST, OUTCOME_PLACED, OUTCOME_PENDING
    }
)

# ❌ WRONG
table.update_item(
    ExpressionAttributeValues={
        ':outcome': 'win'  # DON'T DO THIS
    }
)
```

**When normalizing user input:**
```python
from outcome_standards import normalize_outcome

# Handles any case variation and returns standard value
user_input = 'win'  # Could be from API, scraper, etc.
standard_outcome = normalize_outcome(user_input)  # Returns 'WON'
```

**When checking outcomes:**
```python
from outcome_standards import is_win, is_loss, is_resolved, is_pending

if is_win(pick['outcome']):
    # Calculate winnings
    
if is_resolved(pick['outcome']):
    # Include in ROI calculation
    
if is_pending(pick['outcome']):
    # Exclude from stats
```

## Why This Matters

**The Case-Sensitivity Bug (Feb 14, 2026):**
- Database had mixed values: `'WON'`, `'win'`, `'won'`, `'LOST'`, `'loss'`
- Lambda API checked for `'win'` only → missed `'WON'` entries
- UI showed 0 wins despite having winning bets
- ROI calculations included pending races

**The Fix:**
1. Lambda API now handles all case variations (backward compatible)
2. Going forward, ALL new code MUST use standard uppercase values
3. Use `outcome_standards.py` module to ensure compliance

## Enforcement

**Before committing code that writes outcomes:**
1. ✅ Import from `outcome_standards.py`
2. ✅ Use `OUTCOME_WON`, `OUTCOME_LOST`, `OUTCOME_PLACED`, `OUTCOME_PENDING`
3. ✅ Never hardcode lowercase outcome strings
4. ✅ Use `normalize_outcome()` when processing external data

**Files to update when adding new result scripts:**
- Any script using `UpdateExpression='SET outcome = :outcome'`
- Any script with `':outcome':` in ExpressionAttributeValues
- Any script processing race results from scrapers/APIs

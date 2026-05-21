# EMBEDDED AUTOMATED LEARNING SYSTEM

## Overview
The learning system is now **fully embedded** into the daily workflow. It runs automatically every day without manual intervention.

## How It Works

### Daily Workflow (Automated)
Every day at **8:00 AM**, the system automatically:

1. **Fetches Yesterday's Results** → Gets actual race outcomes from Betfair API
2. **Analyzes Performance** → Compares predictions vs actual results
3. **Auto-Adjusts Weights** → Updates scoring algorithm based on patterns
4. **Fetches Today's Races** → Gets current race data
5. **Generates New Picks** → Uses optimized weights from step 3
6. **Saves to DynamoDB** → Makes picks available via Lambda/API

### Continuous Learning Loop

```
Day 1:
  Results → Learn → Adjust → Predict
                       ↓
Day 2:                Weights v2
  Results → Learn → Adjust → Predict
                       ↓
Day 3:                Weights v3
  Results → Learn → Adjust → Predict
                       ↓
Day N:                Weights vN (continuously improving)
```

## What Gets Learned

### Pattern Detection
The system automatically detects:
- Poor form horses that win/place (form may be overweighted)
- Optimal odds effectiveness (correlation with wins)
- Sweet spot range performance (3-9 odds validation)
- Course bonus effectiveness
- Database history predictive power

### Weight Adjustments
Example from today (Feb 2, 2026):
- **Finding:** 83.3% success rate despite poor/missing form
- **Action:** Reduced `recent_win` weight from 25 → 23 (-2pts)
- **Finding:** 66.7% win rate in optimal odds range (3-6)
- **Action:** Increased `optimal_odds` weight from 20 → 25 (+5pts)

### Score Recalibration
Every pick uses current weights:
```python
# OLD (Day 1):
score = sweet_spot(30) + optimal_odds(20) + recent_win(25) + ...

# NEW (Day 2 - after learning):
score = sweet_spot(30) + optimal_odds(25) + recent_win(23) + ...
```

## Files Modified

### Core Workflow Files

**1. continuous_learning_system.py**
- Added `auto_adjust_weights()` method
- Calls `auto_adjust_weights.py` after processing results
- Runs every 30 minutes during 2-week learning cycle

**2. daily_learning_workflow.py**
- Added weight adjustment after evaluation step
- Runs as part of daily learning loop
- Continues even if weight adjustment fails

**3. daily_automated_workflow.py** ⭐ NEW
- Complete daily workflow script
- Combines all steps in correct order
- Scheduled to run automatically via Windows Task Scheduler

### Learning Engine

**4. auto_adjust_weights.py**
- Analyzes completed picks
- Detects performance patterns
- Calculates weight adjustments
- Saves to DynamoDB (SYSTEM_WEIGHTS record)

**5. comprehensive_pick_logic.py**
- Loads dynamic weights from DynamoDB
- Caches weights for 5 minutes
- Falls back to defaults if unavailable
- Uses updated weights for all new picks

### Automation

**6. setup_automated_learning.ps1** ⭐ NEW
- Creates Windows Task Scheduler entry
- Runs daily at 8:00 AM
- Configures logging and error handling

## Scheduled Task Setup

### Create the Task:
```powershell
.\setup_automated_learning.ps1
```

### Verify It's Running:
```powershell
Get-ScheduledTask -TaskName "BettingWorkflow_AutoLearning"
```

### Manual Test Run:
```powershell
python daily_automated_workflow.py
```

### Check Logs:
```powershell
Get-Content .\logs\daily_workflow.log -Tail 50
```

## Data Flow

### Weight Storage (DynamoDB)
```
Table: SureBetBets
Record:
  bet_id: "SYSTEM_WEIGHTS"
  bet_date: "CONFIG"
  weights: {
    sweet_spot: 30,
    optimal_odds: 25,  ← Updated automatically
    recent_win: 23,     ← Updated automatically
    total_wins: 5,
    consistency: 2,
    course_bonus: 10,
    database_history: 15
  }
  last_updated: "2026-02-02T20:18:36"
  learning_summary: {
    poor_form_success_count: 5,
    optimal_odds_win_rate: 0.667,
    adjustments_made: [...]
  }
```

### Pick Generation Flow
```
1. comprehensive_pick_logic.py loads weights from DynamoDB
2. Analyzes each horse using current weights
3. Calculates comprehensive score (0-100)
4. Assigns confidence level automatically
5. Sets show_in_ui=True only if score >= 75
6. Saves pick to DynamoDB
7. Lambda/API filters and displays
```

## Monitoring

### Check Current Weights:
```python
python -c "
from auto_adjust_weights import get_current_weights
import json
print(json.dumps(get_current_weights(), indent=2))
"
```

### View Learning History:
```python
import boto3
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
response = table.get_item(Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'})
print(response['Item'])
```

### Test Weight Adjustment:
```powershell
python auto_adjust_weights.py
```

## Benefits

### 1. No Manual Intervention
- System runs automatically every day
- Learns from results without human input
- Adjusts weights based on evidence

### 2. Continuous Improvement
- Gets smarter over time
- Adapts to changing patterns
- Self-corrects when strategies underperform

### 3. Data-Driven Decisions
- Every adjustment backed by results
- Pattern detection from actual outcomes
- Quantified performance metrics

### 4. Transparency
- All adjustments logged
- Reasoning documented
- History preserved in DynamoDB

### 5. Embedded Integration
- Works seamlessly with existing workflow
- No separate scripts to remember
- Part of the daily process

## Example Learning Cycle

### Day 1 (Feb 2, 2026):
```
Results:
- 4 wins (Take The Boat, Horace Wallace, My Genghis, Mr Nugget)
- 1 loss (Market House @ 5.9, score 93 - good pick, unlucky)
- 1 place (Crimson Rambler @ 4.0, score 47 - poor form but placed 2nd)

Learning:
- Poor form success rate: 83.3% (5 of 6 picks had no/poor form)
- Optimal odds win rate: 66.7% (all 4 winners in 3-6 range)
- Form analysis may be too strict

Adjustments:
- optimal_odds: 20 → 25 (+5pts)
- recent_win: 25 → 23 (-2pts)
```

### Day 2 (Feb 3, 2026):
```
Next analysis will use new weights:
- Horse with poor form but optimal odds gets fairer evaluation
- Optimal odds correlation now weighted more heavily
- System adapts based on Day 1 evidence
```

### Day 7 (Feb 8, 2026):
```
After 7 days of learning:
- Weights continuously refined
- Patterns validated or adjusted
- Scoring algorithm optimized for current conditions
```

## Rollback / Manual Override

### View Current Weights:
```python
python demonstrate_learning.py
```

### Reset to Defaults (if needed):
```python
# Delete SYSTEM_WEIGHTS record to reset
import boto3
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
table.delete_item(Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'})
# System will use DEFAULT_WEIGHTS on next run
```

### Disable Automated Learning:
```powershell
# Disable the scheduled task
Disable-ScheduledTask -TaskName "BettingWorkflow_AutoLearning"

# Re-enable later
Enable-ScheduledTask -TaskName "BettingWorkflow_AutoLearning"
```

## Status

✅ **FULLY OPERATIONAL**

- Daily workflow: Automated ✓
- Weight adjustment: Embedded ✓
- Pattern detection: Active ✓
- DynamoDB storage: Working ✓
- Scheduled task: Configured ✓
- Continuous learning: Enabled ✓

**Next Run:** Tomorrow at 8:00 AM  
**Learning Status:** Active (learning from Feb 2, 2026 results)  
**Current Weights:** Optimized based on first day's performance

---

**Created:** 2026-02-02  
**Status:** Production  
**Automation:** Fully embedded in daily workflow
